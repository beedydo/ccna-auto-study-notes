"""Mock Catalyst Center (DNA Center) API for the T45 script-reading lab (Python stdlib only).

Run:  python3 labs/T45/mock_catalyst_center.py      -> http://127.0.0.1:18045
Port: T45_PORT env var (default 18045).  Page size cap: T45_MAX_LIMIT (default 3).

Paths and JSON shapes follow the Catalyst Center Intent API docs:
  POST /dna/system/api/v1/auth/token           Basic auth          -> {"Token": ...}
  GET  /dna/intent/api/v1/network-device       ?offset=1&limit=N   -> {"response": [...], "version"}
  GET  /dna/intent/api/v1/network-device/count                     -> {"response": 7, "version"}
  PUT  /dna/intent/api/v1/network-device/sync  ["id", ...]         -> {"response": {"taskId", "url"}}
  GET  /dna/intent/api/v1/task/{taskId}                            -> {"response": {"progress", "isError", ...}}
The real API caps limit at 500; this mock caps it at 3 so pagination shows with 7 devices.
Credentials below are fake, for this local mock only.
"""
import base64
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = int(os.environ.get("T45_PORT", "18045"))
MAX_LIMIT = int(os.environ.get("T45_MAX_LIMIT", "3"))
USERS = {"devnetuser": "Cisco123!"}
TOKEN = "eyJhbGciOiJSUzI1NiJ9.mock-t45-token"

DEVICES = [
    # (hostname, ip, platform, version, reachability, role)
    ("cat9k-core-1", "10.10.20.81", "C9300-24U", "17.9.4a", "Reachable", "CORE"),
    ("cat9k-acc-1", "10.10.20.82", "C9300-48P", "17.9.4a", "Reachable", "ACCESS"),
    ("cat9k-acc-2", "10.10.20.83", "C9300-48P", "17.9.4a", "Reachable", "ACCESS"),
    ("isr4k-edge-1", "10.10.20.84", "ISR4451-X/K9", "17.6.5", "Unreachable", "BORDER ROUTER"),
    ("cat9k-acc-3", "10.10.20.85", "C9200L-24P-4G", "17.9.4a", "Reachable", "ACCESS"),
    ("c9800-wlc-1", "10.10.20.86", "C9800-CL-K9", "17.9.3", "Reachable", "ACCESS"),
    ("cat9k-acc-4", "10.10.20.87", "C9300-48P", "17.6.5", "Unreachable", "ACCESS"),
]
devices = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, name)),
        "hostname": name,
        "managementIpAddress": ip,
        "platformId": platform,
        "softwareType": "IOS-XE",
        "softwareVersion": version,
        "reachabilityStatus": reach,
        "reachabilityFailureReason": "SNMP Timeouts" if reach == "Unreachable" else "",
        "role": role,
        "family": "Routers" if "ISR" in platform else "Switches and Hubs",
        "upTime": "41 days, 3:12:09.00" if reach == "Reachable" else "",
    }
    for name, ip, platform, version, reach, role in DEVICES
]
tasks = {}   # taskId -> number of times polled


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):          # silence the default access log
        pass

    def log_request(self, code="-", size="-"):  # one line per call: METHOD path -> code
        print(f"{self.command:<4} {self.path} -> {code}", flush=True)

    def send(self, code, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def error(self, code, message, headers=None):
        self.send(code, {"response": {"errorCode": str(code), "message": message}, "version": "1.0"}, headers)

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    # ---------- routing ----------
    def route(self, method):
        url = urlparse(self.path)
        path, query = url.path, parse_qs(url.query)

        if path == "/dna/system/api/v1/auth/token":
            if method != "POST":
                return self.error(405, f"{method} not allowed; use POST", {"Allow": "POST"})
            return self.auth()

        if not path.startswith("/dna/intent/api/v1/"):
            return self.error(404, f"no such path {path}")
        if self.headers.get("X-Auth-Token") != TOKEN:
            return self.error(401, "missing or invalid X-Auth-Token header")

        if path == "/dna/intent/api/v1/network-device":
            if method != "GET":
                return self.error(405, f"{method} not allowed", {"Allow": "GET"})
            return self.list_devices(query)
        if path == "/dna/intent/api/v1/network-device/count" and method == "GET":
            return self.send(200, {"response": len(devices), "version": "1.0"})
        if path == "/dna/intent/api/v1/network-device/sync":
            if method != "PUT":
                return self.error(405, f"{method} not allowed; sync uses PUT", {"Allow": "PUT"})
            return self.sync(query)
        if path.startswith("/dna/intent/api/v1/task/") and method == "GET":
            return self.task(path.rsplit("/", 1)[-1])
        return self.error(404, f"no such path {path}")

    # ---------- endpoints ----------
    def auth(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            user, _, password = base64.b64decode(auth[6:]).decode().partition(":")
            if USERS.get(user) == password:
                return self.send(200, {"Token": TOKEN})
        return self.error(401, "Authentication has failed. Please provide valid credentials.")

    def list_devices(self, query):
        offset = int(query.get("offset", ["1"])[0])           # 1-based, like the real API
        limit = min(int(query.get("limit", [str(MAX_LIMIT)])[0]), MAX_LIMIT)
        page = devices[offset - 1: offset - 1 + limit]
        return self.send(200, {"response": page, "version": "1.0"})

    def sync(self, query):
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.error(415, f"Content-Type must be application/json, got '{self.headers.get('Content-Type', '')}'")
        try:
            ids = json.loads(self.body())
        except json.JSONDecodeError as err:
            return self.error(400, f"invalid JSON: {err.msg}")
        known = {d["id"] for d in devices}
        if not isinstance(ids, list) or not ids or not set(ids) <= known:
            return self.error(400, "body must be a non-empty list of known device ids")
        task_id = str(uuid.uuid5(uuid.NAMESPACE_URL, ",".join(ids)))
        tasks[task_id] = 0
        return self.send(202, {"response": {"taskId": task_id, "url": f"/api/v1/task/{task_id}"},
                               "version": "1.0"})

    def task(self, task_id):
        if task_id not in tasks:
            return self.error(404, "No task corresponding to the id was found")
        tasks[task_id] += 1
        done = tasks[task_id] >= 2                              # first poll: still running
        response = {"id": task_id, "isError": False, "serviceType": "Inventory service",
                    "startTime": 1791612000000,
                    "progress": "Device resync completed" if done else "Synchronizing devices"}
        if done:
            response["endTime"] = 1791612004000
        return self.send(200, {"response": response, "version": "1.0"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_DELETE(self):
        self.route("DELETE")


if __name__ == "__main__":
    print(f"Mock Catalyst Center on http://{HOST}:{PORT} (page size cap {MAX_LIMIT})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
