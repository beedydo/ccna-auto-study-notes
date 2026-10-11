"""Mock 'Webex-style' messaging platform for the T43 webhook lab (Python stdlib only).

Run:  python3 -u labs/T43/platform.py          -> http://127.0.0.1:8143/v1
It is the EVENT SOURCE. It lets an app register a webhook, then, whenever a message
is posted, it POSTs a signed JSON notification to every matching targetUrl and
retries if the receiver doesn't answer 2xx. All tokens and IDs are fake.
"""
import hashlib
import hmac
import itertools
import json
import queue
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

HOST, PORT = "127.0.0.1", 8143
TOKENS = {"bot-token-T43": "person-bot", "alice-token-T43": "person-alice"}
EMAILS = {"person-bot": "netops-bot@example.com", "person-alice": "alice@example.com"}
RESOURCES, EVENTS = {"messages", "rooms", "memberships", "all"}, {"created", "updated", "deleted", "all"}
DELIVERY_TIMEOUT = 3            # seconds the platform waits for the receiver's reply
RETRY_DELAYS = [0.5, 1, 2]      # backoff between attempts: 1 try + 3 retries
DISABLE_AFTER = 6               # consecutive failed attempts -> webhook set to inactive

lock = threading.Lock()
webhooks = {}                   # id -> webhook dict (includes the secret)
messages = []                   # every message ever posted
failures = {}                   # webhook id -> consecutive failed attempts
ids = {"wh": itertools.count(1), "msg": itertools.count(1)}
deliveries = queue.Queue()      # (webhook id, raw body) waiting to be sent


def log(text):
    print(f"[platform] {text}", flush=True)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def public(hook):
    """A webhook as the API returns it: never echo the secret back."""
    return {k: v for k, v in hook.items() if k != "secret"}


def matches(hook, msg):
    if hook["status"] != "active":
        return False
    if hook["resource"] not in ("messages", "all") or hook["event"] not in ("created", "all"):
        return False
    wanted = dict(parse_qsl(hook.get("filter", "")))
    return all(msg.get(key) == value for key, value in wanted.items())


def notify(msg):
    """Event happened: queue one notification per matching webhook (metadata only, no text)."""
    with lock:
        targets = [h for h in webhooks.values() if matches(h, msg)]
        skipped = [h["id"] for h in webhooks.values() if h["status"] != "active"]
    for hook_id in skipped:
        log(f"event {msg['id']}: webhook {hook_id} is inactive, nothing sent")
    if not targets and not skipped:
        log(f"event {msg['id']}: no webhook matches (resource/event/filter), nothing sent")
    for hook in targets:
        envelope = {
            "id": hook["id"], "name": hook["name"], "resource": "messages", "event": "created",
            "filter": hook.get("filter", ""), "orgId": "org-T43", "createdBy": hook["createdBy"],
            "appId": "app-T43", "ownedBy": "creator", "status": "active", "actorId": msg["personId"],
            "data": {k: msg[k] for k in ("id", "roomId", "roomType", "personId", "personEmail", "created")},
        }
        deliveries.put((hook["id"], json.dumps(envelope).encode()))


def sign(secret, body):
    return hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()


