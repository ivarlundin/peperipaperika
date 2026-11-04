import { test, expect } from '@playwright/test';

const BASE = process.env.NOTLANKEN_URL || 'http://127.0.0.1:8765/';

async function waitForSongReady(page) {
  const loading = page.locator('#loading-modal');
  await expect(loading).toBeHidden({ timeout: 120_000 });
  await expect(page.locator('#btn-play')).toBeEnabled({ timeout: 120_000 });
}

test.describe('Notlänken player v2 layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE);
    if (await page.locator('#player').isVisible()) {
      await page.locator('#btn-back').click();
    }
    await expect(page.locator('.song-btn')).toHaveCount(3, { timeout: 30_000 });
  });

  test('chord strip and dock scrub sit above transport', async ({ page }) => {
    await page.locator('.song-btn').nth(1).click();
    await waitForSongReady(page);

    await expect(page.locator('#chord-progress')).toBeVisible();
    await expect(page.locator('#chord-progress .chord-chip.is-current')).toHaveCount(1);

    const scrubBeforeTransport = await page.evaluate(() => {
      const scrub = document.querySelector('.progress-scrub');
      const transport = document.querySelector('.transport-block');
      return scrub.compareDocumentPosition(transport) & Node.DOCUMENT_POSITION_FOLLOWING;
    });
    expect(scrubBeforeTransport).toBeTruthy();
  });

  test('mixer tab shows inline horizontal faders', async ({ page }) => {
    await page.locator('.song-btn').first().click();
    await waitForSongReady(page);

    await page.locator('#player-tab-btn-mixer').click();
    await expect(page.locator('#player-tab-mixer')).toBeVisible();
    await expect(page.locator('#player-tab-mixer .mixer-track-row')).not.toHaveCount(0);
    await expect(page.locator('#reverb')).toBeVisible();
    await expect(page.locator('#master-vol')).toBeVisible();
  });

  test('segment tabs switch spelvy and noter', async ({ page }) => {
    await page.locator('.song-btn').nth(1).click();
    await waitForSongReady(page);

    await page.locator('#player-tab-btn-noter').click();
    await expect(page.locator('#player-tab-noter')).toBeVisible();
    await expect(page.locator('#komp-bar')).toBeVisible();

    await page.locator('#player-tab-btn-spelvy').click();
    await expect(page.locator('#player-tab-spelvy')).toBeVisible();
    await expect(page.locator('#lane')).toBeVisible();
  });
});
