"""Mock 'cloud dashboard' REST API for the T08 drill (Python stdlib only).

Run:  python3 labs/T08/mock_api.py          -> http://127.0.0.1:8108/api/v1
It enforces every consumer-side limit in bee/T08 notes: rate limit, pagination,
payload size, slow and async endpoints, token expiry, a deprecated version, ETags.
Credentials below are fake, for this local mock only.
"""
import base64
import json
import math
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

HOST, PORT = "127.0.0.1", 8108
BASE = f"http://{HOST}:{PORT}"
USERS = {"admin": "C1sco12345"}
RATE_LIMIT, RATE_WINDOW = 3, 2          # 3 requests per 2-second window, per token
MAX_BODY_BYTES, MAX_ITEMS = 512, 10     # payload limits on POST /devices/claim
DEFAULT_TTL = 300                       # token lifetime in seconds

DEVICES = [{"serial": f"Q2SW-{n:04d}", "hostname": f"sw{n:02d}", "model": "MS120-8"} for n in range(1, 13)]
CLIENTS = [{"id": f"c{n:03d}", "mac": f"00:18:0a:00:00:{n:02x}", "ip": f"10.10.30.{n + 10}"} for n in range(1, 26)]
EVENTS = [{"id": n, "type": "port_down" if n % 3 else "port_up", "device": f"Q2SW-{n:04d}"} for n in range(1, 10)]

lock = threading.Lock()
tokens = {}            # access token -> expiry (epoch seconds)
refresh_tokens = {}    # refresh token -> ttl to reissue with
windows = {}           # token -> [window_start, count]
flaky_calls = {}       # token -> count of /reports/flaky calls
job_polls = {}         # job id -> poll count
counter = {"at": 0, "rt": 0, "job": 0}


