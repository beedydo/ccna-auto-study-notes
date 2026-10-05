---
id: T25
title: "NSO + Cisco Modeling Labs"
owner: Bob
blueprint: "3.2, 5.3, 5.6"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-22
---

# T25 · NSO + Cisco Modeling Labs

> Owner: **Bob** · Blueprint: **3.2, 5.3, 5.6** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T25.01 · What NSO is

**Must cover:**

- [ ] Network Services Orchestrator: model-driven orchestration across multivendor networks

**Notes:**

<!-- TODO -->

### T25.02 · Architecture

**Must cover:**

- [ ] Service models (YANG) + templates/Python map a service to device config
- [ ] NEDs (Network Element Drivers) translate to each device (CLI, NETCONF, SNMP)
- [ ] CDB (configuration database) holds the network config
- [ ] Northbound interfaces: CLI, web UI, REST/RESTCONF, NETCONF, JSON-RPC

**Notes:**

<!-- TODO -->

### T25.03 · Transactions

**Must cover:**

- [ ] Changes commit as one transaction across many devices; all-or-nothing with rollback
- [ ] commit dry-run previews device changes
- [ ] FASTMAP: tracks what a service created so it can update/remove it cleanly

**Notes:**

<!-- TODO -->

### T25.04 · Sync

**Must cover:**

- [ ] devices sync-from (pull device config into CDB), sync-to (push CDB to device), check-sync

**Notes:**

<!-- TODO -->

### T25.05 · CML

**Must cover:**

- [ ] Cisco Modeling Labs: simulate networks with virtual Cisco images (IOSv, Catalyst 8000v, NX-OSv, IOS XRv)
- [ ] Topology defined in YAML; REST API and Python client (virl2_client)
- [ ] Used to test changes in CI pipelines before production

**Notes:**

<!-- TODO -->

### T25.06 · Tool choice

**Must cover:**

- [ ] NSO vs Ansible vs Terraform (shared with Beedy T33): NSO = transactional, model-driven, multivendor services

**Notes:**

<!-- TODO -->

### T25.07 · Not tested

**Must cover:**

- [ ] Terraform segment of the CML video

**Notes:**

<!-- TODO -->

### T25.08 · Exam angle

**Must cover:**

- [ ] Capabilities of NSO and CML; when to use each

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
| T25.1 | Video | Automate Everything with NSO | 29 | CBT module |
| T25.2 | Video | CML + NSO in Action (skip Terraform) | 20 | CBT: Understand Network Simulation, NSO & Terraform |

- Skip / low priority: Terraform part

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
