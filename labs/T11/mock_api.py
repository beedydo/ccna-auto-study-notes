"""Mock network-inventory REST API for the T11 requests lab (Python stdlib only).

Adapted from labs/T07/mock_api.py, with three changes for T11:
  - HTTPS with a self-signed cert (to practise verify= and InsecureRequestWarning)
  - Catalyst Center style login: POST /auth/token -> {"Token": ...}, sent back as X-Auth-Token
  - paging with a "next" link, a short 429 + Retry-After, and a slow endpoint for timeouts

Run:  python3 labs/T11/mock_api.py CERT KEY   -> https://127.0.0.1:8111/api/v1
(bash labs/T11/run_lab.sh makes the cert and starts this for you.)
Credentials below are fake, for this local mock only.
"""
import base64
import json
import re
import ssl
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8111
USERS = {"admin": "C1sco12345"}
TOKEN = "tok-admin-7f3a"
REQUIRED = ("hostname", "mgmt_ip", "role", "os")
RATE_LIMIT, RETRY_AFTER = 2, 2          # 2 calls, then 429 for 2 seconds

devices = {
    1: {"id": 1, "hostname": "csr1", "mgmt_ip": "10.10.20.48", "role": "edge", "os": "iosxe"},
    2: {"id": 2, "hostname": "n9k1", "mgmt_ip": "10.10.20.58", "role": "core", "os": "nxos"},
    3: {"id": 3, "hostname": "edge2", "mgmt_ip": "10.10.20.49", "role": "edge", "os": "iosxe"},
    4: {"id": 4, "hostname": "cat9k1", "mgmt_ip": "10.10.20.60", "role": "access", "os": "iosxe"},
    5: {"id": 5, "hostname": "cat9k2", "mgmt_ip": "10.10.20.61", "role": "access", "os": "iosxe"},
}
lock = threading.Lock()
rate = {"calls": 0, "blocked_until": 0.0}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"          # keep-alive, so a Session can reuse the connection

    def version_string(self):
        return "MockAPI/1.1"

    def log_message(self, *args):
        pass

    # ---------- helpers ----------
    def send(self, code, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        self.send_header("X-Client-Port", str(self.client_address[1]))   # which TCP connection
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def authed(self):
        token = self.headers.get("X-Auth-Token") or self.headers.get("Authorization", "").removeprefix("Bearer ")
        return token == TOKEN

    def json_body(self):
        """Return (dict, False), or (None, True) after sending the error."""
        body = self.read_body()
        ctype = self.headers.get("Content-Type", "")
        if not ctype.startswith("application/json"):
            self.send(415, {"error": f"Content-Type must be application/json, got '{ctype}'"})
            return None, True
        try:
            return json.loads(body), False
        except json.JSONDecodeError as err:
            self.send(400, {"error": f"invalid JSON: {err.msg}"})
            return None, True

    # ---------- routing ----------
    def route(self, method):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)

        if path == "/api/v1/health":
            return self.send(200, {"status": "up"})
        if path == "/api/v1/auth/token" and method == "POST":
            return self.auth_token()
        if not self.authed():
            self.read_body()
            return self.send(401, {"error": "missing or invalid X-Auth-Token"})

        if path == "/api/v1/devices":
            if method == "GET":
                return self.list_devices(params)
            if method == "POST":
                return self.create_device()
            return self.send(405, {"error": "method not allowed"}, {"Allow": "GET, POST"})
        if path == "/api/v1/interfaces/stats" and method == "GET":
            return self.stats()
        if path == "/api/v1/slow" and method == "GET":
            time.sleep(3)                  # longer than the client's timeout=1
            return self.send(200, {"status": "finally"})

        match = re.fullmatch(r"/api/v1/devices/(\d+)", path)
        if not match:
            return self.send(404, {"error": "unknown path"})
        dev_id = int(match.group(1))
        if dev_id not in devices and method != "PUT":
            self.read_body()
            return self.send(404, {"error": f"device {dev_id} not found"})
        if method == "GET":
            return self.send(200, devices[dev_id])
        if method == "DELETE":
            del devices[dev_id]
            return self.send(204)
        if method in ("PUT", "PATCH"):
            body, failed = self.json_body()
            if failed:
                return
            if method == "PUT":
                missing = [f for f in REQUIRED if f not in body]
                if missing:
                    return self.send(400, {"error": f"PUT needs every field; missing: {', '.join(missing)}"})
                devices[dev_id] = {"id": dev_id, **{f: body[f] for f in REQUIRED}}
            else:
                devices[dev_id].update({k: v for k, v in body.items() if k != "id"})
            return self.send(200, devices[dev_id])
        return self.send(405, {"error": "method not allowed"}, {"Allow": "GET, PUT, PATCH, DELETE"})

    # ---------- endpoints ----------
    def auth_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            user, _, password = base64.b64decode(auth[6:]).decode().partition(":")
            if USERS.get(user) == password:
                return self.send(200, {"Token": TOKEN, "expires_in": 3600})
        return self.send(401, {"error": "bad credentials"}, {"WWW-Authenticate": 'Basic realm="mock-api"'})

    def list_devices(self, params):
        result = [d for d in devices.values() if all(d.get(k) == v for k, v in params.items() if k in ("role", "os"))]
        offset, limit = int(params.get("offset", 0)), int(params.get("limit", 100))
        page = result[offset:offset + limit]
        nxt = None
        if offset + limit < len(result):
            extra = "".join(f"&{k}={v}" for k, v in params.items() if k in ("role", "os"))
            nxt = f"/api/v1/devices?offset={offset + limit}&limit={limit}{extra}"
        return self.send(200, {"response": page, "total": len(result), "next": nxt})

    def create_device(self):
        body, failed = self.json_body()
        if failed:
            return
        missing = [f for f in REQUIRED if f not in body]
        if missing:
            return self.send(400, {"error": f"missing field(s): {', '.join(missing)}"})
        if any(d["hostname"] == body["hostname"] for d in devices.values()):
            return self.send(409, {"error": f"hostname {body['hostname']} already exists"})
        dev_id = max(devices) + 1
        devices[dev_id] = {"id": dev_id, **{f: body[f] for f in REQUIRED}}
        return self.send(201, devices[dev_id], {"Location": f"/api/v1/devices/{dev_id}"})

    def stats(self):
        with lock:
            now = time.monotonic()
            if now < rate["blocked_until"]:
                wait = max(1, round(rate["blocked_until"] - now))
                return self.send(429, {"error": "rate limit exceeded"}, {"Retry-After": str(wait)})
            if rate["blocked_until"]:
                rate.update(calls=0, blocked_until=0.0)      # window over: start counting again
            rate["calls"] += 1
            if rate["calls"] > RATE_LIMIT:
                rate["blocked_until"] = now + RETRY_AFTER
                return self.send(429, {"error": "rate limit: 2 requests, then wait"}, {"Retry-After": str(RETRY_AFTER)})
        return self.send(200, {"rx_errors": 0, "tx_errors": 3})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_PATCH(self):
        self.route("PATCH")

    def do_DELETE(self):
        self.route("DELETE")


if __name__ == "__main__":
    cert, key = sys.argv[1], sys.argv[2]
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print(f"Mock API on https://{HOST}:{PORT}/api/v1  (Ctrl+C to stop)")
    server.serve_forever()
