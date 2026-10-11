"""Print one sequence-diagram line per HTTP message, in Mermaid syntax.

    01 Client->>CatC: POST /dna/system/api/v1/auth/token      request  = solid arrow  ->>
    02 CatC-->>Client: 200 OK {"Token": "tok-0001"}          response = dashed arrow -->>

Strip the number and the line is valid inside a Mermaid `sequenceDiagram`.
"""
import threading

_lock = threading.Lock()
_count = 0


def start(title):
    """Start a new flow: print a heading and restart the arrow numbers at 01."""
    global _count
    with _lock:
        _count = 0
        print(f"\n== {title} ==")


def arrow(src, dst, text, reply=False):
    global _count
    with _lock:
        _count += 1
        print(f"{_count:02d} {src}{'-->>' if reply else '->>'}{dst}: {text}")


def note(over, text):
    with _lock:
        print(f"   Note over {over}: {text}")
