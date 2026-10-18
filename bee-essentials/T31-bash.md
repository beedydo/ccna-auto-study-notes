# T31 · Bash: essentials

> Blueprint 4.11, 5.9 · Full note: [bee/T31-bash.md](../bee/T31-bash.md) · Teach-back 2026-11-01

## In one picture
![T31 at a glance: every Bash concept on one page](../assets/T31/00-overview.png)
*Each row is one concept area; the numbered examples are lines from `labs/T31/device_report.sh`, and the red boxes are the exam traps.*

## The big idea
- Bash is home turf, so this page is about the exam's angle, not the basics. The exam asks two kinds of question.
- Blueprint 4.11 asks you to **pick the right command** for a file, navigation or environment-variable task.
- Blueprint 5.9 asks you to **read a short script** and say what it does, what it prints and what exit code it returns.
- Think of a script as a recipe card with three outputs: what goes into files, what goes on screen, and a single number at the end (the exit status). Most wrong answers come from mixing up those three channels.

## What you need to know

### 1. Getting around and handling files (4.11)
- `pwd` prints where you are. `cd` on its own (or `cd ~`) goes home, `cd ..` goes up one level, and `cd -` jumps back to the **previous** directory (it is not "up one").
- `ls -l` gives the long listing (permissions, owner, size, time), `ls -a` includes hidden dot-files, and `ls -la` does both.
- An **absolute path** starts at `/` (`/etc/hosts`) and means the same thing from anywhere. A **relative path** starts from the current directory (`./script.sh`, `../labs`).
- From the practice-exam review: `pushd /etc/ansible` saves where you are and jumps there, and `popd` jumps back. This is a **directory stack**, so it can remember several places, while `cd -` only swaps the last two. Exam cue: "temporarily change directory and return later" means **`pushd`**.

| Task | Command | Trap |
|---|---|---|
| create nested dirs | `mkdir -p backups/2026/oct` | without `-p`, missing parents give an error |
| copy a folder | `cp -r backups backups-copy` | without `-r`: "is a directory" |
| move or rename | `mv csr1.cfg csr1-running.cfg` | same command for both |
| delete a non-empty folder | `rm -r backups-copy` | `rmdir` only removes **empty** dirs |
| first / last lines, follow a log | `head -n 1 f`, `tail -n 20 -f /var/log/syslog` | default is 10 lines |
| lines **without** a pattern | `grep -v ntp csr1-running.cfg` | `-i` ignore case, `-r` recurse |
| find files by name | `find . -name "*.yaml"` | quote the pattern or the shell expands it first |

- `grep` also has exit codes you can test: **0** = a match was found, **1** = no match, **2** = an error. That is why `grep -q pattern file && echo found` works.

### 2. Permissions
- The first column of `ls -l`, such as `-rwxr-xr-x`, is the file type followed by three triplets for **user (owner), group and other**.
- In octal, read = 4, write = 2 and execute = 1, with one digit per triplet.

| Octal | Symbolic | Typical use |
|---|---|---|
| `755` | `rwxr-xr-x` | scripts, directories |
| `644` | `rw-r--r--` | config and data files |
| `700` | `rwx------` | private script or dir |
| `600` | `rw-------` | private keys, `.env` with tokens |

- `chmod +x f` adds execute for everyone, `chmod u+x f` only for the owner. On a directory, `x` means you may `cd` into it and `r` means you may list it.
- `chown beedy:netops report.csv` changes owner and group, and needs `sudo`.
- `sudo echo x > /etc/f` **fails**, because your own shell does the redirect, not sudo. Use `echo x | sudo tee /etc/f`.
- If a script has no execute bit, `./script.sh` gives "Permission denied" and exit code **126**. `bash script.sh` still works, because Bash only needs to read the file.

### 3. Variables and who can see them
- A plain variable lives in the current shell only. `export` hands it down to child processes (a Python script, a sub-shell). A child can never change its parent's variables.

