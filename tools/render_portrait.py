"""Render assets/photo-ready.png as a self-drawing monochrome ASCII portrait.

Each output row is wrapped in its own clip-path rect whose width animates
from 0 to full via SMIL, staggered row by row, so the portrait appears to
draw itself in top-to-bottom. Once fully drawn it holds (no looping).
"""
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "assets" / "photo-ready.png"
OUTPUT = REPO_ROOT / "portrait.svg"

GLYPHS = " '.,:;~+*xXO#"  # left = light/empty, right = dense/dark

COLS = 90
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.05
ROW_STAGGER = 0.04  # seconds
DRAW_DUR = 0.5  # seconds per row

BG_COLOR = "#0a0e0f"
FG_COLOR = "#39ff14"


def brightness_to_glyph(value: int) -> str:
    idx = int((255 - value) / 255 * (len(GLYPHS) - 1))
    return GLYPHS[idx]


def build_grid(source: Path) -> list[str]:
    img = Image.open(source).convert("L")
    rows = round(COLS * (img.height / img.width) * (CHAR_W / LINE_H))
    small = img.resize((COLS, rows), Image.LANCZOS)
    pixels = small.load()
    lines = []
    for y in range(rows):
        line = "".join(brightness_to_glyph(pixels[x, y]) for x in range(COLS))
        lines.append(line)
    return lines


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(lines: list[str]) -> str:
    width = COLS * CHAR_W + 20
    height = len(lines) * LINE_H + 20

    rows_svg = []
    for i, line in enumerate(lines):
        y = 10 + (i + 1) * LINE_H
        row_width = COLS * CHAR_W
        begin = round(i * ROW_STAGGER, 3)
        rows_svg.append(f'''
  <clipPath id="row{i}">
    <rect x="0" y="{y - LINE_H}" width="0" height="{LINE_H + 2}">
      <animate attributeName="width" from="0" to="{row_width + 20}"
               begin="{begin}s" dur="{DRAW_DUR}s" fill="freeze" calcMode="spline"
               keySplines="0.25 0.1 0.25 1" />
    </rect>
  </clipPath>
  <g clip-path="url(#row{i})">
    <text x="10" y="{y}" font-family="'Cascadia Code','Consolas',monospace"
          font-size="{FONT_SIZE}" fill="{FG_COLOR}" xml:space="preserve">{escape(line)}</text>
  </g>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}"
     viewBox="0 0 {width:.0f} {height:.0f}">
  <rect width="100%" height="100%" fill="{BG_COLOR}" />
{"".join(rows_svg)}
</svg>
'''


if __name__ == "__main__":
    grid = build_grid(SOURCE)
    svg = render_svg(grid)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT} ({COLS}x{len(grid)} chars)")
