// Screenshot an assets/TXX/00-overview.html sheet to PNG at 2x.
// Usage: node scripts/render-overview.mjs assets/T02/00-overview.html
// The page must wrap everything in one element with class="sheet" and a fixed CSS width.
// Env override: CHROME_PATH (e.g. /usr/bin/google-chrome on Linux).
// Needs puppeteer-core (npm install --no-save puppeteer-core) and Google Chrome.
import path from "node:path";
import puppeteer from "puppeteer-core";

const input = path.resolve(process.argv[2]);
const output = input.replace(/\.html$/, ".png");
const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  args: process.env.CHROME_PATH ? ["--no-sandbox"] : [],
  headless: "new",
});
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 800, deviceScaleFactor: 2 });
await page.goto(`file://${input}`, { waitUntil: "networkidle0" });
const sheet = await page.$(".sheet");
// Fit the viewport to the sheet's own width, so wide map layouts aren't clipped.
const width = await sheet.evaluate((el) => Math.ceil(el.scrollWidth));
await page.setViewport({ width, height: 800, deviceScaleFactor: 2 });
await sheet.screenshot({ path: output });
await browser.close();
console.log(`wrote ${output}`);
