import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 180_000,
  use: {
    baseURL: process.env.NOTLANKEN_URL || 'http://127.0.0.1:8765/',
    headless: true,
  },
  webServer: process.env.NOTLANKEN_URL
    ? undefined
    : {
        command: 'python3 -m http.server 8765',
        cwd: '.',
        url: 'http://127.0.0.1:8765/',
        reuseExistingServer: true,
      },
});
