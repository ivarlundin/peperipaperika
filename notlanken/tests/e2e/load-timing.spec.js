import { test, expect, chromium } from '@playwright/test';

async function openFirstSong(page) {
  const firstSong = page.locator('.song-btn').first();
  await expect(firstSong).toBeVisible({ timeout: 30_000 });
  const t0 = Date.now();
  await firstSong.click();
  await expect(page.locator('#loading-modal')).toBeVisible({ timeout: 5_000 });
  await expect(page.locator('#loading-modal')).toBeHidden({ timeout: 120_000 });
  return Date.now() - t0;
}

test('load timing — core warm + song switch', async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto('/?bench=1');

  const firstOpenMs = await openFirstSong(page);

  await page.locator('#btn-back').click();
  await expect(page.locator('.song-btn').first()).toBeVisible();

  const t1 = Date.now();
  const songs = page.locator('.song-btn');
  const count = await songs.count();
  if (count > 1) {
    await songs.nth(1).click();
  } else {
    await songs.first().click();
  }
  await expect(page.locator('#btn-play-pause:not([disabled])')).toBeVisible({ timeout: 120_000 });
  const modalVisible = await page.locator('#loading-modal').isVisible();
  const switchMs = Date.now() - t1;

  console.log(JSON.stringify({
    profile: 'local-unthrottled',
    firstOpenMs,
    switchMs,
    modalOnSwitch: modalVisible,
  }));

  expect(firstOpenMs).toBeGreaterThan(50);
  expect(switchMs).toBeLessThan(firstOpenMs * 0.85 + 5000);
});

test('load timing — Fast 3G cold vs warm', async () => {
  test.setTimeout(180_000);
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false,
    downloadThroughput: (1.6 * 1024 * 1024) / 8,
    uploadThroughput: (750 * 1024) / 8,
    latency: 40,
  });

  await page.goto('http://127.0.0.1:8765/?bench=1');
  const coldMs = await openFirstSong(page);

  await page.locator('#btn-back').click();
  await expect(page.locator('.song-btn').first()).toBeVisible();

  const t1 = Date.now();
  await page.locator('.song-btn').nth(1).click();
  await expect(page.locator('#btn-play-pause:not([disabled])')).toBeVisible({ timeout: 120_000 });
  const warmSwitchMs = Date.now() - t1;

  console.log(JSON.stringify({
    profile: 'fast-3g-playwright-cdp',
    coldFirstSongMs: coldMs,
    warmSongSwitchMs: warmSwitchMs,
  }));

  expect(coldMs).toBeLessThan(12_000);
  expect(warmSwitchMs).toBeLessThan(3_000);

  await browser.close();
});
