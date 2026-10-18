# T30 · OWASP: XSS, SQL injection, CSRF: essentials

> Blueprint 4.10 · Full note: [bee/T30-owasp-xss-sqli-csrf.md](../bee/T30-owasp-xss-sqli-csrf.md) (not drafted yet) · Teach-back 2026-11-01

## In one picture

| Attack | What it does, in plain words | Where it happens | The fix | OWASP category |
|---|---|---|---|---|
| **SQL injection (SQLi)** | User input is glued into a SQL statement, so the input changes what the query does | Server → database | Parameterised queries (prepared statements) | Injection: A03:2021, A05:2025 |
| **Cross-site scripting (XSS)** | The attacker's script ends up running in *another user's* browser, as if the trusted site sent it | Victim's browser | Encode/escape output for its context | Injection: A03:2021, A05:2025 |
| **Cross-site request forgery (CSRF)** | A malicious site makes the victim's browser send a request to a site where the victim is already logged in | Victim's browser → trusted site | Anti-CSRF token checked by the server, plus SameSite cookies | Broken Access Control: A01 (2021 and 2025) |

## The big idea

- All three attacks abuse **trust**:
  - SQLi: the database trusts the query the app builds.
  - XSS: the user's browser trusts scripts that come from the site.
  - CSRF: the site trusts any request that arrives with a valid session cookie.
- The exam gives you a scenario or a code snippet. You name the attack, then pick its fix. The pairs to remember are **SQLi → parameterised queries**, **XSS → output encoding**, **CSRF → anti-CSRF tokens**.

## What you need to know

### 1. What OWASP and the Top 10 are

