#!/usr/bin/env python3
"""Render data/pair-plan.csv as month calendars in README.md.

Writes between <!-- calendar:start --> and <!-- calendar:end -->.
Usage:  python3 scripts/plan_calendar.py          # rebuild the block
        python3 scripts/plan_calendar.py --check  # exit 1 if the block is stale
"""
import calendar
import csv
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START, END = "<!-- calendar:start -->", "<!-- calendar:end -->"


def ids(text):
    return " ".join(re.findall(r"\bT\d{2}\b", text))


def cell(row):
    """Short label for one day: what Beedy and Bob do, or the joint event."""
    b, o, t, phase = row["beedy"], row["bob"], row["together"], row["phase"]
    if b.startswith("EXAM"):
        return "🎯 **EXAM**"
    if phase == "Own topics (catch-up/review)":
        bi, oi = ids(b), ids(o)
        return f"🗂️ review<br>🐝 {bi or '—'}<br>🅱️ {oi or '—'}"
    if "SWAP QUIZ" in t:
        return "🔀 **Swap quiz**"
    if b.startswith("MOCK EXAM"):
        return "🧪 **Mock exam** (2 h)"
    if "MOCK REVIEW" in t:
        return "🔍 **Mock review**"
    if "rapid-fire" in t:
        return "⚡ Rapid-fire"
    if "weakest" in b:
        return "🩹 Weak-domain Qs" + (" · 🔁 cross-study" if "cross-study" in b else "")
    if "cheat sheet" in b.lower():
        return "📋 Cheat sheet + admin"
    if b == "Rest":
        return "😴 Rest"
    if "Check + correct" in b:
        return "✅ Check notes + cards"
    if phase.startswith("Own topics (batch 1)"):
        return "📚 Cycle 1 study"
    bi, oi = ids(b), ids(o)
    if bi or oi:
        out = f"🐝 {bi or '—'}<br>🅱️ {oi or '—'}"
        if "cross-study" in b:
            out += "<br>🔁 cross-study"
        return out
    if row["date"] == "2026-10-08":
        return "📚 Cycle 1 study"
    return phase


def build():
    rows = {dt.date.fromisoformat(r["date"]): r for r in csv.DictReader(open(ROOT / "data/pair-plan.csv", encoding="utf-8"))}
    first, last = min(rows), max(rows)
    parts = [START, ""]
    month = dt.date(first.year, first.month, 1)
    while month <= last:
        parts += [f"**{month.strftime('%B %Y')}**", "",
                  "| Mon | Tue | Wed | Thu | Fri | Sat | Sun |",
                  "|---|---|---|---|---|---|---|"]
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
            if all(d not in rows for d in week):
                continue
            week = [d if d <= last else None for d in week]
            cells = []
            for d in week:
                if d is None or d.month != month.month:
                    cells.append(" ")
                elif d in rows:
                    cells.append(f"**{d.day}**<br>{cell(rows[d])}")
                else:
                    cells.append(f"{d.day}")
            parts.append("| " + " | ".join(cells) + " |")
        parts.append("")
        month = (month.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    parts += ["🐝 Beedy · 🅱️ Bob · 🗂️ self-review day (no joint session) · ✅ check + correct notes, practice Qs, cards · 🔁 cross-study the partner's notes · 🔀 swap quiz · 🧪 mock · 🎯 exam",
              "",
              "_Generated from `data/pair-plan.csv` by `scripts/plan_calendar.py`. Change the CSV, then re-run the script._",
              "",
              END]
    return "\n".join(parts)


def main(argv):
    text = README.read_text(encoding="utf-8")
    block = build()
    if START not in text:
        sys.exit("README.md has no calendar markers")
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, count=1, flags=re.S)
    if "--check" in argv:
        if new != text:
            print("README calendar is stale: run python3 scripts/plan_calendar.py")
            return 1
        return 0
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("updated README.md calendar")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
