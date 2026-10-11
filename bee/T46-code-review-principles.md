---
id: T46
title: "Code review principles"
owner: Beedy
blueprint: "5.13"
primary_domain: D5
cbt_coverage: "None"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-19
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T46 · Code review principles

> Owner: **Beedy** · Blueprint: **5.13** · CBT coverage: **None** · Learn by 2026-10-19 · Teach-back 2026-10-20

![T46 at a glance: review process swim-lane, benefits, review types, CI vs human, giving feedback](../assets/T46/00-overview.png)

*Every T46 concept on one page. The top swim-lane is the process (numbers = order, red = the fix loop, blue = merge); the four panels below are purpose, types, what to look for and feedback. Red boxes are exam traps.*

## TL;DR (teach-back card)

- **Why (the 5.13 "benefits" answer):** find bugs and security issues **early** (cheaper than in prod) · **share knowledge** (no single person owns a module) · keep **style and standards** consistent · **mentor** and raise code quality over time. Never "faster code" or "replaces testing".
- **Where it sits:** branch → commit → push → **open PR/MR** → **CI** runs lint + tests → **human review** (Comment / Request changes / Approve) → author pushes fixes to the **same branch** → approve → **merge** (branch protection needs approval **and** green checks).
- **What and how:** small focused PRs; review design, logic, security, tests, naming; let **linters/CI own style**; feedback is about the **code, not the person**, specific, actionable, labelled blocking vs `Nit:`. Types: tool-assisted PR (most common), over-the-shoulder, **pair programming = continuous review while coding**, email patches.
- **Trap:** CI green ≠ reviewed. In PR #42 the linters flagged `verify=False` and the missing timeout, but only a human caught the hard-coded password, the `return` inside the loop and the missing tests.

## Concepts

Every section below points at one realistic review: **PR #42** on a small network-automation script. Files are in `labs/T46/`:

```
labs/T46/
├── base/                     main before the PR
│   ├── link_report.py        lists down interfaces from a saved RESTCONF reply
│   ├── test_link_report.py   one unit test
│   └── fixtures/interfaces.json
├── pr-42.diff                the change under review (planted issues)
├── review-42.txt             the review comments a good reviewer submits
├── pr-42-fix.diff            the author's fix-up commit after the review
└── review_pr.sh              builds a throwaway repo, applies the diff(s), runs the CI checks
```

**The starting point on `main`: `base/link_report.py`**

```python
"""Report interfaces that are down, from a saved RESTCONF reply (ietf-interfaces)."""
import json
import sys


def load_interfaces(path):
    """Return the interface list from a saved ietf-interfaces JSON reply."""
    with open(path, encoding="utf-8") as reply:
        data = json.load(reply)
    return data["ietf-interfaces:interfaces-state"]["interface"]


def down_interfaces(interfaces):
    """Return the names of interfaces whose oper-status is not 'up'."""
    return [intf["name"] for intf in interfaces if intf["oper-status"] != "up"]


def main(argv):
    interfaces = load_interfaces(argv[1])
    for name in down_interfaces(interfaces):
        print(f"DOWN    {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

**The pull request: `pr-42.diff`** ("link_report: live mode + error check"). Read it the T05 way first ([T05.06](T05-unified-diffs.md#t0506--exam-angle)), then look for problems before reading on.

```diff
diff --git a/link_report.py b/link_report.py
index cba917c..6029e0f 100644
--- a/link_report.py
+++ b/link_report.py
@@ -1,7 +1,10 @@
 """Report interfaces that are down, from a saved RESTCONF reply (ietf-interfaces)."""
 import json
+import os
 import sys
 
+import requests
+
 
 def load_interfaces(path):
     """Return the interface list from a saved ietf-interfaces JSON reply."""
@@ -10,15 +13,39 @@ def load_interfaces(path):
     return data["ietf-interfaces:interfaces-state"]["interface"]
 
 
+def get_live(h):
+    r = requests.get("https://" + h + "/restconf/data/ietf-interfaces:interfaces-state",
+                     auth=("admin", "FAKE-Passw0rd-not-real"),
+                     headers={"Accept": "application/yang-data+json"},
+                     verify=False)
+    return r.json()["ietf-interfaces:interfaces-state"]["interface"]
+
+
 def down_interfaces(interfaces):
     """Return the names of interfaces whose oper-status is not 'up'."""
     return [intf["name"] for intf in interfaces if intf["oper-status"] != "up"]
 
 
+def chk(d):
+    x = []
+    for i in d:
+        try:
+            if i["statistics"]["in-errors"] > 100:
+                x.append(i["name"])
+        except:
+            pass
+        return x
+
+
 def main(argv):
-    interfaces = load_interfaces(argv[1])
+    if argv[1].startswith("live:"):
+        interfaces = get_live(argv[1][5:])
+    else:
+        interfaces = load_interfaces(argv[1])
     for name in down_interfaces(interfaces):
         print(f"DOWN    {name}")
+    for name in chk(interfaces):
+        print(f"ERRORS  {name}")
     return 0
 
 
```

- Planted issues (the reviewer's job is to find them):

| # | Line(s) in the new file | Issue | Category |
|---|---|---|---|
| 1 | 18 `auth=("admin", "FAKE-Passw0rd-not-real")` | hard-coded credential (fake here), lands in Git history ([T29.01](T29-secrets-encryption-data-handling.md#t2901--secrets)) | security |
| 2 | 20 `verify=False` | TLS certificate check off → man-in-the-middle can read the password | security |
| 3 | 17 `requests.get(...)` | no `timeout=` → one dead device hangs the run ([T11.05](T11-python-requests-scripting.md#t1105--errors)) | robustness |
| 4 | 21 `r.json()[...]` | no `raise_for_status()` → a 401/404 shows up as a confusing `KeyError` | error handling |
| 5 | 35–36 `except: pass` | bare except swallows every error, even typos and Ctrl-C | error handling |
| 6 | 33 `> 100` | magic number | readability |
| 7 | 16, 29 `get_live(h)`, `chk(d)`, `x`, `i`, `r` | names don't say what they hold | readability |
| 8 | 37 `return x` | **logic bug**: indented inside the `for`, so it returns after the first interface | correctness |
| 9 | (no test file in the diff) | new functions without tests ([T32](T32-tdd-python-unit-tests.md)) | tests |
| 10 | 3 `import os` | unused import | style (linter) |

**Automated half of the review: real output of `bash labs/T46/review_pr.sh`** (linters from a throwaway venv, Python 3.14, ruff 0.17.0, flake8 7.4.1, pylint 4.1.2, bandit 1.9.4):

```
== git log --oneline main..HEAD
link_report: live mode + error check
== git diff --stat main...HEAD
 link_report.py | 29 ++++++++++++++++++++++++++++-
 1 file changed, 28 insertions(+), 1 deletion(-)
