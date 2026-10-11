"""Mock API for the T10 auth drill: one local server, six auth styles (Python stdlib only).

Run:  python3 labs/T10/mock_auth_api.py        -> http://127.0.0.1:8110
Each path prefix copies the auth *shape* of one Cisco platform (see bee/T10 notes).
The paths are NOT the real platform paths. All users, keys and secrets are fake.
Every request line is printed to stdout like a web-server access log.
"""
import base64
import json
import secrets
import sys
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

HOST, PORT = "127.0.0.1", 8110
USERS = {"admin": ("C1sco12345", "admin"), "viewer": ("viewonly", "read")}   # fake user DB
API_KEYS = {"6bec40cf957de430a6f1f2baa056b99a4fac9ea0": "admin"}            # fake key, portal-generated
OAUTH_CLIENTS = {"demo-app": ("demo-secret", "http://127.0.0.1:9000/callback")}
ACCESS_TTL = 2            # seconds; deliberately tiny so the drill can show expiry

DEVICES = [{"id": 1, "hostname": "csr1"}, {"id": 2, "hostname": "n9k1"}]
tokens = {}               # X-Auth-Token / APIC token -> role
sessions = {}             # JSESSIONID -> {"role": ..., "xsrf": ...}
auth_codes = {}           # code -> {"client_id", "redirect_uri", "scope", "role"}
access_tokens = {}        # OAuth access token -> {"scope", "role", "exp"}
refresh_tokens = {}       # OAuth refresh token -> {"scope", "role"}


