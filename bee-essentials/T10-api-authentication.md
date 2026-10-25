# T10 · API authentication: essentials

> Blueprint 2.7: auth mechanisms (basic, custom token, API key) · Full note: [bee/T10-api-authentication.md](../bee/T10-api-authentication.md)

![T10 at a glance: every API auth method as one card](../assets/T10/00-overview.png)

*Each card is one auth method, with the same parts: how you get the credential, what goes on the wire, which Cisco platforms use it, and a red trap. The bottom strip covers 401 vs 403 and credential handling.*

## 🧭 The big idea

Every API call has to prove **who is calling**. Each auth method answers one question differently: **what do you show, and how often do you show it?**

**Analogy: getting into an office building.**

| | Method | What you show | How often | Office-building analogy |
|---|---|---|---|---|
| 🪪 | **Basic auth** | username + password | **every single request** | showing your **ID card at every door** |
| 🎫 | **Custom token** | a token from a login call | ID **once**, then the token on every call; it expires | a **day visitor badge**. You show your ID **once** at reception (a login call), get a badge (the token), and wear the badge to every door. The badge expires at the end of the day. |
| 🔑 | **API key** | a key made in a portal | every call, for months, until cancelled | a **permanent staff pass** made in the HR portal. No reception desk: you just tap it at every door, for months, until someone cancels it. |
| 🍪 | **Cookie** | a cookie set after sign-in | automatically on every call | a **wristband** the building puts on you after sign-in; your browser shows it automatically |
| 🚗 | **OAuth** | an access token issued for an app | | a **valet key**: it lets an app do limited things for you without ever seeing your real key |

- 🎯 **What the exam asks:** read a header or a code snippet and name the method; match Cisco platforms to their method; tell 401 from 403. The blueprint names three methods (Basic, custom token, API key), so those are the core.

## 🟥 Must know

### 1. 🪪 Basic auth: username and password on every request

**Recipe:**

1. Join the username, a colon and the password: `admin:C1sco12345`.
2. Base64-encode it: `YWRtaW46QzFzY28xMjM0NQ==`.
3. Send it in the header on every call:

```http
GET /restconf/data/ietf-interfaces:interfaces HTTP/1.1
Host: sandbox-iosxe.cisco.com
Authorization: Basic YWRtaW46QzFzY28xMjM0NQ==
```

> 💡 **Base64 is encoding, not encryption.** There's no key or secret: anyone who sees the header can decode it straight back to `admin:C1sco12345`. That's why Basic auth is **only safe over HTTPS**, which encrypts the whole request including headers.

- 🐍 **In Python** you never encode by hand; `requests` does it:

```python
requests.get(url, auth=("admin", "C1sco12345"))   # builds the Authorization: Basic header for you
```

**🧩 Two ways Cisco uses Basic:**

| 🔁 On every request | 1️⃣ Once, just to get a token |
|---|---|
| IOS XE RESTCONF, NX-API | Catalyst Center (DNA Center) and FMC (see section 2) |

![Basic auth on every request](../assets/T10/02-basic-auth.png)

*The same Base64 string goes out on every call, and the server checks the password each time.*

### 2. 🎫 Custom token: log in once, then send the token

> 💡 **Why:** the password crosses the wire **once**. After that, every call carries a short-lived token instead. A token can expire or be cancelled without changing the password.

**The three steps** (Catalyst Center example):

```python
# 1. Log in once with Basic auth to the token endpoint
r = requests.post("https://dnac/dna/system/api/v1/auth/token", auth=(user, pw))
token = r.json()["Token"]                       # the token comes back in the body

# 2. Send the token on every later call, in Catalyst Center's custom header
headers = {"X-Auth-Token": token}
devices = requests.get("https://dnac/dna/intent/api/v1/network-device", headers=headers)

# 3. When the token expires, calls return 401 → log in again (step 1)
```

**Where each platform puts the token** (⚠ verify each row against current docs):

