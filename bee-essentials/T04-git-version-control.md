# T04 · Git + version control: essentials

> Blueprint 1.7, 1.8 · Full note: [bee/T04-git-version-control.md](../bee/T04-git-version-control.md) · Teach-back 2026-10-11

## In one picture
![Git four areas](../assets/T04/01-four-areas.png)
*Read left to right to save work (`add`, `commit`, `push`) and right to left to get work back (`fetch`, `pull`, `restore`). There is no separate overview image for T04, so this diagram stands in for it.*

## The big idea
Version control is a full, signed logbook of every change to your code, so you can see who changed what and why, roll back, and work in parallel without overwriting each other. Git is **distributed**: every clone carries the whole logbook, so you can commit on a plane and sync later. You use Git daily, so the exam value here is in the confusable pairs (`rm` vs `rm --cached`, `reset` vs `revert`, `fetch` vs `pull`, `diff` vs `diff --staged`) and in putting a workflow in the right order.

## What you need to know

### 1. Why version control, and centralised vs distributed (1.7)
- The exam answer to "advantages of version control" is: a history and audit trail, rollback, parallel work on branches, collaboration and review, and a trigger for automation.
- Every commit records the **author, timestamp, message, parent and a snapshot**, which answers who, what, when and why.
- A shared remote (GitHub, GitLab) enables **pull requests** and code review (T46). CI/CD pipelines (T28) trigger on push or merge, which makes version control the foundation of NetDevOps.
- Wrong answers say version control makes code run faster, encrypts the code, or removes the need for testing.

| | Centralised (SVN, CVS) | Distributed (Git, Mercurial) |
|---|---|---|
| Where full history lives | Only on the central server | In **every** clone |
| Commit offline | No | Yes, commit locally and push later |
| Single point of failure | The server | None; any clone can restore it |
| Speed of log, diff, branch | Network-bound | Local and fast |
| Cost | Simpler model | You must push and pull to share |

- Exam cue: "a developer on a plane commits changes" means **distributed**.

![Centralised vs distributed](../assets/T04/03-centralised-vs-distributed.png)
*Centralised: only the server holds history. Distributed: every clone is a full backup.*

### 2. The Git model: four areas and file states
- The **working directory** is the files you edit. The **staging area** (also called the **index**, stored in `.git/index`) holds the changes picked for the next commit, so you can commit some changes and not others.
- The **local repository** is the `.git/` folder of committed snapshots; delete it and the folder stops being a repo. The **remote** is the shared copy, and `origin` is just the default name `git clone` gives it.
- A file moves through the states **untracked**, then **staged** (after `add`), then **committed** (after `commit`), then **modified** (after an edit), then staged again.
- `git status --short` codes: `??` untracked, ` M` modified but not staged, `M ` staged, `A ` new file staged, `D ` deletion staged.
- A commit ID is a **SHA-1 hash** (40 hex characters; `--oneline` shows the first 7). Any change to content, metadata or parent gives a new hash. ⚠ verify: Git also supports SHA-256 repos; SHA-1 remains the default, so use SHA-1 for the exam.
- **HEAD** is a pointer to your current branch, which in turn points to its latest commit. `HEAD~1` is the parent. A **detached HEAD** means HEAD points straight at a commit (for example after `git checkout <sha>`).

![HEAD and branches](../assets/T04/04-head-branches.png)
*HEAD points to a branch, the branch points to a commit, and each commit points back to its parent. Branches are just labels.*

### 3. Starting, changing and inspecting
- `git init` creates `.git/` with no remote. `git clone <url>` downloads the full history and **adds `origin` automatically**. After `init` you need `git remote add origin <url>` before you can push; after `clone` you don't. `git remote -v` lists remotes.
- `git config --global user.name "Beedy"` writes to `~/.gitconfig`; without `--global` it applies to this repo only (`.git/config`).
- `git add .` stages new, modified and deleted files from the current folder down; `git add -A` covers the whole repo.
- `git rm <file>` deletes the file from disk **and** stages the deletion. `git rm --cached <file>` stops tracking it but **keeps it on disk**. The classic fix for a committed `.env` is `git rm --cached .env`, add it to `.gitignore`, and commit. The secret is still in history, so rotate it.
- `git mv old new` renames and stages in one step.
- `git commit -m "msg"` commits only what is staged. `git commit -a -m "msg"` auto-stages **tracked** files but **does not add untracked files**.
- `git log --oneline --graph` shows compact history with a branch graph. `git show <commit>` shows one commit's details plus its diff.

| Command | Compares | So it shows |
|---|---|---|
| `git diff` | working directory vs staging | unstaged changes |
| `git diff --staged` (same as `--cached`) | staging vs last commit | what the next commit will contain |
| `git diff HEAD` | working directory vs last commit | all uncommitted changes |
| `git diff a b` | two commits or branches | changes between them |

- After `git add`, plain `git diff` prints **nothing**, because the changes moved to `--staged`. Reading the diff output itself is T05.

### 4. Syncing with a remote
- `git push origin <branch>` uploads local commits; `git push -u origin <branch>` the first time also sets the upstream.
- `git fetch` downloads remote commits into the **remote-tracking branch** `origin/<branch>`. Your own branch and your files are **untouched**, so it is a safe "look before you merge".
- `git pull` is `git fetch` plus integrate: a merge, or a rebase if `--rebase` or `pull.rebase=true` is set.
- ⚠ verify: current git-pull docs say the default with no config is **fast-forward only**, so `pull` fails with a "divergent branches" hint when both sides have new commits (confirmed on Git 2.54). The exam still expects **pull = fetch + merge**.
- A push rejected as "non-fast-forward" means someone pushed first: `pull`, then `push`.