== py_compile (syntax only)
-- exit 0
== unittest
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
-- exit 0
== ruff check (E,F,B,S rules)
link_report.py:3:8: F401 [*] `os` imported but unused
link_report.py:17:9: S113 Probable use of `requests` call without timeout
link_report.py:20:22: S501 Probable use of `requests` call with `verify=False` disabling SSL certificate checks
link_report.py:35:9: E722 Do not use bare `except`
link_report.py:35:9: S110 `try`-`except`-`pass` detected, consider logging the exception
Found 5 errors.
[*] 1 fixable with `--fix`.
-- exit 1
== flake8
link_report.py:3:1: F401 'os' imported but unused
link_report.py:35:9: E722 do not use bare 'except'
-- exit 1
== pylint
************* Module link_report
link_report.py:17:8: W3101: Missing timeout argument for method 'requests.get' can cause your program to hang indefinitely (missing-timeout)
link_report.py:35:8: W0702: No exception type(s) specified (bare-except)
link_report.py:3:0: W0611: Unused import os (unused-import)
-- exit 4
== bandit (security)
20: B501 [HIGH] Call to requests with verify=False disabling SSL certificate checks, security issue.
17: B113 [MEDIUM] Call to requests without timeout
35: B110 [LOW] Try, Except, Pass detected.
-- exit 1
== program on the saved reply
DOWN    GigabitEthernet3
ERRORS  GigabitEthernet1
-- exit 0
```

- What CI proved: the code **compiles**, the **old test passes**, and four pattern problems exist (unused `os`, bare `except`, no timeout, `verify=False`).
- What CI missed: the password (bandit's hard-coded-password checks didn't match this tuple ⚠ verify), the early `return` (Gi4 with 120 errors is missing from the output, but nothing failed), the missing tests, the names, the magic number.

**Human half of the review: `review-42.txt`** (what Bob submits with **Request changes**)

```
Thanks for adding live mode, Beedy. Reading straight from the device is what the NOC asked for, and keeping load_interfaces() for saved replies means the old workflow still works.

Requesting changes for the 4 blocking items below; the rest are suggestions.

BLOCKING
1. link_report.py:18 (security) The password is hard-coded, so it ends up in Git history and in every clone. Please read it from the environment, e.g. os.environ["RESTCONF_USER"] / os.environ["RESTCONF_PASS"] (T29). The unused `import os` on line 3 suggests that was the plan.
2. link_report.py:20 (security) verify=False turns off TLS certificate checks, so a man-in-the-middle can read the credentials. Please keep verification on; if the lab device uses a private CA, pass its bundle path: verify=os.environ.get("RESTCONF_CA", True).
3. link_report.py:37 (bug) `return x` is indented inside the for loop, so chk() returns after the first interface. With fixtures/interfaces.json it reports Gi1 but misses Gi4 (120 errors). Dedent the return one level, and please add a test that has two interfaces over the threshold so this can't come back.
4. test_link_report.py (tests) The PR adds get_live() and chk() but no tests. Could you add unit tests for chk() (several errored interfaces, an interface without "statistics") and one for the live path with requests.get mocked (T32)?

SHOULD FIX
5. link_report.py:17 requests.get() has no timeout, so one dead device hangs the whole run. Suggest timeout=10 (a named constant), plus response.raise_for_status() so a 401/404 gives a clear error instead of a KeyError on r.json().
6. link_report.py:35 The bare `except: pass` hides every error, including typos and KeyboardInterrupt. If the goal is to skip interfaces without statistics (Loopback0), intf.get("statistics", {}).get("in-errors", 0) says that directly without any try/except.
7. link_report.py:41-42 A failed live call raises a traceback at the user. Catch requests.RequestException in main(), print one line to stderr and return 1, so cron/CI sees a non-zero exit.

NITS (non-blocking)
8. Nit: names chk / d / x / i / h / r don't say what they hold. Maybe error_interfaces(interfaces) and fetch_interfaces(host), to match down_interfaces().
9. Nit: 100 is a magic number; IN_ERRORS_THRESHOLD = 100 at the top, used as a default parameter, makes it tunable and self-documenting.
10. Nit: the module docstring still says "down" only; worth mentioning input errors and live mode. An f-string would also read better than "https://" + h + "...".

CI already flagged 2, 5 and 6 plus the unused import (ruff/pylint/bandit output is in the checks tab). Items 1, 3, 4, 7 and the naming only show up when a person reads the change.
```

**After the fix-up commit: `FIX=yes bash labs/T46/review_pr.sh`** (the author applied `pr-42-fix.diff` on the same branch)

```
== git log --oneline main..HEAD
Address review: env creds, TLS, timeout, fix loop, tests
link_report: live mode + error check
== git diff --stat main...HEAD
 link_report.py      | 53 ++++++++++++++++++++++++++++++++++++++++++++++++++---
 test_link_report.py | 41 +++++++++++++++++++++++++++++++++++------
 2 files changed, 85 insertions(+), 9 deletions(-)
