# T31 · Bash: essentials

> Blueprint 4.11: Bash commands (files, navigation, environment variables); 5.9: interpret Bash script workflows · Full note: [bee/T31-bash.md](../bee/T31-bash.md) · Teach-back 2026-11-01

![T31 at a glance: every Bash concept on one page](../assets/T31/00-overview.png)

*Each row is one concept area; the numbered examples are lines from `labs/T31/device_report.sh`, and the red boxes are the exam traps.*

## The big idea
- Bash is home turf, so this page is the exam's angle only. The exam asks **two kinds of question**:
  - **4.11: pick the right command** for a file, navigation or environment-variable task.
  - **5.9: read a short script** and say what it does, what it prints and what exit code it returns.
- **Analogy: a script is a recipe card with three outputs.** What goes into **files**, what goes on **screen** (stdout vs stderr), and **one number at the end** (the exit status). Most wrong answers come from mixing up those three channels.
- **Analogy for variables: a note on the fridge vs a note in the kids' lunchbox.** `VAR=x` is on the fridge: only this shell sees it. `export VAR=x` goes in every child's lunchbox. A child can read its copy but can never change the note on the parent's fridge.
- **What the exam asks:** the right flag (`-p`, `-r`), what `>` vs `>>` and `2>&1` leave in a file, why a child can't see a variable, and the `$?` / exit code after a line runs.

## 🟥 Must know

### 1. Navigation and the 4.11 command picks
- `cd` alone (or `cd ~`) = home. `cd ..` = up one. **`cd -` = the previous directory** (`$OLDPWD`), not "up one".
- **Exam-sim gap (practice-test review): `pushd` / `popd` = a directory stack.**

```bash
pushd /etc/ansible     # save where I am on the stack, then jump to /etc/ansible
popd                   # pop the stack: jump back to where I was
```

  - Nest them to visit several directories and return in order; `dirs -v` shows the stack.
  - `cd -` only swaps the **last two** directories; `pushd` remembers a whole stack.
  - Exam cue: "temporarily change directory and return later" → **`pushd`** (then `popd`).
- Absolute path starts at `/` (`/etc/hosts`); relative starts at the current directory (`./script.sh`, `../labs`).

| Task | Command | Trap |
|---|---|---|
| create nested dirs | `mkdir -p backups/2026/oct` | without `-p`, missing parents give an error |
| copy a folder | `cp -r backups backups-copy` | without `-r`: "is a directory" |
| move or rename | `mv csr1.cfg csr1-running.cfg` | same command for both |
| delete a non-empty folder | `rm -r backups-copy` | `rmdir` only removes **empty** dirs |
| last 20 lines, then follow a log | `tail -n 20 -f /var/log/syslog` | default is 10 lines |
| lines **without** a pattern | `grep -v ntp csr1-running.cfg` | `-i` ignore case, `-r` recurse |
| find files by name | `find . -name "*.yaml"` | quote the pattern or the shell expands it first |
| make a script runnable | `chmod +x device_report.sh` | |
| var visible to child processes | `export NETBOX_TOKEN=abc123` | |
| reload shell config | `source ~/.bashrc` | |

### 2. Permissions
- `-rwxr-xr-x` = file type, then three triplets: **user (owner) · group · other**. Octal: r = 4, w = 2, x = 1, one digit per triplet.

| Octal | Symbolic | Typical use |
|---|---|---|
| `755` | `rwxr-xr-x` | scripts, directories |
| `644` | `rw-r--r--` | config and data files |
| `700` | `rwx------` | private script or dir |
| `600` | `rw-------` | private keys, `.env` with tokens |

- `chmod +x f` = execute for everyone; `chmod u+x f` = owner only. On a directory, `x` = may `cd` into it, `r` = may list it.
- **No execute bit:** `./script.sh` → "Permission denied", exit **126**. `bash script.sh` still works, because Bash only needs to **read** the file.

### 3. Variables: who can see them
- The fridge-vs-lunchbox rule as a table:

| Form | Who sees it |
|---|---|
| `VAR=value` | this shell only (a **shell variable**) |
| `export VAR=value` | this shell and every child process |
| `VAR=value cmd` | that one command only |
| `local var` (inside a function) | that function only |

- **No spaces around `=`.** `VAR = x` runs a command called `VAR` with arguments `=` and `x`.
- **Defaults from the environment:**

```bash
API_BASE=${API_BASE:-http://127.0.0.1:8131}   # use $API_BASE if set and non-empty, else the default
```

- `env` / `printenv` list **exported** variables only; `set` lists everything; `unset VAR` deletes one.
- **`PATH`** = colon-separated dirs, searched left to right. Missing command → exit **127**.
  - `PATH=/my/bin` without `:$PATH` wipes the search path; every other command disappears.
  - `./script.sh` needs the `./` because the current directory isn't in `PATH`.
- **Persist** in `~/.bashrc` or `~/.profile`; `source ~/.bashrc` reloads into the **current** shell.
- **`source file` vs `bash file`:** `bash vars.sh` runs in a child shell, so its variables die with it. `source vars.sh` runs in your shell, so they stay. A child can never change its parent's variables.

