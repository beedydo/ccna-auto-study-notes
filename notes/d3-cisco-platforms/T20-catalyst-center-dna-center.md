---
id: T20
title: "Catalyst Center (DNA Center)"
owner: Bob
blueprint: "3.1, 3.2, 3.9"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-14
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T20 · Catalyst Center (DNA Center)

> Owner: **Bob** · Blueprint: **3.1, 3.2, 3.9** · CBT coverage: **Full** · Learn by 2026-10-14 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T20.01 · What Catalyst Center is

**Must cover:**

- [ ] Formerly DNA Center: controller for campus/branch, intent-based networking
- [ ] Functions: design, policy, provision (automation), assurance (analytics)

**Notes:**

<!-- TODO -->

### T20.02 · API families

**Must cover:**

- [ ] Intent API: northbound REST for apps
- [ ] Integration API: ITSM (e.g. ServiceNow), IPAM
- [ ] Multivendor SDK: southbound to third-party devices
- [ ] Events and notifications: webhooks, email, syslog

**Notes:**

<!-- TODO -->

### T20.03 · Authentication

**Must cover:**

- [ ] POST /dna/system/api/v1/auth/token with HTTP basic auth → {"Token": "..."}
- [ ] Send the token in the X-Auth-Token header on every call

**Notes:**

<!-- TODO -->

### T20.04 · Common endpoints

**Must cover:**

- [ ] /dna/intent/api/v1/network-device (inventory)
- [ ] /site, /site-health, /client-health, /client-detail?macAddress=
- [ ] /topology/physical-topology; /network-device-poller/cli/read-request (command runner)

**Notes:**

<!-- TODO -->

### T20.05 · Asynchronous tasks

**Must cover:**

- [ ] Many POST/PUT calls return 202 with a taskId
- [ ] Poll GET /dna/intent/api/v1/task/{taskId} until finished; check isError and progress

**Notes:**

<!-- TODO -->

### T20.06 · Python SDK

**Must cover:**

- [ ] pip install dnacentersdk
- [ ] api = DNACenterAPI(base_url=..., username=..., password=..., verify=False)
- [ ] api.devices.get_device_list()

**Notes:**

<!-- TODO -->

### T20.07 · Client discovery (3.9.c)

**Must cover:**

- [ ] client-detail by MAC shows where a client connects (device, port, SSID) and its health

**Notes:**

<!-- TODO -->

### T20.08 · Exam angle

**Must cover:**

- [ ] Auth flow and header; async task polling; complete code calling the intent API

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
| T20.1 | Video | Automate the Campus with DNA Center Platform | 36 | CBT module |
| T20.2 | Video | Easier DNA Center Automation with the SDK | 19 | CBT module |

- Skip / low priority: SDK walkthrough

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
