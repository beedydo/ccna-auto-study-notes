# T51 · Summary examples: REST request/response anatomy and parsing a dictionary: essentials

> Worked examples for blueprint 2.x (REST) and 1.x/5.x (reading Python) · Related: [T45](T45-reading-python-scripts-using-cisco-apis.md), [T50](T50-api-cheatsheet-transport-auth-operations.md)

## 🧭 The big idea
| Example | Shows | Exam cue |
|---|---|---|
| 1. REST request + response | the six parts of one HTTP exchange | "which part carries X?" |
| 2. Parsing a dictionary | `[]` vs `.get()`, nested dict + list, filtering | "what does this script print?" |

## Example 1 · One script, six parts of a REST call
Self-contained: it starts a tiny local server, then calls it, so you can run it with no network. `pip install requests`, then `python3 rest_anatomy.py`.

### 🎨 Colour key (🟦 request, 🟩 response; the [n] tag is the same in the table, the wire view, the code comments and the output)
| Tag | Part | Direction | Where in the code |
|---|---|---|---|
| 🟦 **[1]** | **REQUEST LINE** (method + URL) | client → server | `"POST"`, URL in `requests.Request(...)` |
| 🟦 **[2]** | **REQUEST HEADERS** (metadata) | client → server | `headers={...}` |
| 🟦 **[3]** | **REQUEST BODY / payload** (data) | client → server | `json={...}` |
| 🟩 **[4]** | **STATUS LINE** (code + reason) | server → client | `resp.status_code`, `resp.reason` |
| 🟩 **[5]** | **RESPONSE HEADERS** (metadata) | server → client | `resp.headers` |
| 🟩 **[6]** | **RESPONSE BODY / payload** (data) | server → client | `resp.json()` |

🟦 = what **I send** · 🟩 = what **I get back**

### 📡 On the wire (raw HTTP, each part labelled)
```text
🟦 REQUEST (client → server)
  POST /api/v1/devices HTTP/1.1                     ◀── [1] request line
  Content-Type: application/json                    ◀── [2] request headers
  Accept: application/json                          ◀── [2]
  Authorization: Bearer abc123                      ◀── [2]
  Content-Length: 33                                ◀── [2]
                                                    ◀── (blank line: headers end, body starts)
  {"name": "sw1", "ip": "10.0.0.1"}                 ◀── [3] request body

🟩 RESPONSE (server → client)
  HTTP/1.1 201 Created                              ◀── [4] status line
  Content-Type: application/json                    ◀── [5] response headers
  Location: /api/v1/devices/42                      ◀── [5]
  Content-Length: 25                                ◀── [5]
                                                    ◀── (blank line: headers end, body starts)
  {"id": 42, "name": "sw1"}                         ◀── [6] response body
```

> 💡 Headers and body are separated by one **blank line**. Everything above it is metadata; everything below is the data.

### 💻 The script
Each comment tag `[1]`-`[6]` matches the table. The fake server's lines show where the 🟩 parts are produced.

```python
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests


def banner(text):
    print(f"\n===== {text} " + "=" * (50 - len(text)))


class Handler(BaseHTTPRequestHandler):  # the fake server
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = json.dumps({"id": 42, "name": body["name"]}).encode()
        self.send_response(201)                                  # [4] status line
        self.send_header("Content-Type", "application/json")     # [5] response headers
        self.send_header("Location", "/api/v1/devices/42")       # [5]
        self.send_header("Content-Length", str(len(out)))        # [5]
        self.end_headers()
        self.wfile.write(out)                                    # [6] response body

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8080), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

# ################ REQUEST (client -> server) ################
req = requests.Request(
    "POST",                                         # [1] REQUEST LINE: method
    "http://127.0.0.1:8080/api/v1/devices",         # [1] REQUEST LINE: URL
    headers={                                       # [2] REQUEST HEADERS
        "Content-Type": "application/json",         #     format of MY body
        "Accept": "application/json",               #     format I WANT back
        "Authorization": "Bearer abc123",           #     who I am
    },
    json={"name": "sw1", "ip": "10.0.0.1"},         # [3] REQUEST BODY (payload)
).prepare()

banner("[1] REQUEST LINE")
print("   ", req.method, req.path_url)
banner("[2] REQUEST HEADERS")
for k, v in req.headers.items():
    print(f"    {k}: {v}")
banner("[3] REQUEST BODY")
print("   ", req.body.decode())

# ################ RESPONSE (server -> client) ################
resp = requests.Session().send(req)

banner("[4] STATUS LINE")
print("   ", resp.status_code, resp.reason)
banner("[5] RESPONSE HEADERS")
for k, v in resp.headers.items():
    print(f"    {k}: {v}")
banner("[6] RESPONSE BODY")
print("   ", resp.json())
srv.shutdown()
```

### 🖨️ Output (each part prints under its own banner)
```text
===== [1] REQUEST LINE ==================================
    POST /api/v1/devices

===== [2] REQUEST HEADERS ===============================
    Content-Type: application/json
    Accept: application/json
    Authorization: Bearer abc123
    Content-Length: 33

===== [3] REQUEST BODY ==================================
    {"name": "sw1", "ip": "10.0.0.1"}

===== [4] STATUS LINE ===================================
    201 Created

===== [5] RESPONSE HEADERS ==============================
    Server: BaseHTTP/0.6 Python/3.10.12
    Date: Fri, 30 Oct 2026 04:59:08 GMT
    Content-Type: application/json
    Location: /api/v1/devices/42
    Content-Length: 25

===== [6] RESPONSE BODY =================================
    {'id': 42, 'name': 'sw1'}
```

### 🚩 Exam traps
| Looks like | Actually |
|---|---|
| `Content-Type` and `Accept` are the same | `Content-Type` = format of **my body**; `Accept` = format I **want back** |
| `json=` and `data=` are the same | `json=` serialises the dict **and** sets `Content-Type: application/json`; `data=` does neither |
| `resp.json` | a method: needs `()` |
| `201` means done | `201` = created (check `Location`); `202` = accepted, not finished |
| Headers and body are one thing | headers = metadata (auth, format, length); body = the data |

## Example 2 · Python script parsing a dictionary
A typical API reply is a dict holding a list of dicts. Read it from the outside in.

```python
resp = {
    "response": [
        {"hostname": "sw1", "reachabilityStatus": "Reachable",
         "interfaces": [{"name": "Gi1/0/1", "status": "up"}, {"name": "Gi1/0/2", "status": "down"}]},
        {"hostname": "sw2", "reachabilityStatus": "Unreachable", "interfaces": []},
    ],
    "version": "1.0",
}

print(resp["version"])
for dev in resp["response"]:
    print(dev["hostname"], dev.get("role", "n/a"))
    for intf in dev["interfaces"]:
        if intf["status"] == "down":
            print("  down:", intf["name"])
print([d["hostname"] for d in resp["response"] if d["reachabilityStatus"] == "Reachable"])
```

Output:
```text
1.0
sw1 n/a
  down: Gi1/0/2
sw2 n/a
['sw1']
```

| Syntax | Meaning | Trap |
|---|---|---|
| `resp["version"]` | value for a key | missing key → `KeyError` |
| `dev.get("role", "n/a")` | value or default | missing key → default, **no** error |
| `resp["response"][0]["hostname"]` | dict → list index → dict key | order matters: key, index, key |
| `for dev in resp["response"]` | loop over a list of dicts | looping a dict directly gives **keys** |
| `[x for x in ... if ...]` | list comprehension with filter | result is a list |
| `json.loads(text)` / `json.dumps(obj)` | string → dict / dict → string | `load`/`dump` (no `s`) work on files |
