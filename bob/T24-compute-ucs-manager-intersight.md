---
id: T24
title: "Compute: UCS Manager + Intersight"
owner: Bob
blueprint: "3.3"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-22
---

# T24 · Compute: UCS Manager + Intersight

> Owner: **Bob** · Blueprint: **3.3** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T24.01 · UCS and UCS Manager

**Must cover:**

- [ ] UCS = Cisco Unified Computing System: blade/rack servers + fabric interconnects
- [ ] UCS Manager runs on the fabric interconnects and manages one UCS domain

**Notes:**

<!-- TODO -->

### T24.02 · Service profiles

**Must cover:**

- [ ] Logical server identity: UUID, MAC, WWN, BIOS, firmware, boot order
- [ ] Applied to physical servers → stateless computing (move identity to new hardware)
- [ ] Built from pools, policies and templates

**Notes:**

<!-- TODO -->

### T24.03 · UCSM XML API

**Must cover:**

- [ ] Everything in UCSM is an MO in a Management Information Tree (DN-based, like ACI)
- [ ] XML API over HTTP(S) to /nuova; aaaLogin returns a cookie
- [ ] Query by class (computeBlade) or DN

**Notes:**

<!-- TODO -->

### T24.04 · UCSM Python SDK

**Must cover:**

- [ ] pip install ucsmsdk
- [ ] handle = UcsHandle(ip, user, pw); handle.login()
- [ ] handle.query_classid("computeBlade"); handle.logout()

**Notes:**

<!-- TODO -->

### T24.05 · Intersight

**Must cover:**

- [ ] SaaS (or on-prem appliance) management for UCS, HyperFlex and more, across many sites
- [ ] OpenAPI-based REST API; auth = API key ID + secret key used to sign each request (HTTP signature)
- [ ] Python SDK: intersight

**Notes:**

<!-- TODO -->

### T24.06 · UCSM vs Intersight

**Must cover:**

- [ ] UCSM: on-prem, per domain, XML API
- [ ] Intersight: cloud, multi-domain, OpenAPI with signed requests

**Notes:**

<!-- TODO -->

### T24.07 · Not tested

**Must cover:**

- [ ] UCS Director and UCS PowerTool (skip those videos)

**Notes:**

<!-- TODO -->

### T24.08 · Exam angle

**Must cover:**

- [ ] Pick UCSM vs Intersight; know service profile purpose and auth styles

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
| T24.1 | Video | UCS platform + UCSM SDK (skip PowerTool, UCS Director) | 14 | CBT: Automate Cisco Compute and More with UCS |
| T24.2 | Video | Cisco's Compute Solutions + Intersight's API | 14 | CBT: Understand Cisco Compute & Security Solutions |

- Skip / low priority: UCS Director, PowerTool

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