![fetch vs pull](../assets/T04/08-fetch-vs-pull.png)
*`fetch` stops at `origin/main`; `pull` goes one step further and merges into your branch.*

### 5. Branching, merging and conflicts
- A branch is a lightweight, movable pointer to a commit, so creating one is instant.
- `git branch` lists branches (`*` marks the current one). `git branch <name>` creates a branch but **does not switch** to it. `git checkout -b <name>` or `git switch -c <name>` creates **and** switches. `git branch -d` deletes a merged branch (refuses if unmerged); `-D` forces it.
- `switch` and `restore` (Git 2.23) split up the overloaded `checkout`; the exam may show either.
- `git merge <branch>` merges that branch **into the branch you are on**, so run `git switch main` first, then `git merge feature`.
- **Fast-forward**: main has no new commits since the branch split, so the pointer just slides forward and no merge commit is made. **Merge commit**: both sides moved, so Git makes a new commit with **two parents**, reported as `Merge made by the 'ort' strategy.` (older Git says `'recursive'`, same meaning). `--no-ff` forces a merge commit anyway.
- **Rebase** (awareness only) replays your commits on top of another branch for a straight-line history, which **rewrites hashes**, so don't rebase shared branches.
- A **conflict** happens when both branches changed the same lines (or one edited and one deleted). Different lines or files merge automatically.

```
<<<<<<< HEAD
hostname R1-CORE        <- current branch (the one you are merging INTO)
=======
hostname R1-EDGE        <- incoming branch
>>>>>>> feature
```

- To resolve: edit the file, keep the lines you want, delete all three marker lines, then `git add <file>` and `git commit`. Committing without the `add` doesn't work. `git merge --abort` bails out.

![Merge commit](../assets/T04/05b-merge-commit.png)
*Both branches moved (`c3` and `e5`), so Git creates `m6` with two parents.*

### 6. Undoing things
- `reset` moves the branch pointer back, which **rewrites history**, so keep it for local work.

| `git reset` mode | HEAD moves | Staging | Working files |
|---|---|---|---|
| `--soft` | yes | changes **stay staged** | kept |
| `--mixed` (the default) | yes | changes **unstaged** | kept |
| `--hard` | yes | wiped | **wiped (lost)** |

- `git revert <sha>` makes a **new commit** that undoes the old one, leaving history intact, so it is **safe on shared, pushed branches**.
- "Undo a bad commit already pushed to main" means `revert`. "Undo my last local commit but keep the work" means `reset --soft HEAD~1`.
- `git restore <file>` (old form `git checkout -- <file>`) throws away working-directory edits. `git restore --staged <file>` (or `git reset <file>`) unstages but keeps the edits.

![reset modes vs revert](../assets/T04/07-reset-modes.png)
*Green to red shows how much you lose; blue is revert, the only one safe after a push.*

### 7. Other tools and the team workflow (1.8)
- `.gitignore` lists patterns Git should not track (`*.pyc`, `venv/`, `.env`, `__pycache__/`). It only affects **untracked** files; an already-tracked file needs `git rm --cached` first.
- `git stash` shelves uncommitted changes and leaves a clean working directory. `git stash pop` applies and drops the stash; `git stash apply` applies and keeps it.
- `git tag v1.0` puts a lightweight tag on HEAD; `git tag -a v1.0 -m "msg"` makes an annotated one. Tags are not pushed by plain `git push`; use `git push origin v1.0`.
- A **fork** is a server-side copy of someone else's repo under your account (a GitHub/GitLab feature, not a Git command). A **clone** is a local copy. A **pull request** asks the upstream owner to merge your branch.
- The canonical order for drag-and-drop questions: **clone, branch (`switch -c`), edit, add, commit, push, open pull request, review, merge**.

![Pull request workflow](../assets/T04/09-pr-workflow.png)
*The full team flow, which is also the answer to the ordering questions.*

## Exam traps (the ones that catch people)
- Looks like `git rm` just stops tracking a file, but it also **deletes it from disk**; `git rm --cached` is the one that keeps it.
- Looks like `reset` is the normal undo, but on a pushed branch the right answer is `revert`, because reset rewrites history others already have.
- Looks like `fetch` updates your branch, but it only updates `origin/<branch>`; `pull` is the one that merges.
- Looks like `git diff` shows everything you changed, but after `git add` it is **empty**; use `git diff --staged`.
- Looks like `git commit -a` commits everything, but it **skips untracked** files.
- Looks like `git branch x` moves you to `x`, but it only creates it; use `git switch -c x` to create and switch.
- Looks like `.gitignore` will untrack a committed file, but it only affects untracked files.
- Looks like the top half of a conflict is the incoming change, but the `HEAD` half is **your current branch**.

## Quick self-check
<details><summary>Q1. Which command shows what will go into the next commit after `git add`?</summary>`git diff --staged`; it compares the staging area with the last commit.</details>
<details><summary>Q2. Which reset mode undoes the last commit but keeps its changes staged?</summary>`--soft`; `--mixed` unstages them and `--hard` deletes them.</details>
<details><summary>Q3. Which command downloads new commits without touching your branch or files?</summary>`git fetch`; it only updates the remote-tracking branches.</details>
<details><summary>Q4. You ran `git init`. What must you do before your first `git push`?</summary>`git remote add origin <url>`; only `clone` sets up `origin` for you.</details>
<details><summary>Q5. Name two advantages of distributed over centralised version control.</summary>You can commit offline, and every clone holds full history, so there is no single point of failure.</details>

## Cheat lines to say out loud
- "Working dir, add, staging, commit, local repo, push, remote."
- "Reset rewrites, revert records: revert for anything already pushed."
- "rm deletes, rm --cached keeps the file and just stops tracking."
- "Fetch looks, pull looks and merges."
- "HEAD on top is mine, the bottom half is theirs; edit, add, commit."
