---
id: T33
title: "IaC + tool comparison"
owner: Beedy
blueprint: "5.5, 5.6"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T33 · IaC + tool comparison

> Owner: **Beedy** · Blueprint: **5.5, 5.6** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T33.01 · IaC principles

**Must cover:**

- [ ] Infrastructure defined in machine-readable files instead of manual changes
- [ ] Stored in version control: history, review, rollback
- [ ] Repeatable and consistent across environments
- [ ] Enables CI/CD for infrastructure

**Notes:**

<!-- TODO -->

### T33.02 · Models

**Must cover:**

- [ ] Declarative: describe the desired end state; the tool works out the steps (Terraform, NSO, Puppet)
- [ ] Imperative/procedural: describe the steps in order (shell scripts; Ansible tasks run in order)

**Notes:**

<!-- TODO -->

### T33.03 · Properties

**Must cover:**

- [ ] Idempotency: running again with no changes makes no changes
- [ ] Configuration drift: real state diverging from the defined state
- [ ] Mutable infra: change servers in place; immutable: replace with new instances

**Notes:**

<!-- TODO -->

### T33.04 · Architectures

**Must cover:**

- [ ] Push: central server pushes changes (Ansible)
- [ ] Pull: agents on nodes fetch config (Puppet, Chef)
- [ ] Agentless (SSH/API) vs agent-based (software on each node)

**Notes:**

<!-- TODO -->

### T33.05 · Ansible

**Must cover:**

- [ ] Agentless, push model, uses SSH / NETCONF / HTTP APIs
- [ ] YAML playbooks of tasks using modules
- [ ] Strong for configuration management and orchestration across many devices

**Notes:**

<!-- TODO -->

### T33.06 · Terraform

**Must cover:**

- [ ] HashiCorp, declarative HCL
- [ ] Providers talk to platform APIs (AWS, ACI, Meraki, IOS XE)
- [ ] State file tracks what it manages; terraform plan (preview) → apply → destroy
- [ ] Strong for provisioning resources

**Notes:**

<!-- TODO -->

### T33.07 · NSO

**Must cover:**

- [ ] Cisco Network Services Orchestrator: model-driven (YANG) service orchestration
- [ ] NEDs (Network Element Drivers) talk to multivendor devices
- [ ] CDB stores config; changes are transactional across devices with rollback
- [ ] Northbound APIs: REST, RESTCONF, NETCONF, CLI

**Notes:**

<!-- TODO -->

### T33.08 · Puppet/Chef (awareness)

**Must cover:**

- [ ] Puppet: agent-based, pull, declarative manifests
- [ ] Chef: agent-based, pull, Ruby "recipes"

**Notes:**

<!-- TODO -->

### T33.09 · Exam angle

**Must cover:**

- [ ] Pick the tool for a scenario (multivendor service transactions → NSO; cloud provisioning with state → Terraform; agentless config push → Ansible)
- [ ] Declarative vs imperative and push vs pull definitions

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
| T33.1 | Top-up | One-line differentiator per tool | 15 | Own notes |

- Skip / low priority: Whole video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