### 4. Redirection: where output goes
- File descriptors: **0** stdin, **1** stdout, **2** stderr.

| Syntax | Effect |
|---|---|
| `> file` | create or **wipe**, then write |
| `>> file` | create or **append** |
| `< file` | feed the file in as input |
| `a \| b` | send a's **stdout only** into b |
| `>&2` | send this message to stderr |
| `2> file` | stderr only into the file |
| `2>&1` | point stderr wherever stdout points **right now** |
| `&> file` | Bash shorthand for `> file 2>&1` |

- **Order matters**, read left to right:

```bash
ls /nope > out1.txt 2>&1     # stdout → file, THEN stderr copies that → error is in the file
ls /nope 2>&1 > out2.txt     # stderr copies stdout's target (the terminal) FIRST → error on screen, file empty
cmd 2>&1 | grep err          # pipe is set up first, so 2>&1 here sends errors into the pipe
```

![2>&1 order](../assets/T31/02-redirect-order.png)

*`2>&1` copies wherever stdout points at that moment, so it must come after `> file` to catch errors.*

- `>` inside a loop wipes the file on every pass, so only the last line survives.
- Well-written scripts send data to stdout and log messages to stderr (`>&2`), so `./script.sh > out.txt` captures the data while messages stay on screen.

### 5. Script anatomy: shebang, arguments, exit codes
- **Shebang** on line 1: `#!/bin/bash` (the exam form). `bash script.sh` ignores it. Run: `chmod +x device_report.sh`, then `./device_report.sh devices.csv`.

