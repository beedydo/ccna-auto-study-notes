---
id: T23
title: "Security platforms"
owner: Bob
blueprint: "3.5"
primary_domain: D3
cbt_coverage: "Partial"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-22
---

# T23 · Security platforms

> Owner: **Bob** · Blueprint: **3.5** · CBT coverage: **Partial** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T23.01 · Secure Firewall Management Center (FMC)

**Must cover:**

- [ ] Central manager for Firepower/Secure Firewall devices
- [ ] Token: POST /api/fmc_platform/v1/auth/generatetoken with basic auth → X-auth-access-token and X-auth-refresh-token response headers + DOMAIN_UUID
- [ ] Config calls: /api/fmc_config/v1/domain/{domainUUID}/object/..., /policy/accesspolicies/...
- [ ] Token sent in the X-auth-access-token header

**Notes:**

<!-- TODO -->

### T23.02 · FDM (awareness)

**Must cover:**

- [ ] Firepower Device Manager: on-box manager for a single firewall, with its own REST API (OAuth-style tokens)

**Notes:**

<!-- TODO -->

### T23.03 · ISE

**Must cover:**

- [ ] Identity Services Engine: AAA, network access control, posture, guest
- [ ] ERS API (REST, HTTPS port 9060, basic auth) for endpoints, identity groups, network devices: /ers/config/...
- [ ] pxGrid shares context (user, device, posture) with other systems; newer OpenAPI

**Notes:**

<!-- TODO -->

### T23.04 · XDR

**Must cover:**

- [ ] Extended detection and response: correlates telemetry from endpoint, network, email and cloud
- [ ] APIs (OAuth client credentials) to enrich observables and respond (e.g. block, isolate)

**Notes:**

<!-- TODO -->

### T23.05 · Secure Endpoint

**Must cover:**

- [ ] Formerly AMP for Endpoints: endpoint malware protection, EDR
- [ ] API with client ID + API key (basic auth): list computers, events, isolate endpoints

**Notes:**

<!-- TODO -->

### T23.06 · Secure Malware Analytics

**Must cover:**

- [ ] Formerly Threat Grid: sandbox that detonates files/URLs and reports behaviour
- [ ] API key: submit samples, get analysis reports and threat scores

**Notes:**

<!-- TODO -->

### T23.07 · Secure Connect

**Must cover:**

- [ ] Cisco SASE/SSE cloud security service (built on Umbrella and Meraki): secure remote access, DNS-layer and web security
- [ ] APIs use key/secret to get an OAuth token

**Notes:**

<!-- TODO -->

### T23.08 · Exam angle

**Must cover:**

- [ ] Match platform → capability (e.g. sandboxing → Malware Analytics; NAC → ISE; firewall policy → FMC)

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
| T23.1 | Video | Automate the Cisco Security Platform (FMC) | 21 | CBT module |
| T23.2 | Video | Create Access Policies in FMC with Python | 17 | CBT module |
| T23.3 | Video | Security Solutions, FDM REST API, ISE REST API | 43 | CBT: Understand Cisco Compute & Security Solutions |
| T23.4 | Top-up | XDR, Secure Endpoint, Secure Connect, Secure Malware Analytics: 1-liner each | 50 | developer.cisco.com product API pages |

- Skip / low priority: ASA video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