def deliver_forever():
    """One worker sends notifications in order, retrying on anything that isn't 2xx."""
    while True:
        hook_id, body = deliveries.get()
        with lock:
            hook = dict(webhooks.get(hook_id, {}))
        msg_id = json.loads(body)["data"]["id"]
        headers = {"Content-Type": "application/json", "User-Agent": "MockPlatform-Webhooks/1.0"}
        if hook.get("secret"):
            headers["X-Spark-Signature"] = sign(hook["secret"], body)
        for attempt in range(1, len(RETRY_DELAYS) + 2):
            if hook.get("status") != "active":
                log(f"POST {hook['targetUrl']} ({msg_id}) dropped: webhook {hook_id} is inactive")
                break
            log(f"POST {hook['targetUrl']} ({msg_id}) attempt {attempt}")
            request = urllib.request.Request(hook["targetUrl"], data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=DELIVERY_TIMEOUT) as reply:
                    code = reply.status
            except urllib.error.HTTPError as err:          # receiver answered, but not 2xx
                code = err.code
            except urllib.error.URLError as err:           # nothing listening
                code = f"no connection ({err.reason.strerror if hasattr(err.reason, 'strerror') else err.reason})"
            except TimeoutError:                           # receiver too slow
                code = f"no reply within {DELIVERY_TIMEOUT}s"
            if isinstance(code, int) and 200 <= code < 300:
                log(f"  <- {code}: delivered")
                with lock:
                    failures[hook_id] = 0
                break
            with lock:
                failures[hook_id] = failures.get(hook_id, 0) + 1
                failed = failures[hook_id]
                if failed >= DISABLE_AFTER:
                    webhooks[hook_id]["status"] = "inactive"
                    hook["status"] = "inactive"
            if hook["status"] == "inactive":
                log(f"  <- {code}: {failed} failures in a row, webhook {hook_id} DISABLED")
                break
            if attempt <= len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt - 1]
                log(f"  <- {code}: retry in {delay}s")
                time.sleep(delay)
            else:
                log(f"  <- {code}: gave up on {msg_id}")
        deliveries.task_done()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockPlatform/1.0"

    def log_message(self, *args):
        pass

    def send(self, code, body=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def person(self):
        auth = self.headers.get("Authorization", "")
        person = TOKENS.get(auth[len("Bearer "):]) if auth.startswith("Bearer ") else None
        if person is None:
            self.send(401, {"message": "The request requires a valid access token set in the Authorization request header."})
        return person

    def json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def do_GET(self):
        person = self.person()
        if person is None:
            return
        parts = urlsplit(self.path)
        path, params = parts.path, dict(parse_qsl(parts.query))
        if path == "/v1/webhooks":
            with lock:
                return self.send(200, {"items": [public(h) for h in webhooks.values() if h["createdBy"] == person]})
        if path == "/v1/messages":                                    # what a polling client calls
            room = params.get("roomId")
            if not room:
                return self.send(400, {"message": "roomId is required"})
            with lock:
                items = [m for m in reversed(messages) if m["roomId"] == room][: int(params.get("max", 50))]
            return self.send(200, {"items": items})
        if path.startswith("/v1/messages/"):                          # the follow-up GET
            with lock:
                found = [m for m in messages if m["id"] == path.rsplit("/", 1)[1]]
            return self.send(200, found[0]) if found else self.send(404, {"message": "message not found"})
        return self.send(404, {"message": "unknown path"})

    def do_POST(self):
        person = self.person()
        if person is None:
            return
        body = self.json_body()
        if body is None:
            return self.send(400, {"message": "body is not valid JSON"})
        if self.path == "/v1/webhooks":                               # registration
            missing = [k for k in ("name", "targetUrl", "resource", "event") if not body.get(k)]
            if missing:
                return self.send(400, {"message": f"missing required field(s): {', '.join(missing)}"})
            if body["resource"] not in RESOURCES or body["event"] not in EVENTS:
                return self.send(400, {"message": f"unsupported resource/event: {body['resource']}/{body['event']}"})
            if not body["targetUrl"].startswith(("http://", "https://")):
                return self.send(400, {"message": "targetUrl must be an http(s) URL"})
            with lock:
                hook_id = f"wh-{next(ids['wh']):04d}"
                hook = {"id": hook_id, "name": body["name"], "targetUrl": body["targetUrl"],
                        "resource": body["resource"], "event": body["event"], "filter": body.get("filter", ""),
                        "secret": body.get("secret", ""), "status": "active", "createdBy": person, "created": now()}
                webhooks[hook_id] = hook
            log(f"registered {hook_id}: {hook['resource']}/{hook['event']} filter={hook['filter']!r} -> {hook['targetUrl']}")
            return self.send(200, public(hook))
        if self.path == "/v1/messages":                               # a user posts: this IS the event
            with lock:
                msg = {"id": f"msg-{next(ids['msg']):04d}", "roomId": body.get("roomId", ""), "roomType": "group",
                       "text": body.get("text", ""), "personId": person, "personEmail": EMAILS[person], "created": now()}
                messages.append(msg)
            log(f"event: {msg['personEmail']} posted {msg['id']} in {msg['roomId']}")
            notify(msg)
            return self.send(200, msg)
        return self.send(404, {"message": "unknown path"})

    def do_DELETE(self):
        if self.person() is None:
            return
        hook_id = self.path.rsplit("/", 1)[1]
        with lock:
            found = webhooks.pop(hook_id, None)
        return self.send(204) if found else self.send(404, {"message": "webhook not found"})


if __name__ == "__main__":
    threading.Thread(target=deliver_forever, daemon=True).start()
    log(f"listening on http://{HOST}:{PORT}/v1")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
