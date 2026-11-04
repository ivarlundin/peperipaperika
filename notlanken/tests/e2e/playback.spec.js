import { test, expect } from '@playwright/test';

const BASE = process.env.NOTLANKEN_URL || 'http://127.0.0.1:8765/';

async function waitForSongReady(page) {
  const loading = page.locator('#loading-modal');
  await expect(loading).toBeHidden({ timeout: 120_000 });
  await expect(page.locator('#btn-play')).toBeEnabled({ timeout: 120_000 });
}

test.describe('Notlänken playback', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE);
    if (await page.locator('#player').isVisible()) {
      await page.locator('#btn-back').click();
    }
    await expect(page.locator('.song-btn')).toHaveCount(3, { timeout: 30_000 });
  });

  test('logo visible on player view and home link returns to list', async ({ page }) => {
    await page.locator('.song-btn').first().click();
    await waitForSongReady(page);

    const brand = page.locator('.nl-site-brand h1');
    await expect(brand).toBeVisible();
    await expect(brand).toHaveText('Notlänken ™');

    await page.locator('#site-home').click();
    await expect(page.locator('#view-list')).toBeVisible();
    await expect(page.locator('#player')).toBeHidden();
  });

  test('rapid song switching keeps play working', async ({ page }) => {
    const songs = page.locator('.song-btn');
    const count = await songs.count();
    for (let round = 0; round < 6; round += 1) {
      await songs.nth(round % count).click();
      await waitForSongReady(page);
      await page.locator('#btn-play').click();
      await expect(page.locator('#btn-pause')).toBeEnabled({ timeout: 90_000 });
      await page.waitForTimeout(350);
      await page.locator('#btn-back').click();
      await expect(page.locator('#view-list')).toBeVisible();
    }

    await songs.first().click();
    await waitForSongReady(page);
    await page.locator('#btn-play').click();
    await expect(page.locator('#btn-pause')).toBeEnabled();
    await expect.poll(async () => page.locator('#time-elapsed').textContent(), {
      timeout: 5000,
    }).not.toBe('0:00');
  });

  test('transport spam and scrub while playing', async ({ page }) => {
    await page.locator('.song-btn').first().click();
    await waitForSongReady(page);

    for (let i = 0; i < 8; i += 1) {
      await page.locator('#btn-play').click();
      await expect(page.locator('#btn-pause')).toBeEnabled({ timeout: 30_000 });
      await page.waitForTimeout(80);
      await page.locator('#btn-pause').click();
    }
    await page.locator('#btn-play').click();
    await expect(page.locator('#btn-pause')).toBeEnabled({ timeout: 30_000 });
    await page.waitForTimeout(200);

    const lane = page.locator('#lane');
    const box = await lane.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width * 0.7, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width * 0.3, box.y + box.height / 2);
      await page.mouse.up();
    }
    await page.waitForTimeout(200);
    await expect(page.locator('#btn-pause')).toBeEnabled({ timeout: 30_000 });
    await page.locator('#btn-pause').click();
    await page.locator('#btn-play').click();
    await expect(page.locator('#btn-pause')).toBeEnabled({ timeout: 30_000 });
  });

  test('autokomp bar hidden for full arrangement, visible for utan komp', async ({ page }) => {
    await page.locator('.song-btn').nth(0).click();
    await waitForSongReady(page);
    await expect(page.locator('#komp-bar')).toBeHidden();

    await page.locator('#btn-back').click();
    await expect(page.locator('#view-list')).toBeVisible();
    await page.locator('.song-btn').nth(1).click();
    await waitForSongReady(page);
    await expect(page.locator('#komp-bar')).toBeVisible();
    await expect(page.locator('#komp-enabled')).toBeChecked();
    await expect(page.locator('#komp-style-picker')).toBeVisible();
  });

  test('speed opens in modal with grouped rows', async ({ page }) => {
    await page.locator('.song-btn').first().click();
    await waitForSongReady(page);
    await expect(page.locator('#speed-dialog')).not.toBeVisible();
    await page.locator('#btn-speed').click();
    const dialog = page.locator('#speed-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('.speed-group')).toHaveCount(3);
    await page.locator('#speed-close').click();
    await expect(dialog).not.toBeVisible();
  });

  test('mobile viewport: logo and song switch', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('.song-btn').nth(1).click();
    await waitForSongReady(page);
    await expect(page.locator('.nl-site-brand')).toBeVisible();
    await page.locator('#btn-play').click();
    await page.locator('#btn-back').click();
    await page.locator('.song-btn').first().click();
    await waitForSongReady(page);
    await page.locator('#btn-play').click();
    await expect(page.locator('#btn-pause')).toBeEnabled();
  });
});
