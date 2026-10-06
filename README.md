# CCNA Automation (200-901 CCNAAUTO v1.1) study notes

Shared study notes for Beedy ([@beedydo](https://github.com/beedydo)) and Bob, for the exam on **Sun 1 Nov 2026**.

- Notes are written mostly with Claude Code. `CLAUDE.md` holds the rules, and `.claude/commands/` holds the slash commands.
- Each person writes their own topics, teaches them to the other, and then studies the other person's notes.

## Who owns what

| Owner | Topics | Focus |
|---|---|---|
| **Beedy** (22) | T02, T04-T11, T26-T34, T43, T44, T46, T47 | Python, Git, data formats, REST/APIs, deployment, Docker, CI/CD, security, OWASP, Bash, TDD, IaC, Ansible, webhooks, pyATS, code review, sequence diagrams |
| **Bob** (25) | T01, T03, T12-T25, T35-T42, T45 | Dev methods, design patterns, model-driven programmability (YANG/NETCONF/RESTCONF), device APIs, Cisco platforms, network fundamentals, Webex, reading Cisco API scripts |

The full list is in `data/topics.csv`. Each topic note lives in its owner's folder (`bee/` or `bob/`), and each scaffold note starts with a pre-filled checklist of every concept it must cover (370 concepts in total).

## Exam domains (v1.1 weights)

| Domain | Weight | Index |
|---|---|---|
| 1 Software Development and Design | 15% | `notes/d1-software-development/` |
| 2 Understanding and Using APIs | 20% | `notes/d2-apis/` |
| 3 Cisco Platforms and Development | 15% | `notes/d3-cisco-platforms/` |
| 4 Application Deployment and Security | 15% | `notes/d4-app-deployment-security/` |
| 5 Infrastructure and Automation | 20% | `notes/d5-infrastructure-automation/` |
| 6 Network Fundamentals | 15% | `notes/d6-network-fundamentals/` |

Every one of the 63 blueprint items maps to at least one topic (`data/blueprint-map.csv`).

## Plan (30 min a night each)

| Dates | Phase |
|---|---|
| 5-19 Oct | Learn your own topics in 4 batches |
| **8, 12, 16, 20 Oct** | **Teach-backs 1-4** (together, 30 min) |
| 21-23 Oct | Cross-study the partner's notes and do practice questions |
| **24 Oct** | **Swap quiz** (together) |
| 25-28 Oct | Mock 1, in four 30-min timed blocks |
| **29 Oct** | **Joint mock review** |
| 30 Oct | Remediation + rapid-fire quiz |
| 31 Oct | Cheat sheet, admin, rest |
| **1 Nov** | **Exam** |

Night-by-night detail is in `data/pair-plan.csv`.

## Quick start (Claude Code)

```bash
gh repo clone beedydo/ccna-auto-study-notes
cd ccna-auto-study-notes
claude
```

Then, inside Claude Code:

```
/progress          # what's due tonight
/note T07          # draft a topic note
/verify T07        # fact-check it
/quiz T07          # practice questions
/teachback 2       # cards for the next joint session
```

## Progress

<!-- progress:start -->
_Updated 2026-10-05 by scripts/progress.py_

| ID | Topic | Owner | Status | Checklist | Learn by | Flag |
|---|---|---|---|---|---|---|
| T01 | Software dev methods: agile, lean, waterfall | Bob | not-started | 0/16 | 2026-10-05 |  |
| T02 | Functions, classes, modules | Beedy | not-started | 0/52 | 2026-10-05 |  |
| T03 | Design patterns: MVC + Observer | Bob | not-started | 0/18 | 2026-10-05 |  |
| T04 | Git + version control | Beedy | not-started | 0/57 | 2026-10-05 |  |
| T05 | Unified diffs | Beedy | not-started | 0/21 | 2026-10-06 |  |
| T06 | Data formats + parsing | Beedy | not-started | 0/59 | 2026-10-06 |  |
| T07 | REST fundamentals, HTTP codes | Beedy | not-started | 0/63 | 2026-10-09 |  |
| T08 | API consumption constraints | Beedy | not-started | 0/31 | 2026-10-09 |  |
| T09 | API styles: REST vs RPC, sync vs async | Beedy | not-started | 0/32 | 2026-10-10 |  |
| T10 | API authentication | Beedy | not-started | 0/34 | 2026-10-10 |  |
| T11 | Python requests scripting | Beedy | not-started | 0/29 | 2026-10-11 |  |
| T12 | Automation foundations: controller vs device | Bob | not-started | 0/22 | 2026-10-05 |  |
| T13 | DevNet resources | Bob | not-started | 0/9 | 2026-10-06 |  |
| T14 | YANG data models | Bob | not-started | 0/20 | 2026-10-09 |  |
| T15 | NETCONF | Bob | not-started | 0/28 | 2026-10-10 |  |
| T16 | RESTCONF | Bob | not-started | 0/26 | 2026-10-11 |  |
| T17 | IOS XE and NX-OS device-level APIs | Bob | not-started | 0/14 | 2026-10-11 |  |
| T18 | Meraki | Bob | not-started | 0/18 | 2026-10-13 |  |
| T19 | ACI | Bob | not-started | 0/17 | 2026-10-13 |  |
| T20 | Catalyst Center (DNA Center) | Bob | not-started | 0/18 | 2026-10-14 |  |
| T21 | Collaboration: CUCM AXL + UDS | Bob | not-started | 0/9 | 2026-10-14 |  |
| T22 | Catalyst SD-WAN | Bob | not-started | 0/12 | 2026-10-15 |  |
| T23 | Security platforms | Bob | not-started | 0/17 | 2026-10-17 |  |
| T24 | Compute: UCS Manager + Intersight | Bob | not-started | 0/18 | 2026-10-17 |  |
| T25 | NSO + Cisco Modeling Labs | Bob | not-started | 0/15 | 2026-10-17 |  |
| T26 | Deployment models + edge computing | Beedy | not-started | 0/30 | 2026-10-13 |  |
| T27 | Docker | Beedy | not-started | 0/33 | 2026-10-13 |  |
| T28 | CI/CD + DevOps principles | Beedy | not-started | 0/30 | 2026-10-13 |  |
| T29 | Secrets, encryption, data handling | Beedy | not-started | 0/26 | 2026-10-14 |  |
| T30 | OWASP: XSS, SQLi, CSRF | Beedy | not-started | 0/30 | 2026-10-14 |  |
| T31 | Bash | Beedy | not-started | 0/24 | 2026-10-15 |  |
| T32 | TDD + Python unit tests | Beedy | not-started | 0/24 | 2026-10-17 |  |
| T33 | IaC + tool comparison | Beedy | not-started | 0/27 | 2026-10-17 |  |
| T34 | Ansible playbook interpretation | Beedy | not-started | 0/23 | 2026-10-17 |  |
| T35 | Layer 2: MAC, VLANs | Bob | not-started | 0/7 | 2026-10-06 |  |
| T36 | Layer 3: IP, masks, routes, gateways | Bob | not-started | 0/9 | 2026-10-06 |  |
| T37 | Transport, ports, IP services | Bob | not-started | 0/10 | 2026-10-15 |  |
| T38 | Topology diagrams + components | Bob | not-started | 0/7 | 2026-10-18 |  |
| T39 | Management, control, data planes | Bob | not-started | 0/5 | 2026-10-07 |  |
| T40 | App connectivity + network constraints | Bob | not-started | 0/11 | 2026-10-19 |  |
| T41 | Firewall, DNS, LB, reverse proxy | Bob | not-started | 0/12 | 2026-10-19 |  |
| T42 | Webex + Webex devices | Bob | not-started | 0/13 | 2026-10-18 |  |
| T43 | Webhooks | Beedy | not-started | 0/28 | 2026-10-18 |  |
| T44 | pyATS + Genie | Beedy | not-started | 0/24 | 2026-10-18 |  |
| T45 | Reading Python scripts using Cisco APIs | Bob | not-started | 0/5 | 2026-10-18 |  |
| T46 | Code review principles | Beedy | not-started | 0/18 | 2026-10-19 |  |
| T47 | Sequence diagrams with API calls | Beedy | not-started | 0/21 | 2026-10-19 |  |
<!-- progress:end -->

## Repo map

- `CLAUDE.md`: rules for Claude Code (format, accuracy, ownership)
- `HANDOVER.md`: how this repo was set up, decisions, open flags
- `CONTRIBUTING.md`: Git workflow for Beedy and Bob
- `data/`: topics, concepts, blueprint map, CBT aids, skip list, top-ups, pair plan, practice log
- `bee/`: Beedy's topic notes
- `bob/`: Bob's topic notes
- `notes/dN-*/README.md`: per-domain index linking to both
- `teach-back/`: cards for the 4 joint sessions
- `quizzes/`: generated question banks
- `labs/`: Docker lab container and per-topic labs
- `cheatsheet.md`: exam-eve sheet
