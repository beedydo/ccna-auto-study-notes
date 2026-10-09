---
description: Draft the full study note for one topic (e.g. /note T07)
argument-hint: <topic-id e.g. T07>
---
Draft the study note for topic **$ARGUMENTS**.

## 1. Gather

1. Look up $ARGUMENTS in `data/topics.csv` to get `note_path`, owner, blueprint items, CBT coverage and skip list. Read the existing note at that path; it has front matter and a pre-filled **Must cover** checklist per concept ID.
2. Read the matching rows in `data/concepts.csv`, `data/study-aids.csv`, `data/blueprint-map.csv` (for the gap/action text) and `data/top-ups.csv` (if the topic appears there).
3. Research with official sources (developer.cisco.com, Cisco docs, RFCs, Python docs, Webex/Meraki docs) whenever the topic is platform-specific or version-sensitive. Keep the URLs.

## 2. Pick the backbone before writing

Decide how the note hangs together, so it reads as one story rather than fragments. Most topics use one of these, and some use both.

- **Code-heavy topic** (Python, parsing, `requests`, SDKs, tests, pyATS, Ansible, Bash): build **one reference program**.
  - Design a single realistic network-automation program that exercises every **Must cover** item, e.g. an inventory builder or a RESTCONF client.
  - Save it as runnable files in `labs/$ARGUMENTS/`.
  - Show the whole program, plus its real output, once at the top of `## Concepts`.
  - Every `### TXX.NN` section then explains its concept by pointing at named lines or functions in that program ("`build_inventory()` uses all four parameter kinds…"). It doesn't introduce new scattered snippets.
  - Use standalone snippets only for traps that can't live in a working program (e.g. a mutable default argument), and put them in `## Examples`.
- **Flow-heavy topic** (workflows, state changes, request/response, auth handshakes, pipelines, protocol sessions): add **rendered diagrams**.
  - Make one diagram per flow-heavy concept, aiming for about 5–10 per note. Good candidates: state lifecycle, before/after, decision flow, sequence of calls, comparison side by side.
  - Write Mermaid sources as `assets/$ARGUMENTS/NN-short-name.mmd`, then render each one to `.png` next to it (see §5).
  - Embed the image directly under the concept it explains, with a one-line italic caption saying what to notice:
    `![Alt text](../assets/$ARGUMENTS/NN-short-name.png)` then a blank line, then `*Caption.*`
  - Use colour to carry meaning, and keep it the same across diagrams: green = safe/kept, yellow = partial, red = destructive/error, blue = the recommended answer.
  - Prefer `flowchart` or `sequenceDiagram`. Avoid `gitGraph` with long commit labels, because they render rotated. Avoid circle nodes, because they balloon in size.

## 3. Fill the note (follow CLAUDE.md)

- Under each `### TXX.NN` concept, keep the checklist, tick `[x]` every item you explain, and write point-form **Notes:**.
  - From first principles for new areas.
  - Straight to exam angle for the owner's home-turf topics.
  - Use tables for comparisons, and the diagrams/program from §2 for flows and code.
- `## Exam traps`: at least 5 crisp traps (confused pairs, exact syntax, scenario → answer).
- `## Examples`:
  - Start with how to run the reference program (local command plus the Docker lab command), if there is one.
  - Then list a few **"break it on purpose"** edits (delete X → see error Y), short standalone trap snippets, and drills.
  - Use full runnable commands/code (curl, Python requests/ncclient/SDK, Docker). Target DevNet Sandbox hosts where relevant, with credentials read from env vars.
  - Every block must be **reproducible from the note alone**. Never show output without the commands that create the files and produce it.
- `## Practice questions`: 6-8 original exam-style Qs (mix of MCQ, drag-and-drop-as-ordering, complete-the-code). Answer + one-line explanation inside `<details>`. Where it fits, base questions on the reference program or a diagram.
- `## TL;DR (teach-back card)`: 3 key points + 1 trap, written last.
- `## Sources`: the URLs actually used. If diagrams exist, add a line pointing at `assets/$ARGUMENTS/*.mmd`. `## To verify`: every `⚠ verify` item.
- Cross-link related notes with relative links instead of repeating their content, e.g. `[T04.07](T04-git-version-control.md#t0407--commands-inspect)`.

## 4. Verify before reporting

- **Run everything you can.** Run the reference program, every drill, and every "break it" edit, in `$TMPDIR` or a throwaway copy. Paste the **real** output into the note.
  - If something can't run (sandbox host, network), say so in `## To verify`.
- After pasting code into the note, extract it back out and `diff` it against the `labs/` file, so the two never drift apart.
- Check that every file path the note references (`labs/...`, `assets/...`) exists.
- Third-party Python packages: install them into a throwaway venv under `$TMPDIR`, never into the system Python or the repo.
- Throwaway git repos: set `git config commit.gpgsign false` locally. Global signing fails inside the sandbox.

## 5. Rendering diagrams

- Render each `.mmd` to PNG with mermaid-cli at `--scale 2 --backgroundColor white`.
  - In this setup, install `@mermaid-js/mermaid-cli` into `$TMPDIR` with `PUPPETEER_SKIP_DOWNLOAD=1`.
  - Point it at system Chrome with a puppeteer config: `executablePath` = Google Chrome, a fresh `userDataDir`, `--no-sandbox`.
  - Headless Chrome only launches with the Bash sandbox disabled, and it only writes to `$TMPDIR` and `assets/`.
- **Look at every PNG** (Read the image). Redraw any that are cluttered: crossing arrows, rotated labels, oversized nodes, unclear direction.
- `assets/README.md` has the re-render command for the user.

## 6. Rules and report

- Do NOT claim what the CBT video says; only reference it as a study aid.
- Set front matter `status: drafted` (leave `confidence` for the owner).
- Show a short summary:
  - concepts covered (x/y ticked)
  - number of Qs
  - ⚠ items
  - backbone used (reference program in `labs/$ARGUMENTS/` and/or N diagrams in `assets/$ARGUMENTS/`)
  - anything not run
- Suggest the commit message `$ARGUMENTS: draft notes`, but do not commit unless asked.
