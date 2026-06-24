import { mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.EWC_BACKEND_SERVED_QA_URL ?? "http://127.0.0.1:8000/";
const outputDir =
  process.env.EWC_RESPONSIVE_SCREENSHOT_DIR ??
  path.join(os.tmpdir(), "ewc-responsive-scroll-screenshots");

const viewports = [
  { width: 390, height: 844 },
  { width: 480, height: 900 },
  { width: 640, height: 900 },
  { width: 834, height: 900 },
  { width: 1024, height: 768 },
  { width: 1280, height: 900 },
  { width: 1440, height: 900 },
];

const pages = [
  { name: "dashboard", nav: 0, tab: null, waitMs: 10_000, scroller: ".dashboard-page" },
  { name: "upload-preview", nav: 1, tab: 0, waitMs: 750, scroller: ".page--upload" },
  { name: "upload-job", nav: 1, tab: 1, waitMs: 750, scroller: ".page--upload" },
  { name: "logs-job", nav: 2, tab: 0, waitMs: 750, scroller: ".page--logs" },
  { name: "audit-logs", nav: 2, tab: 1, waitMs: 750, scroller: ".page--logs" },
  { name: "settings", nav: 3, tab: null, waitMs: 750, scroller: ".settings-page" },
];

const scrollStops = [
  { name: "top", ratio: 0 },
  { name: "middle", ratio: 0.5 },
  { name: "bottom", ratio: 1 },
];

const criticalSelectors = [
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
  await setScroll(page, target.scroller, 0);
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

async function getScrollMetrics(page, selector) {
  return page.evaluate((scrollerSelector) => {
    const scroller = document.querySelector(scrollerSelector);
    const node = scroller ?? document.scrollingElement ?? document.documentElement;
    return {
      clientHeight: node.clientHeight,
      scrollHeight: node.scrollHeight,
      maxScrollTop: Math.max(0, node.scrollHeight - node.clientHeight),
    };
  }, selector);
}

async function setScroll(page, selector, ratio) {
  return page.evaluate(
    ({ scrollerSelector, scrollRatio }) => {
      const scroller = document.querySelector(scrollerSelector);
      const node = scroller ?? document.scrollingElement ?? document.documentElement;
      const maxScrollTop = Math.max(0, node.scrollHeight - node.clientHeight);
      node.scrollTop = Math.round(maxScrollTop * scrollRatio);
      return {
        scrollTop: node.scrollTop,
        clientHeight: node.clientHeight,
        scrollHeight: node.scrollHeight,
        maxScrollTop,
      };
    },
    { scrollerSelector: selector, scrollRatio: ratio },
  );
}

async function measureLayout(page) {
  return page.evaluate((selectors) => {
    const viewport = window.innerWidth;
    const offenders = [];
    const clipped = [];

    for (const selector of selectors) {
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
  }, criticalSelectors);
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

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const consoleErrors = [];
const failedRequests = [];
const captures = [];

page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});

page.on("requestfailed", (request) => {
  const failure = request.failure()?.errorText ?? "";
  failedRequests.push(`${request.method()} ${request.url()} ${failure}`);
});

for (const viewport of viewports) {
  await page.setViewportSize(viewport);
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 15_000 });
  await page.waitForTimeout(500);

  for (const target of pages) {
    await selectView(page, target);
    const metrics = await getScrollMetrics(page, target.scroller);

    for (const stop of scrollStops) {
      const scroll = await setScroll(page, target.scroller, stop.ratio);
      await page.waitForTimeout(250);

      const fileName = `${viewport.width}x${viewport.height}-${target.name}-${stop.name}.png`;
      const filePath = path.join(outputDir, fileName);
      const layout = await measureLayout(page);
      await page.screenshot({ path: filePath, fullPage: false });
      captures.push({
        viewport,
        page: target.name,
        stop: stop.name,
        filePath,
        initialMaxScrollTop: metrics.maxScrollTop,
        scroll,
        layout,
      });
    }
  }
}

await browser.close();

const layoutIssues = captures.filter(
  (capture) =>
    capture.layout.offenders.length > 0 ||
    capture.layout.clipped.length > 0 ||
    capture.layout.scrollWidth > capture.layout.viewport + 1 ||
    capture.layout.bodyScrollWidth > capture.layout.viewport + 1,
);
const { ignoredFailedRequests, unexpectedFailedRequests } = splitFailedRequests(failedRequests);

const summary = {
  baseUrl,
  outputDir,
  summaryPath: path.join(outputDir, "summary.json"),
  captureCount: captures.length,
  viewports,
  pages: pages.map((target) => target.name),
  scrollStops: scrollStops.map((stop) => stop.name),
  layoutIssueCount: layoutIssues.length,
  layoutIssues,
  captures,
  consoleErrors: unique(consoleErrors),
  failedRequests: unique(failedRequests),
  ignoredFailedRequests,
  unexpectedFailedRequests,
};

await writeFile(summary.summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

console.log(
  JSON.stringify(
    {
      baseUrl: summary.baseUrl,
      outputDir: summary.outputDir,
      summaryPath: summary.summaryPath,
      captureCount: summary.captureCount,
      viewports: summary.viewports.map((viewport) => `${viewport.width}x${viewport.height}`),
      pages: summary.pages,
      scrollStops: summary.scrollStops,
      layoutIssueCount: summary.layoutIssueCount,
      consoleErrors: summary.consoleErrors,
      failedRequests: summary.failedRequests,
      ignoredFailedRequests: summary.ignoredFailedRequests,
      unexpectedFailedRequests: summary.unexpectedFailedRequests,
    },
    null,
    2,
  ),
);

if (layoutIssues.length > 0 || consoleErrors.length > 0 || unexpectedFailedRequests.length > 0) {
  process.exitCode = 1;
}
