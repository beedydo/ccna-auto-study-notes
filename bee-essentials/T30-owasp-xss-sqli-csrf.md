# T30 · OWASP: XSS, SQL injection, CSRF: essentials

> Blueprint 4.10: top OWASP threats (XSS, SQL injection, CSRF) · Full note: [bee/T30-owasp-xss-sqli-csrf.md](../bee/T30-owasp-xss-sqli-csrf.md) (not drafted yet) · Teach-back 2026-11-01

## The big idea
- All three attacks abuse **trust**. For each one, ask: **who trusts what, and how does the attacker slip something in?**
  - **SQL injection (SQLi):** the database trusts the query the app builds.
  - **Cross-site scripting (XSS):** the user's browser trusts scripts that come from the site.
  - **Cross-site request forgery (CSRF):** the site trusts any request that arrives with a valid session cookie.
- **Analogies:**
  - **SQLi is a poisoned order slip.** A customer writes "one burger, *and also give me the cash drawer*" on the order form, and the kitchen follows the whole slip blindly.
  - **XSS is a fake notice on the official noticeboard.** Staff read it and follow it because it's on the company board.
  - **CSRF is a forged form in your outbox.** Someone slips a pre-filled, pre-signed form into your outbox. The post room sends it because it came from your desk.
- **What the exam asks:** read a scenario or a code snippet, name the attack, then pick its fix. The three pairs to remember:
  - **SQLi → parameterised queries**
  - **XSS → output encoding**
  - **CSRF → anti-CSRF tokens**

## 🟥 Must know

### 1. OWASP and the Top 10
- **OWASP** = the **Open Worldwide Application Security Project**, a non-profit community that publishes free web-security guidance.
- The **OWASP Top 10** = its ranked list of the most critical web application security risks. Teams use it as a baseline checklist for secure development and code review.
- **Where the three attacks sit:**
  - SQLi and XSS are both **Injection** (A03 in the 2021 edition, A05 in 2025).
  - CSRF maps to **Broken Access Control** (A01 in both editions).
- ⚠ verify: which edition the 200-901 v1.1 exam expects. The blueprint names the three attacks, not category numbers, so **answer by name**.

### 2. SQL injection: input becomes part of the query
- **What it is:** the app builds a SQL statement by **gluing strings together** with user input. If the input contains SQL syntax (a quote, then extra conditions, then a comment marker such as `--`), it changes what the query does.
- **The analogy:** the kitchen (database) can't tell which part of the slip the restaurant wrote and which part the customer wrote, so it runs all of it.
- **The classic example:** a login form where the username is `' OR 1=1 --`.

```python
# Vulnerable: input is pasted into the SQL text
cur.execute(f"SELECT * FROM users WHERE name = '{name}'")
```

  - With `name = "' OR 1=1 --"`, the database receives `SELECT * FROM users WHERE name = '' OR 1=1 --'`.
  - `'` closes the app's quoted string early.
  - `OR 1=1` adds a condition that is always true, so the `WHERE` clause matches **every row**.
  - `--` starts a SQL comment, so the app's leftover closing `'` is ignored and the query stays valid.
  - Result: the query returns every row, or the login check is bypassed.
- **Impact:** read, change or delete data, and bypass authentication.

```
Attacker --(form field with SQL syntax)--> Web app --(glued-together SQL)--> Database
                                                       Database runs the attacker's logic
```

- **The fix: parameterised queries (prepared statements).** The SQL text and the values travel **separately**, so the database always treats the input as **data, never as code**.

```python
# Safe: ? placeholder, value passed separately as a tuple
cur.execute("SELECT * FROM users WHERE name = ?", (name,))
```

  - `?` is a placeholder: a slot for a value, not a place to paste text.
  - `(name,)` is the value, sent alongside. Even `' OR 1=1 --` is just compared as a weird username.
- **Why it matters:** "input validation" or "escaping" can look like the fix in an answer list. The best answer for SQLi is **parameterised queries** (or an ORM, which builds them for you).

### 3. Cross-site scripting (XSS): their script runs in your browser
- **What it is:** an attacker gets their script to run in **another user's browser**, delivered by a trusted site. The browser can't tell it apart from the site's own code.
- **The analogy:** the fake notice is on the official board (the trusted site), so every reader (browser) obeys it.
- **Impact:**
  - stealing session cookies, which lets the attacker take over the account
  - defacing the page or redirecting the user
  - performing actions *as the user*
- **The three types** (the exam names them from a scenario):
  - **Stored (persistent):** the script is **saved on the server**, for example in a comment or forum post, then served to **everyone** who views that page. Does the most damage.
  - **Reflected:** the script sits in a **URL or parameter**, often in a link sent by email. The server **echoes it straight back** in the response, for example on a search results page. Only the person who clicks the link is hit.
  - **DOM-based:** the page's own **client-side JavaScript** writes untrusted data into the page. The bug lives entirely in browser-side code; the server need not be involved.

