import { expect, test, type Page } from "@playwright/test";

const apiModeEnabled = process.env.EWC_QA_VITE_API_MODE === "api";

type GateCase = {
  reviewShellVisible: boolean;
  source: "default" | "env";
  status: "hidden" | "review_shell_visible";
  reason: string;
};

function featureGate(overrides: Partial<GateCase> = {}) {
  const gate: GateCase = {
    reviewShellVisible: false,
    source: "default",
    status: "hidden",
    reason: "date_scoped_delete_ui_gate_default_off",
    ...overrides,
  };
  return {
    key: "v2_date_scoped_delete_ui_enabled",
    enabled: false,
    reviewShellVisible: gate.reviewShellVisible,
    source: gate.source,
    mutable: false,
    requiredRole: "maintainer",
    status: gate.status,
    reason: gate.reason,
  };
}

function configResponse(gate: ReturnType<typeof featureGate>) {
  const blockedGate = (key: string, requiredRole: string, reason: string) => ({
    key,
    enabled: false,
    reviewShellVisible: false,
    source: "default",
    mutable: false,
    requiredRole,
    status: "hidden",
    reason,
  });

  return {
    configFilePath: "hidden",
    items: [
      {
        key: "plcDataDir",
        label: "PLC data folder",
        value: "qa-source",
        source: "default",
        secret: false,
        envKey: "EWC_PLC_DATA_DIR",
        overridden: false,
      },
    ],
    featureGates: {
      v2DeleteExpansion: blockedGate("v2_delete_expansion_enabled", "maintainer", "delete_expansion_gate_default_off"),
      v2DateScopedDeleteUi: gate,
      v2LanAccess: blockedGate("v2_lan_access_enabled", "admin", "lan_access_gate_default_off"),
    },
    targetClasses: {
      db: {
        configured: true,
        source: "default",
        targetClass: "local",
        hostClass: "loopback",
        portClass: "local_supabase_db",
        pathClass: "not_applicable",
      },
      uploadEdge: {
        configured: true,
        source: "default",
        targetClass: "local",
        hostClass: "loopback",
        portClass: "local_supabase_api",
        pathClass: "not_applicable",
      },
      runtimeEdge: {
        configured: true,
        source: "default",
        targetClass: "local",
        hostClass: "loopback",
        portClass: "local_supabase_api",
        pathClass: "not_applicable",
      },
      uploadRuntimeAligned: true,
      status: "passed",
      reason: "target_classes_aligned",
    },
    stateContext: {
      contextClass: "qa_temporary",
      label: "QA temporary state",
      storageStatus: "present",
      source: "init",
    },
  };
}

function latestPreviewResponse() {
  return {
    run: {
      previewRunId: "qa_preview",
      status: "succeeded",
      requestedAt: "2026-06-22T00:00:00Z",
      startedAt: "2026-06-22T00:00:01Z",
      finishedAt: "2026-06-22T00:00:02Z",
      dbStatus: "reachable",
      summary: {
        total: 1,
        target: 0,
        alreadyInDb: 1,
        partialOverlap: 0,
        risky: 0,
        excluded: 0,
        uploadRows: 0,
        targetRows: 0,
        partialOverlapRows: 0,
        dbMatchedRows: 12,
      },
      warnings: [],
      requestedProfile: "large_source_operational",
      appliedProfile: "large_source_operational",
      autoProfileReason: null,
      timeoutStage: null,
      timing: null,
      errorCode: null,
      errorMessage: null,
    },
    items: [
      {
        previewItemId: 101,
        status: "already_in_db",
        reasonCode: "already_in_db",
        reasonText: "Exact keys already exist.",
        kind: "plc",
        folderLabel: "PLC",
        filename: "qa_fixture.csv",
        path: "qa-source/qa_fixture.csv",
        fileDate: "2026-06-22",
        sizeBytes: 1000,
        modifiedAt: "2026-06-22T00:00:00Z",
        scanMode: "full",
        rowCount: 12,
        localKeyCount: 12,
        dbMatchCount: 12,
        uploadRowEstimate: 0,
        firstTimestamp: "2026-06-22T00:00:00Z",
        lastTimestamp: "2026-06-22T00:01:00Z",
        deviceIds: ["QA"],
        issues: [],
        timeoutStage: null,
        timing: null,
        errorCode: null,
        errorMessage: null,
      },
    ],
    page: { limit: 100, offset: 0, totalItems: 1 },
  };
}

async function installApiRoutes(page: Page, gate: ReturnType<typeof featureGate>) {
  const mutationCalls: string[] = [];

  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith("/api/")) {
      await route.continue();
      return;
    }
    const method = request.method();
    if (method !== "GET") {
      mutationCalls.push(`${method} ${url.pathname}`);
      await route.fulfill({ status: 500, contentType: "application/json", body: "{}" });
      return;
    }

    if (url.pathname === "/api/config") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(configResponse(gate)) });
      return;
    }
    if (url.pathname === "/api/upload/preview/latest") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(latestPreviewResponse()) });
      return;
    }
    if (url.pathname === "/api/upload/delete/jobs/latest" || url.pathname === "/api/upload/jobs/latest") {
      await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
      return;
    }

    await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
  });

  return mutationCalls;
}

async function gotoUpload(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("ewc.language", "en");
  });
  await page.goto("/");
  await page.locator("aside").getByRole("button", { name: "Upload" }).click();
  await expect(page.getByRole("heading", { name: "Upload Preview" })).toBeVisible();
}

test.describe("Date-scoped delete review shell gate", () => {
  test.skip(!apiModeEnabled, "Run with EWC_QA_VITE_API_MODE=api.");

  test("keeps the review shell hidden when reviewShellVisible is false", async ({ page }) => {
    const mutationCalls = await installApiRoutes(page, featureGate());

    await gotoUpload(page);

    await expect(page.getByText("Date-scoped delete review")).toHaveCount(0);
    expect(mutationCalls).toEqual([]);
  });

  test("shows only a disabled non-mutating shell when reviewShellVisible is true", async ({ page }) => {
    const mutationCalls = await installApiRoutes(
      page,
      featureGate({
        reviewShellVisible: true,
        source: "env",
        status: "review_shell_visible",
        reason: "date_scoped_delete_ui_review_shell_visible",
      }),
    );

    await gotoUpload(page);

    await expect(page.getByText("Date-scoped delete review")).toBeVisible();
    await expect(page.getByText("Mutation unavailable")).toBeVisible();
    await expect(page.getByRole("button", { name: "Date-scoped delete unavailable" })).toBeDisabled();
    expect(mutationCalls).toEqual([]);
  });
});
