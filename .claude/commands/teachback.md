---
description: Build the teach-back cards for a joint session (e.g. /teachback 2)
argument-hint: <1|2|3|4>
---
Prepare **teach-back $ARGUMENTS** (`teach-back/teach-back-$ARGUMENTS.md`).

- Topics: rows in `data/topics.csv` whose `teach_back` date matches session $ARGUMENTS (1=2026-10-08, 2=2026-10-12, 3=2026-10-16, 4=2026-10-20).
- Ask who is running this (Beedy or Bob) if not obvious from git config; fill only that person's section.
- For each of their topics: pull from the note's TL;DR and Exam traps → 3 key points, 1 exam trap, 1 question for the partner (with answer), max ~90 seconds of talking per topic. 12 minutes total per person, so be ruthless.
- If a note has no TL;DR yet, draft one from the note and flag it.
- Keep the "Weak IDs logged" list at the bottom for the session.
