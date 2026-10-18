# T10 · API authentication: essentials

> Blueprint 2.7 · Full note: [bee/T10-api-authentication.md](../bee/T10-api-authentication.md) · Teach-back 2026-10-18

## In one picture
![T10 at a glance: every API auth method as one card](../assets/T10/00-overview.png)
*Each card is one auth method, and every card has the same parts: how you get the credential, what goes on the wire, which Cisco platforms use it, and a red trap. The bottom strip covers 401 vs 403 and how to handle credentials.*

## The big idea
- Every API call has to prove who is calling. The method decides **what you show** and **how often you show it**.
- Think of a building:
  - **Basic auth** is showing your ID card at every door.
  - A **token** is a day visitor badge you collect once at reception.
  - An **API key** is a permanent staff pass made in the office portal.
  - A **cookie** is a wristband the building gives you after you sign in.
  - **OAuth** is a valet key. It lets an app do limited things for you without ever seeing your real key.
- On the exam, you will mostly read a header or a code snippet and name the method. You will also match each Cisco platform to its method, and tell 401 apart from 403.

## What you need to know

### 1. Who you are vs what you may do (401 vs 403)
- **Authentication** (**AuthN**) is the server checking **who** you are, using a password, token, key, cookie or certificate.
- **Authorisation** (**AuthZ**) is the server checking **what** that identity may do, based on a role (admin vs read-only) or an OAuth scope.
- Authentication always comes first, because the server can't decide what you may do until it knows who you are.

| Code | Meaning | What fixes it |
|---|---|---|
| `401 Unauthorized` | The credential is missing, wrong or expired. Despite its name, 401 is really about **authentication**. | Send the credential, or get a new one |
| `403 Forbidden` | The server knows who you are, but the action is not allowed | A different account, role or scope. A fresh token for the same user won't help |

- A `401` response includes a `WWW-Authenticate` header that names the scheme the server wants, for example `Basic realm="mock"` or `Bearer error="invalid_token"`.

![Authentication vs authorisation](../assets/T10/01-authn-vs-authz.png)
*If you fail the first check you get 401. If you pass it but fail the second, you get 403. Only passing both gets a 2xx.*

### 2. Basic auth: username and password on the request
- The recipe (RFC 7617):
  1. Join the username, a colon and the password: `user:password`.
  2. Base64-encode the result.
  3. Send it as `Authorization: Basic <result>`.
- The username can't contain a colon, because the first colon splits the user from the password.
- **Base64 is encoding, not encryption.** There is no key, so anyone who sees the header can decode it. For example, `YWRtaW46QzFzY28xMjM0NQ==` decodes straight back to `admin:C1sco12345`. Basic auth is only safe over **HTTPS**, which encrypts the whole request, headers included.
- Basic auth is used in two ways:
  - **On every request.** IOS XE RESTCONF and NX-API work this way.
  - **Once, to get a token.** Catalyst Center (DNA Center) does this with `POST /dna/system/api/v1/auth/token` ⚠ verify, and FMC does it with `generatetoken`.

### 3. Tokens and API keys: something other than the password
- **Custom token.** You log in once (often with Basic auth), receive a short-lived token, and then send that token on every call instead of the password. A token can expire or be revoked without changing the password.
- Where each platform puts the token (⚠ verify every row against the docs):

| Platform | Login call | Token comes back in | Send it as |
|---|---|---|---|
| Catalyst Center (DNA Center) | `POST /dna/system/api/v1/auth/token` + Basic | body `{"Token": "…"}` | `X-Auth-Token: <token>` |
| Secure Firewall Management Center (FMC) | `POST /api/fmc_platform/v1/auth/generatetoken` + Basic | **response headers** `X-auth-access-token`, `X-auth-refresh-token` | `X-auth-access-token: <token>` |
| Webex | no login call (token from the portal or OAuth) | n/a | `Authorization: Bearer <token>` |

- `Authorization: Bearer <token>` is the **standard** header (RFC 6750). `X-Auth-Token` and `X-auth-access-token` are vendor-specific headers. If you see any of them, the answer is "token auth".
- **Tokens expire.** On a `401`, either log in again or use a refresh call if the API has one.
  - FMC's SDK assumes the token lasts about 30 min and allows 3 refreshes ⚠ verify.
  - Catalyst Center tokens are often quoted as lasting 60 min ⚠ verify.

