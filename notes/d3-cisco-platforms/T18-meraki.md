---
id: T18
title: "Meraki"
owner: Bob
blueprint: "3.1, 3.2, 3.9"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-13
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T18 · Meraki

> Owner: **Bob** · Blueprint: **3.1, 3.2, 3.9** · CBT coverage: **Full** · Learn by 2026-10-13 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T18.01 · Platform

**Must cover:**

- [ ] Cloud-managed networking (MX security appliance, MS switch, MR wireless, MV camera)
- [ ] Managed in the Meraki dashboard; no on-prem controller

**Notes:**

<!-- TODO -->

### T18.02 · APIs

**Must cover:**

- [ ] Dashboard API: REST, base https://api.meraki.com/api/v1
- [ ] Scanning API: location data POSTed to your server (webhook-style)
- [ ] MV Sense: camera analytics (REST/MQTT)
- [ ] Webhooks for alerts; captive portal APIs (awareness)

**Notes:**

<!-- TODO -->

### T18.03 · Authentication

**Must cover:**

- [ ] API key generated in the dashboard user profile
- [ ] Header X-Cisco-Meraki-API-Key: <key> or Authorization: Bearer <key>

**Notes:**

<!-- TODO -->

### T18.04 · Hierarchy and endpoints

**Must cover:**

- [ ] organizations → networks → devices (by serial) → clients
- [ ] GET /organizations; /organizations/{orgId}/networks; /networks/{networkId}/devices; /networks/{networkId}/clients

**Notes:**

<!-- TODO -->

### T18.05 · Constraints

**Must cover:**

- [ ] Rate limit ~10 requests/second per organisation → 429 + Retry-After
- [ ] Pagination via Link header (rel=next) and startingAfter/perPage

**Notes:**

<!-- TODO -->

### T18.06 · Python SDK

**Must cover:**

- [ ] pip install meraki
- [ ] dashboard = meraki.DashboardAPI(api_key)
- [ ] dashboard.organizations.getOrganizations(); dashboard.networks.getNetworkClients(net_id)
- [ ] SDK handles retries on 429 and pagination

**Notes:**

<!-- TODO -->

### T18.07 · Client discovery (3.9.c)

**Must cover:**

- [ ] List clients per network/device; look up a client by MAC/IP to find where it is connected

**Notes:**

<!-- TODO -->

### T18.08 · Exam angle

**Must cover:**

- [ ] Order the calls org → network → device; complete SDK/requests code; know the auth header

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
| T18.1 | Video | Automate Cisco Meraki Networks | 26 | CBT module |
| T18.2 | Video | Automation with the Meraki Python SDK | 22 | CBT module |
| T18.3 | Lab | orgs > networks > devices > clients (requests + SDK) | 30 | Meraki sandbox / docs API key |

- Skip / low priority: Deep SDK walkthrough

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
