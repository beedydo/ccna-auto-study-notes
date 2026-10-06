---
id: T37
title: "Transport, ports, IP services"
owner: Bob
blueprint: "6.6, 6.7"
primary_domain: D6
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-15
teach_back: 2026-10-16
cross_study: 2026-10-23
---

# T37 · Transport, ports, IP services

> Owner: **Bob** · Blueprint: **6.6, 6.7** · CBT coverage: **Full** · Learn by 2026-10-15 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T37.01 · TCP vs UDP

**Must cover:**

- [ ] TCP: connection-oriented, reliable, ordered (3-way handshake)
- [ ] UDP: connectionless, low overhead (DNS queries, SNMP, NTP, syslog)

**Notes:**

<!-- TODO -->

### T37.02 · Ports to memorise

**Must cover:**

- [ ] SSH 22, Telnet 23, HTTP 80, HTTPS 443, NETCONF 830, RESTCONF 443
- [ ] DNS 53, DHCP 67/68, TFTP 69, NTP 123, SNMP 161 / traps 162, syslog 514, SMTP 25, FTP 20/21

**Notes:**

<!-- TODO -->

### T37.03 · IP services

**Must cover:**

- [ ] DHCP: DORA (Discover, Offer, Request, Ack)
- [ ] DNS: A, AAAA, CNAME, PTR, MX records
- [ ] NAT/PAT: private ↔ public translation
- [ ] SNMP: manager/agent, MIB, OID, traps; v3 adds auth/encryption
- [ ] NTP: time sync, stratum levels

**Notes:**

<!-- TODO -->

### T37.04 · Exam angle

**Must cover:**

- [ ] Match port to protocol; pick the service for a scenario

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
| T37.1 | Video | Describe Transport Layer Functions and Protocols | 21 | CBT module |
| T37.2 | Video | Describe Application Layer Functions and Protocols | 38 | CBT module |
| T37.3 | Drill | Flashcards: port numbers | 20 | Own cheat sheet |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
