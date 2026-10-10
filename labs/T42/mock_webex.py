"""Mock Webex REST API + mock RoomOS device xAPI for the T42 lab (Python stdlib only).

Run:  python3 labs/T42/mock_webex.py     -> http://127.0.0.1:18042
      cloud API under   /v1/...          (stands in for https://webexapis.com/v1)
      device xAPI under /getxml, /putxml (stands in for https://<device-ip>/...)

Response shapes follow the Webex REST API reference (developer.webex.com) and the
RoomOS xAPI HTTP docs. IDs, tokens and people are fake. Nothing leaves your laptop.

What it imitates:
  - auth:        Authorization: Bearer <token>, else 401 (cloud);  Basic auth, else 401 (device)
  - token kinds: a bot token (messaging scopes only) and an integration token that also
                 has spark:xapi_statuses / spark:xapi_commands. Bot token on /xapi -> 403
  - rooms:       GET /rooms (?type=, ?max= with Link rel="next"), POST, GET/{id}, DELETE/{id}
  - messages:    POST /messages (roomId | toPersonEmail, text | markdown, parentId), GET /{id}
                 rate limit: 3 POST /messages per 1 s per token per room -> 429 + Retry-After: 1
  - memberships: POST /memberships (roomId + personEmail), 409 if already a member
  - webhooks:    POST/GET/DELETE /webhooks; the envelope carries IDs only, never the text
  - devices:     GET /devices, GET /xapi/status?deviceId=&name=, POST /xapi/command/{name}
  - mock only:   POST /v1/_mock/mention -> "Bob mentions the bot"; returns the request
                 Webex would POST to your targetUrl (headers + raw body), signed with
                 HMAC-SHA1 of the body using the webhook secret (X-Spark-Signature)
"""
import base64
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

HOST, PORT = "127.0.0.1", int(os.environ.get("MOCK_PORT", "18042"))
BOT_TOKEN = os.environ.get("MOCK_BOT_TOKEN", "T42-mock-bot-token")
INTEGRATION_TOKEN = os.environ.get("MOCK_INTEGRATION_TOKEN", "T42-mock-integration-token")
DEVICE_USER = os.environ.get("MOCK_DEVICE_USER", "integrator")
DEVICE_PASS = os.environ.get("MOCK_DEVICE_PASS", "integrator")
ORG = "Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi9UNDItT1JH"


def wid(kind):
    """Webex-style ID: base64 of ciscospark://us/<KIND>/<uuid>, padding stripped."""
    raw = f"ciscospark://us/{kind}/{uuid.uuid4()}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + "000Z"


PEOPLE = {
    BOT_TOKEN: {"id": wid("PEOPLE"), "emails": ["noc-alerts@webex.bot"], "displayName": "NOC Alerts",
                "nickName": "NOC Alerts", "orgId": ORG, "type": "bot", "created": "2026-10-01T09:00:00.000Z"},
    INTEGRATION_TOKEN: {"id": wid("PEOPLE"), "emails": ["bob@example.com"], "displayName": "Bob",
                        "nickName": "Bob", "orgId": ORG, "type": "person", "created": "2025-03-14T02:10:00.000Z"},
}
SCOPES = {BOT_TOKEN: {"spark:messages_write", "spark:rooms_write", "spark:memberships_write"},
          INTEGRATION_TOKEN: {"spark:messages_write", "spark:rooms_write", "spark:memberships_write",
                              "spark:xapi_statuses", "spark:xapi_commands"}}
BOB = PEOPLE[INTEGRATION_TOKEN]


def _room(title, rtype="group"):
    rid = wid("ROOM")
    return rid, {"id": rid, "title": title, "type": rtype, "isLocked": False, "lastActivity": now(),
                 "creatorId": BOB["id"], "created": "2026-09-20T01:00:00.000Z", "ownerId": ORG,
                 "isPublic": False, "isReadOnly": False}


ROOMS, MEMBERS, MESSAGES, WEBHOOKS = {}, {}, {}, {}
for t in ("SG-NOC Shift", "TY4S Cutover", "Change Board"):
    rid, r = _room(t)
    ROOMS[rid] = r
    MEMBERS[rid] = {PEOPLE[BOT_TOKEN]["emails"][0], BOB["emails"][0]}

