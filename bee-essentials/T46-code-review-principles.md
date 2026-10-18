# T46 · Code review principles: essentials

> Blueprint 5.13 · Full note: [bee/T46-code-review-principles.md](../bee/T46-code-review-principles.md) · Teach-back 2026-11-01

## In one picture
![T46 at a glance: review process swim-lane, benefits, review types, CI vs human, giving feedback](../assets/T46/00-overview.png)
*The top swim-lane is the process in numbered order (red is the fix loop, blue is the merge). The four panels below cover purpose, review types, what to look for, and how to give feedback. Red boxes are exam traps.*

## The big idea
- Code review means another person reads a change before it joins the main branch. You already do this daily, so this page is about matching your experience to the exam's wording.
- Blueprint 5.13 says: "Describe the principles and benefits of a code review process". Expect "which is a benefit", "which step comes next", "which review type is this" and "which is the best comment" questions.
- The running example is **PR #42**, a small network script change with ten planted issues. CI caught some of them, and only a human caught the rest. Your CBT course has no 5.13 video, so this page and the full note are your coverage.

## What you need to know

### 1. Why we review: the benefits the exam wants
| Benefit | What it means in plain words | PR #42 example |
|---|---|---|
| **Find defects early** | a bug found in review costs a comment; in production it costs an outage | `return x` inside a loop made the report silently miss an interface |
| **Find security issues early** | a second pair of eyes before code reaches `main` and Git history | a hard-coded password and `verify=False` |
| **Knowledge sharing** | at least two people understand every change, so there are fewer single points of knowledge ("bus factor") | Bob now knows how live mode works |
| **Consistent style and standards** | team rules (PEP 8, "always set a timeout") are applied every time | named constants, matching function names |
| **Mentoring and code quality** | juniors learn from comments, and code health improves over time | a comment teaching `.get()` instead of `try/except: pass` |

- Secondary benefits that also appear as answers: **shared ownership** of the codebase, **better documentation** (the PR thread records *why*), and an **audit trail** (who approved what).
- Google's guide says to approve once a change **definitely improves overall code health**, even if it is not perfect. Aim for continuous improvement, not perfection.
- **Exam-sim gap:** collaborative review is also a **learning tool**. Juniors learn the codebase and standards, seniors spread knowledge, and the team converges on shared conventions. Cue: "benefit of collaborative code review" points to **a supportive environment for learning and knowledge sharing**.
- Wrong answers to spot: "makes code run faster", "replaces unit tests", "removes the need for CI", "lets one senior engineer own each module".

### 2. Where review sits in the workflow
![Code review process: branch, push, PR, CI, human review, fix loop, merge](../assets/T46/01-review-process.png)
*There are two gates before merge: CI (automatic) and human review (manual). Any red result loops back to the author on the same branch, and merge needs both gates green.*

1. **Branch**: work on a feature branch, never commit straight to `main`.
2. **Commit and push** the branch.
3. **Open a pull request (GitHub) or merge request (GitLab)** with a description: what changed, why, how you tested it, and anything risky. The first line is a short imperative summary.
4. **CI runs automatically**: lint, unit tests, security scan. If CI is red, the author fixes it before anyone spends review time.
5. **Reviewers read the diff** and submit one of three GitHub decisions:

| Decision | Meaning |
|---|---|
| **Comment** | general feedback; neither approves nor blocks |
| **Request changes** | must be addressed before merging |
| **Approve** | ready to merge |

6. **The author pushes fixes to the same branch.** That updates the same PR, and CI re-runs on every push. No new PR is needed.
7. **Approval plus green checks, then merge** to `main` (merge, squash or rebase) and delete the branch. CD can then deploy.

- **Branch protection** enforces the gates: "Require pull request reviews before merging" (optionally from a **code owner** listed in `CODEOWNERS`) and "Require status checks before merging". Note that "Request changes" only blocks merging when branch protection requires reviews (⚠ verify).

### 3. The four review types
![Review types sorted by when the review happens](../assets/T46/02-review-types.png)
*Sort the types by when the review happens: pair programming reviews during coding, and the other three review afterwards. Tool-assisted is the default modern answer.*

| Type | How it works | Strengths | Weaknesses |
|---|---|---|---|
| **Over-the-shoulder** | the author walks a reviewer through the change at the desk or on a screen share | fast, informal | no written record, the author steers attention |
| **Tool-assisted** (most common) | a GitHub PR or GitLab MR with inline comments, approvals and CI status in one place | asynchronous, audit trail, CI built in, enforceable | can be slow; big PRs get rubber-stamped |
| **Pair programming** | two people, one keyboard: the **driver** types, the **navigator** reviews each line live | continuous review, instant feedback | two people's time on one task, no separate record |
| **Email-based** | patches sent with `git format-patch` and `git send-email`; reviewers reply inline on a mailing list (Linux kernel style) | needs no platform | manual, threads are hard to track, no CI gate |

- **Pair programming vs PR review** is a common exam pair. Pairing reviews **while** you write, synchronously, and leaves no record. A PR reviews **after** you push, asynchronously, leaves a record and can be gated by CI. Teams often do both.
- Formal **inspection** (a Fagan-style meeting with set roles) also exists but is heavyweight and rarely the answer (⚠ verify whether the exam names it).