== py_compile (syntax only)
-- exit 0
== unittest
.....
----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
-- exit 0
== ruff check (E,F,B,S rules)
All checks passed!
-- exit 0
== flake8
-- exit 0
== pylint
-- exit 0
== bandit (security)
-- exit 0
== program on the saved reply
DOWN    GigabitEthernet3
ERRORS  GigabitEthernet1
ERRORS  GigabitEthernet4
-- exit 0
```

- Now Gi4 appears, 5 tests pass, every linter is clean → reviewer approves → merge.

### T46.01 · Purpose

**Must cover:**

- [x] Catch defects and security issues early (cheaper to fix)
- [x] Share knowledge across the team; reduce single points of knowledge
- [x] Keep code style and standards consistent
- [x] Mentoring and improving overall code quality

**Notes:**

- Blueprint 5.13 wording: *"Describe the principles and benefits of a code review process"* (checked against the v1.1 PDF). Expect "which is a benefit" and "which step comes next" questions.

| Benefit | What it means | Where PR #42 shows it |
|---|---|---|
| **Find defects early** | a bug found in review costs a comment; in prod it costs an outage | `return x` inside the loop: the report silently missed Gi4 |
| **Find security issues early** | second pair of eyes before code reaches `main` (and Git history) | hard-coded password, `verify=False` |
| **Knowledge sharing** | at least 2 people understand every change; fewer single points of knowledge ("bus factor") | Bob now knows how live mode works and can maintain it |
| **Consistent style and standards** | code reads the same everywhere; team rules (PEP 8, "always set a timeout") applied every time | `timeout=`, named constants, `error_interfaces()` matching `down_interfaces()` |
| **Mentoring and code quality** | juniors learn from comments; code health improves over time | comment 6 teaches `.get()` instead of `try/except: pass` |

- Secondary benefits that also appear as answers: **shared ownership** of the codebase, **better documentation** (PR description and review thread are a record of why), **compliance/audit trail** (who approved what).
- Google's guide puts the senior principle as: approve once the change **definitely improves overall code health**, even if not perfect. Seek continuous improvement, not perfection.
- Wrong answers to spot: "makes code execute faster", "replaces unit tests", "removes the need for CI", "lets one senior engineer own each module".

### T46.02 · Process

**Must cover:**

- [x] Developer works on a branch
- [x] Opens a pull/merge request with a description
- [x] CI runs automated tests/linters
- [x] Reviewers comment; author fixes; approval; merge to main

**Notes:**

![Code review process: branch, push, PR, CI, human review, fix loop, merge](../assets/T46/01-review-process.png)

*Two gates before merge: CI (yellow, automatic) and human review (yellow, manual). Any red result loops back to the author on the same branch; merge (blue) needs both.*

![Animated PR #42 review loop: push, CI fails, request changes, fix on same branch, CI green, approve, merge](../assets/T46/05-review-loop.gif)

*PR #42 step by step: push + open PR → CI flags 5 issues → reviewer requests changes → author pushes a fix to the **same branch** → CI re-runs green → approve → merge. Fixes the misconception that a fix needs a new PR, or that green CI alone lets the PR merge.*

1. **Branch:** `git switch -c feature/live-errors` (never commit straight to `main`). Git side: [T04.09](T04-git-version-control.md#t0409--branching).
2. **Commit + push:** `git push -u origin feature/live-errors`.
3. **Open a PR (GitHub) / MR (GitLab)** with a description: what changed, why, how it was tested, anything risky. First line = short imperative summary ("Add live RESTCONF mode to link_report").
4. **CI runs automatically** on the PR: lint, unit tests, security scan ([T28.03](T28-ci-cd-devops-principles.md#t2803--pipeline-components)). Red CI → author fixes before anyone spends review time.
5. **Reviewers read the diff** and submit one of three GitHub decisions:

| Decision | Meaning |
|---|---|
| **Comment** | general feedback, neither approve nor block |
| **Request changes** | feedback that must be addressed before merging |
| **Approve** | ready to merge |

6. **Author addresses comments**: new commits on the **same branch** update the same PR; CI re-runs on every push; reply to or resolve each thread.
7. **Approval + green checks → merge** to `main` (merge, squash or rebase), delete the branch. CD can then deploy `main` ([T28.02](T28-ci-cd-devops-principles.md#t2802--cd)).

- **Branch protection** (GitHub) / protected branches + approval rules (GitLab) enforce the gates: "Require pull request reviews before merging" (N approvals, optionally from a **code owner** listed in `CODEOWNERS`) and "Require status checks before merging" (CI must pass).
- Same flow from the CLI with `gh` (GitHub CLI), shown in **Examples**.
- This repo uses the same flow: Beedy's batch branch → PR → Bob reviews (CLAUDE.md calls this practice for 5.13).

### T46.03 · Types

**Must cover:**

- [x] Over-the-shoulder: reviewer at the author's desk
- [x] Tool-assisted: PRs in GitHub/GitLab (most common)
- [x] Pair programming: continuous review while coding
- [x] Email-based: patches sent for review

**Notes:**

![Review types sorted by when the review happens](../assets/T46/02-review-types.png)

*Sort by **when**: pair programming reviews during coding; the other three review after. Tool-assisted (blue) is the default modern answer.*

| Type | How | Strengths | Weaknesses |
|---|---|---|---|
| **Over-the-shoulder** | author walks the reviewer through the change at the desk (or screen-share) | fast, informal, easy discussion | no written record, author steers attention, hard across time zones |
| **Tool-assisted** | GitHub pull request / GitLab merge request: inline comments, suggestions, approvals, CI status in one place | async, audit trail, CI integrated, enforceable by branch protection | can be slow if reviewers don't respond; big PRs get rubber-stamped |
| **Pair programming** | two people, one keyboard: **driver** types, **navigator** reviews each line live, swap often | continuous review, instant feedback, strong knowledge sharing | two people's time on one task; no separate record |
| **Email-based** | author sends patches with `git format-patch` + `git send-email`; reviewers reply inline on a mailing list (Linux kernel style) | works with any mail client, no platform needed | manual, threads hard to track, no built-in CI gate |

- **Pair programming vs PR review** (common exam pair): pair = review **while** writing, synchronous, ends when the code is written; PR = review **after** pushing, asynchronous, leaves a record and can be gated by CI. Teams often do both (pair, then still open a PR).
- Formal **inspection** (Fagan-style meeting with roles: moderator, reader, recorder) also exists; heavyweight, rarely the exam answer. ⚠ verify whether the exam ever names it.

### T46.04 · Good practice

**Must cover:**

- [x] Keep changes small and focused
- [x] Use checklists; review logic, security, tests, readability
- [x] Constructive, specific feedback about the code, not the person
- [x] Let linters/formatters and CI handle style

**Notes:**

**Author side**

- **Small, focused PR:** one self-contained change. Google's guide: ~100 lines is usually reasonable, ~1000 usually too large; spread across many files also counts as "large". PR #42 is 28 added lines in one file: easy to review properly.
- Small PRs are reviewed faster and more thoroughly, introduce fewer bugs, merge with fewer conflicts and roll back cleanly.
- Don't mix a reformat with a logic change (split into two PRs), or the real change hides in the noise.
- Include the **tests in the same PR** as the code.
- Review your own diff first (`git diff main...HEAD`), and write a description that says how you tested it.

**Reviewer checklist** (Google's "what to look for", in priority order)

| Check | Question | PR #42 finding |
|---|---|---|
| Design | does the change belong here, fit the system? | live mode fits; keep file mode working |
| Functionality | does it do what's intended? edge cases? | `return x` in the loop; Loopback0 has no `statistics` |
| Security | secrets, TLS, input handling, injection? | hard-coded password, `verify=False` |
| Complexity | can it be understood quickly? over-engineered? | `try/except: pass` hides intent |
| Tests | tests added, and would they fail if the code broke? | none for `get_live()` or `chk()` |
| Naming | names say what things are? | `chk`, `d`, `x`, `h`, `r` |
| Comments / docs | comments explain **why**, docstrings updated? | module docstring still says "down" only |
| Style | follows the style guide? | unused `import os` (linter already said so) |

**Automated checks vs human review**

![What CI caught vs what the human reviewer caught in PR #42](../assets/T46/03-automated-vs-human.png)

*Green = found by the real linter run; yellow = only a person reading the diff found it. Neither list covers the other.*

- **Let tools own style:** formatter (e.g. `black`, `ruff format`) + linter (`flake8`, `pylint`, `ruff`) + security scanner (`bandit`) run in CI on every push. Humans then spend their time on logic, design, security intent and tests.
- PEP 8 is the Python style guide; on style questions the style guide wins over personal preference. A point that isn't in the guide is a `Nit:` at most.
- `py_compile` only checks **syntax**: PR #42 passes it with all 10 issues inside.

**Giving feedback**

![Decide the severity of a review comment](../assets/T46/04-comment-severity.png)

*Blocking (red) → Request changes. Anything a tool can enforce goes into CI (blue). Preferences become `Nit:` (green). Say what's good too.*

- **About the code, not the person.** Bad: "Why did you hard-code the password?" Good: "The password on line 18 ends up in Git history; please read it from `RESTCONF_PASS`."
- **Specific + actionable:** file and line, the problem, **why** it matters, a suggested fix (see `review-42.txt` item 3: line, effect on Gi4, fix, test to add).
- **Label severity:** blocking / should fix / `Nit:` / `Optional:` / `FYI:`. Without labels, authors treat every comment as mandatory.
- **Point out problems, let the author decide the fix** (the author is closer to the code); give direct code when it's quicker.
- **Praise good parts** (first line of `review-42.txt`).
- **Respond fast:** within one business day; quick replies matter more than the total time to merge.
- **Author side:** reply to every comment, push fixes, don't take it personally. If the reviewer asks "what does this do?", the right fix is clearer code, not an explanation only in the PR thread.
- Disagreements: facts and data beat opinions; if stuck, talk live, then escalate to the tech lead. Record the outcome in the PR.

### T46.05 · Exam angle

**Must cover:**

- [x] Pick the benefit or the correct step in a review process
- [x] Know where review fits relative to CI and merge

**Notes:**

- **"Which is a benefit?"** → early defect/security detection, knowledge sharing, consistent standards, mentoring/quality. Distractors: faster execution, fewer tests needed, no need for CI.
- **"What comes next?"** → branch → commit → push → **PR** → **CI** → **review** → fix → **approve** → **merge** → deploy.
- **"Where does review fit?"** → after the PR is opened and (usually) after CI is green, **before merge** to `main`. CI and review are both merge gates; neither replaces the other.
- **"Which type?"** → "two developers, one writes, one watches each line" = pair programming; "comments on a GitHub/GitLab PR" = tool-assisted; "patches on a mailing list" = email-based; "walks a colleague through at the desk" = over-the-shoulder.
- **"Best review comment?"** → the one that names the line, explains why, suggests a fix, and is about the code.
- **"Spot the problem in this diff"** → read it with [T05](T05-unified-diffs.md), then check secrets, `verify=False`, timeouts, bare `except`, logic in loops, missing tests.

## Exam traps

- **CI green ≠ reviewed.** Linters find patterns (unused import, bare `except`, `verify=False`); a human finds intent bugs, hard-coded secrets, missing tests. Both gates are required.
- **Review is before merge,** not after deploy. "Review the code in production logs" is a distractor.
- **Pair programming vs PR review:** pair = continuous, during coding, synchronous; PR = after push, asynchronous, recorded.
- **Tool-assisted** (GitHub PR / GitLab MR) is the most common type; "pull request" is a platform feature, not a `git` command ([T04 traps](T04-git-version-control.md#exam-traps)).
- **Fixes go on the same branch** and update the same PR; CI re-runs automatically. No new PR, no direct push to `main`.
- **Small PRs beat big ones**: faster, more thorough review. A 2,000-line PR is a reason to ask for a split, not to approve quickly.
- **Style belongs to tools.** Humans arguing about whitespace = wasted review; put the rule in the linter/formatter.
- **Feedback targets code, not people.** "You always…" is never the best answer.
- **`py_compile` / "it runs" is not a review.** PR #42 compiles, passes its old test and prints output, yet has a logic bug.
- **Benefit distractors:** "faster execution", "replaces testing", "single owner per module" are never benefits.
- **Approve vs Request changes vs Comment:** only **Request changes** blocks; **Comment** is neutral.

## Examples

### 1. Run the reference program

Needs Python 3 and Git; linters are optional. From the repo root:

```bash
python3 -m venv "${TMPDIR:-/tmp}/t46-venv"
"${TMPDIR:-/tmp}/t46-venv/bin/pip" install requests ruff flake8 pylint bandit
PATH="${TMPDIR:-/tmp}/t46-venv/bin:$PATH" bash labs/T46/review_pr.sh            # PR #42 as submitted
PATH="${TMPDIR:-/tmp}/t46-venv/bin:$PATH" FIX=yes bash labs/T46/review_pr.sh    # after the fix-up commit
```

In the lab container (⚠ not run here: Docker daemon down; the image has `requests` but no linters, so those steps print "not installed, skipped"):

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work --workdir /work ccna-auto-lab:latest bash labs/T46/review_pr.sh
```

