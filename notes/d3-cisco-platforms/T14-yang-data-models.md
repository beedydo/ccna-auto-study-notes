---
id: T14
title: "YANG data models"
owner: Bob
blueprint: "3.8, 5.11"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-09
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T14 · YANG data models

> Owner: **Bob** · Blueprint: **3.8, 5.11** · CBT coverage: **Full** · Learn by 2026-10-09 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T14.01 · What YANG is

**Must cover:**

- [ ] Data modelling language (RFC 6020 / 7950) that defines the structure, types and constraints of config and operational data
- [ ] Describes data; does not contain it
- [ ] Protocol-independent: used by NETCONF, RESTCONF, gNMI

**Notes:**

<!-- TODO -->

### T14.02 · Model sources

**Must cover:**

- [ ] IETF standard models (e.g. ietf-interfaces)
- [ ] OpenConfig: vendor-neutral, operator-driven
- [ ] Native/vendor models (e.g. Cisco-IOS-XE-native)
- [ ] Found in the YangModels GitHub repo and YANG Catalog

**Notes:**

<!-- TODO -->

### T14.03 · Module header

**Must cover:**

- [ ] module name, namespace (unique URI), prefix, import, organization, revision

**Notes:**

<!-- TODO -->

### T14.04 · Node types

**Must cover:**

- [ ] container: groups related nodes (no value itself)
- [ ] list: repeated entries, each identified by a key leaf
- [ ] leaf: single value with a type
- [ ] leaf-list: list of values of one type

**Notes:**

<!-- TODO -->

### T14.05 · Reuse and types

**Must cover:**

- [ ] grouping + uses (reusable blocks); augment (add nodes into another model); typedef (custom type)
- [ ] Built-in types: string, int/uint8..64, boolean, enumeration, union, leafref, identityref

**Notes:**

<!-- TODO -->

### T14.06 · Config vs state

**Must cover:**

- [ ] config true = configuration data (read-write)
- [ ] config false = operational state (read-only), e.g. counters

**Notes:**

<!-- TODO -->

### T14.07 · pyang tree output

**Must cover:**

- [ ] pyang -f tree model.yang
- [ ] rw = config, ro = state; ? = optional; * = list or leaf-list; [name] = list key

**Notes:**

<!-- TODO -->

### T14.08 · Model to API path

**Must cover:**

- [ ] Module:container/list=key/leaf, e.g. /restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet1/description

**Notes:**

<!-- TODO -->

### T14.09 · Exam angle

**Must cover:**

- [ ] Read a YANG snippet or tree: identify node types, keys, config vs state; build the RESTCONF path

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
| T14.1 | Video | Data Models and YANG | 41 | CBT module |
| T14.2 | Lab | pyang tree: ietf-interfaces + a Cisco native model | 40 | Docker lab + YangModels repo |
| T14.3 | Drill | Read YANG snippets; pick the correct RESTCONF path | 30 | YangModels repo |

- Skip / low priority: Writing YANG

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
