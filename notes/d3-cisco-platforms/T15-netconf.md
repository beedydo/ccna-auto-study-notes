---
id: T15
title: "NETCONF"
owner: Bob
blueprint: "3.8, 5.10"
primary_domain: D3
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-10
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T15 · NETCONF

> Owner: **Bob** · Blueprint: **3.8, 5.10** · CBT coverage: **Full** · Learn by 2026-10-10 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T15.01 · What NETCONF is

**Must cover:**

- [ ] RFC 6241 protocol to install, change and read device config/state
- [ ] XML-encoded messages over SSH, default port 830

**Notes:**

<!-- TODO -->

### T15.02 · Layers

**Must cover:**

- [ ] Content: config/state data (YANG-modelled)
- [ ] Operations: get, get-config, edit-config…
- [ ] Messages: <rpc>, <rpc-reply>, <notification>
- [ ] Secure transport: SSH

**Notes:**

<!-- TODO -->

### T15.03 · Session

**Must cover:**

- [ ] Client and server exchange <hello> with their capabilities (supported models/features)
- [ ] Test manually: ssh -p 830 user@host -s netconf
- [ ] Message framing: ]]>]]> (1.0) vs chunked framing (1.1)

**Notes:**

<!-- TODO -->

### T15.04 · Operations

**Must cover:**

- [ ] <get>: config + operational state
- [ ] <get-config>: config from a datastore (source)
- [ ] <edit-config>: change a datastore (target); operation attribute merge / replace / create / delete / remove
- [ ] <copy-config>, <delete-config>, <lock>/<unlock>
- [ ] <commit>, <discard-changes>, <validate>, <close-session>, <kill-session>

**Notes:**

<!-- TODO -->

### T15.05 · Datastores

**Must cover:**

- [ ] running: active config
- [ ] candidate: staging area, applied with <commit> (if capability supported)
- [ ] startup: config loaded at boot

**Notes:**

<!-- TODO -->

### T15.06 · Filters

**Must cover:**

- [ ] Subtree filter (XML template of what to return) or XPath filter

**Notes:**

<!-- TODO -->

### T15.07 · Replies

**Must cover:**

- [ ] <ok/> on success
- [ ] <data> containing results
- [ ] <rpc-error> with error-type, error-tag, error-severity, error-message

**Notes:**

<!-- TODO -->

### T15.08 · Python ncclient

**Must cover:**

- [ ] from ncclient import manager
- [ ] m = manager.connect(host=..., port=830, username=..., password=..., hostkey_verify=False)
- [ ] m.get_config(source="running", filter=("subtree", f)); m.edit_config(target="running", config=xml)
- [ ] m.server_capabilities lists capabilities

**Notes:**

<!-- TODO -->

### T15.09 · Device setup and value

**Must cover:**

- [ ] IOS XE: netconf-yang (global config)
- [ ] Value vs CLI: transactions, validation, structured output, network-wide consistency

**Notes:**

<!-- TODO -->

### T15.10 · Exam angle

**Must cover:**

- [ ] Pick the operation/datastore for a task; read an rpc-reply; know port 830 and SSH

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
| T15.1 | Video | Develop NETCONF Scripts for Cisco IOS-XE Devices | 42 | CBT module |
| T15.2 | Lab | ncclient get / get-config / edit-config; ssh -s netconf hello | 60 | DevNet always-on IOS XE sandbox |
| T15.3 | Drill | Flashcards: operations, datastores, port 830 | 20 | Own cheat sheet |

- Skip / low priority: Full ncclient scripts

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
