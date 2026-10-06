---
id: T09
title: "API styles: REST vs RPC, sync vs async"
owner: Beedy
blueprint: "2.8"
primary_domain: D2
cbt_coverage: "Partial"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-10
teach_back: 2026-10-12
cross_study: 2026-10-22
---

# T09 · API styles: REST vs RPC, sync vs async

> Owner: **Beedy** · Blueprint: **2.8** · CBT coverage: **Partial** · Learn by 2026-10-10 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T09.01 · REST

**Must cover:**

- [ ] Resources are nouns in the URI (/devices/1); actions are HTTP methods
- [ ] Stateless, cacheable, usually JSON over HTTP
- [ ] Examples: Meraki, Catalyst Center, Webex, RESTCONF

**Notes:**

<!-- TODO -->

### T09.02 · RPC

**Must cover:**

- [ ] RPC = Remote Procedure Call: the client calls a named function on the server
- [ ] Action is in the payload or URL (e.g. "method": "getDevice")
- [ ] Usually POST to a single endpoint
- [ ] Examples: JSON-RPC, XML-RPC, gRPC (HTTP/2 + protobuf), NX-API CLI (JSON-RPC option)
- [ ] NETCONF is RPC-based: <rpc><get-config>…</get-config></rpc>

**Notes:**

<!-- TODO -->

### T09.03 · SOAP

**Must cover:**

- [ ] SOAP = Simple Object Access Protocol, XML only
- [ ] Message = Envelope > optional Header > Body (> Fault on errors)
- [ ] WSDL describes the operations and types (strict contract)
- [ ] Typically HTTP POST; Cisco AXL (CUCM) is SOAP

**Notes:**

<!-- TODO -->

### T09.04 · Comparison

**Must cover:**

- [ ] REST: resource-centric, flexible formats, light
- [ ] RPC: action-centric, simple to map to functions
- [ ] SOAP: strict contract, heavier XML, built-in standards (WS-Security)
- [ ] Recognise the style from a payload: <soap:Envelope> = SOAP; {"jsonrpc": "2.0", "method": …} = JSON-RPC; GET /resources/123 = REST

**Notes:**

<!-- TODO -->

### T09.05 · Synchronous

**Must cover:**

- [ ] Client sends a request and blocks until the full response arrives
- [ ] Simple to code and reason about
- [ ] Problem for long jobs: timeouts, client tied up

**Notes:**

<!-- TODO -->

### T09.06 · Asynchronous

**Must cover:**

- [ ] Server accepts the job and replies at once, typically 202 Accepted with a task ID or status URL
- [ ] Client gets the result later by polling the status URL or via a callback/webhook
- [ ] Client is free to do other work meanwhile
- [ ] Asynchronous code in Python: asyncio (awareness)

**Notes:**

<!-- TODO -->

### T09.07 · Async example

**Must cover:**

- [ ] POST/PUT to an intent API → response contains taskId (and URL)
- [ ] GET /dna/intent/api/v1/task/{taskId} until endTime is set / isError is false
- [ ] Then GET the result (e.g. fileId or progress field)
- [ ] Same pattern shows in sequence-diagram questions (T47)

**Notes:**

<!-- TODO -->

### T09.08 · Choosing

**Must cover:**

- [ ] Synchronous: quick lookups, small changes
- [ ] Asynchronous: long-running jobs (provisioning, image upgrades), large scale, avoiding HTTP timeouts

**Notes:**

<!-- TODO -->

### T09.09 · Exam angle

**Must cover:**

- [ ] Identify the API style from a snippet
- [ ] Explain why a call returned 202 and what to do next
- [ ] Match REST/RPC/SOAP to example Cisco APIs

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
| T09.1 | Top-up | Async taskId polling pattern | 30 | Catalyst Center API docs (task API) |
| T09.2 | Top-up | REST vs RPC (JSON-RPC / NETCONF RPC examples) | 20 | NSO docs; own notes |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