![Custom token flow](../assets/T10/03-token-flow.png)
*Yellow is the one Basic call. Green is the token replacing the password on every call. Red is expiry, which gives a 401 so you log in again.*

- **API key.** A person generates a long random string once in a web portal, and it is tied to their account. There is **no login call**: the key itself is the credential on every request.
- **Meraki** API keys:
  - The official SDK sends the key as `Authorization: Bearer <key>`.
  - The older header `X-Cisco-Meraki-API-Key: <key>` is still common in docs and exam material ⚠ verify which one is current. Learn to recognise both.
- You can send a key in a header or in the query string (`?api_key=…`).
  - Both work.
  - The query-string version is copied in full into server access logs, proxy logs and browser history, so prefer the header.
- An API key is long-lived and usually has the account's full rights. If it leaks, rotate it and store it like a password.
- **Key vs token:**
  - A key is created by a person in a portal and lasts for months.
  - A token is created by a login call and lasts for minutes or hours.

### 4. Cookies: the server remembers your session
- After you log in, the server sends `Set-Cookie: name=value`. The client sends it back as `Cookie: name=value` on every later call, and the server uses it to look up your session.
- **ACI APIC:**
  - Log in with `POST /api/aaaLogin.json` and the body `{"aaaUser": {"attributes": {"name": …, "pwd": …}}}`.
  - The reply contains a token, and the same token comes back as the cookie **`APIC-cookie`**.
- **SD-WAN Manager (vManage)** (⚠ verify the paths):
  1. `POST /j_security_check` with the form fields `j_username` and `j_password`. This returns the cookie `JSESSIONID`.
  2. `GET /dataservice/client/token`. The body of the reply is the XSRF token.
  3. Writes (POST/PUT/DELETE) need the cookie **plus** the header `X-XSRF-TOKEN: <token>`. If the header is missing, you get a `403`.
- **Why the XSRF header exists:** a browser sends cookies automatically, so a malicious web page could trigger a write using your cookie. That attack is called cross-site request forgery. The attacker can't set the extra header, so it blocks them.

![SD-WAN Manager style cookie + XSRF session](../assets/T10/05-cookie-session.png)
*Steps 1–2: logging in sets the cookie. Steps 3–4: the Session sends it back automatically. Steps 5–8: writes also need the XSRF header.*

### 5. OAuth 2.0: an app acting for a user (awareness)
- OAuth lets an app act **on behalf of a user**, for example to read their Webex rooms, without ever seeing the user's password. This is called **delegated access**.
- There are four roles:
  - the **resource owner**, which is the user
  - the **client**, which is the app
  - the **authorization server**, which logs the user in and issues tokens
  - the **resource server**, which is the API
- The **authorization-code grant** works like this:
  1. The app sends the user's browser to the authorization server's `/authorize` page.
  2. The user logs in **there**, not in the app.
  3. The browser is redirected back to the app with a one-time `code` and a `state` value.
  4. The app swaps the code, plus its `client_secret`, for tokens.
  5. The app calls the API with `Authorization: Bearer <access_token>`.

| Piece | What it is |
|---|---|
| `code` | Single use, short-lived (≤ 10 min). Reusing it gives `400 invalid_grant`. It is **not** the token. |
| `state` | An anti-CSRF value. The app checks that it comes back unchanged. |
| access token | Short-lived and sent as a Bearer token |
| refresh token | Long-lived. It gets a new access token **without the user logging in again**. |
| scope | Limits what the token may do. A missing scope gives `403 insufficient_scope`. |

![Animated OAuth 2.0 authorization-code flow](../assets/T10/08-oauth-code-flow.gif)
*The app never collects the password, and the code is swapped for the token behind the scenes.*

- **Webex** (⚠ verify the lifetimes):
  - An **integration** is an OAuth app that acts for a user. Its access tokens are often quoted at 14 days and refresh tokens at 90 days.
  - A **bot** has its own long-lived **bot token** from the portal, with no OAuth flow.
  - A **personal access token** is for testing and is often quoted at 12 h.

