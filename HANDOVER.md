# Handover: from Claude (Cowork) to Claude Code

Written 5 Oct 2026. It covers everything decided so far, so a Claude Code session can pick up without the earlier chats.

## 1. Context in one screen

- **Exam:** Cisco 200-901 CCNAAUTO v1.1 ("CCNA Automation", formerly DevNet Associate), on **Mon 9 Nov 2026** (moved from 1 Nov on 11 Oct 2026).
- **People:**
  - **Beedy** (Wendy Tan, `beedydo`): Cloud Infrastructure Engineer and Automation SME. RHCSA, RHCE, AWS SAA, ex-Ansible SA. Strong on Ansible, AWS, Bash, YAML, Docker, Git and CI/CD. New to Cisco platforms and model-driven programmability.
  - **Bob** (Jun Hao): network engineer. Strong on networking. Owns the platform and network topics.
- **Main course:** CBT Nuggets *Cisco CCNA Automation (200-901)*. Videos are skimmed at 1.5–2x for main points; notes come from this repo.
- **Practice questions:** the N2K practice exams inside the CBT course, using the domain filter.
- **Time:** 30 min per night per person, from 5 Oct to 1 Nov, then a break week (2–8 Nov) with the mock and review.

## 2. What exists already

| Artifact | Where | Notes |
|---|---|---|
| Google Sheet `CCNA_Automation_Training_Schedule` | Beedy's Google Drive | Tabs: Overview, Weekly Plan, Daily Plan, Topic Map (with Assignee), Beedy Concepts (202 rows), Bob Concepts (168 rows), Pair Plan, Practice Log. **Pair Plan is the current schedule.** Daily Plan, Weekly Plan and the Topic Map "Scheduled" column are from an earlier solo plan and are out of date. |
| This repo's `data/*.csv` | here | Exported from that sheet plus the coverage audit, so the sheet and the repo hold the same data |
| `CCNA_Automation_CBT_Coverage_Audit.xlsx` | Beedy's downloads (Cowork chat) | Item-level blueprint map: same content as `data/blueprint-map.csv`, `cbt-skip-list.csv`, `top-ups.csv` |
| Older tracker `CCNA_Automation_Study_Checklist.xlsx` | claude.ai chat "CCNA automation exam preparation plan" | Contains an earlier **Notes** tab (131 concepts, 89 exam traps, 21 examples) and a platform auth quick-reference. Useful raw material. Export it and drop it in `reference/` if wanted. Its MVC/Observer claim is unverified (see §6). |

## 3. Topic split (from the Topic Map "Assignee" column)

- **Beedy (22):** T02, T04, T05, T06, T07, T08, T09, T10, T11, T26, T27, T28, T29, T30, T31, T32, T33, T34, T43, T44, T46, T47
- **Bob (25):** T01, T03, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22, T23, T24, T25, T35, T36, T37, T38, T39, T40, T41, T42, T45

## 4. Schedule (Pair Plan)

Re-planned on Sun 11 Oct 2026: the exam moved to **Mon 9 Nov**. Four weekly cycles: **Mon–Sat** self-study (draft notes, check and correct them, practice questions, teach-back cards), **Sunday** teach-back together. Topics were rebalanced across cycles by note size, CBT gaps and how new each topic is to its owner.

| Cycle | Study | Teach-back | Beedy | Bob |
|---|---|---|---|---|
| 1 | 5–10 Oct | **Sun 11 Oct** | T02, T04, T05, T06 | T01, T03, T12, T13, T35, T36, T39 |
| 2 | 12–17 Oct | **Sun 18 Oct** | T07, T08, T09, T10, T11 | T14, T15, T16, T17, T18, T19 |
| 3 | 19–24 Oct | **Sun 25 Oct** | T43, T47, T26, T27, T28, T29 | T20, T21, T22, T37, T23, T24, T25 |
| 4 | 26–31 Oct | **Sun 1 Nov** | T30, T31, T32, T33, T34, T44, T46 | T42, T45, T38, T40, T41 |

| Date | Together |
|---|---|
| Tue 20 / Thu 22 Oct | Cross-study the partner's cycle 1 / cycle 2 notes (after own topics) |
| Tue 27 Oct | Cross-study the partner's cycle 3 notes |
| **Fri 30 Oct** | **Swap quiz** |
| **Mon 2 Nov** | **Mock exam, one 2-hour sitting** (fixes the old 4×30-min stamina gap) |
| **Tue 3 Nov** | **Joint mock review** |
| Wed 4 Nov | Weak-domain Qs + cross-study cycle 4 notes |
| Thu 5 Nov | Weak-domain Qs |
| Fri 6 Nov | 10-min rapid-fire |
| Sat 7 – Sun 8 Nov | Cheat sheet, booking/ID check, rest |
| **Mon 9 Nov** | **Exam** |

Day-by-day detail: `data/pair-plan.csv`.

**Teach-back format (30 min):** Beedy teaches for 12 min and Bob for 12 min, using 3 key points and 1 exam trap per topic. The last 6 min is one question per topic, with weak topic IDs logged.

## 5. CBT coverage audit (done 1 Oct against the v1.1 exam topics PDF)

- **Blueprint mapping:** all 63 blueprint items map to a tracker topic, so nothing tested is missing from the plan.
- **CBT covers fully:** 52 items.
- **CBT covers partly:** 6 items.
  - 1.4: dev methods comparison
  - 2.8: REST vs RPC, sync vs async
  - 3.4: Webex devices / xAPI
  - 3.5: XDR, Secure Endpoint, Secure Connect, Malware Analytics
  - 6.3: load balancers
  - 6.8: proxy/VPN diagnosis
- **CBT doesn't cover:** 5 items.
  - 2.2: webhooks (T43)
  - 2.3: API consumption constraints (T08)
  - 4.9: firewall/DNS/load balancer/reverse proxy (T41)
  - 5.13: code review (T46)
  - 5.14: sequence diagrams (T47)
- **Skip list:** about 263 min of off-blueprint CBT. Covers ASA, PowerShell, UCS Director/PowerTool, Singleton, VS Code setup, Postman, VM/WSL setup, Ansible install, and the old "Webex Teams" module. Also skim the ACI Toolkit and "Real-World Nexus" videos (`data/cbt-skip-list.csv`).
- **Top-ups:** about 315 min for the partial and uncovered items (`data/top-ups.csv`).
- **Method caveat:** coverage was matched from video **titles**, because CBT content is behind a login. It was not matched from transcripts.

## 6. Open flags (resolve while studying)

| Flag | Topic | What to do |
|---|---|---|
| Does CBT "Determine When to Use Design Patterns" cover **MVC and Observer**? | T03 (Bob) | Bob checks while watching. If not, learn them from the note. Blueprint 1.6 names MVC and Observer explicitly. |
| Does the CBT Git diff video teach reading `@@` hunk headers? | T05 (Beedy) | Use the drill in the note regardless |
| Edge-computing depth in the CBT deployment-models video | T26 (Beedy) | A one-paragraph note is enough |
| Version-sensitive facts | various | FMC token lifetime; Meraki rate limit; Catalyst Center / SD-WAN Manager paths; Webex token lifetimes; ISE ERS port. Confirm against current docs or a sandbox and mark `⚠ verify` until done. |
| Blueprint 3.9.a/b/c sub-item wording | T18–T22, T42 | Labels are paraphrased; confirm in the Cisco PDF |
| Bob's GitHub username | repo | Needed for `CODEOWNERS` and the collaborator invite |
| Mock 1 is four 30-min blocks, which doesn't train 120-min stamina | both | Resolved: the mock is now one 2-hour sitting on Mon 2 Nov |
| `quizzes/question-bank/` (≈500 MB of PDFs, one folder named `dump/`) | both | Ask Bob where the PDFs came from. If they're real exam dumps, remove them (Cisco exam rules + CLAUDE.md forbid them) with a history rewrite; if legitimate, move them to Git LFS or Drive. |
| T30 OWASP has no full note | T30 (Beedy) | `bee/T30-…` is still an empty template, so its essentials facts have no backing note. Run `/note T30` before cycle 4. |

## 7. How to start in Claude Code (Beedy, today)

1. Unzip this package, then push it to the empty repo. Clone first if the repo already has a README:

   ```bash
   gh repo clone beedydo/ccna-auto-study-notes
   cp -R ccna-auto-study-notes-scaffold/. ccna-auto-study-notes/
   cd ccna-auto-study-notes
   git add --all
   git commit --message "Scaffold: topics, concepts, plan, Claude Code commands"
   git push origin main
   ```

2. Invite Bob (see `CONTRIBUTING.md`).
3. Run `claude` in the repo, then:
   - `/progress`
   - `/note T02`, then `/note T04`. These are tonight's topics (Mon 5 Oct).
   - `/verify T02`, `/verify T04`
   - Do the questions, then set `status: verified`.
4. Tomorrow: T05, T06. Wednesday: `/teachback 1` for your section.

## 8. Ideas Claude Code can take further

- **Spaced repetition:** export each note's "Exam traps" and practice questions to an Anki-compatible CSV (`quizzes/anki.csv`).
- **Mock simulator:** `/quiz partner` in interactive mode on cross-study nights.
- **Score tracking:** a small script that reads `data/practice-log.csv` and prints weighted readiness by domain (weights 15/20/15/15/20/15).
- **Labs:** CI-free labs only. Use DevNet Sandbox and the Docker container in `labs/`; nothing needs cloud spend.

## 9. Session log: Beedy, 19–24 Oct 2026

- **Essentials redesign.** All 22 `bee-essentials/` files rewritten in two passes: (1) tiered 🟥 must / 🟨 should / recognise-only, fully explained with analogies and annotated examples; (2) visual: big idea as a table, icons, tables over bullets, ❌/✅ contrasts, traps as "Looks like / Actually". Rules now live in `.claude/commands/note.md` §3 "Essentials file"; `/note` writes essentials every run.
- **T05 and T06 visuals.** HTML-rendered comparison sheets + GIFs in `assets/T05/` and `assets/T06/`. `assets/T06/02-cisco-api-formats.png` maps the data format and first parse step of every Cisco API in Bob's topics: share it with Bob.
- **Syntax drills.** Standalone cheat sheets were tried and rejected as clutter; the content is now a collapsed `## Syntax drill` at the end of the T05/T06 essentials, and question → answer tables are in `cheatsheet.md`.
- **Content added on request:** JWT as a token format (T10, awareness), what an artifact is (T28), the mutable vs immutable section rewritten with a one-line analogy (T33), the Dockerfile → image → container image (T27).
- **Case study.** `case-studies/api-to-s3-collector.md`: a sample API → S3 pipeline read through T06–T47, with 10 issues and fixes. Names made generic before publishing.
- **Repo housekeeping.** `bob/question-bank` branch was already merged and was deleted. T04–T08 marked done by Beedy on 20 Oct.

