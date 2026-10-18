# Teach-back 2 · 2026-10-18

30 min together: Beedy teaches 12 min, Bob teaches 12 min, 6 min swapping one question per topic.

## Beedy teaches

_~2.5 min per topic (5 topics in 12 min). Say the 3 points, show the trap (and the GIF where noted), then ask the question at the end. Order: T07 → T10 → T11 → T08 → T09._

### T07 · REST fundamentals, HTTP codes

- Key point 1: **Request = method + URI + headers + body.** POST to the collection creates (`201` + `Location`), GET reads, PUT replaces **all** fields, PATCH changes **some**, DELETE removes (`204`). Path param = which one (`/devices/1`), query = filter (`?role=edge`).
- Key point 2: **First digit first:** 2xx worked · 3xx look elsewhere / cache (`304`) · 4xx **you** fix the request · 5xx the **server** failed. Run `labs/T07` once: every code comes back for real.
- Key point 3: **REST = 6 constraints;** stateless (token on every call) and cacheable (`ETag` → `304`) are the tested ones. Safe = GET/HEAD/OPTIONS; idempotent = those + PUT/DELETE; POST is neither.
- Exam trap: **401 ≠ 403.** 401 = who are you (re-login). 403 = known but not allowed (new token won't help). Also 404 wrong URI vs 405 wrong method; 400 bad body vs 415 wrong `Content-Type`.
- Question for partner: DELETE `/devices/4` twice returns `204` then `404`. Is DELETE idempotent? → **Yes**: same end state (device gone); the code can differ.

### T08 · API consumption constraints

- Key point 1: **`429` + `Retry-After`:** sleep exactly that long, then send the **same** call. No header → capped backoff (1, 2, 4, 8 s). Cut calls with caching, batching, webhooks.
- Key point 2: **Pagination:** every page is `200`; "more" is only in the body (`total`, `total_pages`) or the `Link: rel="next"` header. Loop until no next.
- Key point 3: **Other limits:** `413` = body too big (split it) · always set `timeout=` · long job = `202` + `Location` → poll · `401` mid-script = token expired → refresh once · `Deprecation`/`Sunset` = migrate versions.
- Exam trap: **"Records missing, no error" = only page 1 was read**, not a timeout or permission issue. And `429` ≠ broken request: don't change the URL or re-auth, just wait.
- Question for partner: `429` vs `503`, who is the problem? → **429 = you** (too many calls, per client). **503 = the service** is down or overloaded for everyone. Both: wait and retry.

### T09 · API styles: REST vs RPC, sync vs async

- Key point 1: **Where is the verb?** REST: the HTTP method on a **noun** URI (`GET /devices/1`). RPC: a **named function** in the body, `POST` to one endpoint (JSON-RPC `"method": "getDevice"`, NETCONF `<rpc>`). SOAP: XML **Envelope > Body**, contract = **WSDL** (CUCM AXL).
- Key point 2: **Sync** = client waits for the full answer. **Async** = `202 Accepted` + task ID now, poll (or webhook) later. Use async for long jobs: provisioning, upgrades, CLI on many devices.
- Key point 3: **Catalyst Center (DNA Center) pattern:** POST → `202` + `taskId` → GET `/task/{taskId}` until `endTime` set (check `isError`) → read `fileId` → GET `/file/{fileId}`. Show the async GIF.
- Exam trap: **`202` ≠ done**, and the first `200` from the task URL ≠ done either (wait for `endTime`). JSON-RPC errors come back in **HTTP 200**: check for an `error` member.
- Question for partner: NETCONF is REST or RPC? → **RPC**: one session, operations named in `<rpc>` (`get-config`, `edit-config`). RESTCONF is the REST one.

### T10 · API authentication

- Key point 1: **Read the header to name the method:** `Authorization: Basic …` = Basic · token from a login call sent as `X-Auth-Token` = custom token (Catalyst Center; FMC `X-auth-access-token`) · static portal key = API key (Meraki) · `Set-Cookie` after login = session cookie (APIC, SD-WAN Manager) · OAuth = Webex integration.
- Key point 2: **OAuth 2.0 code flow:** user logs in at the auth server → app gets a one-time **code** → swaps it (+ client secret) for an **access token** + **refresh token**. The app never sees the password. Show the OAuth GIF.
- Key point 3: **Base64 = encoding, not encryption,** so everything needs HTTPS. Secrets from env vars / vault, never in the script or Git. Python: `auth=(u, p)` or `headers={"X-Auth-Token": t}`; `Session()` keeps cookies.
- Exam trap: **Catalyst Center isn't `Bearer`**, it's `X-Auth-Token`. Wrong scheme word (`Basic` vs `Bearer`) or wrong header name → `401`.
- Question for partner: A user's valid token gets `403` on DELETE. Will a fresh token fix it? → **No**: 403 = role/scope. Needs an account with permission.

### T11 · Python requests scripting

- Key point 1: **One call = method + URL + keyword args:** `params=` → `?a=1` · `headers=` · `json=` (dict → JSON **and** sets `Content-Type`) · `auth=(u, p)` · `timeout=` · `verify=`. Always set `timeout`, there's no default.
- Key point 2: **Read the response:** `status_code` (int) → `headers` → `.json()` / `.text` / `.content`. `requests` **never raises on 4xx/5xx**; `raise_for_status()` turns it into `HTTPError`.
- Key point 3: **Script pattern:** login → `token = resp.json()["Token"]` → `Session()` + `headers.update(...)` → loop while `next` → on `429` `time.sleep(int(resp.headers["Retry-After"]))` and retry → `except RequestException` last. Show the 429 GIF.
- Exam trap: **`data=dict` sends a form and `data=json.dumps(d)` sends no Content-Type**: both get `415` from a JSON API. Use `json=d`. And `resp.json` without `()` is a method, not the data.
- Question for partner: `if resp.status_code == "200":` never runs. Why? → **`status_code` is an int**, compare with `200`.

## Bob teaches

### T14 · YANG data models

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T15 · NETCONF

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T16 · RESTCONF

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T17 · IOS XE and NX-OS device-level APIs

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T18 · Meraki

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T19 · ACI

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

## Weak IDs logged

- 
