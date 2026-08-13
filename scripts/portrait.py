"""
Turns a photo into an animated ASCII-art SVG portrait.

Pipeline:
  1. rembg cuts the subject out, background forced to white
  2. bilateral filter smooths skin while keeping edges
  3. CLAHE adds local contrast so the face isn't one flat tone
  4. a darkening curve (v/255)**1.7 keeps glasses/brows/lips visible
  5. brightness is mapped to a 13-character ramp (light -> dark)
  6. the character grid is rendered as SVG text, one row per <text>,
     each row wrapped in a clipPath that wipes open left-to-right
     (a SMIL "typing" animation), staggered top to bottom.
"""
import sys
import numpy as np
import cv2
from PIL import Image

# --- tunables -----------------------------------------------------------
COLS = 90                 # character columns
CHAR_W_EM = 0.600         # monospace advance width, in em (see notes below)
FONT_SIZE = 12.9          # px, paired with CHAR_W_EM above
DISPLAY_WIDTH_PX = 460
CLAHE_CLIP = 3.0
DARKEN_GAMMA = 1.7
STAGGER_S = 0.09          # seconds between each row starting its wipe
ROW_DURATION_S = 0.6      # how long each row's wipe animation takes

# light -> dark, 13 levels. First char is a blank so background -> nothing.
RAMP = " .:-=+*#%@$&B"


def load_and_cutout(path: str) -> Image.Image:
    """Remove the background, force it to white."""
    from rembg import remove  # imported lazily: heavy dep, only needed here
    with open(path, "rb") as f:
        img = Image.open(f).convert("RGBA")
        cut = remove(img)  # RGBA, transparent background
    # composite onto a white canvas so "no subject" == brightest value
    bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    bg.alpha_composite(cut)
    return bg.convert("L")  # grayscale


def process(gray_img: Image.Image) -> np.ndarray:
    arr = np.array(gray_img)

    # smooth skin, keep edges
    arr = cv2.bilateralFilter(arr, d=9, sigmaColor=75, sigmaSpace=75)

    # local contrast so the face isn't a flat mid-tone blob
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # darken midtones so features survive the ramp mapping
    arr = 255.0 * (arr / 255.0) ** DARKEN_GAMMA
    return arr.astype(np.uint8)


def to_char_grid(arr: np.ndarray, cols: int = COLS) -> list[str]:
    h, w = arr.shape
    rows = max(1, round(cols * (h / w) * 0.48))  # chars are ~2x taller than wide

    small = cv2.resize(arr, (cols, rows), interpolation=cv2.INTER_AREA)

    n = len(RAMP)
    lines = []
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = small[r, c] / 255.0          # 0 = dark, 1 = light
            idx = int((1.0 - brightness) * (n - 1))    # dark -> higher index
            idx = max(0, min(n - 1, idx))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def render_svg(lines: list[str], out_path: str) -> None:
    cols = max(len(l) for l in lines)
    rows = len(lines)

    char_w_px = CHAR_W_EM * FONT_SIZE
    line_h_px = FONT_SIZE * 1.15

    width = cols * char_w_px
    height = rows * line_h_px

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{DISPLAY_WIDTH_PX}" '
        f'font-family="ui-monospace, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">'
    )
    parts.append('<rect width="100%" height="100%" fill="#0d1117"/>')

    for i, line in enumerate(lines):
        y = (i + 1) * line_h_px - (line_h_px - FONT_SIZE)
        row_width = len(line) * char_w_px
        clip_id = f"row{i}"
        begin = f"{i * STAGGER_S:.2f}s"

        escaped = (
            line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{i * line_h_px:.1f}" width="0" height="{line_h_px:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{begin}" dur="{ROW_DURATION_S}s" fill="freeze"/>'
            f"</rect>"
        )
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'<text x="0" y="{y:.1f}" xml:space="preserve" fill="#c9d1d9">{escaped}</text>'
        )
        # small cursor block riding the wipe edge
        parts.append(
            f'<rect y="{i * line_h_px:.1f}" width="{char_w_px:.1f}" height="{line_h_px:.1f}" fill="#c9d1d9">'
            f'<animate attributeName="x" from="0" to="{row_width:.1f}" '
            f'begin="{begin}" dur="{ROW_DURATION_S}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin}+{ROW_DURATION_S}s"/>'
            f"</rect>"
        )
        parts.append("</g>")

    parts.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(parts))


def generate_portrait(input_path: str, output_path: str) -> None:
    gray = load_and_cutout(input_path)
    arr = process(gray)
    lines = to_char_grid(arr)
    render_svg(lines, output_path)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "assets/photo.jpg"
    dst = sys.argv[2] if len(sys.argv) > 2 else "portrait.svg"
    generate_portrait(src, dst)
    print(f"wrote {dst}")
