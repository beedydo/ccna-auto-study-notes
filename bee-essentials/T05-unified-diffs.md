# T05 · Unified diffs: essentials

> Blueprint 5.12 · Full note: [bee/T05-unified-diffs.md](../bee/T05-unified-diffs.md) · Teach-back 2026-10-11

## In one picture
There is no image for T05 yet, so here is the shape of every Git diff as a labelled sketch:

```
diff --git a/switch.cfg b/switch.cfg     <- FILE HEADER: which file (a/ = old, b/ = new)
index de65e08..76a0304 100644           <-   blob hashes and file mode (ignore)
--- a/switch.cfg                        <-   OLD version ("before")
+++ b/switch.cfg                        <-   NEW version ("after")
@@ -4,15 +4,17 @@ vlan 10                 <- HUNK HEADER: old 15 lines from line 4 became
                                             new 17 lines from line 4; "vlan 10" is just a label
  name USERS                            <- space  = context, unchanged, in both files
+vlan 30                                <- plus   = added, only in the new file
- switchport access vlan 10             <- minus  = removed, only in the old file
+ switchport access vlan 30             <- minus then plus = one line changed
```
*Read it top to bottom: the file header tells you which file and which side is old or new, each `@@` line opens one changed region, and the first character of every line after that tells you what happened to it.*

## The big idea
A unified diff is like a "track changes" view printed as plain text. Instead of colours, it uses one symbol at the start of each line: a minus for deleted, a plus for added, and a space for "unchanged, shown so you can find your place". Blueprint 5.12 asks you to read one and say what changed, for example "VLAN 30 was added" or "the IP address changed". Once you can read the `@@` line and the first character of each line, these questions become free marks.

## What you need to know

### 1. The file header: which file, and which side is old
- A Git diff has two parts: a **file header** that names the file, and one or more **hunks** (the changed regions of that file).
- `diff --git a/switch.cfg b/switch.cfg` says which file is being compared. `a/` is the old version and `b/` is the new version.
- The `index de65e08..76a0304 100644` line holds the old and new **blob hashes** and the file mode. You can ignore it.
- `--- a/file` is the **old** version (the "from" file), and `+++ b/file` is the **new** version (the "to" file).
- Memory hook: minus and `a` mean **before**; plus and `b` mean **after**. These are the same symbols used on the lines below.
- `/dev/null` means "nothing on this side":

| You see | Meaning | Matching hunk header |
|---|---|---|
| `new file mode 100644`, `--- /dev/null`, `+++ b/banner.cfg` | the file was **created** | `@@ -0,0 +1 @@` |
| `deleted file mode 100644`, `--- a/legacy.txt`, `+++ /dev/null` | the file was **deleted** | `@@ -1 +0,0 @@` |

- `/dev/null` appears only on the `---` and `+++` lines; the `diff --git a/x b/x` line keeps the real file name.
- A plain `diff -u` made outside Git has no `diff --git` or `index` lines, and its `---`/`+++` lines show the filename **plus a timestamp**.

### 2. The hunk header: the `@@` line
- The format is `@@ -oldStart,oldCount +newStart,newCount @@ [section]`.
- The minus part describes the region in the **old** file, and the plus part describes it in the **new** file.
- The **start** is the first line number shown in the hunk, context included. The **count** is how many lines the hunk covers on that side, counting both context and changed lines.
- Worked example, `@@ -4,15 +4,17 @@ vlan 10`:
  - In the old file, the hunk covers 15 lines starting at line 4 (lines 4 to 18).
  - In the new file, it covers 17 lines starting at line 4 (lines 4 to 20).
  - The net change is 17 minus 15, which is **+2 lines** for this hunk. Check: it has 4 plus lines and 2 minus lines, and 4 minus 2 is 2.
- When a count is **left out, it means 1**: `@@ -1 +1 @@` is one line on each side, not zero.
- A **count of 0** means no lines on that side: `-0,0` is a new file and `+0,0` is a file that was emptied or deleted.
- The text after the second `@@` (like `vlan 10`) is the **enclosing function or section**, there only to help you find your place. It is not part of the change.
  - Git finds that label by searching upwards from the hunk for the nearest line starting in column 0. In a config file that is usually a `vlan` or `interface` line. In Python without a language diff driver it may show `import requests` rather than the function name. ⚠ verify per language driver.
- Shortcut: if a later hunk's new start is different from its old start, the **earlier** hunks added or removed lines. The difference is the net shift.

### 3. Line prefixes: the first character tells the story
| First character | Meaning | Counts toward |
|---|---|---|
| a space | unchanged **context** line | both old and new counts |
| `-` | line exists only in the **old** file (removed) | old count only |
| `+` | line exists only in the **new** file (added) | new count only |

- There is no special "changed" symbol. A **modified line** appears as a `-` line followed by a `+` line:

```
- switchport access vlan 10
+ switchport access vlan 30
```

- Read that pair as "the access VLAN changed from 10 to 30".
- `\ No newline at end of file` is a marker, not content. It just says the last line has no trailing newline.
- Only the **first character** is the prefix; the rest is the actual line. Cisco configs indent sub-commands with a space, so an added ` name CAMERAS` shows as `+ name CAMERAS`, and an unchanged ` name VOICE` shows with two leading spaces.
- **Exam-sim gap (from practice test review):**
  - A long **run of consecutive `-` lines** with few or no `+` lines means a block was deleted. A run of `+` lines means a block was added.
  - In `@@ -40,30 +40,2 @@`, the old side has 30 lines and the new side has 2, so about **28 lines were deleted** in that hunk.
  - Exam cue: "how do you recognise a large deleted block in unified diff output?" The answer is **many consecutive lines starting with `-`**.

