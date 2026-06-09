import { defineConfig, devices } from '@playwright/test'

// Saved student auth state produced by global-setup.ts.
const STUDENT_STATE = 'e2e/.auth/student.json'

export default defineConfig({
  testDir: './e2e',
  // global-setup.ts runs after the webServers are up and before specs.
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  timeout: 60_000,
  use: {
    baseURL: 'http://localhost:3000',
    storageState: STUDENT_STATE,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
    {
      name: 'webkit-mobile',
      use: { ...devices['iPhone 12'] },
    },
  ],
  // Playwright starts both webServers and waits for each `url` before running
  // globalSetup and specs. run-api.sh seeds + serves the API; preview serves
  // the production build and proxies /api + /health to the API.
  // webServer `cwd` defaults to this config file's directory (frontend/), so
  // `../scripts/...` resolves to the repo root and the npm commands run here.
  // We do not set `cwd: __dirname` because this config loads as native ESM
  // (package.json has "type": "module"), where __dirname is undefined.
  webServer: [
    {
      command: 'bash ../scripts/e2e/run-api.sh',
      url: 'http://localhost:8000/health/live',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'npm run build && npm run preview -- --port 3000',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
})
