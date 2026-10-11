"""T43 driver: register a webhook, then make events happen (Python stdlib only).

Needs platform.py (8143) and receiver.py (8144) running; run_lab.sh starts both.
Plays two roles:
  * the bot developer: POST /v1/webhooks once (registration)
  * a user, Alice: posts messages, which are the events the platform pushes
"""
import json
import os
import time
import urllib.error
import urllib.request

API = os.environ.get("PLATFORM_API", "http://127.0.0.1:8143/v1")
BOT_TOKEN, ALICE_TOKEN = "bot-token-T43", "alice-token-T43"
SECRET = os.environ.get("REGISTER_SECRET", "s3cr3t-T43-demo")
ROOM = "room-netops"


def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method,
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as reply:
            return reply.status, json.loads(reply.read() or b"null")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"null")


def main():
    print("== 1. Register the webhook (one API call, made by the bot developer) ==")
    status, hook = call("POST", "/webhooks", BOT_TOKEN, {
        "name": "netops room commands",
        "targetUrl": "http://127.0.0.1:8144/webhook",
        "resource": "messages",
        "event": "created",
        "filter": f"roomId={ROOM}",
        "secret": SECRET,
    })
    print(f"POST /v1/webhooks -> {status}")
    print(json.dumps(hook, indent=2))

    print("\n== 1b. A bad registration (no targetUrl) ==")
    print("POST /v1/webhooks ->", *call("POST", "/webhooks", BOT_TOKEN,
                                         {"name": "broken", "resource": "messages", "event": "created"}))

    print("\n== 2. Events happen: Alice posts 3 messages (2 in the filtered room) ==")
    for room, text in [(ROOM, "show ip interface brief"), ("room-random", "lunch?"), (ROOM, "thanks bot")]:
        status, msg = call("POST", "/messages", ALICE_TOKEN, {"roomId": room, "text": text})
        print(f"POST /v1/messages {room!r} {text!r} -> {status} {msg['id']}")
        time.sleep(0.3)
    time.sleep(float(os.environ.get("SETTLE_SECONDS", "1.5")))   # let deliveries (and retries) finish

    print("\n== 3. Webhook status after the run ==")
    status, body = call("GET", "/webhooks", BOT_TOKEN)
    for item in body["items"]:
        print(f"GET /v1/webhooks -> {item['id']} status={item['status']}  (secret not echoed: {'secret' not in item})")


if __name__ == "__main__":
    main()
