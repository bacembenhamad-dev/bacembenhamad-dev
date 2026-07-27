"""Render a terminal-style system-info panel as a self-typing SVG.

Set PREVIEW=1 to render a static (fully visible, non-animated) frame for
quick viewing in a normal image viewer.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "sysinfo.svg"

TITLE = "guest@bacembenhamad-dev"

ROWS = [
    ("role", "Ai and Data Sience Engineer"),
    ("focus", "Building things that work"),
    ("stack", "Full-Stack Python · Typescript · SQL"),
    ("now", "I just do it and learn along the way"),
]

BG_COLOR = "#0a0e0f"
PANEL_BORDER = "#154d27"
HEADER_BG = "#0d1f12"
FG_COLOR = "#39ff14"
LABEL_COLOR = "#1f8f3f"
FONT = "'Cascadia Code','Consolas',monospace"

FONT_SIZE = 14
LINE_H = 28
PADDING = 20
HEADER_H = 36
ROW_STAGGER = 0.35  # seconds between each row appearing
FADE_DUR = 0.4

PREVIEW = os.environ.get("PREVIEW") == "1"


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_svg() -> str:
    width = 460
    height = HEADER_H + PADDING * 2 + LINE_H * len(ROWS)
    label_w = max(len(label) for label, _ in ROWS) + 1

    rows_svg = []
    for i, (label, value) in enumerate(ROWS):
        y = HEADER_H + PADDING + (i + 1) * LINE_H - 8
        initial_opacity = 1 if PREVIEW else 0
        text = f'''
  <text x="{PADDING}" y="{y}" font-family="{FONT}" font-size="{FONT_SIZE}" opacity="{initial_opacity}">
    <tspan fill="{LABEL_COLOR}">{escape(label).ljust(label_w)}</tspan><tspan fill="{FG_COLOR}"> {escape(value)}</tspan>'''
        if not PREVIEW:
            begin = round(i * ROW_STAGGER, 2)
            text += f'''
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{FADE_DUR}s" fill="freeze" />'''
        text += "\n  </text>"
        rows_svg.append(text)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{BG_COLOR}" stroke="{PANEL_BORDER}" stroke-width="1.5" rx="6" />
  <rect x="0" y="0" width="100%" height="{HEADER_H}" fill="{HEADER_BG}" rx="6" />
  <rect x="0" y="{HEADER_H - 6}" width="100%" height="6" fill="{HEADER_BG}" />
  <circle cx="18" cy="{HEADER_H / 2}" r="5" fill="#ff5f56" />
  <circle cx="36" cy="{HEADER_H / 2}" r="5" fill="#ffbd2e" />
  <circle cx="54" cy="{HEADER_H / 2}" r="5" fill="#27c93f" />
  <text x="{width / 2}" y="{HEADER_H / 2 + 5}" text-anchor="middle" font-family="{FONT}"
        font-size="12" fill="{LABEL_COLOR}">{escape(TITLE)}</text>
{"".join(rows_svg)}
</svg>
'''


if __name__ == "__main__":
    OUTPUT.write_text(render_svg(), encoding="utf-8")
    mode = "preview (static)" if PREVIEW else "animated"
    print(f"wrote {OUTPUT} [{mode}]")
