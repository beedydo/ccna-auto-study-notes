# CCNA Automation (200-901 CCNAAUTO v1.1) study notes

Shared study notes for Beedy ([@beedydo](https://github.com/beedydo)) and Bob, for the exam on **Mon 9 Nov 2026**.

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

Four weekly cycles: Mon-Sat self-study (draft, check and correct notes, prep cards), Sunday teach-back. Then a break week before the exam.

| Dates | Phase |
|---|---|
| 5-10 Oct | Cycle 1: learn your own topics |
| **Sun 11 Oct** | **Teach-back 1** (together, 30 min) |
| 12-17 Oct | Cycle 2: learn, check and correct notes, prep cards |
| **Sun 18 Oct** | **Teach-back 2** |
| 19-24 Oct | Cycle 3, plus cross-study the partner's cycle 1-2 notes (Tue, Thu) |
| **Sun 25 Oct** | **Teach-back 3** |
| 26-31 Oct | Cycle 4, plus cross-study cycle 3 notes (Tue); **swap quiz Fri 30 Oct** |
| **Sun 1 Nov** | **Teach-back 4** |
| Mon 2 Nov | Mock exam: one 2-hour sitting |
| Tue 3 Nov | Joint mock review |
| 4-5 Nov | Weak-domain questions (cross-study cycle 4 notes on Wed) |
| Fri 6 Nov | 10-min rapid-fire together |
| 7-8 Nov | Cheat sheet, admin, rest |
| **Mon 9 Nov** | **Exam** |

### Calendar

<!-- calendar:start -->

**October 2026**

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|
| **5**<br>📚 Cycle 1 study | **6**<br>📚 Cycle 1 study | **7**<br>📚 Cycle 1 study | **8**<br>📚 Cycle 1 study | **9**<br>📚 Cycle 1 study | **10**<br>📚 Cycle 1 study | **11**<br>🎤 **Teach-back 1** |
| **12**<br>🐝 T07 T08<br>🅱️ T14 T15 | **13**<br>🐝 T09<br>🅱️ T16 | **14**<br>🐝 T10<br>🅱️ T17 T18 | **15**<br>🐝 T11<br>🅱️ T19 | **16**<br>✅ Check notes + cards | **17**<br>✅ Check notes + cards | **18**<br>🎤 **Teach-back 2** |
| **19**<br>🐝 T43 T47<br>🅱️ T20 T21 | **20**<br>🐝 T26<br>🅱️ T22 T37<br>🔁 cross-study | **21**<br>🐝 T27 T28<br>🅱️ T23 T24 | **22**<br>🐝 T29<br>🅱️ T25<br>🔁 cross-study | **23**<br>✅ Check notes + cards | **24**<br>✅ Check notes + cards | **25**<br>🎤 **Teach-back 3** |
| **26**<br>🐝 T30 T31<br>🅱️ T42 T45 | **27**<br>🐝 T32 T33<br>🅱️ T38<br>🔁 cross-study | **28**<br>🐝 T34 T44<br>🅱️ T40 | **29**<br>🐝 T46<br>🅱️ T41 | **30**<br>🔀 **Swap quiz** | **31**<br>✅ Check notes + cards |   |

**November 2026**

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|
|   |   |   |   |   |   | **1**<br>🎤 **Teach-back 4** |
| **2**<br>🧪 **Mock exam** (2 h) | **3**<br>🔍 **Mock review** | **4**<br>🩹 Weak-domain Qs · 🔁 cross-study | **5**<br>🩹 Weak-domain Qs | **6**<br>⚡ Rapid-fire | **7**<br>📋 Cheat sheet + admin | **8**<br>😴 Rest |
| **9**<br>🎯 **EXAM** |   |   |   |   |   |   |

🐝 Beedy · 🅱️ Bob · 🎤 teach-back (Sun, 30 min together) · ✅ check + correct notes, practice Qs, cards · 🔁 cross-study the partner's notes · 🔀 swap quiz · 🧪 mock · 🎯 exam

_Generated from `data/pair-plan.csv` by `scripts/plan_calendar.py`. Change the CSV, then re-run the script._

<!-- calendar:end -->

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
