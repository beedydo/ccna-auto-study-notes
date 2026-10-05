#!/usr/bin/env python3
"""Print study progress from note front matter vs dates in data/topics.csv.

Usage:
  python3 scripts/progress.py            # table for both owners
  python3 scripts/progress.py --owner Bob
  python3 scripts/progress.py --readme   # also rewrite the progress block in README.md
"""
import argparse, csv, datetime as dt, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORDER = ["not-started", "drafted", "verified", "taught"]


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.split("#")[0].strip().strip('"')
    boxes = re.findall(r"- \[( |x)\] ", text)
    fm["_done"] = sum(1 for b in boxes if b == "x")
    fm["_total"] = len(boxes)
    return fm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner")
    ap.add_argument("--readme", action="store_true")
    a = ap.parse_args()
    today = dt.date.today().isoformat()
    rows = list(csv.DictReader(open(ROOT / "data/topics.csv", encoding="utf-8")))
    out = ["| ID | Topic | Owner | Status | Checklist | Learn by | Flag |", "|---|---|---|---|---|---|---|"]
    summary = {}
    for r in rows:
        if a.owner and r["owner"].lower() != a.owner.lower():
            continue
        p = ROOT / r["note_path"]
        fm = front_matter(p) if p.exists() else {"status": "missing", "_done": 0, "_total": 0}
        st = fm.get("status", "not-started")
        flag = ""
        if st in ("not-started", "missing") and r["learn_by"] and r["learn_by"] < today:
            flag = "OVERDUE"
        out.append(f"| {r['id']} | {r['title']} | {r['owner']} | {st} | {fm['_done']}/{fm['_total']} | {r['learn_by']} | {flag} |")
        s = summary.setdefault(r["owner"], {k: 0 for k in ORDER + ["missing"]})
        s[st] = s.get(st, 0) + 1
    print(f"Progress as of {today}\n")
    for owner, s in summary.items():
        print(f"- {owner}: " + ", ".join(f"{k} {v}" for k, v in s.items() if v))
    print()
    table = "\n".join(out)
    print(table)
    if a.readme:
        readme = ROOT / "README.md"
        txt = readme.read_text(encoding="utf-8")
        block = f"<!-- progress:start -->\n_Updated {today} by scripts/progress.py_\n\n{table}\n<!-- progress:end -->"
        txt = re.sub(r"<!-- progress:start -->.*?<!-- progress:end -->", block, txt, flags=re.S)
        readme.write_text(txt, encoding="utf-8")
        print("\nREADME.md progress block updated.")


if __name__ == "__main__":
    main()
