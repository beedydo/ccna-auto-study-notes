---
id: T11
title: "Python requests scripting"
owner: Beedy
blueprint: "2.9"
primary_domain: D2
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-11
teach_back: 2026-10-12
cross_study: 2026-10-22
---

# T11 · Python requests scripting

> Owner: **Beedy** · Blueprint: **2.9** · CBT coverage: **Full** · Learn by 2026-10-11 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T11.01 · Calls

**Must cover:**

- [ ] import requests
- [ ] requests.get / post / put / patch / delete(url, ...)
- [ ] Or the generic requests.request("GET", url, ...)

**Notes:**

<!-- TODO -->

### T11.02 · Arguments

**Must cover:**

- [ ] headers={...}: Content-Type, Accept, auth headers
- [ ] params={...}: builds the query string (?a=1&b=2)
- [ ] json=dict: serialises body and sets Content-Type: application/json
- [ ] data=string/dict: raw or form-encoded body (you set Content-Type yourself)
- [ ] auth=(user, pass), verify=False (skip TLS check), timeout=seconds

**Notes:**

<!-- TODO -->

### T11.03 · Response

**Must cover:**

- [ ] resp.status_code (int), resp.ok (True for <400)
- [ ] resp.headers (dict-like), resp.text (str), resp.content (bytes)
- [ ] resp.json() → Python dict/list
- [ ] resp.raise_for_status() raises HTTPError on 4xx/5xx

**Notes:**

<!-- TODO -->

### T11.04 · Sessions

**Must cover:**

- [ ] s = requests.Session() keeps cookies and default headers across calls
- [ ] s.headers.update({"X-Auth-Token": token})
- [ ] Reuses TCP connections (faster)

**Notes:**

<!-- TODO -->

### T11.05 · Errors

**Must cover:**

- [ ] requests.exceptions.HTTPError (from raise_for_status)
- [ ] ConnectionError (host unreachable), Timeout
- [ ] try: … except requests.exceptions.RequestException as e: catches all

**Notes:**

<!-- TODO -->

### T11.06 · TLS warnings

**Must cover:**

- [ ] verify=False triggers InsecureRequestWarning on self-signed lab certs
- [ ] requests.packages.urllib3.disable_warnings() or urllib3.disable_warnings() hides it
- [ ] Acceptable in sandboxes only; real scripts should verify certificates

**Notes:**

<!-- TODO -->

### T11.07 · Patterns

**Must cover:**

- [ ] Auth then use: POST login → read token → GET with token header
- [ ] Pagination: loop while a next link/page exists
- [ ] Rate limits: if status_code == 429: time.sleep(int(resp.headers["Retry-After"])) then retry

**Notes:**

<!-- TODO -->

### T11.08 · Output

**Must cover:**

- [ ] print(json.dumps(data, indent=2)) to inspect structure
- [ ] Then extract fields: for d in data["response"]: print(d["hostname"])

**Notes:**

<!-- TODO -->

### T11.09 · Exam angle

**Must cover:**

- [ ] Complete-the-code: missing method, URL, header, argument or attribute
- [ ] Predict the output or the error of a short script
- [ ] Spot json= vs data= and .json() vs .text mistakes

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T11.1 | Lab | requests script: auth header, JSON body, raise_for_status, 429 retry | 30 | Docker lab |

- Skip / low priority: Writing long scripts

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