`labs/T46/review_pr.sh`:

```bash
#!/usr/bin/env bash
# T46 lab: play the CI half of a code review on "PR #42".
# 1. Builds a throwaway repo with labs/T46/base/ on main.
# 2. Creates the PR branch and applies pr-42.diff (the change under review).
# 3. Runs the automated checks a CI job would run, then the program itself.
# Usage:  bash labs/T46/review_pr.sh            # review PR #42 as submitted
#         FIX=yes bash labs/T46/review_pr.sh    # also apply pr-42-fix.diff (the author's fix-up commit)
# Linters are optional: put ruff/flake8/pylint/bandit on PATH (e.g. activate a venv) to see their output.
set -u
LAB="$(cd "$(dirname "$0")" && pwd)"
WORK="${TMPDIR:-/tmp}/t46-review"
PY="${PYTHON:-python3}"
export PYLINTHOME="$WORK/.pylint" RUFF_CACHE_DIR="$WORK/.ruff"

rm -rf "$WORK" && mkdir -p "$WORK" && cd "$WORK" || exit 1
git init --quiet --initial-branch=main
git config user.name "Beedy"
git config user.email "beedy@example.com"
git config commit.gpgsign false
cp -R "$LAB/base/." .
git add . && git commit --quiet --message "link_report: list down interfaces"

git switch --quiet --create feature/live-errors
git apply "$LAB/pr-42.diff" && git commit --quiet --all --message "link_report: live mode + error check"
if [ "${FIX:-no}" = "yes" ]; then
  git apply "$LAB/pr-42-fix.diff" && git commit --quiet --all --message "Address review: env creds, TLS, timeout, fix loop, tests"
fi

echo "== git log --oneline main..HEAD"; git log --oneline main..HEAD | sed 's/^[0-9a-f]* //'
echo "== git diff --stat main...HEAD"; git diff --stat main...HEAD

run() {                                   # run one check; never stop the script, report the exit code
  local name="$1"; shift
  echo "== $name"
  "$@"; echo "-- exit $?"
}
run "py_compile (syntax only)" "$PY" -m py_compile link_report.py test_link_report.py
run "unittest" "$PY" -m unittest 2>&1
for tool in ruff flake8 pylint bandit; do
  if ! command -v "$tool" >/dev/null 2>&1; then echo "== $tool: not installed, skipped"; continue; fi
  case "$tool" in
    ruff)   run "ruff check (E,F,B,S rules)" ruff check --no-cache --select E,F,B,S --output-format concise link_report.py ;;
    flake8) run "flake8" flake8 --max-line-length 100 link_report.py ;;
    pylint) run "pylint" pylint --score=n --disable=C0114,C0116,C0301 link_report.py ;;
    bandit) run "bandit (security)" bandit --quiet --format custom --msg-template "{line}: {test_id} [{severity}] {msg}" link_report.py ;;
  esac
done
run "program on the saved reply" "$PY" link_report.py fixtures/interfaces.json
```