### 6. Python and safe credential handling
- These are the `requests` lines to recognise:

| Method | Code |
|---|---|
| Basic | `requests.get(url, auth=(user, pw))`, or the identical `auth=HTTPBasicAuth(user, pw)` |
| Custom token | `headers={"X-Auth-Token": token}` |
| Bearer token / key | `headers={"Authorization": f"Bearer {token}"}` |
| Form login | `s.post(url, data={...})`. Use `json=` for a JSON login such as APIC. |
| Remember for every call | `s = requests.Session()` then `s.headers.update({...})` |

- `auth=` already does the base64 encoding for you, so don't encode it by hand.
- A `Session` keeps cookies, `s.headers` and `s.auth` across calls. A plain `requests.get()` remembers nothing, and per-call `headers=` apply to that one call only.
- Never hardcode secrets in a script or commit them to Git.
  - Read them from environment variables or a vault.
  - `os.environ["X"]` fails loudly (`KeyError`) if the variable is missing. `os.environ.get("X")` quietly returns `None`, so the failure shows up later.
  - Keep real values in a git-ignored `labs/.env` file and load them with `set -a && source labs/.env && set +a`.
- HTTPS protects credentials **in transit only**. It doesn't stop a key in a query string from landing in a log. `verify=False` turns off certificate checks, which counts as a weakness in a code-review question.

![Identify the auth method from a snippet](../assets/T10/07-identify-method.png)
*Ask "is it Basic?" first. Then ask where the credential came from: a login call, a redirect plus code, or a portal.*

## Exam traps (the ones that catch people)
- 401 and 403 both look like "access denied". But **401 means the server doesn't know who you are**, so log in again. **403 means it knows you, but you aren't allowed**, so you need a different role or scope.
- Basic auth looks scrambled, but base64 is only encoding. Anyone can decode it, so HTTPS is required.
- Catalyst Center looks like it should use Bearer, but it uses **`X-Auth-Token`**. If you send a fresh token in the wrong header, you still get 401.
- FMC's token looks like it should be in the body, but it comes back in the **response headers** (`X-auth-access-token`).
- An SD-WAN Manager POST with a valid cookie can still fail. The cause is a missing `X-XSRF-TOKEN`, and the error is **403**, not 401.
- In OAuth, the code looks like a token, but it is a single-use code that is swapped for the token. The app never sees the user's password.
- A refresh looks like it should fix a 403 scope error, but a refreshed token has the **same scope**. You must ask the user for the wider scope.
- A Webex bot and an integration both send Bearer tokens. A bot uses its own long-lived token with no OAuth. An integration uses OAuth and acts for a user.

## Quick self-check
<details><summary>Q1. `requests.get(url, auth=("developer", pw))`: which method is this?</summary>HTTP Basic. `requests` builds `Authorization: Basic <base64>` for you.</details>
<details><summary>Q2. Someone sniffs `Authorization: Basic …` over plain HTTP. What do they get?</summary>The username and password, because base64 decodes without any key.</details>
<details><summary>Q3. Which header carries a Catalyst Center token?</summary>`X-Auth-Token`, not `Authorization: Bearer`.</details>
<details><summary>Q4. An OAuth token with scope `devices:read` gets 403 on a POST. What is the fix?</summary>Re-run the authorization flow and ask for a write scope. Refreshing only gives the same scope.</details>
<details><summary>Q5. Which two `requests` pieces keep the SD-WAN Manager cookie and XSRF header on every call?</summary>`requests.Session()` (its cookie jar keeps the cookie) and `s.headers.update({"X-XSRF-TOKEN": xsrf})`.</details>

## Cheat lines to say out loud
- "401 means who are you; 403 means I know you, but no."
- "Base64 is a costume, not a lock."
- "Meraki uses a key, Catalyst Center uses X-Auth-Token, Webex uses Bearer, APIC uses a cookie, and SD-WAN Manager uses a cookie plus XSRF."
- "In OAuth the password goes to the auth server, the code gets swapped for the token, and the refresh token skips the user."
- "Session remembers; plain requests forgets."
