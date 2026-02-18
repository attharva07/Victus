import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  use: {
    baseURL: process.env.WEB_BASE_URL ?? 'http://127.0.0.1:8000',
    trace: 'retain-on-failure',
  },
  reporter: [['list']],
});
