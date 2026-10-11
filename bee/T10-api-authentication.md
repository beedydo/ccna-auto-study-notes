---
id: T10
title: "API authentication"
owner: Beedy
blueprint: "2.7"
primary_domain: D2
cbt_coverage: "Full"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-10
teach_back: 2026-10-12
cross_study: 2026-10-22
---

# T10 · API authentication

> Owner: **Beedy** · Blueprint: **2.7** · CBT coverage: **Full** · Learn by 2026-10-10 · Teach-back 2026-10-12

![T10 at a glance: every API auth method as one card](../assets/T10/00-overview.png)

*Every T10 concept on one page. Each card is one auth method with the same parts: how you get the credential, what goes on the wire, the Cisco platforms that use it, and a red trap. The bottom strip is 401 vs 403 and credential handling. Numbers are the order of calls in `labs/T10/auth_tour.py`.*

## TL;DR (teach-back card)

- **Read the header to name the method.** `Authorization: Basic <base64 user:pass>` = Basic. A token fetched from a login call and then sent as `X-Auth-Token` / `X-auth-access-token` = custom token (Catalyst Center (DNA Center) / Secure Firewall Management Center (FMC)). A static key from a portal = API key (Meraki). `Set-Cookie` after login = session cookie (APIC `APIC-cookie`, SD-WAN Manager (vManage) `JSESSIONID` + `X-XSRF-TOKEN`). Redirect → code → token exchange = OAuth 2.0 (Webex integrations).
- **Base64 is encoding, not encryption.** Anyone can decode `YWRtaW46QzFzY28xMjM0NQ==` back to `admin:C1sco12345`, so every method depends on HTTPS. Secrets come from env vars or a vault, never from the script or Git.
- **In Python:** `auth=(user, pw)` → Basic. `headers={"X-Auth-Token": t}` or `{"Authorization": f"Bearer {t}"}` → token/key. `requests.Session()` keeps cookies and `s.headers.update()` headers for every later call.
- **Trap:** `401` = authentication failed (no, bad or expired credential, so log in again). `403` = authenticated but not allowed (role or OAuth scope), so a fresh token for the same user won't help.

## Concepts

Every section below explains one part of the same program. Read it once first.

