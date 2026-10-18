#!/usr/bin/env python3
"""Insert or refresh the "Contents" block in topic notes.

The block sits between <!-- toc:start --> and <!-- toc:end --> markers,
directly under the title line (and under the overview image, if the note has one).
It links every `##` section and every `### TXX.NN` concept, using GitHub's
heading-anchor rules so the links work on GitHub and in VS Code preview.

Usage:
  python3 scripts/toc.py bee/T07-rest-fundamentals-http-codes.md   # one note
  python3 scripts/toc.py bee/*.md                                  # many notes
  python3 scripts/toc.py --check bee/*.md                          # exit 1 if any block is missing or stale
"""
import re
import sys
import unicodedata
from pathlib import Path

START, END = "<!-- toc:start -->", "<!-- toc:end -->"
CONCEPT = re.compile(r"^### (T\d{2}\.\d{2}) · (.+)$")


def github_anchor(heading, seen):
    """Lowercase, drop punctuation except - and _, spaces to -, de-duplicate with -1, -2 ..."""
    text = re.sub(r"`([^`]*)`", r"\1", heading)          # inline code keeps its text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links keep their text
    text = text.strip().lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "-_" or ch == " " or cat[0] in "LN":
            out.append(ch)
    slug = "".join(out).replace(" ", "-")
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def build_toc(text):
    """Return the contents block for a note, computed from its headings outside code fences."""
    seen = {}
    sections = []          # (title, anchor, [concept entries])
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("#"):
            continue
        m = re.match(r"^(#{1,6}) (.+?)\s*$", line)
        if not m:
            continue
        level, title = len(m.group(1)), m.group(2)
        anchor = github_anchor(title, seen)
        if level == 2:
            sections.append([title, anchor, []])
        elif level == 3 and sections:
            c = CONCEPT.match(line)
            if c:
                sections[-1][2].append((c.group(1), c.group(2), anchor))

    lines = [START, "", "**Contents**", ""]
    for title, anchor, concepts in sections:
        lines.append(f"- [{title}](#{anchor})")
        if concepts:
            lines.append("  - " + " · ".join(f"[{cid}](#{a}) {area}" for cid, area, a in concepts))
    lines += ["", END]
    return "\n".join(lines)


def insert_or_refresh(text):
    block = build_toc(text)
    if START in text:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, count=1, flags=re.S)
    # Insert after the overview image + caption if present, else after the "> Owner" line.
    lines = text.split("\n")
    owner = next(i for i, l in enumerate(lines) if l.startswith("> Owner:"))
    at = owner + 1
    j = at
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    if j < len(lines) and lines[j].startswith("![") and "00-overview" in lines[j]:
        k = j + 1
        while k < len(lines) and lines[k].strip() == "":
            k += 1
        if k < len(lines) and lines[k].startswith("*"):
            at = k + 1
        else:
            at = j + 1
    lines[at:at] = ["", block]
    return "\n".join(lines)


def main(argv):
    check = "--check" in argv
    paths = [Path(a) for a in argv if a != "--check"]
    stale = []
    for p in paths:
        if not re.match(r"T\d{2}-", p.name):
            continue  # not a topic note (e.g. bee/TODO.md)
        text = p.read_text(encoding="utf-8")
        new = insert_or_refresh(text)
        if new != text:
            if check:
                stale.append(str(p))
            else:
                p.write_text(new, encoding="utf-8")
                print(f"updated {p}")
    if check and stale:
        print("contents block missing or stale:\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