```
Stored:    Attacker --(post with script)--> Server DB --(page)--> every Victim's browser runs it
Reflected: Attacker --(crafted link)--> Victim --(clicks)--> Server echoes it --> Victim's browser runs it
DOM:       Victim opens crafted URL --> page's own JS writes it into the DOM --> runs in browser
```

- **The fix: encode or escape output for its context.** Before the site puts user data into a page, it turns the special characters into harmless text, so the browser **displays** the script instead of **running** it.

```python
import html
safe = html.escape(user_comment)   # & < > " ' become &amp; &lt; &gt; &quot; &#x27;
```

  - A comment containing `<script>` is stored as text but rendered as `&lt;script&gt;`: the reader sees the characters, and nothing runs.
  - Each place data lands needs its own encoding: HTML body, HTML attribute, JavaScript, CSS, URL.
  - **Templating frameworks that auto-escape** do this for you (for example Jinja2 with autoescaping on, React, Angular).
- **Extra layers, not the primary fix:**
  - **`HttpOnly` cookie:** JavaScript can't read the cookie, so a script can't steal it. The script still runs.
  - **Content Security Policy (CSP) header:** the server tells the browser which script sources are allowed. OWASP calls it defence in depth.

### 4. CSRF: your cookie, their request
- **What it is:** the victim is logged in to `bank.example`. They visit a malicious page, which quietly makes **their browser** send a request to `bank.example`, such as a password change or a money transfer. The browser **attaches the session cookie automatically**, so the request looks legitimate.
- **The analogy:** the forged form came "from your desk" (your browser, your cookie), so the post room (the bank) sends it.

```
Victim (logged in to bank) --visits--> evil.example
evil.example --(hidden form/auto-submit)--> Victim's browser --(request + bank cookie)--> bank.example
bank.example: "valid cookie, so it must be the user" --> action performed
```

- **Key difference from XSS:** CSRF runs **no script on the trusted site**. It borrows your logged-in session to send **one forged request**, and the attacker usually can't read the response.
- **Impact:** unwanted state-changing actions: changing an email address or password, transferring funds.
- **The fix: an anti-CSRF token (the synchronizer token pattern).**
  - The server puts a **unique, unpredictable token** in each form (or a header) and checks it on every state-changing request.
  - The attacker's site can't know the token, so its forged request arrives without it and is rejected.

```python
import hmac
if not hmac.compare_digest(request.form["csrf_token"], session["csrf_token"]):
    abort(403)   # reject the forged request
```

  - `request.form["csrf_token"]` = the token the form sent back.
  - `session["csrf_token"]` = the token the server issued to this user.
  - `hmac.compare_digest` compares them; no match → `403`, nothing happens.
- **Backup layer: the `SameSite` cookie attribute** tells the browser not to attach the cookie to cross-site requests.
- **XSS defeats every CSRF defence**, because a script running on your own site can read the token. You need both protections.

### 5. Telling them apart (summary)

| Attack | What happens | Where it happens | Primary fix | OWASP category |
|---|---|---|---|---|
| **SQLi** | input changes what the SQL query does | server → database | **parameterised queries** (prepared statements) | Injection |
| **XSS** | attacker's script **runs** in another user's browser | victim's browser | **encode/escape output** for its context | Injection |
| **CSRF** | victim's browser **sends a forged request** with their cookie | victim's browser → trusted site | **anti-CSRF token** checked by the server, plus SameSite | Broken Access Control |

- **Cookie flags, one per attack:** `HttpOnly` → limits **XSS** cookie theft. `SameSite` → limits **CSRF**. `Secure` → cookie sent only over HTTPS.
- **Scenario cues:**
  - `' OR 1=1 --`, a query built with `+` or an f-string → **SQLi**.
  - A script runs for visitors, a comment box, a search page echoing input → **XSS**.
  - "Logged in, visited another site, an action happened, no script ran on the site" → **CSRF**.

## Exam traps
- **XSS vs CSRF:** XSS = the attacker's **script runs** in the victim's browser. CSRF = the victim's browser **sends a forged request** riding on their cookie; no script runs on the target site.
- **Fix mix-ups:** a CSRF token does nothing against SQLi; parameterised queries do nothing against XSS; input validation alone is not the "best" answer for SQLi or XSS.
- **Stored vs reflected vs DOM:** saved on the server, hits everyone = stored. In the URL, bounced back once = reflected. Only in the page's JavaScript = DOM.
- **`HttpOnly` vs `SameSite`:** `HttpOnly` is about XSS (JavaScript can't read the cookie). `SameSite` is about CSRF (the cookie isn't sent cross-site).
- **CSP is defence in depth for XSS**, not the primary fix. **Escaping SQL input by hand** is discouraged: pick placeholders or an ORM.
- **OWASP category numbers differ by edition** (Injection is A03 in 2021, A05 in 2025), so answer by name.

