---
id: T05
title: "Unified diffs"
owner: Beedy
blueprint: "5.12"
primary_domain: D5
cbt_coverage: "Full"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T05 · Unified diffs

> Owner: **Beedy** · Blueprint: **5.12** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

- **Header:** `--- a/file` = old, `+++ b/file` = new. `/dev/null` on the `---` side = file created; on the `+++` side = file deleted.
- **Hunk header** `@@ -4,15 +4,17 @@`: old file has 15 lines from line 4, new file has 17 lines from line 4 → net **+2**. A missing count means 1. Text after `@@` is only the enclosing section label.
- **Prefixes:** space = context (counts on both sides), `-` = removed, `+` = added. A changed line = `-` then `+`. Default context is 3 lines; changes close together merge into one hunk.
- **Trap:** counts include context lines, so `-6,2 +6,4` means +2 lines, not 4 added. The prefix is only the first character: ` name VOICE` is context, and `+ name CAMERAS` is an added line.

## Concepts

### T05.01 · Diff header

**Must cover:**

- [x] diff --git a/file b/file: which file is compared
- [x] index abc123..def456: blob hashes (can ignore)
- [x] --- a/file = old version; +++ b/file = new version
- [x] /dev/null on one side = file was created or deleted

**Notes:**

- A Git diff = **file header** (which file, old vs new) + one or more **hunks** (the changed regions).
- Real header (modified file):

```
diff --git a/switch.cfg b/switch.cfg      <- comparing this file: a/ = old, b/ = new
index de65e08..76a0304 100644            <- old blob hash..new blob hash, file mode (ignore)
--- a/switch.cfg                         <- OLD version ("from" file)
+++ b/switch.cfg                         <- NEW version ("to" file)
```

- **Mnemonic:** `-` / `a` = before; `+` / `b` = after. Same symbols as the line prefixes.
- **Created file:** `new file mode 100644` + `--- /dev/null` + `+++ b/banner.cfg` → hunk `@@ -0,0 +1 @@`.
- **Deleted file:** `deleted file mode 100644` + `--- a/legacy.txt` + `+++ /dev/null` → hunk `@@ -1 +0,0 @@`.
- `/dev/null` = "nothing on this side". Only on the `---`/`+++` lines; `diff --git a/x b/x` keeps the real name.
- Plain `diff -u` (no Git) has no `diff --git`/`index` lines. `---`/`+++` show filename **plus timestamp**.

### T05.02 · Hunk header

**Must cover:**

- [x] Format: @@ -oldStart,oldCount +newStart,newCount @@
- [x] Example @@ -10,7 +10,8 @@: 7 lines from old line 10 became 8 lines from new line 10
- [x] Net change = newCount minus oldCount (here one line added)
- [x] Optional text after the second @@ shows the enclosing function/section

**Notes:**

- Format: `@@ -oldStart,oldCount +newStart,newCount @@ [section]`
  - `-` part = range in the **old** file; `+` part = range in the **new** file.
  - `start` = first line number shown in the hunk (context included).
  - `count` = number of lines the hunk covers on that side (context + changed lines).
- Worked example (real drill output):

```
@@ -4,15 +4,17 @@ vlan 10
```

  - Old file: 15 lines starting at line 4 (lines 4–18).
  - New file: 17 lines starting at line 4 (lines 4–20).
  - Net: 17 − 15 = **+2 lines** in this hunk. Check: 4 `+` and 2 `-` lines → +2 ✔.
- **Count omitted = 1:** `@@ -1 +1 @@` = one line on each side.
- **Count 0** = no lines on that side: `-0,0` = new file, `+0,0` = file emptied/deleted.
- Text after the second `@@` = the **enclosing function/section**, for orientation only (not part of the change).
  - Git finds it by searching **upwards** from the hunk for a line starting at column 0 (letter, `_`, `$`). Config file → nearest `vlan 10`/`interface …` line; Python without a diff driver → may show `import requests`, not the function. ⚠ verify per language driver.
- Exam shortcut: **new start − old start** = net lines added/removed by **earlier** hunks in the same file.

