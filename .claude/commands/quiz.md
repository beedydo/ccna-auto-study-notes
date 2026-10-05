---
description: Generate exam-style practice questions for a topic or batch (e.g. /quiz T16 or /quiz batch-2)
argument-hint: <topic-id | batch-N | domain dN | partner>
---
Build a practice question bank for **$ARGUMENTS**.

- Topic ID → that topic. `batch-N` → topics whose `teach_back` date is teach-back N (1=2026-10-08, 2=2026-10-12, 3=2026-10-16, 4=2026-10-20) in `data/topics.csv`. `dN` → topics whose `primary_domain` is DN. `partner` → all topics NOT owned by the person running this (ask who if unclear).
- Base questions on the notes in this repo (and their concept checklists), not on memory alone. If a note is still `not-started`, use `data/concepts.csv` as scope.
- 10 questions per topic for single topics, ~3 per topic for batches/domains. Mix: single answer, multiple answer ("choose two"), ordering (e.g. git workflow, auth → call → poll), complete-the-code (requests, ncclient, Dockerfile, Ansible), interpret-output (RESTCONF JSON, NETCONF rpc-reply, unified diff, HTTP response).
- Original questions only: never reproduce real exam/dump questions.
- Write to `quizzes/<arg>.md`: questions first, then answers in `<details>` with a one-line why and the concept ID it tests (e.g. T16.05).
- After writing, offer to run it interactively: ask one question at a time, wait for the answer, score, and at the end list weak concept IDs to log in `data/practice-log.csv`.