| Platform | Login call | Token comes back in | Send it on later calls as |
|---|---|---|---|
| Catalyst Center (DNA Center) | `POST /dna/system/api/v1/auth/token` with Basic | the **body**: `{"Token": "…"}` | **`X-Auth-Token: <token>`** |
| Secure Firewall Management Center (FMC) | `POST /api/fmc_platform/v1/auth/generatetoken` with Basic | the **response headers**: `X-auth-access-token` | `X-auth-access-token: <token>` |
| Webex | no login call (token from the developer portal or OAuth) | n/a | `Authorization: Bearer <token>` |

**Standard vs custom header:**

| ✅ Standard | 🏷️ Custom (vendor-specific) |
|---|---|
| `Authorization: Bearer <token>` is the **standard** way to send a token | `X-Auth-Token` and `X-auth-access-token` are **vendor-specific** (custom) names |

> 🎯 Any of them in a snippet → the answer is "**token** auth".

![Custom token flow](../assets/T10/03-token-flow.png)

*Yellow = the one Basic login call. Green = the token replaces the password on every call. Red = the token expires, you get 401, you log in again.*

### 3. 🔑 API key: a long-lived key from a portal, no login

> 💡 An **API key** is a long random string a **person generates once in a web portal** (e.g. the Meraki dashboard). It's tied to their account. **There is no login call.** The key itself is the credential, sent on every request:

```python
headers = {"Authorization": f"Bearer {meraki_key}"}        # what the official Meraki SDK sends
# or, the older header still shown in many docs and exam questions:
headers = {"X-Cisco-Meraki-API-Key": meraki_key}
requests.get("https://api.meraki.com/api/v1/organizations", headers=headers)
```

- Recognise both Meraki headers (⚠ verify which one Cisco treats as current).

**Header vs query string:** a key can also go in the URL (`?api_key=…`). Both work, but:

| ✅ Header | ❌ Query string `?api_key=…` |
|---|---|
| prefer the header | the URL version gets **copied in full into server logs, proxy logs and browser history** |

- ⚠️ **Risk:** a key lives for months and usually has the account's full rights. If it leaks, it keeps working until someone revokes it. Rotate it and store it like a password.

| | 🔑 API key | 🎫 Token |
|---|---|---|
| Created by | a **person**, in a **portal** | a **login call** |
| Lives for | months, until rotated | minutes to hours |
| Login step? | ❌ **no** | ✅ **yes**, once |

### 4. 🚦 401 vs 403: who you are vs what you may do

> 💡 AuthN always happens first: the server can't decide what you may do until it knows who you are.

| 🆔 Authentication (AuthN) | 🛂 Authorisation (AuthZ) |
|---|---|
| the server checks **who** you are (password, token, key) | the server checks **what** that identity may do (admin vs read-only role) |

