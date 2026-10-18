# T11 · Python requests scripting: essentials

> Blueprint 2.9 · Full note: [bee/T11-python-requests-scripting.md](../bee/T11-python-requests-scripting.md) · Teach-back 2026-10-18

## In one picture
![T11 at a glance: every requests concept on one page](../assets/T11/00-overview.png)
*Each row is one group of concepts. The numbered items are lines from the lab's `inventory_client.py`, and the red boxes are exam traps.*

## The big idea
- `requests` is the Python library you use to talk to REST APIs. Think of it as `curl` with Python objects.
  - You describe the request with keyword arguments.
  - You get back a `Response` object to read.
- A useful analogy is posting a parcel:
  - The **URL** is the address.
  - The **headers** are the labels on the box.
  - `json=` is packing the contents **and** writing "contents: JSON" on the label for you.
  - The **response** is the delivery receipt, which you must read yourself.
- The exam loves "complete the code" and "what does this print?" questions. Most marks come from a handful of small details: `json=` vs `data=`, `.json()` vs `.text`, `raise_for_status()`, and `verify=`.

## What you need to know

### 1. Making a call: method + URL + keyword arguments
- `requests` is a third-party package (`pip install requests`), not part of the standard library.
- There is one function per HTTP method: `requests.get`, `requests.post`, `requests.put`, `requests.patch` and `requests.delete`. Each one takes a URL and returns a `Response`.
- The generic form `requests.request("PATCH", url, ...)` does the same job. It is handy when the method is stored in a variable. `requests.get(url)` is literally `requests.request("GET", url)`.
- Each keyword argument fills one part of the HTTP request:

| Argument | What it does |
|---|---|
| `headers={...}` | Adds request headers, such as `Accept` or `X-Auth-Token` |
| `params={...}` | Builds the query string, for example `?role=edge&limit=2`. A value of `None` is **dropped**. |
| `json=dict` | Turns the dict into a JSON body **and** sets `Content-Type: application/json` |
| `data=dict` | Sends a **form** (`a=1&b=2`) with `Content-Type: application/x-www-form-urlencoded` |
| `data="string"` | Sends the string as-is, with **no** Content-Type added |
| `auth=(user, pass)` | Adds HTTP Basic auth: `Authorization: Basic <base64>` |
| `verify=` | Controls the TLS certificate check: `True` (the default), `False`, or a path to a CA file |
| `timeout=` | How many seconds to wait. **There is no timeout by default**, so set one on every call. |

- `verify` and `timeout` are never sent to the server. They only change how the client behaves.
- `json=` is ignored if you also pass `data=`.
- `auth=` takes priority over an `Authorization` header you set by hand.

![Python call to HTTP request](../assets/T11/01-call-anatomy.png)
*Method, URL and params make the request line. Headers and `json` make the headers, and `json` also makes the body. `timeout` and `verify` stay on the client.*

![json= vs data=](../assets/T11/02-body-encoding.png)
*Only `json=` both converts the dict and labels it. `data=dict` sends a form, and `data=json.dumps(d)` sends the right bytes with no label. A JSON API answers the last two with `415`.*

### 2. Reading the response
- Read a response in this order: status first, then headers, then body.

| Attribute | Type | What it gives you |
|---|---|---|
| `resp.status_code` | `int` | For example `201`. Compare it with `== 201`, not `== "201"`. |
| `resp.ok` | `bool` | True for **any code below 400**, so `204` and `3xx` count as ok too |
| `resp.headers` | dict-like | Header names are **case-insensitive**: `resp.headers["location"]` finds `Location` |
| `resp.text` | `str` | The body as text |
| `resp.content` | `bytes` | The raw body (it shows a `b'...'` prefix) |
| `resp.json()` | `dict` / `list` | The body parsed from JSON |

- `.json()` is a **method**, so it needs the brackets.
  - `resp.json["id"]` gives `TypeError: 'method' object is not subscriptable`.
  - `resp.text["Token"]` gives `TypeError: string indices must be integers`, because `.text` is a plain string.
