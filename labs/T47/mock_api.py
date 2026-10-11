"""Mock APIs for T47: a Catalyst Center (DNA Center)-shaped controller and a Webex-shaped messaging API.

Run alone:  python3 labs/T47/mock_api.py        -> http://127.0.0.1:8147
Normally flows.py imports it and starts it in a thread (one process, one port).
Python stdlib only. Shapes copy the real APIs; values are fake.

Catalyst Center shape
  POST /dna/system/api/v1/auth/token            Basic devnet:cisco123  -> 200 {"Token": ...} | 401
  GET  /dna/intent/api/v1/network-device        X-Auth-Token; ?offset=1&limit=N (offset is 1-based)
                                                -> 200 {"response": [...]} | 401 (token missing/expired)
  POST /dna/intent/api/v1/network-device-poller/cli/read-request   -> 202 {"response": {"taskId": ...}}
  GET  /dna/intent/api/v1/task/{taskId}         -> 200; "endTime" appears after JOB_POLLS polls
  GET  /dna/intent/api/v1/file/{fileId}         -> 200 command output
  expire_tokens() makes every issued token invalid (stands in for the real expiry time).

Webex shape (Authorization: Bearer <token>)
  POST /v1/webhooks       {"name", "targetUrl", "resource", "event"} -> 200 webhook object
  POST /v1/messages       {"roomId", "text"} -> 200; then the server POSTs a webhook to every matching targetUrl
  GET  /v1/messages/{id}  -> 200 full message (the webhook payload carries only the IDs)
"""
import base64
import json
import re
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8147
USER, PASSWORD = "devnet", "cisco123"
WEBEX_TOKEN = "bot-token-T47"
JOB_POLLS = 2           # task polls that still show "running" before endTime appears

DEVICES = [{"id": f"dev-{n}", "hostname": h, "managementIpAddress": f"10.10.20.{80 + n}"}
           for n, h in enumerate(["edge1", "edge2", "core1", "core2", "access1"], start=1)]

state = {"tokens": {}, "token_seq": 0, "tasks": {}, "files": {}, "webhooks": [], "messages": {}}
lock = threading.Lock()
extra_routes = {}       # path -> handler(request) ; lets flows.py mount the app's webhook listener on 8147


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

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

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    # ---------- auth helpers ----------
    def catc_token_ok(self):
        token = self.headers.get("X-Auth-Token")
        with lock:
            return state["tokens"].get(token) == "valid"

    def webex_ok(self):
        return self.headers.get("Authorization") == f"Bearer {WEBEX_TOKEN}"

    # ---------- routing ----------
    def do_GET(self):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        if path == "/health":
            return self.send(200, {"status": "ok"})
        if path.startswith("/dna/intent/"):
            if not self.catc_token_ok():
                return self.send(401, {"error": "Unauthorized: token missing or expired"})
            if path == "/dna/intent/api/v1/network-device":
                offset, limit = int(params.get("offset", 1)), int(params.get("limit", 500))
                return self.send(200, {"response": DEVICES[offset - 1:offset - 1 + limit], "version": "1.0"})
            m = re.fullmatch(r"/dna/intent/api/v1/task/([\w-]+)", path)
            if m:
                return self.get_task(m.group(1))
            m = re.fullmatch(r"/dna/intent/api/v1/file/([\w-]+)", path)
            if m and m.group(1) in state["files"]:
                return self.send(200, state["files"][m.group(1)])
        m = re.fullmatch(r"/v1/messages/([\w-]+)", path)
        if m:
            if not self.webex_ok():
                return self.send(401, {"message": "The request requires a valid access token."})
            msg = state["messages"].get(m.group(1))
            return self.send(200, msg) if msg else self.send(404, {"message": "not found"})
        return self.send(404, {"error": "unknown path"})

    def do_POST(self):
        path = self.path.partition("?")[0]
        if path in extra_routes:
            return extra_routes[path](self)
        if path == "/dna/system/api/v1/auth/token":
            expected = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
            if self.headers.get("Authorization") != expected:
                return self.send(401, {"error": "bad credentials"})
            with lock:
                state["token_seq"] += 1
                token = f"tok-{state['token_seq']:04d}"
                state["tokens"][token] = "valid"
            return self.send(200, {"Token": token})
        if path == "/dna/intent/api/v1/network-device-poller/cli/read-request":
            if not self.catc_token_ok():
                return self.send(401, {"error": "Unauthorized: token missing or expired"})
            commands = self.body().get("commands", [])
            with lock:
                n = len(state["tasks"]) + 1
                task_id, file_id = f"task-{n:03d}", f"file-{n:03d}"
                state["tasks"][task_id] = {"polls": 0, "fileId": file_id, "commands": commands}
            return self.send(202, {"response": {"taskId": task_id, "url": f"/api/v1/task/{task_id}"}, "version": "1.0"})
        if path in ("/v1/webhooks", "/v1/messages"):
            if not self.webex_ok():
                return self.send(401, {"message": "The request requires a valid access token."})
            body = self.body()
            if path == "/v1/webhooks":
                hook = {"id": f"hook-{len(state['webhooks']) + 1}", "status": "active", **body}
                state["webhooks"].append(hook)
                return self.send(200, hook)
            msg = {"id": f"msg-{len(state['messages']) + 1}", "roomId": body["roomId"],
                   "personEmail": "alice@example.com", "text": body["text"]}
            state["messages"][msg["id"]] = msg
            self.send(200, msg)
            for hook in state["webhooks"]:                   # event happened -> push to every subscriber
                if hook["resource"] == "messages" and hook["event"] == "created":
                    threading.Thread(target=deliver, args=(hook, msg), daemon=True).start()
            return None
        return self.send(404, {"error": "unknown path"})

    def get_task(self, task_id):
        with lock:
            task = state["tasks"].get(task_id)
            if task is None:
                return self.send(404, {"error": "task not found"})
            task["polls"] += 1
            info = {"taskId": task_id, "isError": False, "progress": "CLI Runner request creation"}
            if task["polls"] > JOB_POLLS:
                info["progress"] = json.dumps({"fileId": task["fileId"]})
                info["endTime"] = 1791700000000
                state["files"][task["fileId"]] = [{"deviceUuid": "dev-1", "commandResponses": {
                    "SUCCESS": {c: f"{c}\nedge1 uptime is 4 weeks" for c in task["commands"]}}}]
        return self.send(200, {"response": info, "version": "1.0"})


def expire_tokens():
    with lock:
        for token in state["tokens"]:
            state["tokens"][token] = "expired"


def deliver(hook, msg):
    """The service side of a webhook: POST a small notification (IDs only) to the subscriber's targetUrl."""
    payload = {"id": hook["id"], "name": hook["name"], "resource": "messages", "event": "created",
               "data": {"id": msg["id"], "roomId": msg["roomId"], "personEmail": msg["personEmail"]}}
    time.sleep(0.3)                                  # the event's 200 reaches the user first
    req = urllib.request.Request(hook["targetUrl"], data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=5).read()


def serve_in_thread():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":
    print(f"Mock API on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