DEVICE = {"id": wid("DEVICE"), "displayName": "SG-HQ Board Room", "workspaceId": wid("PLACE"),
          "product": "Cisco Room Kit Pro", "type": "roomdesk", "tags": [], "ip": "10.10.20.70",
          "mac": "00:1B:D5:12:34:56", "serial": "FOC2417N0AB", "software": "RoomOS 11.20.1.5",
          "connectionStatus": "connected", "capabilities": ["xapi"], "permissions": ["xapi"],
          "orgId": ORG}
DEVICE_STATE = {"Audio.Volume": 50, "Standby.State": "Off", "Audio.DefaultVolume": 50}
post_times = {}


def error(message, code_hint=""):
    return {"message": message, "errors": [{"description": message}],
            "trackingId": f"ROUTER_{uuid.uuid4().hex[:8].upper()}{code_hint}"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockWebex/1.0"

    def log_message(self, *args):
        pass

    # ---------- helpers ----------
    def send(self, code, body=None, headers=None, ctype="application/json"):
        data = b""
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return self._raw

    def token(self):
        auth = self.headers.get("Authorization", "")
        tok = auth[len("Bearer "):] if auth.startswith("Bearer ") else None
        return tok if tok in PEOPLE else None

    def need_token(self):
        tok = self.token()
        if not tok:
            self.send(401, error("The request requires a valid access token set in the Authorization request header."))
        return tok

    def device_auth_ok(self):
        expected = "Basic " + base64.b64encode(f"{DEVICE_USER}:{DEVICE_PASS}".encode()).decode()
        if self.headers.get("Authorization") != expected:
            self.send(401, "<html><body>401 Unauthorized</body></html>",
                      {"WWW-Authenticate": 'Basic realm="Cisco Codec"'}, "text/html")
            return False
        return True

    # ---------- dispatch ----------
    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_DELETE(self):
        self.route("DELETE")

    def route(self, method):
        n = int(self.headers.get("Content-Length", 0))       # always drain the body first, so an
        self._raw = self.rfile.read(n) if n else b""          # early 401/429 keeps keep-alive clean
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        p = url.path
        if p in ("/getxml", "/putxml"):
            return self.device(method, p, q)
        if not p.startswith("/v1/"):
            return self.send(404, error("Not found"))
        p = p[3:]
        if p == "/_mock/mention" and method == "POST":
            return self.mock_mention()
        tok = self.need_token()
        if not tok:
            return
        me = PEOPLE[tok]
        if p == "/people/me" and method == "GET":
            return self.send(200, me)
        if p == "/rooms":
            return self.list_rooms(q, me) if method == "GET" else self.create_room(me)
        m = re.fullmatch(r"/rooms/([\w-]+)", p)
        if m:
            return self.one_room(method, m.group(1))
        if p == "/memberships" and method == "POST":
            return self.add_member()
        if p == "/messages" and method == "POST":
            return self.post_message(tok, me)
        m = re.fullmatch(r"/messages/([\w-]+)", p)
        if m and method == "GET":
            msg = MESSAGES.get(m.group(1))
            return self.send(200, msg) if msg else self.send(404, error("Message not found"))
        if p == "/webhooks":
            if method == "GET":
                return self.send(200, {"items": list(WEBHOOKS.values())})
            return self.create_webhook(me)
        m = re.fullmatch(r"/webhooks/([\w-]+)", p)
        if m and method == "DELETE":
            return self.send(204) if WEBHOOKS.pop(m.group(1), None) else self.send(404, error("Webhook not found"))
        if p == "/devices" and method == "GET":
            return self.send(200, {"items": [DEVICE]})
        if p.startswith("/xapi/"):
            return self.cloud_xapi(method, p, q, tok)
        self.send(404, error(f"{method} {p} is not a mocked endpoint"))

    # ---------- rooms ----------
    def list_rooms(self, q, me):
        mine = [r for rid, r in ROOMS.items() if me["emails"][0] in MEMBERS.get(rid, set())]
        if q.get("type"):
            mine = [r for r in mine if r["type"] == q["type"]]
        mx = int(q.get("max", 100))
        start = int(q.get("cursor", 0))
        page = mine[start:start + mx]
        headers = {}
        if start + mx < len(mine):
            nq = {**q, "cursor": start + mx}
            headers["Link"] = f'<http://{HOST}:{PORT}/v1/rooms?{urlencode(nq)}>; rel="next"'
        self.send(200, {"items": page}, headers)

    def create_room(self, me):
        data = json.loads(self.body() or b"{}")
        if not data.get("title"):
            return self.send(400, error("title: may not be empty"))
        rid, room = _room(data["title"])
        room["creatorId"] = me["id"]
        ROOMS[rid] = room
        MEMBERS[rid] = {me["emails"][0]}
        self.send(200, room)

    def one_room(self, method, rid):
        if rid not in ROOMS:
            return self.send(404, error("Could not find a room with provided ID."))
        if method == "DELETE":
            ROOMS.pop(rid)
            MEMBERS.pop(rid, None)
            return self.send(204)
        self.send(200, ROOMS[rid])

    def add_member(self):
        data = json.loads(self.body() or b"{}")
        rid, email = data.get("roomId"), data.get("personEmail")
        if rid not in ROOMS:
            return self.send(404, error("Could not find a room with provided ID."))
        if email in MEMBERS[rid]:
            return self.send(409, error("Person is already in the room."))
        MEMBERS[rid].add(email)
        self.send(200, {"id": wid("MEMBERSHIP"), "roomId": rid, "personId": wid("PEOPLE"),
                        "personEmail": email, "personDisplayName": email.split("@")[0].title(),
                        "personOrgId": ORG, "isModerator": bool(data.get("isModerator", False)),
                        "isMonitor": False, "roomType": ROOMS[rid]["type"], "created": now()})

    # ---------- messages ----------
    def post_message(self, tok, me):
        data = json.loads(self.body() or b"{}")
        if not (data.get("text") or data.get("markdown") or data.get("files")):
            return self.send(400, error("Message must contain text, markdown or files."))
        bucket = (tok, data.get("roomId") or data.get("toPersonEmail"))
        recent = [t for t in post_times.get(bucket, []) if time.time() - t < 1]
        if len(recent) >= 3:
            post_times[bucket] = recent
            return self.send(429, error("Too many requests."), {"Retry-After": "1"})
        post_times[bucket] = recent + [time.time()]
        if data.get("roomId"):
            rid = data["roomId"]
            if rid not in ROOMS:
                return self.send(404, error("Could not find a room with provided ID."))
        elif data.get("toPersonEmail"):
            rid = next((k for k, r in ROOMS.items() if r["type"] == "direct"
                        and MEMBERS[k] == {me["emails"][0], data["toPersonEmail"]}), None)
            if not rid:                       # first 1:1 message creates the direct room
                rid, room = _room(data["toPersonEmail"], "direct")
                ROOMS[rid] = room
                MEMBERS[rid] = {me["emails"][0], data["toPersonEmail"]}
        else:
            return self.send(400, error("roomId, toPersonId or toPersonEmail is required."))
        msg = {"id": wid("MESSAGE"), "roomId": rid, "roomType": ROOMS[rid]["type"],
               "text": data.get("text") or re.sub(r"[*_`]", "", data.get("markdown", "")),
               "personId": me["id"], "personEmail": me["emails"][0], "created": now()}
        for key in ("markdown", "parentId", "files"):
            if data.get(key):
                msg[key] = data[key]
        if data.get("toPersonEmail"):
            msg["toPersonEmail"] = data["toPersonEmail"]
        MESSAGES[msg["id"]] = msg
        self.send(200, msg)

    # ---------- webhooks ----------
    def create_webhook(self, me):
        data = json.loads(self.body() or b"{}")
        missing = [k for k in ("name", "targetUrl", "resource", "event") if not data.get(k)]
        if missing:
            return self.send(400, error(f"missing: {', '.join(missing)}"))
        hook = {"id": wid("WEBHOOK"), "name": data["name"], "targetUrl": data["targetUrl"],
                "resource": data["resource"], "event": data["event"], "orgId": ORG,
                "createdBy": me["id"], "appId": wid("APPLICATION"), "ownedBy": "creator",
                "status": "active", "created": now()}
        for key in ("filter", "secret"):
            if data.get(key):
                hook[key] = data[key]
        WEBHOOKS[hook["id"]] = hook
        self.send(200, hook)

    def mock_mention(self):
        """Mock only: Bob @mentions the bot in a room; return what Webex would POST to targetUrl."""
        data = json.loads(self.body() or b"{}")
        rid = data["roomId"]
        bot = PEOPLE[BOT_TOKEN]
        msg = {"id": wid("MESSAGE"), "roomId": rid, "roomType": "group", "text": data["text"],
               "personId": BOB["id"], "personEmail": BOB["emails"][0],
               "mentionedPeople": [bot["id"]], "created": now()}
        MESSAGES[msg["id"]] = msg
        hook = next(h for h in WEBHOOKS.values() if h["resource"] == "messages")
        envelope = {k: hook[k] for k in ("id", "name", "targetUrl", "resource", "event", "orgId",
                                          "createdBy", "appId", "ownedBy", "status", "created")}
        envelope["filter"] = hook.get("filter", "")
        envelope["actorId"] = BOB["id"]
        envelope["data"] = {k: msg[k] for k in ("id", "roomId", "roomType", "personId",
                                                 "personEmail", "mentionedPeople", "created")}
        raw = json.dumps(envelope)
        sig = hmac.new(hook.get("secret", "").encode(), raw.encode(), hashlib.sha1).hexdigest()
        self.send(200, {"POST": hook["targetUrl"],
                        "headers": {"Content-Type": "application/json", "X-Spark-Signature": sig},
                        "body": raw})

    # ---------- cloud xAPI ----------
    def cloud_xapi(self, method, p, q, tok):
        need = "spark:xapi_statuses" if p == "/xapi/status" else "spark:xapi_commands"
        if need not in SCOPES[tok]:
            return self.send(403, error(f"Missing required scope: {need}"))
        if p == "/xapi/status" and method == "GET":
            if q.get("deviceId") != DEVICE["id"]:
                return self.send(404, error("Device not found"))
            name = q.get("name", "")
            if name not in DEVICE_STATE:
                return self.send(400, error(f"Unknown status path: {name}"))
            top, leaf = name.split(".")
            return self.send(200, {"deviceId": DEVICE["id"], "result": {top: {leaf: DEVICE_STATE[name]}}})
        m = re.fullmatch(r"/xapi/command/([\w.]+)", p)
        if m and method == "POST":
            data = json.loads(self.body() or b"{}")
            if data.get("deviceId") != DEVICE["id"]:
                return self.send(404, error("Device not found"))
            name, args = m.group(1), data.get("arguments", {})
            if name == "Audio.Volume.Set":
                DEVICE_STATE["Audio.Volume"] = int(args["Level"])
            elif name == "Standby.Deactivate":
                DEVICE_STATE["Standby.State"] = "Off"
            else:
                return self.send(400, error(f"Unknown command: {name}"))
            return self.send(200, {"deviceId": DEVICE["id"], "arguments": args, "result": {}})
        self.send(404, error("Not found"))

    # ---------- on-device xAPI over HTTP ----------
    def device(self, method, p, q):
        if not self.device_auth_ok():
            return
        head = '<?xml version="1.0"?>\n'
        if p == "/getxml" and method == "GET":
            loc = q.get("location", "")
            m = re.fullmatch(r"/(Status|Configuration)/(\w+)/(\w+)", loc)
            key = f"{m.group(2)}.{m.group(3)}" if m else ""
            if key not in DEVICE_STATE:
                return self.send(400, head + "<Error>Unknown location</Error>", ctype="text/xml")
            kind, a, b = m.groups()
            xml = (f'{head}<{kind} product="Cisco Codec" version="ce11.20.1.5" apiVersion="4">\n'
                   f"  <{a}>\n    <{b}>{DEVICE_STATE[key]}</{b}>\n  </{a}>\n</{kind}>")
            return self.send(200, xml, ctype="text/xml")
        if p == "/putxml" and method == "POST":
            doc = self.body().decode()
            if self.headers.get("Content-Type", "").split(";")[0] != "text/xml":
                return self.send(415, head + "<Error>Content-Type must be text/xml</Error>", ctype="text/xml")
            m = re.fullmatch(r"\s*<Command><Audio><Volume><Set><Level>(\d+)</Level></Set></Volume></Audio></Command>\s*", doc)
            if m:
                DEVICE_STATE["Audio.Volume"] = int(m.group(1))
                return self.send(200, head + '<Command><AudioVolumeSetResult status="OK"/></Command>', ctype="text/xml")
            m = re.fullmatch(r"\s*<Configuration><Audio><DefaultVolume>(\d+)</DefaultVolume></Audio></Configuration>\s*", doc)
            if m:
                DEVICE_STATE["Audio.DefaultVolume"] = int(m.group(1))
                return self.send(200, head + "<Configuration/>", ctype="text/xml")
            return self.send(400, head + '<Command><Result status="Error"><Reason>Unknown command</Reason></Result></Command>',
                             ctype="text/xml")
        self.send(405, "", {"Allow": "GET" if p == "/getxml" else "POST"})


if __name__ == "__main__":
    print(f"Mock Webex API on http://{HOST}:{PORT}/v1  (device xAPI on /getxml, /putxml)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