- Calling `.json()` on an empty body, such as a `204 No Content` after a DELETE, raises `requests.exceptions.JSONDecodeError`.
- Error responses also have JSON bodies, for example `{"error": "device 99 not found"}`. A successful `.json()` does not mean the request worked, so check the status code first.
- **`requests` never raises an exception on a 4xx/5xx by itself.** Call `resp.raise_for_status()`.
  - It does nothing if the code is below 400.
  - It raises `HTTPError` on a 4xx or 5xx.

### 3. Sessions: remember settings and reuse the connection
- `s = requests.Session()` creates a client object that holds **defaults** for every call made through it: headers, auth, verify and cookies. It also keeps a connection pool.
- `s.headers.update({"X-Auth-Token": token, "Accept": "application/json"})` means every later `s.get(...)` or `s.post(...)` sends those headers.
  - In the lab, a plain `requests.get()` without the token gets `401`, while `session.get()` gets `200`.
- Arguments you pass on a single call are **merged in for that call only** and are not remembered.
- Cookies from `Set-Cookie` are stored in `s.cookies` and sent back automatically. That is how cookie logins stay logged in.
- A Session **reuses the TCP connection**. In the lab, 3 calls through a Session used 1 TCP connection, while 3 plain `requests.get()` calls used 3. One handshake instead of three is why sessions are faster.
- `with requests.Session() as s:` closes the connections at the end of the block.

![Session vs plain calls](../assets/T11/03-session.png)
*A Session keeps headers, verify and cookies, and reuses one pooled connection. Plain `requests.get()` rebuilds everything each time.*

### 4. Errors and TLS warnings
- There are two different kinds of failure.
  - **The server answered with a 4xx or 5xx.** You still get a normal `Response`, and nothing is raised until you call `raise_for_status()`, which raises `HTTPError`.
  - **There was no usable answer**, for example the host is down, the port is closed, TLS failed, or the server was too slow. In this case `requests` raises at once, and there is no `resp` to look at.

| What happened | Exception |
|---|---|
| A 404 followed by `raise_for_status()` | `HTTPError` (`err.response` still holds the error body) |
| The server was slower than `timeout=` | `Timeout` (here, `ReadTimeout`) |
| Nothing was listening on the port | `ConnectionError` |
| The URL had no `https://` | `InvalidSchema`, a kind of `RequestException` |

- Every one of these inherits from **`RequestException`**, so put `except RequestException` **last**. Python runs the first `except` that matches, so a base class placed first would catch everything.

![requests exception tree](../assets/T11/04-exceptions.png)
*Everything inherits from RequestException. SSLError is a kind of ConnectionError.*

- Lab devices usually have **self-signed certificates**, which no public CA vouches for. Here is what each setting does:

| Call | Result |
|---|---|
| Default (`verify=True`) | `SSLError`, and no response at all |
| `verify=False` | `200` plus an **`InsecureRequestWarning`**. This is a warning, not an error, so the call still works. |
| After `urllib3.disable_warnings()` (or `requests.packages.urllib3.disable_warnings()`) | `200` with the warning hidden. It still checks nothing. |
| `verify="/path/to/ca.pem"` | `200` with no warning. This is the real fix. |

- `verify=False` and `disable_warnings()` are for sandboxes only. Real scripts should verify certificates, using a CA file path or the `REQUESTS_CA_BUNDLE` environment variable.

### 5. The three script patterns
- **Log in, then use the token.** This is the Catalyst Center (DNA Center) shape:
  1. `POST` the login with `auth=(user, pass)`.
  2. Read `token = resp.json()["Token"]`.
  3. Put the token in a session header: `s.headers.update({"X-Auth-Token": token})`.

![Auth then use](../assets/T11/06-auth-then-use.png)
*The token comes back in the body of the login reply. The script copies it into a session header, so every later call carries it.*

- **Pagination.** The API returns one page plus a pointer to the next one, so keep calling while `data["next"]` is set.
  - In the lab, 3 GETs collected 5 devices.
  - `urljoin(BASE_URL, data["next"])` turns the relative link into a full URL.
  - After the first page, set `params = None`, because the next link already contains the query string.
  - Some APIs use a `Link` header instead, which `requests` exposes as `resp.links["next"]["url"]`.
