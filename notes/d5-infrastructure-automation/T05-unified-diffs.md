---
id: T05
title: "Unified diffs"
owner: Beedy
blueprint: "5.12"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T05 · Unified diffs

> Owner: **Beedy** · Blueprint: **5.12** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T05.01 · Diff header

**Must cover:**

- [ ] diff --git a/file b/file: which file is compared
- [ ] index abc123..def456: blob hashes (can ignore)
- [ ] --- a/file = old version; +++ b/file = new version
- [ ] /dev/null on one side = file was created or deleted

**Notes:**

<!-- TODO -->

### T05.02 · Hunk header

**Must cover:**

- [ ] Format: @@ -oldStart,oldCount +newStart,newCount @@
- [ ] Example @@ -10,7 +10,8 @@: 7 lines from old line 10 became 8 lines from new line 10
- [ ] Net change = newCount minus oldCount (here one line added)
- [ ] Optional text after the second @@ shows the enclosing function/section

**Notes:**

<!-- TODO -->

### T05.03 · Line prefixes

**Must cover:**

- [ ] Leading space: unchanged context line
- [ ] "-": line exists only in the old file (removed)
- [ ] "+": line exists only in the new file (added)
- [ ] A modified line shows as a "-" line followed by a "+" line

**Notes:**

<!-- TODO -->

### T05.04 · Context

**Must cover:**

- [ ] Default is 3 lines of context before and after each change
- [ ] A file can have several hunks, each with its own @@ header
- [ ] Context lines count towards both old and new line counts

**Notes:**

<!-- TODO -->

### T05.05 · Producing diffs

**Must cover:**

- [ ] git diff (unstaged), git diff --staged, git diff commit1 commit2
- [ ] git show <commit> shows the commit diff
- [ ] diff -u old.txt new.txt produces unified format outside Git

**Notes:**

<!-- TODO -->

### T05.06 · Exam angle

**Must cover:**

- [ ] Read a config diff and state what changed (e.g. VLAN added, IP changed)
- [ ] Count added/removed lines; work out what the new file looks like
- [ ] Know which side is old vs new from --- and +++

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
| T05.1 | Drill | Read @@ hunk headers + +/- lines | 20 | git diff output in Docker lab |

- Skip / low priority: Anything beyond reading a diff

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
