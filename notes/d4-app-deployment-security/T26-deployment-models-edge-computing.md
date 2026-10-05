---
id: T26
title: "Deployment models + edge computing"
owner: Beedy
blueprint: "4.1-4.3"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-13
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T26 · Deployment models + edge computing

> Owner: **Beedy** · Blueprint: **4.1-4.3** · CBT coverage: **Full** · Learn by 2026-10-13 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T26.01 · Cloud models

**Must cover:**

- [ ] Private cloud: dedicated to one organisation (on-prem or hosted); most control, highest cost
- [ ] Public cloud: shared provider infrastructure (AWS, Azure, GCP); pay-as-you-go, elastic
- [ ] Hybrid cloud: private + public connected, workloads move between them
- [ ] Community cloud: shared by organisations with common needs (e.g. government)
- [ ] Multi-cloud: several public providers, avoids lock-in

**Notes:**

<!-- TODO -->

### T26.02 · Service models

**Must cover:**

- [ ] IaaS: provider runs hardware/virtualisation; you manage OS, runtime, apps (EC2)
- [ ] PaaS: provider also runs OS/runtime; you deploy code (Elastic Beanstalk, App Engine)
- [ ] SaaS: complete application delivered to users (Webex, Microsoft 365)

**Notes:**

<!-- TODO -->

### T26.03 · Cloud traits

**Must cover:**

- [ ] On-demand self-service
- [ ] Broad network access
- [ ] Resource pooling (multi-tenant)
- [ ] Rapid elasticity (scale up/down)
- [ ] Measured service (pay per use)

**Notes:**

<!-- TODO -->

### T26.04 · Edge computing

**Must cover:**

- [ ] Processing happens close to where data is produced (branch, factory, IoT device) instead of a central DC/cloud
- [ ] Benefits: lower latency, less WAN bandwidth, keeps working if the WAN fails, data stays local (privacy/sovereignty)
- [ ] Fog computing: layer between edge devices and cloud
- [ ] Cisco example: apps hosted on routers/switches (IOx)

**Notes:**

<!-- TODO -->

### T26.05 · Deployment types

**Must cover:**

- [ ] Bare metal: OS directly on hardware; best performance, slow to provision, low density
- [ ] VM: hypervisor runs multiple guest OSes; Type 1 (bare-metal: ESXi, KVM) vs Type 2 (hosted: VirtualBox)
- [ ] Container: isolated process sharing the host kernel; packages app + dependencies

**Notes:**

<!-- TODO -->

### T26.06 · Comparison

**Must cover:**

- [ ] Isolation: bare metal > VM > container
- [ ] Overhead/start-up: container (seconds) < VM (minutes) < bare metal
- [ ] Density: containers highest
- [ ] Portability: containers run the same anywhere with a container runtime

**Notes:**

<!-- TODO -->

### T26.07 · Other types

**Must cover:**

- [ ] Serverless/FaaS: run functions on events, provider manages servers, pay per execution (Lambda)

**Notes:**

<!-- TODO -->

### T26.08 · App architecture

**Must cover:**

- [ ] Monolith: one deployable unit; simple at first, hard to scale parts independently
- [ ] Microservices: small services communicating over APIs; independent deploy/scale, more complexity

**Notes:**

<!-- TODO -->

### T26.09 · Exam angle

**Must cover:**

- [ ] Scenario: "low latency for IoT sensors" → edge
- [ ] "Sensitive data must stay on-prem" → private/hybrid
- [ ] "Fast start-up, many instances" → containers

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
| T26.1 | Video | Computing and Application Deployment Models (1.5x) | 31 | CBT module |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