| Form | Who sees it |
|---|---|
| `VAR=value` | this shell only (a **shell variable**) |
| `export VAR=value` | this shell and every child process |
| `VAR=value cmd` | that one command only |
| `local var` (inside a function) | that function only |

- There must be **no spaces** around `=`. `VAR = x` tries to run a command called `VAR`.
- `${API_BASE:-http://127.0.0.1:8131}` means "use the variable if it is set and non-empty, otherwise use the default". This is how a script reads config from the environment.
- `env` and `printenv` list only **exported** variables. `set` lists everything. `unset VAR` deletes one.
- **`PATH`** is a colon-separated list of directories searched left to right. A missing command gives exit code **127**. Writing `PATH=/my/bin` without `:$PATH` wipes the search path, and every other command disappears.
- `./script.sh` needs the `./` because the current directory is not in `PATH`.
- To make a variable permanent, put `export VAR=value` in `~/.bashrc` or `~/.profile`. `source ~/.bashrc` reloads it into the **current** shell.
- **`source file` vs `bash file`:** `bash vars.sh` runs in a child shell, so its variables die with it. `source vars.sh` runs in your shell, so they stay.

### 4. Redirection: where output goes
- Every command has three streams, numbered as **file descriptors**: 0 = stdin (input), 1 = stdout (normal output), 2 = stderr (errors).

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

- Well-written scripts send data to stdout and log messages to stderr, so `./script.sh > out.txt` captures the data while the messages stay on screen.
- **Order matters**, because redirections are read left to right:

![2>&1 order](../assets/T31/02-redirect-order.png)
*`2>&1` copies wherever stdout points at that moment, so it must come after `> file` to catch errors.*

- `cmd > f 2>&1` puts both streams in the file. `cmd 2>&1 > f` leaves errors on screen.
- To grep error text through a pipe, write `cmd 2>&1 | grep err`. Here `2>&1` comes first because the pipe is set up before the redirections.
- Using `>` inside a loop wipes the file on every pass, so only the last line survives.

### 5. Script basics: shebang, arguments, exit codes
- The **shebang** must be line 1 and start with `#!`. `#!/bin/bash` is the exam form; `#!/usr/bin/env bash` picks the first `bash` in `PATH`. Running `bash script.sh` ignores the shebang.
- To run a script: `chmod +x device_report.sh`, then `./device_report.sh devices.csv`.

