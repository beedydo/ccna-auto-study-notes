"""T43 contrast: the same "tell me about new messages" job done by POLLING (stdlib only).

Needs platform.py (8143) running. Asks GET /v1/messages every POLL_INTERVAL seconds
for WATCH_SECONDS, while a background "Alice" posts 2 messages. Counts the calls.
"""
import json
import threading
import time
import urllib.request

API = "http://127.0.0.1:8143/v1"
ROOM = "room-poll"
POLL_INTERVAL, WATCH_SECONDS = 1.0, 6


def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method,
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as reply:
        return json.load(reply)


def alice():
    for delay, text in [(2.2, "show version"), (2.5, "show clock")]:
        time.sleep(delay)
        msg = call("POST", "/messages", "alice-token-T43", {"roomId": ROOM, "text": text})
        posted[msg["id"]] = time.monotonic()


posted = {}
seen, calls, empty, lags = set(), 0, 0, []
start = time.monotonic()
threading.Thread(target=alice, daemon=True).start()
while time.monotonic() - start < WATCH_SECONDS:
    items = call("GET", f"/messages?roomId={ROOM}&max=10", "bot-token-T43")["items"]
    calls += 1
    new = [m for m in items if m["id"] not in seen]
    if not new:
        empty += 1
    for m in new:
        seen.add(m["id"])
        lag = time.monotonic() - posted.get(m["id"], time.monotonic())
        lags.append(lag)
        print(f"poll #{calls}: NEW {m['id']} {m['text']!r} (noticed {lag:.1f}s after it was posted)")
    time.sleep(POLL_INTERVAL)

print(f"polling: {calls} GETs in {WATCH_SECONDS}s, {empty} came back with nothing new, "
      f"{len(seen)} events -> {calls / max(len(seen), 1):.1f} calls per event, worst lag {max(lags):.1f}s")
print("webhook: 0 GETs to discover them; 1 POST per event pushed to you (+1 follow-up GET for details)")