Without a venv (system Python here has no `requests`), the "CI" goes red before any linter runs. Summary lines only:

```bash
bash labs/T46/review_pr.sh 2>&1 | grep -E "^(== |-- exit|ModuleNotFoundError|FAILED)"
```

```
== git log --oneline main..HEAD
== git diff --stat main...HEAD
== py_compile (syntax only)
-- exit 0
== unittest
ModuleNotFoundError: No module named 'requests'
FAILED (errors=1)
-- exit 1
== ruff: not installed, skipped
== flake8: not installed, skipped
== pylint: not installed, skipped
== bandit: not installed, skipped
== program on the saved reply
ModuleNotFoundError: No module named 'requests'
-- exit 1
```

### 2. Prove the logic bug with a test (what review comment 4 asks for)

Run after `review_pr.sh` (without `FIX=yes`), in its throwaway repo:

```bash
cd "${TMPDIR:-/tmp}/t46-review"
cat > test_chk.py <<'EOF'
import unittest

from link_report import chk


class ChkTest(unittest.TestCase):
    def test_finds_every_errored_interface(self):
        interfaces = [
            {"name": "GigabitEthernet1", "statistics": {"in-errors": 250}},
            {"name": "GigabitEthernet4", "statistics": {"in-errors": 120}},
        ]
        self.assertEqual(chk(interfaces), ["GigabitEthernet1", "GigabitEthernet4"])


if __name__ == "__main__":
    unittest.main()
EOF
"${TMPDIR:-/tmp}/t46-venv/bin/python" -m unittest test_chk
```

Output:

