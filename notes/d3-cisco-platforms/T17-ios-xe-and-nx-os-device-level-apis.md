---
id: T17
title: "IOS XE and NX-OS device-level APIs"
owner: Bob
blueprint: "3.6"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-11
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T17 · IOS XE and NX-OS device-level APIs

> Owner: **Bob** · Blueprint: **3.6** · CBT coverage: **Full** · Learn by 2026-10-11 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T17.01 · IOS XE programmability

**Must cover:**

- [ ] NETCONF, RESTCONF, gNMI/gRPC over YANG models
- [ ] Model-driven telemetry (streaming)
- [ ] On-box Python (guestshell) and EEM (awareness)

**Notes:**

<!-- TODO -->

### T17.02 · NX-API CLI

**Must cover:**

- [ ] Send CLI commands over HTTP/HTTPS POST to /ins
- [ ] Formats: JSON, XML, JSON-RPC
- [ ] Command types: cli_show (structured output), cli_show_ascii (raw text), cli_conf (config)
- [ ] Enable with feature nxapi; NX-API sandbox in the browser generates request code

**Notes:**

<!-- TODO -->

### T17.03 · NX-API REST

**Must cover:**

- [ ] Object model (DME): Management Information Tree of managed objects with DNs, like ACI
- [ ] Login POST /api/aaaLogin.json → token cookie
- [ ] Read: GET /api/mo/<dn>.json (one object) or /api/class/<class>.json (all of a class)

**Notes:**

<!-- TODO -->

### T17.04 · Other NX-OS interfaces

**Must cover:**

- [ ] NETCONF, RESTCONF and gRPC/gNMI with YANG (native and OpenConfig)

**Notes:**

<!-- TODO -->

### T17.05 · Dynamic interfaces

**Must cover:**

- [ ] Model-driven telemetry: devices stream data (push) instead of SNMP polling (pull)
- [ ] Dial-in (collector subscribes) vs dial-out (device connects to collector)

**Notes:**

<!-- TODO -->

### T17.06 · Exam angle

**Must cover:**

- [ ] NX-API CLI vs NX-API REST; pick the interface/URL for a task

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
| T17.1 | Video | Nexus Programmability with NX-API CLI | 30 | CBT module |
| T17.2 | Video | Nexus Programmability with NX-API REST | 36 | CBT module |
| T17.3 | Video | Real-World Nexus Automation for Real-World Network Engineers (optional) | 28 | CBT module |

- Skip / low priority: Real-World Nexus video (optional)

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
