---
id: T43
title: "Webhooks"
owner: Beedy
blueprint: "2.2"
primary_domain: D2
cbt_coverage: "None"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-18
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T43 · Webhooks

> Owner: **Beedy** · Blueprint: **2.2** · CBT coverage: **None** · Learn by 2026-10-18 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T43.01 · Concept

**Must cover:**

- [ ] Webhook = HTTP callback: when an event happens, the service sends an HTTP POST to a URL you registered
- [ ] "Reverse API": the server calls you
- [ ] Event-driven, near real time

**Notes:**

<!-- TODO -->

### T43.02 · Comparison

**Must cover:**

- [ ] Polling: client repeatedly asks "anything new?" → wasted calls, delay, rate-limit risk
- [ ] Webhook: server pushes only when something happens
- [ ] WebSocket: persistent two-way connection (awareness)

**Notes:**

<!-- TODO -->

### T43.03 · Components

**Must cover:**

- [ ] Event source (e.g. Webex, Meraki, Catalyst Center)
- [ ] Target URL: a publicly reachable HTTPS endpoint you host
- [ ] Receiver app: parses the payload and acts

**Notes:**

<!-- TODO -->

### T43.04 · Registration

**Must cover:**

- [ ] Register via API (Webex POST /v1/webhooks)
- [ ] name, targetUrl, resource (messages, rooms, memberships…), event (created, updated, deleted…)
- [ ] Optional filter (e.g. roomId=…) and secret

**Notes:**

<!-- TODO -->

### T43.05 · Payload

**Must cover:**

- [ ] Service sends a JSON POST describing the event
- [ ] Often minimal (IDs only, e.g. message ID) for security
- [ ] Receiver makes a follow-up GET to fetch full details (e.g. GET /messages/{id})
- [ ] Receiver should reply quickly with 2xx

**Notes:**

<!-- TODO -->

### T43.06 · Security

**Must cover:**

- [ ] Set a secret at registration; service signs each payload with HMAC (Webex: X-Spark-Signature header)
- [ ] Receiver recomputes the HMAC to verify origin and integrity
- [ ] Use HTTPS; validate and sanitise payloads

**Notes:**

<!-- TODO -->

### T43.07 · Testing tools

**Must cover:**

- [ ] ngrok: exposes a local app on a public URL for testing
- [ ] webhook.site / RequestBin: inspect payloads without writing code

**Notes:**

<!-- TODO -->

### T43.08 · Use cases

**Must cover:**

- [ ] Webex bots reacting to messages
- [ ] Meraki alerts to a ticketing/chat system
- [ ] Catalyst Center event notifications
- [ ] CI pipelines triggered by Git pushes

**Notes:**

<!-- TODO -->

### T43.09 · Exam angle

**Must cover:**

- [ ] Identify a webhook pattern in a scenario
- [ ] Explain why the target must be reachable and why a follow-up GET is needed
- [ ] Webhook vs polling trade-offs

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
| T43.1 | Top-up | Register a Webex webhook via curl; inspect payload | 45 | Webex developer docs: Webhooks |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