### T05.03 · Line prefixes

**Must cover:**

- [x] Leading space: unchanged context line
- [x] "-": line exists only in the old file (removed)
- [x] "+": line exists only in the new file (added)
- [x] A modified line shows as a "-" line followed by a "+" line

**Notes:**

| Prefix | Meaning | Counts toward |
|---|---|---|
| ` ` (space) | unchanged context | old **and** new count |
| `-` | only in **old** file (removed) | old count |
| `+` | only in **new** file (added) | new count |

- **Modified line** = `-` old line followed by `+` new line. There is no "changed" symbol.

```
- switchport access vlan 10
+ switchport access vlan 30
```

- Read as: "access VLAN on Gi1/0/2 changed from 10 to 30".
- `\ No newline at end of file` = marker, not content. Means last line has no trailing newline.
- Don't confuse the prefix with the content: ` name CAMERAS` (IOS indent) shows as `+ name CAMERAS`. First char is the prefix; rest is the line.

### T05.04 · Context

**Must cover:**

- [x] Default is 3 lines of context before and after each change
- [x] A file can have several hunks, each with its own @@ header
- [x] Context lines count towards both old and new line counts

**Notes:**

- Default **3 lines** of context before and after each change (`-U<n>` / `--unified=<n>` changes it; `diff.context` config).
- Changes close together (≤ 2×context lines apart) **merge into one hunk**. Further apart → separate hunks, each with its own `@@` header.
- Same edit with `git diff --unified=1` → 3 hunks (real output):

```
@@ -6,2 +6,4 @@ vlan 20
@@ -12,3 +14,3 @@ interface GigabitEthernet1/0/1
@@ -16,3 +18,3 @@ ntp server 10.0.0.1
```

  - Hunk 1 adds 2 lines → every later new-start is shifted **+2** (12→14, 16→18).
- Context lines are counted in **both** oldCount and newCount.
  - `-6,2 +6,4`: 2 context lines (` name VOICE`, ` !`) + 2 added = 4 new, 2 old.

### T05.05 · Producing diffs

**Must cover:**

- [x] git diff (unstaged), git diff --staged, git diff commit1 commit2
- [x] git show <commit> shows the commit diff
- [x] diff -u old.txt new.txt produces unified format outside Git

**Notes:**

