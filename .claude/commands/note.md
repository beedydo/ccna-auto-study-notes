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
  - **Mermaid is for flows only** (sequences, decisions, lifecycles). If the diagram shows **what the parts are and how they connect** (a platform, a topology, planes, tiers), it's an architecture diagram: build it with the kit in §2d, not Mermaid. An auto-laid-out flowchart of boxes is not an architecture diagram.

## 2b. One-page overview sheet (top of every note)

Every note opens with one cheat-sheet-style infographic that summarises **every concept ID** in the topic. The visual style is ByteByteGo-inspired: bold title with a coloured pill, thick-bordered panels, icons, numbered callouts, grey code chips and red trap boxes. Build it last, after the Concepts are written, so it mirrors them exactly. `assets/T02/00-overview.html` is the worked reference: copy its CSS and adapt the layout.

**Pick the layout from the shape of the knowledge, not the topic name.** Ask: "What would the learner draw on a whiteboard to explain this?"

| Archetype | Use when the topic is mostly… | Layout | ByteByteGo inspiration | Fits topics like |
|---|---|---|---|---|
| **A. Command / concept grid** | a set of parallel items, each with syntax + options + a trap | One row per concept group: icon + name · key syntax pill + 2-line meaning · 2-col numbered examples with code chips · red trap box | "Top 6 Log Parsing Commands" | T02 Python, T06 data formats, T31 Bash, T04 Git commands, T45 script reading |
| **B. Comparison cheat sheet** | 2–5 things to compare on the same criteria ("X vs Y vs Z") | Row per option, columns = criteria (left: what/why, middle: measurements or rules, right: a tiny diagram of how it works). Or a big matrix with ✅/❌ cells | "System Design Cheat Sheet" (HA / throughput / scalability) | T09 REST vs RPC, T15/T16 NETCONF vs RESTCONF, T26 deployment models, T33 IaC tools, T10 auth types, T08 rate limit vs pagination |
| **C. Swim-lane pipeline** | a process with stages, roles or environments, in order | Horizontal lanes per stage (Plan / Build / Test / Release), numbered steps flowing between lanes with dashed arrows, actors as small icons | "How Companies Ship Code to Production" | T28 CI/CD, T04 PR workflow, T01 dev methods, T32 TDD cycle, T43 webhooks, T47 sequence diagrams |
| **D. Lifecycle / loop** | one cycle repeated (develop → commit → test → deploy → back) | Numbered panels top to bottom: 1 the loop as a circle/arrows, 2 the split (e.g. CI ↔ CD with a dashed divider), 3 the detail | "CI/CD Pipelines" zine | T28 CI/CD, T04 file lifecycle, T32 red-green-refactor, T11 request → retry loop |
| **E. Architecture / system map** | components and how traffic or data flows between them | Grouped zones (boxes with a coloured header: Client · Edge · Controller · Device) with labelled arrows, side notes for options, and a legend for colours | "System Design Blueprint" | T12 controller vs device, T17/T18–T25 platform APIs, T38 topology, T39 planes, T40/T41 FW/DNS/LB/proxy, T27 Docker, T20 Catalyst Center |
| **F. Family of variants** | 3–6 variants of one idea, each with the same internal parts | Grid of same-sized cards, each with its own colour, same mini-diagram inside (so differences pop), plus one shared element (e.g. "Environment" bar) per card. Optional wide card at the bottom for the most complex variant | "Types of AI Agents" | T10 auth methods (basic / API key / OAuth / token), T14 YANG node types, T30 OWASP attacks, T23 security platforms, T36 IP addressing/routing types |

- **Mixing is fine.** For example: archetype A rows with one row that holds a mini system map, or archetype E with a comparison strip at the bottom. Pick one **primary** archetype so the sheet has a clear reading order.
- **Networking, platform and system topics usually suit E or F.** Process topics suit C or D. "Which option/command" topics suit A or B. When unsure between a diagram and a table, ask yourself whether the exam questions are "what happens next / where does it go" (choose a diagram) or "which one / what's the difference" (choose a table or comparison).
- State the chosen archetype and a one-line reason in the final summary.

**Content rules (same for every archetype)**

- **Coverage:** every `TXX.NN` concept ID appears somewhere on the sheet. Label each panel/row with its IDs (small grey text, e.g. `T02.02 · T02.03`).
- **One red trap box** per panel/row, taken from `## Exam traps`.
- **Grey code chips** for exact syntax only (commands, paths, status codes, ports). Code-heavy topics take their examples from the reference program in `labs/TXX/`, with identical text. If a line is too long, split it across two chips; never shorten it into code that doesn't exist.
- **Numbered black circles** for steps or examples. In flows they show order; in grids they're just indexes.
- **Diagrams inside the sheet** are HTML/CSS boxes and arrows, or inline SVG. Keep them simple: boxes, arrows, short labels. Use colour to carry meaning, the same way as in §2 (green safe/kept, yellow partial, red destructive/error, blue recommended answer).
- **Icons:** emoji (🎯 🔧 🧱 📦 🌐 🔐 ⚙️ 🚀). No external images or web fonts; the sheet must render offline.
- **Header:** `TXX · <pill>Topic name</pill> at a glance`, plus a right-aligned meta block (blueprint items, "Every TXX concept on one page", and where the code lives). **Footer:** a legend for chips, colours and numbers.
- **Density:** scannable in about 2 minutes. Short phrases, not sentences. If the sheet needs more than about 7 rows/panels, merge concept IDs instead of growing it.

