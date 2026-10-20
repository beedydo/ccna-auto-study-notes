# T11 · Python requests scripting: essentials

> Blueprint 2.9: Python script calling a REST API with requests · Full note: [bee/T11-python-requests-scripting.md](../bee/T11-python-requests-scripting.md) · Teach-back 2026-10-18

![T11 at a glance: every requests concept on one page](../assets/T11/00-overview.png)

*Each row is one group of concepts. The numbered items are lines from the lab's `inventory_client.py`, and the red boxes are exam traps.*

## 🧭 The big idea

`requests` is the Python library you use to talk to REST APIs. Think of it as **`curl` with Python objects**. The topic answers two questions:

| | Question | Answer options | Parcel analogy |
|---|---|---|---|
| 📦 | **How do I describe the request?** | keyword arguments: `headers=`, `params=`, `json=`, `auth=`, `verify=`, `timeout=` | the **URL** is the address; the **headers** are the labels on the box; `json=` is packing the contents **and** writing "contents: JSON" on the label for you |
| 🧾 | **How do I read what came back?** | a `Response` object: `.status_code`, `.headers`, `.json()`, `.text`, and `raise_for_status()` | the **response** is the delivery receipt, which you must read yourself: the post office won't shout if the parcel was refused (no exception on a 404) |

- 🎯 **What the exam asks:** "complete the code" and "what does this print?". Most marks come from a handful of small details: `json=` vs `data=`, `.json()` vs `.text`, `raise_for_status()`, and `verify=`.

## 🟥 Must know

### 1. 📦 Making a call: method + URL + keyword arguments

> 💡 `requests` is a **third-party** package (`pip install requests`), not part of the standard library. **One function per HTTP method:** `requests.get`, `requests.post`, `requests.put`, `requests.patch`, `requests.delete`. Each takes a URL and returns a `Response`.

**Each keyword argument fills one part of the HTTP request.** A real call from the full note's lab, annotated:

```python
resp = requests.get(
    "https://127.0.0.1:8111/api/v1/devices",        # URL: base URL + endpoint path
    params={"limit": 2, "role": None},               # query string → ?limit=2 (a None value is DROPPED)
    headers={"X-Auth-Token": token,                  # request headers
             "Accept": "application/json"},
    verify=CA_CERT,                                  # client-side: check the TLS cert against this CA file
    timeout=5,                                       # client-side: give up after 5 s (NO default timeout)
)
```

- 🖥️ `verify` and `timeout` are **never sent** to the server; they only change how the client behaves.
- ⏱️ **There's no timeout by default**, so a call to a dead host can hang for a long time. Set `timeout=` on every call.
- 🪪 **`auth=(user, pass)` = HTTP Basic auth.** `requests` builds `Authorization: Basic <base64>` for you:

```python
resp = requests.post(f"{BASE_URL}/auth/token", auth=("admin", "C1sco12345"), verify=CA_CERT, timeout=5)
# sends: Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==
```

![Python call to HTTP request](../assets/T11/01-call-anatomy.png)

*Method, URL and params make the request line. Headers and `json` make the headers, and `json` also makes the body. `timeout` and `verify` stay on the client.*

**Summary:**

| | Argument | What it does | Sent to the server? |
|---|---|---|---|
| 🏷️ | `headers={...}` | adds request headers, such as `Accept` or `X-Auth-Token` | ✅ |
| 🔎 | `params={...}` | builds the query string, e.g. `?role=edge&limit=2`; `None` values are dropped | ✅ |
| 📦 | `json=dict` | JSON body **+** `Content-Type: application/json` (section 2) | ✅ |
| 📝 | `data=` | form or raw body (section 2) | ✅ |
| 🪪 | `auth=(user, pass)` | HTTP Basic auth | ✅ |
| 🔐 | `verify=` | TLS check: `True` (default), `False`, or a path to a CA file | ❌ client-side |
| ⏱️ | `timeout=` | seconds to wait; no default | ❌ client-side |

### 2. 📦 Sending a body: `json=` vs `data=`

> 💡 **This is the most tested detail in the topic.** Three ways to send the same dict, and only one "just works" against a JSON API.

