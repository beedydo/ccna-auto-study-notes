---
id: T22
title: "Catalyst SD-WAN"
owner: Bob
blueprint: "3.2, 3.9.a"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-15
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T22 · Catalyst SD-WAN

> Owner: **Bob** · Blueprint: **3.2, 3.9.a** · CBT coverage: **Full** · Learn by 2026-10-15 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T22.01 · Components

**Must cover:**

- [ ] SD-WAN Manager (formerly vManage): management/NMS and API
- [ ] SD-WAN Controller (vSmart): control plane, OMP routing and policy
- [ ] SD-WAN Validator (vBond): orchestration, authenticates devices
- [ ] WAN Edge routers: data plane

**Notes:**

<!-- TODO -->

### T22.02 · API base

**Must cover:**

- [ ] REST API on SD-WAN Manager: https://<manager>:8443/dataservice/

**Notes:**

<!-- TODO -->

### T22.03 · Authentication

**Must cover:**

- [ ] POST /j_security_check with form data j_username and j_password → JSESSIONID cookie
- [ ] GET /dataservice/client/token → token sent as X-XSRF-TOKEN header on POST/PUT/DELETE
- [ ] requests.Session() keeps the cookie

**Notes:**

<!-- TODO -->

### T22.04 · Common endpoints

**Must cover:**

- [ ] /dataservice/device (inventory)
- [ ] /dataservice/device/monitor, /statistics, /alarms
- [ ] /dataservice/template/... (device/feature templates)

**Notes:**

<!-- TODO -->

### T22.05 · Exam angle

**Must cover:**

- [ ] Order the login steps; know the cookie + XSRF token; map component names old ↔ new

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
| T22.1 | Video | Automate WAN Workloads with SD-WAN | 20 | CBT module (vManage = SD-WAN Manager) |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
