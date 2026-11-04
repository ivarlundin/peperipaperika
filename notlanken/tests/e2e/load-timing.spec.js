import { test, expect } from '@playwright/test';

test('load timing — core warm + song switch', async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto('/?bench=1');

  const firstSong = page.locator('.song-btn').first();
  await expect(firstSong).toBeVisible({ timeout: 30_000 });

  const t0 = Date.now();
  await firstSong.click();
  await expect(page.locator('#loading-modal')).toBeVisible({ timeout: 5_000 });
  await expect(page.locator('#loading-modal')).toBeHidden({ timeout: 120_000 });
  const firstOpenMs = Date.now() - t0;

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
  await expect(page.locator('#btn-play:not([disabled])')).toBeVisible({ timeout: 120_000 });
  const modalVisible = await page.locator('#loading-modal').isVisible();
  const switchMs = Date.now() - t1;

  console.log(JSON.stringify({
    firstOpenMs,
    switchMs,
    modalOnSwitch: modalVisible,
  }));

  expect(firstOpenMs).toBeGreaterThan(100);
  expect(switchMs).toBeLessThan(firstOpenMs * 0.85 + 5000);
});