| | Call | Parcel analogy | Content-Type | Result |
|---|---|---|---|---|
| ✅ | `json=body` | packs the parcel **and** labels it | `application/json` | works |
| ❌ | `data=body` (a dict) | repacks it as a different kind of parcel (a form) | `application/x-www-form-urlencoded` | `415` (a form) |
| ❌ | `data=json.dumps(body)` | packs it correctly but **forgets the label** | `None` | `415` (no label) |

What each one actually sends (from the full note's `prepare()` drill, no server needed):

```python
body = {"hostname": "edge3", "role": "edge"}

requests.post(url, json=body)              # Content-Type: application/json
                                           # body: b'{"hostname": "edge3", "role": "edge"}'   ✔ works

requests.post(url, data=body)              # Content-Type: application/x-www-form-urlencoded
                                           # body: 'hostname=edge3&role=edge'               ✘ 415 (a form)

requests.post(url, data=json.dumps(body))  # Content-Type: None
                                           # body: '{"hostname": "edge3", "role": "edge"}'  ✘ 415 (no label)
```

- A JSON API answers the last two with **`415 Unsupported Media Type`** (T07).
- `json=` is ignored if you also pass `data=`.

![json= vs data=](../assets/T11/02-body-encoding.png)

*Only `json=` both converts the dict and labels it. `data=dict` sends a form, and `data=json.dumps(d)` sends the right bytes with no label. A JSON API answers the last two with `415`.*

### 3. 🧾 Reading the response, and `raise_for_status()`

> 💡 **Read a response in this order:** status first, then headers, then body. **Analogy: the delivery receipt.** First the stamp (delivered or refused), then the small print, then the attached sheet.

From the full note's lab, after a successful `POST /devices` with `json=`:

```python
resp.status_code        # 201                  ← an int: compare with == 201, not == "201"
resp.ok                 # True                 ← True for ANY code below 400 (so 204 and 3xx too)
resp.headers["location"]# '/api/v1/devices/6'  ← header names are case-insensitive (server sent "Location")
resp.text               # '{"id": 6, "hostname": "edge3", ...}'   ← str
resp.content            # b'{"id": 6, "hostname": "edge3",...'    ← bytes (note the b)
resp.json()["id"]       # 6                    ← parsed into a dict/list; .json() is a METHOD, needs ()
```

| Attribute | Type | What it gives you |
|---|---|---|
| `resp.status_code` | `int` | the code, e.g. `201` |
| `resp.ok` | `bool` | True if code < 400 |
| `resp.headers` | dict-like, case-insensitive | response headers |
| `resp.text` | `str` | body as text |
| `resp.content` | `bytes` | raw body |
| `resp.json()` | `dict` / `list` | body parsed from JSON |

**🪤 The bracket traps:**

| ❌ Code | Error | ✅ Why |
|---|---|---|
| `resp.json["id"]` | `TypeError: 'method' object is not subscriptable` | no brackets on `.json` |
| `resp.text["Token"]` | `TypeError: string indices must be integers` | `.text` is a plain string |

- 🫙 **Empty body:** `.json()` on a `204 No Content` (e.g. after a DELETE) raises `requests.exceptions.JSONDecodeError`.
- 📄 **Error responses have JSON bodies too**, e.g. `{"error": "device 99 not found"}`. A successful `.json()` doesn't mean the request worked: check the code first.

**🚨 `requests` never raises an exception on a 4xx/5xx by itself.**

```python
resp = requests.get(f"{BASE_URL}/devices/99", headers=headers, timeout=5)
print(resp.status_code, resp.ok)    # 404 False   ← no exception: the script carries on silently
resp.raise_for_status()             # NOW it raises:
# requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://127.0.0.1:8111/api/v1/devices/99
```

| Code below 400 | Code 4xx or 5xx |
|---|---|
| `raise_for_status()` does **nothing** | raises **`HTTPError`** |

- Call it straight after each request, so a bad status stops the script instead of crashing three lines later.

### 4. 🎫 Log in, then use the token with a Session

> 💡 **The Catalyst Center (DNA Center) shape:** Basic auth **once** to get a token, then send the token in a header on **every** call (REST is stateless).

- **`requests.Session()`** is a client object that holds **defaults** for every call made through it: headers, auth, verify and cookies. It also keeps a **connection pool**.
- 🪢 **Analogy: a visitor badge on a lanyard.** You collect it once at reception, clip it on, and every door sees it without you digging it out each time.

The full pattern from the full note's lab, annotated:

```python
# 1. Log in once with Basic auth; the token comes back in the JSON BODY
resp = requests.post(f"{BASE_URL}/auth/token", auth=(USER, PASSWORD), verify=CA_CERT, timeout=5)
resp.raise_for_status()
token = resp.json()["Token"]

# 2. Put the token in a Session header: every later call through the session sends it
session = requests.Session()
session.headers.update({"X-Auth-Token": token, "Accept": "application/json"})
session.verify = CA_CERT                                   # every session call checks the cert

# 3. Use the session
requests.get(f"{BASE_URL}/devices", verify=CA_CERT, timeout=5)   # → 401 (plain call: no token)
session.get(f"{BASE_URL}/devices", timeout=5)                    # → 200 (token from the session)
```

| ✅ Session headers persist | ❌ Per-call headers don't |
|---|---|
| `session.headers.update(...)` | `session.get(url, headers={"X-Debug": "1"})` adds `X-Debug` to **that call only** |

- 🪪 **`auth=(u, p)` is for the token endpoint.** It's Basic auth, not how you send the token afterwards; that's a header.

| | 🔁 Plain `requests.get()` × 3 | 🪢 Session × 3 |
|---|---|---|
| **Connection reuse** (in the lab) | **3** TCP connections | **1** TCP connection |
| Why it matters | | one handshake instead of three is why sessions are faster |

![Auth then use](../assets/T11/06-auth-then-use.png)

*The token comes back in the body of the login reply. The script copies it into a session header, so every later call carries it.*

![Session vs plain calls](../assets/T11/03-session.png)

*A Session keeps headers, verify and cookies, and reuses one pooled connection. Plain `requests.get()` rebuilds everything each time.*

### 5. 🚨 Exceptions, and 🔐 `verify=` on self-signed certs

**Two different kinds of failure:**

| | 📨 The server answered with 4xx/5xx | 🚚 There was no usable answer |
|---|---|---|
| Examples | | host down, port closed, TLS failed, server too slow |
| What you get | a normal `Response`; nothing is raised until `raise_for_status()` raises `HTTPError` | `requests` raises **at once**, and there is **no `resp`** to look at |
| Analogy | a refused parcel still comes back with a receipt (`HTTPError` holds the response) | a lost van brings nothing back at all (`ConnectionError`, `Timeout`) |

The full note's `safe_get()`, with the order that matters:

```python
try:
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()                              # 4xx/5xx → HTTPError
    return resp.json()
except requests.exceptions.HTTPError as err:             # the server said no; err.response has the error body
    print(err.response.json())                           # {'error': 'device 99 not found'}
except requests.exceptions.Timeout:                      # server slower than timeout= (ReadTimeout)
    ...
except requests.exceptions.ConnectionError:              # nothing listening on the port
    ...
except requests.exceptions.RequestException as err:      # base class of ALL the above: must go LAST
    ...                                                  # e.g. InvalidSchema: URL had no https://
```

> 🎯 **`except RequestException` goes last.** Python runs the **first** matching `except`; the base class first would swallow everything.

![requests exception tree](../assets/T11/04-exceptions.png)

*Everything inherits from RequestException. SSLError is a kind of ConnectionError.*

**🔐 `verify=` and self-signed lab certs.** Lab devices usually have **self-signed certificates**, which no public CA vouches for:

```python
requests.get(url, timeout=5)                     # verify=True (default) → SSLError, no response at all
requests.get(url, verify=False, timeout=5)       # 200 + InsecureRequestWarning (a WARNING, call still works)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.get(url, verify=False, timeout=5)       # 200, warning hidden, STILL checks nothing
requests.get(url, verify="/path/to/ca.pem", timeout=5)   # 200, no warning: the real fix
```

| Setting | Result | Checks the cert? |
|---|---|---|
| `verify=True` (default) | `SSLError`, no response at all | ✅ (fails closed) |
| `verify=False` | 200 + `InsecureRequestWarning` (a WARNING, call still works) | ❌ |
| `verify=False` + `disable_warnings()` | 200, warning hidden | ❌ STILL checks nothing |
| `verify="/path/to/ca.pem"` | 200, no warning: the real fix | ✅ |

- `requests.packages.urllib3.disable_warnings()` is the same call, spelled the other way.
- `verify=False` and `disable_warnings()` are for **sandboxes only**. Real scripts verify, with a CA file path or the `REQUESTS_CA_BUNDLE` environment variable.

![verify= outcomes](../assets/T11/05-tls-verify.png)

*Default = fail closed. `verify=False` works but checks nothing, and hiding the warning doesn't change that. Pointing `verify=` at the CA cert is the real fix.*

### 6. 🗄️ Inspect the data, then pull out fields

1. **Inspect:** `print(json.dumps(data, indent=2))` pretty-prints the structure, so you can see the keys and how they nest.
2. **Extract:** walk the path one level at a time. If the body is `{"response": [ {...}, {...} ]}`:

```python
data = resp.json()
data["response"]                  # a list of devices
data["response"][0]               # the first device: a dict
data["response"][0]["hostname"]   # 'csr1'

for d in data["response"]:        # every device
    print(d["hostname"])
```

> 🗄️ **Analogy: a filing cabinet.** `["response"]` opens the drawer, `[0]` takes the first folder, `["hostname"]` reads one line on it.

- Catalyst Center wraps its results in `"response"`, while Meraki returns a bare list ⚠ verify per platform.

| `json.dumps` | `json.loads` |
|---|---|
| Python → JSON string | JSON string → Python. `resp.json()` is `json.loads(resp.text)` done for you. |

**🧩 Complete-the-code: pick the blank by its clue:**

| Clue in the question | | Blank |
|---|---|---|
| a filter or page | 🔎 | `params=` |
| a dict body | 📦 | `json=` |
| a username and password | 🪪 | `auth=` |
| the integer code | 🚦 | `.status_code` |
| the parsed body | 🧾 | `.json()` |

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| `data=dict` or `data=json.dumps(d)` sends JSON | **`data=dict` sends a form; `data=json.dumps(d)` sends no Content-Type.** A JSON API answers both with `415`. Use `json=d`. |
| A 404 raises an exception; `resp.ok` means 200 | **A 404 doesn't raise.** `requests` returns quietly with `status_code == 404`; only `raise_for_status()` raises `HTTPError`. And `resp.ok` is True for **anything below 400**, not just 200. |
| `resp.json["id"]`, `resp.text["Token"]`, `status_code == "200"` all work | **`.json()` needs brackets; `.text` is a string.** `resp.json["id"]` and `resp.text["Token"]` both give `TypeError`. `status_code` is an **int**: `== "200"` is always False. |
| `verify=False` raises an error | **`verify=False` is a warning, not an error.** The call succeeds with `InsecureRequestWarning`; `disable_warnings()` only hides it. Default `verify=True` on a self-signed cert → `SSLError`, no response. |
| `except` order doesn't matter | **`except RequestException` goes last**, or it swallows the specific handlers below it. |
| Per-call headers stick; `auth=` sends the token | **Session headers persist; per-call headers don't.** `s.headers.update()` is what persists. `auth=(u, p)` is Basic auth for the login, not how you send the token. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 🧰 The generic form and other body rules

| | |
|---|---|
| 🧰 **The generic form** | `requests.request("PATCH", url, json={"role": "core"}, timeout=5)` does the same job as `requests.patch(...)`. Handy when the method is stored in a variable. `requests.get(url)` is literally `requests.request("GET", url)`. Sessions have the same methods (`session.get`, `session.request`, …). |
| 📝 **`data="string"`** | sends the string as-is with **no** Content-Type added |
| 🪪 **`auth=`** | takes priority over an `Authorization` header you set by hand in `headers=` |

### 📑 Pagination

> 💡 The API returns one page plus a pointer to the next, so keep calling while it's set (T08 covers paging styles in depth):

```python
devices, url = [], f"{BASE_URL}/devices"
params = {"limit": 2}
while url:
    resp = session.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    devices.extend(data["response"])
    url = urljoin(BASE_URL, data["next"]) if data["next"] else None   # relative link → full URL
    params = None                         # the next link already carries the query string
```

- Lab result: 3 GETs (`limit=2`, `offset=2`, `offset=4`) collected 5 devices.
- Some APIs use a `Link` header instead, which `requests` exposes as `resp.links["next"]["url"]`.

![Pagination loop](../assets/T11/07-pagination.png)

### ⏳ Rate limit (429)

> 💡 Read `Retry-After`, sleep that long, retry the **same** request, and cap the tries:

```python
for attempt in range(1, max_tries + 1):
    resp = session.get(url, timeout=5)
    if resp.status_code != 429:
        resp.raise_for_status()
        return resp
    time.sleep(int(resp.headers.get("Retry-After", 1)))   # header values are strings, so int()
raise RuntimeError(f"still rate limited after {max_tries} tries")
```

| ✅ `resp.headers.get("Retry-After", 1)` | ❌ `resp.headers["Retry-After"]` |
|---|---|
| gives a default if the header is missing | raises `KeyError` instead |

- `time.sleep("2")` → `TypeError`: header values are strings.
- `requests` does not retry by itself, and doesn't raise on a 429: you check `status_code`.

![Animated 429 retry loop](../assets/T11/09-retry-429.gif)

*The flow is: call, 200, call, 200, call, 429 + `Retry-After: 2`, sleep 2, then the same call gets 200. Retrying without sleeping just gets 429 four times.*

### 🍪 Cookies and closing a session

- **Cookies:** a `Set-Cookie` from the server is stored in `s.cookies` and sent back automatically. That's how cookie logins stay logged in (T10).
- **`with requests.Session() as s:`** closes the session's connections at the end of the block.

### 🚨 Exception table

| What happened | Exception |
|---|---|
| A 404, then `raise_for_status()` | `HTTPError` (`err.response` still holds the error body) |
| The server was slower than `timeout=` | `Timeout` (here, `ReadTimeout`) |
| Nothing listening on the port | `ConnectionError` |
| The URL had no `https://` | `InvalidSchema`, a kind of `RequestException` |

</details>

> 📚 **Recognise only, details in the full note:** `urllib3.util.Retry` with `HTTPAdapter(max_retries=...)`, `REQUESTS_CA_BUNDLE` overriding `session.verify` (⚠ verify), `resp.reason` / `resp.request` / `resp.url`, `ConnectTimeout` / `MissingSchema` / `TooManyRedirects`, `Request(...).prepare()`, `requests` default headers (`User-Agent: python-requests/…`, `Accept: */*`), `json=` ignored with `files=`.

## ✍️ Quick self-check
<details><summary>Q1. Which argument sends a dict as JSON and sets the Content-Type?</summary><code>json=</code>. <code>data=</code> sends a form, and <code>params=</code> builds the query string.</details>
<details><summary>Q2. <code>resp = requests.get(url_of_missing_device)</code>, then <code>print(resp.status_code, resp.ok)</code>. What prints?</summary><code>404 False</code>. No exception is raised, because nothing called <code>raise_for_status()</code>.</details>
<details><summary>Q3. How do you send the token on 50 calls and reuse one connection?</summary><code>s = requests.Session()</code>, then <code>s.headers.update({"X-Auth-Token": token})</code>, then call <code>s.get(...)</code>.</details>
<details><summary>Q4. <code>token = resp.text["Token"]</code> raises what, and what is the fix?</summary><code>TypeError: string indices must be integers</code>. Use <code>resp.json()["Token"]</code>.</details>
<details><summary>Q5. You get a 429. What are the next two lines?</summary><code>time.sleep(int(resp.headers["Retry-After"]))</code>, then send the same request again.</details>
<details><summary>Q6. <code>requests.post(url, data=json.dumps(body))</code> returns <code>415</code>. Why?</summary>The bytes are JSON but no <code>Content-Type</code> is set. Use <code>json=body</code>, which serialises and labels it.</details>
<details><summary>Q7. <code>requests.get("https://127.0.0.1:8111/api/v1/health", timeout=5)</code> against the lab's self-signed cert: what happens, and what's the real fix?</summary>It raises <code>SSLError</code> (default <code>verify=True</code>) with no response. The real fix is <code>verify="/path/to/ca.pem"</code>; <code>verify=False</code> works but checks nothing and warns.</details>

## 🗣️ Say it out loud
- 📦 "json= packs it and labels it; data= sends a form."
- 🚨 "requests never raises on a 404 unless you call raise_for_status()."
- 🧾 "Remember the brackets: .json() gives you a dict, and .text is just a string."
- 🔐 "verify=False means a warning, not an error, and nothing gets checked."
- 🎫 "Log in once with auth=, then the token rides in the Session headers."
