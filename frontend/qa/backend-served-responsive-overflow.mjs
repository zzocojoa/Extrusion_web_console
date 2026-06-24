import { chromium } from "playwright";

const baseUrl = process.env.EWC_BACKEND_SERVED_QA_URL ?? "http://127.0.0.1:8000/";
const viewports = [390, 480, 640, 834, 1024, 1280, 1440];
const pages = [
  { name: "Dashboard", nav: 0, tab: null, waitMs: 10_000 },
  { name: "Upload Preview", nav: 1, tab: 0, waitMs: 500 },
  { name: "Upload Job", nav: 1, tab: 1, waitMs: 500 },
  { name: "Logs Job", nav: 2, tab: 0, waitMs: 500 },
  { name: "Audit Logs", nav: 2, tab: 1, waitMs: 500 },
  { name: "Settings", nav: 3, tab: null, waitMs: 500 },
];

const selectors = [
  ".topbar",
  ".topbar__status",
  ".topbar__status .status-chip",
  ".topbar__status .status-badge",
  ".dashboard-status-matrix",
  ".dashboard-status-matrix .status-cell",
  ".dashboard-status-matrix .status-badge",
  ".safety-summary",
  ".safety-summary .button",
  ".preview-status-strip",
  ".preview-status-strip > .status-badge",
  ".upload-preview__actions",
  ".upload-preview__actions .button",
  ".delete-selection-panel",
  ".delete-selection-panel__summary",
  ".delete-selection-panel__metrics",
  ".delete-selection-panel__metrics > span",
  ".upload-job__metrics",
  ".upload-job__metric",
  ".upload-job__actions",
  ".upload-job__actions .button",
  ".logs-panel .panel__header",
  ".audit-toolbar",
  ".audit-summary-strip",
  ".resizable-table__actions",
  ".resizable-table__actions .button",
  ".table-pagination",
  ".table-pagination__buttons",
  ".table-pagination .button",
  ".table-pagination__compact-page",
  ".settings-save-bar__actions",
  ".settings-save-bar__actions .button",
];

async function selectView(page, target) {
  await page.evaluate((navIndex) => {
    const items = Array.from(document.querySelectorAll(".sidebar__nav-item"));
    items[navIndex]?.click();
  }, target.nav);
  await page.waitForTimeout(500);
  if (target.tab !== null) {
    await page.evaluate((tabIndex) => {
      const tabs = Array.from(document.querySelectorAll(".upload-tabs .tab"));
      tabs[tabIndex]?.click();
    }, target.tab);
  }
  await page.waitForTimeout(target.waitMs);
}

function unique(values) {
  return [...new Set(values)];
}

function splitFailedRequests(values) {
  const ignoredFailedRequests = [];
  const unexpectedFailedRequests = [];

  for (const value of unique(values)) {
    if (value.includes("net::ERR_ABORTED")) {
      ignoredFailedRequests.push(value);
    } else {
      unexpectedFailedRequests.push(value);
    }
  }

  return { ignoredFailedRequests, unexpectedFailedRequests };
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const consoleErrors = [];
const failedRequests = [];

page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("requestfailed", (request) => {
  const failure = request.failure()?.errorText ?? "";
  failedRequests.push(`${request.method()} ${request.url()} ${failure}`);
});

const results = [];

for (const width of viewports) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 15_000 });
  await page.waitForTimeout(500);

  for (const target of pages) {
    await selectView(page, target);
    const data = await page.evaluate((criticalSelectors) => {
      const viewport = window.innerWidth;
      const offenders = [];
      const clipped = [];

      for (const selector of criticalSelectors) {
        for (const [index, node] of Array.from(document.querySelectorAll(selector)).entries()) {
          if (node.closest(".table-scroll") && !node.classList.contains("table-pagination")) continue;
          const style = window.getComputedStyle(node);
          if (style.display === "none" || style.visibility === "hidden") continue;
          const rect = node.getBoundingClientRect();
          if (rect.width <= 0 || rect.height <= 0) continue;
          if (rect.left < -1 || rect.right > viewport + 1 || rect.width > viewport + 1) {
            offenders.push({
              selector,
              index,
              left: Math.round(rect.left),
              right: Math.round(rect.right),
              width: Math.round(rect.width),
              viewport,
            });
          }
        }
      }

      for (const selector of [".safety-summary__copy", ".safety-summary h2", ".safety-summary p"]) {
        for (const [index, node] of Array.from(document.querySelectorAll(selector)).entries()) {
          const parent = node.closest(".safety-summary");
          if (!parent) continue;
          const rect = node.getBoundingClientRect();
          const parentRect = parent.getBoundingClientRect();
          if (
            rect.top < parentRect.top - 1 ||
            rect.bottom > parentRect.bottom + 1 ||
            rect.left < parentRect.left - 1 ||
            rect.right > parentRect.right + 1
          ) {
            clipped.push({
              selector,
              index,
              top: Math.round(rect.top),
              bottom: Math.round(rect.bottom),
              parentBottom: Math.round(parentRect.bottom),
            });
          }
        }
      }

      return {
        viewport,
        scrollWidth: document.documentElement.scrollWidth,
        bodyScrollWidth: document.body.scrollWidth,
        offenders,
        clipped,
      };
    }, selectors);

    results.push({ width, page: target.name, ...data });
  }
}

await browser.close();

const bad = results.filter(
  (result) =>
    result.offenders.length > 0 ||
    result.clipped.length > 0 ||
    result.scrollWidth > result.viewport + 1 ||
    result.bodyScrollWidth > result.viewport + 1,
);
const { ignoredFailedRequests, unexpectedFailedRequests } = splitFailedRequests(failedRequests);

const summary = {
  baseUrl,
  viewports,
  pages: pages.map((target) => target.name),
  bad,
  consoleErrors: unique(consoleErrors),
  failedRequests: unique(failedRequests),
  ignoredFailedRequests,
  unexpectedFailedRequests,
};

console.log(JSON.stringify(summary, null, 2));

if (bad.length > 0 || consoleErrors.length > 0 || unexpectedFailedRequests.length > 0) {
  process.exitCode = 1;
}
