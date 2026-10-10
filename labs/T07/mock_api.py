"""Mock network-inventory REST API for the T07 drill (Python stdlib only).

Run:  python3 labs/T07/mock_api.py          -> http://127.0.0.1:8080/api/v1
Every endpoint and status code is listed in the API doc table in bee/T07 notes.
Credentials below are fake, for this local mock only.
"""
import base64
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST, PORT = "127.0.0.1", 8080
USERS = {"admin": ("C1sco12345", "admin"), "viewer": ("viewonly", "read")}
TOKENS = {"tok-admin-7f3a": "admin", "tok-viewer-91c2": "read"}
REQUIRED = ("hostname", "mgmt_ip", "role", "os")

devices = {
    1: {"id": 1, "hostname": "csr1", "mgmt_ip": "10.10.20.48", "role": "edge", "os": "iosxe"},
    2: {"id": 2, "hostname": "n9k1", "mgmt_ip": "10.10.20.58", "role": "core", "os": "nxos"},
    3: {"id": 3, "hostname": "edge2", "mgmt_ip": "10.10.20.49", "role": "edge", "os": "iosxe"},
}
versions = {1: 1, 2: 1, 3: 1}
stats_calls = {}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def version_string(self):              # Server: response header
        return "MockAPI/1.0"

    def log_message(self, *args):          # keep the drill output clean
        pass

    # ---------- helpers ----------
    def send(self, code, body=None, headers=None, content_type="application/json"):
        data = b""
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def role(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return TOKENS.get(auth[len("Bearer "):])
        return None

    def json_body(self):
        """Return (dict, None) or (None, error-response-already-sent)."""
        ctype = self.headers.get("Content-Type", "")
        if not ctype.startswith("application/json"):
            self.send(415, {"error": f"Content-Type must be application/json, got '{ctype}'"})
            return None, True
        try:
            return json.loads(self.read_body()), None
        except json.JSONDecodeError as err:
            self.send(400, {"error": f"invalid JSON: {err.msg}"})
            return None, True

    def device_etag(self, dev_id):
        return f'"dev-{dev_id}-v{versions[dev_id]}"'

    # ---------- routing ----------
    def route(self, method):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)

        if path == "/api/v1/auth/token" and method == "POST":
            return self.auth_token()
        if path == "/api/v1/health" and method == "GET":
            return self.send(503, {"status": "maintenance"}, {"Retry-After": "120"})
        if path == "/api/v1/old/devices":
            return self.send(301, None, {"Location": "/api/v1/devices"})

        if not path.startswith("/api/v1/"):
            return self.send(404, {"error": "unknown path"})
        role = self.role()
        if role is None:
            return self.send(401, {"error": "missing or invalid token"},
                             {"WWW-Authenticate": 'Bearer realm="mock-api"'})

        if path == "/api/v1/devices":
            if method == "GET":
                return self.list_devices(params)
            if method == "POST":
                return self.create_device(role)
            return self.send(405, {"error": f"{method} not allowed on /api/v1/devices"},
                             {"Allow": "GET, POST"})

        if path == "/api/v1/interfaces/stats" and method == "GET":
            token = self.headers["Authorization"]
            stats_calls[token] = stats_calls.get(token, 0) + 1
            if stats_calls[token] > 2:
                return self.send(429, {"error": "rate limit: 2 requests per minute"},
                                 {"Retry-After": "30"})
            return self.send(200, {"rx_errors": 0, "tx_errors": 3})

        match = re.fullmatch(r"/api/v1/devices/(\d+)(/backup|/config)?", path)
        if not match:
            return self.send(404, {"error": "unknown path"})
        dev_id, sub = int(match.group(1)), match.group(2)

        if sub == "/backup" and method == "POST":
            if dev_id not in devices:
                return self.send(404, {"error": f"device {dev_id} not found"})
            return self.send(202, {"job": "/api/v1/jobs/17", "status": "queued"},
                             {"Location": "/api/v1/jobs/17"})
        if sub == "/config" and method == "GET":
            if dev_id == 2:
                return self.send(500, {"error": "internal error: config parser crashed"})
            return self.send(200, f"hostname {devices[dev_id]['hostname']}\n", None, "text/plain")
        if sub:
            return self.send(405, {"error": "method not allowed"}, {"Allow": "POST" if sub == "/backup" else "GET"})

        return {
            "GET": self.get_device, "PUT": self.put_device,
            "PATCH": self.patch_device, "DELETE": self.delete_device,
        }.get(method, lambda *_: self.send(405, {"error": "method not allowed"},
                                          {"Allow": "GET, PUT, PATCH, DELETE"}))(dev_id, role)

    # ---------- endpoints ----------
    def auth_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            user, _, password = base64.b64decode(auth[6:]).decode().partition(":")
            if user in USERS and USERS[user][0] == password:
                token = next(t for t, r in TOKENS.items() if r == USERS[user][1])
                return self.send(200, {"token": token, "expires_in": 3600})
        return self.send(401, {"error": "bad credentials"}, {"WWW-Authenticate": 'Basic realm="mock-api"'})

    def list_devices(self, params):
        result = [d for d in devices.values()
                  if all(d.get(k) == v for k, v in params.items() if k in ("role", "os"))]
        offset, limit = int(params.get("offset", 0)), int(params.get("limit", 100))
        page = result[offset:offset + limit]
        return self.send(200, {"response": page, "total": len(result)})

    def get_device(self, dev_id, role):
        if dev_id not in devices:
            return self.send(404, {"error": f"device {dev_id} not found"})
        etag = self.device_etag(dev_id)
        if self.headers.get("If-None-Match") == etag:
            return self.send(304, None, {"ETag": etag})
        if "application/xml" in self.headers.get("Accept", ""):
            d = devices[dev_id]
            xml = "<device>" + "".join(f"<{k}>{v}</{k}>" for k, v in d.items()) + "</device>"
            return self.send(200, xml, {"ETag": etag}, "application/xml")
        return self.send(200, devices[dev_id], {"ETag": etag})

    def create_device(self, role):
        if role != "admin":
            return self.send(403, {"error": "role 'read' cannot create devices"})
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
        versions[dev_id] = 1
        return self.send(201, devices[dev_id], {"Location": f"/api/v1/devices/{dev_id}"})

    def put_device(self, dev_id, role):
        if role != "admin":
            return self.send(403, {"error": "role 'read' cannot modify devices"})
        body, failed = self.json_body()
        if failed:
            return
        missing = [f for f in REQUIRED if f not in body]
        if missing:
            return self.send(400, {"error": f"PUT replaces the whole resource; missing: {', '.join(missing)}"})
        created = dev_id not in devices
        devices[dev_id] = {"id": dev_id, **{f: body[f] for f in REQUIRED}}
        versions[dev_id] = versions.get(dev_id, 0) + 1
        if created:
            return self.send(201, devices[dev_id], {"Location": f"/api/v1/devices/{dev_id}"})
        return self.send(200, devices[dev_id])

    def patch_device(self, dev_id, role):
        if role != "admin":
            return self.send(403, {"error": "role 'read' cannot modify devices"})
        if dev_id not in devices:
            return self.send(404, {"error": f"device {dev_id} not found"})
        body, failed = self.json_body()
        if failed:
            return
        devices[dev_id].update({k: v for k, v in body.items() if k != "id"})
        versions[dev_id] += 1
        return self.send(200, devices[dev_id])

    def delete_device(self, dev_id, role):
        if role != "admin":
            return self.send(403, {"error": "role 'read' cannot delete devices"})
        if dev_id not in devices:
            return self.send(404, {"error": f"device {dev_id} not found"})
        del devices[dev_id]
        return self.send(204)

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
    print(f"Mock API on http://{HOST}:{PORT}/api/v1  (Ctrl+C to stop)")
    HTTPServer((HOST, PORT), Handler).serve_forever()
