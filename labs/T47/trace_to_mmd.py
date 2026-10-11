"""Turn one flow of the flows.py trace back into a Mermaid sequenceDiagram.

    python3 labs/T47/flows.py > /tmp/trace.txt
    python3 labs/T47/trace_to_mmd.py /tmp/trace.txt 3 > /tmp/flow3.mmd

Proves the trace and the diagram are the same thing: each numbered line becomes one arrow.
"""
import re
import sys

path, flow = sys.argv[1], sys.argv[2]
lines, inside = ["sequenceDiagram", "    autonumber"], False
for line in open(path, encoding="utf-8"):
    if line.startswith("== "):
        inside = line.startswith(f"== Flow {flow} ")
        continue
    if not inside:
        continue
    arrow = re.match(r"\d\d (.*)", line)
    note = re.match(r"\s+Note over (\w+): (.*)", line)
    if arrow:
        lines.append("    " + arrow.group(1).replace(";", ","))   # ';' ends a Mermaid statement
    elif note:
        lines.append(f"    Note over {note.group(1)}: {note.group(2)}")
print("\n".join(lines))
