"""
Entry point the workflow calls. Right now this just writes placeholder
files so the pipeline (checkout -> generate -> commit-if-changed) works
end to end. Swap in the real portrait + stats logic next.
"""
import os
from datetime import datetime, timezone

GH_LOGIN = os.environ.get("GH_LOGIN", "unknown")


def write_placeholder_svg(path: str, label: str) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="460" height="120">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <text x="16" y="64" font-family="monospace" font-size="14" fill="#c9d1d9">
    {label} — generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}
  </text>
</svg>"""
    with open(path, "w") as f:
        f.write(svg)


def main() -> None:
    write_placeholder_svg("portrait.svg", "portrait placeholder")
    write_placeholder_svg("stats.svg", "stats placeholder")
    write_placeholder_svg("streak.svg", "streak placeholder")
    write_placeholder_svg("languages.svg", "languages placeholder")
    write_placeholder_svg("year.svg", "year placeholder")

    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write(f"# {GH_LOGIN}\n\n<!-- generated content will replace this -->\n")


if __name__ == "__main__":
    main()