- `labs/T10/mock_auth_api.py` is a local mock server (Python stdlib only) on `http://127.0.0.1:8110`. Each path prefix copies the **auth shape** of one Cisco platform. The paths are invented, so don't learn them as real platform URLs.
- `labs/T10/auth_tour.py` (below) is the **reference program**. It's one client that logs in with each of the six methods and triggers the matching `401`/`403` errors.
- `labs/T10/mock-creds.env` holds the **fake** credentials. The program reads them from environment variables only.
- To run it all: `bash labs/T10/run_lab.sh`. It starts the mock, loads the env file, runs the client, prints the server access-log lines that leaked a secret, then stops the mock.
- [T07's mock API](T07-rest-fundamentals-http-codes.md#concepts) already did Basic → Bearer. T10 widens it to every method on the exam.

**Mock API map** (the mock's own paths; the real-platform column is the shape it copies):

| Section | Mock path | Credential in | Copies the shape of |
|---|---|---|---|
| 1 | `GET /basic/devices` | `Authorization: Basic …` on every call | RESTCONF on IOS XE (T16) |
| 2 | `POST /catc/auth/token` → `GET /catc/devices` | Basic once → `{"Token": …}` → `X-Auth-Token` | Catalyst Center (DNA Center) |
| 3 | `GET /key/devices` | `X-API-Key` header or `?api_key=` | Meraki dashboard API key |
| 4a | `POST /sdwan/j_security_check` → `/sdwan/dataservice/…` | form login → `JSESSIONID` cookie, + `X-XSRF-TOKEN` on writes | SD-WAN Manager (vManage) |
| 4b | `POST /apic/api/aaaLogin.json` → `/apic/api/class/…` | JSON login → token + `APIC-cookie` | ACI APIC |
| 5 | `/oauth/authorize` → `/oauth/token` → `/oauth/api/devices` | code → `Authorization: Bearer <access_token>` | Webex integration (OAuth 2.0) |

**`labs/T10/auth_tour.py`**

```python
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
```

**Output** (`bash labs/T10/run_lab.sh`; token and cookie values are random on every run):

```
== 1. Basic auth: credentials on EVERY request ==
>>> GET http://127.0.0.1:8110/basic/devices
<<< 401 Unauthorized
    WWW-Authenticate: Basic realm="mock"
    body: {"error": "missing or invalid credentials"}
>>> GET http://127.0.0.1:8110/basic/devices
<<< 200 OK
    sent:    Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==
    decoded: admin:C1sco12345   <- base64 is encoding, not encryption

== 2. Custom token: Basic once -> token -> X-Auth-Token on every call ==
>>> POST http://127.0.0.1:8110/catc/auth/token
<<< 200 OK
    token in body: tok-1f602c7a
>>> GET http://127.0.0.1:8110/catc/devices
<<< 200 OK
>>> GET http://127.0.0.1:8110/catc/devices
<<< 401 Unauthorized
    body: {"error": "missing or invalid credentials"}
>>> POST http://127.0.0.1:8110/catc/devices
<<< 403 Forbidden
    body: {"error": "role 'read' may not add devices"}

== 3. API key: static key, no login step ==
>>> GET http://127.0.0.1:8110/key/devices
<<< 200 OK
>>> GET http://127.0.0.1:8110/key/devices?api_key=6bec40cf957de430a6f1f2baa056b99a4fac9ea0
<<< 200 OK
>>> GET http://127.0.0.1:8110/key/devices
<<< 401 Unauthorized
    WWW-Authenticate: ApiKey realm="mock"
    body: {"error": "missing or invalid credentials"}

== 4a. Session cookie + XSRF header (SD-WAN Manager shape) ==
>>> POST http://127.0.0.1:8110/sdwan/j_security_check
<<< 200 OK
    Set-Cookie: JSESSIONID=56F61F31D6D2721D; Path=/sdwan; HttpOnly
    cookie jar now holds: ['JSESSIONID']
>>> GET http://127.0.0.1:8110/sdwan/dataservice/device
<<< 200 OK
>>> GET http://127.0.0.1:8110/sdwan/dataservice/device
<<< 401 Unauthorized
    body: {"error": "no valid JSESSIONID cookie"}
>>> GET http://127.0.0.1:8110/sdwan/dataservice/client/token
<<< 200 OK
>>> POST http://127.0.0.1:8110/sdwan/dataservice/template
<<< 403 Forbidden
    body: {"error": "missing or wrong X-XSRF-TOKEN"}
>>> POST http://127.0.0.1:8110/sdwan/dataservice/template
<<< 201 Created

== 4b. Login body -> token + APIC-cookie (ACI APIC shape) ==
>>> POST http://127.0.0.1:8110/apic/api/aaaLogin.json
<<< 200 OK
    Set-Cookie: APIC-cookie=apic-a3c4b742; Path=/apic; HttpOnly
    token in body: apic-a3c4b742
>>> GET http://127.0.0.1:8110/apic/api/class/fabricNode.json
<<< 200 OK

== 5. OAuth 2.0 authorization-code grant (Webex integration shape) ==
>>> GET http://127.0.0.1:8110/oauth/authorize?response_type=code&client_id=demo-app&redirect_uri=http%3A%2F%2F127.0.0.1%3A9000%2Fcallback&scope=devices%3Aread&state=1bbde62a
<<< 302 Found
    Location: http://127.0.0.1:9000/callback?code=5005cd8804&state=1bbde62a
>>> POST http://127.0.0.1:8110/oauth/token
<<< 200 OK
    {'access_token': 'acc-678ea5f7', 'token_type': 'Bearer', 'expires_in': 2, 'refresh_token': 'ref-02281d06', 'scope': 'devices:read'}
>>> GET http://127.0.0.1:8110/oauth/api/devices
<<< 200 OK
>>> POST http://127.0.0.1:8110/oauth/api/devices
<<< 403 Forbidden
    WWW-Authenticate: Bearer error="insufficient_scope", scope="devices:write"
    body: {"error": "insufficient_scope"}
>>> POST http://127.0.0.1:8110/oauth/token
<<< 400 Bad Request
    body: {"error": "invalid_grant"}
>>> GET http://127.0.0.1:8110/oauth/api/devices
<<< 401 Unauthorized
    WWW-Authenticate: Bearer error="invalid_token"
    body: {"error": "invalid_token"}
>>> POST http://127.0.0.1:8110/oauth/token
<<< 200 OK
    new access_token: acc-00c50aa9 (no user login needed)
>>> GET http://127.0.0.1:8110/oauth/api/devices
<<< 200 OK

== Server access log: lines that contain a secret ==
ACCESS "GET /key/devices?api_key=6bec40cf957de430a6f1f2baa056b99a4fac9ea0 HTTP/1.1" 200
```

### T10.01 · Concepts

**Must cover:**

- [x] Authentication = proving identity (who you are)
- [x] Authorisation = permissions after login (what you may do)
- [x] 401 relates to authentication; 403 to authorisation

**Notes:**

- **Authentication (AuthN)** = the server checks **who** you are: password, token, key, cookie or certificate.
- **Authorisation (AuthZ)** = the server checks **what** that identity may do: role (admin vs read-only) or OAuth scope.
- AuthN always comes first. The server can't decide what you may do until it knows who you are.

![Authentication vs authorisation](../assets/T10/01-authn-vs-authz.png)

*Fail the first check → 401. Pass it but fail the second → 403. Only passing both gets a 2xx.*

| Code | Name (the exam uses these) | Means | Fix | In the program |
|---|---|---|---|---|
| `401` | Unauthorized (really "unauthenticated") | no, wrong or expired credential | send or refresh the credential | section 1 first call; section 2 `tok-wrong`; section 5 after expiry |
| `403` | Forbidden | identity known, action not allowed | another account, role or scope | section 2 viewer POST; section 4a no XSRF; section 5 `insufficient_scope` |

- `401` responses carry `WWW-Authenticate`, which names the scheme the server wants (`Basic realm="mock"`, `Bearer error="invalid_token"`). See [T07.06](T07-rest-fundamentals-http-codes.md#t0706--headers).
- The name "Unauthorized" is historical. 401 is about **authentication**.

### T10.02 · Basic auth

**Must cover:**

- [x] Header: Authorization: Basic <base64("user:password")>
- [x] Base64 is encoding, not encryption → anyone can decode it
- [x] Must be used over HTTPS
- [x] Sent on every request (or once to obtain a token)
- [x] Often used only to call the token endpoint (e.g. Catalyst Center)

**Notes:**

- **Recipe (RFC 7617):** join `user` + `:` + `password` → base64-encode it → send `Authorization: Basic <result>`.
  - The username can't contain `:`, because the first colon splits user from password.
  - RFC example: `Aladdin` / `open sesame` → `Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==`.
- `basic_auth()` in the program: the first call without credentials gets `401` + `WWW-Authenticate: Basic realm="mock"`. Then `auth=(USER, PASSWORD)` makes `requests` build `Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==`, and one `base64.b64decode()` gives back `admin:C1sco12345`.
- **Base64 is encoding, not encryption.** There's no key, so anyone who sees the header can reverse it. RFC 7617 calls cleartext password transmission the scheme's "most serious flaw", so use it only over **HTTPS** (TLS encrypts the whole request, headers included).
- **Two ways Basic is used:**

| Pattern | Credentials cross the wire | Where you see it |
|---|---|---|
| Basic on **every** request (section 1) | every call | RESTCONF on IOS XE, NX-API (T16, T17) |
| Basic **once** to a token endpoint (section 2) | once; then a token | Catalyst Center `POST /dna/system/api/v1/auth/token` (⚠ verify), FMC `generatetoken` |

![Basic auth on every request](../assets/T10/02-basic-auth.png)

*The same Base64 string goes out on every call, and the server is stateless, so it checks the password each time.*

### T10.03 · Custom token

**Must cover:**

- [x] Step 1: authenticate (often basic auth) to a login endpoint
- [x] Step 2: receive a token in the body, header or cookie
- [x] Step 3: send the token on each call in a custom or standard header
- [x] Examples: X-Auth-Token (Catalyst Center), Authorization: Bearer <token> (Webex, FMC uses X-auth-access-token)
- [x] Tokens expire → refresh or log in again

**Notes:**

- **Why tokens:** the password is sent once. Every later call carries a short-lived token instead, which can expire and be revoked without touching the password.
- `custom_token()` in the program:
  1. `requests.post(".../catc/auth/token", auth=HTTPBasicAuth(USER, PASSWORD))` → `200` with `{"Token": "tok-…"}` in the **body**.
  2. `s.headers.update({"X-Auth-Token": token, ...})` → every call on `s` now carries the token.
  3. A wrong token → `401`. The viewer's valid token on a write → `403` (authenticated, not authorised).

![Custom token flow](../assets/T10/03-token-flow.png)

*Yellow = one Basic call. Green = the token replaces the password on every call. Red = expiry gives 401, then log in again.*

- **Where the token comes back and where it goes**, by platform (header names are from the official Cisco Python SDK source; ⚠ verify against the API docs):

| Platform | Login call | Token comes back in | Send it as |
|---|---|---|---|
| Catalyst Center (DNA Center) | `POST /dna/system/api/v1/auth/token` + Basic | body: `{"Token": "…"}` | `X-Auth-Token: <token>` |
| Secure Firewall Management Center (FMC) | `POST /api/fmc_platform/v1/auth/generatetoken` + Basic | **response headers** `X-auth-access-token`, `X-auth-refresh-token` (+ `DOMAIN_UUID`) | `X-auth-access-token: <token>` |
| Webex | none (token from the portal or OAuth) | n/a | `Authorization: Bearer <token>` |
| ACI APIC | `POST /api/aaaLogin.json` with JSON body | body `imdata[0].aaaLogin.attributes.token` **and** cookie | `APIC-cookie` (T10.05) |

- **Standard vs custom header:** `Authorization: Bearer <token>` is the standard (RFC 6750). `X-Auth-Token` and `X-auth-access-token` are vendor-specific. Both kinds carry a token, so if an exam snippet shows either, the answer is "token auth".
- **Expiry:** tokens are short-lived. On `401`, get a new one: either log in again, or use a **refresh** call if the API has one.
  - FMC: `POST /api/fmc_platform/v1/auth/refreshtoken` with both tokens in headers. The `fmcapi` SDK assumes a 30-min lifetime and 3 refreshes before a full re-login (⚠ verify).
  - APIC: `/api/aaaRefresh.json`. Catalyst Center: log in again (⚠ verify token lifetime, often quoted as 60 min).

### T10.04 · API key

**Must cover:**

- [x] Long-lived static key generated in a portal, tied to a user/account
- [x] Sent in a header (e.g. X-Cisco-Meraki-API-Key or Authorization: Bearer) or query string
- [x] Simple, but full access if leaked → rotate and store securely
- [x] Query-string keys can end up in logs (avoid)

**Notes:**

- **API key** = a long random string you generate once in a web portal, tied to a user or account. There's **no login call**: the key itself is the credential on every request.
- `api_key()` in the program sends the same key two ways. Both return `200`, but the access log at the end of the output shows the difference:
  - Header `X-API-Key: …` → the server log line is just `GET /key/devices`.
  - Query string `?api_key=…` → the **full key** is in the log line: `ACCESS "GET /key/devices?api_key=6bec40cf… HTTP/1.1" 200`.

![API key in header vs query string](../assets/T10/04-api-key-placement.png)

*Same key, same 200. Only the query-string version gets copied into access logs, proxy logs and browser history.*

- **Meraki:** the dashboard API key goes in `Authorization: Bearer <key>`. The official `meraki` Python SDK sends this header. The older `X-Cisco-Meraki-API-Key: <key>` header is still widely shown in docs and exam material (⚠ verify which one Cisco treats as current). Recognise both.
- **Risk:** the key is long-lived and usually has the account's full rights. If it leaks, it works until someone revokes it, so rotate it and store it like a password (T10.08). RFC 6750 says tokens in URIs "SHOULD NOT be used" unless there's no alternative.
- **API key vs token:** a key is created **by a person in a portal** and lives for months. A token is created **by a login call** and lives for minutes or hours.

### T10.05 · Session/cookie

**Must cover:**

- [x] Server returns Set-Cookie after login; client sends the cookie back
- [x] APIC: aaaLogin returns a token, set as cookie APIC-cookie
- [x] SD-WAN Manager: JSESSIONID cookie plus X-XSRF-TOKEN header
- [x] requests.Session() keeps cookies automatically

**Notes:**

- **Cookie auth:** after login the server sends `Set-Cookie: name=value`. The client stores it and sends `Cookie: name=value` on later calls. The server looks the value up to find your session.
- `requests.Session()` has a **cookie jar**: it stores every `Set-Cookie` and replays it automatically. A bare `requests.get()` has no memory, which is why section 4a's second GET (no Session) gets `401`.
- **SD-WAN Manager (vManage) shape**, `cookies()` part 4a. The steps match the `catalystwan` SDK's `vmanage_auth.py` (⚠ verify the paths in the SD-WAN API docs):
  1. `POST /j_security_check` with **form** fields `j_username`, `j_password` → `Set-Cookie: JSESSIONID=…`.
  2. `GET /dataservice/client/token` (with the cookie) → the body **is** the XSRF token.
  3. Writes (`POST`/`PUT`/`DELETE`) need the cookie **plus** the header `X-XSRF-TOKEN: <token>`. Cookie only → `403` in the mock.
- **Why XSRF:** a browser sends cookies automatically, so a malicious page could trigger a write using your cookie (cross-site request forgery, T30). A header the attacker can't read or set blocks that.

![SD-WAN Manager style cookie + XSRF session](../assets/T10/05-cookie-session.png)

*Steps 1–2: login sets the cookie. 3–4: the Session sends it back automatically. 5–8: writes also need the XSRF header.*

- **ACI APIC shape**, part 4b: `POST /api/aaaLogin.json` with `{"aaaUser": {"attributes": {"name": …, "pwd": …}}}`. The reply body has `imdata[0].aaaLogin.attributes.token` (and `refreshTimeoutSeconds`), and the same token comes back as cookie `APIC-cookie`. Later calls send the cookie. This structure matches the `acitoolkit` source. Full APIC queries are in [T19](../bob/T19-aci.md).

### T10.06 · OAuth 2.0 (awareness)

**Must cover:**

- [x] Delegated access without sharing the password
- [x] Access token (short-lived) + refresh token (to get new access tokens)
- [x] Scopes limit what the token can do
- [x] Webex integrations use OAuth; bots use a long-lived bot token

**Notes:**

- **Problem OAuth solves:** an app wants to act **for a user** (read their Webex rooms) without ever seeing that user's password. That's called **delegated access**.
- **Four roles (RFC 6749):**
  - **resource owner**: the user
  - **client**: the app or integration
  - **authorization server**: logs the user in and issues tokens
  - **resource server**: the API
- **Authorization-code grant**, `oauth_code_flow()` in the program, steps (A)–(E) as in RFC 6749 §4.1:

![OAuth 2.0 authorization-code flow](../assets/T10/06-oauth-code-flow.png)

*The password goes only to the authorization server (step 2). The app gets a one-time code via the browser (3–4), swaps it with its client_secret (5–6), then uses the access token (7).*

![Animated OAuth 2.0 authorization-code flow](../assets/T10/08-oauth-code-flow.gif)

*Redirect to `/authorize` → user logs in at the auth server → `302` back with `code` + `state` → app POSTs the code + `client_secret` to `/token` → `access_token` + `refresh_token` → API call with `Bearer` → expiry → refresh. Fixes the misconception that the app collects the password, or that the code itself is the token.*

- **What each piece is:**

| Item | Lifetime | Who sees it | Used for |
|---|---|---|---|
| authorization `code` | ≤ 10 min (RFC recommends), **single use** | browser, app | swapped once for tokens. Reuse → `400 invalid_grant` (see output) |
| `state` | one flow | browser, app | anti-CSRF: the app checks it comes back unchanged |
| `client_secret` | long | app ↔ auth server only (back channel) | proves the app's identity at `/token` |
| **access token** | short (minutes to hours) | app → API | `Authorization: Bearer <access_token>` |
| **refresh token** | long | app → auth server | `grant_type=refresh_token` → new access token, **no user login** |
| **scope** | per token | all | limits what the token may do. Missing scope → `403 insufficient_scope` |

- In the output: the `devices:read` token can GET (`200`) but not POST (`403`, `WWW-Authenticate: Bearer error="insufficient_scope", scope="devices:write"`). After `expires_in` → `401 invalid_token`. The refresh grant then gives a new token without the user.
- **Other grant types (names only, awareness):** client credentials (app acts as itself, no user), plus the legacy implicit and password grants.
- **Webex** (⚠ verify the numbers on developer.webex.com):
  - **Integration** = OAuth app acting for a user. It uses `https://webexapis.com/v1/authorize` and `https://webexapis.com/v1/access_token`. The `webexpythonsdk` sends `grant_type=authorization_code`, `client_id`, `client_secret`, `code`, `redirect_uri`. Access tokens are often quoted as 14 days and refresh tokens as 90 days.
  - **Bot** = its own identity, with a long-lived **bot token** from the portal (no OAuth flow). It's sent as `Authorization: Bearer`.
  - **Personal access token** = your own token from the developer portal, for testing. Often quoted as 12 h.

### T10.07 · Python

**Must cover:**

- [x] requests.get(url, auth=("user", "pass")) or auth=HTTPBasicAuth(user, pw) → basic auth
- [x] headers={"X-Auth-Token": token} or {"Authorization": f"Bearer {token}"} → token/API key
- [x] Session object: s.headers.update({...}) for all later calls

**Notes:**

- One line per method, all taken from `auth_tour.py`:

| Method | `requests` code | Line in the program |
|---|---|---|
| Basic (tuple shorthand) | `requests.get(url, auth=(USER, PASSWORD))` | `basic_auth()` |
| Basic (explicit class) | `requests.post(url, auth=HTTPBasicAuth(USER, PASSWORD))` | `custom_token()` |
| Custom token header | `headers={"X-Auth-Token": token}` | `custom_token()` |
| Bearer token | `headers={"Authorization": f"Bearer {tokens['access_token']}"}` | `oauth_code_flow()` |
| API key header / query | `headers={"X-API-Key": API_KEY}` / `params={"api_key": API_KEY}` | `api_key()` |
| Form login + cookie | `s = requests.Session(); s.post(url, data={...})` | `cookies()` |
| JSON login | `s.post(url, json=login)` | `cookies()` 4b |
| Header on every later call | `s.headers.update({"X-XSRF-TOKEN": xsrf})` | `cookies()` 4a |

- `auth=("u", "p")` and `auth=HTTPBasicAuth("u", "p")` are **identical** (requests docs). Both build the Basic header for you, so don't base64-encode by hand.
- A `Session` keeps **cookies, `s.headers` and `s.auth`** across calls and reuses the TCP connection. Per-call `headers=` / `cookies=` are merged in for that call only and **not** remembered.
- `data=` sends a form (`application/x-www-form-urlencoded`, as `j_security_check` and the OAuth `/token` endpoint expect). `json=` sends JSON (as `aaaLogin.json` expects). See [T07.13](T07-rest-fundamentals-http-codes.md#t0713--media-types).
- More on `requests` (timeouts, `raise_for_status`, retries): [T11](T11-python-requests-scripting.md).

### T10.08 · Credential handling

**Must cover:**

- [x] Never hardcode secrets in scripts or commit them to Git
- [x] Use environment variables (os.environ["API_KEY"]) or a secrets vault
- [x] Use HTTPS so credentials are encrypted in transit

**Notes:**

- `require_env()` at the top of the program reads every secret from the environment and stops with a clear message if one is missing (`ERROR: environment variable LAB_API_KEY is not set …`). That's the same failure you'd want in CI.
  - `os.environ["X"]` raises `KeyError` if it's missing. `os.environ.get("X")` returns `None`, which makes a quieter failure later.
- Repo pattern (already in this repo): real values in `labs/.env`, which is git-ignored. Only fake values like `labs/T10/mock-creds.env` get committed. Load them with `set -a && source labs/.env && set +a`, or `docker run --env-file labs/.env`.
- For anything shared, use a vault or secrets manager (HashiCorp Vault, a CI secret store), plus the Cisco SDK env vars: `MERAKI_DASHBOARD_API_KEY`, `WEBEX_ACCESS_TOKEN`, `DNA_CENTER_USERNAME`/`DNA_CENTER_PASSWORD`.
- **HTTPS** encrypts the whole request, so headers, cookies and query strings are protected **in transit**. It doesn't stop a query-string key being written to the server's access log (T10.04).
- `verify=False` / `curl --insecure` turns off certificate checks, so a man-in-the-middle could read the credential. It's fine for a sandbox with a self-signed cert, but recognise it as a weakness in a code-review question. Deeper secret handling is in [T29](T29-secrets-encryption-data-handling.md).

### T10.09 · Exam angle

**Must cover:**

- [x] Match a header/code snippet to basic, token or API key
- [x] Know the method per platform: Meraki API key, Catalyst Center token, Webex bearer token, APIC cookie
- [x] Know why base64 is not secure

**Notes:**

![Identify the auth method from a snippet](../assets/T10/07-identify-method.png)

*First ask "Basic?", then ask "where did the credential come from?": a login call (custom header or cookie), a redirect + code (OAuth), or a portal (API key / static token).*

- **Platform quick reference** (every row is ⚠ verify against current docs; names from the Cisco SDK source):

| Platform | Method | Exactly what's sent |
|---|---|---|
| Meraki Dashboard | API key | `Authorization: Bearer <key>` (SDK) or `X-Cisco-Meraki-API-Key: <key>` (older) |
| Catalyst Center (DNA Center) | Basic → custom token | `X-Auth-Token: <Token>` |
| Webex | Bearer token (personal, bot or OAuth access token) | `Authorization: Bearer <token>` |
| ACI APIC | login → cookie | `Cookie: APIC-cookie=<token>` |
| SD-WAN Manager (vManage) | form login → cookie + XSRF | `Cookie: JSESSIONID=…` + `X-XSRF-TOKEN: …` |
| Secure Firewall Management Center (FMC) | Basic → custom token (in response headers) | `X-auth-access-token: <token>` |
| IOS XE RESTCONF / NX-API | Basic on every call | `Authorization: Basic <base64>` |

- **Why base64 isn't secure:** it's a reversible encoding with no key. `echo YWRtaW46QzFzY28xMjM0NQ== | base64 --decode` → `admin:C1sco12345`. Only TLS protects it.

## Exam traps

- **401 vs 403:** 401 = who are you? (missing, bad or expired credential → re-authenticate). 403 = I know you, but no (role or scope → a new token for the same user won't help).
- **Base64 ≠ encryption.** "Which statement about Basic auth is true?" → credentials are only encoded, so HTTPS is required.
- **`Bearer` is a scheme word.** `Authorization: Bearer <token>` for a token. `Authorization: Basic <base64>` for user:pass. Swapping them → `401` (curl drill step 6).
- **Catalyst Center ≠ Bearer.** It's `X-Auth-Token`. FMC is `X-auth-access-token`, and its token comes back in **response headers**, not the body.
- **API key vs token:** key = portal, static, long-lived, no login call. Token = from a login call, expires.
- **API key in the query string** works, but it leaks into logs and history. Prefer a header.
- **APIC = cookie** (`APIC-cookie` from `aaaLogin`). **SD-WAN Manager = `JSESSIONID` cookie + `X-XSRF-TOKEN`** on writes. A missing XSRF header on a POST → `403`, not `401`.
- **`requests.get()` doesn't remember cookies; `requests.Session()` does.** Per-call `headers=` aren't remembered either. Use `s.headers.update()`.
- **`auth=("u","p")` already does the base64.** Don't also add `headers={"Authorization": "Basic u:p"}` (that's raw text, not base64 → `401`).
- **OAuth:** the user's password goes to the **authorization server**, never to the app. The **code** isn't the token: it's single-use and swapped (with `client_secret`) for the access token. The **refresh token** gets a new access token without the user. **Scope** limits the token.
- **Webex bot vs integration:** bot = its own long-lived bot token, no OAuth. Integration = OAuth, acting for a user.
- **HTTPS protects in transit only.** It doesn't stop a secret hardcoded in a script or committed to Git.

## Examples

### 1. Run the reference program

Needs Python 3, `requests` and curl. No DevNet sandbox.

```bash
python3 -m venv /tmp/t10venv && /tmp/t10venv/bin/pip install requests
PATH=/tmp/t10venv/bin:$PATH bash labs/T10/run_lab.sh                        # mock + auth_tour.py
bash labs/T10/run_lab.sh labs/T10/curl_drill.sh                             # mock + curl drill
```

By hand, in two terminals:

```bash
python3 labs/T10/mock_auth_api.py                                           # terminal 1: leave running
set -a && source labs/T10/mock-creds.env && set +a && python3 labs/T10/auth_tour.py   # terminal 2
```

In the lab container (it already has `requests`):

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work --workdir /work ccna-auto-lab:latest bash labs/T10/run_lab.sh
```

**`labs/T10/run_lab.sh`**

```bash
#!/usr/bin/env bash
# Start the T10 mock auth API, load the fake credentials, run a client, show the
# server access log lines that leaked a secret, then stop the API.
# Usage:  bash labs/T10/run_lab.sh                         (runs auth_tour.py)
#         bash labs/T10/run_lab.sh labs/T10/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/auth_tour.py}"
LOG="$(mktemp)"

python3 "$HERE/mock_auth_api.py" > "$LOG" 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; rm -f "$LOG"' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8110/" && break
  sleep 0.25
done

set -a && source "$HERE/mock-creds.env" && set +a

case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac

echo
echo "== Server access log: lines that contain a secret =="
grep "api_key=" "$LOG" || echo "(none)"
```

### 2. curl drill (`labs/T10/curl_drill.sh`)

```bash
#!/usr/bin/env bash
# T10 curl drill: the same auth methods as auth_tour.py, with curl.
# Run via:  bash labs/T10/run_lab.sh labs/T10/curl_drill.sh   (starts the API, loads mock-creds.env)
set -u
BASE="http://127.0.0.1:8110"

echo "== 1. --user builds the Basic header for you (see it with --verbose)"
curl --silent --verbose --output /dev/null --user "$LAB_USER:$LAB_PASS" "$BASE/basic/devices" 2>&1 \
  | grep -E "^> (GET|Authorization)|^< HTTP"

echo; echo "== 2. Same header by hand: base64 of user:pass"
B64=$(printf '%s' "$LAB_USER:$LAB_PASS" | base64)
echo "Authorization: Basic $B64"
printf '%s' "$B64" | base64 --decode; echo "   <- anyone can decode it"

echo; echo "== 3. Custom token: POST with Basic, then X-Auth-Token"
TOKEN=$(curl --silent --request POST --user "$LAB_USER:$LAB_PASS" "$BASE/catc/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['Token'])")
echo "TOKEN=$TOKEN"
curl --silent --header "X-Auth-Token: $TOKEN" "$BASE/catc/devices"; echo

echo; echo "== 4. API key in a header"
curl --silent --header "X-API-Key: $LAB_API_KEY" "$BASE/key/devices"; echo

echo; echo "== 5. Cookie jar: --cookie-jar saves Set-Cookie, --cookie sends it back"
JAR="$(mktemp)"
curl --silent --output /dev/null --cookie-jar "$JAR" --request POST \
  --data-urlencode "j_username=$LAB_USER" --data-urlencode "j_password=$LAB_PASS" \
  "$BASE/sdwan/j_security_check"
curl --silent --cookie "$JAR" "$BASE/sdwan/dataservice/device"; echo
rm -f "$JAR"

echo; echo "== 6. Wrong scheme word: Bearer where the API wants Basic -> 401"
curl --silent --include --header "Authorization: Bearer $B64" "$BASE/basic/devices" | head -1
```

Output (`bash labs/T10/run_lab.sh labs/T10/curl_drill.sh`):

```
== 1. --user builds the Basic header for you (see it with --verbose)
> GET /basic/devices HTTP/1.1
> Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==
< HTTP/1.1 200 OK

== 2. Same header by hand: base64 of user:pass
Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==
admin:C1sco12345   <- anyone can decode it

== 3. Custom token: POST with Basic, then X-Auth-Token
TOKEN=tok-170d26c9
{"devices": [{"id": 1, "hostname": "csr1"}, {"id": 2, "hostname": "n9k1"}]}

== 4. API key in a header
{"devices": [{"id": 1, "hostname": "csr1"}, {"id": 2, "hostname": "n9k1"}]}

== 5. Cookie jar: --cookie-jar saves Set-Cookie, --cookie sends it back
{"data": [{"id": 1, "hostname": "csr1"}, {"id": 2, "hostname": "n9k1"}]}

== 6. Wrong scheme word: Bearer where the API wants Basic -> 401
HTTP/1.1 401 Unauthorized

== Server access log: lines that contain a secret ==
(none)
```

- Step 1: `--user` is curl's Basic auth, and `--verbose` shows the header it built. It's the same string Python built.
- Step 5: `--cookie-jar FILE` saves `Set-Cookie` and `--cookie FILE` sends it back. That's curl's version of `requests.Session()`.
- Step 6: a valid-looking credential with the wrong scheme word is still `401`.

### 3. Break it on purpose

Copy `labs/T10/auth_tour.py`, make one edit, run it with `bash labs/T10/run_lab.sh /path/to/copy.py`. All four were run, and the result shown is the real first changed line.

| Edit | What changes in the output | Lesson |
|---|---|---|
| In `custom_token()`, change `{"X-Auth-Token": token, …}` to `{"Authorization": f"Bearer {token}", …}` | the `GET /catc/devices` after the token → `<<< 401 Unauthorized` | right token, wrong header name; Catalyst Center wants `X-Auth-Token` |
| In `cookies()`, delete `s.headers.update({"X-XSRF-TOKEN": xsrf})` | the second `POST /sdwan/dataservice/template` → `<<< 403 Forbidden` · `missing or wrong X-XSRF-TOKEN` | cookie authenticates you, but writes also need the XSRF header |
| In `oauth_code_flow()`, change the `redirect_uri` in `form` to `"http://127.0.0.1:9000/other"` | `POST /oauth/token` → `<<< 400 Bad Request` · `invalid_grant`, then `KeyError: 'access_token'` | the code is bound to the original `redirect_uri`; check the status before reading the body |
| Run without `LAB_API_KEY` in the env (`unset LAB_API_KEY`) | `ERROR: environment variable LAB_API_KEY is not set (see labs/T10/mock-creds.env)` | fail fast on a missing secret instead of sending an empty credential |

### 4. Decode a Basic header (drill)

```bash
printf '%s' 'netops:Pa55word!' | base64                  # -> bmV0b3BzOlBhNTV3b3JkIQ==
printf '%s' 'bmV0b3BzOlBhNTV3b3JkIQ==' | base64 --decode; echo   # -> netops:Pa55word!
python3 -c "import base64; print(base64.b64encode(b'netops:Pa55word!').decode())"
```

- Use `printf '%s'`, not `echo`. `echo` adds a newline, so you'd encode `user:pass\n` and get a different string.

### 5. Real Cisco APIs (DevNet Sandbox), not run

⚠ verify hosts, credentials and paths at developer.cisco.com/sandbox and in each API reference before running. Put values in `labs/.env` (git-ignored).

```bash
set -a && source labs/.env && set +a

# Catalyst Center: Basic once -> Token in body -> X-Auth-Token
TOKEN=$(curl --silent --insecure --request POST --user "$DNAC_USER:$DNAC_PASS" \
  "https://$DNAC_HOST/dna/system/api/v1/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['Token'])")
curl --silent --insecure --header "X-Auth-Token: $TOKEN" \
  "https://$DNAC_HOST/dna/intent/api/v1/network-device"

# Meraki: API key, no login call
curl --silent --header "Authorization: Bearer $MERAKI_DASHBOARD_API_KEY" \
  "https://api.meraki.com/api/v1/organizations"

# Webex: personal/bot token as Bearer
curl --silent --header "Authorization: Bearer $WEBEX_ACCESS_TOKEN" \
  "https://webexapis.com/v1/people/me"

# ACI APIC: aaaLogin -> APIC-cookie in a cookie jar
curl --silent --insecure --cookie-jar /tmp/apic.jar --request POST \
  --header "Content-Type: application/json" \
  --data "{\"aaaUser\": {\"attributes\": {\"name\": \"$APIC_USER\", \"pwd\": \"$APIC_PASS\"}}}" \
  "https://$APIC_HOST/api/aaaLogin.json"
curl --silent --insecure --cookie /tmp/apic.jar "https://$APIC_HOST/api/class/fabricNode.json"
```

## Practice questions

**Q1.** Refer to the exhibit:

```python
r = requests.get(
    "https://10.10.20.48/restconf/data/ietf-interfaces:interfaces",
    auth=("developer", os.environ["IOSXE_PASS"]),
    headers={"Accept": "application/yang-data+json"},
    verify=True,
)
```

Which authentication method does the script use?
A. API key  B. OAuth 2.0 bearer token  C. HTTP Basic  D. Session cookie

<details><summary>Answer</summary>

**C.** `auth=(user, password)` makes `requests` send `Authorization: Basic <base64 user:pass>` on this call. There's no token or key. (T10.02, T10.07)
</details>

**Q2.** A script sends `Authorization: Basic bmV0b3BzOlBhNTV3b3JkIQ==` over plain HTTP. What can an attacker who captures the packet do?
A. Nothing; the value is encrypted with the server's key  B. Decode it to the username and password  C. Only replay it within 10 minutes  D. Read the username but not the password

<details><summary>Answer</summary>

**B.** Base64 is a reversible encoding with no key. It decodes to `netops:Pa55word!`. Only TLS (HTTPS) protects it in transit. (T10.02, T10.09)
</details>

**Q3.** A script gets a token from Catalyst Center, then gets `401 Unauthorized` on `GET /dna/intent/api/v1/network-device` while sending `Authorization: Bearer <token>`. The token is less than a minute old. What fixes it?
A. Request a new token  B. Send the token in an `X-Auth-Token` header  C. Use an account with the admin role  D. Base64-encode the token

<details><summary>Answer</summary>

**B.** Catalyst Center expects the token in its custom `X-Auth-Token` header. A fresh token in the wrong header is still unauthenticated (break-it edit 1). A role problem would give `403`. (T10.03)
</details>

**Q4.** Match each platform to how a script normally authenticates its API calls.
Platforms: Meraki Dashboard · ACI APIC · Webex (bot) · Catalyst Center
Methods: cookie set by a login call · static key from the dashboard · custom token header from a token endpoint · long-lived bearer token from the developer portal

<details><summary>Answer</summary>

Meraki → static key from the dashboard. APIC → cookie set by `aaaLogin` (`APIC-cookie`). Webex bot → long-lived bearer token. Catalyst Center → `X-Auth-Token` from `/auth/token`. (T10.09)
</details>

**Q5.** Put the OAuth 2.0 authorization-code steps in order:
1. App POSTs the code and its client secret to the token endpoint
2. User logs in at the authorization server and approves the scopes
3. App calls the API with `Authorization: Bearer <access_token>`
4. App redirects the user's browser to the authorization endpoint with `response_type=code`
5. Authorization server redirects back to the app's `redirect_uri` with `code` and `state`

<details><summary>Answer</summary>

**4 → 2 → 5 → 1 → 3.** The app never sees the password (step 2 is at the authorization server), and the code is swapped for the token on the back channel. (T10.06)
</details>

**Q6.** An OAuth access token with scope `devices:read` gets `403` and `WWW-Authenticate: Bearer error="insufficient_scope"` on a POST. What's the correct fix?
A. Use the refresh token to get a new access token  B. Re-run the authorization flow and request a write scope  C. Retry with exponential backoff  D. Send the token as a query parameter

<details><summary>Answer</summary>

**B.** 403 = authorisation. Refreshing returns a token with the **same** scope, so the app must ask the user to grant a write scope. (T10.01, T10.06)
</details>

**Q7.** Complete the code so that every later call sends the SD-WAN Manager XSRF token, and the session cookie from login is reused automatically:

```python
s = requests.__________()
s.post(f"{BASE}/j_security_check", data={"j_username": USER, "j_password": PASSWORD})
xsrf = s.get(f"{BASE}/dataservice/client/token").text
s.__________.update({"X-XSRF-TOKEN": xsrf})
```

<details><summary>Answer</summary>

`requests.Session()` and `s.headers.update(...)`. The Session's cookie jar keeps `JSESSIONID`, and session headers apply to every later call. Per-call `headers=` would apply only once. (T10.05, T10.07)
</details>

**Q8.** Which two practices protect an API key used by an automation script? (Choose two.)
A. Pass it as `?api_key=` so it's not in the headers  B. Read it from an environment variable or a secrets vault  C. Base64-encode it in the script  D. Rotate it, and revoke it if it leaks  E. Commit it to a private Git repo

<details><summary>Answer</summary>

**B, D.** Query strings end up in logs, base64 is reversible, and private repos still leak (forks, clones, CI logs). (T10.04, T10.08)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T10.1 | Video | Authentication with HTTP and REST | 27 | CBT module |

- Skip / low priority: Tool setup

## Sources

- Overview image: HTML source `assets/T10/00-overview.html`, rendered to PNG (see `assets/README.md`). Diagrams: Mermaid sources in `assets/T10/*.mmd`. Animation: `assets/T10/08-oauth-code-flow-anim.html` → `.gif`.
- RFC 7617, HTTP Basic auth (user-pass format, colon rule, Aladdin example, cleartext flaw, `WWW-Authenticate: Basic realm=…`): https://www.rfc-editor.org/rfc/rfc7617
- RFC 6749, OAuth 2.0 (roles, grant types, auth-code steps A–E, `state` anti-CSRF, code ≤ 10 min single use, token response fields, refresh grant, TLS at token endpoint): https://www.rfc-editor.org/rfc/rfc6749
- RFC 6750, Bearer token usage (header recommended, URI query "SHOULD NOT", `invalid_token` 401, `insufficient_scope` 403): https://www.rfc-editor.org/rfc/rfc6750
- RFC 9110, HTTP semantics (401 + `WWW-Authenticate`, 403): https://www.rfc-editor.org/rfc/rfc9110
- requests docs, Authentication (`auth=` tuple = `HTTPBasicAuth`, netrc) and Advanced (Session persists cookies, headers, `auth`; method-level params not persisted): https://requests.readthedocs.io/en/latest/user/authentication/ · https://requests.readthedocs.io/en/latest/user/advanced/
- Python `base64`, `os.environ`, `http.server`: https://docs.python.org/3/library/base64.html · https://docs.python.org/3/library/os.html#os.environ · https://docs.python.org/3/library/http.server.html
- Official Cisco SDK source code from PyPI, read locally because developer.cisco.com failed TLS from this machine:
  - `meraki` 4.6.0: `Authorization: Bearer`, `MERAKI_DASHBOARD_API_KEY`
  - `dnacentersdk` 2.11.4: `/dna/system/api/v1/auth/token`, Basic, `.Token`, `X-Auth-Token`
  - `webexpythonsdk` 2.0.6: `Authorization: Bearer`, `access_token` endpoint, `grant_type=authorization_code`/`refresh_token`
  - `catalystwan` 0.41.6: `j_security_check`, `JSESSIONID`, `/dataservice/client/token`, `x-xsrf-token`
  - `fmcapi`: `auth/generatetoken`, `X-auth-access-token`/`X-auth-refresh-token` in response headers, `TOKEN_LIFETIME = 60 * 30`, `MAX_REFRESHES = 3`
  - `acitoolkit`: `/api/aaaLogin.json`, `aaaUser`, `imdata[0].aaaLogin.attributes.token`, `/api/aaaRefresh.json`
- Cisco 200-901 v1.1 exam topics (2.7): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## To verify

- ⚠ **developer.cisco.com and developer.webex.com were not reachable** this session (TLS check failed), and web search was unavailable. Platform facts come from the official Cisco SDK source code (listed in Sources), not from the API reference pages. Confirm each of these in the docs:
  - Catalyst Center: token path `/dna/system/api/v1/auth/token`, `Token` key, `X-Auth-Token` header, token lifetime (often quoted 60 min).
  - Meraki: `Authorization: Bearer <key>` (SDK) vs `X-Cisco-Meraki-API-Key` (older docs). Which one Cisco documents as current, and whether the exam still expects the older one.
  - FMC: `generatetoken`/`refreshtoken` paths, token lifetime ~30 min, max 3 refreshes (from `fmcapi` constants, not Cisco docs).
  - SD-WAN Manager: `j_security_check`, `/dataservice/client/token`, `X-XSRF-TOKEN` needed on POST/PUT/DELETE.
  - APIC: `APIC-cookie` name, `aaaLogin` reply structure, `aaaRefresh`.
  - Webex: integration access-token lifetime (~14 days), refresh-token lifetime (~90 days), personal access token (~12 h), bot token "doesn't expire". Authorize/token URLs.
- ⚠ Example 5 (real sandboxes) wasn't run: no sandbox access from this machine.
- ⚠ Docker command in Example 1: not run, because the lab image isn't built.
- Run locally (Python 3.14.6, requests 2.34.2, curl 8.7): the reference program, the curl drill and all four break-it edits. The output shown is real. Token, cookie and code values change on every run. The mock needs local port binding, which the Claude Code sandbox blocks, but it runs normally in your own terminal.
- The mock API is a teaching stand-in: its paths are invented, and only the auth **shape** copies each platform. Its 2-second OAuth access-token lifetime exists only to show expiry in the demo.
