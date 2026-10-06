---
id: T34
title: "Ansible playbook interpretation"
owner: Beedy
blueprint: "5.8"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T34 · Ansible playbook interpretation

> Owner: **Beedy** · Blueprint: **5.8** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T34.01 · Inventory

**Must cover:**

- [ ] Inventory lists hosts and groups (INI or YAML)
- [ ] group_vars/ and host_vars/ hold per-group / per-host variables
- [ ] Variables like ansible_network_os, ansible_connection, ansible_user

**Notes:**

<!-- TODO -->

### T34.02 · Playbook structure

**Must cover:**

- [ ] Play: hosts (target group), gather_facts, connection, vars, tasks
- [ ] connection: network_cli (SSH CLI), netconf, httpapi (REST), local
- [ ] Each task: name + module + arguments

**Notes:**

<!-- TODO -->

### T34.03 · Modules

**Must cover:**

- [ ] ios_command / cisco.ios.ios_command: run show commands
- [ ] ios_config / cisco.ios.ios_config: push config lines
- [ ] uri: generic REST calls
- [ ] netconf_get / netconf_config; restconf_get / restconf_config
- [ ] template (Jinja2 → file); debug (print variables)

**Notes:**

<!-- TODO -->

### T34.04 · Variables

**Must cover:**

- [ ] {{ variable }} Jinja2 substitution
- [ ] register: save task output to a variable
- [ ] Facts: gathered device/host data

**Notes:**

<!-- TODO -->

### T34.05 · Control

**Must cover:**

- [ ] loop (or with_items) repeats a task
- [ ] when: conditional execution
- [ ] notify triggers a handler that runs once at the end if something changed

**Notes:**

<!-- TODO -->

### T34.06 · Running

**Must cover:**

- [ ] ansible-playbook -i inventory.yml site.yml
- [ ] --check dry run; -v / -vvv verbosity; --limit host
- [ ] Result states: ok (no change), changed, failed, skipped

**Notes:**

<!-- TODO -->

### T34.07 · Structure (awareness)

**Must cover:**

- [ ] Roles package tasks/vars/templates for reuse
- [ ] ansible.cfg sets defaults (inventory path, etc.)

**Notes:**

<!-- TODO -->

### T34.08 · Exam angle

**Must cover:**

- [ ] Read a playbook: which devices, which modules, what config or data, in what order

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
| T34.1 | Video | RESTCONF playbook videos only | 15 | CBT: Automate Your Entire Network with Ansible |

- Skip / low priority: Ansible installation

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
