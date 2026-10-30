# T51 · Summary examples: REST request/response anatomy and parsing a dictionary: essentials

> Worked examples for blueprint 2.x (REST) and 1.x/5.x (reading Python) · Related: [T45](T45-reading-python-scripts-using-cisco-apis.md), [T50](T50-api-cheatsheet-transport-auth-operations.md)

## 🧭 The big idea
| Example | Shows | Exam cue |
|---|---|---|
| 1. REST request + response | the six parts of one HTTP exchange | "which part carries X?" |
| 2. Parsing a dictionary | `[]` vs `.get()`, nested dict + list, filtering | "what does this script print?" |

## Example 1 · One script, six parts of a REST call
Self-contained: it starts a tiny local server, then calls it, so you can run it with no network. `pip install requests`, then `python3 rest_anatomy.py`.

| # | Part | Direction | Where in the code | Example value |
|---|---|---|---|---|
| 1 | 🎯 Request line (method + URL) | → | `req.method`, `req.path_url` | `POST /api/v1/devices` |
| 2 | 🏷️ Request headers | → | `headers={...}` | `Content-Type`, `Accept`, `Authorization` |
| 3 | 📦 Request payload (body) | → | `json={...}` | `{"name": "sw1", "ip": "10.0.0.1"}` |
| 4 | ✅ Status line | ← | `resp.status_code`, `resp.reason` | `201 Created` |
| 5 | 🏷️ Response headers | ← | `resp.headers` | `Content-Type`, `Location` |
| 6 | 📦 Response payload (body) | ← | `resp.json()` | `{"id": 42, "name": "sw1"}` |

```python
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = json.dumps({"id": 42, "name": body["name"]}).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Location", "/api/v1/devices/42")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8080), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

req = requests.Request(
    "POST",
    "http://127.0.0.1:8080/api/v1/devices",
    headers={"Content-Type": "application/json", "Accept": "application/json",
             "Authorization": "Bearer abc123"},
    json={"name": "sw1", "ip": "10.0.0.1"},
).prepare()
print(req.method, req.path_url)
print(req.headers)
print(req.body)
resp = requests.Session().send(req)
print(resp.status_code, resp.reason)
print(resp.headers)
print(resp.json())
srv.shutdown()
```

Output:
```text
POST /api/v1/devices
{'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Bearer abc123', 'Content-Length': '33'}
b'{"name": "sw1", "ip": "10.0.0.1"}'
201 Created
{'Server': 'BaseHTTP/0.6 Python/3.10.12', 'Date': '...', 'Content-Type': 'application/json', 'Location': '/api/v1/devices/42', 'Content-Length': '25'}
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