- **Rate limit (429).** When you get `429 Too Many Requests`:
  1. Read the `Retry-After` header.
  2. Sleep for that many seconds.
  3. Retry the same request.
  - Cap the number of tries so a stuck API can't loop forever.

```python
if resp.status_code == 429:
    time.sleep(int(resp.headers["Retry-After"]))   # header values are strings, so int()
```

![Animated 429 retry loop](../assets/T11/09-retry-429.gif)
*The flow is: call, 200, call, 200, call, 429 + `Retry-After: 2`, sleep 2, then the same call gets 200. Retrying without sleeping just gets 429 four times.*

- `requests` does not retry by itself. A built-in alternative exists (`urllib3.util.Retry` with `HTTPAdapter`), but the exam pattern is the manual loop.
- `resp.headers.get("Retry-After", 1)` gives a default value if the header is missing. `resp.headers["Retry-After"]` raises `KeyError` instead.

### 6. Looking at the data, then pulling out fields
- **Step 1, inspect:** run `print(json.dumps(data, indent=2))` to pretty-print the structure, so you can see the keys and how they nest.
- **Step 2, extract:** if the body is `{"response": [ {...}, {...} ]}`:
  - `data["response"]` is a list.
  - `data["response"][0]` is the first device, which is a dict.
  - `data["response"][0]["hostname"]` is `"csr1"`.

```python
for d in data["response"]:
    print(d["hostname"])
```

- Catalyst Center wraps its results in `"response"`, while Meraki returns a bare list ⚠ verify per platform.
- `json.dumps` turns Python into a JSON string, and `json.loads` turns a JSON string into Python. `resp.json()` is simply `json.loads(resp.text)` done for you.
- **To fill a blank in complete-the-code questions, pick by clue:**
  - A filter goes in `params`.
  - A dict body goes in `json`.
  - A username and password go in `auth`.
  - The integer code is `.status_code`.
  - The parsed body is `.json()`.

## Exam traps (the ones that catch people)
- `data=dict` looks like it sends JSON, but it actually sends a **form**. `data=json.dumps(d)` sends JSON bytes with **no Content-Type**. A JSON API answers both with `415`. Use `json=d`.
- A 404 looks like it should raise an exception, but `requests` returns quietly with `status_code == 404`. Only `raise_for_status()` raises `HTTPError`.
- `resp.ok` sounds like "is 200", but it is True for **anything below 400**, including 204 and 3xx.
- `status_code` looks like `"200"`, but it is an **int**, so `== "200"` is always False.
- `verify=False` looks like it would fail, but the call succeeds with an `InsecureRequestWarning`. `disable_warnings()` only hides the message.
- `except RequestException` looks like a safe first handler, but because it is the base class it swallows every specific handler below it. Put it last.
- `auth=(u, p)` looks like the way to send a token, but it is Basic auth. Use it for the token endpoint, then send the token itself in a header.
- Per-call `headers=` look like they persist, but they apply to one call only. `s.headers.update()` is what persists.

## Quick self-check
<details><summary>Q1. Which argument sends a dict as JSON and sets the Content-Type?</summary>`json=`. `data=` sends a form, and `params=` builds the query string.</details>
<details><summary>Q2. `resp = requests.get(url_of_missing_device)`, then `print(resp.status_code, resp.ok)`. What prints?</summary>`404 False`. No exception is raised, because nothing called `raise_for_status()`.</details>
<details><summary>Q3. How do you send the token on 50 calls and reuse one connection?</summary>`s = requests.Session()`, then `s.headers.update({"X-Auth-Token": token})`, then call `s.get(...)`.</details>
<details><summary>Q4. `token = resp.text["Token"]` raises what, and what is the fix?</summary>`TypeError: string indices must be integers`. Use `resp.json()["Token"]`.</details>
<details><summary>Q5. You get a 429. What are the next two lines?</summary>`time.sleep(int(resp.headers["Retry-After"]))`, then send the same request again.</details>

## Cheat lines to say out loud
- "json= packs it and labels it; data= sends a form."
- "requests never raises on a 404 unless you call raise_for_status()."
- "Remember the brackets: .json() gives you a dict, and .text is just a string."
- "verify=False means a warning, not an error, and nothing gets checked."
- "On a 429, read Retry-After, int() it, sleep, and try again."
