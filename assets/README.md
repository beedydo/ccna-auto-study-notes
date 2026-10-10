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
- Edit the HTML, then screenshot the `.sheet` element at 2x (auto-sizes to the full page height):

```bash
npm install --no-save puppeteer-core
node scripts/render-overview.mjs assets/T02/00-overview.html
```
