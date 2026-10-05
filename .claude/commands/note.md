---
description: Draft the full study note for one topic (e.g. /note T07)
argument-hint: <topic-id e.g. T07>
---
Draft the study note for topic **$ARGUMENTS**.

1. Look up $ARGUMENTS in `data/topics.csv` to get `note_path`, owner, blueprint items, CBT coverage and skip list. Read the existing note at that path; it has front matter and a pre-filled **Must cover** checklist per concept ID.
2. Read the matching rows in `data/concepts.csv`, `data/study-aids.csv`, `data/blueprint-map.csv` (for the gap/action text) and `data/top-ups.csv` (if the topic appears there).
3. Research with official sources (developer.cisco.com, Cisco docs, RFCs, Python docs, Webex/Meraki docs) whenever the topic is platform-specific or version-sensitive. Keep the URLs.
4. Fill the note following CLAUDE.md:
   - Under each `### TXX.NN` concept, keep the checklist, tick `[x]` every item you explain, and write point-form **Notes:**.
     - From first principles for new areas.
     - Straight to exam angle for the owner's home-turf topics.
   - `## Exam traps`: at least 5 crisp traps (confused pairs, exact syntax, scenario → answer).
   - `## Examples`: full runnable commands/code (curl, Python requests/ncclient/SDK, Docker). Target DevNet Sandbox hosts where relevant, with credentials read from env vars.
   - `## Practice questions`: 6-8 original exam-style Qs (mix of MCQ, drag-and-drop-as-ordering, complete-the-code). Answer + one-line explanation inside `<details>`.
   - `## TL;DR (teach-back card)`: 3 key points + 1 trap, written last.
   - `## Sources`: the URLs actually used. `## To verify`: every `⚠ verify` item.
5. Do NOT claim what the CBT video says; only reference it as a study aid.
6. Set front matter `status: drafted` (leave `confidence` for the owner).
7. Show a short summary: concepts covered (x/y ticked), number of Qs, ⚠ items. Suggest the commit message `$ARGUMENTS: draft notes` but do not commit unless asked.
