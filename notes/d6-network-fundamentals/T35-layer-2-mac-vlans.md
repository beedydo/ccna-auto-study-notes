---
id: T35
title: "Layer 2: MAC, VLANs"
owner: Bob
blueprint: "6.1"
primary_domain: D6
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-23
---

# T35 · Layer 2: MAC, VLANs

> Owner: **Bob** · Blueprint: **6.1** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T35.01 · MAC addresses

**Must cover:**

- [ ] 48-bit, hex; first 24 bits = OUI (vendor)
- [ ] Unicast, multicast, broadcast (FF:FF:FF:FF:FF:FF)

**Notes:**

<!-- TODO -->

### T35.02 · Switching

**Must cover:**

- [ ] Learn source MAC → port; forward known unicast; flood broadcast/unknown unicast; filter same-port; MAC table aging

**Notes:**

<!-- TODO -->

### T35.03 · VLANs

**Must cover:**

- [ ] Separate L2 broadcast domain per VLAN
- [ ] Access port (one VLAN) vs trunk (many VLANs, 802.1Q tag, 12-bit VLAN ID 1-4094, native VLAN untagged)
- [ ] Inter-VLAN traffic needs L3 (SVI or router-on-a-stick)

**Notes:**

<!-- TODO -->

### T35.04 · Exam angle

**Must cover:**

- [ ] Purpose/usage questions; what a switch does with a frame

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
| T35.1 | Video | Describe How a Switch Performs Layer 2 Forwarding | 33 | CBT module |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
