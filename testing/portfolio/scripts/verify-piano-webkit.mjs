import { webkit, devices } from "playwright";
import { createServer } from "http";
import { readFileSync, statSync } from "fs";
import { join, extname } from "path";
import { fileURLToPath } from "url";

const root = join(fileURLToPath(import.meta.url), "..", "..");
const types = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "text/javascript",
  ".svg": "image/svg+xml",
};

const server = createServer((req, res) => {
  let path = req.url?.split("?")[0] || "/";
  if (path === "/") path = "/index.html";
  const file = join(root, path.replace(/^\//, ""));
  try {
    const body = readFileSync(file);
    res.writeHead(200, { "Content-Type": types[extname(file)] || "text/plain" });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end("not found");
  }
});

const PORT = 9876;
await new Promise((r) => server.listen(PORT, "127.0.0.1", r));

const errors = [];
const browser = await webkit.launch();
const context = await browser.newContext({ ...devices["iPhone 13"] });
const page = await context.newPage();
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});

await page.goto(`http://127.0.0.1:${PORT}/index.html`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);

const whiteCount = await page.locator(".piano-key--white").count();
const pianoBox = await page.locator(".piano__whites").boundingBox();
const titleWeight = await page.locator(".home-hero__title").evaluate((el) => {
  const s = getComputedStyle(el);
  return {
    fontWeight: s.fontWeight,
    fontVariationSettings: s.fontVariationSettings,
    fontFamily: s.fontFamily,
  };
});

await page.screenshot({ path: "/opt/cursor/artifacts/portfolio-ios-piano-webkit.png", fullPage: true });

server.close();
await browser.close();

if (whiteCount !== 7) {
  console.error("Expected 7 white keys on iPhone width, got", whiteCount);
  process.exit(1);
}
if (!pianoBox || pianoBox.height < 80) {
  console.error("Piano height too small:", pianoBox);
  process.exit(1);
}
if (errors.length) {
  console.error("JS errors:", errors);
  process.exit(1);
}
console.log("OK", { whiteCount, pianoHeight: pianoBox?.height, titleWeight });
