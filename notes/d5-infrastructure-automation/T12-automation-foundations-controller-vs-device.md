---
id: T12
title: "Automation foundations: controller vs device"
owner: Bob
blueprint: "5.1, 5.2"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-05
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T12 · Automation foundations: controller vs device

> Owner: **Bob** · Blueprint: **5.1, 5.2** · CBT coverage: **Full** · Learn by 2026-10-05 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T12.01 · Why automate

**Must cover:**

- [ ] Scale: hundreds of devices changed consistently
- [ ] Speed, fewer human errors, repeatability, compliance and audit trail

**Notes:**

<!-- TODO -->

### T12.02 · Model-driven programmability

**Must cover:**

- [ ] Device config and state described by data models (YANG) instead of free-form CLI text
- [ ] Accessed through APIs (NETCONF, RESTCONF, gNMI) that return structured data (XML/JSON)
- [ ] Replaces CLI screen-scraping with parsing-free, schema-validated data

**Notes:**

<!-- TODO -->

### T12.03 · Value (5.1)

**Must cover:**

- [ ] Vendor-neutral models (OpenConfig, IETF) → same code across vendors
- [ ] Validation against the model before applying
- [ ] Transactions and rollback (NETCONF candidate/commit)
- [ ] Easier tooling, programmability and streaming telemetry

**Notes:**

<!-- TODO -->

### T12.04 · Programmability stack

**Must cover:**

- [ ] Data model: YANG
- [ ] Encoding: XML, JSON (protobuf for gRPC)
- [ ] Protocol: NETCONF, RESTCONF, gNMI/gRPC
- [ ] Transport: SSH (NETCONF), HTTPS (RESTCONF), HTTP/2 (gRPC)

**Notes:**

<!-- TODO -->

### T12.05 · Device-level management

**Must cover:**

- [ ] Script/tool talks to each device directly: SSH CLI, NETCONF, RESTCONF, NX-API
- [ ] Granular control, no controller dependency
- [ ] You handle scale, consistency and state across devices yourself

**Notes:**

<!-- TODO -->

### T12.06 · Controller-level management

**Must cover:**

- [ ] Central controller (Catalyst Center, APIC, SD-WAN Manager, Meraki dashboard) holds intent/policy and programs devices
- [ ] Northbound API: apps → controller (REST); southbound: controller → devices (NETCONF, OpenFlow, CLI, proprietary)
- [ ] Abstraction, network-wide view, policy-based; depends on the controller

**Notes:**

<!-- TODO -->

### T12.07 · SDN concepts

**Must cover:**

- [ ] SDN separates the control plane (centralised controller) from the data plane (devices)
- [ ] Intent-based networking: declare the outcome, controller translates it into config

**Notes:**

<!-- TODO -->

### T12.08 · Exam angle

**Must cover:**

- [ ] Compare controller vs device level for a scenario; state the value of model-driven programmability

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
| T12.1 | Video | Network Programmability & Automation Foundations | 56 | CBT module |
| T12.2 | Top-up | Notes: controller-level vs device-level management | 20 | Own notes |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