| Param | Meaning |
|---|---|
| `$0` | the name the script was called with |
| `$1`, `$2` | positional arguments (inside a function, the function's own arguments) |
| `$#` | how many arguments |
| `"$@"` | every argument, each kept as one word |
| `"$*"` | every argument joined into **one** string |
| `$?` | exit status of the last command |

- With the arguments `"site a" b`: `"$@"` gives two words (`site a`, `b`), `"$*"` gives one (`site a b`), and unquoted `$@` gives three (`site`, `a`, `b`).
- **Exit status:** 0 = success, anything 1–255 = failure. Conventions: 1 = general error, 2 = misuse, **126** = found but not executable, **127** = command not found, 128+N = killed by signal N.
- A function returns its last command's status (or `return N`). A pipeline returns the **last** command's status. A script returns `exit N` or its last command's status.
- **`$?` is overwritten by every command**, even `echo` and `[`. Save it on the very next line: `rc=$?`.
- `local json=$(curl ...)` hides curl's failure, because the line's status is that of `local` (always 0). Declare first, then assign on a separate line.

![Workflow of device_report.sh](../assets/T31/01-script-workflow.png)
*The lab script's flow, traced with a real run: red = failure paths, yellow = skipped, green = success. This is the shape of a 5.9 answer.*

### 6. Tests, loops, substitution and quotes
- `if` runs a command and branches on its exit status (0 = true). `[` is itself a command, so it needs spaces: `[ -f "$f" ]`, never `[-f "$f"]`.
- File tests: `-f` regular file, `-d` directory, `-e` exists. String tests: `-z` empty, `-n` non-empty, `==` and `!=`. Number tests: `-eq -ne -lt -le -gt -ge`.

| | `[ ]` (`test`) | `[[ ]]` (Bash keyword) |
|---|---|---|
| Works in plain `sh` | yes | no |
| Unquoted variable with spaces | breaks with an error | safe |
| Patterns and regex | no | `[[ $name == core* ]]`, `=~` |
| `<` and `>` | redirection (creates a file!) | string order, so `[[ 10 > 9 ]]` is false |

- `for x in list; do ...; done` loops over a list. `while IFS=, read -r host ip os; do ... done < file` is the standard way to read a CSV line by line. `continue` skips to the next pass and `break` leaves the loop.
- `$(command)` runs a command and drops its output into the line. `$((failed + 1))` does integer maths; plain `x=5+1` stores the text `5+1`.
- **Quotes:** double quotes expand `$var` and `$(cmd)` and keep spaces together. Single quotes keep everything literal, so `'$host'` prints `$host`.
- The exam assumes Linux GNU tools. On macOS, `sed -i` and `date -d` behave differently, and `/bin/bash` is the old 3.2.

### 7. Reading a script on the exam (5.9)
- Trace it in this order: (1) shebang and defaults, (2) argument checks, (3) what the loops iterate over, (4) which branch writes what, and where (`>` vs `>>`, stdout vs stderr), (5) the final output and the **exit status**.
- For "what's in the file?" questions, check `>` vs `>>`, the position of `2>&1`, and whether messages go to `>&2`.

## Exam traps (the ones that catch people)
- `cmd 2>&1 > f` looks like it captures errors, but it doesn't, because `2>&1` copied stdout's target (the terminal) before stdout moved to the file.
- `cmd | grep error` looks like it searches errors, but pipes carry stdout only. You need `cmd 2>&1 | grep error`.
- `echo "rc=$?"` twice looks like it prints the same number twice, but the second shows `0`, because the first `echo` overwrote `$?`.
- `VAR=x` then running a child program looks like it should pass `VAR`, but it doesn't, because only `export` reaches child processes.
- `cd -` looks like "go up", but it is "go to the previous directory". Up is `cd ..`.
- `[[ 10 > 9 ]]` looks true, but it is false, because `>` inside `[[ ]]` compares strings. Use `-gt` for numbers. In `[ ]`, `>` even creates a file named `9`.
- "Permission denied" on `./script.sh` (exit 126) means the execute bit is missing. "command not found" (exit 127) means it isn't in `PATH`, so use `./`.
- Unquoted `$@` looks harmless, but it splits a path with spaces into several words. Always write `"$@"` and `"$var"`.

## Quick self-check
<details><summary>Q1. A loop runs `echo "$h" > report.csv` for three hosts, then `echo done >> report.csv`. What is in the file?</summary>The last host and `done`. `>` wipes the file on every pass, and `>>` appends once.</details>
<details><summary>Q2. Which form sends both stdout and stderr to a log: `cmd 2>&1 > log` or `cmd > log 2>&1`?</summary>`cmd > log 2>&1`. `2>&1` copies stdout's target at that moment, so it must come after `> log`.</details>
<details><summary>Q3. `TOKEN=abc`, then a Python child prints `None` for `TOKEN`. One fix?</summary>`export TOKEN`. A plain shell variable is not passed to child processes.</details>
<details><summary>Q4. What does `chmod 744 deploy.sh` give?</summary>`rwxr--r--`: the owner can run it, and group and other can only read.</details>
<details><summary>Q5. Called with `"Gi1/0/1 uplink" Gi1/0/2`, how many times does `for p in "$@"` loop?</summary>Twice. `"$@"` keeps each argument whole; unquoted it would loop three times.</details>

## Cheat lines to say out loud
- "Single greater-than wipes, double appends, and a pipe only carries stdout."
- "Two-and-one goes **after** the file, because it copies stdout's target at that moment."
- "Save dollar-question-mark straight away, because the next command overwrites it."
- "Export to share with children; source to change my own shell."
- "126 means not executable, 127 means not found."
