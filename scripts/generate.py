"""
Entry point the workflow calls.

Portrait now uses the real pipeline (scripts/portrait.py) if a source
photo exists at assets/photo.jpg. If it's missing, or something in the
pipeline fails, we fall back to a placeholder so the workflow never
breaks the whole profile over a photo problem.

Stats graphics (stats/streak/languages/year) are still placeholders --
that's the next piece to build.
"""
import os
import traceback
from datetime import datetime, timezone

GH_LOGIN = os.environ.get("GH_LOGIN", "unknown")
PHOTO_PATH = "assets/photo.jpg"


def write_placeholder_svg(path: str, label: str) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="460" height="120">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <text x="16" y="64" font-family="monospace" font-size="14" fill="#c9d1d9">
    {label} — generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}
  </text>
</svg>"""
    with open(path, "w") as f:
        f.write(svg)


def build_portrait() -> None:
    if not os.path.exists(PHOTO_PATH):
        print(f"no photo found at {PHOTO_PATH}, writing placeholder")
        write_placeholder_svg("portrait.svg", "portrait placeholder (no photo uploaded yet)")
        return
    try:
        from portrait import generate_portrait
        generate_portrait(PHOTO_PATH, "portrait.svg")
        print("portrait.svg generated from photo")
    except Exception:
        print("portrait generation failed, falling back to placeholder:")
        traceback.print_exc()
        write_placeholder_svg("portrait.svg", "portrait placeholder (generation failed)")


def main() -> None:
    build_portrait()

    write_placeholder_svg("stats.svg", "stats placeholder")
    write_placeholder_svg("streak.svg", "streak placeholder")
    write_placeholder_svg("languages.svg", "languages placeholder")
    write_placeholder_svg("year.svg", "year placeholder")

    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write(f"# {GH_LOGIN}\n\n<!-- generated content will replace this -->\n")


if __name__ == "__main__":
    main()
