"""T07 reference program: one REST session that hits every status code on the exam.

Start the mock API first:   python3 labs/T07/mock_api.py
Then in another terminal:   python3 labs/T07/rest_walkthrough.py

Python stdlib only (urllib), so every header and status line is visible.
T11 rebuilds the same calls with the `requests` library.
"""
import base64
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlencode

BASE_URL = os.environ.get("API_BASE", "http://127.0.0.1:8080/api/v1")   # scheme://host:port + base path
USER = os.environ.get("API_USER", "admin")
PASSWORD = os.environ.get("API_PASS", "C1sco12345")


def call(method, path, token=None, body=None, params=None, headers=None, show_body=True):
    """Send one request; print request line, status line, key headers and body."""
    url = BASE_URL + path
    if params:
        url += "?" + urlencode(params)                  # query parameters: ?key=value&key=value
    req_headers = {"Accept": "application/json"}        # format we want back
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()                # serialise the payload (T06)
        req_headers["Content-Type"] = "application/json"  # format we are sending
    req_headers.update(headers or {})

    request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    print(f"\n>>> {method} {url}")
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:               # urllib raises on 4xx/5xx
        response = err
    status, reason = response.status, response.reason
    raw = response.read().decode()

    print(f"<<< HTTP/1.1 {status} {reason}")            # status line: version, code, reason phrase
    for name in ("Content-Type", "Location", "Retry-After", "WWW-Authenticate", "Allow", "ETag"):
        if response.headers.get(name):
            print(f"    {name}: {response.headers[name]}")
    if raw and show_body:
        print(f"    body: {raw.strip()}")
    return status, response.headers, raw


def get_token():
    """POST credentials with Basic auth, get a bearer token back (T10 covers auth in depth)."""
    basic = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    status, _, raw = call("POST", "/auth/token", headers={"Authorization": f"Basic {basic}"})
    return json.loads(raw)["token"] if status == 200 else None


def main():
    print("== 1. Authenticate ==")
    call("GET", "/devices")                                          # 401: no token
    token = get_token()                                              # 200 + token in body

    print("\n== 2. Read (GET) ==")
    call("GET", "/devices", token, params={"role": "edge"})          # 200, query param filters
    status, headers, _ = call("GET", "/devices/1", token)            # 200, path param = id 1
    call("GET", "/devices/1", token, headers={"If-None-Match": headers["ETag"]})  # 304 Not Modified
    call("GET", "/devices/99", token)                                # 404: no such id
    call("GET", "/devices/1", token, headers={"Accept": "application/xml"})       # XML body

    print("\n== 3. Create (POST) ==")
    new = {"hostname": "edge3", "mgmt_ip": "10.10.20.50", "role": "edge", "os": "iosxe"}
    status, headers, _ = call("POST", "/devices", token, body=new)   # 201 + Location header
    new_path = headers["Location"].replace("/api/v1", "")
    call("POST", "/devices", token, body=new)                        # 409: duplicate hostname
    call("POST", "/devices", token, body={"hostname": "edge4"})      # 400: missing fields
    call("POST", "/devices", token, body=new,
         headers={"Content-Type": "text/plain"})                     # 415: wrong Content-Type

    print("\n== 4. Update (PUT vs PATCH) ==")
    call("PATCH", new_path, token, body={"role": "core"})            # 200, only role changes
    call("PUT", new_path, token, body={"hostname": "edge3"})         # 400: PUT needs every field
    call("PUT", new_path, token, body={**new, "role": "core"})       # 200, full replacement

    print("\n== 5. Delete ==")
    call("DELETE", new_path, token)                                  # 204: empty body
    call("DELETE", new_path, token)                                  # 404: already gone

    print("\n== 6. Wrong method, permissions, async ==")
    call("DELETE", "/devices", token)                                # 405 + Allow header
    viewer = json.loads(call("POST", "/auth/token", headers={
        "Authorization": "Basic " + base64.b64encode(b"viewer:viewonly").decode()})[2])["token"]
    call("POST", "/devices", viewer, body=new)                       # 403: valid token, wrong role
    call("POST", "/devices/1/backup", token)                         # 202 Accepted + job Location

    print("\n== 7. Redirects, rate limits, server errors ==")
    call("GET", "/old/devices", token, show_body=False)              # 301 followed silently -> 200
    for _ in range(3):
        call("GET", "/interfaces/stats", token)                      # 200, 200, then 429
    call("GET", "/devices/2/config", token)                          # 500: server bug
    call("GET", "/health")                                           # 503 + Retry-After


if __name__ == "__main__":
    main()
