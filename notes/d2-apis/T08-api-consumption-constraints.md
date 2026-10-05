---
id: T08
title: "API consumption constraints"
owner: Beedy
blueprint: "2.3"
primary_domain: D2
cbt_coverage: "None"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-09
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T08 · API consumption constraints

> Owner: **Beedy** · Blueprint: **2.3** · CBT coverage: **None** · Learn by 2026-10-09 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T08.01 · Rate limiting

**Must cover:**

- [ ] Rate limit = max requests per time window (e.g. per second per org/key)
- [ ] Exceeding it returns 429 Too Many Requests
- [ ] Retry-After header: seconds (or a date) to wait before retrying
- [ ] Some APIs expose X-RateLimit-Limit / -Remaining / -Reset headers

**Notes:**

<!-- TODO -->

### T08.02 · Rate limiting

**Must cover:**

- [ ] On 429: sleep for Retry-After, then retry
- [ ] Exponential backoff: wait 1s, 2s, 4s… with a cap
- [ ] Reduce calls: cache results, batch requests, use webhooks instead of polling
- [ ] Spread work across time rather than bursts

**Notes:**

<!-- TODO -->

### T08.03 · Pagination

**Must cover:**

- [ ] APIs return large collections in pages to limit load
- [ ] Offset/limit: ?offset=100&limit=50
- [ ] Page number: ?page=3&per_page=50
- [ ] Cursor/token: response gives a next token (startingAfter in Meraki)
- [ ] Link header with rel="next" gives the next page URL (Meraki)
- [ ] Script bug pattern: only the first page is read → records "missing"

**Notes:**

<!-- TODO -->

### T08.04 · Payload limits

**Must cover:**

- [ ] Servers cap request body size and items per call
- [ ] 413 Payload Too Large when a body is too big
- [ ] Split large updates into several smaller requests

**Notes:**

<!-- TODO -->

### T08.05 · Timeouts

**Must cover:**

- [ ] Client timeout: requests.get(url, timeout=10) avoids hanging forever
- [ ] Server/gateway timeouts show up as 504
- [ ] Long-running jobs are often returned as async tasks (202) instead

**Notes:**

<!-- TODO -->

### T08.06 · Auth limits

**Must cover:**

- [ ] Tokens expire (e.g. after a set number of minutes)
- [ ] 401 mid-script often means an expired token → log in again
- [ ] Some APIs issue refresh tokens

**Notes:**

<!-- TODO -->

### T08.07 · Versioning

**Must cover:**

- [ ] APIs are versioned in the URL (/v1/) or a header
- [ ] Old versions get deprecated and removed
- [ ] Scripts must be updated to new versions/fields

**Notes:**

<!-- TODO -->

### T08.08 · Caching

**Must cover:**

- [ ] Server sends ETag (version tag) with a resource
- [ ] Client sends If-None-Match: <etag> on the next GET
- [ ] 304 Not Modified = nothing changed, no body, saves bandwidth and quota

**Notes:**

<!-- TODO -->

### T08.09 · Exam angle

**Must cover:**

- [ ] Pick the cause and fix for 429 errors or incomplete results
- [ ] Know the headers involved: Retry-After, Link, ETag

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
| T08.1 | Top-up | 429 + Retry-After, pagination, payload limits | 15 | Meraki Dashboard API docs |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
