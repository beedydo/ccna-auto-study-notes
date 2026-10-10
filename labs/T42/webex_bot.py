"""T42 reference program: a NOC alert bot on the Webex REST API (Python requests).

Start the mock first:   python3 labs/T42/mock_webex.py
Then:                   python3 labs/T42/webex_bot.py
Or both at once:        bash labs/T42/run_lab.sh

Against real Webex: export WEBEX_BASE=https://webexapis.com/v1 and WEBEX_TOKEN=<bot token>.
Step 7 (the simulated @mention) only exists on the mock.
"""
import hashlib
import hmac
import json
import os
import re
import time

import requests

BASE = os.environ.get("WEBEX_BASE", "http://127.0.0.1:18042/v1")       # real: https://webexapis.com/v1
TOKEN = os.environ.get("WEBEX_TOKEN", "T42-mock-bot-token")            # bot token from the developer portal
ROOM_TITLE = "T42-NOC-Alerts"
ONCALL = os.environ.get("ONCALL_EMAIL", "bob@example.com")
HOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "T42-shared-secret")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {TOKEN}",             # every call, every time
                        "Content-Type": "application/json"})


def short_ids(line):
    """Webex IDs are long base64 strings (ciscospark://us/ROOM/<uuid>); print the first 16 chars."""
    return re.sub(r"Y2lzY29zcGFyazovL[\w-]+", lambda m: m.group()[:16] + "...", line)


def call(method, path, show=("id",), **kwargs):
    """One Webex call. Retries once per 429 using Retry-After. Prints a one-line summary."""
    url = path if path.startswith("http") else BASE + path
    while True:
        resp = session.request(method, url, timeout=10, **kwargs)
        if resp.status_code != 429:
            break
        wait = int(resp.headers.get("Retry-After", "1"))
        print(f"<<< 429 Too Many Requests  Retry-After: {wait}  (sleeping, then retry)")
        time.sleep(wait)
    short = url.replace(BASE, "")
    body = resp.json() if resp.content else {}
    picked = {k: body[k] for k in show if k in body} if resp.ok else body.get("message")
    print(short_ids(f"<<< {resp.status_code} {method} {short}  {picked if picked else ''}".rstrip()))
    return resp


def find_or_create_room(title):
    """GET /rooms is paged: follow the Link rel="next" header until there are no more pages."""
    url, params = "/rooms", {"type": "group", "max": 2}
    while url:
        resp = call("GET", url, show=(), params=params)
        for room in resp.json()["items"]:
            print(f"    room: {room['title']}")
            if room["title"] == title:
                return room
        url = resp.links.get("next", {}).get("url")                    # requests parses Link for you
        params = None                                                  # next URL already has the query
    return call("POST", "/rooms", show=("id", "title", "type"), json={"title": title}).json()


def verify_signature(raw_body, signature):
    """Webex signs each webhook POST: X-Spark-Signature = HMAC-SHA1(secret, raw body) as hex."""
    expected = hmac.new(HOOK_SECRET.encode(), raw_body.encode(), hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_webhook(raw_body, headers):
    """What the bot's web server does when Webex POSTs to targetUrl."""
    if not verify_signature(raw_body, headers["X-Spark-Signature"]):
        print("    signature mismatch -> ignore")
        return
    event = json.loads(raw_body)
    print(f"    webhook: resource={event['resource']} event={event['event']} data keys={sorted(event['data'])}")
    msg = call("GET", f"/messages/{event['data']['id']}", show=("personEmail", "text")).json()  # text is NOT in the webhook
    if msg["text"].lower().endswith("status"):
        call("POST", "/messages", show=("id", "parentId"),
             json={"roomId": msg["roomId"], "parentId": msg["id"],      # reply in a thread
                   "markdown": "**3 alerts open**, 0 critical"})


def main():
    print("== 1. Who am I? (token -> identity) ==")
    call("GET", "/people/me", show=("displayName", "emails", "type"))

    print("\n== 2. Find or create the space (GET /rooms paged, POST /rooms) ==")
    room = find_or_create_room(ROOM_TITLE)
    room_id = room["id"]

    print("\n== 3. Add the on-call engineer (POST /memberships) ==")
    call("POST", "/memberships", show=("personEmail", "isModerator"),
         json={"roomId": room_id, "personEmail": ONCALL})
    call("POST", "/memberships", json={"roomId": room_id, "personEmail": ONCALL})   # 409: already in

    print("\n== 4. Post to the space: text, markdown, a file URL (POST /messages) ==")
    call("POST", "/messages", show=("id", "roomType"),
         json={"roomId": room_id, "text": "TY4S-NSWPGNACC01 Eth1/49 down"})
    call("POST", "/messages", show=("id", "roomType"),
         json={"roomId": room_id, "markdown": "**P2** BGP to 10.15.131.2 *Idle*"})
    call("POST", "/messages", show=("id", "files"),
         json={"roomId": room_id, "text": "Runbook attached",
               "files": ["https://example.com/runbooks/TY4S-uplink.pdf"]})
    call("POST", "/messages", show=("id",), json={"roomId": room_id, "text": "4th post in 1 s"})  # 429 -> retry

    print("\n== 5. 1:1 message by email: no room ID needed ==")
    call("POST", "/messages", show=("roomType", "toPersonEmail"),
         json={"toPersonEmail": ONCALL, "text": "You are on call tonight"})

    print("\n== 6. Register a webhook so Webex pushes events to the bot ==")
    hook = call("POST", "/webhooks", show=("name", "resource", "event", "filter"),
                json={"name": "T42-noc-bot", "targetUrl": "https://bot.example.com/webex",
                      "resource": "messages", "event": "created",
                      "filter": f"roomId={room_id}", "secret": HOOK_SECRET}).json()

    print("\n== 7. Bob @mentions the bot; Webex POSTs to targetUrl (simulated by the mock) ==")
    delivery = call("POST", "/_mock/mention", show=(),
                    json={"roomId": room_id, "text": "NOC Alerts status"}).json()
    handle_webhook(delivery["body"], delivery["headers"])

    print("\n== 8. Errors you must recognise ==")
    session.headers["Authorization"] = "Bearer expired-or-wrong"
    call("GET", "/people/me")                                          # 401
    session.headers["Authorization"] = f"Bearer {TOKEN}"
    call("GET", "/rooms/not-a-real-room-id")                           # 404
    call("POST", "/messages", json={"roomId": room_id})                # 400: no text/markdown/files

    print("\n== 9. Clean up what we created ==")
    call("DELETE", f"/webhooks/{hook['id']}")
    call("DELETE", f"/rooms/{room_id}")


if __name__ == "__main__":
    main()
