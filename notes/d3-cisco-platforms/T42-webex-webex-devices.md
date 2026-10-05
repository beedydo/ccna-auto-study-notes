---
id: T42
title: "Webex + Webex devices"
owner: Bob
blueprint: "3.4, 3.9.b"
primary_domain: D3
cbt_coverage: "Partial"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-18
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T42 · Webex + Webex devices

> Owner: **Bob** · Blueprint: **3.4, 3.9.b** · CBT coverage: **Partial** · Learn by 2026-10-18 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T42.01 · Webex REST API

**Must cover:**

- [ ] Base https://webexapis.com/v1
- [ ] Resources: people, rooms (spaces), messages, memberships, teams, webhooks, meetings

**Notes:**

<!-- TODO -->

### T42.02 · Authentication

**Must cover:**

- [ ] Authorization: Bearer <token>
- [ ] Personal access token (developer portal, short-lived ~12 h), bot token (long-lived), integration (OAuth 2.0 grant), guest issuer (awareness)

**Notes:**

<!-- TODO -->

### T42.03 · Common calls

**Must cover:**

- [ ] GET /rooms; POST /rooms {"title": ...}
- [ ] POST /messages with roomId or toPersonEmail, plus text/markdown/files
- [ ] POST /memberships to add people

**Notes:**

<!-- TODO -->

### T42.04 · Bots

**Must cover:**

- [ ] Separate identity that is added to spaces; reacts to events via webhooks (see Beedy T43)

**Notes:**

<!-- TODO -->

### T42.05 · Webex devices xAPI

**Must cover:**

- [ ] API on RoomOS devices: xCommand (actions), xConfiguration (settings), xStatus (state), xEvent (events)
- [ ] Access: SSH, HTTP(S) /putxml and /getxml, cloud xAPI via webexapis.com/v1/xapi/...
- [ ] Macros: JavaScript running on the device

**Notes:**

<!-- TODO -->

### T42.06 · SDKs (awareness)

**Must cover:**

- [ ] Webex JS SDK; Python webexpythonsdk (formerly webexteamssdk)

**Notes:**

<!-- TODO -->

### T42.07 · Exam angle

**Must cover:**

- [ ] Complete code that posts a message; pick token type; recognise xAPI command types

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
| T42.1 | Video | Automate Cisco Webex (skip older 'Webex Teams' module) | 58 | CBT module |
| T42.2 | Top-up | Webex devices xAPI overview | 20 | Webex developer docs |

- Skip / low priority: Webex Teams (older module)

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
