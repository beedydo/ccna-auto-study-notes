// Screenshot an assets/TXX/00-overview.html sheet to PNG at 2x.
// Usage: node scripts/render-overview.mjs assets/T02/00-overview.html
// Needs puppeteer-core (npm install --no-save puppeteer-core) and Google Chrome.
import path from "node:path";
import puppeteer from "puppeteer-core";

const input = path.resolve(process.argv[2]);
const output = input.replace(/\.html$/, ".png");
const browser = await puppeteer.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: "new",
});
const page = await browser.newPage();
await page.setViewport({ width: 1180, height: 800, deviceScaleFactor: 2 });
await page.goto(`file://${input}`, { waitUntil: "networkidle0" });
await (await page.$(".sheet")).screenshot({ path: output });
await browser.close();
console.log(`wrote ${output}`);
