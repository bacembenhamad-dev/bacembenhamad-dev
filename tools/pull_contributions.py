"""Pull the public GitHub contribution calendar (no auth/token needed) and
save daily counts plus streak/day-of-week stats to assets/contributions.json.
"""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import httpx
from lxml import html

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "assets" / "contributions.json"
USERNAME = "bacembenhamad-dev"
URL = f"https://github.com/users/{USERNAME}/contributions"

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

COUNT_RE = re.compile(r"([\d,]+)\s+contribution")


def count_from_text(text: str) -> int:
    text = text.strip().lower()
    if not text or text.startswith("no contributions"):
        return 0
    match = COUNT_RE.search(text)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def cell_count(tree, cell) -> int:
    # Newer markup: count directly on the cell (data-count / aria-label / title).
    for attr in ("data-count", "aria-label", "title"):
        value = cell.get(attr)
        if value:
            if attr == "data-count":
                return int(value)
            return count_from_text(value)

    # Older markup: count lives in a separate <tool-tip for="cell-id">.
    tooltip_id = cell.get("id")
    if tooltip_id:
        tooltip = tree.xpath(f"//*[@for='{tooltip_id}']")
        if tooltip:
            return count_from_text(tooltip[0].text_content())

    return 0


def fetch_days() -> list[dict]:
    resp = httpx.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)

    days = []
    cells = tree.xpath("//td[@data-date]") or tree.xpath("//*[@data-date]")
    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level_attr = cell.get("data-level")
        days.append({
            "date": d,
            "count": cell_count(tree, cell),
            "level": int(level_attr) if level_attr is not None else None,
        })

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {"current_streak": 0, "longest_streak": 0, "busiest_day": None, "total": 0}

    total = sum(d["count"] for d in days)

    longest = current = 0
    for d in days:
        if d["count"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    by_weekday = Counter()
    for d in days:
        if d["count"] > 0:
            weekday = datetime.strptime(d["date"], "%Y-%m-%d").weekday()
            by_weekday[DAY_NAMES[weekday]] += d["count"]
    busiest_day = max(by_weekday, key=by_weekday.get) if by_weekday else None

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "busiest_day": busiest_day,
    }


if __name__ == "__main__":
    days = fetch_days()
    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(days)} days, {stats})")
