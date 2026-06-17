import type {
  PreviewItem,
  PreviewItemStatus,
  PreviewQueryParams,
  PreviewResponse,
  PreviewRunStatus,
  PreviewSummary,
} from "../../api/uploadPreview";

const uploadableItems: PreviewItem[] = [
  {
    previewItemId: 101,
    status: "target",
    reasonCode: "db_no_match",
    reasonText: "No exact DB keys found; safe preview target.",
    kind: "plc",
    folderLabel: "PLC",
    filename: "training_fixture_A.csv",
    path: "training-source/upload-preview/A.csv",
    fileDate: "2026-06-01",
    sizeBytes: 8_821_234,
    modifiedAt: "2026-06-01T09:03:00+09:00",
    scanMode: "full",
    rowCount: 20_000,
    localKeyCount: 20_000,
    dbMatchCount: 0,
    uploadRowEstimate: 20_000,
    firstTimestamp: "2026-06-01T08:59:00+09:00",
    lastTimestamp: "2026-06-01T09:30:00+09:00",
    deviceIds: ["extruder_integrated"],
    issues: [],
  },
  {
    previewItemId: 102,
    status: "already_in_db",
    reasonCode: "db_full_match",
    reasonText: "All exact (timestamp, device_id) keys already exist.",
    kind: "plc",
    folderLabel: "PLC",
    filename: "training_fixture_B.csv",
    path: "training-source/upload-preview/B.csv",
    fileDate: "2026-06-01",
    sizeBytes: 8_103_554,
    modifiedAt: "2026-06-01T08:34:00+09:00",
    scanMode: "full",
    rowCount: 18_003,
    localKeyCount: 18_003,
    dbMatchCount: 18_003,
    uploadRowEstimate: 0,
    firstTimestamp: "2026-06-01T08:29:00+09:00",
    lastTimestamp: "2026-06-01T08:58:00+09:00",
    deviceIds: ["extruder_integrated"],
    issues: [],
  },
  {
    previewItemId: 103,
    status: "partial_overlap",
    reasonCode: "db_partial_match",
    reasonText: "Some exact keys already exist in DB. Upload is excluded unless explicitly allowed later.",
    kind: "plc",
    folderLabel: "PLC",
    filename: "training_fixture_C.csv",
    path: "training-source/upload-preview/C.csv",
    fileDate: "2026-06-01",
    sizeBytes: 7_402_120,
    modifiedAt: "2026-06-01T08:04:00+09:00",
    scanMode: "full",
    rowCount: 16_000,
    localKeyCount: 16_000,
    dbMatchCount: 9_250,
    uploadRowEstimate: 6_750,
    firstTimestamp: "2026-06-01T07:59:00+09:00",
    lastTimestamp: "2026-06-01T08:28:00+09:00",
    deviceIds: ["extruder_integrated"],
    issues: ["overlap"],
  },
  {
    previewItemId: 105,
    status: "excluded",
    reasonCode: "file_unstable",
    reasonText: "File was modified inside the configured stability lag window.",
    kind: "plc",
    folderLabel: "PLC",
    filename: "training_fixture_D.csv",
    path: "training-source/upload-preview/D.csv",
    fileDate: "2026-06-01",
    sizeBytes: 931_204,
    modifiedAt: "2026-06-01T09:31:40+09:00",
    scanMode: "metadata",
    rowCount: null,
    localKeyCount: null,
    dbMatchCount: null,
    uploadRowEstimate: 0,
    firstTimestamp: null,
    lastTimestamp: null,
    deviceIds: [],
    issues: ["file_unstable"],
  },
];

const riskyBlockedItem: PreviewItem = {
  previewItemId: 104,
  status: "risky",
  reasonCode: "schema_mismatch",
  reasonText: "CSV schema is incomplete; timestamp or device_id could not be confirmed.",
  kind: "plc",
  folderLabel: "PLC",
  filename: "training_fixture_schema_check.csv",
  path: "training-source/upload-preview/schema-check.csv",
  fileDate: "2026-06-01",
  sizeBytes: 2_231_902,
  modifiedAt: "2026-06-01T07:58:00+09:00",
  scanMode: "sample",
  rowCount: null,
  localKeyCount: null,
  dbMatchCount: null,
  uploadRowEstimate: 0,
  firstTimestamp: null,
  lastTimestamp: null,
  deviceIds: [],
  issues: ["schema_mismatch"],
};

const riskyBlockedItems: PreviewItem[] = [
  ...uploadableItems.slice(0, 3),
  riskyBlockedItem,
  uploadableItems[3],
];

const koreanReasons: Record<number, string> = {
  101: "DB에서 일치하는 키가 없어 업로드 대상입니다.",
  102: "모든 (timestamp, device_id) 키가 이미 DB에 있습니다.",
  103: "일부 키가 이미 DB에 있습니다. 명시적으로 허용하기 전에는 제외합니다.",
  104: "CSV 스키마가 불완전해 timestamp 또는 device_id를 확인할 수 없습니다.",
  105: "설정된 안정 대기 시간 안에 파일이 수정되었습니다.",
};

const statusRank: Record<PreviewItemStatus, number> = {
  target: 1,
  partial_overlap: 2,
  risky: 3,
  already_in_db: 4,
  excluded: 5,
};