- **OWASP** stands for the **Open Worldwide Application Security Project**. It is a non-profit community that publishes free web-security guidance.
- The **OWASP Top 10** is its ranked list of the most critical web application security risks. Teams use it as a baseline checklist for secure development and code review.
- There are two editions you might meet:
  - **2021** (the repo's concept list uses this one): A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 Server-Side Request Forgery (SSRF).
  - **2025** (the current edition): A01 Broken Access Control, A02 Security Misconfiguration, A03 Software Supply Chain Failures, A04 Cryptographic Failures, A05 Injection, A06 Insecure Design, A07 Authentication Failures, A08 Software or Data Integrity Failures, A09 Security Logging and Alerting Failures, A10 Mishandling of Exceptional Conditions. In 2025, SSRF moved into A01.
- ⚠ verify: which edition the 200-901 v1.1 exam expects. The blueprint just says "top OWASP threats (XSS, SQL injection, CSRF)", so learn the three attacks by name and don't rely on category numbers.

### 2. SQL injection

- **What it is:** the app builds a SQL statement by gluing strings together with user input. Input containing SQL syntax (a quote, then extra conditions, then a comment marker such as `--`) changes the query's logic.
  - The classic exam example is a login form where the username `' OR 1=1 --` makes the `WHERE` clause always true. The query returns every row, or the login check is bypassed.
- **Analogy:** a customer writes "one burger, *and also give me the cash drawer*" on the order form, and the kitchen follows the whole slip blindly.
- **Impact:** an attacker can read, change or delete data, and can bypass authentication.

```
Attacker --(form field with SQL syntax)--> Web app --(glued-together SQL)--> Database
                                                       Database runs the attacker's logic
```

- **The fix is parameterised queries (prepared statements).** The SQL text and the values travel separately, so the database always treats the input as **data, never as code**.

```python
# Vulnerable: input is pasted into the SQL text
cur.execute(f"SELECT * FROM users WHERE name = '{name}'")

# Safe: ? placeholder, value passed separately as a tuple
cur.execute("SELECT * FROM users WHERE name = ?", (name,))
```

- More SQLi defences, from OWASP:
  - **ORMs** (object-relational mappers). These are libraries that build parameterised SQL for you. OWASP lists them as a safe API.
  - **Stored procedures**, but only if they are parameterised.
  - **Allow-list input validation.** This is required where placeholders can't be used, such as table or column names. Elsewhere it is a secondary defence.
  - **Least-privilege database accounts.** The app's account should never have DBA rights, so a successful injection can do less damage.
- OWASP **strongly discourages escaping input by hand** because it is fragile. OWASP also notes that "validated" input is still not safe to build into SQL as a string.

### 3. Cross-site scripting (XSS): stored, reflected and DOM

- **What it is:** an attacker gets their script to run in **another user's browser**, delivered by a trusted site. The browser can't tell it apart from the site's own code.
- **Analogy:** someone pins a fake notice on the company noticeboard. Staff read it and follow it because it's on the official board.
- **Impact:**
  - stealing session cookies, which lets the attacker take over the account
  - defacing the page or redirecting the user
  - performing actions *as the user*
- **The three types:**
  - **Stored (persistent):** the script is saved on the server, for example in a comment or forum post. It is then served to **everyone** who views that page. This type does the most damage.
  - **Reflected:** the script sits in a URL or parameter, often in a link sent by email. The server **echoes it straight back** in the response, for example on a search results page. Only the person who clicks the link is hit.
  - **DOM-based:** the page's own **client-side JavaScript** writes untrusted data into the page. The bug lives entirely in the browser-side code, and the server need not be involved.

```
Stored:    Attacker --(post with script)--> Server DB --(page)--> every Victim's browser runs it
Reflected: Attacker --(crafted link)--> Victim --(clicks)--> Server echoes it --> Victim's browser runs it
DOM:       Victim opens crafted URL --> page's own JS writes it into the DOM --> runs in browser
```

- **Defences:**
  - **Encode or escape output for its context.** HTML body, HTML attribute, JavaScript, CSS and URL each need their own encoding. This is the primary fix.
  - **Use templating frameworks that auto-escape** (for example Jinja2 with autoescaping on, React or Angular). Avoid their escape hatches, such as React's `dangerouslySetInnerHTML`.
  - **Validate input** with an allow-list. This supports output encoding but does not replace it.
  - **Content Security Policy (CSP) header:** the server tells the browser which script sources are allowed. OWASP calls it defence in depth, not the primary defence.
  - **`HttpOnly` cookies:** JavaScript can't read the cookie, so stolen-cookie damage is limited. This does not stop the script from running.

```python
import html
safe = html.escape(user_comment)   # & < > " ' become &amp; &lt; &gt; &quot; &#x27;
```

### 4. Cross-site request forgery (CSRF)

- **What it is:** the victim is logged in to `bank.example`. They visit a malicious page, which quietly makes their browser send a request to `bank.example`, such as a password change or a money transfer. The browser **attaches the session cookie automatically**, so the request looks legitimate.
- **Analogy:** someone slips a pre-filled, pre-signed form into your outbox. The post room sends it because it came from your desk.
- **Key difference from XSS:** CSRF runs **no script on the trusted site**. It borrows your logged-in session to send *one forged request*. The attacker usually can't read the response.
- **Impact:** unwanted state-changing actions, such as changing an email address or password, or transferring funds.

```
Victim (logged in to bank) --visits--> evil.example
evil.example --(hidden form/auto-submit)--> Victim's browser --(request + bank cookie)--> bank.example
bank.example: "valid cookie, so it must be the user" --> action performed
```

- **Defences:**
  - **Anti-CSRF token (the synchronizer token pattern).** The server puts a unique, unpredictable token in each form or header and checks it on every state-changing request. The attacker's site can't know the token, so its forged request fails.
  - **`SameSite` cookie attribute:**
    - `Strict` never sends the cookie on cross-site requests.
    - `Lax` sends it only on top-level navigations that use safe methods such as GET. Many browsers use `Lax` by default.
    - `None` always sends the cookie and requires `Secure`.
  - **Check the `Origin` and `Referer` headers** to confirm the request came from your own site.
  - **Re-authentication or confirmation** (password prompt, one-time code) before sensitive actions.
  - **Never change state with GET.** GET requests get past SameSite `Lax`.
- **XSS defeats every CSRF defence**, because a script running on your own site can read the token. You need both protections.

```python
import hmac
if not hmac.compare_digest(request.form["csrf_token"], session["csrf_token"]):
    abort(403)   # reject the forged request
```

### 5. General defences (one list for all three)

- **Input validation:** allow-list what's expected (type, length, format) and reject everything else. It supports the main fixes and does not replace them. See [T29](../bee/T29-secrets-encryption-data-handling.md) for data handling.
- **Output encoding:** escape data for the place it lands (HTML, JS, URL). This is the main XSS fix.
- **Parameterised queries:** these keep code and data separate. This is the main SQLi fix, also covered in [T29](../bee/T29-secrets-encryption-data-handling.md).
- **Least privilege:** give the app's database account and API tokens only the rights they need. This limits the blast radius when something gets through.
- **CSP:** restricts where scripts can load from, so it limits XSS.
- **Cookie flags:** `HttpOnly` limits XSS cookie theft, `SameSite` limits CSRF, and `Secure` means the cookie is sent only over HTTPS. Session and token handling is covered in [T10](../bee/T10-api-authentication.md).
- **Awareness of the rest of the Top 10:** broken access control, cryptographic failures, insecure design, security misconfiguration, vulnerable or outdated components, authentication failures, integrity failures, logging and monitoring failures, and SSRF.

## Exam traps (the ones that catch people)

- **XSS vs CSRF:**
  - XSS = the attacker's **script runs** in the victim's browser.
  - CSRF = the victim's browser **sends a forged request** that rides on their cookie, and no script runs on the target site.
- **Fix mix-ups:**
  - A CSRF token does nothing against SQLi.
  - Parameterised queries do nothing against XSS.
  - Input validation alone is not the "best" answer for either SQLi or XSS.
- **Stored vs reflected:**
  - Saved on the server and seen by everyone = stored.
  - In the URL and bounced back once = reflected.
  - Only in the page's JavaScript = DOM.
- **`HttpOnly` vs `SameSite`:** `HttpOnly` is about XSS (JavaScript can't read the cookie). `SameSite` is about CSRF (the cookie isn't sent cross-site).
- **`' OR 1=1 --` in a scenario** points to SQLi, and the answer is a parameterised query.
- **CSP is defence in depth for XSS**, not the primary fix.
- **Escaping SQL input by hand** is discouraged. Pick placeholders or an ORM.
- **OWASP category numbers differ by edition** (Injection is A03 in 2021 and A05 in 2025), so answer by name.

## Quick self-check

1. A comment box saves user text, and later every visitor's browser runs a script hidden in a comment. What is the attack and the primary fix?
<details><summary>Answer</summary>Stored XSS. Encode or escape the output for its HTML context, for example with an auto-escaping template engine. CSP and HttpOnly are extra layers.</details>

2. Code: `"SELECT * FROM devices WHERE site = '" + site + "'"`. What is the risk and the fix?
<details><summary>Answer</summary>SQL injection. Use a parameterised query (`... WHERE site = ?` with the value passed separately) or an ORM, and use a least-privilege database account.</details>

3. A user logged in to an admin portal visits another site, and their password gets changed. No script ran on the portal. What happened, and what is the best defence?
<details><summary>Answer</summary>CSRF. The best defence is an anti-CSRF token validated by the server on every state-changing request, backed up by SameSite cookies and re-authentication for password changes.</details>

4. Which cookie attribute stops JavaScript from reading the session cookie, and which attack does it limit?
<details><summary>Answer</summary>`HttpOnly` limits XSS session theft. (`SameSite` is the CSRF one.)</details>

5. Which OWASP Top 10 category contains both SQLi and XSS?
<details><summary>Answer</summary>Injection: A03 in 2021, A05 in 2025. CSRF maps to Broken Access Control (A01).</details>

## Cheat lines to say out loud

- "SQLi: input becomes code. The fix is placeholders, so data stays data."
- "XSS: their script, my browser, your site. The fix is to encode the output."
- "CSRF: my cookie, their request. The fix is a token they can't guess, plus SameSite."
- "Stored hits everyone, reflected hits whoever clicks, DOM is the page's own JavaScript."
- "HttpOnly is for XSS, SameSite is for CSRF."
- "XSS beats every CSRF defence, so fix XSS first."

## Sources

- https://top10.owasp.org/2025
- https://top10.owasp.org/2025/A05_2025-Injection
- https://top10.owasp.org/2025/A01_2025-Broken_Access_Control
- https://top10.owasp.org/2021/A03_2021-Injection
- https://top10.owasp.org/2021/A01_2021-Broken_Access_Control
- https://community.owasp.org/attacks/xss
- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- https://docs.python.org/3/library/sqlite3.html
- https://docs.python.org/3/library/html.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie
