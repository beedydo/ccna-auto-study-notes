# CLAUDE.md: CCNA Automation (200-901 CCNAAUTO v1.1) study notes

Project memory for Claude Code. Read this first in every session.

## Mission

- Two people are preparing for **Cisco 200-901 CCNAAUTO v1.1**, with the **exam on Sun 1 Nov 2026**.
  - **Beedy** (Wendy, GitHub `beedydo`, repo owner) is a DevOps/cloud infra engineer. She owns the dev, API, DevOps and app-deployment topics.
  - **Bob** (Jun Hao) is a network engineer. He owns the platforms, model-driven programmability and network-fundamentals topics.
- This repo holds the learning notes for all 47 tracker topics, in 6 blueprint domains.
  - Each person writes notes for their own topics, mostly with Claude Code.
  - Each person then teaches their topics to the other. Notes must be good enough to learn from without the video.
- Time budget: **30 min per night per person**. Notes must be scannable, exam-focused and complete. Do not pad them.

## Who is running this session

- Check `git config user.name` (or ask) to tell whether Beedy or Bob is at the keyboard. Use that to pick their topics, their schedule column and their section of shared files.
- Use today's date with `data/pair-plan.csv` to work out tonight's topics.

## Handover context (decisions, schedule, open flags)

Full background from the planning chats: topic split, Pair Plan schedule, teach-back format, CBT coverage audit and open flags. Imported so every session loads it:

@HANDOVER.md

## Source of truth

| What | Where |
|---|---|
| Topic list, owner, blueprint items, CBT coverage, dates | `data/topics.csv` |
| Every concept a topic must cover (minimum scope) | `data/concepts.csv` (370 rows; also pre-filled as checklists in each note) |
| Cisco blueprint v1.1 → topic mapping and CBT gaps | `data/blueprint-map.csv` |
| CBT videos/labs/top-ups per topic | `data/study-aids.csv` |
| Topics CBT doesn't cover (fully) and how to fill the gap | `data/top-ups.csv` |
| CBT videos to skip | `data/cbt-skip-list.csv` |
| Night-by-night pair plan, 5 Oct to 1 Nov | `data/pair-plan.csv` |
| Practice scores | `data/practice-log.csv` |
| Original Google Sheet (tracker with status columns) | `CCNA_Automation_Training_Schedule` in Beedy's Google Drive |

If the CSVs and a note disagree on owner, blueprint or dates, the CSV wins. Update the note's front matter to match.

## Repo layout

```
bee/                              Beedy's topic notes ONLY (22 files): TXX-slug.md
bob/                              Bob's topic notes ONLY (25 files): TXX-slug.md
notes/d1..d6-*/README.md          per-domain index tables linking into bee/ and bob/ (no notes here)
CLAUDE.md, HANDOVER.md, data/     shared context: stays at the root, never inside bee/ or bob/
teach-back/                       teach-back-1..4.md (cards for each joint session)
quizzes/                          generated question banks (one file per topic or batch)
labs/                             Docker lab container + runnable scripts
cheatsheet.md                     1-page exam-eve sheet (build from "Exam traps" sections)
scripts/progress.py               prints progress from note front matter
```

- Topic notes live in the **owner's folder**: `bee/` for Beedy, `bob/` for Bob. Only topic notes go there; shared files stay at the root.
- `data/topics.csv` → `note_path` is the exact path of every topic note. Always resolve paths from it, never guess.
- New note for a topic: create it at its `note_path` from `templates/topic-note.md`, pre-filling the **Must cover** checklist from `data/concepts.csv`.
- Bob's round-1 notes (T01, T03, T12-T17) use his own format without front matter. Treat them as `drafted`. Don't reformat them unless Bob asks.
- If you add or rename a note, update `note_path` in `data/topics.csv` and the link in the matching `notes/dN-*/README.md`.

## Note format (every topic file)

- Front matter: `id, title, owner, blueprint, primary_domain, cbt_coverage, status, confidence, learn_by, teach_back, cross_study`.
  - `status` values: `not-started` → `drafted` (Claude wrote it) → `verified` (owner checked it against sources and did practice Qs) → `taught` (after the teach-back).
- Sections, in this order:
  1. `## TL;DR (teach-back card)`: 3 key points and 1 exam trap. Written last.
  2. `## Concepts`: one `### TXX.NN · Area` per concept ID.
     - Keep the pre-filled **Must cover** checklist. Tick `[x]` each item once the notes below explain it.
     - Write the explanation under **Notes:**.
  3. `## Exam traps`: confused pairs, exact syntax, scenario → answer.
  4. `## Examples`: full, runnable commands and code.
  5. `## Practice questions`: 5–8 exam-style questions, each answer and its explanation in `<details>`.
  6. `## Study aids`: pre-filled from `data/study-aids.csv`.
  7. `## Sources`: official links actually used.
  8. `## To verify`: anything version-sensitive or unconfirmed.

## Writing rules (Beedy's preferences apply to all notes)

- Point form, not paragraphs. Start each section with the high-level idea, then the detail.
- Don't repeat the question or summarise what is about to be said.
- **New topics:** explain from first principles. This means anything Cisco-platform specific, YANG/NETCONF/RESTCONF, and networking theory for Beedy.
- **Beedy's home turf:** skip basics on Ansible, AWS, Bash and YAML (she has RHCE, AWS SAA, and was an Ansible SA). Go straight to exam traps.
- **Bob's home turf:** keep networking fundamentals (T35–T41) exam-focused for him.
- Always show **full commands**, never partial. Use **Docker**, not Podman. AWS CLI with full flags, if AWS ever comes up.
- CLI and code only, no GUI walkthroughs, unless the topic itself is a GUI tool (e.g. ACI API Inspector, NX-API sandbox).
- No "be careful in production" warnings.
- Use current Cisco names and give the old name once in brackets:
  - Catalyst Center (DNA Center)
  - SD-WAN Manager / Controller / Validator (vManage / vSmart / vBond)
  - Secure Firewall Management Center (FMC)
  - Secure Endpoint (AMP)
  - Secure Malware Analytics (Threat Grid)
- Tables are fine for comparisons (e.g. NETCONF vs RESTCONF).
- Mermaid is fine for sequence diagrams, which are themselves a T47 topic.

## Accuracy rules (important)

- Ground every platform-specific fact in official sources: developer.cisco.com, Cisco docs, RFCs (6241 NETCONF, 8040 RESTCONF, 7950 YANG), Webex/Meraki developer docs, Python docs.
  - Use web search/fetch when available. List the URLs in `## Sources`.
- Mark anything version-sensitive or unconfirmed with `⚠ verify` and add it to `## To verify`. Known examples:
  - FMC token lifetime (~30 min) and refresh limits
  - Meraki rate limit (~10 req/s per org)
  - Exact Catalyst Center / SD-WAN Manager endpoint paths
  - Webex personal token lifetime (~12 h)
  - ISE ERS port 9060
- **Never claim what a CBT Nuggets video contains** unless the owner has watched it and said so. CBT content is behind a login, so coverage in this repo comes from video titles only. Known open flags:
  - T03: does CBT "Determine When to Use Design Patterns" actually teach MVC and Observer? Unconfirmed.
  - T05: does the CBT Git Diff video teach reading `@@` hunk headers? Unconfirmed.
  - T08 (2.3): the CBT "RESTful API Constraints" video covers REST architectural constraints, not consumer limits. Treat T08 as top-up.
  - T26 (4.1): edge computing depth in the CBT video is unconfirmed.
- Practice questions must be original, written in exam style. Never copy or reconstruct real exam questions or "dumps".
- Blueprint wording in `data/blueprint-map.csv` is paraphrased. For exact wording, check the official PDF: https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## Ownership and collaboration

- Each person edits **only their own topic notes** (`owner:` in front matter).
  - To suggest a change to a partner's note, open a PR or add a line under that note's `## To verify` on your branch. Do not rewrite their content.
- Branch per person per batch: `beedy/batch-2-apis`, `bob/batch-2-model-driven`. Open a PR to `main`; the other person reviews.
  - The review is itself practice for blueprint 5.13 (code review).
- Commit messages: `T07: draft REST fundamentals notes`, `T15: verify NETCONF ops, add 6 Qs`, `teach-back-2: Beedy cards`.
- Shared files (`cheatsheet.md`, `teach-back/*.md`, `data/practice-log.csv`): each person edits only their own section.

## Typical workflows (custom slash commands in `.claude/commands/`)

| Command | What it does |
|---|---|
| `/note T07` | Draft the full note for a topic: every concept checklist item covered, exam traps, runnable examples, 5–8 Qs, sources. Sets `status: drafted`. |
| `/verify T07` | Fact-check a drafted note against official docs; fix errors; tick the checklist; list `⚠ verify` items. |
| `/quiz T07` or `/quiz batch-2` | Generate or extend an exam-style question bank in `quizzes/`, answers hidden. |
| `/teachback 2` | Build the teach-back cards for session 2 from the TL;DRs of that batch's notes. |
| `/crossstudy beedy` | Make a condensed study pack of the *partner's* notes for cross-study nights (21–23 Oct). |
| `/lab T16` | Write a runnable lab script for a topic (DevNet Sandbox target, Docker lab container). |
| `/cheatsheet` | Rebuild `cheatsheet.md` from all "Exam traps" sections. |
| `/progress` | Run `scripts/progress.py` and summarise what is behind schedule against `data/pair-plan.csv`. |

## Definition of done for a topic

- [ ] Every **Must cover** checkbox ticked
- [ ] TL;DR card written
- [ ] At least 5 practice questions with explained answers
- [ ] Examples are runnable, full commands
- [ ] Sources listed; `⚠ verify` items resolved or listed
- [ ] `status: verified` set by the **owner**, not by Claude
