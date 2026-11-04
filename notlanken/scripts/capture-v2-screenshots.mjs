import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const outDir = process.env.SCREENSHOT_DIR || '/opt/cursor/artifacts/screenshots';
const base = 'http://127.0.0.1:8765/';

async function waitEngineReady(page) {
  const loading = page.locator('#loading-modal');
  await loading.waitFor({ state: 'hidden', timeout: 120_000 });
  await page.locator('#btn-play').waitFor({ state: 'visible', timeout: 120_000 });
  await page.locator('#btn-play').waitFor({ state: 'attached' });
  await page.waitForFunction(() => {
    const dlg = document.getElementById('loading-modal');
    return !dlg || !dlg.open;
  }, null, { timeout: 120_000 });
  await page.locator('#chord-progress').waitFor({ state: 'visible', timeout: 30_000 });
}

const server = spawn('python3', ['-m', 'http.server', '8765'], {
  cwd: new URL('..', import.meta.url).pathname,
  stdio: 'ignore',
});
await new Promise((r) => setTimeout(r, 900));

await mkdir(outDir, { recursive: true });
const browser = await chromium.launch();

async function openUtanKomp(page) {
  await page.goto(base);
  await page.getByRole('button', { name: /utan komp/i }).click();
  await waitEngineReady(page);
}

async function shot(page, name) {
  const open = await page.locator('#loading-modal').evaluate((el) => el?.open ?? false).catch(() => false);
  if (open) throw new Error(`Loading modal still open before ${name}`);
  await page.screenshot({ path: path.join(outDir, name), fullPage: true });
}

{
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await openUtanKomp(page);
  await page.locator('#btn-play').click();
  await page.locator('#btn-play').waitFor({ state: 'visible' });
  await page.waitForFunction(() => document.getElementById('btn-play')?.getAttribute('aria-pressed') === 'true');
  await page.locator('#player-tab-btn-spelvy').click();
  await shot(page, 'notlanken-v2-mobile-spelvy-playing.png');
  await page.close();
}

{
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await openUtanKomp(page);
  await page.locator('#player-tab-btn-mixer').click();
  await page.locator('#player-tab-mixer .mixer-track-row').first().waitFor({ state: 'visible' });
  await shot(page, 'notlanken-v2-mobile-mixer.png');
  await page.close();
}

{
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await openUtanKomp(page);
  await page.locator('#player-tab-btn-noter').click();
  await page.locator('#note-add').waitFor({ state: 'visible' });
  await shot(page, 'notlanken-v2-mobile-noter.png');
  await page.close();
}

{
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await openUtanKomp(page);
  await page.locator('#player-tab-btn-spelvy').click();
  await page.locator('#lane').waitFor({ state: 'visible' });
  await shot(page, 'notlanken-v2-desktop-spelvy.png');
  await page.close();
}

await browser.close();
server.kill();
console.log('Saved screenshots to', outDir);