function localizeItems(items: PreviewItem[], language: string): PreviewItem[] {
  if (language.startsWith("en")) return items;
  return items.map((item) => ({
    ...item,
    reasonText: koreanReasons[item.previewItemId] ?? item.reasonText,
  }));
}

function getMockStatus(startedAt: number): PreviewRunStatus {
  const elapsed = Date.now() - startedAt;
  if (elapsed < 700) return "queued";
  if (elapsed < 3500) return "running";
  return "succeeded";
}

function applyFilters(
  items: PreviewItem[],
  params: PreviewQueryParams,
  runStatus: PreviewRunStatus,
): PreviewItem[] {
  const availableItems = terminalStatus(runStatus) ? items : items.slice(0, runStatus === "running" ? 3 : 0);
  const search = params.q?.trim().toLowerCase();

  let filtered = availableItems;
  if (params.status && params.status !== "all") {
    filtered = filtered.filter((item) => item.status === params.status);
  }
  if (search) {
    filtered = filtered.filter(
      (item) =>
        item.filename.toLowerCase().includes(search) ||
        item.path.toLowerCase().includes(search) ||
        item.reasonText.toLowerCase().includes(search),
    );
  }

  const orderFactor = params.order === "desc" ? -1 : 1;
  return [...filtered].sort((a, b) => {
    switch (params.sort) {
      case "fileDate":
        return orderFactor * String(a.fileDate ?? "").localeCompare(String(b.fileDate ?? ""));
      case "filename":
        return orderFactor * a.filename.localeCompare(b.filename);
      case "uploadRows":
        return orderFactor * ((a.uploadRowEstimate ?? 0) - (b.uploadRowEstimate ?? 0));
      case "modifiedAt":
        return orderFactor * String(a.modifiedAt ?? "").localeCompare(String(b.modifiedAt ?? ""));
      case "status":
      default:
        return orderFactor * (statusRank[a.status] - statusRank[b.status]);
    }
  });
}

function summarize(items: PreviewItem[]): PreviewSummary {
  return {
    total: items.length,
    target: items.filter((item) => item.status === "target").length,
    alreadyInDb: items.filter((item) => item.status === "already_in_db").length,
    partialOverlap: items.filter((item) => item.status === "partial_overlap").length,
    risky: items.filter((item) => item.status === "risky").length,
    excluded: items.filter((item) => item.status === "excluded").length,
    uploadRows: items
      .filter((item) => item.status === "target")
      .reduce((sum, item) => sum + (item.uploadRowEstimate ?? 0), 0),
    dbMatchedRows: items.reduce((sum, item) => sum + (item.dbMatchCount ?? 0), 0),
  };
}

function getMockPreviewItems(language: string): PreviewItem[] {
  const scenario = new URLSearchParams(window.location.search).get("preview");
  if (scenario === "db_unreachable") return buildDbUnreachableItems(language);
  if (scenario === "risky_blocked") return localizeItems(riskyBlockedItems, language);
  return localizeItems(uploadableItems, language);
}

export function getMockUploadPreview(
  previewRunId: string,
  startedAt: number,
  language: string,
  params: PreviewQueryParams,
  cancelled = false,
): PreviewResponse {
  const dbUnreachable = new URLSearchParams(window.location.search).get("preview") === "db_unreachable";
  const runStatus: PreviewRunStatus = cancelled
    ? "cancelled"
    : dbUnreachable
      ? "partial_failed"
      : getMockStatus(startedAt);
  const allItems = getMockPreviewItems(language);
  const filteredItems = applyFilters(allItems, params, runStatus);
  const offset = params.offset ?? 0;
  const limit = params.limit ?? 100;

  return {
    run: {
      previewRunId,
      status: runStatus,
      requestedAt: new Date(startedAt).toISOString(),
      startedAt: runStatus === "queued" ? null : new Date(startedAt + 700).toISOString(),
      finishedAt: terminalStatus(runStatus) ? new Date(startedAt + 3500).toISOString() : null,
      dbStatus: dbUnreachable ? "unreachable" : runStatus === "queued" ? "not_checked" : "reachable",
      summary: summarize(terminalStatus(runStatus) ? allItems : filteredItems),
      warnings: dbUnreachable ? ["db_unreachable"] : runStatus === "succeeded" ? ["partial_overlap"] : [],
      errorCode: dbUnreachable ? "db_unreachable" : null,
      errorMessage: dbUnreachable
        ? language.startsWith("en")
          ? "Local Supabase DB could not be reached."
          : "Local Supabase DB에 연결할 수 없습니다."
        : null,
    },
    items: filteredItems.slice(offset, offset + limit),
    page: {
      limit,
      offset,
      totalItems: filteredItems.length,
    },
  };
}

function buildDbUnreachableItems(language: string): PreviewItem[] {
  return localizeItems(uploadableItems, language).map((item) =>
    item.status === "excluded"
      ? item
      : {
          ...item,
          status: "risky",
          reasonCode: "db_unreachable",
          reasonText: language.startsWith("en")
            ? "Local Supabase DB could not be reached."
            : "Local Supabase DB에 연결할 수 없습니다.",
          dbMatchCount: null,
          uploadRowEstimate: 0,
          issues: ["db_unreachable"],
        },
  );
}

function terminalStatus(status: PreviewRunStatus): boolean {
  return ["succeeded", "partial_failed", "failed", "cancelled", "timed_out"].includes(status);
}