def new_token(ttl):
    counter["at"] += 1
    counter["rt"] += 1
    access, refresh = f"at-{counter['at']:04d}", f"rt-{counter['rt']:04d}"
    tokens[access] = time.time() + ttl
    refresh_tokens[refresh] = DEFAULT_TTL
    return {"access_token": access, "refresh_token": refresh, "token_type": "Bearer", "expires_in": ttl}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockDashboard/1.0"

    def log_message(self, *args):
        pass

    # ---------- helpers ----------
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

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def bearer(self):
        """Return (token, None) if valid, else (None, True) after sending 401."""
        auth = self.headers.get("Authorization", "")
        token = auth[len("Bearer "):] if auth.startswith("Bearer ") else None
        with lock:
            expiry = tokens.get(token)
        if expiry is None:
            self.send(401, {"error": "missing or invalid token"},
                      {"WWW-Authenticate": 'Bearer realm="mock-api", error="invalid_token"'})
            return None, True
        if time.time() > expiry:
            self.send(401, {"error": "token expired"},
                      {"WWW-Authenticate": 'Bearer realm="mock-api", error="invalid_token", '
                                           'error_description="The access token expired"'})
            return None, True
        return token, None

    # ---------- routing ----------
    def route(self, method):
        parts = urlsplit(self.path)
        path, params = parts.path, dict(parse_qsl(parts.query))

        if path == "/api/v1/auth/token" and method == "POST":
            return self.auth_token(params)
        if path.startswith("/api/v0/"):
            return self.v0(method, path)
        if not path.startswith("/api/v1/"):
            return self.send(404, {"error": f"unknown API version in {path}"})

        token, failed = self.bearer()
        if failed:
            return

        if path == "/api/v1/devices" and method == "GET":
            return self.list_devices(params)
        if path == "/api/v1/networks/N_100/clients" and method == "GET":
            return self.list_clients(params)
        if path == "/api/v1/events" and method == "GET":
            return self.list_events(params)
        if path == "/api/v1/devices/claim" and method == "POST":
            return self.claim()
        if path == "/api/v1/reports/flaky" and method == "GET":
            return self.flaky(token)
        if path == "/api/v1/reports/slow" and method == "GET":
            time.sleep(2)
            return self.send(200, {"report": "slow", "rows": 1200})
        if path == "/api/v1/reports/gateway" and method == "GET":
            return self.send(504, {"error": "gateway: upstream did not respond within 30 s"})
        if path == "/api/v1/reports" and method == "POST":
            with lock:
                counter["job"] += 1
                job = counter["job"]
                job_polls[job] = 0
            return self.send(202, {"job_id": job, "status": "queued"}, {"Location": f"/api/v1/jobs/{job}"})

        match = re.fullmatch(r"/api/v1/jobs/(\d+)", path)
        if match and method == "GET":
            return self.job(int(match.group(1)))
        match = re.fullmatch(r"/api/v1/devices/(Q2SW-\d{4})/status", path)
        if match and method == "GET":
            return self.status(token, match.group(1))
        match = re.fullmatch(r"/api/v1/devices/(Q2SW-\d{4})", path)
        if match and method == "GET":
            return self.get_device(match.group(1))
        return self.send(404, {"error": "unknown path"})

    # ---------- endpoints ----------
    def auth_token(self, params):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):                                   # log in with user:pass
            user, _, password = base64.b64decode(auth[6:]).decode().partition(":")
            if USERS.get(user) == password:
                ttl = int(params.get("ttl", DEFAULT_TTL))              # mock-only: ask for a short life
                with lock:
                    return self.send(200, new_token(ttl))
            return self.send(401, {"error": "bad credentials"}, {"WWW-Authenticate": 'Basic realm="mock-api"'})
        form = dict(parse_qsl(self.read_body().decode()))               # OAuth-style refresh
        if form.get("grant_type") == "refresh_token":
            with lock:
                ttl = refresh_tokens.pop(form.get("refresh_token"), None)
                if ttl is not None:
                    return self.send(200, new_token(ttl))
            return self.send(400, {"error": "invalid_grant"})
        return self.send(401, {"error": "send Basic credentials or a refresh_token grant"})

    def status(self, token, serial):
        now = time.time()
        with lock:
            win = windows.get(token)
            if win is None or now >= win[0] + RATE_WINDOW:
                win = windows[token] = [now, 0]
            reset = str(math.ceil(win[0] + RATE_WINDOW - now))
            if win[1] >= RATE_LIMIT:
                return self.send(429, {"error": f"rate limit: {RATE_LIMIT} requests per {RATE_WINDOW} s"},
                                 {"Retry-After": reset, "X-RateLimit-Limit": str(RATE_LIMIT),
                                  "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset})
            win[1] += 1
            remaining = str(RATE_LIMIT - win[1])
        return self.send(200, {"serial": serial, "status": "online"},
                         {"X-RateLimit-Limit": str(RATE_LIMIT), "X-RateLimit-Remaining": remaining,
                          "X-RateLimit-Reset": reset})

    def flaky(self, token):
        with lock:
            flaky_calls[token] = flaky_calls.get(token, 0) + 1
            n = flaky_calls[token]
            if n >= 3:
                flaky_calls[token] = 0
        if n < 3:
            return self.send(503, {"error": "backend busy, try again later"})   # no Retry-After
        return self.send(200, {"report": "flaky", "rows": 42})

    def list_devices(self, params):                                     # offset / limit
        offset, limit = int(params.get("offset", 0)), int(params.get("limit", 5))
        return self.send(200, {"response": DEVICES[offset:offset + limit], "total": len(DEVICES)})

    def list_clients(self, params):                                     # cursor + Link header
        per_page = int(params.get("perPage", 10))
        after = params.get("startingAfter")
        start = next((i + 1 for i, c in enumerate(CLIENTS) if c["id"] == after), 0)
        page = CLIENTS[start:start + per_page]
        url = f"{BASE}/api/v1/networks/N_100/clients?perPage={per_page}"
        links = [f'<{url}>; rel="first"']
        if start + per_page < len(CLIENTS):
            links.append(f'<{url}&startingAfter={page[-1]["id"]}>; rel="next"')
        return self.send(200, page, {"Link": ", ".join(links)})

    def list_events(self, params):                                      # page / per_page
        page, per_page = int(params.get("page", 1)), int(params.get("per_page", 4))
        total_pages = math.ceil(len(EVENTS) / per_page)
        items = EVENTS[(page - 1) * per_page:page * per_page]
        return self.send(200, {"page": page, "per_page": per_page, "total_pages": total_pages, "items": items})

    def claim(self):
        size = int(self.headers.get("Content-Length", 0))
        if size > MAX_BODY_BYTES:                                       # reject before reading the body
            self.read_body()
            return self.send(413, {"error": f"body is {size} bytes; limit is {MAX_BODY_BYTES}"})
        serials = json.loads(self.read_body()).get("serials", [])
        if len(serials) > MAX_ITEMS:
            return self.send(400, {"error": f"{len(serials)} serials; max {MAX_ITEMS} per request"})
        return self.send(200, {"claimed": len(serials)})

    def job(self, job):
        with lock:
            if job not in job_polls:
                return self.send(404, {"error": f"job {job} not found"})
            job_polls[job] += 1
            polls = job_polls[job]
        if polls < 3:
            return self.send(200, {"job_id": job, "status": "running"}, {"Retry-After": "1"})
        return self.send(200, {"job_id": job, "status": "complete", "result": f"/api/v1/reports/{job}"})

    def get_device(self, serial):
        device = next((d for d in DEVICES if d["serial"] == serial), None)
        if device is None:
            return self.send(404, {"error": f"device {serial} not found"})
        etag = f'"{serial}-r1"'
        if self.headers.get("If-None-Match") == etag:
            return self.send(304, None, {"ETag": etag})
        return self.send(200, device, {"ETag": etag, "Cache-Control": "max-age=60"})

    def v0(self, method, path):
        token, failed = self.bearer()
        if failed:
            return
        if path == "/api/v0/devices" and method == "GET":
            old = [{"serial": d["serial"], "name": d["hostname"]} for d in DEVICES[:3]]   # v0 field = name
            return self.send(200, {"response": old}, {
                "Deprecation": "@1767225599",                           # deprecated since 31 Dec 2025
                "Sunset": "Thu, 31 Dec 2026 23:59:59 GMT",              # removed after this date
                "Link": '</api/v1/devices>; rel="successor-version"'})
        return self.send(404, {"error": "unknown path"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")


if __name__ == "__main__":
    print(f"Mock dashboard API on {BASE}/api/v1  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
