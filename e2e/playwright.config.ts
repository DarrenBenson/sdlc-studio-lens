import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./specs",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  globalSetup: "./global-setup.ts",
  globalTeardown: "./global-teardown.ts",
  webServer: [
    {
      command:
        "cd ../backend && PYTHONPATH=src SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:////tmp/sdlc-lens-e2e.db uvicorn sdlc_lens.main:create_app --factory --port 8000",
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "cd ../frontend && npx vite --port 5173",
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