### 4. Context lines and multiple hunks
- By default Git shows **3 lines of context** before and after each change. `-U<n>` or `--unified=<n>` changes that, and so does the `diff.context` setting.
- Changes that sit close together (within twice the context size) **merge into one hunk**. Changes further apart get separate hunks, each with its own `@@` header.
- The same edit shown with `git diff --unified=1` splits into three hunks:

```
@@ -6,2 +6,4 @@ vlan 20
@@ -12,3 +14,3 @@ interface GigabitEthernet1/0/1
@@ -16,3 +18,3 @@ ntp server 10.0.0.1
```

- The first hunk adds 2 lines, so every later hunk's new start is shifted by +2 (12 became 14, and 16 became 18).
- Context lines count on **both** sides. In `-6,2 +6,4`, there are 2 context lines plus 2 added lines, giving 4 on the new side and 2 on the old side. That is **+2**, not "4 added".

### 5. Producing diffs
- `git diff` shows unstaged changes, `git diff --staged` shows staged changes, and `git diff <c1> <c2>` compares two commits. The full matrix is in T04.
- `git show <commit>` prints a commit's metadata plus its diff against its parent.
- `git diff --stat` gives a summary only, for example `switch.cfg | 6 ++++--` meaning 4 insertions and 2 deletions.
- `git diff --unified=0` shows no context, only the changes.
- Outside Git, `diff -u old.cfg new.cfg` produces the same unified format. Plain `diff` without `-u` gives the older **normal** format with `<` and `>` lines and commands like `4a5`, which is not unified.

### 6. How to answer a diff question in three steps
1. Look at `---` and `+++` to find the file and which side is old or new. `/dev/null` means created or deleted.
2. Look at `@@` to find where the change is and the net line change (newCount minus oldCount).
3. Pair each `-` with the `+` that follows it to say "X changed to Y". A lone `+` is an addition and a lone `-` is a removal.

- To rebuild the **new** file, keep the space and `+` lines and drop the `-` lines. To rebuild the **old** file, keep the space and `-` lines and drop the `+` lines.
- `+` lines are **insertions** and `-` lines are **deletions**, which is what `--stat` reports. One modified line counts as 1 insertion and 1 deletion.
- Typical answers: "VLAN 30 added", "access port moved from VLAN 10 to 30", "SNMP community changed", "TLS verification turned on (`verify=False` became `verify=True`)", "API path moved from v1 to v2".
- A hunk like `@@ -4,12 +4,12 @@` can have net 0 lines yet still contain 3 modified lines, so don't assume "same count" means "no change".

## Exam traps (the ones that catch people)
- Looks like `-` means "take a line away from the new file", but it actually marks a line that exists only in the **old** file.
- Looks like `@@ -10,7 +10,8 @@` means 8 lines were added, but the counts include context, so it is a **net +1**.
- Looks like `@@ -1 +1 @@` has no lines, but a missing count means **1**.
- Looks like `--- /dev/null` means deleted, but a null **old** side means the file was **created**; `+++ /dev/null` is the deleted case.
- Looks like the text after `@@` (such as `vlan 10` or `def connect():`) was changed or added, but it is only an orientation label.
- Looks like a later hunk is misnumbered when new start differs from old start, but earlier hunks shifted the lines (for example `-12` becoming `+14` after a +2 hunk).
- Looks like any `diff` output is unified, but only `diff -u` gives `---`, `+++` and `@@`; plain `diff` uses `<` and `>`.
- Looks like `@@@` is a typo, but three `@` signs mark a **combined diff** of a merge commit with two parents.

## Quick self-check
<details><summary>Q1. What does `@@ -22,6 +22,9 @@` mean?</summary>A 6-line region from old line 22 is now a 9-line region from new line 22, so net +3 for this hunk; counts include context.</details>
<details><summary>Q2. `--- /dev/null` and `+++ b/playbook.yml`: what happened to the file?</summary>It was created, because there was nothing on the old side.</details>
<details><summary>Q3. A hunk header is `@@ -5,7 +5,6 @@` with 5 context lines. How many `-` and `+` lines?</summary>2 minus and 1 plus: old is 5 + 2 = 7, new is 5 + 1 = 6.</details>
<details><summary>Q4. Which flag makes the `diff` command produce unified format outside Git?</summary>`-u`; without it you get the normal `<`/`>` format.</details>
<details><summary>Q5. Hunks `@@ -2,6 +2,9 @@` then `@@ -20,4 +23,4 @@`: why does the second start at 23?</summary>The first hunk added a net 3 lines (9 minus 6), which pushes later lines down by 3.</details>

## Cheat lines to say out loud
- "Minus, a, three dashes: before. Plus, b, three pluses: after."
- "The @@ counts include context, so subtract to get the net change."
- "No count means one; zero count means nothing on that side."
- "A change is a minus followed by a plus; there is no change symbol."
- "Text after the @@ is a signpost, not a change."
