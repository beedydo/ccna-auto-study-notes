"""T10 reference program: one client, every API auth method on the exam.

Start the mock API first:   python3 labs/T10/mock_auth_api.py
Load the fake credentials:  set -a && source labs/T10/mock-creds.env && set +a
Then:                       python3 labs/T10/auth_tour.py
Or all in one:              bash labs/T10/run_lab.sh

Needs `requests` (pip install requests, or use the labs/ Docker image).
"""
import base64
import os
import secrets
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from requests.auth import HTTPBasicAuth

BASE = os.environ.get("AUTH_LAB_BASE", "http://127.0.0.1:8110")


def require_env(name):
    """Read a secret from the environment; stop with a clear message if it's missing."""
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: environment variable {name} is not set (see labs/T10/mock-creds.env)")
    return value


USER = require_env("LAB_USER")
PASSWORD = require_env("LAB_PASS")
API_KEY = require_env("LAB_API_KEY")
CLIENT_ID = require_env("LAB_CLIENT_ID")
CLIENT_SECRET = require_env("LAB_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:9000/callback"


def show(r, *headers):
    """Print the request line, the status line, any named response headers, and 4xx bodies."""
    print(f">>> {r.request.method} {r.request.url}")
    print(f"<<< {r.status_code} {r.reason}")
    for name in headers:
        if name in r.headers:
            print(f"    {name}: {r.headers[name]}")
    if r.status_code >= 400:
        print(f"    body: {r.text}")
    return r


def basic_auth():
    print("== 1. Basic auth: credentials on EVERY request ==")
    show(requests.get(f"{BASE}/basic/devices", timeout=5), "WWW-Authenticate")      # 401
    r = show(requests.get(f"{BASE}/basic/devices", auth=(USER, PASSWORD), timeout=5))
    sent = r.request.headers["Authorization"]
    print(f"    sent:    Authorization: {sent}")
    print(f"    decoded: {base64.b64decode(sent.split()[1]).decode()}   <- base64 is encoding, not encryption")


def custom_token():
    print("\n== 2. Custom token: Basic once -> token -> X-Auth-Token on every call ==")
    r = show(requests.post(f"{BASE}/catc/auth/token", auth=HTTPBasicAuth(USER, PASSWORD), timeout=5))
    token = r.json()["Token"]
    print(f"    token in body: {token}")
    s = requests.Session()
    s.headers.update({"X-Auth-Token": token, "Accept": "application/json"})          # every later call
    show(s.get(f"{BASE}/catc/devices", timeout=5))                                   # 200
    show(requests.get(f"{BASE}/catc/devices", headers={"X-Auth-Token": "tok-wrong"}, timeout=5))  # 401
    viewer = requests.post(f"{BASE}/catc/auth/token", auth=("viewer", "viewonly"), timeout=5).json()["Token"]
    show(requests.post(f"{BASE}/catc/devices", headers={"X-Auth-Token": viewer}, json={}, timeout=5))  # 403


def api_key():
    print("\n== 3. API key: static key, no login step ==")
    show(requests.get(f"{BASE}/key/devices", headers={"X-API-Key": API_KEY}, timeout=5))   # header
    show(requests.get(f"{BASE}/key/devices", params={"api_key": API_KEY}, timeout=5))      # query string
    show(requests.get(f"{BASE}/key/devices", timeout=5), "WWW-Authenticate")               # 401


def cookies():
    print("\n== 4a. Session cookie + XSRF header (SD-WAN Manager shape) ==")
    s = requests.Session()
    show(s.post(f"{BASE}/sdwan/j_security_check",
                data={"j_username": USER, "j_password": PASSWORD}, timeout=5), "Set-Cookie")
    print(f"    cookie jar now holds: {sorted(s.cookies.keys())}")
    show(s.get(f"{BASE}/sdwan/dataservice/device", timeout=5))                       # cookie sent for us
    show(requests.get(f"{BASE}/sdwan/dataservice/device", timeout=5))                # no Session -> 401
    xsrf = show(s.get(f"{BASE}/sdwan/dataservice/client/token", timeout=5)).text
    show(s.post(f"{BASE}/sdwan/dataservice/template", json={"name": "t1"}, timeout=5))   # 403
    s.headers.update({"X-XSRF-TOKEN": xsrf})
    show(s.post(f"{BASE}/sdwan/dataservice/template", json={"name": "t1"}, timeout=5))   # 201

    print("\n== 4b. Login body -> token + APIC-cookie (ACI APIC shape) ==")
    s = requests.Session()
    login = {"aaaUser": {"attributes": {"name": USER, "pwd": PASSWORD}}}
    r = show(s.post(f"{BASE}/apic/api/aaaLogin.json", json=login, timeout=5), "Set-Cookie")
    print(f"    token in body: {r.json()['imdata'][0]['aaaLogin']['attributes']['token']}")
    show(s.get(f"{BASE}/apic/api/class/fabricNode.json", timeout=5))                 # 200


def oauth_code_flow():
    print("\n== 5. OAuth 2.0 authorization-code grant (Webex integration shape) ==")
    state = secrets.token_hex(4)                                     # anti-CSRF value we check later
    authorize_url = f"{BASE}/oauth/authorize?" + urlencode({
        "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "scope": "devices:read", "state": state})
    # (A)+(B) the USER's browser opens authorize_url and logs in at the auth server, not in our app.
    # Here a Basic header stands in for the login form; the app never sees this password.
    r = show(requests.get(authorize_url, auth=(USER, PASSWORD), allow_redirects=False, timeout=5), "Location")
    # (C) the browser is redirected back to our redirect_uri with ?code=...&state=...
    back = parse_qs(urlparse(r.headers["Location"]).query)
    assert back["state"][0] == state, "state mismatch: possible CSRF"
    code = back["code"][0]
    # (D) our app swaps the code for tokens, server to server, proving itself with client_secret
    form = {"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    tokens = show(requests.post(f"{BASE}/oauth/token", data=form, timeout=5)).json()
    print(f"    {tokens}")
    bearer = {"Authorization": f"Bearer {tokens['access_token']}"}
    # (E) call the API with the access token
    show(requests.get(f"{BASE}/oauth/api/devices", headers=bearer, timeout=5))                  # 200
    show(requests.post(f"{BASE}/oauth/api/devices", headers=bearer, json={}, timeout=5),
         "WWW-Authenticate")                                                                    # 403 scope
    show(requests.post(f"{BASE}/oauth/token", data=form, timeout=5))                            # code reused
    time.sleep(tokens["expires_in"] + 0.5)
    show(requests.get(f"{BASE}/oauth/api/devices", headers=bearer, timeout=5), "WWW-Authenticate")  # expired
    refresh = {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"],
               "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    new = show(requests.post(f"{BASE}/oauth/token", data=refresh, timeout=5)).json()
    print(f"    new access_token: {new['access_token']} (no user login needed)")
    show(requests.get(f"{BASE}/oauth/api/devices",
                      headers={"Authorization": f"Bearer {new['access_token']}"}, timeout=5))  # 200


def main():
    basic_auth()
    custom_token()
    api_key()
    cookies()
    oauth_code_flow()


if __name__ == "__main__":
    main()