### 4. Good practice for authors and reviewers
- **Author side:**
  - Keep the PR **small and focused**. Google's guide says about 100 lines is usually reasonable and about 1,000 is usually too large. Small PRs get reviewed faster and more thoroughly, cause fewer bugs and roll back cleanly.
  - Do not mix a mass reformat with a logic change. Split them into two PRs, or the real change hides in the noise.
  - Put the **tests in the same PR** as the code, review your own diff first, and say how you tested it.
- **Reviewer checklist** (Google's priority order): design, functionality and edge cases, security, complexity, tests (would they fail if the code broke?), naming, comments and docs, then style.
- **Let tools own style.** A formatter (`black`, `ruff format`), linters (`flake8`, `pylint`, `ruff`) and a security scanner (`bandit`) run in CI on every push, so humans can spend their time on logic, design and tests. On style questions, the style guide (PEP 8) wins over personal preference.

![What CI caught vs what the human reviewer caught in PR #42](../assets/T46/03-automated-vs-human.png)
*Green items were found by the real linter run; yellow items were only found by a person reading the diff. Neither list covers the other.*

- In PR #42, the linters flagged the unused import, the bare `except`, the missing timeout and `verify=False`. Only the human caught the hard-coded password, the early `return` inside the loop, the missing tests, the vague names and the magic number.
- `py_compile` only checks **syntax**. PR #42 passed it, passed its old test and printed output, with all ten issues still inside.
- **Exam-sim gap: industry best practices** (often quoted on exams):
  - **Set goals and measure**: inspection rate (lines per hour), defect rate, defects found per review.
  - **Keep it small and slow**: a few hundred lines at a time, under about 500 lines an hour, and stop after about 60 to 90 minutes (⚠ verify these figures; they come from the SmartBear/Cisco study, not a standard).
  - **The author annotates the change first**, explaining intent and pointing at risky parts.
  - **Assign reviewers by expertise, not seniority**, and use a checklist.
  - Cue: "best practice for code review" points to **set review goals and collect metrics**.

### 5. Giving feedback well
![Decide the severity of a review comment](../assets/T46/04-comment-severity.png)
*Blocking issues mean Request changes. Anything a tool can enforce belongs in CI. Preferences become `Nit:` comments. Say what is good too.*

- **Talk about the code, not the person.** Bad: "Why did you hard-code the password?" Good: "The password on line 18 ends up in Git history; please read it from `RESTCONF_PASS`."
- **Be specific and actionable**: give the file and line, the problem, **why** it matters, and a suggested fix.
- **Label the severity**: blocking, should fix, `Nit:`, `Optional:`, `FYI:`. Without labels, authors treat every comment as mandatory.
- Point out the problem and let the author choose the fix, since they are closer to the code. Give direct code when that is quicker.
- **Praise the good parts**, and **respond fast** (within one business day).
- As the author, reply to every comment and do not take it personally. If a reviewer asks "what does this do?", the right fix is clearer code, not an explanation that lives only in the PR thread.
- For disagreements, facts and data beat opinions. If you are stuck, talk live, then escalate to the tech lead, and record the outcome in the PR.

## Exam traps (the ones that catch people)
- Green CI looks like "reviewed", but **linters only find patterns**. A human finds intent bugs, hard-coded secrets and missing tests. Both gates are required.
- "Review in production" sounds thorough, but **review happens before merge**, not after deployment.
- Pair programming and over-the-shoulder both involve two people at a desk, but **pairing reviews continuously while coding**, while over-the-shoulder happens **after** the code is written, with the author walking the reviewer through it.
- A fix after review looks like it needs a new PR, but **fixes go on the same branch**, which updates the same PR and re-runs CI.
- A huge PR looks efficient, but **a 2,000-line PR is a reason to ask for a split**, not to approve quickly.
- Arguing about whitespace looks like diligence, but **style belongs to tools**; put the rule in the linter or formatter.
- "It compiles and runs" looks like proof, but **PR #42 compiled, passed its old test and still had a logic bug**.
- Comment sounds like it blocks, but **only Request changes blocks**; Comment is neutral.

## Quick self-check
<details><summary>Q1. Name two real benefits of code review.</summary>Any two of: early defect and security detection, knowledge sharing, consistent standards, mentoring. Never "faster code" or "replaces testing".</details>
<details><summary>Q2. Two developers share one keyboard; one types and one checks each line. Which review type?</summary>Pair programming: continuous review while coding, with driver and navigator roles.</details>
<details><summary>Q3. Where does review sit relative to CI and merge?</summary>On the open PR, alongside CI; an approving review and passing checks are both required before merge.</details>
<details><summary>Q4. Which comment is best for `verify=False`?</summary>One that names the line, explains that it disables certificate checks so a man-in-the-middle could read the password, and suggests keeping verification on or passing the CA bundle.</details>
<details><summary>Q5. A PR reformats 40 files and changes retry logic in one. What should the reviewer ask for?</summary>Split it into a formatting-only PR and a separate logic PR, so the real change is not hidden.</details>

## Cheat lines to say out loud
- "Review finds bugs early, spreads knowledge, keeps standards and mentors people; it never replaces tests."
- "Branch, push, PR, CI, review, fix on the same branch, approve, merge."
- "Tools own style; humans own logic, security and tests."
- "Pairing reviews while you type; a PR reviews after you push."
- "Talk about the line, not the person, and label it blocking or nit."