def new_token(prefix):
    return f"{prefix}-{secrets.token_hex(4)}"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockAuth/1.0"

    def log_message(self, fmt, *args):                       # access log -> stdout
        print(f'ACCESS "{self.requestline}" {args[1] if len(args) > 1 else ""}', flush=True)

    # ---------- helpers ----------
    def send(self, code, body=None, headers=None, content_type="application/json"):
        data = b""
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        for key, value in (headers or []):
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        raw = self.raw_body
        if self.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
            return {k: v[0] for k, v in parse_qs(raw).items()}
        return json.loads(raw) if raw else {}

    def basic_user(self):
        """Return the role if a valid Authorization: Basic header is present."""
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return None
        user, _, password = base64.b64decode(auth[6:]).decode().partition(":")
        if user in USERS and USERS[user][0] == password:
            return USERS[user][1]
        return None

    def cookie(self, name):
        jar = SimpleCookie(self.headers.get("Cookie", ""))
        return jar[name].value if name in jar else None

    def deny(self, scheme, detail="missing or invalid credentials"):
        return self.send(401, {"error": detail}, [("WWW-Authenticate", f'{scheme} realm="mock"')])

    # ---------- routing ----------
    def route(self, method):
        length = int(self.headers.get("Content-Length", 0))       # always drain the body, so a
        self.raw_body = self.rfile.read(length).decode() if length else ""   # keep-alive conn stays clean
        url = urlparse(self.path)
        path, query = url.path, {k: v[0] for k, v in parse_qs(url.query).items()}

        # 1. Basic auth on EVERY request (e.g. RESTCONF on IOS XE)
        if path == "/basic/devices" and method == "GET":
            if self.basic_user() is None:
                return self.deny("Basic")
            return self.send(200, {"devices": DEVICES})

        # 2. Custom token: Basic once -> token -> X-Auth-Token header (Catalyst Center shape)
        if path == "/catc/auth/token" and method == "POST":
            role = self.basic_user()
            if role is None:
                return self.deny("Basic", "bad username or password")
            token = new_token("tok")
            tokens[token] = role
            return self.send(200, {"Token": token})
        if path == "/catc/devices":
            role = tokens.get(self.headers.get("X-Auth-Token", ""))
            if role is None:
                return self.deny("X-Auth-Token")
            if method == "POST" and role != "admin":
                return self.send(403, {"error": "role 'read' may not add devices"})
            return self.send(201 if method == "POST" else 200,
                             {"added": True} if method == "POST" else {"devices": DEVICES})

        # 3. API key in a header or the query string (Meraki shape)
        if path == "/key/devices" and method == "GET":
            key = self.headers.get("X-API-Key") or query.get("api_key")
            if key not in API_KEYS:
                return self.deny("ApiKey")
            return self.send(200, {"devices": DEVICES})

        # 4a. Session cookie + XSRF token (SD-WAN Manager shape)
        if path == "/sdwan/j_security_check" and method == "POST":
            form = self.body()
            user = USERS.get(form.get("j_username"))
            if not user or user[0] != form.get("j_password"):
                return self.send(200, "<html>login failed</html>", None, "text/html")
            sid = secrets.token_hex(8).upper()
            sessions[sid] = {"role": user[1], "xsrf": secrets.token_hex(6)}
            return self.send(200, None, [("Set-Cookie", f"JSESSIONID={sid}; Path=/sdwan; HttpOnly")])
        if path.startswith("/sdwan/dataservice/"):
            sess = sessions.get(self.cookie("JSESSIONID") or "")
            if sess is None:
                return self.deny("Cookie", "no valid JSESSIONID cookie")
            if path == "/sdwan/dataservice/client/token" and method == "GET":
                return self.send(200, sess["xsrf"], None, "text/plain")
            if path == "/sdwan/dataservice/device" and method == "GET":
                return self.send(200, {"data": DEVICES})
            if path == "/sdwan/dataservice/template" and method == "POST":
                if self.headers.get("X-XSRF-TOKEN") != sess["xsrf"]:
                    return self.send(403, {"error": "missing or wrong X-XSRF-TOKEN"})
                return self.send(201, {"templateId": "tpl-01"})

        # 4b. Login body -> token, also set as cookie APIC-cookie (ACI APIC shape)
        if path == "/apic/api/aaaLogin.json" and method == "POST":
            attrs = self.body().get("aaaUser", {}).get("attributes", {})
            user = USERS.get(attrs.get("name"))
            if not user or user[0] != attrs.get("pwd"):
                return self.deny("Cookie", "aaaLogin failed")
            token = new_token("apic")
            tokens[token] = user[1]
            reply = {"imdata": [{"aaaLogin": {"attributes": {"token": token, "refreshTimeoutSeconds": "600"}}}]}
            return self.send(200, reply, [("Set-Cookie", f"APIC-cookie={token}; Path=/apic; HttpOnly")])
        if path == "/apic/api/class/fabricNode.json" and method == "GET":
            if self.cookie("APIC-cookie") not in tokens:
                return self.deny("Cookie", "no valid APIC-cookie")
            return self.send(200, {"totalCount": "2", "imdata": DEVICES})

        # 5. OAuth 2.0 authorization-code grant (Webex integration shape)
        if path == "/oauth/authorize" and method == "GET":
            client = OAUTH_CLIENTS.get(query.get("client_id"))
            if query.get("response_type") != "code" or not client or client[1] != query.get("redirect_uri"):
                return self.send(400, {"error": "invalid_request"})
            role = self.basic_user()                        # stands in for the login + consent page
            if role is None:
                return self.send(200, "<html>login page: enter username and password</html>", None, "text/html")
            code = secrets.token_hex(5)
            auth_codes[code] = {"client_id": query["client_id"], "redirect_uri": query["redirect_uri"],
                                "scope": query.get("scope", ""), "role": role}
            location = query["redirect_uri"] + "?" + urlencode({"code": code, "state": query.get("state", "")})
            return self.send(302, None, [("Location", location)])
        if path == "/oauth/token" and method == "POST":
            form = self.body()
            client = OAUTH_CLIENTS.get(form.get("client_id"))
            if not client or client[0] != form.get("client_secret"):
                return self.send(401, {"error": "invalid_client"})
            if form.get("grant_type") == "authorization_code":
                grant = auth_codes.pop(form.get("code"), None)   # pop: a code works ONCE
                if not grant or grant["redirect_uri"] != form.get("redirect_uri"):
                    return self.send(400, {"error": "invalid_grant"})
            elif form.get("grant_type") == "refresh_token":
                grant = refresh_tokens.get(form.get("refresh_token"))
                if not grant:
                    return self.send(400, {"error": "invalid_grant"})
            else:
                return self.send(400, {"error": "unsupported_grant_type"})
            access, refresh = new_token("acc"), form.get("refresh_token") or new_token("ref")
            access_tokens[access] = {"scope": grant["scope"], "role": grant["role"], "exp": time.time() + ACCESS_TTL}
            refresh_tokens[refresh] = {"scope": grant["scope"], "role": grant["role"]}
            return self.send(200, {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TTL,
                                   "refresh_token": refresh, "scope": grant["scope"]})
        if path == "/oauth/api/devices":
            auth = self.headers.get("Authorization", "")
            tok = access_tokens.get(auth[7:]) if auth.startswith("Bearer ") else None
            if tok is None or tok["exp"] < time.time():
                return self.send(401, {"error": "invalid_token"},
                                 [("WWW-Authenticate", 'Bearer error="invalid_token"')])
            needed = "devices:write" if method == "POST" else "devices:read"
            if needed not in tok["scope"].split():
                return self.send(403, {"error": "insufficient_scope"},
                                 [("WWW-Authenticate", f'Bearer error="insufficient_scope", scope="{needed}"')])
            return self.send(201 if method == "POST" else 200,
                             {"added": True} if method == "POST" else {"devices": DEVICES})

        return self.send(404, {"error": "unknown path"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")


if __name__ == "__main__":
    print(f"Mock auth API on http://{HOST}:{PORT}  (Ctrl+C to stop)", flush=True)
    sys.stdout.reconfigure(line_buffering=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
