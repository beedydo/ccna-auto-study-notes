# T51 · Summary examples: REST request/response anatomy and parsing a dictionary: essentials

> Worked examples for blueprint 2.x (REST) and 1.x/5.x (reading Python) · Related: [T45](T45-reading-python-scripts-using-cisco-apis.md), [T50](T50-api-cheatsheet-transport-auth-operations.md)

## 🧭 The big idea
| Example | Shows | Exam cue |
|---|---|---|
| 1. REST request + response | the six parts of one HTTP exchange (raw) | "which part carries X?" |
| 2. Parsing a dictionary | `[]` vs `.get()`, dict holding a list of dicts, looping | "what does this script print?" |
| 3. Reading API code | how to read a script for each platform, line by line | "which platform / what is printed / what is missing?" |

## Example 1 · The six parts of a REST call
One exchange = **3 parts going out** (request) + **3 parts coming back** (response). Each part has its own colour and its own box below.

| Colour | Part | Direction | What it is |
|---|---|---|---|
| 🟥 | **HTTP request** | client → server | method + URL: *what I want to do, and where* |
| 🟧 | **request header** | client → server | metadata about my request: format, login |
| 🟨 | **request payload** | client → server | the data I send |
| 🟩 | **HTTP response** | server → client | status line: *did it work?* |
| 🟦 | **response header** | server → client | metadata about the reply: format, location |
| 🟪 | **response payload** | server → client | the data I get back |

---

### ➡️ REQUEST (client → server)

#### 🟥 1. HTTP request
```text
POST /api/v1/devices HTTP/1.1
```
- `POST` = the action (create). `/api/v1/devices` = where.

#### 🟧 2. request header
```text
Content-Type: application/json
Accept: application/json
Authorization: Bearer abc123
Content-Length: 33
```
- `Content-Type` = format of **my** payload. `Accept` = format I **want back**. `Authorization` = who I am.

#### 🟨 3. request payload
```json
{"name": "sw1", "ip": "10.0.0.1"}
```
- Sits **after** the blank line that ends the headers.

---

### ⬅️ RESPONSE (server → client)

#### 🟩 4. HTTP response
```text
HTTP/1.1 201 Created
```
- `201` = created. This line is the first thing in the reply.

#### 🟦 5. response header
```text
Content-Type: application/json
Location: /api/v1/devices/42
Content-Length: 25
```
- `Location` = where the new object lives.

#### 🟪 6. response payload
```json
{"id": 42, "name": "sw1"}
```
- Also after a blank line. This is the data you parse with `resp.json()`.

---

### 🧩 Put together (raw, in order)
```text
POST /api/v1/devices HTTP/1.1            <- 🟥 HTTP request
Content-Type: application/json           <- 🟧 request header
Accept: application/json                 <- 🟧 request header
Authorization: Bearer abc123             <- 🟧 request header
Content-Length: 33                       <- 🟧 request header
                                         <- (blank line)
{"name": "sw1", "ip": "10.0.0.1"}        <- 🟨 request payload

HTTP/1.1 201 Created                     <- 🟩 HTTP response
Content-Type: application/json           <- 🟦 response header
Location: /api/v1/devices/42             <- 🟦 response header
Content-Length: 25                       <- 🟦 response header
                                         <- (blank line)
{"id": 42, "name": "sw1"}                <- 🟪 response payload
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
data = {
    "version": "1.0",
    "devices": [
        {"hostname": "sw1", "status": "up"},
        {"hostname": "sw2", "status": "down"},
    ],
}

print(data["version"])
for device in data["devices"]:
    print(device["hostname"], device["status"])
print(data["devices"][0].get("role", "n/a"))
```

Output:
```text
1.0
sw1 up
sw2 down
n/a
```

| Syntax | Meaning | Trap |
|---|---|---|
| `data["version"]` | value for a key | missing key → `KeyError` |
| `data["devices"]` | the list of dicts | a list, so loop it or index it |
| `for device in data["devices"]` | one dict per loop | looping a dict directly gives **keys** |
| `data["devices"][0]` | first item of the list | index starts at `0` |
| `.get("role", "n/a")` | value or default | missing key → default, **no** error |

## Example 3 · Reading API code, platform by platform
Same 4 questions for every script, in this order:

| # | Ask | Look at |
|---|---|---|
| 1 | 🎯 **Which platform?** | URL path, import line (`requests` / `ncclient` / SDK) |
| 2 | 🔐 **How does it log in?** | first call, `auth=`, which header carries the credential |
| 3 | 📦 **Where is the data?** | the key path after `.json()` |
| 4 | ✅ **What does success look like?** | status code check, `raise_for_status()`, task polling |

Snippets are trimmed from the runnable lab scripts in `labs/` (path under each heading).

### 🟩 Meraki Dashboard · `labs/T18/meraki_requests.py`
```python
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",     # login = static key in every call
    "Accept": "application/json",
})

resp = session.get(url, params=params)
if resp.status_code == 429:                   # rate limited
    wait = int(resp.headers.get("Retry-After", "1"))   # server says how long to wait
    time.sleep(wait)

items = resp.json()                           # plain JSON list, no wrapper key
while "next" in resp.links:                   # pagination = Link header, rel=next
    resp = session.get(resp.links["next"]["url"])
    items.extend(resp.json())
```
| Spot | Meaning |
|---|---|
| `Bearer` + `api.meraki.com` | Meraki (host decides, because Webex also uses Bearer) |
| `Session()` | headers set once, reused by every call |
| `429` + `Retry-After` | rate limit: wait, then retry |
| `resp.links["next"]` | pagination lives in a **header**, not the body |

