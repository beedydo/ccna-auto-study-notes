---
id: T10
title: "API authentication"
owner: Beedy
blueprint: "2.7"
primary_domain: D2
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-10
teach_back: 2026-10-12
cross_study: 2026-10-22
---

# T10 · API authentication

> Owner: **Beedy** · Blueprint: **2.7** · CBT coverage: **Full** · Learn by 2026-10-10 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T10.01 · Concepts

**Must cover:**

- [ ] Authentication = proving identity (who you are)
- [ ] Authorisation = permissions after login (what you may do)
- [ ] 401 relates to authentication; 403 to authorisation

**Notes:**

<!-- TODO -->

### T10.02 · Basic auth

**Must cover:**

- [ ] Header: Authorization: Basic <base64("user:password")>
- [ ] Base64 is encoding, not encryption → anyone can decode it
- [ ] Must be used over HTTPS
- [ ] Sent on every request (or once to obtain a token)
- [ ] Often used only to call the token endpoint (e.g. Catalyst Center)

**Notes:**

<!-- TODO -->

### T10.03 · Custom token

**Must cover:**

- [ ] Step 1: authenticate (often basic auth) to a login endpoint
- [ ] Step 2: receive a token in the body, header or cookie
- [ ] Step 3: send the token on each call in a custom or standard header
- [ ] Examples: X-Auth-Token (Catalyst Center), Authorization: Bearer <token> (Webex, FMC uses X-auth-access-token)
- [ ] Tokens expire → refresh or log in again

**Notes:**

<!-- TODO -->

### T10.04 · API key

**Must cover:**

- [ ] Long-lived static key generated in a portal, tied to a user/account
- [ ] Sent in a header (e.g. X-Cisco-Meraki-API-Key or Authorization: Bearer) or query string
- [ ] Simple, but full access if leaked → rotate and store securely
- [ ] Query-string keys can end up in logs (avoid)

**Notes:**

<!-- TODO -->

### T10.05 · Session/cookie

**Must cover:**

- [ ] Server returns Set-Cookie after login; client sends the cookie back
- [ ] APIC: aaaLogin returns a token, set as cookie APIC-cookie
- [ ] SD-WAN Manager: JSESSIONID cookie plus X-XSRF-TOKEN header
- [ ] requests.Session() keeps cookies automatically

**Notes:**

<!-- TODO -->

### T10.06 · OAuth 2.0 (awareness)

**Must cover:**

- [ ] Delegated access without sharing the password
- [ ] Access token (short-lived) + refresh token (to get new access tokens)
- [ ] Scopes limit what the token can do
- [ ] Webex integrations use OAuth; bots use a long-lived bot token

**Notes:**

<!-- TODO -->

### T10.07 · Python

**Must cover:**

- [ ] requests.get(url, auth=("user", "pass")) or auth=HTTPBasicAuth(user, pw) → basic auth
- [ ] headers={"X-Auth-Token": token} or {"Authorization": f"Bearer {token}"} → token/API key
- [ ] Session object: s.headers.update({...}) for all later calls

**Notes:**

<!-- TODO -->

### T10.08 · Credential handling

**Must cover:**

- [ ] Never hardcode secrets in scripts or commit them to Git
- [ ] Use environment variables (os.environ["API_KEY"]) or a secrets vault
- [ ] Use HTTPS so credentials are encrypted in transit

**Notes:**

<!-- TODO -->

### T10.09 · Exam angle

**Must cover:**

- [ ] Match a header/code snippet to basic, token or API key
- [ ] Know the method per platform: Meraki API key, Catalyst Center token, Webex bearer token, APIC cookie
- [ ] Know why base64 is not secure

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
| T10.1 | Video | Authentication with HTTP and REST | 27 | CBT module |

- Skip / low priority: Tool setup

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
