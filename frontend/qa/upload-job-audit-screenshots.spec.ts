import { expect, test, type Page, type TestInfo } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

type ViewportCase = {
  name: string;
  width: number;
  height: number;
};

type CaptureLog = {
  type: string;
  url: string;
  text: string;
};

const viewports: ViewportCase[] = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1366x768", width: 1366, height: 768 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "720x900", width: 720, height: 900 },
];

const forbiddenVisibleText = [/Inserted/i, /적재/u, /삽입/u, /새로 삽입/u];
const forbiddenArtifactText = [
  /[A-Za-z0-9_-]+_\d{8}_\d{6}\.csv/i,
  /postgres(?:ql)?:\/\//i,
  /Bearer\s+\S+/i,
  /Authorization:\s*\S+/i,
  /service_role\s*[:=]\s*\S+/i,
  /C:\\Users\\/i,
  /C:\\extrusion\\/i,
  /[A-Za-z]:\\(?:[^\\\r\n"'<>]+\\)+[^\\\r\n"'<>]+/i,
];

function redact(value: string): string {
  return value
    .replace(/postgres(?:ql)?:\/\/[^\s"'<>]+/gi, "[redacted-db-url]")
    .replace(/Bearer\s+[A-Za-z0-9._~+/-]+=*/gi, "Bearer [redacted]")
    .replace(/Authorization:\s*[^\s"'<>]+/gi, "Authorization: [redacted]")
    .replace(/eyJ[A-Za-z0-9._-]+/g, "[redacted-jwt]")
    .replace(/[A-Za-z]:\\Users\\[^"'<>\\\s]+(?:\\[^"'<>\\\s]+)*/g, "[redacted-user-path]")
    .replace(/[A-Za-z]:\\extrusion\\[^"'<>]+/gi, "[redacted-path]")
    .replace(/[A-Za-z]:\\(?:[^\\\r\n"'<>]+\\)+[^\\\r\n"'<>]+/g, "[redacted-path]")
    .replace(/[A-Za-z0-9_-]+_\d{8}_\d{6}\.csv/gi, "[redacted-file]");
}

function safeName(value: string): string {
  return value.replace(/[^A-Za-z0-9_.-]+/g, "-").replace(/^-+|-+$/g, "");
}

async function writeJsonl(filePath: string, rows: unknown[]) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const body = rows.map((row) => JSON.stringify(row)).join("\n");
  await fs.writeFile(filePath, body ? `${body}\n` : "", "utf8");
}

async function maskSensitiveUiText(page: Page) {
  await page.evaluate(() => {
    const setText = (selector: string, value: string) => {
      document.querySelectorAll<HTMLElement>(selector).forEach((element, index) => {
        element.textContent = `${value}-${index + 1}`;
        element.removeAttribute("title");
      });
    };

    setText(".preview-path", "[redacted-path]");
    setText(".preview-file-cell strong", "[redacted-file]");
    document.querySelectorAll<HTMLElement>("[title]").forEach((element) => {
      const title = element.getAttribute("title") ?? "";
      if (/[A-Za-z]:\\|[A-Za-z0-9_-]+_\d{8}_\d{6}\.csv/i.test(title)) element.setAttribute("title", "[redacted]");
    });
  });
}

async function expectNoForbiddenVisibleText(page: Page) {
  const body = await page.locator("body").innerText();
  for (const pattern of forbiddenVisibleText) {
    expect(body, `forbidden visible text ${pattern}`).not.toMatch(pattern);
  }
}

async function expectNoBodyHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(
    overflow.scrollWidth,
    `body horizontal overflow: scrollWidth=${overflow.scrollWidth}, viewport=${overflow.viewportWidth}`,
  ).toBeLessThanOrEqual(overflow.viewportWidth + 2);
}

async function capture(page: Page, testInfo: TestInfo, viewport: ViewportCase, label: string, screenshots: string[]) {
  await maskSensitiveUiText(page);
  await expectNoForbiddenVisibleText(page);
  await expectNoBodyHorizontalOverflow(page);
  const screenshotPath = testInfo.outputPath(`${viewport.name}-${safeName(label)}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  screenshots.push(path.relative(testInfo.outputDir, screenshotPath).replace(/\\/g, "/"));
}

async function setLanguage(page: Page, language: "ko" | "en") {
  await page.addInitScript((nextLanguage) => {
    window.localStorage.setItem("ewc.language", nextLanguage);
  }, language);
}

async function gotoPage(page: Page, pageName: "dashboard" | "upload" | "logs" | "settings") {
  const labels = {
    dashboard: /대시보드|Dashboard/,
    upload: /업로드|Upload/,
    logs: /로그|Logs/,
    settings: /설정|Settings/,
  };
  await page.locator("aside").getByRole("button", { name: labels[pageName] }).click();
  await page.locator("main").waitFor({ state: "visible" });
}

async function runUploadPreview(page: Page, startUploadState: "enabled" | "disabled" = "enabled") {
  await gotoPage(page, "upload");
  const controls = page.locator(".upload-preview__actions");
  await controls.getByRole("button", { name: /미리보기|Preview/ }).click();
  await expect(page.locator(".preview-status-strip")).toContainText(/완료|Succeeded/, { timeout: 15_000 });
  await expect(page.locator(".preview-summary-strip").getByText(/DB에 있음|Already in DB/)).toBeVisible();
  const startUploadButton = controls.getByRole("button", { name: /업로드 시작|Start Upload/ });
  if (startUploadState === "enabled") {
    await expect(startUploadButton).toBeEnabled({ timeout: 15_000 });
  } else {
    await expect(startUploadButton).toBeDisabled({ timeout: 15_000 });
  }
}

async function openAndCancelStartUploadReview(page: Page) {
  const controls = page.locator(".upload-preview__actions");
  await controls.getByRole("button", { name: /업로드 시작|Start Upload/ }).click();
  const dialog = page.locator(".start-upload-modal");
  await expect(dialog).toBeVisible({ timeout: 5_000 });
  await expect(dialog.locator(".start-upload-modal__actions .button--danger")).toBeDisabled();
  await dialog.locator(".start-upload-modal__actions .button--secondary").click();
  await expect(dialog).toBeHidden({ timeout: 5_000 });
}

async function openMockUploadJob(page: Page) {
  await gotoPage(page, "upload");
  await page.locator(".upload-tabs button").nth(1).click();
  await expect(page.locator(".upload-job")).toBeVisible({ timeout: 5_000 });
}

async function openAuditLogs(page: Page) {
  await gotoPage(page, "logs");
  await page.getByRole("button", { name: /감사 로그|Audit Logs/ }).click();
  await expect(page.locator("#audit-logs-title")).toBeVisible({ timeout: 5_000 });
}

async function scanTextArtifacts(testInfo: TestInfo) {
  const files = ["summary.json", "console.jsonl", "network-failures.jsonl"];
  for (const file of files) {
    const fullPath = path.join(testInfo.outputDir, file);
    let content = "";
    try {
      content = await fs.readFile(fullPath, "utf8");
    } catch {
      continue;
    }
    for (const pattern of forbiddenArtifactText) {
      expect(content, `forbidden artifact marker ${pattern} in ${file}`).not.toMatch(pattern);
    }
  }
}

test.describe("Upload Job and Audit Logs screenshot QA", () => {
  test("captures mock-mode screenshots across required viewports", async ({ page }, testInfo) => {
    const consoleRows: CaptureLog[] = [];
    const pageErrors: CaptureLog[] = [];
    const failedRequests: CaptureLog[] = [];
    const badResponses: CaptureLog[] = [];
    const screenshots: string[] = [];

    page.on("console", (message) => {
      const type = message.type();
      if (type === "error" || type === "warning") {
        consoleRows.push({
          type,
          url: redact(message.location().url ?? ""),
          text: redact(message.text()),
        });
      }
    });
    page.on("pageerror", (error) => {
      pageErrors.push({ type: "pageerror", url: "", text: redact(error.message) });
    });
    page.on("requestfailed", (request) => {
      failedRequests.push({
        type: "requestfailed",
        url: redact(request.url()),
        text: redact(request.failure()?.errorText ?? ""),
      });
    });
    page.on("response", (response) => {
      const status = response.status();
      const url = response.url();
      if (status >= 400 && !url.includes("/@vite/") && !url.includes("/__vite_ping")) {
        badResponses.push({ type: `http-${status}`, url: redact(url), text: "" });
      }
    });

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/?preview=risky_blocked");
    await runUploadPreview(page, "disabled");

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await setLanguage(page, "ko");
      await page.goto("/");
      await expect(page.locator("main")).toBeVisible();
      await capture(page, testInfo, viewport, "dashboard-ko", screenshots);

      await runUploadPreview(page);
      await capture(page, testInfo, viewport, "upload-preview-ko", screenshots);
      await openAndCancelStartUploadReview(page);

      await openMockUploadJob(page);
      await expect(page.getByText("수락").first()).toBeVisible();
      await capture(page, testInfo, viewport, "upload-job-ko", screenshots);

      await gotoPage(page, "logs");
      await capture(page, testInfo, viewport, "job-logs-ko", screenshots);

      await openAuditLogs(page);
      await capture(page, testInfo, viewport, "audit-logs-ko", screenshots);

      await gotoPage(page, "settings");
      await capture(page, testInfo, viewport, "settings-ko", screenshots);

      await setLanguage(page, "en");
      await page.reload();
      await openMockUploadJob(page);
      await expect(page.getByText("Accepted").first()).toBeVisible();
      await capture(page, testInfo, viewport, "upload-job-en", screenshots);

      await openAuditLogs(page);
      await capture(page, testInfo, viewport, "audit-logs-en", screenshots);
    }

    const combinedFailures = [...consoleRows, ...pageErrors, ...failedRequests, ...badResponses];
    await writeJsonl(path.join(testInfo.outputDir, "console.jsonl"), [...consoleRows, ...pageErrors]);
    await writeJsonl(path.join(testInfo.outputDir, "network-failures.jsonl"), [...failedRequests, ...badResponses]);
    await fs.writeFile(
      path.join(testInfo.outputDir, "summary.json"),
      JSON.stringify(
        {
          artifactRoot: ".gstack/screenshots/upload-job-browser-qa",
          screenshots,
          viewportCount: viewports.length,
          mode: "mock",
          realUploadPerformed: false,
          failureCount: combinedFailures.length,
        },
        null,
        2,
      ),
      "utf8",
    );
    await scanTextArtifacts(testInfo);
    expect(combinedFailures).toEqual([]);
  });
});
