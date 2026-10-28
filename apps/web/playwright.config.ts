import { defineConfig, devices } from "@playwright/test";
import { WEB_URL } from "./tests/setup";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.spec.ts",
  globalSetup: "./tests/setup.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: "list",
  outputDir: "test-results",
  use: { baseURL: WEB_URL, trace: "off", screenshot: "off", video: "off" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
