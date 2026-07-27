"""Render assets/contributions.json as an animated contribution grid SVG.

Squares reveal column-by-column (week-by-week) rather than row-by-row, then
freeze once fully drawn. Colors use a green-matrix ramp instead of GitHub's
default greens so the graph matches the portrait/panel theme.
"""
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "assets" / "contributions.json"
OUTPUT = REPO_ROOT / "graph.svg"

LEVELS = ["#0d1f12", "#154d27", "#1f8f3f", "#39ff14", "#9dffb0"]
BG_COLOR = "#0a0e0f"
TEXT_COLOR = "#39ff14"
LABEL_COLOR = "#1f8f3f"
FONT = "'Cascadia Code','Consolas',monospace"

CELL = 11
GAP = 3
COL_STAGGER = 0.03
CELL_FADE = 0.35
PADDING = 16
LEGEND_H = 26
STATS_H = 22


def level_for(day: dict, max_count: int) -> int:
    if day.get("level") is not None:
        return max(0, min(4, day["level"]))
    if day["count"] == 0 or max_count == 0:
        return 0
    ratio = day["count"] / max_count
    return max(1, min(4, round(ratio * 4)))


def build_weeks(days: list[dict]) -> list[list[tuple[int, dict]]]:
    weeks: list[list[tuple[int, dict]]] = []
    current: list[tuple[int, dict]] = []
    for day in days:
        dow_sun = (datetime.strptime(day["date"], "%Y-%m-%d").weekday() + 1) % 7
        if dow_sun == 0 and current:
            weeks.append(current)
            current = []
        current.append((dow_sun, day))
    if current:
        weeks.append(current)
    return weeks


def render_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload["stats"]
    max_count = max((d["count"] for d in days), default=0)
    weeks = build_weeks(days)

    grid_w = len(weeks) * (CELL + GAP)
    grid_h = 7 * (CELL + GAP)
    width = grid_w + PADDING * 2
    height = grid_h + PADDING * 2 + LEGEND_H + STATS_H

    cells_svg = []
    for col, week in enumerate(weeks):
        begin = round(col * COL_STAGGER, 3)
        for row, day in week:
            x = PADDING + col * (CELL + GAP)
            y = PADDING + row * (CELL + GAP)
            color = LEVELS[level_for(day, max_count)]
            cells_svg.append(f'''
  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" opacity="0">
    <title>{day["date"]}: {day["count"]} contributions</title>
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{CELL_FADE}s" fill="freeze" />
  </rect>''')

    legend_y = PADDING + grid_h + 16
    legend_x = width - PADDING - (len(LEVELS) * (CELL + GAP)) - 40
    legend_svg = [f'<text x="{legend_x - 34}" y="{legend_y + CELL - 1}" font-family="{FONT}" font-size="10" fill="{LABEL_COLOR}">Less</text>']
    for i, color in enumerate(LEVELS):
        legend_svg.append(
            f'<rect x="{legend_x + i * (CELL + GAP)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" />'
        )
    legend_svg.append(
        f'<text x="{legend_x + len(LEVELS) * (CELL + GAP) + 6}" y="{legend_y + CELL - 1}" font-family="{FONT}" font-size="10" fill="{LABEL_COLOR}">More</text>'
    )

    stats_line = (
        f"total: {stats['total']}   "
        f"current streak: {stats['current_streak']}d   "
        f"longest streak: {stats['longest_streak']}d   "
        f"busiest day: {stats['busiest_day'] or 'n/a'}"
    )
    stats_y = legend_y + 22

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{BG_COLOR}" rx="6" />
{"".join(cells_svg)}
{"".join(legend_svg)}
  <text x="{PADDING}" y="{stats_y}" font-family="{FONT}" font-size="11" fill="{TEXT_COLOR}">{stats_line}</text>
</svg>
'''


if __name__ == "__main__":
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    svg = render_svg(payload)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT}")
