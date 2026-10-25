---
id: T47
title: "Sequence diagrams with API calls"
owner: Beedy
blueprint: "5.14"
primary_domain: D5
cbt_coverage: "None"
status: drafted   # not-started | drafted | verified
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-24
cross_study: 2026-10-27
---

# T47 · Sequence diagrams with API calls

> Owner: **Beedy** · Blueprint: **5.14** · CBT coverage: **None** · Learn by 2026-10-24

![T47 at a glance: notation, frames, auth, async, webhook and reading flows](../assets/T47/00-overview.png)

*Six panels, one per concept group (IDs top right). Each mini diagram is read top to bottom; black numbers are the order of the arrows, solid = request, dashed = response, yellow boxes = frames. Red boxes are exam traps.*

<!-- toc:start -->

**Contents**

- [TL;DR](#tldr)
- [Concepts](#concepts)
  - [T47.01](#t4701--notation) Notation · [T47.02](#t4702--notation) Notation · [T47.03](#t4703--auth-flow) Auth flow · [T47.04](#t4704--async-flow) Async flow · [T47.05](#t4705--webhook-flow) Webhook flow · [T47.06](#t4706--reading) Reading · [T47.07](#t4707--exam-angle) Exam angle
- [Exam traps](#exam-traps)
- [Examples](#examples)
- [Practice questions](#practice-questions)
- [Study aids](#study-aids)
- [Sources](#sources)
- [To verify](#to-verify)

<!-- toc:end -->

## TL;DR

- **How to read it:** boxes across the top are **participants**, and each has a dashed **lifeline** going down. **Time runs top → bottom.** A **solid** arrow is a request (method + URL); a **dashed** arrow is the response (status + data) going back the other way. A thin **activation bar** means "this one is busy".
- **Frames are code:** `alt` = `if/else` (one branch runs), `opt` = `if` with no else, `loop` = `while` (poll, paginate), `par` = in parallel. Each request/response arrow pair = one `requests.get()` / `post()`.
- **The flows the exam draws:** auth first (`POST …/auth/token` → `200` + token → calls with `X-Auth-Token`); async (`POST` → **`202` + taskId** → `loop GET /task/{id}` → `GET` result); webhook (register → the **service POSTs to you** → `200` → you `GET` the details).
- **Trap:** the arrow right after `202 Accepted` is **GET the task/status URL**, not "read the result" and not "POST again". And a data call drawn **before** the token arrow is the bug, so expect a `401`.

## Concepts

Every section below explains one part of the same program. Read it once first.

- **Backbone:** `labs/T47/flows.py` runs five real API flows against a stdlib mock (`labs/T47/mock_api.py`, port **8147**). It has a Catalyst Center (DNA Center)-shaped controller and a Webex-shaped messaging API.
- `labs/T47/seqtrace.py` prints **one line per HTTP message**, already in Mermaid syntax: `->>` for each request, `-->>` for each response, numbered in time order.
- So the **printed trace is the sequence diagram**. Each diagram in `assets/T47/` matches one flow of the output, arrow for arrow. `labs/T47/trace_to_mmd.py` turns the trace straight back into a `.mmd` file to prove it.
- Builds on: REST and status codes in [T07](T07-rest-fundamentals-http-codes.md), the async taskId pattern in [T09.07](T09-api-styles-rest-vs-rpc-sync-vs-async.md#t0907--async-example), token and OAuth flows in [T10.03](T10-api-authentication.md#t1003--custom-token) / [T10.06](T10-api-authentication.md#t1006--oauth-20-awareness), pagination in [T08.03](T08-api-consumption-constraints.md#t0803--pagination), webhooks in [T43](T43-webhooks.md).

**API doc for the mock:**

| Participant (trace name) | Method | Path | Auth | Success | Error |
|---|---|---|---|---|---|
| Catalyst Center (`CatC`) | `POST` | `/dna/system/api/v1/auth/token` | Basic `devnet:cisco123` | `200` `{"Token": "tok-0001"}` | `401` |
| | `GET` | `/dna/intent/api/v1/network-device?offset=1&limit=2` | `X-Auth-Token` | `200` `{"response": [...]}` | `401` missing/expired token |
| | `POST` | `/dna/intent/api/v1/network-device-poller/cli/read-request` | `X-Auth-Token` | **`202`** `{"response": {"taskId": ...}}` | `401` |
| | `GET` | `/dna/intent/api/v1/task/{taskId}` | `X-Auth-Token` | `200`; `endTime` appears on the 3rd poll | `404` |
| | `GET` | `/dna/intent/api/v1/file/{fileId}` | `X-Auth-Token` | `200` command output | |
| Webex (`Webex`) | `POST` | `/v1/webhooks` | `Authorization: Bearer` | `200` webhook object | `401` |
| | `POST` | `/v1/messages` | `Authorization: Bearer` | `200`, **then** the service POSTs to every matching `targetUrl` | `401` |
| | `GET` | `/v1/messages/{id}` | `Authorization: Bearer` | `200` full message | `404` |

**`labs/T47/flows.py`**

```python
"""T47 reference program: five API flows, each printed as a sequence-diagram trace.

Run:  python3 labs/T47/flows.py
It starts labs/T47/mock_api.py in a thread on http://127.0.0.1:8147, runs the flows, and exits
(the server stops with the process). Python stdlib only.

Every HTTP request prints one solid arrow (->>) and every response one dashed arrow (-->>),
numbered in time order, so the output can be laid next to the matching diagram in
assets/T47/ and compared line by line.
"""
import base64
import json
import threading
import time
import urllib.error
import urllib.request

import mock_api
import seqtrace

BASE = f"http://{mock_api.HOST}:{mock_api.PORT}"
BASIC = "Basic " + base64.b64encode(b"devnet:cisco123").decode()
WEBEX = {"Authorization": f"Bearer {mock_api.WEBEX_TOKEN}"}


def summary(body):
    """Shorten a JSON reply to the fields a diagram label would show."""
    if body is None:
        return ""
    inner = body.get("response", body) if isinstance(body, dict) else body
    if isinstance(inner, list) and inner and "commandResponses" in inner[0]:   # Command Runner file
        return "SUCCESS: " + ", ".join(inner[0]["commandResponses"]["SUCCESS"])
    if isinstance(inner, list):                                    # device list
        return "[" + ", ".join(d["hostname"] for d in inner) + "]"
    if "Token" in inner:
        return f'{{"Token": "{inner["Token"]}"}}'
    if "isError" in inner:                                         # task status
        done = f'endTime set, progress={inner["progress"]}' if "endTime" in inner else "no endTime yet"
        return f'isError={str(inner["isError"]).lower()}, {done}'
    keys = ("taskId", "error", "id", "status", "targetUrl", "text", "message")
    return json.dumps({k: inner[k] for k in keys if k in inner})


def call(src, dst, method, path, body=None, headers=None):
    """One request/response pair = one solid arrow down, one dashed arrow back."""
    headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    auth = next((f" [{k}: {v}]" for k, v in headers.items()
                 if k in ("X-Auth-Token", "Authorization")), "")
    seqtrace.arrow(src, dst, f"{method} {path}{auth}")
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as err:          # 4xx/5xx still carry a body
        response = err
    text = response.read().decode()
    body = json.loads(text) if text else None
    seqtrace.arrow(dst, src, f"{response.status} {response.reason} {summary(body)}", reply=True)
    return response.status, body


# ---------- Flow 1 (T47.03): authenticate, then call the API with the token ----------
def get_token():
    status, body = call("Client", "CatC", "POST", "/dna/system/api/v1/auth/token",
                        headers={"Authorization": BASIC})
    return body["Token"]


# ---------- Flow 2 (T47.02 alt): 200 → use data | 401 → get a new token, retry once ----------
def get_devices(session, path="/dna/intent/api/v1/network-device"):
    status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    if status == 401:                                              # alt [401 token expired]
        seqtrace.note("Client", "alt 401: token expired -> log in again, retry once")
        session["token"] = get_token()
        status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    return body["response"]


# ---------- Flow 3 (T47.04 loop): POST job → 202 + taskId → poll task → GET result ----------
def run_command(session, command):
    hdr = {"X-Auth-Token": session["token"]}
    status, body = call("Client", "CatC", "POST",
                        "/dna/intent/api/v1/network-device-poller/cli/read-request",
                        {"commands": [command], "deviceUuids": ["dev-1"]}, hdr)
    task_id = body["response"]["taskId"]                           # 202 = accepted, NOT done
    while True:                                                    # loop [until endTime is set]
        time.sleep(0.2)
        task = call("Client", "CatC", "GET", f"/dna/intent/api/v1/task/{task_id}", headers=hdr)[1]["response"]
        if task["isError"]:                                        # opt [isError true]
            raise RuntimeError(task.get("failureReason"))
        if "endTime" in task:
            break
    file_id = json.loads(task["progress"])["fileId"]
    return call("Client", "CatC", "GET", f"/dna/intent/api/v1/file/{file_id}", headers=hdr)[1]


# ---------- Flow 4 (T47.02 loop): paginate with offset/limit until a short page ----------
def all_devices(session, limit=2):
    devices, offset = [], 1                                        # Catalyst Center offset starts at 1
    while True:                                                    # loop [until page < limit]
        page = get_devices(session, f"/dna/intent/api/v1/network-device?offset={offset}&limit={limit}")
        devices += page
        if len(page) < limit:
            return devices
        offset += limit


# ---------- Flow 5 (T47.05): register webhook → event → service POSTs to us → we GET details ----------
received = threading.Event()


def webhook_listener(handler):
    """The app's targetUrl. Runs when Webex (the mock) POSTs a notification to us."""
    length = int(handler.headers.get("Content-Length", 0))
    note = json.loads(handler.rfile.read(length))
    seqtrace.arrow("Webex", "App", f"POST /webhook-listener {json.dumps(note['data'])}")
    handler.send(200)                                              # ack fast, then do the work
    seqtrace.arrow("App", "Webex", "200 OK", reply=True)
    message = call("App", "Webex", "GET", f"/v1/messages/{note['data']['id']}", headers=WEBEX)[1]
    seqtrace.note("App", f"full text = {message['text']!r}")
    received.set()


def webhook_flow():
    mock_api.extra_routes["/webhook-listener"] = webhook_listener
    call("App", "Webex", "POST", "/v1/webhooks",
         {"name": "new-msg", "targetUrl": f"{BASE}/webhook-listener",
          "resource": "messages", "event": "created"}, WEBEX)
    seqtrace.note("App", "nothing to do now: no polling, just wait")
    call("User", "Webex", "POST", "/v1/messages", {"roomId": "room-1", "text": "edge1 is down"}, WEBEX)
    received.wait(timeout=5)


def main():
    server = mock_api.serve_in_thread()
    try:
        seqtrace.start("Flow 1 · auth, then call")
        session = {"token": get_token()}
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=2")

        seqtrace.start("Flow 2 · alt: 200 vs 401 -> re-auth")
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=1")
        mock_api.expire_tokens()                                   # time passes; the token expires
        seqtrace.note("CatC", "time passes: tok-0001 expires")
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=1")

        seqtrace.start("Flow 3 · async job: 202 + taskId, poll, fetch")
        result = run_command(session, "show version")
        print(f"   result: {result[0]['commandResponses']['SUCCESS']['show version']!r}")

        seqtrace.start("Flow 4 · pagination loop")
        names = [d["hostname"] for d in all_devices(session, limit=2)]
        print(f"   collected {len(names)} devices: {names}")

        seqtrace.start("Flow 5 · webhook")
        webhook_flow()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
```

**Output** (`python3 labs/T47/flows.py`; Python 3.14.6, real run):

```
== Flow 1 · auth, then call ==
01 Client->>CatC: POST /dna/system/api/v1/auth/token [Authorization: Basic ZGV2bmV0OmNpc2NvMTIz]
02 CatC-->>Client: 200 OK {"Token": "tok-0001"}
03 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=2 [X-Auth-Token: tok-0001]
04 CatC-->>Client: 200 OK [edge1, edge2]

== Flow 2 · alt: 200 vs 401 -> re-auth ==
01 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0001]
02 CatC-->>Client: 200 OK [edge1]
   Note over CatC: time passes: tok-0001 expires
03 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0001]
04 CatC-->>Client: 401 Unauthorized {"error": "Unauthorized: token missing or expired"}
   Note over Client: alt 401: token expired -> log in again, retry once
05 Client->>CatC: POST /dna/system/api/v1/auth/token [Authorization: Basic ZGV2bmV0OmNpc2NvMTIz]
06 CatC-->>Client: 200 OK {"Token": "tok-0002"}
07 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0002]
08 CatC-->>Client: 200 OK [edge1]

== Flow 3 · async job: 202 + taskId, poll, fetch ==
01 Client->>CatC: POST /dna/intent/api/v1/network-device-poller/cli/read-request [X-Auth-Token: tok-0002]
02 CatC-->>Client: 202 Accepted {"taskId": "task-001"}
03 Client->>CatC: GET /dna/intent/api/v1/task/task-001 [X-Auth-Token: tok-0002]
04 CatC-->>Client: 200 OK isError=false, no endTime yet
05 Client->>CatC: GET /dna/intent/api/v1/task/task-001 [X-Auth-Token: tok-0002]
06 CatC-->>Client: 200 OK isError=false, no endTime yet
07 Client->>CatC: GET /dna/intent/api/v1/task/task-001 [X-Auth-Token: tok-0002]
08 CatC-->>Client: 200 OK isError=false, endTime set, progress={"fileId": "file-001"}
09 Client->>CatC: GET /dna/intent/api/v1/file/file-001 [X-Auth-Token: tok-0002]
10 CatC-->>Client: 200 OK SUCCESS: show version
   result: 'show version\nedge1 uptime is 4 weeks'

== Flow 4 · pagination loop ==
01 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=2 [X-Auth-Token: tok-0002]
02 CatC-->>Client: 200 OK [edge1, edge2]
03 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=3&limit=2 [X-Auth-Token: tok-0002]
04 CatC-->>Client: 200 OK [core1, core2]
05 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=5&limit=2 [X-Auth-Token: tok-0002]
06 CatC-->>Client: 200 OK [access1]
   collected 5 devices: ['edge1', 'edge2', 'core1', 'core2', 'access1']

== Flow 5 · webhook ==
01 App->>Webex: POST /v1/webhooks [Authorization: Bearer bot-token-T47]
02 Webex-->>App: 200 OK {"id": "hook-1", "status": "active", "targetUrl": "http://127.0.0.1:8147/webhook-listener"}
   Note over App: nothing to do now: no polling, just wait
03 User->>Webex: POST /v1/messages [Authorization: Bearer bot-token-T47]
04 Webex-->>User: 200 OK {"id": "msg-1", "text": "edge1 is down"}
05 Webex->>App: POST /webhook-listener {"id": "msg-1", "roomId": "room-1", "personEmail": "alice@example.com"}
06 App-->>Webex: 200 OK
07 App->>Webex: GET /v1/messages/msg-1 [Authorization: Bearer bot-token-T47]
08 Webex-->>App: 200 OK {"id": "msg-1", "text": "edge1 is down"}
   Note over App: full text = 'edge1 is down'
```

- Each `NN` line is one arrow. Odd numbers are requests (`->>`) and even numbers are their responses (`-->>`); the `Note over` lines are notes in the diagram.
- `mock_api.py` and `seqtrace.py` are helpers. Open them only if curious: the mock fakes token expiry with `expire_tokens()` and fakes the job finishing on the 3rd task poll.

### T47.01 · Notation

**Must cover:**

- [x] Participants (boxes) with vertical lifelines
- [x] Time flows from top to bottom
- [x] Solid arrow = request/call (often labelled with method + URL)
- [x] Dashed arrow = response (often labelled with status code/data)

**Notes:**

- **Sequence diagram** = a UML interaction diagram that shows **who talks to whom, in what order**. For APIs: which system calls which endpoint, and what comes back.
- **Participant:** a box at the top, one per system. Typical ones are the script/client, an auth server, a controller (Catalyst Center, SD-WAN Manager, Meraki cloud), a device, and a webhook receiver.
  - Mermaid draws a stick figure for an `actor` (a human). Same meaning: a participant.
  - The **left-to-right order of the boxes means nothing**. The author chooses it.
- **Lifeline:** the vertical (often dashed) line under each box. UML 2.5.1 §17.3.4: a rectangle "head" followed by a vertical line "that represents the lifetime of the participant".
- **Time flows down.** An arrow lower on the page happens later. Message lines are "horizontal or downwards" from send to receive (UML §17.4.4.1).
- **Arrow types** (UML 2.5.1 §17.4.4.1, and the Mermaid syntax used in this repo):

| Looks like | UML meaning | In API diagrams | Mermaid |
|---|---|---|---|
| solid line, **filled** arrowhead | synchronous call | request: `GET /dna/intent/api/v1/network-device` | `A->>B: label` |
| **dashed** line, arrowhead | reply message | response: `200 OK [edge1, edge2]` | `B-->>A: label` |
| solid line, **open** arrowhead | asynchronous message (sender doesn't wait) | fire-and-forget event, push, webhook | `A-)B: label` |
| arrow from a box back to itself | self-call | local processing (parse JSON, build list) | `A->>A: label` |

- **Labels:** requests are labelled with the **method + URL** (and sometimes a header or body). Responses are labelled with the **status code + data**. In the trace: `03 Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=2 [X-Auth-Token: tok-0001]`, then `04 CatC-->>Client: 200 OK [edge1, edge2]`.
- **Numbers** (`autonumber` in Mermaid) are optional. Exam diagrams may number the arrows so a question can say "at arrow 5…" ⚠ verify how the exam draws them.

![Notation: participants, lifelines, solid vs dashed vs open arrows, activation](../assets/T47/01-notation.png)

*Four participants, time running down. Solid = request, dashed = response; the open arrowhead to the switch is async (the sender doesn't wait). The grey bars are activation.*

**Exam-sim gap (practice test review):**
- **Practice tests may show telecom-style time-sequence diagrams** (OSI/ITU service primitives), not just API calls:
  - **The vertical lines are the endpoints:** the service user and service provider on each side of an interface.
  - Messages between them are labelled with primitives such as request, indication, response and confirm.
  - Timers and checks (e.g. a timer-check function) mark completion or error events.
  - These are less likely on the real 200-901 exam than API diagrams ⚠ verify.
- Same reading rule as API diagrams: **lifelines = participants**, **time runs down**, an arrow = a message between two of them.

### T47.02 · Notation

**Must cover:**

- [x] Activation bar = participant busy processing
- [x] Frames: alt (if/else), opt (optional), loop (repeat), par (parallel)

**Notes:**

- **Activation bar** (UML "execution specification", §17.2.4 / §17.3.4: "thin rectangles (gray or white) on the lifeline"):
  - It starts where a request arrives and ends where the response leaves. It means **this participant is busy working**.
  - A long bar on the client during a sync call = the client is blocked ([T09.05](T09-api-styles-rest-vs-rpc-sync-vs-async.md#t0905--synchronous)).
  - Mermaid: `activate CatC` / `deactivate CatC`, or the shorthand `Client->>+CatC:` (`+` starts the bar) and `CatC-->>-Client:` (`-` ends it).
- **Frames** (UML "combined fragments", §17.6.3): a box around some arrows, with an operator tag in the top-left corner and a **guard** in `[brackets]`.

| Frame | UML rule | Code equivalent | Where in `flows.py` |
|---|---|---|---|
| `alt [g1] / [else]` | "at most one of the operands will be chosen" | `if … elif … else` | `get_devices()`: `if status == 401:` |
| `opt [g]` | "either the (sole) operand happens or nothing happens" | `if` with no `else` | `run_command()`: `if task["isError"]: raise …` |
| `loop [g]` | "the loop operand will be repeated a number of times" | `while` / `for` | `run_command()` poll loop, `all_devices()` page loop |
| `par` | "parallel merge between the behaviors of the operands" | threads / `asyncio.gather()` | none (see [T09.06](T09-api-styles-rest-vs-rpc-sync-vs-async.md#t0906--asynchronous)) |
| `break [g]` | operand runs "instead of the remainder" | `return` / `raise` early | `raise RuntimeError` in `run_command()` |
| `critical` | atomic region, can't be interleaved | lock | awareness only |

- Mermaid syntax for each: `alt …` / `else …` / `end`, `opt … end`, `loop … end`, `par … and … end`, `break … end`, `critical … option … end`. A `rect rgb(…)` block only adds a background colour; it isn't a UML frame.
- **Notes** (`Note over A,B: …`) are yellow boxes with comments. They aren't messages.

![All four exam frames in one diagram](../assets/T47/02-frames.png)

*alt: exactly one of [200] or [401] happens. loop: the GET/200 pair repeats. opt: the logs call happens only if isError. par: both POSTs go out together; the two 202s can come back in either order.*

### T47.03 · Auth flow

**Must cover:**

- [x] Client → auth endpoint: POST credentials
- [x] Auth → client: 200 + token
- [x] Client → API: GET/POST with token header
- [x] API → client: 200 + data (401 if token missing/expired)

**Notes:**

- **Flow 1** in the output (four arrows) = `get_token()` followed by `get_devices()`:

![Auth then call](../assets/T47/03-auth-flow.png)

*Arrow 1 sends Basic credentials once; arrow 2 brings the token back in the body; arrow 3 carries the token in a header instead of the password; arrow 4 is the data.*

| Arrow | Trace line | Code line |
|---|---|---|
| 1 | `Client->>CatC: POST /dna/system/api/v1/auth/token [Authorization: Basic ZGV2bmV0OmNpc2NvMTIz]` | `call("Client", "CatC", "POST", "/dna/system/api/v1/auth/token", headers={"Authorization": BASIC})` |
| 2 | `CatC-->>Client: 200 OK {"Token": "tok-0001"}` | `return body["Token"]` |
| 3 | `Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=2 [X-Auth-Token: tok-0001]` | `call(..., headers={"X-Auth-Token": session["token"]})` |
| 4 | `CatC-->>Client: 200 OK [edge1, edge2]` | `return body["response"]` |

- Why a token at all, and where each platform puts it (`X-Auth-Token`, `X-auth-access-token`, `Authorization: Bearer`): see [T10.03](T10-api-authentication.md#t1003--custom-token). The OAuth version of this diagram, with a browser and an authorization server as extra participants, is in [T10.06](T10-api-authentication.md#t1006--oauth-20-awareness).
- **The `alt` version: token expired.** Flow 2 in the output: the same GET returns `401`, so the client logs in again and retries once.

![alt frame: 200 uses the data, 401 re-authenticates and retries](../assets/T47/04-alt-401.png)

*Arrow 3 is the same GET as arrow 1. Its answer decides the branch: green [200] ends the flow, red [401] adds a new token request and a retry (arrows 5–9). Only one branch runs.*

- In code, the frame is literally the `if`:

```python
    status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    if status == 401:                                              # alt [401 token expired]
        seqtrace.note("Client", "alt 401: token expired -> log in again, retry once")
        session["token"] = get_token()
        status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    return body["response"]
```

![Animated: alt frame, one arrow = one line of code](../assets/T47/10-alt-reauth.gif)

*Arrow 1 (GET, old token) → arrow 2 (`401`) → alt picks the [401] branch → arrow 3 (`POST …/auth/token`) → arrow 4 (`tok-0002`) → arrow 5 (retry GET) → arrow 6 (`200`). The code line and trace line light up with each arrow. Fixes two misconceptions: that both alt branches run, and that a `401` ends the flow.*

- **`401` vs `403` on this diagram:** `401` = no valid token (missing, wrong, expired), so the fix is to authenticate. `403` = the token is fine but the user lacks the role, so re-authenticating won't help ([T07.09](T07-rest-fundamentals-http-codes.md#t0709--key-codes)).

### T47.04 · Async flow

**Must cover:**

- [x] Client → API: POST job
- [x] API → client: 202 Accepted + taskId
- [x] loop: Client → API: GET /task/{taskId} until complete
- [x] Client → API: GET result

**Notes:**

- **Flow 3** in the output = `run_command()`. It's the same Catalyst Center Command Runner flow as T09, which has the full field-by-field table and its own animation ([T09.07](T09-api-styles-rest-vs-rpc-sync-vs-async.md#t0907--async-example)). This section is about **reading the diagram**.

![Async: POST job, 202 + taskId, loop polling the task, then GET the result](../assets/T47/05-async-poll.png)

*Arrow 2 is short and fast: the activation bar on Catalyst Center ends at once, because the job runs in the background. The loop holds an alt: every poll gets a 200, but only the [finished] branch carries endTime and the fileId. Then one more GET fetches the actual output.*

| Diagram piece | Trace | Code in `run_command()` |
|---|---|---|
| arrow 1, `POST` job | `01 … POST /dna/intent/api/v1/network-device-poller/cli/read-request` | `call(..., "POST", ".../cli/read-request", {...}, hdr)` |
| arrow 2, `202` + taskId | `02 CatC-->>Client: 202 Accepted {"taskId": "task-001"}` | `task_id = body["response"]["taskId"]` |
| `loop [until endTime]` | lines `03`–`08` (3 polls) | `while True:` … `if "endTime" in task: break` |
| `opt [isError]` | (didn't happen) | `if task["isError"]: raise RuntimeError(...)` |
| `GET` result | `09 … GET /dna/intent/api/v1/file/file-001` → `10 … 200 OK SUCCESS: show version` | `json.loads(task["progress"])["fileId"]` then `call(..., "GET", f".../file/{file_id}")` |

- **How many polls?** The diagram draws the loop body **once**. The real run went round 3 times (lines `03`–`08`). A diagram never tells you the iteration count, only the condition.
- **Pagination is the same shape:** a `loop` around one GET. Flow 4 = `all_devices()`. Catalyst Center's `offset` is 1-based, and the loop stops on a short page ([T08.03](T08-api-consumption-constraints.md#t0803--pagination)).

![Pagination loop](../assets/T47/06-pagination.png)

*One GET inside a loop. The real run made 3 calls (offset 1, 3, 5) and stopped when the page had fewer than limit=2 items.*

### T47.05 · Webhook flow

**Must cover:**

- [x] App → service: register webhook (POST /webhooks)
- [x] Event occurs → service POSTs payload to the app's targetUrl
- [x] App → service: GET full details using the IDs in the payload

**Notes:**

- **Flow 5** = `webhook_flow()` + `webhook_listener()`. Here the arrows **change direction**: after registering, the service calls the app. Webhook concepts (security, `X-Spark-Signature`, testing tools) are in [T43](T43-webhooks.md).

![Webhook: register, event, service POSTs to targetUrl, app ACKs and GETs details](../assets/T47/07-webhook.png)

*Arrows 1–2: the app registers once, then sits idle (no polling). Arrows 3–4: someone else causes the event. Arrow 5 starts at Webex and points at the app. Arrow 6: the app's quick 200. Arrows 7–8: the app GETs the full message by ID.*

| Arrow | Trace | Meaning |
|---|---|---|
| 1 | `App->>Webex: POST /v1/webhooks` | body has `name`, `targetUrl`, `resource: "messages"`, `event: "created"` |
| 2 | `Webex-->>App: 200 OK {"id": "hook-1", "status": "active", …}` | registered |
| 3–4 | `User->>Webex: POST /v1/messages` / `200 OK` | the event happens (not the app's doing) |
| 5 | `Webex->>App: POST /webhook-listener {"id": "msg-1", "roomId": "room-1", "personEmail": …}` | **the service is now the client**: it POSTs a small notification to `targetUrl` |
| 6 | `App-->>Webex: 200 OK` | `handler.send(200)`: acknowledge fast |
| 7–8 | `App->>Webex: GET /v1/messages/msg-1` → `200 OK {"text": "edge1 is down"}` | fetch the full resource using the ID from the payload |

- **Why arrow 7 exists:** Webex says that for resources with sensitive data, the notification's `data` holds only metadata. To get the text, the app makes "an authenticated (via your Bearer Token) GET request to `/messages/{id}`" (developer.webex.com webhooks guide).
- **Why arrow 6 matters:** Webex disables the webhook if it doesn't get a 2xx: "100 failed attempts within a five minute period" (⚠ verify the current threshold). So the listener ACKs **before** doing slow work.
- **Webhook vs polling, side by side:** the async diagram has a `loop` on the **client** lifeline; the webhook diagram has **no loop**, and one arrow goes from the **service to the app**.

### T47.06 · Reading

**Must cover:**

- [x] Map each arrow to an HTTP method, URL and expected status code
- [x] Spot the missing or out-of-order step (e.g. call before auth)

**Notes:**

- **Five-step reading routine** (use it on every exam diagram):
  1. **Participants:** name each box (client, auth server, controller, device, listener). Which one holds the data?
  2. **Solid arrows:** for each one, write the **method + URL** (+ the auth header if shown). Is the verb right for the job (create = `POST`, read = `GET`, replace = `PUT`, partial update = `PATCH`)?
  3. **Dashed arrows:** the **status + data** you'd expect: `200` read OK, `201` created, `202` accepted (async), `204` no content, `401`/`403`/`404`/`429`.
  4. **Frames:** what repeats (`loop`), what branches (`alt`), what may be skipped (`opt`)?
  5. **Order:** auth before data · submit before poll · poll before result · register before event.
- **Spot the bug.** The diagram below is a script against Secure Firewall Management Center (FMC). What's wrong?

![Drill: what is wrong with this order?](../assets/T47/08-drill-spot-bug.png)

*Arrow 1 calls the data API before any token exists, so arrow 2 is a 401. Then the script authenticates (3–4) and repeats the call with the token (5–6).*

- **Answer:** arrows 1–2 are wasted: the call came **before auth**. A correct script starts at arrow 3.
  - FMC detail: the token and `DOMAIN_UUID` come back in **response headers**, not the body ([T10.03](T10-api-authentication.md#t1003--custom-token)). The `{domainUUID}` in arrow 1's URL couldn't even be known yet, which is a second clue. ⚠ verify the `204` status on `generatetoken`.
- **Other out-of-order or missing-step patterns to look for:**
  - `GET` the result right after `202`, with no poll → the result isn't there yet.
  - `POST` the job again inside the loop instead of `GET /task/{taskId}` → duplicate jobs.
  - Data arrow pointing **from** the client **to** itself, or a response with no request above it.
  - Webhook arrow drawn from the app to the service at event time → that's polling, not a webhook.
  - Retry after `429` with no wait (should honour `Retry-After`, [T08](T08-api-consumption-constraints.md)).

### T47.07 · Exam angle

**Must cover:**

- [x] Order the calls in a flow
- [x] Say what happens or what is returned at a given arrow

**Notes:**

- **"Order the calls"** (drag-and-drop style ⚠ verify exam format): find the **anchor** first: auth is always first; the result GET is always last. Then fill the middle by data dependency: you can't call `/task/{taskId}` until a response gave you `taskId`.
- **"What is arrow N?"** Read the arrows either side of N. A solid arrow carries the request, so the answer is a method + URL. A dashed one carries the response, so the answer is a status + data. Then check which frame and guard arrow N sits under.
- **Drill: what is arrow 5?**

![Drill: fill in arrow 5](../assets/T47/09-drill-next-call.png)

*A template deploy: token, PUT the job, 202 + taskId, then a loop. What does the client send at arrow 5?*

- **Answer:** `GET /api/v1/task/t-77` (the task-status URL, with `X-Auth-Token: abc`).
  - Arrow 4 handed back `taskId`. Arrow 6 returns `progress`, which is a task status. It's inside a `loop [until done]`.
  - Not `PUT /templates/deploy` again (that queues a second deploy). Not the status GET (arrow 7 is after the loop).
- **Diagram → code** (the exam can show either side and ask for the other):

| Diagram | Python (`requests`) |
|---|---|
| solid + dashed arrow pair | `r = requests.get(url, headers=h, verify=False)` (one call = two arrows) |
| label `200 {"Token": …}` | `token = r.json()["Token"]` |
| `alt [200] / [401]` | `if r.status_code == 401: … else: …` |
| `opt [isError]` | `if task["isError"]: raise …` |
| `loop [until endTime]` | `while "endTime" not in task: time.sleep(2); task = …` |
| `par` | threads / `asyncio.gather()` |
| arrow from service to app | a Flask/HTTP route handler that receives the POST |

- The table's `requests` lines are standard `requests` usage ([T11](T11-python-requests-scripting.md)). `flows.py` uses `urllib` only so it needs no install.

## Exam traps

- **Solid vs dashed:** solid = request (method + URL); dashed = response (status + data). A dashed arrow never carries a `GET`.
- **Time runs down; the box order means nothing.** "Which call happens first?" → the **highest** arrow, whatever box it starts at.
- **`202` is the middle of the flow, not the end.** Next arrow = `GET /task/{taskId}` (or status URL). Not the result, not a repeat POST.
- **`alt` ≠ both.** Exactly one branch runs. `opt` = one block that may not run at all. `loop` = the arrows inside repeat; the diagram doesn't say how many times.
- **Call before auth** → `401`. A missing token arrow at the top is the classic "missing step".
- **`401` → re-authenticate. `403` → re-auth won't help** (wrong role or scope).
- **Webhook direction:** the event arrow goes **from the service to the app's `targetUrl`**. The app replies `200` fast, then GETs details by ID. No loop on the app lifeline.
- **Open vs filled arrowhead:** open = async message (sender doesn't wait); filled = sync call. A `202` response is still drawn as a **dashed** reply, though.
- **Activation bar = busy, not alive.** The lifeline is "exists"; the thin bar is "processing right now".
- **One HTTP call = two arrows.** "How many API calls?" → count the **solid** arrows only (Flow 2: 6 arrows, 3 calls).
- **Vertical lines = participants/endpoints** in any sequence diagram (API client/server, or service user/provider in telecom-style diagrams). Time runs down.

## Examples

### 1. Run the reference program

Needs only Python 3. Nothing to install. It starts the mock API in a thread on port 8147 and stops it on exit.

```bash
python3 labs/T47/flows.py
```

In the lab container:

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work --workdir /work ccna-auto-lab:latest python3 labs/T47/flows.py
```

### 2. Turn the trace back into a diagram

The trace already uses Mermaid arrows, so one flow becomes a `.mmd` file with a 25-line script:

```bash
python3 labs/T47/flows.py > "$TMPDIR/trace.txt"
python3 labs/T47/trace_to_mmd.py "$TMPDIR/trace.txt" 2 > "$TMPDIR/flow2.mmd"
cat "$TMPDIR/flow2.mmd"
npx --yes @mermaid-js/mermaid-cli --input "$TMPDIR/flow2.mmd" --output "$TMPDIR/flow2.png" --scale 2 --backgroundColor white
```

Output of `cat` (real run):

```
sequenceDiagram
    autonumber
    Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0001]
    CatC-->>Client: 200 OK [edge1]
    Note over CatC: time passes: tok-0001 expires
    Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0001]
    CatC-->>Client: 401 Unauthorized {"error": "Unauthorized: token missing or expired"}
    Note over Client: alt 401: token expired -> log in again, retry once
    Client->>CatC: POST /dna/system/api/v1/auth/token [Authorization: Basic ZGV2bmV0OmNpc2NvMTIz]
    CatC-->>Client: 200 OK {"Token": "tok-0002"}
    Client->>CatC: GET /dna/intent/api/v1/network-device?offset=1&limit=1 [X-Auth-Token: tok-0002]
    CatC-->>Client: 200 OK [edge1]
```

- Compare it with `assets/T47/04-alt-401.mmd`. Same arrows, in the same order; the hand-drawn version only adds the `alt` frame and the colours.

### 3. curl drill: one curl per solid arrow (`labs/T47/curl_drill.sh`)

```bash
#!/usr/bin/env bash
# T47 curl drill: the auth flow + async flow, one curl per solid arrow.
# Starts labs/T47/mock_api.py on 127.0.0.1:8147, runs the calls, then stops the API.
#   bash labs/T47/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="http://127.0.0.1:8147"

python3 "$HERE/mock_api.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl --silent --output /dev/null "$BASE/health" && break
  sleep 0.25
done

echo "== arrow 1: no token yet (the out-of-order bug)"
curl --silent --write-out " [HTTP %{http_code}]\n" "$BASE/dna/intent/api/v1/network-device"

echo "== arrows 1-2: POST credentials -> 200 + token"
TOKEN=$(curl --silent --request POST --user "devnet:cisco123" "$BASE/dna/system/api/v1/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['Token'])")
echo "Token=$TOKEN"

echo "== arrows 3-4: GET with X-Auth-Token -> 200 + data"
curl --silent --write-out " [HTTP %{http_code}]\n" --header "X-Auth-Token: $TOKEN" \
  "$BASE/dna/intent/api/v1/network-device?offset=1&limit=2"

echo "== async arrows 1-2: POST job -> 202 + taskId"
TASK_ID=$(curl --silent --request POST --header "X-Auth-Token: $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"commands": ["show version"], "deviceUuids": ["dev-1"]}' \
  "$BASE/dna/intent/api/v1/network-device-poller/cli/read-request" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['response']['taskId'])")
echo "taskId=$TASK_ID"

echo "== async loop: GET the task until endTime appears"
for poll in 1 2 3; do
  curl --silent --write-out " [HTTP %{http_code}] poll $poll\n" --header "X-Auth-Token: $TOKEN" \
    "$BASE/dna/intent/api/v1/task/$TASK_ID"
done

echo "== async last arrow: GET the result"
curl --silent --write-out " [HTTP %{http_code}]\n" --header "X-Auth-Token: $TOKEN" \
  "$BASE/dna/intent/api/v1/file/file-001"
```

Output (`bash labs/T47/curl_drill.sh`; curl 8.7.1):

```
== arrow 1: no token yet (the out-of-order bug)
{"error": "Unauthorized: token missing or expired"} [HTTP 401]
== arrows 1-2: POST credentials -> 200 + token
Token=tok-0001
== arrows 3-4: GET with X-Auth-Token -> 200 + data
{"response": [{"id": "dev-1", "hostname": "edge1", "managementIpAddress": "10.10.20.81"}, {"id": "dev-2", "hostname": "edge2", "managementIpAddress": "10.10.20.82"}], "version": "1.0"} [HTTP 200]
== async arrows 1-2: POST job -> 202 + taskId
taskId=task-001
== async loop: GET the task until endTime appears
{"response": {"taskId": "task-001", "isError": false, "progress": "CLI Runner request creation"}, "version": "1.0"} [HTTP 200] poll 1
{"response": {"taskId": "task-001", "isError": false, "progress": "CLI Runner request creation"}, "version": "1.0"} [HTTP 200] poll 2
{"response": {"taskId": "task-001", "isError": false, "progress": "{\"fileId\": \"file-001\"}", "endTime": 1791700000000}, "version": "1.0"} [HTTP 200] poll 3
== async last arrow: GET the result
[{"deviceUuid": "dev-1", "commandResponses": {"SUCCESS": {"show version": "show version\nedge1 uptime is 4 weeks"}}}] [HTTP 200]
```

- The first call has no token and gets `401`. That's the "call before auth" bug, live.
- The task URL answers `200` three times; only the third reply has `endTime`.

### 4. Break it on purpose

Copy the lab to scratch, make one edit, run it:

```bash
mkdir -p "$TMPDIR/t47" && cp labs/T47/*.py "$TMPDIR/t47/"
# edit $TMPDIR/t47/flows.py as in the table, then:
cd "$TMPDIR/t47" && python3 flows.py
```

All four were run; the result column is the real output.

| Edit in `flows.py` | What you get | Diagram lesson |
|---|---|---|
| In `get_devices()`, change `if status == 401:` to `if False:` | Flow 2 stops after `04 CatC-->>Client: 401 Unauthorized …`, then `KeyError: 'response'` | the `alt [401]` branch is gone, so a 401 is a dead end |
| In `run_command()`, change `if "endTime" in task:` to `if True:` | one poll (`04 … 200 OK isError=false, no endTime yet`), then `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` | the `loop` exited before its guard was met; `progress` wasn't a fileId yet |
| In `webhook_flow()`, change `"event": "created"` to `"event": "deleted"` | Flow 5 ends at `04 Webex-->>User: 200 OK …`; arrows 5–8 never appear (the run waits the 5 s timeout) | no matching subscription → the service never calls the app |
| In `main()`, change `session = {"token": get_token()}` to `session = {"token": "none-yet"}` | Flow 1 now starts `01 … [X-Auth-Token: none-yet]` → `02 … 401 Unauthorized`, then the alt branch logs in (`03`–`04`) and retries | the "call before auth" diagram from T47.06, produced by real code |

### 5. Write a sequence diagram yourself (Mermaid)

This is the minimum syntax to draw any exam flow, and it renders in GitHub Markdown as a `mermaid` code block:

```mermaid
sequenceDiagram
    autonumber
    participant S as Script
    participant M as Meraki Dashboard
    S->>M: GET /api/v1/organizations<br/>Authorization: Bearer MERAKI_API_KEY
    M-->>S: 200 OK [{"id": "123"}]
    loop while the Link header has rel=next
        S->>M: GET /api/v1/organizations/123/networks?perPage=100
        alt 200 OK
            M-->>S: 200 OK [page] + Link header
        else 429 Too Many Requests
            M-->>S: 429 + Retry-After: 1
            Note over S: sleep 1 s, then repeat the same GET
        end
    end
```

- The Meraki details (Bearer key, `Link` header paging, `429` + `Retry-After`) are covered in [T08](T08-api-consumption-constraints.md) and [T10.04](T10-api-authentication.md#t1004--api-key). ⚠ verify paths against the Meraki API docs.

### 6. Real Catalyst Center (DevNet Sandbox), not run

The same Flow 1 + Flow 3 against a real controller is in [T09 Example 5](T09-api-styles-rest-vs-rpc-sync-vs-async.md#5-real-catalyst-center-async-call-devnet-sandbox). Its curl calls map one-to-one onto arrows 1, 3 and 5 of `05-async-poll.png`.

## Practice questions

**Q1.** In an API sequence diagram, a horizontal **dashed** arrow goes from the controller to the script, labelled `200 OK`. What does it represent?
A. A request the controller sends to the script  B. The response to an earlier request from the script  C. An asynchronous event with no reply  D. The script's activation period

<details><summary>Answer</summary>

**B.** Dashed = reply/return message carrying the status code and data. A request is a solid arrow; an activation is a thin bar on the lifeline. (T47.01)
</details>

**Q2.** Put these arrows in the order they appear in a diagram of a Catalyst Center job:
`GET /dna/intent/api/v1/task/{taskId}` · `POST /dna/system/api/v1/auth/token` · `GET /dna/intent/api/v1/file/{fileId}` · `202 Accepted {"taskId": …}` · `POST …/network-device-poller/cli/read-request` · `200 OK {"Token": …}`

<details><summary>Answer</summary>

`POST …/auth/token` → `200 OK {"Token": …}` → `POST …/cli/read-request` → `202 Accepted {"taskId": …}` → `GET …/task/{taskId}` (inside a loop) → `GET …/file/{fileId}`. Auth first; each call needs a value from the response before it. (T47.03, T47.04, T47.07)
</details>

**Q3.** A diagram shows:

```
Client ->> API: GET /api/v1/devices  (X-Auth-Token: abc)
alt [200]
    API -->> Client: 200 + device list
else [401]
    API -->> Client: 401 Unauthorized
    Client ->> API: POST /api/v1/auth/token
    ...
end
```

The token is valid. How many arrows in the `alt` frame happen?
A. All of them  B. Only the `200` arrow  C. The `401` branch only  D. None, `alt` is optional

<details><summary>Answer</summary>

**B.** `alt` is if/else: exactly one operand runs, chosen by its guard. Valid token → `[200]`. "May not happen at all" describes `opt`, not `alt`. (T47.02)
</details>

**Q4.** Which Python code produces exactly this diagram?

```
loop [until "endTime" in task]
    Script ->> CatC: GET /dna/intent/api/v1/task/{taskId}
    CatC -->> Script: 200 {"response": {...}}
end
```

A.
```python
r = requests.post(f"{BASE}/dna/intent/api/v1/task/{task_id}", headers=h, verify=False)
```
B.
```python
task = {}
while "endTime" not in task:
    time.sleep(2)
    task = requests.get(f"{BASE}/dna/intent/api/v1/task/{task_id}", headers=h, verify=False).json()["response"]
```
C.
```python
if "endTime" in task:
    requests.get(f"{BASE}/dna/intent/api/v1/task/{task_id}", headers=h, verify=False)
```
D.
```python
for _ in range(3):
    requests.put(f"{BASE}/dna/intent/api/v1/task/{task_id}", headers=h, verify=False)
```

<details><summary>Answer</summary>

**B.** `loop` = `while`, one GET per pass, stopping when the guard is met. A is a single POST, C is an `opt` with the guard inverted, D uses the wrong method and a fixed count. (T47.02, T47.07)
</details>

**Q5.** In a webhook sequence diagram, which arrow comes right after "a user posts a message in the room"?
A. App → Webex: `GET /v1/messages` (the app checks for new messages)  B. Webex → App: `POST <targetUrl>` with a JSON payload  C. App → Webex: `POST /v1/webhooks`  D. Webex → User: `302` redirect

<details><summary>Answer</summary>

**B.** The service pushes a notification to the registered `targetUrl`. A is polling, and C (registration) happened earlier. (T47.05)
</details>

**Q6.** The webhook payload in a diagram contains only `{"id": "msg-1", "roomId": "room-1"}`. What is the app's next request?
A. `POST /v1/webhooks` again  B. `GET /v1/messages/msg-1` with its Bearer token  C. `DELETE /v1/webhooks/{id}`  D. None, the payload has the full text

<details><summary>Answer</summary>

**B.** The notification carries IDs/metadata; the app fetches the full resource by ID, authenticated. (T47.05)
</details>

**Q7.** A diagram shows: (1) Script → FMC `GET /api/fmc_config/v1/domain/{domainUUID}/object/networks`, (2) FMC → Script `401`, (3) Script → FMC `POST /api/fmc_platform/v1/auth/generatetoken`, (4) FMC → Script `204` + `X-auth-access-token`. What is the problem with the script?
A. It used POST for the token request  B. It called the data API before authenticating  C. FMC returned the token in the wrong header  D. Nothing; a 401 always comes first

<details><summary>Answer</summary>

**B.** Arrows 1–2 are a call before auth. Authenticate first; then the token (and the domain UUID) are available for the data call. (T47.06)
</details>

**Q8.** A sequence diagram has 10 arrows: 5 solid and 5 dashed, and no frames. How many HTTP requests did the client make?
A. 10  B. 5  C. 2  D. Can't tell

<details><summary>Answer</summary>

**B.** Each request is one solid arrow; each dashed arrow is its response. One HTTP call = two arrows. (T47.01, T47.06)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T47.1 | Top-up | Read token-auth + async-poll sequence diagrams | 30 | Catalyst Center / Webex docs |

- Skip / low priority: n/a
- Blueprint gap (5.14): no CBT content (`data/blueprint-map.csv`). This note plus top-up T47.1 cover it: the auth diagram in T47.03 and the async diagram in T47.04 are that top-up.
- 30-min plan: run `python3 labs/T47/flows.py` and lay its output next to diagrams 03–07 (10 min), the two drills in T47.06/T47.07 (5 min), Q1–Q8 (15 min).

## Sources

- Overview image: HTML source `assets/T47/00-overview.html`, rendered to PNG (see `assets/README.md`). Diagrams: Mermaid sources in `assets/T47/*.mmd`. Animation: `assets/T47/10-alt-reauth-anim.html` → `.gif`.
- Cisco 200-901 v1.1 exam topics (5.14 "Interpret a sequence diagram that includes API calls"): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf
- OMG UML 2.5.1 (PDF), §17.3.4 Lifeline notation; §17.4.4.1 Message notation (synchronous = filled arrowhead, asynchronous = open arrowhead, reply = dashed line, lines horizontal or downwards); §17.2.4 / §17.3.4 execution specification as thin rectangles; §17.6.3 interaction operators alt, opt, break, par, critical, loop: https://www.omg.org/spec/UML/2.5.1/PDF
- Mermaid sequence diagram syntax (arrow types `->>`, `-->>`, `-)`, `-x`; `activate`/`+`/`-`; `loop`, `alt`/`else`, `opt`, `par`/`and`, `critical`, `break`, `rect`, `autonumber`, notes, `actor`): https://mermaid.js.org/syntax/sequenceDiagram.html
- Webex webhooks guide (create with `name`/`targetUrl`/`resource`/`event`; notification carries metadata, then an authenticated `GET /messages/{id}`; disabled after 100 failed deliveries in 5 minutes without a 2xx; `X-Spark-Signature`): https://developer.webex.com/docs/api/guides/webhooks
- Catalyst Center paths and task fields: same sources as [T09 Sources](T09-api-styles-rest-vs-rpc-sync-vs-async.md#sources) (official `dnacentersdk` source).
- FMC token headers: same sources as [T10 Sources](T10-api-authentication.md#sources).

## To verify

- ⚠ **Exam notation:** whether Cisco's diagrams use strict UML arrowheads (filled vs open), number the arrows, or draw `alt`/`loop` frames at all. This note follows UML 2.5.1 + Mermaid conventions; the exam's own drawing style is unconfirmed.
- ⚠ **Question formats** (drag-and-drop ordering, "what is returned at arrow N"): assumed from the blueprint verb "interpret". Not confirmed against official sample questions.
- ⚠ Webex webhook auto-disable threshold (100 failures in 5 min) and the `200` status on `POST /v1/webhooks`: from the guide as fetched on 10 Oct 2026; the status code is from prior knowledge.
- ⚠ FMC `generatetoken` returning `204` with the tokens in headers (drill 08): from prior knowledge and the `fmcapi` SDK pattern; see T10's To verify.
- ⚠ Catalyst Center 1-based `offset` on `/dna/intent/api/v1/network-device`, and the task fields: see T08 / T09 To verify.
- ⚠ Meraki example in Examples §5 (paths, `Link` header paging, `Retry-After`): not run.
- Not run: the Docker command in Examples §1 (lab image not built; Docker daemon not running), Examples §6 (no sandbox access), and the `npx` render line in Examples §2 (rendered here with a local mermaid-cli install instead).
- Run locally and pasted as real output: `flows.py`, `trace_to_mmd.py`, `curl_drill.sh`, and all four break-it edits (Python 3.14.6, curl 8.7.1). Running the mock needs local port binding, which the Claude Code sandbox blocks; it runs normally in your own terminal.
