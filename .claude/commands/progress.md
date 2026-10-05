---
description: Show study progress vs the pair plan
---
Run `python3 scripts/progress.py` and then:

- Compare each topic's `status` with its `learn_by` / `teach_back` dates (today's date from the shell: `date +%F`).
- List overdue topics per person, what is due in the next 3 days (from `data/pair-plan.csv`), and the next joint session.
- If `data/practice-log.csv` has rows, show the latest score per domain and the 2 weakest domains per person.
- Suggest the single most valuable next action for tonight's 30 minutes.