```
F
======================================================================
FAIL: test_finds_every_errored_interface (test_chk.ChkTest.test_finds_every_errored_interface)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/claude-501/T46-work/t46-review/test_chk.py", line 12, in test_finds_every_errored_interface
    self.assertEqual(chk(interfaces), ["GigabitEthernet1", "GigabitEthernet4"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['GigabitEthernet1'] != ['GigabitEthernet1', 'GigabitEthernet4']

Second list contains 1 additional elements.
First extra element 1:
'GigabitEthernet4'

- ['GigabitEthernet1']
+ ['GigabitEthernet1', 'GigabitEthernet4']

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
```

- No linter flagged this; one 10-line test does. That's why "no tests" is a **blocking** comment.

### 3. The fix-up commit (`pr-42-fix.diff`)

What the author pushed to the same branch in response to `review-42.txt`:

```diff
diff --git a/link_report.py b/link_report.py
index 6029e0f..8a4191a 100644
--- a/link_report.py
+++ b/link_report.py
@@ -1,24 +1,38 @@
-"""Report interfaces that are down, from a saved RESTCONF reply (ietf-interfaces)."""
+"""Report interfaces that are down or have input errors, from a saved RESTCONF reply
+or a live device (ietf-interfaces)."""
 import json
 import os
 import sys
 
 import requests
 
+INTERFACES_STATE = "ietf-interfaces:interfaces-state"
+IN_ERRORS_THRESHOLD = 100          # flag an interface with more input errors than this
+REQUEST_TIMEOUT_S = 10             # seconds; never wait forever on a device
+
 
 def load_interfaces(path):
     """Return the interface list from a saved ietf-interfaces JSON reply."""
     with open(path, encoding="utf-8") as reply:
         data = json.load(reply)
-    return data["ietf-interfaces:interfaces-state"]["interface"]
+    return data[INTERFACES_STATE]["interface"]
+
 
+def fetch_interfaces(host):
+    """Return the interface list from a live device over RESTCONF.
 
-def get_live(h):
-    r = requests.get("https://" + h + "/restconf/data/ietf-interfaces:interfaces-state",
-                     auth=("admin", "FAKE-Passw0rd-not-real"),
-                     headers={"Accept": "application/yang-data+json"},
-                     verify=False)
-    return r.json()["ietf-interfaces:interfaces-state"]["interface"]
+    Credentials come from RESTCONF_USER / RESTCONF_PASS; TLS is verified
+    (set RESTCONF_CA to a CA bundle path for a private CA).
+    """
+    response = requests.get(
+        f"https://{host}/restconf/data/{INTERFACES_STATE}",
+        auth=(os.environ["RESTCONF_USER"], os.environ["RESTCONF_PASS"]),
+        headers={"Accept": "application/yang-data+json"},
+        verify=os.environ.get("RESTCONF_CA", True),
+        timeout=REQUEST_TIMEOUT_S,
+    )
+    response.raise_for_status()
+    return response.json()[INTERFACES_STATE]["interface"]
 
 
 def down_interfaces(interfaces):
@@ -26,25 +40,31 @@ def down_interfaces(interfaces):
     return [intf["name"] for intf in interfaces if intf["oper-status"] != "up"]
 
 
-def chk(d):
-    x = []
-    for i in d:
-        try:
-            if i["statistics"]["in-errors"] > 100:
-                x.append(i["name"])
-        except:
-            pass
-        return x
+def error_interfaces(interfaces, threshold=IN_ERRORS_THRESHOLD):
+    """Return the names of interfaces with more than `threshold` input errors.
+
+    Interfaces without a statistics container (e.g. some loopbacks) are skipped.
+    """
+    return [
+        intf["name"]
+        for intf in interfaces
+        if intf.get("statistics", {}).get("in-errors", 0) > threshold
+    ]
 
 
 def main(argv):
-    if argv[1].startswith("live:"):
-        interfaces = get_live(argv[1][5:])
+    source = argv[1]
+    if source.startswith("live:"):
+        try:
+            interfaces = fetch_interfaces(source.removeprefix("live:"))
+        except requests.RequestException as err:
+            print(f"ERROR   RESTCONF request failed: {err}", file=sys.stderr)
+            return 1
     else:
-        interfaces = load_interfaces(argv[1])
+        interfaces = load_interfaces(source)
     for name in down_interfaces(interfaces):
         print(f"DOWN    {name}")
-    for name in chk(interfaces):
+    for name in error_interfaces(interfaces):
         print(f"ERRORS  {name}")
     return 0
 
diff --git a/test_link_report.py b/test_link_report.py
index d084b5d..649a449 100644
--- a/test_link_report.py
+++ b/test_link_report.py
@@ -1,16 +1,45 @@
 """Unit tests for link_report.py (run: python3 -m unittest -v)."""
+import io
 import unittest
+from unittest.mock import patch
 
-from link_report import down_interfaces
+import requests
+
+from link_report import down_interfaces, error_interfaces, main
+
+INTERFACES = [
+    {"name": "GigabitEthernet1", "oper-status": "up", "statistics": {"in-errors": 250}},
+    {"name": "GigabitEthernet2", "oper-status": "down", "statistics": {"in-errors": 0}},
+    {"name": "GigabitEthernet4", "oper-status": "up", "statistics": {"in-errors": 120}},
+    {"name": "Loopback0", "oper-status": "up"},
+]
 
 
 class DownInterfacesTest(unittest.TestCase):
     def test_lists_only_down_interfaces(self):
-        interfaces = [
-            {"name": "GigabitEthernet1", "oper-status": "up"},
-            {"name": "GigabitEthernet2", "oper-status": "down"},
-        ]
-        self.assertEqual(down_interfaces(interfaces), ["GigabitEthernet2"])
+        self.assertEqual(down_interfaces(INTERFACES), ["GigabitEthernet2"])
+
+
+class ErrorInterfacesTest(unittest.TestCase):
+    def test_checks_every_interface_not_just_the_first(self):
+        self.assertEqual(error_interfaces(INTERFACES), ["GigabitEthernet1", "GigabitEthernet4"])
+
+    def test_threshold_is_strictly_greater_than(self):
+        self.assertEqual(error_interfaces(INTERFACES, threshold=250), [])
+
+    def test_skips_interface_without_statistics(self):
+        self.assertEqual(error_interfaces([{"name": "Loopback0", "oper-status": "up"}]), [])
+
+
+class MainLiveTest(unittest.TestCase):
+    @patch.dict("os.environ", {"RESTCONF_USER": "u", "RESTCONF_PASS": "p"})
+    @patch("link_report.requests.get")
+    @patch("sys.stderr", new_callable=io.StringIO)
+    def test_live_failure_returns_1(self, fake_stderr, mock_get):
+        mock_get.side_effect = requests.ConnectionError("no route to host")
+        self.assertEqual(main(["link_report.py", "live:192.0.2.10"]), 1)
+        self.assertIn("RESTCONF request failed", fake_stderr.getvalue())
+        self.assertEqual(mock_get.call_args.kwargs["timeout"], 10)
 
 
 if __name__ == "__main__":
```

