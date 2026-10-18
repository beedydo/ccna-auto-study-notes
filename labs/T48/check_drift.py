#!/usr/bin/env python3
"""T48: check that every request in auth_side_by_side.py still matches the note that owns it.

For each step, its `marker` (a URL path, header or parameter) must appear in BOTH the request the
program builds and bob/<note>-*.md. If a platform note changes its endpoint or header, or the
program drifts from the note, this fails and T48 needs the same edit.

  python3 labs/T48/check_drift.py

Exit code 0 = all markers found, 1 = at least one missing.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth_side_by_side import STEPS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def note_text(note_id):
    paths = glob.glob(os.path.join(ROOT, "bob", f"{note_id}-*.md"))
    return open(paths[0], encoding="utf-8").read() if paths else None


def rendered(step):
    p = step.prepared
    body = p.body if isinstance(p.body, str) else (p.body or b"").decode()
    headers = "\n".join(f"{k}: {v}" for k, v in p.headers.items())
    return f"{p.method} {p.url}\n{headers}\n{body}"


def main():
    cache, missing = {}, 0
    for s in STEPS:
        if s.note not in cache:
            cache[s.note] = note_text(s.note)
        text = cache[s.note]
        if text is None:
            print(f"✗ {s.label:<44} no bob/{s.note}-*.md")
            missing += 1
        elif s.marker not in rendered(s):
            print(f"✗ {s.label:<44} the program's request has no {s.marker!r}")
            missing += 1
        elif s.marker not in text:
            print(f"✗ {s.label:<44} {s.note} has no {s.marker!r}")
            missing += 1
        else:
            print(f"✓ {s.label:<44} {s.note} has {s.marker!r}")
    print(f"\n{len(STEPS) - missing}/{len(STEPS)} requests match their platform note.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
