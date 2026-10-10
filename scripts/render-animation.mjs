// Render an assets/TXX/*-anim.html step animation to a GIF.
// The page must define window.FRAME_COUNT and window.show(i), and wrap everything in .sheet.
// Usage: node scripts/render-animation.mjs assets/T04/10-workflow-anim.html [seconds-per-frame]
// Needs puppeteer-core (npm install --no-save puppeteer-core), Google Chrome and ffmpeg.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import puppeteer from "puppeteer-core";

const input = path.resolve(process.argv[2]);
const secs = Number(process.argv[3] || 2.5);
const output = input.replace(/-anim\.html$/, ".gif").replace(/\.html$/, ".gif");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "anim-"));

const browser = await puppeteer.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: "new",
});
const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 700, deviceScaleFactor: 1.5 });
await page.goto(`file://${input}`, { waitUntil: "networkidle0" });
const count = await page.evaluate(() => window.FRAME_COUNT);
const sheet = await page.$(".sheet");
for (let i = 0; i < count; i++) {
  await page.evaluate((n) => window.show(n), i);
  await sheet.screenshot({ path: path.join(tmp, `f${String(i).padStart(2, "0")}.png`) });
}
await browser.close();

// Hold the last frame twice as long, then build a palette for crisp colours.
fs.copyFileSync(path.join(tmp, `f${String(count - 1).padStart(2, "0")}.png`), path.join(tmp, `f${String(count).padStart(2, "0")}.png`));
const pattern = path.join(tmp, "f%02d.png");
const rate = `1/${secs}`;
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", rate, "-i", pattern,
  "-vf", "palettegen=stats_mode=diff", path.join(tmp, "palette.png")]);
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", rate, "-i", pattern, "-i", path.join(tmp, "palette.png"),
  "-lavfi", "paletteuse=dither=none", "-loop", "0", output]);
fs.rmSync(tmp, { recursive: true });
console.log(`wrote ${output} (${count} frames, ${secs}s each)`);