### 🟦 Catalyst Center (DNA Center) · `labs/T20/catc_inventory.py`
```python
resp = requests.post(f"{BASE_URL}/dna/system/api/v1/auth/token",
                     auth=HTTPBasicAuth(USER, PASSWORD))   # only call that sends the password
token = resp.json()["Token"]                               # capital T

headers = {"X-Auth-Token": token}                          # every later call
resp = requests.get(f"{BASE_URL}/dna/intent/api/v1/network-device", headers=headers)
for dev in resp.json()["response"]:                        # list sits under "response"
    print(dev["hostname"], dev["reachabilityStatus"])
```
| Spot | Meaning |
|---|---|
| `/dna/system/api/v1/auth/token` | Catalyst Center login: POST + HTTP Basic |
| `["Token"]` | token is in the body, key is capital-T |
| `X-Auth-Token` | the header name that identifies this platform |
| `["response"]` | data wrapper (compare ACI's `imdata`) |
| write calls (PUT/POST) | return a `taskId`; poll `GET /task/{id}` for `endTime` / `isError` |

### 🟨 RESTCONF on IOS XE · `labs/T16/restconf_client.py`
```python
IFACES = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces"   # <module>:<container>
HEADERS = {"Accept": "application/yang-data+json",         # what I want back
           "Content-Type": "application/yang-data+json"}   # what I am sending

r = requests.get(IFACES, auth=AUTH, headers=HEADERS)       # auth=(user, pass): Basic on every call
r = requests.put(f"{IFACES}/interface=Loopback100", auth=AUTH, headers=HEADERS, json=LOOPBACK)
```
| Spot | Meaning |
|---|---|
| `/restconf/data/module:container` | RESTCONF; path is the YANG model |
| `yang-data+json` | RESTCONF media type (not plain `application/json`) |
| `auth=(user, pass)` | HTTP Basic on **every** call: no token step |
| `interface=Loopback100` | list entry addressed by key: `list=key` |
| forgot `auth=` | `401` |

### 🟧 ACI (APIC) · `labs/T19/aci_tenant_builder.py`
```python
body = {"aaaUser": {"attributes": {"name": USER, "pwd": PASSWORD}}}
resp = session.post(f"{BASE}/aaaLogin.json", json=body)    # session keeps the APIC-cookie
token = resp.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]

data = session.get(f"{BASE}/class/fabricNode.json").json()
for mo in data["imdata"]:                                  # list of {class: {attributes: {...}}}
    (cls, body), = mo.items()                              # unpack the single key = class name
    print(cls, body["attributes"]["name"])
```
| Spot | Meaning |
|---|---|
| `aaaLogin.json` + `aaaUser` body | APIC login (JSON body, **not** Basic) |
| `session` | cookie `APIC-cookie` is kept automatically |
| `["imdata"][0]["aaaLogin"]["attributes"]` | 4-level path: wrapper → item → class → attributes |
| `(cls, body), = mo.items()` | each managed object is a one-key dict whose key is its class |
| `/api/class/` vs `/api/mo/` | all objects of a class vs one object by DN |
| empty `imdata` | no match is `200` with `totalCount: "0"`, **not** 404 |

### ⬜ NETCONF · `labs/T15/netconf_walkthrough.py`
```python
from ncclient import manager

m = manager.connect(host=HOST, port=830, username=USER, password=PASSWORD,
                    hostkey_verify=False)                  # SSH, subsystem netconf, port 830
m.get_config(source="running")                             # config only (get = config + state)
m.lock(target="candidate")                                 # nobody else can edit
m.edit_config(target="candidate", config=XML)              # stage the change
m.commit()                                                 # make it live
m.unlock(target="candidate")
```
| Spot | Meaning |
|---|---|
| `ncclient`, `port=830` | NETCONF (SSH, XML): no URL, no HTTP |
| `get_config` vs `get` | config only vs config + operational state |
| `lock` → `edit_config` → `commit` → `unlock` | the safe edit sequence on a `candidate` datastore |
| `edit_config` without `commit` | change staged but **not** live |
| `server_capabilities` | what the device supports (`:candidate`, `:validate`, ...) |

### 🚩 Reading traps
| Looks like | Actually |
|---|---|
| `Bearer` means Webex | Meraki and Webex both use it; the host name decides |
| `aaaLogin.json` means ACI | also NX-API REST: look at `uni/` (ACI) vs `sys/` (Nexus) |
| `200` on a write means done | Catalyst Center returns a task; poll it |
| `["response"]` and `["imdata"]` are interchangeable | `response` = Catalyst Center; `imdata` = ACI / NX-API REST |
| No `auth=` and no token header | the call fails with `401` |
| `edit_config` succeeded, so it is live | needs `commit` on a candidate datastore |
