---
id: T41
title: "Firewall, DNS, LB, reverse proxy"
owner: Bob
blueprint: "4.9"
primary_domain: D4
cbt_coverage: "None"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-19
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T41 · Firewall, DNS, LB, reverse proxy

> Owner: **Bob** · Blueprint: **4.9** · CBT coverage: **None** · Learn by 2026-10-19 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T41.01 · Firewall

**Must cover:**

- [ ] Permit/deny by IP, port, protocol, application; stateful
- [ ] Segments tiers (web / app / DB); WAF protects HTTP apps (XSS, SQLi)

**Notes:**

<!-- TODO -->

### T41.02 · DNS

**Must cover:**

- [ ] Resolves app names to IPs; enables failover and simple load distribution (round robin, GSLB); TTL affects how fast changes propagate

**Notes:**

<!-- TODO -->

### T41.03 · Load balancer

**Must cover:**

- [ ] Clients hit a virtual IP (VIP); LB spreads requests across backend servers
- [ ] Algorithms: round robin, least connections, weighted
- [ ] Health checks remove failed servers; L4 (TCP/UDP) vs L7 (HTTP-aware)
- [ ] SSL/TLS offload; session persistence (sticky sessions)

**Notes:**

<!-- TODO -->

### T41.04 · Reverse proxy

**Must cover:**

- [ ] Sits in front of servers and forwards client requests to them
- [ ] TLS termination, caching, compression, path-based routing, hides backend servers
- [ ] Forward proxy (clients → internet) vs reverse proxy (internet → servers)

**Notes:**

<!-- TODO -->

### T41.05 · Typical flow

**Must cover:**

- [ ] Client → DNS → firewall/WAF → load balancer / reverse proxy → app servers → database

**Notes:**

<!-- TODO -->

### T41.06 · Exam angle

**Must cover:**

- [ ] Pick which component solves a scenario (scale out, hide servers, block ports, name resolution)

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
| T41.1 | Top-up | Map AWS ALB/NLB/Route 53/WAF to Cisco wording | 30 | Own notes |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
