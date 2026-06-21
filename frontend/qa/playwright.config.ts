import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runId = process.env.EWC_SCREENSHOT_QA_RUN_ID ?? new Date().toISOString().replace(/[:.]/g, "-");
const port = process.env.EWC_SCREENSHOT_QA_PORT ?? "5175";
const viteApiMode = process.env.EWC_QA_VITE_API_MODE ?? "";
const artifactRoot = path.resolve(__dirname, "..", "..", ".gstack", "screenshots", "upload-job-browser-qa", runId);

export default defineConfig({
  testDir: __dirname,
  outputDir: artifactRoot,
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  preserveOutput: "always",
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://127.0.0.1:${port}`,
    trace: "off",
    video: "off",
    screenshot: "off",
  },
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 30_000,
    env: {
      ...process.env,
      VITE_API_MODE: viteApiMode,
    },
  },
});
