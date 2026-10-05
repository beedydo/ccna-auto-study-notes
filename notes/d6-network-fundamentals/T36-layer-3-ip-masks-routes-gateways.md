---
id: T36
title: "Layer 3: IP, masks, routes, gateways"
owner: Bob
blueprint: "6.2"
primary_domain: D6
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-23
---

# T36 · Layer 3: IP, masks, routes, gateways

> Owner: **Bob** · Blueprint: **6.2** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T36.01 · IPv4 addressing

**Must cover:**

- [ ] 32-bit dotted decimal; mask/prefix splits network vs host
- [ ] Network, broadcast, usable hosts = 2^h − 2
- [ ] RFC 1918 private ranges: 10/8, 172.16/12, 192.168/16

**Notes:**

<!-- TODO -->

### T36.02 · IPv6 (awareness)

**Must cover:**

- [ ] 128-bit hex; /64 subnets; link-local fe80::/10

**Notes:**

<!-- TODO -->

### T36.03 · Gateway and ARP

**Must cover:**

- [ ] Default gateway forwards off-subnet traffic
- [ ] ARP resolves IP → MAC on the local subnet

**Notes:**

<!-- TODO -->

### T36.04 · Routing table

**Must cover:**

- [ ] Connected, static, dynamic (OSPF, EIGRP, BGP) routes
- [ ] Longest prefix match wins; default route 0.0.0.0/0

**Notes:**

<!-- TODO -->

### T36.05 · Exam angle

**Must cover:**

- [ ] Subnet maths; same-subnet or not; which route is used

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
| T36.1 | Video | Describe How a Router Performs Layer 3 Forwarding | 35 | CBT module |
| T36.2 | Drill | Subnetting drills | 40 | Own / online drills |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
