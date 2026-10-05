---
id: T04
title: "Git + version control"
owner: Beedy
blueprint: "1.7, 1.8"
primary_domain: D1
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-05
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T04 · Git + version control

> Owner: **Beedy** · Blueprint: **1.7, 1.8** · CBT coverage: **Full** · Learn by 2026-10-05 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T04.01 · Version control

**Must cover:**

- [ ] Full history of every change: who, what, when and why (commit message)
- [ ] Rollback to any earlier version
- [ ] Parallel work through branches without overwriting each other
- [ ] Collaboration and review via a shared remote
- [ ] Enables automation: CI/CD pipelines trigger on commits

**Notes:**

<!-- TODO -->

### T04.02 · Version control

**Must cover:**

- [ ] Centralised (e.g. SVN): one central server holds the history; clients need it to commit
- [ ] Distributed (Git): every clone has the full history; commit offline, sync later
- [ ] Git trade-off: more resilient and faster locally, but you must push/pull to share

**Notes:**

<!-- TODO -->

### T04.03 · Git model

**Must cover:**

- [ ] Working directory: the files you edit
- [ ] Staging area (index): changes selected for the next commit (git add)
- [ ] Local repository (.git): committed snapshots
- [ ] Remote repository (e.g. origin on GitHub): shared copy you push to / pull from

**Notes:**

<!-- TODO -->

### T04.04 · Git model

**Must cover:**

- [ ] Untracked: new file Git does not know about
- [ ] Modified: tracked file changed but not staged
- [ ] Staged: change added to the index
- [ ] Committed: saved in the repository; each commit has a SHA-1 hash
- [ ] HEAD = pointer to the current commit/branch

**Notes:**

<!-- TODO -->

### T04.05 · Commands: start

**Must cover:**

- [ ] git init: create a new repo in the current folder
- [ ] git clone <url>: copy a remote repo, sets remote "origin"
- [ ] git config --global user.name / user.email: identity on commits
- [ ] git remote add origin <url>; git remote -v lists remotes

**Notes:**

<!-- TODO -->

### T04.06 · Commands: change

**Must cover:**

- [ ] git add <file> or git add .: stage changes
- [ ] git rm <file>: delete from disk and stage the deletion
- [ ] git rm --cached <file>: stop tracking but keep the file on disk (e.g. before adding to .gitignore)
- [ ] git mv old new: rename and stage
- [ ] git commit -m "msg": commit staged changes; git commit -a -m stages tracked files automatically

**Notes:**

<!-- TODO -->

### T04.07 · Commands: inspect

**Must cover:**

- [ ] git status: which files are untracked / modified / staged
- [ ] git log, git log --oneline: commit history
- [ ] git show <commit>: details and diff of one commit
- [ ] git diff: working directory vs staging area
- [ ] git diff --staged (or --cached): staging area vs last commit

**Notes:**

<!-- TODO -->

### T04.08 · Commands: sync

**Must cover:**

- [ ] git push origin <branch>: upload local commits
- [ ] git fetch: download remote commits but do not change your branch
- [ ] git pull = git fetch + git merge (or rebase if configured)

**Notes:**

<!-- TODO -->

### T04.09 · Branching

**Must cover:**

- [ ] git branch: list; git branch <name>: create
- [ ] git checkout <name> or git switch <name>: move to a branch
- [ ] git checkout -b <name> / git switch -c <name>: create and switch
- [ ] git branch -d <name>: delete a merged branch

**Notes:**

<!-- TODO -->

### T04.10 · Merging

**Must cover:**

- [ ] git merge <branch>: merge into the current branch
- [ ] Fast-forward: no new commit, the pointer just moves ahead
- [ ] Merge commit: created when both branches have new commits
- [ ] Rebase (awareness): replays your commits on top of another branch for a linear history

**Notes:**

<!-- TODO -->

### T04.11 · Conflicts

**Must cover:**

- [ ] Conflict = both branches changed the same lines
- [ ] Markers: <<<<<<< HEAD (your version) ======= (theirs) >>>>>>> branch
- [ ] Resolve: edit the file, remove markers, git add, then git commit

**Notes:**

<!-- TODO -->

### T04.12 · Undo

**Must cover:**

- [ ] git reset --soft: move HEAD, keep changes staged
- [ ] git reset --mixed (default): move HEAD, unstage changes, keep files
- [ ] git reset --hard: discard changes entirely
- [ ] git revert <commit>: new commit that undoes an old one; safe on shared branches
- [ ] git restore <file> / git checkout -- <file>: discard working-directory changes

**Notes:**

<!-- TODO -->

### T04.13 · Other

**Must cover:**

- [ ] .gitignore: patterns of files Git should not track (secrets, venv, build output)
- [ ] git stash / git stash pop: shelve uncommitted changes temporarily
- [ ] git tag v1.0: label a release commit
- [ ] Fork + pull request: propose changes to a repo you do not own

**Notes:**

<!-- TODO -->

### T04.14 · Exam angle

**Must cover:**

- [ ] "Which command…" questions are the main format
- [ ] Ordering a workflow: clone > branch > edit > add > commit > push > pull request > merge
- [ ] Classic pairs: fetch vs pull, reset vs revert, rm vs rm --cached, diff vs diff --staged

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T04.1 | Video | Git Diff + Merging/Resolving Conflicts only (1.5x) | 12 | CBT: Getting Started with Git / Collaborate with Git |
| T04.2 | Drill | Command traps: rm vs rm --cached, reset vs revert, fetch vs pull, diff --staged | 20 | Docker lab |

- Skip / low priority: Whole CBT Git videos

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
