---
id: T47
title: "Sequence diagrams with API calls"
owner: Beedy
blueprint: "5.14"
primary_domain: D5
cbt_coverage: "None"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-19
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T47 · Sequence diagrams with API calls

> Owner: **Beedy** · Blueprint: **5.14** · CBT coverage: **None** · Learn by 2026-10-19 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T47.01 · Notation

**Must cover:**

- [ ] Participants (boxes) with vertical lifelines
- [ ] Time flows from top to bottom
- [ ] Solid arrow = request/call (often labelled with method + URL)
- [ ] Dashed arrow = response (often labelled with status code/data)

**Notes:**

<!-- TODO -->

### T47.02 · Notation

**Must cover:**

- [ ] Activation bar = participant busy processing
- [ ] Frames: alt (if/else), opt (optional), loop (repeat), par (parallel)

**Notes:**

<!-- TODO -->

### T47.03 · Auth flow

**Must cover:**

- [ ] Client → auth endpoint: POST credentials
- [ ] Auth → client: 200 + token
- [ ] Client → API: GET/POST with token header
- [ ] API → client: 200 + data (401 if token missing/expired)

**Notes:**

<!-- TODO -->

### T47.04 · Async flow

**Must cover:**

- [ ] Client → API: POST job
- [ ] API → client: 202 Accepted + taskId
- [ ] loop: Client → API: GET /task/{taskId} until complete
- [ ] Client → API: GET result

**Notes:**

<!-- TODO -->

### T47.05 · Webhook flow

**Must cover:**

- [ ] App → service: register webhook (POST /webhooks)
- [ ] Event occurs → service POSTs payload to the app's targetUrl
- [ ] App → service: GET full details using the IDs in the payload

**Notes:**

<!-- TODO -->

### T47.06 · Reading

**Must cover:**

- [ ] Map each arrow to an HTTP method, URL and expected status code
- [ ] Spot the missing or out-of-order step (e.g. call before auth)

**Notes:**

<!-- TODO -->

### T47.07 · Exam angle

**Must cover:**

- [ ] Order the calls in a flow
- [ ] Say what happens or what is returned at a given arrow

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
| T47.1 | Top-up | Read token-auth + async-poll sequence diagrams | 30 | Catalyst Center / Webex docs |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