- Every blocking item maps to a hunk: env-var credentials, `verify=os.environ.get("RESTCONF_CA", True)`, `timeout=REQUEST_TIMEOUT_S` + `raise_for_status()`, the list comprehension (no early `return`, no bare `except`), `RequestException` handled in `main()`, and four new tests.

### 4. Email-based review (patch out of Git)

Run in the throwaway repo from section 1; `format-patch` writes the PR commit as a mailable patch:

```bash
cd "${TMPDIR:-/tmp}/t46-review"
git format-patch -1 HEAD --stdout | head -14
```

```
From 03160d6f701c05b114ef1e2ada1634e0fb96150e Mon Sep 17 00:00:00 2001
From: Beedy <beedy@example.com>
Date: Sat, 10 Oct 2026 20:59:39 +0800
Subject: [PATCH] link_report: live mode + error check

---
 link_report.py | 29 ++++++++++++++++++++++++++++-
 1 file changed, 28 insertions(+), 1 deletion(-)

diff --git a/link_report.py b/link_report.py
index cba917c..6029e0f 100644
--- a/link_report.py
+++ b/link_report.py
@@ -1,7 +1,10 @@
```

- Sending it: `git send-email --to=netdev-team@example.com 0001-link_report-live-mode-error-check.patch` (needs SMTP configured; ⚠ not run). Reviewers reply inline to the email; the author sends `[PATCH v2]`.

### 5. Tool-assisted review from the CLI (GitHub `gh`)

Full commands for a real repo (⚠ not run: no real PR was opened). Flags checked against `gh` 2.97 `--help`.

```bash
git switch --create feature/live-errors
git push --set-upstream origin feature/live-errors
gh pr create --base main --head feature/live-errors \
  --title "Add live RESTCONF mode and input-error check to link_report" \
  --body "What: live: mode + ERRORS report. Why: NOC wants live checks. Tested: unittest + fixtures/interfaces.json."
gh pr checks 42                                                   # CI status of the PR
gh pr diff 42                                                     # the unified diff to review
gh pr review 42 --request-changes --body-file labs/T46/review-42.txt
gh pr review 42 --approve --body "Blocking items fixed, thanks. LGTM."
gh pr merge 42 --squash --delete-branch
```

### 6. Drill: review this hunk yourself

```diff
@@ -12,5 +12,7 @@ def backup(host):
     conn = ConnectHandler(device_type="cisco_ios", host=host,
-                          username=os.environ["NET_USER"], password=os.environ["NET_PASS"])
+                          username="netops", password="FAKE-not-a-real-pw")
     output = conn.send_command("show running-config")
-    with open(f"backups/{host}.cfg", "w") as f:
-        f.write(output)
+    try:
+        open(f"backups/{host}.cfg", "w").write(output)
+    except:
+        pass
```

<details><summary>Model review</summary>

