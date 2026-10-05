---
id: T19
title: "ACI"
owner: Bob
blueprint: "3.1, 3.2, 3.9.a"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-13
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T19 · ACI

> Owner: **Bob** · Blueprint: **3.1, 3.2, 3.9.a** · CBT coverage: **Full** · Learn by 2026-10-13 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T19.01 · What ACI is

**Must cover:**

- [ ] Cisco SDN for the data centre: APIC controller cluster + Nexus 9000 spine-leaf fabric
- [ ] Policy model: define application intent, APIC programs the fabric

**Notes:**

<!-- TODO -->

### T19.02 · Object model

**Must cover:**

- [ ] Management Information Tree (MIT): every element is a managed object (MO) with a class and a distinguished name (DN)
- [ ] Example DN: uni/tn-Prod/ap-Web/epg-Frontend

**Notes:**

<!-- TODO -->

### T19.03 · Logical constructs

**Must cover:**

- [ ] Tenant → VRF (context) → bridge domain (L2) → subnets
- [ ] Application profile → EPGs (endpoint groups)
- [ ] Contracts (with filters) permit traffic between EPGs

**Notes:**

<!-- TODO -->

### T19.04 · REST API login

**Must cover:**

- [ ] POST https://<apic>/api/aaaLogin.json
- [ ] Body: {"aaaUser": {"attributes": {"name": "...", "pwd": "..."}}}
- [ ] Returns a token, also set as the APIC-cookie for later calls

**Notes:**

<!-- TODO -->

### T19.05 · Queries

**Must cover:**

- [ ] GET /api/mo/<dn>.json: one object (and children with query-target=children/subtree)
- [ ] GET /api/class/<class>.json: all objects of a class, e.g. fabricNode, fvTenant
- [ ] Filters: query-target-filter, rsp-subtree

**Notes:**

<!-- TODO -->

### T19.06 · Tools

**Must cover:**

- [ ] API Inspector (shows API calls behind GUI actions); Visore (object browser)
- [ ] Cobra SDK (acicobra/acimodel); ACI Toolkit (lower priority)
- [ ] Ansible and Terraform providers for ACI

**Notes:**

<!-- TODO -->

### T19.07 · Exam angle

**Must cover:**

- [ ] Build the login or class query; map tenant/EPG/contract terms; complete Python requests code

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
| T19.1 | Video | Automate the Data Center with ACI | 43 | CBT module |
| T19.2 | Video | Easier ACI Automation with the Toolkit (optional) | 24 | CBT module |
| T19.3 | Lab | APIC aaaLogin + class query (fabricNode) via curl | 40 | DevNet always-on APIC sandbox |

- Skip / low priority: ACI Toolkit detail

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