**Build and check**

1. Write `assets/$ARGUMENTS/00-overview.html`. One root element `<div class="sheet">` with a fixed CSS width: 1180px for grids and tables, up to about 1500px for system maps. Use `table-layout: fixed` and `grid-template-columns: minmax(0, 1fr) …`, so long content wraps instead of pushing columns off the edge.
2. Render: `node scripts/render-overview.mjs assets/$ARGUMENTS/00-overview.html` → `00-overview.png` at 2x. In this setup, run it from `/private/tmp/claude-501/mmd` (where `puppeteer-core` is installed), with the Bash sandbox disabled.
3. **Look at the PNG** (Read the image) and fix any of these, then re-render:
   - text clipped at the right edge
   - code chips overlapping the next column
   - lines wrapping mid-token
   - empty or lopsided panels
   - invisible legend swatches
   Expect 2–4 rounds.
4. Insert it directly under the `> Owner: …` line at the top of the note:
   `![TXX at a glance: …](../assets/$ARGUMENTS/00-overview.png)`, then a blank line and a one-line italic caption saying how to read it (rows/panels = what, numbers = what, red = traps).
5. Add `- Overview image: HTML source assets/$ARGUMENTS/00-overview.html …` to `## Sources`.

## 2c. Step animations (GIF), only where motion teaches

A GIF shows **something moving through stages over time**, one command or event per frame. Use it sparingly: **0–2 per note**, and most notes need none. A GIF never replaces a static diagram or table, because it can't be paused. Put it right below the static diagram of the same flow.

**Make one only if all three are true:**

1. **The concept is a sequence over time**, where order matters and the exam asks "what happens next" or "put these in order".
2. **The state changes between steps**: something visibly moves, appears or switches location (a file between Git areas, a token between client and server, a packet through hops).
3. **A static diagram leaves a common misconception.** For example: "fetch changes my files", "the webhook is polled", "a NETCONF edit is live before commit".

**Good fits, by topic (one each unless stated):**

| Topic | Animation | Misconception it fixes |
|---|---|---|
| T04 Git ✅ done | edit → add → commit → push → fetch → pull (`assets/T04/10-workflow.gif`) | fetch vs pull |
| T10 API auth | OAuth 2.0 auth-code flow: redirect → login → code → token exchange → API call | where the token comes from |
| T15 NETCONF | SSH :830 → hello/capabilities → lock → edit-config (candidate) → commit → unlock | candidate vs running |
| T43 Webhooks | register URL → event happens → platform POSTs to you → you reply 200 | push vs polling |
| T28 CI/CD | commit → build → test → package → deploy dev/QA/prod (a fail stops the line) | CI vs CD boundary |
| T37 / T41 | DNS lookup chain, or a request through firewall → LB → reverse proxy → server | which box does what |
| T11 requests | call → 429 → wait `Retry-After` → retry → 200 | retry/backoff loop |

**Skip it for** syntax, comparisons, definitions, status-code lists, and any flow with fewer than 4 steps or more than 8. A static diagram or table is clearer there.

**Frame design (copy `assets/T04/10-workflow-anim.html`):**

- **Fixed layout across frames:** the same lanes or boxes in the same places every frame; only their *contents* change. This lets the eye see what moved.
- **4–8 frames.** Each frame = one command or event. Use real commands, codes and values from the note or `labs/`, never placeholders.
- In each frame:
  - **Highlight** the active lane (glow).
  - Show a dark **command label** under the box it acts on. `➜` marks a forward action; `⬅` marks one coming back.
  - Fade or dash anything that's "unchanged" or "gone".
- **Caption strip** at the bottom: step number circle + one sentence of what just happened (bold the key fact) + progress dots.
- Same colour meanings as the diagrams (§2), same fonts and title style as the overview sheet (§2b).
- No smooth tweening. A stepped frame is easier to read than motion, and the file stays small (aim < 300 KB).

**Build and check:**

