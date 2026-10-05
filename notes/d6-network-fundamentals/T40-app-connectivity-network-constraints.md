---
id: T40
title: "App connectivity + network constraints"
owner: Bob
blueprint: "6.8, 6.9"
primary_domain: D6
cbt_coverage: "Partial"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-19
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T40 · App connectivity + network constraints

> Owner: **Bob** · Blueprint: **6.8, 6.9** · CBT coverage: **Partial** · Learn by 2026-10-19 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T40.01 · NAT issues

**Must cover:**

- [ ] Private address not reachable from outside without static NAT/port forwarding
- [ ] Return traffic and logging show translated addresses

**Notes:**

<!-- TODO -->

### T40.02 · Port blocking

**Must cover:**

- [ ] Firewall/ACL blocking: timeout (dropped) vs connection refused (closed port)
- [ ] Test with nc -zv host port, curl -v, telnet host port

**Notes:**

<!-- TODO -->

### T40.03 · Proxy issues

**Must cover:**

- [ ] Corporate proxy required for outbound HTTP(S): set HTTP_PROXY/HTTPS_PROXY or requests proxies={}
- [ ] Proxy auth failures (407), TLS inspection breaking cert checks

**Notes:**

<!-- TODO -->

### T40.04 · VPN issues

**Must cover:**

- [ ] Split vs full tunnel routes; DNS resolution through the tunnel; MTU/fragmentation; overlapping subnets

**Notes:**

<!-- TODO -->

### T40.05 · Diagnostic tools

**Must cover:**

- [ ] ping, traceroute, nslookup/dig, curl -v, ss/netstat

**Notes:**

<!-- TODO -->

### T40.06 · Network constraints (6.9)

**Must cover:**

- [ ] Bandwidth, latency, jitter, packet loss and their effect on apps (timeouts, slow chatty APIs, poor voice/video)
- [ ] Mitigations: QoS, caching, fewer round trips, compression

**Notes:**

<!-- TODO -->

### T40.07 · Exam angle

**Must cover:**

- [ ] Diagnose the cause from symptoms; pick the fix

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
| T40.1 | Video | Describe Network Elements that Impact Applications | 23 | CBT module |
| T40.2 | Top-up | Diagnose NAT, blocked port, proxy, VPN issues | 30 | Own notes |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
