---
id: T45
title: "Reading Python scripts using Cisco APIs"
owner: Bob
blueprint: "5.7"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-18
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T45 · Reading Python scripts using Cisco APIs

> Owner: **Bob** · Blueprint: **5.7** · CBT coverage: **Full** · Learn by 2026-10-18 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T45.01 · Typical script structure

**Must cover:**

- [ ] Imports → constants (base URL, credentials from env) → auth function → API call functions → parse/loop → output

**Notes:**

<!-- TODO -->

### T45.02 · Recognise the platform

**Must cover:**

- [ ] api.meraki.com → Meraki; /dna/ → Catalyst Center; /api/aaaLogin → ACI/NX-API; /dataservice → SD-WAN; webexapis.com → Webex; /restconf/data → RESTCONF; ncclient → NETCONF

**Notes:**

<!-- TODO -->

### T45.03 · Read the workflow

**Must cover:**

- [ ] Which call happens first (auth), what data is extracted, what the loop does, what gets printed or changed

**Notes:**

<!-- TODO -->

### T45.04 · Spot bugs

**Must cover:**

- [ ] Wrong HTTP method, missing auth/content headers, wrong JSON key path, missing raise_for_status, no pagination

**Notes:**

<!-- TODO -->

### T45.05 · Exam angle

**Must cover:**

- [ ] "What does this script do?" and put-the-steps-in-order questions

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
| T45.1 | Drill | Identify the workflow of Cisco API scripts | 40 | CBT supplemental files + DevNet Code Exchange |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