1. Write `assets/$ARGUMENTS/NN-name-anim.html`. It needs `window.FRAME_COUNT`, `window.show(i)` and one `.sheet` root.
2. Render: `node scripts/render-animation.mjs assets/$ARGUMENTS/NN-name-anim.html 2.5` → `NN-name.gif`. The number is seconds per frame; the last frame is held twice as long. In this setup, run it from `/private/tmp/claude-501/mmd` with the Bash sandbox disabled (needs Chrome + ffmpeg).
3. **Check it.** Extract 2–3 frames with `ffmpeg -i X.gif -vf "select=eq(n\,K)" -vframes 1 -update 1 fK.png` and Read them. Fix clipped labels, overlapping boxes and any fake-looking values (e.g. commit hashes must be hex).
4. Embed it under the static diagram of the same flow:
   `![Animated …](../assets/$ARGUMENTS/NN-name.gif)`, then a blank line, then an italic caption listing the steps in order and naming the misconception it fixes.

## 2d. Architecture and topology diagrams (HTML kit, not Mermaid)

Use one when the learner needs to see **components, where they sit and what connects to what**. Typical cases are a platform's architecture (controller, cloud, devices), a network topology, planes or tiers, and a request path through boxes. **Platform topics (T12, T17–T25, T42) and topology topics (T38–T41) need at least one.** Mermaid can't do this well: it auto-places boxes, has no device shapes and doesn't type the links, so the result reads like a flowchart.

**The kit (`assets/_arch/`, shared by every topic):**
- `arch.css`: zones, node and label styles, the link legend, and the same title style as the overview sheets.
- `arch.js`: inline SVG device icons, simplified in the style of the Cisco network topology icons. It also draws the links from a list.
- Worked reference: `assets/T22/01-architecture.html`. Copy its structure.

**How to build one:**
1. Write `assets/$ARGUMENTS/NN-short-name.html`. It loads `../_arch/arch.css` and `../_arch/arch.js` and has one `<div class="sheet">` root (1300px; add `class="sheet wide"` for 1500px).
2. **Place things on purpose, in zones.** A zone is a `.zone` with a header (`.zh`) and a body (`.zb`). Zones stack top to bottom (`.gap` between rows) or sit side by side in a `.row`.
   - Zone kinds give the header colour: `client` · `cloud` · `ctrl` · `fabric` · `site` · `dmz` · `ext`. `dashed` gives an outline-only grouping zone.
   - Usual reading order: whoever calls the API at the top, then controller or cloud, then fabric or devices, then sites or end hosts at the bottom.
3. **Nodes** are `<div class="node" id="…" data-icon="…">` with `.nm` (name), `.sub` (role, old name, port) and an optional `.tag` (an exact value from the lab, e.g. `device-type: vsmart`).
   - Icons: `router switch l3switch firewall lb server controller cloud internet ap wlc laptop script gui user phone roomdevice phonesvc camera db chassis fi dns proxy`.
   - Width modifiers: `.n` narrow, `.w` wide, `.xw` extra wide. `.hl` makes a node glow (the box your code talks to); `.down` marks a failed one.
4. **Links** go in `window.LINKS = [{a, b, k, label, dir, s, ao, bo, mid, t}]`. `k` is the link type, shown in the legend, and must mean the same thing in every diagram:
   - `api`: your code → platform (blue, arrow)
   - `mgmt`: management or config such as NETCONF, SSH or SNMP (grey dashed)
   - `control`: control plane such as OMP, routing protocols or DTLS control (purple dotted)
   - `data`: user traffic (thick green)
   - `phys`: a plain cable or LAN link (dark)
   - `error`: blocked or failing (red dashed)

   A link whose `b` is a zone lands straight below its source, so one line can stand for "to every device in this zone".
5. **Keep it readable:** at most ~16 links. Parallel links get `ao`/`bo` offsets, so none overlap. No label sits on a node. Use 2–3 `.note` boxes under the canvas (one `.note.trap` from `## Exam traps`), and a `footer` legend that lists only the link types the diagram uses.
6. Render with the overview script (it screenshots `.sheet` at 2x): `node scripts/render-overview.mjs assets/$ARGUMENTS/NN-short-name.html` → `NN-short-name.png`. **Read the PNG** and fix crossing lines, labels on top of nodes, lopsided zones and clipped text. Expect 2–4 rounds; move nodes or zones before adding bends.
7. Embed it like any diagram, with an italic caption saying what to notice. In `## Sources`, list it as `Architecture diagram: HTML source assets/$ARGUMENTS/NN-short-name.html (shared kit assets/_arch/)`.

Don't edit `assets/_arch/` for one topic. If the kit needs a new icon or link type, add it there once, then re-render the existing diagrams that use the kit and check them.

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
- Check the overview sheet against the Concepts: every concept ID is on it, and every code chip matches the note or `labs/` exactly.
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
  - overview sheet archetype (A–F) and why
  - architecture/topology diagrams built with the `assets/_arch/` kit (or "none: no component map needed")
  - GIFs made (or "none: no flow needed motion"), each with the misconception it fixes
  - anything not run
- Suggest the commit message `$ARGUMENTS: draft notes`, but do not commit unless asked.
