---
id: T30
title: "OWASP: XSS, SQLi, CSRF"
owner: Beedy
blueprint: "4.10"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-14
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T30 · OWASP: XSS, SQLi, CSRF

> Owner: **Beedy** · Blueprint: **4.10** · CBT coverage: **Full** · Learn by 2026-10-14 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T30.01 · OWASP

**Must cover:**

- [ ] Open Worldwide Application Security Project: community publishing the OWASP Top 10 web app risks
- [ ] Used as a baseline checklist for secure development

**Notes:**

<!-- TODO -->

### T30.02 · XSS

**Must cover:**

- [ ] Cross-Site Scripting: attacker gets malicious script to run in another user's browser
- [ ] Stored: script saved on the server (e.g. in a comment) and served to others
- [ ] Reflected: script in a URL/parameter echoed back in the response
- [ ] DOM-based: client-side JavaScript writes untrusted data into the page
- [ ] Impact: session theft, defacement, actions as the user

**Notes:**

<!-- TODO -->

### T30.03 · XSS defences

**Must cover:**

- [ ] Encode/escape output for its context (HTML, JS, URL)
- [ ] Validate input; use templating frameworks that auto-escape
- [ ] Content Security Policy header restricts script sources
- [ ] HttpOnly cookies limit token theft

**Notes:**

<!-- TODO -->

### T30.04 · SQL injection

**Must cover:**

- [ ] User input concatenated into a SQL statement changes its logic
- [ ] Example: username = ' OR 1=1 -- returns all rows / bypasses login
- [ ] Impact: data theft, modification, deletion

**Notes:**

<!-- TODO -->

### T30.05 · SQLi defences

**Must cover:**

- [ ] Parameterised queries / prepared statements (input treated as data, not code)
- [ ] ORM frameworks
- [ ] Input validation
- [ ] Least-privilege database accounts

**Notes:**

<!-- TODO -->

### T30.06 · CSRF

**Must cover:**

- [ ] Cross-Site Request Forgery: a malicious site makes the victim's browser send a request to a site where they are logged in
- [ ] Browser sends the session cookie automatically, so the request looks legitimate
- [ ] Impact: unwanted actions (change password, transfer funds)

**Notes:**

<!-- TODO -->

### T30.07 · CSRF defences

**Must cover:**

- [ ] Anti-CSRF tokens: unique token in each form, checked by the server
- [ ] SameSite cookie attribute
- [ ] Re-authentication or confirmation for sensitive actions
- [ ] Check Origin/Referer headers

**Notes:**

<!-- TODO -->

### T30.08 · Other Top 10 (awareness)

**Must cover:**

- [ ] Broken access control; cryptographic failures; injection (includes SQLi, XSS)
- [ ] Insecure design; security misconfiguration; vulnerable/outdated components
- [ ] Identification and authentication failures; integrity failures; logging/monitoring failures; SSRF

**Notes:**

<!-- TODO -->

### T30.09 · Exam angle

**Must cover:**

- [ ] Name the attack from a scenario or snippet
- [ ] Pick its mitigation (e.g. SQLi → parameterised queries; CSRF → tokens; XSS → output encoding)

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
| T30.1 | Video | Identify OWASP Standard Threats | 21 | CBT module |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