- **Blocking (security), line 13:** credentials moved from env vars back into the source; they'd be committed. Please keep `os.environ["NET_USER"]` / `os.environ["NET_PASS"]`.
- **Blocking (error handling), lines 15–18:** the bare `except: pass` means a failed backup (disk full, missing `backups/` folder) silently produces no file. Let the `OSError` surface, or catch `OSError` and log which host failed.
- **Should fix:** the `with` block was replaced by a bare `open(...).write(...)`, so the file isn't closed deterministically. Keep `with open(...) as f:`.
- **Ask:** a test with a mocked `ConnectHandler` that checks the file is written.
- Reading it: `-12,5 +12,7` = 2 context lines, 3 removed, 5 added → net +2. One line modified (credentials), and the 2-line `with` block replaced by 4 lines ([T05.02](T05-unified-diffs.md#t0502--hunk-header)).
</details>

## Practice questions

**Q1.** Which two are benefits of a code review process? (Choose two.)
A. Code runs faster in production  B. Defects are found before they reach the main branch  C. Unit tests are no longer needed  D. More than one engineer understands each change  E. CI pipelines can be removed

<details><summary>Answer</summary>

**B, D.** Early defect detection and knowledge sharing. Review complements tests and CI; it never replaces them or speeds up execution. (T46.01)
</details>

**Q2.** Put these steps in order: `Reviewer approves` · `Open a pull request` · `Create a feature branch` · `CI runs lint and unit tests` · `Merge to main` · `Push commits` · `Author pushes fixes for review comments`

<details><summary>Answer</summary>

Create a feature branch → Push commits → Open a pull request → CI runs lint and unit tests → Author pushes fixes for review comments → Reviewer approves → Merge to main. Fixes go on the same branch and re-trigger CI before approval. (T46.02)
</details>

**Q3.** Two developers share one workstation. One types the code while the other reviews each line as it is written and suggests changes. Which review type is this?
A. Over-the-shoulder  B. Tool-assisted  C. Pair programming  D. Email-based

<details><summary>Answer</summary>

**C.** Continuous review during coding, with driver and navigator roles. Over-the-shoulder happens **after** the code is written, with the author walking the reviewer through it. (T46.03)
</details>

**Q4.** A pull request's CI pipeline is green: lint passes and all unit tests pass. What is still true?
A. The PR can skip human review  B. The PR may still contain logic errors and missing tests that only a reviewer would notice  C. The PR is already merged  D. The code is guaranteed secure

<details><summary>Answer</summary>

**B.** Linters catch patterns and tests only cover what they test. In PR #42, CI was happy with the old test while `chk()` returned after the first interface. (T46.04, T46.05)
</details>

**Q5.** A reviewer finds `verify=False` in a new `requests.get()` call. Which comment is the most effective?
A. "This is wrong."  B. "You clearly don't understand TLS."  C. "Line 20: `verify=False` disables certificate checks, so a man-in-the-middle could read the device password. Please keep verification on, or pass the lab CA bundle path to `verify=`."  D. "Nit: maybe change this."

<details><summary>Answer</summary>

**C.** Specific (line), explains why, actionable fix, about the code. D mislabels a security issue as a nit; A and B aren't actionable, and B targets the person. (T46.04)
</details>

**Q6.** Refer to the hunk from PR #42:

```diff
+def chk(d):
+    x = []
+    for i in d:
+        try:
+            if i["statistics"]["in-errors"] > 100:
+                x.append(i["name"])
+        except:
+            pass
+        return x
```

With three interfaces that all have more than 100 input errors, what does `chk()` return, and which review finding explains it?
A. All three names; no issue  B. Only the first interface's name; `return` is inside the loop  C. An empty list; the bare `except` hides a `KeyError`  D. `None`; there is no `return`

<details><summary>Answer</summary>

**B.** `return x` is indented under the `for`, so the function returns after the first iteration. No linter in the lab flagged it; a test with two errored interfaces fails immediately (Examples §2). (T46.04)
</details>

**Q7.** A developer opens a pull request that reformats 40 files and also changes the retry logic in one of them. What should the reviewer ask for?
A. Approve quickly because formatting is harmless  B. Split it into a formatting-only PR and a separate PR for the retry logic  C. Merge it and review after deployment  D. Email the patch instead

<details><summary>Answer</summary>

**B.** Small, focused changes. Mixing a mass reformat with a logic change hides the real change and makes rollback harder. (T46.04)
</details>

**Q8.** Where does code review sit relative to CI and the merge to `main`?
A. After merge, before deployment  B. After the PR is opened; CI and an approving review are both required before merge  C. Before any code is committed  D. Only after CI fails

<details><summary>Answer</summary>

**B.** Review happens on the open PR, alongside CI; branch protection can require both an approval and passing status checks before merge. (T46.02, T46.05)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T46.1 | Top-up | Code review principles + benefits | 15 | Own notes |

- Skip / low priority: n/a
- CBT has no 5.13 content (`data/blueprint-map.csv`); this note plus `labs/T46/` is the whole top-up.
- Real practice: review Bob's PRs in this repo with the checklist in T46.04.

## Sources

- Overview image: HTML source `assets/T46/00-overview.html`, rendered to PNG. Diagrams: Mermaid sources `assets/T46/*.mmd`. Animation: `assets/T46/05-review-loop-anim.html` → `.gif` (re-render commands in `assets/README.md`).
- Cisco 200-901 v1.1 exam topics (5.13 wording "Describe the principles and benefits of a code review process"): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf
- Google Engineering Practices, The Standard of Code Review (code health, mentoring, style guide authority, resolving conflicts): https://google.github.io/eng-practices/review/reviewer/standard.html
- Google Engineering Practices, What to look for in a code review (design, functionality, complexity, tests, naming, comments, style): https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Google Engineering Practices, How to write code review comments (courtesy, explain why, Nit/Optional/FYI labels, praise): https://google.github.io/eng-practices/review/reviewer/comments.html
- Google Engineering Practices, Speed of code reviews (one business day, large CLs): https://google.github.io/eng-practices/review/reviewer/speed.html
- Google Engineering Practices, Small CLs (~100 vs ~1000 lines, benefits): https://google.github.io/eng-practices/review/developer/small-cls.html
- Google Engineering Practices, Writing good CL descriptions (imperative first line): https://google.github.io/eng-practices/review/developer/cl-descriptions.html
- GitHub Docs, About pull request reviews (Comment / Approve / Request changes): https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews
- GitHub Docs, About protected branches (required reviews, required status checks): https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- GitHub Docs, About code owners: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- GitLab Docs, Merge request approvals: https://docs.gitlab.com/user/project/merge_requests/approvals/
- PEP 8 (code is read more often than written; bare `except:` catches `SystemExit`/`KeyboardInterrupt`): https://peps.python.org/pep-0008/
- git-format-patch / git-send-email: https://git-scm.com/docs/git-format-patch · https://git-scm.com/docs/git-send-email

## To verify

- ⚠ Exam wording: the 5.13 text above is from the v1.1 PDF (fetched 10 Oct 2026). The four review types and the benefit list are the tracker's scope (`data/concepts.csv`), not Cisco's own list; Cisco publishes no official sub-items for 5.13.
- ⚠ Formal inspection (Fagan) as a fifth review type: unconfirmed whether the exam ever names it.
- ⚠ bandit 1.9.4 did not flag `auth=("admin", "FAKE-Passw0rd-not-real")`; its hard-coded-password checks (B105–B107) match assignments, defaults and keyword arguments with password-like names. Other scanners (e.g. secret scanners in CI) may catch it.
- ⚠ GitHub "Request changes" blocks merging only when branch protection requires reviews; on an unprotected branch it's advisory.
- Linter output came from real runs: Python 3.14.6, Git 2.54, ruff 0.17.0, flake8 7.4.1, pylint 4.1.2, bandit 1.9.4. Other versions may word messages differently or add rules. Commit hashes and dates in Examples §4 will differ on your machine.
- Not run: the Docker lab command (daemon down), `git send-email` (no SMTP), and the `gh pr` commands (no real PR opened).
- The CBT course has no 5.13 video; nothing here claims CBT content.