| Param | Meaning |
|---|---|
| `$0` | the name the script was called with |
| `$1`, `$2` | positional arguments (inside a function, the function's own arguments) |
| `$#` | how many arguments |
| `"$@"` | every argument, each kept as one word |
| `"$*"` | every argument joined into **one** string |
| `$?` | exit status of the last command |

- With the arguments `"site a" b`: `"$@"` → 2 words (`site a`, `b`); `"$*"` → 1 (`site a b`); unquoted `$@` → 3 (`site`, `a`, `b`).
- **Exit status:** 0 = success, 1–255 = failure. `1` general error, `2` misuse, **`126`** found but not executable, **`127`** command not found.
- Status of a function = its last command (or `return N`). Pipeline = the **last** command's. Script = `exit N` or its last command's.
- **`$?` is overwritten by every command**, `echo` and `[` included:

```bash
grep -q zzz f.txt
echo "grep rc=$?"     # 1  (no match)
echo "now rc=$?"      # 0  (the first echo succeeded)
```

  - Save it on the very next line: `rc=$?`.

![Workflow of device_report.sh](../assets/T31/01-script-workflow.png)

*The lab script's flow, traced with a real run: red = failure paths, yellow = skipped, green = success. This is the shape of a 5.9 answer.*

### 6. Tests, loops, substitution and quotes
- `if` runs a command and branches on its exit status (0 = true). `[` is a command, so it needs spaces: `[ -f "$f" ]`, never `[-f "$f"]`.
  - Files: `-f` regular file, `-d` directory, `-e` exists. Strings: `-z` empty, `-n` non-empty, `==`, `!=`. **Numbers: `-eq -ne -lt -le -gt -ge`.**
- **Loops:**

```bash
for inventory in "$@"; do ... done                       # each argument, spaces preserved
while IFS=, read -r host ip os; do ... done < devices.csv  # read a CSV line by line
```

  - `IFS=,` splits on commas for this `read` only; `-r` keeps backslashes; `< devices.csv` feeds the file to the loop.
  - `continue` = next pass; `break` = leave the loop.
- `$(command)` drops a command's output into the line. `$((failed + 1))` does integer maths; `x=5+1` stores the text `5+1`.
- **Quotes:** double quotes expand `$var` and `$(cmd)` and keep spaces together. Single quotes keep everything literal: `'$host'` prints `$host`.

### 7. Reading a script on the exam (5.9)
- Trace in this order:
  1. Shebang and defaults (`${VAR:-default}`).
  2. Argument checks (`$#`, `usage`, `exit 2`).
  3. What the loops iterate over (`"$@"`, file lines via `< file`).
  4. Which branch writes what, and where (`>` vs `>>`, stdout vs stderr).
  5. The final output and the **exit status**.
- "What's in the file?" → check `>` vs `>>`, the position of `2>&1`, and whether messages go to `>&2`.
- "What's the exit code?" → the last command's: last in the pipeline, last in the function, or the explicit `exit N`.

## Exam traps
- **`cmd 2>&1 > f` leaves errors on screen**; `cmd > f 2>&1` catches both. And `cmd | grep error` misses stderr; write `cmd 2>&1 | grep error`.
- **`$?` changes after every command**, so a second `echo "rc=$?"` prints `0`. Save it straight away: `rc=$?`.
- **`VAR=x` doesn't reach a child program**; only `export` does. `bash vars.sh` can't set your shell's variables; `source vars.sh` can.
- **`cd -` = previous directory**, not up (`cd ..`). "Change directory temporarily and come back" → **`pushd` / `popd`**.
- **`[[ 10 > 9 ]]` is false** (string compare); use `-gt` for numbers. In `[ ]`, `>` even creates a file named `9`.
- **126 = not executable** (`chmod +x`); **127 = not found** (not in `PATH`, use `./`). Always quote `"$@"` and `"$var"`.

<details><summary><b>🟨 Should know (second pass)</b></summary>

- **`[ ]` vs `[[ ]]`:**

| | `[ ]` (`test`) | `[[ ]]` (Bash keyword) |
|---|---|---|
| Works in plain `sh` | yes | no |
| Unquoted variable with spaces | breaks with an error | safe |
| Patterns and regex | no | `[[ $name == core* ]]`, `=~` |
| `<` and `>` | redirection (creates a file!) | string order, so `[[ 10 > 9 ]]` is false |

  - `[ $a == b ]` with an empty `$a` → `unary operator expected`.
- **`local` hides failures:** `local json=$(curl ...)` returns the status of `local` (always 0), not of `curl`, so a following `|| return` never fires. Declare `local json` first, then assign on a separate line.
- **`grep` exit codes:** `0` = match, `1` = no match, `2` = error. That's why `grep -q pattern file && echo found` works.
- **`sudo echo x > /etc/f` fails**, because your own shell does the redirect, not sudo. Use `echo x | sudo tee /etc/f`. `chown beedy:netops report.csv` changes owner and group and needs `sudo`.
- **Shebang variants:** `#!/usr/bin/env bash` picks the first `bash` in `PATH`. `sh script.sh` may not be Bash (Debian/Ubuntu: `dash`), so `[[ ]]` and `==` can fail there.
- **More file commands:** `ls -l` (long), `ls -a` (hidden dot-files), `ls -la` (both); `touch f` creates an empty file or updates its mtime; `head -n 1 f`; `grep -r -i "NTP" .`.
- **Exit code `128+N`** = killed by signal N (130 = Ctrl-C).
- **The exam assumes Linux GNU tools.** On macOS, `sed -i` and `date -d` behave differently, and `/bin/bash` is the old 3.2.

</details>

> **Recognise only, details in the full note:** `awk -F,` / `cut -d` / `wc -l < file` field tricks, `set -o pipefail`, `command -v` vs `which`, `~/.bashrc` vs `~/.bash_profile` (login vs non-login), BSD `sed -i ''` and `date -v`, Bash 4+ features (`declare -A`, `mapfile`, `${var,,}`), curl exit codes 7 and 22, the `ping` no-reply exit code (⚠ verify, platform-dependent).

## Quick self-check
<details><summary>Q1. A loop runs <code>echo "$h" &gt; report.csv</code> for three hosts, then <code>echo done &gt;&gt; report.csv</code>. What is in the file?</summary>The last host and <code>done</code>. <code>&gt;</code> wipes the file on every pass, and <code>&gt;&gt;</code> appends once.</details>
<details><summary>Q2. Which sends both streams to a log: <code>cmd 2&gt;&amp;1 &gt; log</code> or <code>cmd &gt; log 2&gt;&amp;1</code>?</summary><code>cmd &gt; log 2&gt;&amp;1</code>. <code>2&gt;&amp;1</code> copies stdout's target at that moment, so it must come after <code>&gt; log</code>.</details>
<details><summary>Q3. <code>TOKEN=abc</code>, then a Python child prints <code>None</code> for <code>TOKEN</code>. One fix?</summary><code>export TOKEN</code>. A plain shell variable is not passed to child processes.</details>
<details><summary>Q4. What does <code>chmod 744 deploy.sh</code> give?</summary><code>rwxr--r--</code>: the owner can run it, and group and other can only read.</details>
<details><summary>Q5. Called with <code>"Gi1/0/1 uplink" Gi1/0/2</code>, how many times does <code>for p in "$@"</code> loop?</summary>Twice. <code>"$@"</code> keeps each argument whole; unquoted it would loop three times.</details>
<details><summary>Q6. A script must <code>cd</code> into a work directory, do a job, then return to wherever the user was. Which commands?</summary><code>pushd "$WORKDIR"</code> then <code>popd</code>. The directory stack remembers where you came from.</details>
<details><summary>Q7. <code>./backup.sh</code> gives "Permission denied". What is <code>$?</code> and the fix?</summary><code>126</code>: found but not executable. <code>chmod +x backup.sh</code> (or run <code>bash backup.sh</code>).</details>

## Say it out loud
- "Single greater-than wipes, double appends, and a pipe only carries stdout."
- "Two-and-one goes **after** the file, because it copies stdout's target at that moment."
- "Save dollar-question-mark straight away, because the next command overwrites it."
- "Export to share with children; source to change my own shell."
- "126 means not executable, 127 means not found."
