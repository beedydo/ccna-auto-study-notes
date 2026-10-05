---
id: T21
title: "Collaboration: CUCM AXL + UDS"
owner: Bob
blueprint: "3.4"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-14
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T21 · Collaboration: CUCM AXL + UDS

> Owner: **Bob** · Blueprint: **3.4** · CBT coverage: **Full** · Learn by 2026-10-14 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T21.01 · CUCM

**Must cover:**

- [ ] Cisco Unified Communications Manager: call control for IP phones and UC

**Notes:**

<!-- TODO -->

### T21.02 · AXL

**Must cover:**

- [ ] Administrative XML: SOAP/XML API for provisioning and configuration
- [ ] Add/update/list phones, users, lines (e.g. addPhone, getUser, listPhone, executeSQLQuery)
- [ ] Defined by a WSDL; HTTPS POST to https://<cucm>:8443/axl/; needs an application user with the AXL role

**Notes:**

<!-- TODO -->

### T21.03 · UDS

**Must cover:**

- [ ] User Data Services: REST API (XML responses) for end-user and directory data
- [ ] Read-mostly, user-level tasks (e.g. look up users, user devices); /cucm-uds/...

**Notes:**

<!-- TODO -->

### T21.04 · Other UC APIs (awareness)

**Must cover:**

- [ ] Serviceability (RisPort for device registration status), CTI/JTAPI/TAPI for call control, Finesse for contact centre

**Notes:**

<!-- TODO -->

### T21.05 · Choosing

**Must cover:**

- [ ] Admin/bulk provisioning → AXL; user-facing lookups → UDS

**Notes:**

<!-- TODO -->

### T21.06 · Exam angle

**Must cover:**

- [ ] Match AXL vs UDS to a task; recognise AXL as SOAP

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
| T21.1 | Video | Automate Cisco Collaboration Platforms | 30 | CBT module |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