<details><summary><b>🟨 Should know (second pass)</b></summary>

- **More SQLi defences, from OWASP:**
  - **ORMs** (object-relational mappers): libraries that build parameterised SQL for you. OWASP lists them as a safe API.
  - **Stored procedures**, but only if they are parameterised.
  - **Allow-list input validation:** required where placeholders can't be used, such as table or column names. Elsewhere it is a secondary defence.
  - **Least-privilege database accounts:** the app's account never has DBA rights, so a successful injection can do less damage.
  - OWASP **strongly discourages escaping input by hand** (fragile), and notes that "validated" input is still not safe to build into SQL as a string.
- **More XSS detail:**
  - Avoid the auto-escape escape hatches in frameworks, such as React's `dangerouslySetInnerHTML`.
  - Allow-list input validation supports output encoding but does not replace it.
- **`SameSite` values:**
  - `Strict` never sends the cookie on cross-site requests.
  - `Lax` sends it only on top-level navigations that use safe methods such as GET. Many browsers use `Lax` by default.
  - `None` always sends the cookie and requires `Secure`.
- **More CSRF defences:**
  - Check the `Origin` and `Referer` headers to confirm the request came from your own site.
  - Re-authentication or confirmation (password prompt, one-time code) before sensitive actions.
  - **Never change state with GET**, because GET requests get past SameSite `Lax`.
- **General defences that cover all three:** input validation (allow-list type, length, format), output encoding, parameterised queries, least privilege for DB accounts and API tokens, CSP, cookie flags. Data handling is in [T29](../bee/T29-secrets-encryption-data-handling.md); session and token handling in [T10](../bee/T10-api-authentication.md).
- **The rest of the Top 10 (awareness):** broken access control, cryptographic failures, insecure design, security misconfiguration, vulnerable or outdated components, authentication failures, integrity failures, logging and monitoring failures, and SSRF.

</details>

> **Recognise only, details to be added to the full note:** the full 2021 and 2025 Top 10 lists in order (2025 adds Software Supply Chain Failures and Mishandling of Exceptional Conditions, and folds SSRF into A01), per-context encoding rules (attribute, JS, CSS, URL), CSP directive syntax, `SameSite=None` + `Secure` details.

## Quick self-check
<details><summary>Q1. A comment box saves user text, and later every visitor's browser runs a script hidden in a comment. Attack and primary fix?</summary>Stored XSS. Encode or escape the output for its HTML context, for example with an auto-escaping template engine. CSP and HttpOnly are extra layers.</details>
<details><summary>Q2. Code: <code>"SELECT * FROM devices WHERE site = '" + site + "'"</code>. Risk and fix?</summary>SQL injection. Use a parameterised query (<code>... WHERE site = ?</code> with the value passed separately) or an ORM, and a least-privilege database account.</details>
<details><summary>Q3. A user logged in to an admin portal visits another site, and their password gets changed. No script ran on the portal. What happened, and the best defence?</summary>CSRF. An anti-CSRF token validated by the server on every state-changing request, backed up by SameSite cookies and re-authentication for password changes.</details>
<details><summary>Q4. Which cookie attribute stops JavaScript reading the session cookie, and which attack does it limit?</summary><code>HttpOnly</code>, which limits XSS session theft. (<code>SameSite</code> is the CSRF one.)</details>
<details><summary>Q5. Which OWASP Top 10 category contains both SQLi and XSS?</summary>Injection: A03 in 2021, A05 in 2025. CSRF maps to Broken Access Control (A01).</details>
<details><summary>Q6. A phishing email links to a search page with a script in the <code>?q=</code> parameter, and the page echoes it back. Only people who click are hit. Which XSS type?</summary>Reflected XSS: the script is in the URL and the server bounces it straight back once.</details>
<details><summary>Q7. Why doesn't a CSRF token protect a site that also has an XSS bug?</summary>A script running on the site's own pages can read the token and send it with the forged request. XSS defeats every CSRF defence, so fix XSS too.</details>

## Say it out loud
- "SQLi: input becomes code. The fix is placeholders, so data stays data."
- "XSS: their script, my browser, your site. The fix is to encode the output."
- "CSRF: my cookie, their request. The fix is a token they can't guess, plus SameSite."
- "Stored hits everyone, reflected hits whoever clicks, DOM is the page's own JavaScript."
- "HttpOnly is for XSS, SameSite is for CSRF."

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
