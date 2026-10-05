---
description: Fact-check a drafted topic note against official sources (e.g. /verify T15)
argument-hint: <topic-id>
---
Verify the note for **$ARGUMENTS** (path from `data/topics.csv` → `note_path`).

1. Read the note fully. List every factual claim that is platform/version specific: ports, URLs/endpoints, headers, status codes, command flags, SDK method names, RFC behaviour, default values.
2. Check each claim against official docs/RFCs (search/fetch). Fix wrong claims in place. Mark anything you cannot confirm with `⚠ verify` and list it under `## To verify` with what to check.
3. Check scope: every **Must cover** checkbox is genuinely explained; untick any that are not, and fill the gap.
4. Run any Python snippets that can run offline (parsing, unittest, data-structure code) to make sure they work; fix them.
5. Check the practice questions: one unambiguous correct answer each, explanation matches the notes, no copied/dump questions.
6. Report: fixes made, unconfirmed items, checklist completion. Do NOT set `status: verified`; only the owner does that after doing the Qs.