- Which `git diff` compares what (`git diff` / `--staged` / `<c1> <c2>` / `HEAD`) → see the diff matrix in [T04.07](T04-git-version-control.md#t0407--commands-inspect).
- `git show <commit>` → commit metadata + its diff vs parent.
- `git diff --stat` → summary only: `switch.cfg | 6 ++++--` (4 insertions, 2 deletions).
- Outside Git: `diff -u old.cfg new.cfg` → same unified format, no `diff --git`/`index` lines. Plain `diff` (no `-u`) = **normal** format (`4a5`, `<`/`>`), not unified.
- `git diff --unified=0` → no context, just the changes.

### T05.06 · Exam angle

**Must cover:**

- [x] Read a config diff and state what changed (e.g. VLAN added, IP changed)
- [x] Count added/removed lines; work out what the new file looks like
- [x] Know which side is old vs new from --- and +++

**Notes:**

- **Three-step read:**
  1. `---` / `+++` → which file; old vs new (or `/dev/null` = created/deleted).
  2. `@@` → where, and net line change (newCount − oldCount).
  3. Pair `-` with following `+` → "X changed to Y"; lone `+` = added; lone `-` = removed.
- Rebuild **new** file: keep ` ` and `+` lines, drop `-` lines. Rebuild **old**: keep ` ` and `-`, drop `+`.
- Typical answers: "VLAN 30 added", "access port moved from VLAN 10 to 30", "SNMP community changed", "TLS verification turned on (`verify=False` → `verify=True`)", "API path moved v1 → v2".
- Count: `+` lines = insertions, `-` lines = deletions (what `--stat` reports). A modification = 1 insertion + 1 deletion.

## Exam traps

- **Old vs new:** `-`/`---`/`a/` = old; `+`/`+++`/`b/` = new. Don't read `-` as "minus a line from the new file".
- **Counts include context:** `@@ -10,7 +10,8 @@` ≠ "8 lines added". It means net +1 line.
- **Omitted count = 1:** `@@ -1 +1 @@` = one line each side, not zero.
- **`/dev/null` side:** `--- /dev/null` = **new** file; `+++ /dev/null` = **deleted** file. `-0,0` / `+0,0` = empty on that side.
- **Modified line** = a `-` and a `+` pair. `--stat` counts it as 1 insertion + 1 deletion.
- **Text after `@@`** (e.g. `@@ ... @@ vlan 10`) is context for orientation, not a changed line.
- **New start ≠ old start** in later hunks = earlier hunks added/removed lines (e.g. +2 shift: `-12` → `+14`).
- **`diff` vs `diff -u`:** only `-u` produces unified format (`---`/`+++`/`@@`). Plain `diff` = normal format (`<`/`>`).
- **`@@@` (three @)** = combined diff of a merge commit (two parents). Not a normal two-file diff.
- **Which `git diff`:** unstaged = `git diff`; staged = `git diff --staged`; one commit = `git show <sha>`.

## Examples

Drill T05.1. Builds a switch config, changes it (adds VLAN 30, moves an access port, changes SNMP), deletes one file and creates another, then prints the diff. Needs only `git`; or run it in the lab container: `docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/` then `docker run --rm --interactive --tty --volume "$(pwd)":/work ccna-auto-lab:latest`.

```bash
mkdir -p ~/t05-drill && cd ~/t05-drill && rm -rf diffdemo
git init --initial-branch=main diffdemo && cd diffdemo
git config user.name "Beedy"
git config user.email "beedy@example.com"
git config commit.gpgsign false

cat > switch.cfg <<'CFG'
hostname SW1
!
vlan 10
 name USERS
vlan 20
 name VOICE
!
interface GigabitEthernet1/0/1
 description Uplink
 switchport mode trunk
!
interface GigabitEthernet1/0/2
 switchport access vlan 10
!
ntp server 10.0.0.1
logging host 10.0.0.50
snmp-server community public RO
end
CFG
echo "old" > legacy.txt
git add .
git commit --message "Baseline"

# Change the config (BSD/macOS and GNU sed both accept -i.bak)
sed -i.bak \
  -e 's/ name VOICE/ name VOICE\nvlan 30\n name CAMERAS/' \
  -e 's/ switchport access vlan 10/ switchport access vlan 30/' \
  -e 's/^snmp-server community public RO$/snmp-server community N3tOps RO/' \
  switch.cfg && rm switch.cfg.bak
git rm --quiet legacy.txt
printf 'banner motd ^Authorised only^\n' > banner.cfg
git add .

git diff --staged                           # full diff, default 3 context lines
git diff --staged --unified=1 -- switch.cfg # same change split into 3 hunks
git diff --staged --stat                    # summary
```

Output (Git 2.54):

```diff
diff --git a/banner.cfg b/banner.cfg
new file mode 100644
index 0000000..57fc3dc
--- /dev/null
+++ b/banner.cfg
@@ -0,0 +1 @@
+banner motd ^Authorised only^
diff --git a/legacy.txt b/legacy.txt
deleted file mode 100644
index 3367afd..0000000
--- a/legacy.txt
+++ /dev/null
@@ -1 +0,0 @@
-old
diff --git a/switch.cfg b/switch.cfg
index de65e08..76a0304 100644
--- a/switch.cfg
+++ b/switch.cfg
@@ -4,15 +4,17 @@ vlan 10
  name USERS
 vlan 20
  name VOICE
+vlan 30
+ name CAMERAS
 !
 interface GigabitEthernet1/0/1
  description Uplink
  switchport mode trunk
 !
 interface GigabitEthernet1/0/2
- switchport access vlan 10
+ switchport access vlan 30
 !
 ntp server 10.0.0.1
 logging host 10.0.0.50
-snmp-server community public RO
+snmp-server community N3tOps RO
 end
```

`--unified=1` and `--stat` output:

```diff
@@ -6,2 +6,4 @@ vlan 20
  name VOICE
+vlan 30
+ name CAMERAS
 !
@@ -12,3 +14,3 @@ interface GigabitEthernet1/0/1
 interface GigabitEthernet1/0/2
- switchport access vlan 10
+ switchport access vlan 30
 !
@@ -16,3 +18,3 @@ ntp server 10.0.0.1
 logging host 10.0.0.50
-snmp-server community public RO
+snmp-server community N3tOps RO
 end
```

```
 banner.cfg | 1 +
 legacy.txt | 1 -
 switch.cfg | 6 ++++--
 3 files changed, 5 insertions(+), 3 deletions(-)
```

Same comparison without Git:

```bash
cd ~/t05-drill/diffdemo
git show HEAD:switch.cfg > ../old.cfg
cp switch.cfg ../new.cfg
diff -u ../old.cfg ../new.cfg
```

```diff
--- ../old.cfg	2026-10-08 16:43:18
+++ ../new.cfg	2026-10-08 16:43:18
@@ -4,15 +4,17 @@
...
```

Python script diff (the kind used in code review questions, T46). Run this after the drill above, in the same repo:

```bash
cd ~/t05-drill/diffdemo
git commit --quiet --message "Add VLAN 30"

cat > api.py <<'EOF'
import requests


def get_devices(host, token):
    url = f"https://{host}/api/v1/devices"
    headers = {"X-Auth-Token": token}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()


def get_interfaces(host, token):
    url = f"https://{host}/api/v1/interfaces"
    headers = {"X-Auth-Token": token}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()
EOF
git add api.py
git commit --quiet --message "Add API helpers"

sed -i.bak \
  -e 's#/api/v1/interfaces#/api/v2/interfaces#' \
  -e 's#verify=False)$#verify=True)#' \
  api.py && rm api.py.bak
git diff api.py
```

Output:

```diff
@@ -4,12 +4,12 @@ import requests
 def get_devices(host, token):
     url = f"https://{host}/api/v1/devices"
     headers = {"X-Auth-Token": token}
-    response = requests.get(url, headers=headers, verify=False)
+    response = requests.get(url, headers=headers, verify=True)
     return response.json()
 
 
 def get_interfaces(host, token):
-    url = f"https://{host}/api/v1/interfaces"
+    url = f"https://{host}/api/v2/interfaces"
     headers = {"X-Auth-Token": token}
-    response = requests.get(url, headers=headers, verify=False)
+    response = requests.get(url, headers=headers, verify=True)
     return response.json()
```

- Reading: TLS certificate verification turned on in both functions; interfaces endpoint moved from v1 to v2. 12 → 12 lines, net 0, but 3 lines modified.

## Practice questions

**Q1.** A diff contains `@@ -22,6 +22,9 @@`. What does it mean?
A. Lines 22–28 were deleted  B. 9 lines were added at line 22  C. A 6-line region starting at line 22 in the old file is now a 9-line region starting at line 22 in the new file  D. The file grew from 6 to 9 lines in total

<details><summary>Answer</summary>

**C.** The counts are per hunk and include context lines. The net change is +3 lines for this hunk only. (T05.02)
</details>

**Q2.** Refer to the diff:

```diff
--- a/router.cfg
+++ b/router.cfg
@@ -8,4 +8,4 @@ interface GigabitEthernet2
  description WAN
- ip address 192.0.2.1 255.255.255.0
+ ip address 198.51.100.1 255.255.255.0
  negotiation auto
 !
```

What changed?
A. A new interface was added  B. The IP address on GigabitEthernet2 changed from 192.0.2.1 to 198.51.100.1  C. The IP address changed from 198.51.100.1 to 192.0.2.1  D. The description was removed

<details><summary>Answer</summary>

**B.** `-` = old and `+` = new, so a `-`/`+` pair is a modification. `interface GigabitEthernet2` after `@@` is the section label. (T05.03)
</details>

**Q3.** A diff shows `--- /dev/null` and `+++ b/playbook.yml`. What happened to `playbook.yml`?
A. It was deleted  B. It was created  C. It was renamed  D. It was emptied but kept

<details><summary>Answer</summary>

**B.** The old side is `/dev/null`, meaning nothing existed before. `+++ /dev/null` would mean deleted. (T05.01)
</details>

**Q4.** In a hunk with header `@@ -5,7 +5,6 @@`, there are 5 context lines. How many lines start with `-` and how many with `+`?
A. 2 `-`, 1 `+`  B. 1 `-`, 0 `+`  C. 7 `-`, 6 `+`  D. 0 `-`, 1 `+`

<details><summary>Answer</summary>

**A.** Old = 5 context + 2 removed = 7. New = 5 context + 1 added = 6. Context counts on both sides. (T05.04)
</details>

**Q5.** Arrange these parts of a Git diff in the order they appear: `@@ -1,3 +1,4 @@` · `+++ b/app.py` · `diff --git a/app.py b/app.py` · `+import os` · `--- a/app.py` · `index 1a2b3c4..5d6e7f8 100644`

<details><summary>Answer</summary>

`diff --git a/app.py b/app.py` → `index 1a2b3c4..5d6e7f8 100644` → `--- a/app.py` → `+++ b/app.py` → `@@ -1,3 +1,4 @@` → `+import os`. (T05.01, T05.02)
</details>

**Q6.** Refer to the hunk:

```diff
@@ -3,4 +3,4 @@ def connect():
     session = requests.Session()
-    session.auth = ("admin", "C1sco12345")
+    session.auth = (os.environ["USER"], os.environ["PASS"])
     session.verify = True
     return session
```

Which statement best describes the change?
A. Certificate verification was disabled  B. Hard-coded credentials were replaced with environment variables  C. A new function was added  D. Two lines were added

<details><summary>Answer</summary>

**B.** One `-`/`+` pair is a single modified line. `def connect():` is the section label, not a new function. (T05.03, T05.06)
</details>

**Q7.** Complete the command to produce a unified diff of two files outside Git:

```bash
diff ____ old.cfg new.cfg
```

<details><summary>Answer</summary>

**`-u`.** Without `-u`, `diff` prints the normal format with `<`/`>` lines and `4a5`-style change commands. (T05.05)
</details>

**Q8.** A file has two hunks: `@@ -2,6 +2,9 @@` and then `@@ -20,4 +23,4 @@`. Why does the second hunk start at line 23 in the new file?
A. Git renumbers hunks randomly  B. The first hunk added a net 3 lines, which shifts later lines down by 3  C. Three context lines were removed  D. The second hunk added 3 lines

<details><summary>Answer</summary>

**B.** 9 − 6 = +3 from hunk 1, so old line 20 becomes new line 23. Hunk 2 itself is net 0 (4 → 4). (T05.04)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T05.1 | Drill | Read @@ hunk headers + +/- lines | 20 | git diff output in Docker lab |

- Skip / low priority: Anything beyond reading a diff

## Sources

- git-diff, generating patch text (diff --git header, index line, new/deleted file mode, `-U` default 3, function name in hunk header, combined `@@@`): https://git-scm.com/docs/git-diff
- GNU diffutils, Detailed Description of Unified Format (hunk header, omitted count = 1, empty hunk start, line prefixes): https://www.gnu.org/software/diffutils/manual/html_node/Detailed-Unified.html
- gitattributes, Defining a custom hunk-header: https://git-scm.com/docs/gitattributes#_defining_a_custom_hunk_header
- Cisco 200-901 v1.1 exam topics (5.12): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## To verify

- ⚠ Open flag (HANDOVER §6): it's unconfirmed whether the CBT Git Diff video teaches reading `@@` hunk headers. Use drill T05.1 and this note regardless.
- ⚠ Text after the second `@@`: without a language diff driver, Git uses the nearest earlier line starting at column 0. That's why the Python example shows `import requests` instead of the function name. Setting `*.py diff=python` in `.gitattributes` changes it. For the exam, treat it as an orientation label only.
- The drill output in **Examples** came from a real run on Git 2.54. Your blob hashes and timestamps will differ.
