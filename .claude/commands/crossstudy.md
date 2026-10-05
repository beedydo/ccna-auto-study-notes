---
description: Build a condensed study pack of the partner's notes for cross-study nights (e.g. /crossstudy beedy)
argument-hint: <beedy|bob> (the person who will STUDY)
---
Create `quizzes/crossstudy-$ARGUMENTS.md` for **$ARGUMENTS** to learn the partner's topics on 21-23 Oct.

- Partner topics = rows in `data/topics.csv` where owner != $ARGUMENTS, grouped by `cross_study` date (21, 22, 23 Oct).
- Per topic: TL;DR card, the 5 most important exam traps, a 6-line "how it works" from first principles (the studier is new to these), and 3 quick check Qs with hidden answers.
- Source only from the partner's notes in this repo; where a note is not yet `drafted`, flag it at the top as "partner note missing" and use `data/concepts.csv` scope with clearly marked placeholders.
- Target: each day's section readable in ~20 minutes.
