import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const base = process.env.NOTLANKEN_URL || 'http://127.0.0.1:8765/';
const outDir =
  process.env.SCREENSHOT_DIR ||
  '/opt/cursor/artifacts/notlanken-v2-ui-port';

async function waitForSongReady(page) {
  await page.locator('#loading-modal').waitFor({ state: 'hidden', timeout: 120_000 });
  await page.locator('#btn-play-pause:not([disabled])').waitFor({ timeout: 120_000 });
}

async function waitForPlayback(page) {
  await page.waitForFunction(
    () => {
      const btn = document.querySelector('#btn-play-pause');
      const dock = document.querySelector('#time-elapsed-dock');
      if (!btn || !dock) return false;
      if (btn.getAttribute('aria-pressed') !== 'true') return false;
      if (dock.textContent === '0:00') return false;
      const pause = btn.querySelector('.icon-pause');
      if (!pause) return false;
      return getComputedStyle(pause).display !== 'none';
    },
    { timeout: 30_000 },
  );
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
await page.goto(base);
if (await page.locator('#player').isVisible()) {
  await page.locator('#btn-back').click();
}

await page.locator('.song-btn').first().click();
await waitForSongReady(page);
await page.locator('#btn-play-pause').click();
await waitForPlayback(page);
await page.waitForTimeout(500);

await mkdir(outDir, { recursive: true });
await page.screenshot({
  path: path.join(outDir, 'player-playing-390x844.png'),
  fullPage: false,
});

await page.locator('#btn-mixer').click();
await page.locator('#mixer-dialog').waitFor({ state: 'visible' });
await page.waitForTimeout(300);
await page.screenshot({
  path: path.join(outDir, 'mixer-open-390x844.png'),
  fullPage: false,
});

await browser.close();
console.log(`Saved screenshots to ${outDir}`);
