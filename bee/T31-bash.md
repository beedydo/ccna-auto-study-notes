---
id: T31
title: "Bash"
owner: Beedy
blueprint: "4.11, 5.9"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-15
teach_back: 2026-10-16
cross_study: 2026-10-23
---

# T31 · Bash

> Owner: **Beedy** · Blueprint: **4.11, 5.9** · CBT coverage: **Full** · Learn by 2026-10-15 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T31.01 · Navigation

**Must cover:**

- [ ] pwd, cd ~ / cd .. / cd - (previous dir)
- [ ] ls -l (long), -a (hidden), -la
- [ ] Absolute (/etc/hosts) vs relative (./script.sh) paths

**Notes:**

<!-- TODO -->

### T31.02 · File management

**Must cover:**

- [ ] touch, mkdir -p a/b/c, cp -r, mv (move/rename), rm -r, rmdir
- [ ] cat, less, head -n, tail -n / tail -f
- [ ] grep pattern file (-i, -r, -v); find /path -name "*.py"

**Notes:**

<!-- TODO -->

### T31.03 · Permissions

**Must cover:**

- [ ] ls -l shows rwx for user/group/other
- [ ] chmod 755 file = rwxr-xr-x; chmod +x script.sh
- [ ] chown user:group file; sudo runs as root

**Notes:**

<!-- TODO -->

### T31.04 · Environment variables

**Must cover:**

- [ ] VAR=value (shell only) vs export VAR=value (passed to child processes)
- [ ] echo $VAR; env / printenv list them; unset VAR
- [ ] PATH lists dirs searched for commands
- [ ] Persist in ~/.bashrc or ~/.profile; source ~/.bashrc reloads

**Notes:**

<!-- TODO -->

### T31.05 · Redirection

**Must cover:**

- [ ] > overwrite file; >> append; < read input from file
- [ ] | pipes stdout into the next command
- [ ] 2> redirects stderr; 2>&1 merges stderr into stdout

**Notes:**

<!-- TODO -->

### T31.06 · Scripts

**Must cover:**

- [ ] #!/bin/bash shebang on line 1; chmod +x then ./script.sh
- [ ] $0 script name; $1 $2 positional args; $# count; $@ all args
- [ ] $? exit status of last command (0 = success)

**Notes:**

<!-- TODO -->

### T31.07 · Scripts

**Must cover:**

- [ ] if [ -f file ]; then …; fi; [ "$a" == "$b" ]
- [ ] for i in 1 2 3; do …; done; while …; do …; done
- [ ] $(command) captures output; double quotes expand variables, single quotes do not

**Notes:**

<!-- TODO -->

### T31.08 · Exam angle

**Must cover:**

- [ ] Read a short script and state its workflow or output
- [ ] Pick the command for a file/directory/env-var task

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

- Practice Qs only (known topic or no dedicated aid).

- Skip / low priority: Whole video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
