---
id: T16
title: "RESTCONF"
owner: Bob
blueprint: "3.8, 5.10, 2.9"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-11
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T16 · RESTCONF

> Owner: **Bob** · Blueprint: **3.8, 5.10, 2.9** · CBT coverage: **Full** · Learn by 2026-10-11 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T16.01 · What RESTCONF is

**Must cover:**

- [ ] RFC 8040: HTTP-based, REST-like access to YANG-modelled data
- [ ] JSON or XML encoding over HTTPS (port 443)

**Notes:**

<!-- TODO -->

### T16.02 · URI structure

**Must cover:**

- [ ] Root discovery: GET /.well-known/host-meta → /restconf
- [ ] /restconf/data = datastore resources; /restconf/operations = RPCs
- [ ] /restconf/data/<module>:<container>/<list>=<key>/<leaf>

**Notes:**

<!-- TODO -->

### T16.03 · Methods

**Must cover:**

- [ ] GET = read (≈ NETCONF get/get-config)
- [ ] POST = create a child resource (error if it exists)
- [ ] PUT = create or replace
- [ ] PATCH = merge (partial update)
- [ ] DELETE = remove

**Notes:**

<!-- TODO -->

### T16.04 · Headers

**Must cover:**

- [ ] Accept and Content-Type: application/yang-data+json or application/yang-data+xml
- [ ] Authentication: HTTP basic over HTTPS

**Notes:**

<!-- TODO -->

### T16.05 · Responses

**Must cover:**

- [ ] 200 OK with data (GET)
- [ ] 201 Created (POST/PUT new)
- [ ] 204 No Content (successful PUT/PATCH/DELETE)
- [ ] 400 bad payload; 401 auth; 404 path/resource not found; 409 already exists

**Notes:**

<!-- TODO -->

### T16.06 · Query parameters

**Must cover:**

- [ ] depth=N limits nesting; fields= selects leaves
- [ ] content=config | nonconfig | all

**Notes:**

<!-- TODO -->

### T16.07 · Device setup

**Must cover:**

- [ ] IOS XE: restconf and ip http secure-server

**Notes:**

<!-- TODO -->

### T16.08 · NETCONF vs RESTCONF

**Must cover:**

- [ ] Transport: SSH 830 vs HTTPS 443
- [ ] Encoding: XML only vs JSON or XML
- [ ] Datastores: running/candidate/startup + lock/commit vs a single unified datastore, no locking
- [ ] Style: RPC operations vs HTTP methods on resources

**Notes:**

<!-- TODO -->

### T16.09 · Python

**Must cover:**

- [ ] requests.get(url, auth=(u, p), headers={"Accept": "application/yang-data+json"}, verify=False)
- [ ] requests.patch(url, json=body, ...) for a partial change

**Notes:**

<!-- TODO -->

### T16.10 · Exam angle

**Must cover:**

- [ ] Choose the method/URL/header for a change; interpret a RESTCONF JSON reply

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
| T16.1 | Video | Develop RESTCONF Scripts for Cisco IOS-XE | 25 | CBT module |
| T16.2 | Lab | GET / PATCH / PUT / DELETE via curl + requests | 60 | DevNet always-on IOS XE sandbox |
| T16.3 | Top-up | NETCONF vs RESTCONF comparison table | 30 | Own notes |
| T16.4 | Drill | Interpret RESTCONF / NETCONF replies | 30 | Output from labs |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
