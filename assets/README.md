# Diagram assets

- One folder per topic (`assets/T04/`). Each diagram has a Mermaid source (`.mmd`) and a rendered `.png`; notes embed the PNG.
- Edit the `.mmd`, then re-render:

```bash
npx --yes @mermaid-js/mermaid-cli --input assets/T04/01-four-areas.mmd --output assets/T04/01-four-areas.png --scale 2 --backgroundColor white
```

- Render every diagram in a folder:

```bash
for f in assets/T04/*.mmd; do npx --yes @mermaid-js/mermaid-cli --input "$f" --output "${f%.mmd}.png" --scale 2 --backgroundColor white; done
```

## One-page overviews (HTML → PNG)

- `assets/TXX/00-overview.html` is a cheat-sheet-style infographic of the whole topic; the note embeds `00-overview.png`.
- The layout archetype (grid, comparison, swim-lane, lifecycle, system map, variant cards) is chosen per topic; see §2b of `.claude/commands/note.md`. `assets/T02/00-overview.html` is the reference for the CSS.
- Edit the HTML, then screenshot the `.sheet` element at 2x (auto-sizes to the full page height):

```bash
npm install --no-save puppeteer-core
node scripts/render-overview.mjs assets/T02/00-overview.html
```

## Step animations (HTML → GIF)

- `assets/TXX/NN-name-anim.html` defines the frames (`window.FRAME_COUNT`, `window.show(i)`); the note embeds the `.gif`.
- Edit the frames, then re-render (needs ffmpeg):

```bash
npm install --no-save puppeteer-core
node scripts/render-animation.mjs assets/T04/10-workflow-anim.html 2.5
```

- The last argument is seconds per frame. The last frame is held twice as long.

## Linux

- Both render scripts default to the macOS Chrome path. On Linux, point them at Chrome (and at ffmpeg, if it isn't on `PATH`):

```bash
CHROME_PATH=/usr/bin/google-chrome node scripts/render-overview.mjs assets/T19/00-overview.html
CHROME_PATH=/usr/bin/google-chrome FFMPEG=/path/to/ffmpeg node scripts/render-animation.mjs assets/T15/08-candidate-commit-anim.html 2.5
```

- For Mermaid, pass a puppeteer config with `{"executablePath": "/usr/bin/google-chrome", "args": ["--no-sandbox"]}` via `npx @mermaid-js/mermaid-cli -p puppeteer.json ...`.

## Architecture and topology diagrams (HTML kit → PNG)

- Platform architectures, topologies, planes and tiers are hand-placed HTML, not Mermaid. They use the shared kit in `assets/_arch/` (`arch.css` for zones, labels and legend; `arch.js` for the device icons and links drawn from `window.LINKS`).
- The worked reference is `assets/T22/01-architecture.html`. The authoring rules are in §2d of `.claude/commands/note.md`.
- Render the same way as an overview sheet:

```bash
node scripts/render-overview.mjs assets/T22/01-architecture.html
```