| Code | What it really means | What fixes it |
|---|---|---|
| 🆔 `401 Unauthorized` | "**Who are you?**" The credential is missing, wrong or expired. (Despite the name, it's about authentication.) | send the credential, or get a fresh token |
| 🛂 `403 Forbidden` | "**I know who you are, but no.**" Your role doesn't allow this action. | a different account or role. A fresh token for the same user **won't** help. |

- Example: a read-only user's valid token works for `GET /devices` (`200`) but gets `403` on `POST /devices`.

### 5. 🗺️ Platform cheat table

| | Platform | Method | What you send |
|---|---|---|---|
| 🪪 | IOS XE RESTCONF · NX-API | Basic, every call | `Authorization: Basic …` |
| 🎫 | Catalyst Center (DNA Center) | Basic login → token | `X-Auth-Token: <token>` |
| 🎫 | FMC | Basic login → token (in response headers) | `X-auth-access-token: <token>` |
| 🔑 | Meraki | API key | `Authorization: Bearer <key>` or `X-Cisco-Meraki-API-Key: <key>` |
| 🎫 | Webex | Bearer token | `Authorization: Bearer <token>` |
| 🍪 | ACI (APIC) | login → cookie | `Cookie: APIC-cookie=…` (see Should know) |

### 6. 🔒 Handle credentials safely

> 💡 **Never hardcode** a password, token or key in a script, and never commit one to Git. Read them from **environment variables** instead:

```python
import os
user = os.environ["DNAC_USER"]       # fails loudly (KeyError) if the variable isn't set
pw   = os.environ["DNAC_PASS"]
```

| | |
|---|---|
| 🧠 `requests.Session()` | remembers cookies and headers you set on it across calls; a plain `requests.get()` remembers nothing |
| ❌ `verify=False` | turns off TLS certificate checks. In a code-review question it counts as a weakness. |

![Identify the auth method from a snippet](../assets/T10/07-identify-method.png)

*Ask "is it Basic?" first. Then ask where the credential came from: a login call (token), a portal (key), or a redirect and code (OAuth).*

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| 401 and 403 both mean "log in again" | **401 ≠ 403.** 401 = log in again. 403 = you're known but not allowed; a fresh token won't fix it. |
| Base64 hides the password | **Base64 looks scrambled but isn't secret.** Anyone can decode it, so Basic needs HTTPS. |
| Catalyst Center takes `Authorization: Bearer` | **Catalyst Center uses `X-Auth-Token`, not Bearer.** A valid token in the wrong header still gets 401. |
| FMC returns the token in the body | **FMC's token comes back in the response headers**, not the body. |
| An API key is just another token | **Key vs token:** a key has **no login call** and lasts months; a token comes from a login call and expires. |
| A JWT (`Bearer eyJ…`) is a fourth auth method | It's a token **format**: still **token auth**. Its payload is only base64url-encoded, so anyone can read it; the signature just stops tampering. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 🍪 Cookie sessions

> 💡 After login the server sends `Set-Cookie: name=value`; the client sends `Cookie: name=value` on every later call, and the server uses it to find your session. `requests.Session()` stores and replays cookies automatically.

| Platform | Login | Cookie | Extra |
|---|---|---|---|
| **ACI APIC** | `POST /api/aaaLogin.json` with `{"aaaUser": {"attributes": {"name": "admin", "pwd": "…"}}}` | the token comes back in the body **and** as the cookie `APIC-cookie` | |
| **SD-WAN Manager (vManage)** | `POST /j_security_check` with form fields `j_username` / `j_password` | `JSESSIONID` | writes also need an `X-XSRF-TOKEN` header (fetched from `GET /dataservice/client/token`). Cookie without the header → **403**. ⚠ verify paths. |

> 🔐 Why the extra header: browsers send cookies automatically, so a malicious web page could trigger a write with your cookie (cross-site request forgery). The attacker can't add the header.

### 🚗 OAuth 2.0 (awareness)

> 💡 Lets an **app act for a user** without seeing the user's password.

1. The app sends the user to the authorization server's login page.
2. The user logs in **there**, not in the app.
3. The app receives a one-time `code`.
4. The app swaps the code for an **access token**.
5. The app calls the API with `Authorization: Bearer <access_token>`.

### 🧾 JWT: what a token can look like (awareness)

> 💡 **JWT (JSON Web Token) is a token *format*, not a fourth auth method.** It travels like any token, `Authorization: Bearer <jwt>`, so on the exam it is still **token auth**. Blueprint 2.7 doesn't name it; you'll meet it in Bob's T25 (CML) and T22 (newer SD-WAN Manager login).

**Spot it:** three base64url parts joined by dots, and the first two usually start with **`eyJ`** (base64 of `{"`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 . eyJzdWIiOiJhZG1pbiIsImlzcyI6ImNtbCIs… . Ieaie3-UuAUCFiojqkfPPEMRUM8C6Y8_-eXcTvgQfEI
└──────────── header ──────────────┘   └───────────── payload ─────────────┘   └──────────── signature ────────────┘
{"alg":"HS256","typ":"JWT"}            {"sub":"admin","iss":"cml","exp":…}      HMAC-SHA256(header.payload, server secret)
```

| | Part | Holds | Can anyone read it? |
|---|---|---|---|
| 🏷️ | **Header** | `alg` (signing algorithm, e.g. `HS256`, `RS256`) and `typ` | ✅ yes: base64url only |
| 📋 | **Payload** | **claims**, facts about the caller: `sub` who, `iss` issuer, `aud` audience, `exp` expiry, `iat` issued at | ✅ **yes**: base64url only, **not encrypted** |
| ✍️ | **Signature** | proves header + payload weren't changed | needs the key to create or check |

> 🪪 **Analogy: a signed, laminated visitor badge.** Anyone can read the name and expiry printed on it, but only reception's stamp makes it valid. Change the name and the stamp no longer matches.

| ✅ Why APIs use it | ⚠️ The catch |
|---|---|
| **Self-contained:** the server checks the signature and reads `exp`/`sub` straight from the token, with no session lookup | **Readable by anyone:** never put secrets in a JWT, and send it over HTTPS (same lesson as Basic's base64) |
| Tampering fails: change `sub` to `root` and the signature check fails | `"alg": "none"` = an **unsecured** JWT with no signature; a server must reject it |

| 🧩 Cisco | Login | Then send |
|---|---|---|
| Cisco Modeling Labs (CML) | `POST /api/v0/authenticate` with `{"username", "password"}` | `Authorization: Bearer <jwt>` |
| SD-WAN Manager 20.18.1+ | `POST /jwt/login` ⚠ verify | the JWT (see T22) |

### 💬 Webex identities

| Identity | Credential |
|---|---|
| 🤖 **bot** | has its own long-lived token, no OAuth |
| 🔌 **integration** | uses OAuth and acts for a user |
| 🧪 **personal access token** | is for quick testing |

![Animated OAuth 2.0 authorization-code flow](../assets/T10/08-oauth-code-flow.gif)

</details>

> 📚 **Recognise only, details in the full note:** OAuth roles, `state`, scopes and refresh tokens, the `WWW-Authenticate` header, token lifetimes (⚠ verify), `HTTPBasicAuth()` (same as `auth=(u, p)`), `os.environ["X"]` vs `.get("X")`, JWT claim list (`nbf`, `jti`) and JWE (encrypted JWT).

## ✍️ Quick self-check
<details><summary>Q1. <code>requests.get(url, auth=("developer", pw))</code>: which method?</summary>HTTP Basic. <code>requests</code> builds <code>Authorization: Basic &lt;base64&gt;</code> for you.</details>
<details><summary>Q2. Someone sniffs <code>Authorization: Basic …</code> over plain HTTP. What do they get?</summary>The username and password, because base64 decodes without any key.</details>
<details><summary>Q3. Which header carries a Catalyst Center token?</summary><code>X-Auth-Token</code>, not <code>Authorization: Bearer</code>.</details>
<details><summary>Q4. A valid user gets <code>403</code> on a POST. Will logging in again fix it?</summary>No. 403 means the identity is known but not allowed. It needs a different role.</details>
<details><summary>Q5. A string generated once in the Meraki dashboard, sent on every call with no login: which method?</summary>API key.</details>
<details><summary>Q6. A script POSTs to <code>/auth/token</code> with Basic, then sends <code>X-Auth-Token</code> on later calls. Which method?</summary>Custom token. Basic is used only once, to log in.</details>
<details><summary>Q7. Why prefer a header over <code>?api_key=</code> in the URL?</summary>The URL, including the key, is copied into server and proxy logs and browser history.</details>
<details><summary>Q8. A token starts <code>eyJhbGci…</code> and has two dots. What is it, and is its content secret?</summary>A JWT. Its header and payload are only base64url-encoded, so anyone can read them. The signature only proves nobody changed them.</details>

## 🗣️ Say it out loud
- 🪪🎫🔑 "Basic shows the password every time; a token logs in once; a key never logs in."
- 🚦 "401 means who are you; 403 means I know you, but no."
- 🪪 "Base64 is a costume, not a lock."
- 🗺️ "Meraki uses a key, Catalyst Center uses X-Auth-Token, Webex uses Bearer."
