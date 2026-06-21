import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Ban, Database, FileSearch, Pause, Play, RotateCcw, Search, Square, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { isLocalTokenApiError } from "../api/client";
import { fetchConfig, type ConfigResponse } from "../api/config";
import {
  createDeletePreflight,
  fetchLatestDeleteJob,
  reconcileDeleteJob,
  startDeleteJob,
  type DeleteJobCreateResponse,
  type DeleteJobLatestResponse,
  type DeletePreflightResponse,
} from "../api/uploadDelete";
import {
  ActiveUploadJobError,
  controlUploadJob,
  createUploadJob,
  fetchLatestUploadJob,
  fetchUploadJob,
  getUploadJobEventsUrl,
  normalizeJobEvent,
  retryUploadJob,
  type JobEvent,
  type UploadJobDetail,
  type UploadJobFileStatus,
  type UploadJobStatus,
} from "../api/uploadJobs";
import {
  ActivePreviewRunError,
  cancelUploadPreview,
  createLargeSourceOperationalPreviewRequest,
  createUploadPreview,
  fetchLatestUploadPreview,
  fetchUploadPreview,
  type PreviewApprovalScope,
  type PreviewItem,
  type PreviewItemStatus,
  type PreviewProfile,
  type PreviewQueryParams,
  type PreviewRangeMode,
  type PreviewResponse,
  type PreviewRunStatus,
  type PreviewSummary,
  type PreviewSortKey,
} from "../api/uploadPreview";
import { localizeJobEvent, type Translate } from "../components/dashboard/localizedDashboardText";
import { StatusBadge } from "../components/status/StatusBadge";
import type { StatusTone } from "./dashboard/dashboardTypes";

const API_MODE = import.meta.env.VITE_API_MODE === "api";

const statusTone: Record<PreviewItemStatus, StatusTone> = {
  target: "ready",
  already_in_db: "muted",
  partial_overlap: "attention",
  risky: "risk",
  excluded: "muted",
};

const runTone: Record<PreviewRunStatus, StatusTone> = {
  queued: "muted",
  running: "running",
  succeeded: "ready",
  partial_failed: "attention",
  failed: "failed",
  cancelling: "attention",
  cancelled: "muted",
  timed_out: "blocked",
};

const terminalRunStatuses: PreviewRunStatus[] = [
  "succeeded",
  "partial_failed",
  "failed",
  "cancelled",
  "timed_out",
];

const activePreviewRunStatuses: PreviewRunStatus[] = ["queued", "running", "cancelling"];
const dbDerivedItemStatuses: PreviewItemStatus[] = ["target", "already_in_db", "partial_overlap"];

const activeJobStatuses: UploadJobStatus[] = ["queued", "running", "pausing", "paused", "cancelling"];

function previewProfileLabelKey(profile?: PreviewProfile | null) {
  switch (profile) {
    case "large_source_operational":
      return "upload.previewMode.largeSource";
    case "stage3_profile_a_bounded_full_scan":
      return "upload.previewMode.stage3ProfileA";
    case "default":
      return "upload.previewMode.standard";
    default:
      return null;
  }
}

function previewAutoReasonLabelKey(reason?: string | null) {
  switch (reason) {
    case "operational_source_class":
      return "upload.previewMode.autoReason.operationalSourceClass";
    case "large_preview_range":
      return "upload.previewMode.autoReason.largePreviewRange";
    default:
      return null;
  }
}

function configValue(config: ConfigResponse | undefined, key: string): unknown {
  return config?.items.find((item) => item.key === key)?.value ?? null;
}

function sourcePathClass(value: unknown): string {
  const normalized = typeof value === "string" ? value.trim() : "";
  if (!normalized) return "missing";
  if (normalized.startsWith("\\\\") || normalized.startsWith("//")) return "network";
  if (normalized.length >= 3 && normalized[1] === ":" && ["\\", "/"].includes(normalized[2])) {
    return "drive_letter";
  }
  if (normalized.startsWith("/mnt/")) return "mounted";
  return "local";
}

function buildPreviewApprovalScope(
  config: ConfigResponse | undefined,
  rangeMode: PreviewRangeMode,
  startDate: string | null,
  endDate: string | null,
  appliedProfile: PreviewProfile,
): PreviewApprovalScope {
  return {
    expectedSourceClasses: {
      plc: sourcePathClass(configValue(config, "plcDataDir")),
    },
    expectedRangeMode: rangeMode,
    expectedStartDate: rangeMode === "custom" ? startDate : null,
    expectedEndDate: rangeMode === "custom" ? endDate : null,
    expectedAppliedProfile: appliedProfile,
  };
}

const jobTone: Record<UploadJobStatus, StatusTone> = {
  queued: "muted",
  running: "running",
  succeeded: "ready",
  partial_failed: "attention",
  failed: "failed",
  pausing: "attention",
  paused: "attention",
  cancelling: "attention",
  cancelled: "muted",
  interrupted: "blocked",
};

const fileTone: Record<UploadJobFileStatus, StatusTone> = {
  queued: "muted",
  running: "running",
  succeeded: "ready",
  failed: "failed",
  skipped: "muted",
  cancelled: "muted",
  interrupted: "blocked",
};

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat().format(value);
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return value.replace("T", " ").replace(/\.\d+/, "").replace("+09:00", "");
}

const sensitiveDiagnosticPatterns = [
  /[A-Za-z]:[\\/]/,
  /\\\\[^\\\s]+\\/,
  /\b(?:https?|postgres(?:ql)?):\/\/\S+/i,
  /\b(?:authorization|bearer|jwt|token|secret|apikey|anon[_-]?key|service[_-]?role)\b/i,
];

function safeDiagnosticFallback(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed) return null;
  if (sensitiveDiagnosticPatterns.some((pattern) => pattern.test(trimmed))) {
    return null;
  }
  return trimmed;
}

function formatPreviewReason(
  reasonCode: string | null | undefined,
  reasonText: string | null | undefined,
  translate: (key: string) => string,
  exists: (key: string) => boolean,
): string {
  if (reasonCode) {
    const key = `upload.reason.${reasonCode}`;
    if (exists(key)) return translate(key);
  }
  return safeDiagnosticFallback(reasonText) ?? translate("upload.reason.unknown");
}

function sumNullable(values: Array<number | null | undefined>): number {
  return values.reduce<number>((total, value) => total + (value ?? 0), 0);
}

function clampRemainingRows(rowCount: number | null, resumeOffset: number): number {
  if (rowCount === null) return 0;
  return Math.max(0, rowCount - resumeOffset);
}

function isActivePreviewRun(status: PreviewRunStatus) {
  return activePreviewRunStatuses.includes(status);
}

function hasDbReconciliationEvidence(item: PreviewItem) {
  return (
    dbDerivedItemStatuses.includes(item.status) ||
    item.dbMatchCount !== null ||
    Boolean(item.timing && Object.keys(item.timing).length > 0)
  );
}

function buildInterimSummary(response: PreviewResponse): PreviewSummary {
  const items = response.items;
  const targetRows = sumNullable(items.filter((item) => item.status === "target").map((item) => item.uploadRowEstimate));
  const partialOverlapRows = sumNullable(
    items.filter((item) => item.status === "partial_overlap").map((item) => item.uploadRowEstimate),
  );
  return {
    total: Math.max(response.page.totalItems ?? 0, items.length),
    target: items.filter((item) => item.status === "target").length,
    alreadyInDb: items.filter((item) => item.status === "already_in_db").length,
    partialOverlap: items.filter((item) => item.status === "partial_overlap").length,
    risky: items.filter((item) => item.status === "risky").length,
    excluded: items.filter((item) => item.status === "excluded").length,
    uploadRows: targetRows + partialOverlapRows,
    targetRows,
    partialOverlapRows,
    dbMatchedRows: sumNullable(items.map((item) => item.dbMatchCount)),
  };
}

function buildPreviewGateBreakdown(preview: PreviewResponse) {
  const { summary } = preview.run;
  const targetItems = preview.items.filter((item) => item.status === "target");
  const physicalRowsFromItems = sumNullable(targetItems.map((item) => item.rowCount));
  const uniqueKeysFromItems = sumNullable(targetItems.map((item) => item.localKeyCount));
  const targetRows = summary.targetRows > 0 ? summary.targetRows : summary.uploadRows;
  const physicalRows = physicalRowsFromItems > 0 ? physicalRowsFromItems : targetRows;
  const uniqueUploadKeys = uniqueKeysFromItems > 0 ? uniqueKeysFromItems : targetRows;
  return {
    targetPhysicalRows: physicalRows,
    targetUniqueUploadKeys: uniqueUploadKeys,
    targetDuplicateKeyCount: Math.max(0, physicalRows - uniqueUploadKeys),
    previewDbMatchedKeys: summary.dbMatchedRows,
    expectedUploadRows: targetRows,
    partialOverlapRows: summary.partialOverlapRows,
    fullUploadEstimateRows: summary.uploadRows,
    loadedTargetFiles: targetItems.length,
    targetFiles: summary.target,
  };
}

function buildPreviewDisplayState(response: PreviewResponse) {
  const active = isActivePreviewRun(response.run.status);
  const hasItems = response.items.length > 0;
  const hasDbEvidence = response.items.some(hasDbReconciliationEvidence);
  const isInterim = active && hasItems;
  const dbStatusLabelKey =
    active && response.run.dbStatus === "not_checked" && hasDbEvidence
      ? "upload.dbStatus.reconciling"
      : `upload.dbStatus.${response.run.dbStatus}`;

  return {
    summary: isInterim ? buildInterimSummary(response) : response.run.summary,
    isInterim,
    dbStatusLabelKey,
    startUploadDisabledReasonKey: active
      ? "upload.actions.startUploadDisabledRunning"
      : "upload.actions.startUploadDisabledReason",
  };
}

function isRetryableJobFileStatus(status: UploadJobFileStatus) {
  return status === "failed" || status === "interrupted";
}

function buildRetryGateBreakdown(detail: UploadJobDetail) {
  const retryFiles = detail.files.filter((file) => isRetryableJobFileStatus(file.status));
  return {
    retryFiles: retryFiles.length,
    physicalRows: sumNullable(retryFiles.map((file) => file.rowCount)),
    resumeOffsetRows: sumNullable(retryFiles.map((file) => file.resumeOffset)),
    remainingPhysicalRows: sumNullable(retryFiles.map((file) => clampRemainingRows(file.rowCount, file.resumeOffset))),
    acceptedRows: detail.job.summary.acceptedRows,
  };
}

function mockRunId() {
  return `mock_${Date.now()}`;
}

export function UploadPage() {
  const { i18n, t } = useTranslation();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"preview" | "job">("preview");
  const [rangeMode, setRangeMode] = useState<PreviewRangeMode>("today");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [previewRunId, setPreviewRunId] = useState<string | null>(null);
  const [mockStartedAt, setMockStartedAt] = useState<number | null>(null);
  const [mockCancelled, setMockCancelled] = useState(false);
  const [statusFilter, setStatusFilter] = useState<PreviewItemStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<PreviewSortKey>("status");
  const [selectedDeleteItemIds, setSelectedDeleteItemIds] = useState<number[]>([]);
  const [deleteReviewPreflight, setDeleteReviewPreflight] = useState<DeletePreflightResponse | null>(null);
  const [lastDeleteResult, setLastDeleteResult] = useState<DeleteJobCreateResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [mockJobStartedAt, setMockJobStartedAt] = useState<number | null>(null);
  const [mockJobPaused, setMockJobPaused] = useState(false);
  const [mockJobCancelled, setMockJobCancelled] = useState(false);
  const [sseEvents, setSseEvents] = useState<JobEvent[]>([]);
  const latestSeqRef = useRef(0);

  const queryParams: PreviewQueryParams = useMemo(
    () => ({
      status: statusFilter,
      q: search,
      sort,
      order: "asc",
      limit: 100,
      offset: 0,
    }),
    [search, sort, statusFilter],
  );

  const configQuery = useQuery({
    queryKey: ["config", "preview-approval-scope"],
    queryFn: fetchConfig,
    enabled: API_MODE,
    retry: false,
    refetchInterval: API_MODE ? 30_000 : false,
  });

  const previewApprovalScope = useMemo(
    () => {
      const normalizedStartDate = rangeMode === "custom" ? startDate || null : null;
      const normalizedEndDate = rangeMode === "custom" ? endDate || null : null;
      if (!API_MODE) {
        return {
          expectedSourceClasses: { plc: "local" },
          expectedRangeMode: rangeMode,
          expectedStartDate: normalizedStartDate,
          expectedEndDate: normalizedEndDate,
          expectedAppliedProfile: "large_source_operational" as const,
        };
      }
      return buildPreviewApprovalScope(
        configQuery.data,
        rangeMode,
        normalizedStartDate,
        normalizedEndDate,
        "large_source_operational",
      );
    },
    [configQuery.data, endDate, rangeMode, startDate],
  );

  const latestQuery = useQuery({
    queryKey: ["upload-preview", "latest", queryParams],
    enabled: activeTab === "preview" && !previewRunId && API_MODE,
    queryFn: () => fetchLatestUploadPreview(queryParams),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status && terminalRunStatuses.includes(status) ? false : 900;
    },
  });

  const previewQuery = useQuery({
    queryKey: ["upload-preview", previewRunId, mockStartedAt, mockCancelled, queryParams, i18n.language],
    enabled: activeTab === "preview" && Boolean(previewRunId),
    queryFn: async () => {
      if (!previewRunId) return null;
      if (!API_MODE) {
        const { getMockUploadPreview } = await import("./upload/mockUploadPreview");
        return getMockUploadPreview(
          previewRunId,
          mockStartedAt ?? Date.now(),
          i18n.language,
          queryParams,
          mockCancelled,
        );
      }
      return fetchUploadPreview(previewRunId, queryParams);
    },
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status && terminalRunStatuses.includes(status) ? false : 900;
    },
  });

  const currentPreview = previewRunId ? previewQuery.data ?? null : latestQuery.data ?? null;
  const activePreviewRunId = currentPreview?.run.previewRunId ?? previewRunId;
  const selectedDeleteItems = useMemo(() => {
    if (!currentPreview) return [];
    const selected = new Set(selectedDeleteItemIds);
    return currentPreview.items.filter((item) => selected.has(item.previewItemId) && item.status === "already_in_db");
  }, [currentPreview, selectedDeleteItemIds]);
  const canStartUpload = Boolean(
      currentPreview?.run.status === "succeeded" &&
      currentPreview.run.dbStatus === "reachable" &&
      currentPreview.run.summary.target > 0 &&
      currentPreview.run.summary.targetRows > 0 &&
      currentPreview.run.summary.risky === 0,
  );
  const latestDeleteJobQuery = useQuery({
    queryKey: ["upload-delete", "latest"],
    enabled: API_MODE,
    queryFn: fetchLatestDeleteJob,
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.job.status;
      return status && ["preparing", "running", "finalizing", "reconciling"].includes(status) ? 1200 : false;
    },
  });
  const activeDeleteBlocker = Boolean(latestDeleteJobQuery.data?.activeDeleteBlocker);
  const canPreflightDelete = Boolean(
    API_MODE &&
      currentPreview?.run.status === "succeeded" &&
      currentPreview.run.dbStatus === "reachable" &&
      !activeDeleteBlocker &&
      selectedDeleteItems.length > 0 &&
      selectedDeleteItems.length === selectedDeleteItemIds.length,
  );

  useEffect(() => {
    if (!currentPreview) {
      setSelectedDeleteItemIds([]);
      return;
    }
    const selectableIds = new Set(
      currentPreview.items
        .filter((item) => item.status === "already_in_db")
        .map((item) => item.previewItemId),
    );
    setSelectedDeleteItemIds((previous) => previous.filter((itemId) => selectableIds.has(itemId)));
  }, [currentPreview?.run.previewRunId, currentPreview?.items]);

  const latestJobQuery = useQuery({
    queryKey: ["upload-job", "latest", API_MODE ? "api" : "mock"],
    enabled: activeTab === "job" && !jobId,
    queryFn: async () => {
      if (!API_MODE) {
        const { getMockUploadJob } = await import("./upload/mockUploadJob");
        return getMockUploadJob("mock_upl_latest", Date.now() - 8_000, false, false);
      }
      return fetchLatestUploadJob();
    },
    retry: false,
  });

  const jobQuery = useQuery({
    queryKey: ["upload-job", jobId, mockJobStartedAt, mockJobPaused, mockJobCancelled, i18n.language],
    enabled: activeTab === "job" && Boolean(jobId),
    queryFn: async () => {
      if (!jobId) return null;
      if (!API_MODE) {
        const { getMockUploadJob } = await import("./upload/mockUploadJob");
        return getMockUploadJob(
          jobId,
          mockJobStartedAt ?? Date.now(),
          mockJobPaused,
          mockJobCancelled,
        );
      }
      return fetchUploadJob(jobId);
    },
    refetchInterval: (query) => {
      const status = query.state.data?.job.status;
      return status && activeJobStatuses.includes(status) ? 1200 : false;
    },
  });

  const currentJob = useMemo(() => {
    const detail = jobId ? jobQuery.data ?? null : latestJobQuery.data ?? null;
    if (!detail || sseEvents.length === 0 || !jobId || detail.job.jobId !== jobId) return detail;
    const relevantEvents = sseEvents.filter((event) => event.jobId === detail.job.jobId);
    if (relevantEvents.length === 0) return detail;
    const bySeq = new Map<number, JobEvent>();
    for (const event of detail.events) bySeq.set(event.seq, event);
    for (const event of relevantEvents) bySeq.set(event.seq, event);
    const latestSseSeq = relevantEvents.reduce((latest, event) => Math.max(latest, event.seq), 0);
    return {
      ...detail,
      events: [...bySeq.values()].sort((a, b) => a.seq - b.seq),
      eventCursor: { latestSeq: Math.max(detail.eventCursor.latestSeq, latestSseSeq) },
    };
  }, [jobId, jobQuery.data, latestJobQuery.data, sseEvents]);

  useEffect(() => {
    latestSeqRef.current = 0;
    setSseEvents([]);
  }, [jobId]);

  useEffect(() => {
    if (!API_MODE || !jobId || activeTab !== "job") return;
    const streamJobId = jobId;
    const afterSeq = Math.max(latestSeqRef.current, jobQuery.data?.eventCursor.latestSeq ?? 0);
    latestSeqRef.current = afterSeq;
    const source = new EventSource(getUploadJobEventsUrl(streamJobId, afterSeq));
    const eventTypes = [
      "job.created",
      "job.started",
      "job.progress",
      "job.pausing",
      "job.paused",
      "job.resumed",
      "job.cancelling",
      "job.cancelled",
      "job.succeeded",
      "job.partial_failed",
      "job.failed",
      "job.interrupted",
      "file.queued",
      "file.started",
      "file.progress",
      "file.succeeded",
      "file.failed",
      "file.cancelled",
      "log.info",
      "log.warning",
      "log.error",
      "audit.recorded",
    ];
    const onEvent: EventListener = (event) => {
      const message = event as MessageEvent<string>;
      let parsed: JobEvent;
      try {
        parsed = normalizeJobEvent(JSON.parse(message.data));
      } catch {
        return;
      }
      if (parsed.jobId !== streamJobId) return;
      latestSeqRef.current = Math.max(latestSeqRef.current, parsed.seq);
      setSseEvents((previous) => {
        if (previous.some((item) => item.seq === parsed.seq)) return previous;
        return [...previous, parsed].slice(-300);
      });
      if (parsed.eventType.startsWith("job.") || ["file.succeeded", "file.failed", "file.cancelled"].includes(parsed.eventType)) {
        void queryClient.invalidateQueries({ queryKey: ["upload-job", streamJobId] });
      }
    };
    for (const eventType of eventTypes) source.addEventListener(eventType, onEvent);
    return () => source.close();
  }, [activeTab, jobId, jobQuery.data?.eventCursor.latestSeq, queryClient]);

  const createMutation = useMutation({
    mutationFn: async () => {
      if (API_MODE && !configQuery.data) {
        throw new Error("Preview approval scope could not be built");
      }
      const request = createLargeSourceOperationalPreviewRequest(
        rangeMode,
        rangeMode === "custom" ? startDate || null : null,
        rangeMode === "custom" ? endDate || null : null,
        previewApprovalScope,
      );
      if (!API_MODE) {
        const id = mockRunId();
        setMockStartedAt(Date.now());
        setMockCancelled(false);
        return { previewRunId: id, status: "queued" as const, pollUrl: `/api/upload/preview/${id}` };
      }
      return createUploadPreview(request);
    },
    onSuccess: (response) => {
      setPreviewRunId(response.previewRunId);
      setActiveTab("preview");
    },
    onError: (error) => {
      if (error instanceof ActivePreviewRunError) {
        setPreviewRunId(error.activePreviewRunId);
        setActiveTab("preview");
      }
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async () => {
      if (!activePreviewRunId) throw new Error("No preview run");
      if (!API_MODE) return { previewRunId: activePreviewRunId, status: "cancelled" as const, pollUrl: "" };
      return cancelUploadPreview(activePreviewRunId);
    },
    onSuccess: () => {
      if (!API_MODE) setMockCancelled(true);
    },
  });

  const startUploadMutation = useMutation({
    mutationFn: async (approval: { expectedTargetRows: number; expectedTargetFiles: number }) => {
      if (!activePreviewRunId) throw new Error("No preview run");
      if (!API_MODE) {
        const id = `mock_upl_${Date.now()}`;
        setMockJobStartedAt(Date.now());
        setMockJobPaused(false);
        setMockJobCancelled(false);
        return { jobId: id, status: "queued" as const, detailUrl: "", eventsUrl: "" };
      }
      return createUploadJob(activePreviewRunId, approval);
    },
    onSuccess: (response) => {
      latestSeqRef.current = 0;
      setSseEvents([]);
      setJobId(response.jobId);
      setActiveTab("job");
    },
    onError: (error) => {
      if (error instanceof ActiveUploadJobError) {
        setJobId(error.activeJobId);
        setActiveTab("job");
      }
    },
  });

  const deletePreflightMutation = useMutation({
    mutationFn: async () => {
      if (!currentPreview) throw new Error("No preview run");
      return createDeletePreflight({
        previewRunId: currentPreview.run.previewRunId,
        previewItemIds: selectedDeleteItemIds,
        expectedAlreadyInDbItems: selectedDeleteItemIds.length,
      });
    },
    onSuccess: (response) => {
      setDeleteReviewPreflight(response);
    },
  });

  const startDeleteMutation = useMutation({
    mutationFn: async (confirmation: {
      preflightId: string;
      expectedDeleteKeys: number;
      typedDeleteKeys: string;
      acknowledgeNoUndo: boolean;
      acknowledgeRollbackRequiresFreshPreviewAndStartUpload: boolean;
    }) => startDeleteJob(confirmation),
    onSuccess: (response) => {
      setLastDeleteResult(response);
      setDeleteReviewPreflight(null);
      setSelectedDeleteItemIds([]);
      void queryClient.invalidateQueries({ queryKey: ["upload-delete", "latest"] });
      void queryClient.invalidateQueries({ queryKey: ["upload-preview"] });
    },
  });

  const reconcileDeleteMutation = useMutation({
    mutationFn: async (job: DeleteJobLatestResponse["job"]) =>
      reconcileDeleteJob(job.deleteRunId, job.status === "reconciliation_failed"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["upload-delete", "latest"] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: async (approval: { expectedRemainingRows: number; expectedRetryFiles: number }) => {
      if (!currentJob) throw new Error("No upload job");
      if (!API_MODE) {
        const id = `mock_retry_${Date.now()}`;
        setMockJobStartedAt(Date.now());
        setMockJobPaused(false);
        setMockJobCancelled(false);
        return { jobId: id, status: "queued" as const, detailUrl: "", eventsUrl: "" };
      }
      return retryUploadJob(currentJob.job.jobId, approval);
    },
    onSuccess: (response) => {
      latestSeqRef.current = 0;
      setSseEvents([]);
      setJobId(response.jobId);
      setActiveTab("job");
    },
  });

  const controlMutation = useMutation({
    mutationFn: async (action: "pause" | "resume" | "cancel") => {
      if (!currentJob) throw new Error("No upload job");
      if (!API_MODE) {
        if (action === "pause") setMockJobPaused(true);
        if (action === "resume") setMockJobPaused(false);
        if (action === "cancel") setMockJobCancelled(true);
        return currentJob;
      }
      return controlUploadJob(currentJob.job.jobId, action);
    },
  });

  return (
    <main className="page page--upload">
      <section className="upload-tabs" aria-label={t("upload.tabs.label")}>
        <button
          type="button"
          className={activeTab === "preview" ? "tab tab--active" : "tab"}
          onClick={() => setActiveTab("preview")}
        >
          {t("upload.tabs.preview")}
        </button>
        <button
          type="button"
          className={activeTab === "job" ? "tab tab--active" : "tab"}
          onClick={() => setActiveTab("job")}
        >
          {t("upload.tabs.job")}
        </button>
      </section>

      {activeTab === "preview" ? (
        <PreviewTab
          currentPreview={currentPreview}
          loading={
            previewQuery.isLoading ||
            latestQuery.isLoading ||
            createMutation.isPending ||
            (API_MODE && configQuery.isLoading && !currentPreview)
          }
          error={
            previewQuery.error ??
            latestQuery.error ??
            configQuery.error ??
            createMutation.error ??
            cancelMutation.error
          }
          rangeMode={rangeMode}
          startDate={startDate}
          endDate={endDate}
          statusFilter={statusFilter}
          search={search}
          sort={sort}
          canCancel={Boolean(
            currentPreview?.run.status &&
              ["queued", "running", "cancelling"].includes(currentPreview.run.status),
          )}
          runPreviewDisabled={createMutation.isPending || Boolean(
            currentPreview?.run.status &&
              ["queued", "running", "cancelling"].includes(currentPreview.run.status),
          ) || (API_MODE && (!configQuery.data || configQuery.isLoading))}
          cancelling={cancelMutation.isPending}
          approvalScope={previewApprovalScope}
          approvalScopeReady={!API_MODE || Boolean(configQuery.data)}
          onRangeModeChange={setRangeMode}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          onRunPreview={() => createMutation.mutate()}
          onCancel={() => cancelMutation.mutate()}
          canStartUpload={canStartUpload}
          startUploadPending={startUploadMutation.isPending}
          startUploadError={startUploadMutation.error}
          onStartUpload={(approval) => startUploadMutation.mutate(approval)}
          selectedDeleteItemIds={selectedDeleteItemIds}
          canPreflightDelete={canPreflightDelete}
          deletePreflight={deleteReviewPreflight}
          deletePreflightPending={deletePreflightMutation.isPending}
          deletePreflightError={deletePreflightMutation.error}
          startDeletePending={startDeleteMutation.isPending}
          startDeleteError={startDeleteMutation.error}
          latestDeleteJob={latestDeleteJobQuery.data ?? null}
          latestDeleteJobError={latestDeleteJobQuery.error}
          lastDeleteResult={lastDeleteResult}
          reconcileDeletePending={reconcileDeleteMutation.isPending}
          reconcileDeleteError={reconcileDeleteMutation.error}
          onToggleDeleteItem={(itemId, selected) => {
            setSelectedDeleteItemIds((previous) => {
              if (selected) return previous.includes(itemId) ? previous : [...previous, itemId].sort((a, b) => a - b);
              return previous.filter((value) => value !== itemId);
            });
          }}
          onClearDeleteSelection={() => setSelectedDeleteItemIds([])}
          onOpenDeletePreflight={() => deletePreflightMutation.mutate()}
          onCancelDeleteReview={() => setDeleteReviewPreflight(null)}
          onStartDelete={(confirmation) => startDeleteMutation.mutate(confirmation)}
          onReconcileDelete={(job) => reconcileDeleteMutation.mutate(job)}
          onStatusFilterChange={setStatusFilter}
          onSearchChange={setSearch}
          onSortChange={setSort}
        />
      ) : (
        <JobTab
          detail={currentJob}
          loading={jobQuery.isLoading || latestJobQuery.isLoading || retryMutation.isPending || controlMutation.isPending}
          retryPending={retryMutation.isPending}
          error={jobQuery.error ?? latestJobQuery.error ?? retryMutation.error ?? controlMutation.error}
          onPause={() => controlMutation.mutate("pause")}
          onResume={() => controlMutation.mutate("resume")}
          onCancel={() => controlMutation.mutate("cancel")}
          onRetry={(approval) => retryMutation.mutate(approval)}
        />
      )}
    </main>
  );
}

interface PreviewTabProps {
  currentPreview: PreviewResponse | null;
  loading: boolean;
  error: Error | null;
  rangeMode: PreviewRangeMode;
  startDate: string;
  endDate: string;
  statusFilter: PreviewItemStatus | "all";
  search: string;
  sort: PreviewSortKey;
  canCancel: boolean;
  runPreviewDisabled: boolean;
  cancelling: boolean;
  approvalScope: PreviewApprovalScope;
  approvalScopeReady: boolean;
  canStartUpload: boolean;
  startUploadPending: boolean;
  startUploadError: Error | null;
  selectedDeleteItemIds: number[];
  canPreflightDelete: boolean;
  deletePreflight: DeletePreflightResponse | null;
  deletePreflightPending: boolean;
  deletePreflightError: Error | null;
  startDeletePending: boolean;
  startDeleteError: Error | null;
  latestDeleteJob: DeleteJobLatestResponse | null;
  latestDeleteJobError: Error | null;
  lastDeleteResult: DeleteJobCreateResponse | null;
  reconcileDeletePending: boolean;
  reconcileDeleteError: Error | null;
  onRangeModeChange: (value: PreviewRangeMode) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onRunPreview: () => void;
  onCancel: () => void;
  onStartUpload: (approval: { expectedTargetRows: number; expectedTargetFiles: number }) => void;
  onToggleDeleteItem: (itemId: number, selected: boolean) => void;
  onClearDeleteSelection: () => void;
  onOpenDeletePreflight: () => void;
  onCancelDeleteReview: () => void;
  onStartDelete: (confirmation: {
    preflightId: string;
    expectedDeleteKeys: number;
    typedDeleteKeys: string;
    acknowledgeNoUndo: boolean;
    acknowledgeRollbackRequiresFreshPreviewAndStartUpload: boolean;
  }) => void;
  onReconcileDelete: (job: DeleteJobLatestResponse["job"]) => void;
  onStatusFilterChange: (value: PreviewItemStatus | "all") => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: PreviewSortKey) => void;
}

function PreviewTab(props: PreviewTabProps) {
  const { i18n, t } = useTranslation();
  const [startReviewOpen, setStartReviewOpen] = useState(false);
  const run = props.currentPreview?.run;
  const displayState = props.currentPreview ? buildPreviewDisplayState(props.currentPreview) : null;
  const summary = displayState?.summary;
  const runAlert = Boolean(
    run &&
      (["partial_failed", "failed", "timed_out"].includes(run.status) ||
        ["unreachable", "query_failed"].includes(run.dbStatus)),
  );
  const startUploadDisabledReason = displayState?.startUploadDisabledReasonKey ?? "upload.actions.startUploadDisabledReason";
  const reviewablePreview = props.currentPreview && run && summary ? props.currentPreview : null;
  const appliedProfileLabelKey = previewProfileLabelKey(run?.appliedProfile);
  const autoProfileReasonLabelKey = previewAutoReasonLabelKey(run?.autoProfileReason);
  const selectedAlreadyInDbCount = props.selectedDeleteItemIds.length;
  const deleteDisabledReason = !API_MODE
    ? "upload.delete.actions.apiModeRequired"
    : selectedAlreadyInDbCount <= 0
      ? "upload.delete.actions.noSelection"
      : "upload.delete.actions.preflightDisabled";

  function openStartUploadReview() {
    if (!props.canStartUpload || !reviewablePreview) return;
    setStartReviewOpen(true);
  }

  function closeStartUploadReview() {
    setStartReviewOpen(false);
  }

  function confirmStartUpload() {
    props.onStartUpload({
      expectedTargetRows: reviewablePreview?.run.summary.targetRows ?? 0,
      expectedTargetFiles: reviewablePreview?.run.summary.target ?? 0,
    });
    setStartReviewOpen(false);
  }

  function openDeletePreflight() {
    if (!props.canPreflightDelete || props.deletePreflightPending) return;
    props.onOpenDeletePreflight();
  }

  return (
    <section className="upload-preview">
      <div className="panel upload-preview__controls">
        <div className="panel__header">
          <h2>{t("upload.preview.title")}</h2>
          <div className="upload-preview__actions">
            {props.canCancel ? (
              <button className="button button--secondary" type="button" onClick={props.onCancel}>
                <Ban size={16} aria-hidden="true" />
                {props.cancelling ? t("upload.actions.cancelling") : t("upload.actions.cancelPreview")}
              </button>
            ) : null}
            <button
              className="button button--primary"
              type="button"
              onClick={props.onRunPreview}
              disabled={props.runPreviewDisabled}
            >
              <FileSearch size={16} aria-hidden="true" />
              {t("upload.actions.runPreview")}
            </button>
            <button
              className="button button--primary"
              type="button"
              disabled={!props.canStartUpload || props.startUploadPending}
              onClick={openStartUploadReview}
              title={!props.canStartUpload ? t(startUploadDisabledReason) : undefined}
            >
              <Play size={16} aria-hidden="true" />
              {props.startUploadPending ? t("upload.actions.startingUpload") : t("upload.actions.startUpload")}
            </button>
            <button
              className="button button--danger"
              type="button"
              disabled={!props.canPreflightDelete || props.deletePreflightPending}
              onClick={openDeletePreflight}
              title={!props.canPreflightDelete ? t(deleteDisabledReason) : undefined}
            >
              <Trash2 size={16} aria-hidden="true" />
              {props.deletePreflightPending
                ? t("upload.delete.actions.preflighting")
                : t("upload.delete.actions.reviewDelete", { count: selectedAlreadyInDbCount })}
            </button>
          </div>
        </div>
        <div className="upload-preview__toolbar">
          <label>
            <span>{t("upload.controls.range")}</span>
            <select value={props.rangeMode} onChange={(event) => props.onRangeModeChange(event.target.value as PreviewRangeMode)}>
              <option value="today">{t("upload.range.today")}</option>
              <option value="yesterday">{t("upload.range.yesterday")}</option>
              <option value="last_2_days">{t("upload.range.last2Days")}</option>
              <option value="custom">{t("upload.range.custom")}</option>
            </select>
          </label>
          {props.rangeMode === "custom" ? (
            <>
              <label>
                <span>{t("upload.controls.startDate")}</span>
                <input type="date" value={props.startDate} onChange={(event) => props.onStartDateChange(event.target.value)} />
              </label>
              <label>
                <span>{t("upload.controls.endDate")}</span>
                <input type="date" value={props.endDate} onChange={(event) => props.onEndDateChange(event.target.value)} />
              </label>
            </>
          ) : null}
          <div className="upload-preview__source">
            <Database size={16} aria-hidden="true" />
            <span>{t("upload.controls.source")}</span>
          </div>
          <div className="upload-preview__mode-note" role="status">
            {t("upload.previewMode.largeSourceNote")}
          </div>
        </div>
        <div className="upload-preview__approval-scope" role="status">
          <span>{t("upload.previewApproval.title")}</span>
          <strong>
            {props.approvalScopeReady
              ? t("upload.previewApproval.detail", {
                  sourceClass: props.approvalScope.expectedSourceClasses.plc ?? "missing",
                  range: t(
                    `upload.range.${props.approvalScope.expectedRangeMode === "last_2_days" ? "last2Days" : props.approvalScope.expectedRangeMode}`,
                  ),
                  profile: t(
                    previewProfileLabelKey(props.approvalScope.expectedAppliedProfile) ?? "upload.previewMode.largeSource",
                  ),
                })
              : t("upload.previewApproval.loading")}
          </strong>
        </div>
      </div>

      {run ? (
        <div className={`preview-status-strip ${runAlert ? "preview-status-strip--warning" : ""}`} role={runAlert ? "alert" : "status"}>
          <StatusBadge tone={runTone[run.status]} label={t(`upload.runStatus.${run.status}`)} />
          <span>{t("upload.preview.runId")}: <code>{run.previewRunId}</code></span>
          <span>{t("upload.preview.db")}: {t(displayState?.dbStatusLabelKey ?? `upload.dbStatus.${run.dbStatus}`)}</span>
          {appliedProfileLabelKey ? (
            <span>
              {t("upload.previewMode.applied")}: {t(appliedProfileLabelKey)}
              {autoProfileReasonLabelKey ? ` (${t(autoProfileReasonLabelKey)})` : ""}
            </span>
          ) : null}
          <span>{t("upload.preview.updated")}: {formatDateTime(run.finishedAt ?? run.startedAt ?? run.requestedAt)}</span>
          {run.errorMessage ? (
            <strong>{formatPreviewReason(run.errorCode, run.errorMessage, t, (key) => i18n.exists(key))}</strong>
          ) : null}
        </div>
      ) : null}

      {summary ? <PreviewSummaryStrip summary={summary} interim={Boolean(displayState?.isInterim)} /> : null}

      {props.error ? (
        <div className="error-banner" role="alert">
          {formatOperatorError(props.error, t("upload.preview.error"))}
        </div>
      ) : null}
      {props.startUploadError ? (
        <div className="error-banner" role="alert">
          {t("upload.job.startError")}: {props.startUploadError.message}
        </div>
      ) : null}
      {props.deletePreflightError ? (
        <div className="error-banner" role="alert">
          {t("upload.delete.preflightError")}: {props.deletePreflightError.message}
        </div>
      ) : null}
      {props.startDeleteError ? (
        <div className="error-banner" role="alert">
          {t("upload.delete.startError")}: {props.startDeleteError.message}
        </div>
      ) : null}
      {props.reconcileDeleteError ? (
        <div className="error-banner" role="alert">
          {t("upload.delete.reconcileError")}: {props.reconcileDeleteError.message}
        </div>
      ) : null}

      <DeleteSelectionPanel
        selectedCount={selectedAlreadyInDbCount}
        canPreflight={props.canPreflightDelete}
        pending={props.deletePreflightPending}
        latestDeleteJob={props.latestDeleteJob}
        latestDeleteJobError={props.latestDeleteJobError}
        lastDeleteResult={props.lastDeleteResult}
        reconcilePending={props.reconcileDeletePending}
        onReviewDelete={openDeletePreflight}
        onClear={props.onClearDeleteSelection}
        onReconcile={props.onReconcileDelete}
      />

      <div className="panel">
        <div className="preview-table-toolbar">
          <label className="preview-search">
            <Search size={15} aria-hidden="true" />
            <input
              value={props.search}
              placeholder={t("upload.controls.search")}
              onChange={(event) => props.onSearchChange(event.target.value)}
            />
          </label>
          <select value={props.statusFilter} onChange={(event) => props.onStatusFilterChange(event.target.value as PreviewItemStatus | "all")}>
            <option value="all">{t("upload.filters.all")}</option>
            <option value="target">{t("upload.status.target")}</option>
            <option value="already_in_db">{t("upload.status.already_in_db")}</option>
            <option value="partial_overlap">{t("upload.status.partial_overlap")}</option>
            <option value="risky">{t("upload.status.risky")}</option>
            <option value="excluded">{t("upload.status.excluded")}</option>
          </select>
          <select value={props.sort} onChange={(event) => props.onSortChange(event.target.value as PreviewSortKey)}>
            <option value="status">{t("upload.sort.status")}</option>
            <option value="fileDate">{t("upload.sort.fileDate")}</option>
            <option value="filename">{t("upload.sort.filename")}</option>
            <option value="uploadRows">{t("upload.sort.uploadRows")}</option>
            <option value="modifiedAt">{t("upload.sort.modifiedAt")}</option>
          </select>
        </div>
        {props.loading && !props.currentPreview ? (
          <div className="panel--loading">{t("upload.preview.loading")}</div>
        ) : props.currentPreview ? (
          <PreviewTable
            items={props.currentPreview.items}
            selectedDeleteItemIds={props.selectedDeleteItemIds}
            onToggleDeleteItem={props.onToggleDeleteItem}
          />
        ) : (
          <div className="upload-empty">
            <FileSearch aria-hidden="true" />
            <strong>{t("upload.empty.title")}</strong>
            <span>{t("upload.empty.detail")}</span>
          </div>
        )}
      </div>

      {startReviewOpen && reviewablePreview ? (
        <StartUploadConfirmationModal
          preview={reviewablePreview}
          onCancel={closeStartUploadReview}
          onConfirm={confirmStartUpload}
          pending={props.startUploadPending}
        />
      ) : null}
      {props.deletePreflight ? (
        <DeleteConfirmationModal
          preflight={props.deletePreflight}
          pending={props.startDeletePending}
          onCancel={props.onCancelDeleteReview}
          onConfirm={props.onStartDelete}
        />
      ) : null}
    </section>
  );
}

function StartUploadConfirmationModal({
  preview,
  onCancel,
  onConfirm,
  pending,
}: {
  preview: PreviewResponse;
  onCancel: () => void;
  onConfirm: () => void;
  pending: boolean;
}) {
  const { t } = useTranslation();
  const [typedRows, setTypedRows] = useState("");
  const { run } = preview;
  const { summary } = run;
  const breakdown = buildPreviewGateBreakdown(preview);
  const expectedRows = String(summary.targetRows);
  const formattedUploadRows = formatNumber(summary.targetRows);
  const confirmAllowed =
    run.status === "succeeded" &&
    run.dbStatus === "reachable" &&
    summary.target > 0 &&
    summary.targetRows > 0 &&
    summary.risky === 0 &&
    typedRows.trim() === expectedRows;
  const blockedReasons = [
    run.status !== "succeeded" ? t("upload.startReview.blocked.previewStatus") : null,
    run.dbStatus !== "reachable" ? t("upload.startReview.blocked.dbStatus") : null,
    summary.target <= 0 || summary.targetRows <= 0 ? t("upload.startReview.blocked.noTarget") : null,
    summary.risky > 0 ? t("upload.startReview.blocked.risky") : null,
  ].filter((reason): reason is string => Boolean(reason));
  const countItems: Array<{ id: string; label: string; value: string | number }> = [
    { id: "previewRunId", label: t("upload.startReview.previewRunId"), value: run.previewRunId },
    { id: "targetFiles", label: t("upload.startReview.targetFiles"), value: summary.target },
    { id: "targetPhysicalRows", label: t("upload.startReview.targetPhysicalRows"), value: formatNumber(breakdown.targetPhysicalRows) },
    { id: "targetUniqueUploadKeys", label: t("upload.startReview.targetUniqueUploadKeys"), value: formatNumber(breakdown.targetUniqueUploadKeys) },
    { id: "targetDuplicateKeyCount", label: t("upload.startReview.targetDuplicateKeyCount"), value: formatNumber(breakdown.targetDuplicateKeyCount) },
    { id: "previewDbMatchedKeys", label: t("upload.startReview.previewDbMatchedKeys"), value: formatNumber(breakdown.previewDbMatchedKeys) },
    { id: "expectedUploadRows", label: t("upload.startReview.expectedUploadRows"), value: formatNumber(breakdown.expectedUploadRows) },
    { id: "partialOverlapRows", label: t("upload.startReview.partialOverlapRows"), value: formatNumber(breakdown.partialOverlapRows) },
    { id: "fullUploadEstimateRows", label: t("upload.startReview.fullUploadEstimateRows"), value: formatNumber(breakdown.fullUploadEstimateRows) },
    { id: "alreadyInDb", label: t("upload.startReview.alreadyInDb"), value: summary.alreadyInDb },
    { id: "risky", label: t("upload.startReview.risky"), value: summary.risky },
    { id: "excluded", label: t("upload.startReview.excluded"), value: summary.excluded },
    { id: "dbStatus", label: t("upload.startReview.dbStatus"), value: t(`upload.dbStatus.${run.dbStatus}`) },
  ];

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-labelledby="start-upload-review-title"
        aria-modal="true"
        className="start-upload-modal"
        role="dialog"
      >
        <div className="start-upload-modal__header">
          <div>
            <span className="panel-eyebrow">{t("upload.startReview.eyebrow")}</span>
            <h2 id="start-upload-review-title">{t("upload.startReview.title")}</h2>
          </div>
          <StatusBadge tone={confirmAllowed ? "attention" : "blocked"} label={t("upload.startReview.badge")} />
        </div>

        <div className="start-upload-modal__warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <span>{t("upload.startReview.warning", { files: summary.target, rowsFormatted: formattedUploadRows })}</span>
        </div>

        <dl className="start-upload-modal__counts">
          {countItems.map(({ id, label, value }) => (
            <div className="start-upload-modal__count" key={id}>
              <dt>{label}</dt>
              <dd className="num">{value}</dd>
            </div>
          ))}
        </dl>

        <p className="start-upload-modal__note">
          {t("upload.startReview.countSemantics")}
        </p>
        {breakdown.loadedTargetFiles < breakdown.targetFiles ? (
          <p className="start-upload-modal__note start-upload-modal__note--attention">
            {t("upload.startReview.partialBreakdown", {
              loaded: breakdown.loadedTargetFiles,
              total: breakdown.targetFiles,
            })}
          </p>
        ) : null}

        {blockedReasons.length > 0 ? (
          <div className="start-upload-modal__blocked" role="alert">
            <strong>{t("upload.startReview.blocked.title")}</strong>
            <ul>
              {blockedReasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <label className="start-upload-modal__input">
          <span>{t("upload.startReview.inputLabel", { rows: expectedRows })}</span>
          <input
            autoComplete="off"
            inputMode="numeric"
            pattern="[0-9]*"
            value={typedRows}
            onChange={(event) => setTypedRows(event.target.value.replace(/[^\d]/g, ""))}
            placeholder={expectedRows}
          />
        </label>

        <div className="start-upload-modal__actions">
          <button className="button button--secondary" type="button" onClick={onCancel}>
            {t("upload.startReview.cancel")}
          </button>
          <button
            className="button button--danger"
            type="button"
            disabled={!confirmAllowed || pending}
            onClick={onConfirm}
          >
            {pending ? t("upload.actions.startingUpload") : t("upload.startReview.confirm", { rowsFormatted: formattedUploadRows })}
          </button>
        </div>
      </section>
    </div>
  );
}

function DeleteSelectionPanel({
  selectedCount,
  canPreflight,
  pending,
  latestDeleteJob,
  latestDeleteJobError,
  lastDeleteResult,
  reconcilePending,
  onReviewDelete,
  onClear,
  onReconcile,
}: {
  selectedCount: number;
  canPreflight: boolean;
  pending: boolean;
  latestDeleteJob: DeleteJobLatestResponse | null;
  latestDeleteJobError: Error | null;
  lastDeleteResult: DeleteJobCreateResponse | null;
  reconcilePending: boolean;
  onReviewDelete: () => void;
  onClear: () => void;
  onReconcile: (job: DeleteJobLatestResponse["job"]) => void;
}) {
  const { t } = useTranslation();
  const job = latestDeleteJob?.job ?? null;
  const showPanel = selectedCount > 0 || job || lastDeleteResult || latestDeleteJobError;
  if (!showPanel) return null;
  const canReconcile = Boolean(job?.recoveryRequired);
  return (
    <section className="panel delete-selection-panel" aria-label={t("upload.delete.panel.title")}>
      <div className="delete-selection-panel__summary">
        <div>
          <span className="panel-eyebrow">{t("upload.delete.panel.eyebrow")}</span>
          <strong>{t("upload.delete.panel.selected", { count: selectedCount })}</strong>
        </div>
        <div className="delete-selection-panel__actions">
          {selectedCount > 0 ? (
            <button className="button button--secondary" type="button" onClick={onClear}>
              {t("upload.delete.actions.clearSelection")}
            </button>
          ) : null}
          {selectedCount > 0 ? (
            <button
              className="button button--danger"
              type="button"
              disabled={!canPreflight || pending}
              onClick={onReviewDelete}
            >
              <Trash2 size={16} aria-hidden="true" />
              {pending ? t("upload.delete.actions.preflighting") : t("upload.delete.actions.reviewDelete", { count: selectedCount })}
            </button>
          ) : null}
          {job && canReconcile ? (
            <button
              className="button button--secondary"
              type="button"
              disabled={reconcilePending}
              onClick={() => onReconcile(job)}
            >
              <RotateCcw size={16} aria-hidden="true" />
              {reconcilePending ? t("upload.delete.actions.reconciling") : t("upload.delete.actions.reconcile")}
            </button>
          ) : null}
        </div>
      </div>
      {lastDeleteResult ? (
        <div className="delete-selection-panel__line" role="status">
          {t("upload.delete.panel.lastResult", {
            status: t(`upload.delete.status.${lastDeleteResult.status}`),
            rows: formatNumber(lastDeleteResult.deletedKeys),
          })}
        </div>
      ) : null}
      {job ? (
        <div className="delete-selection-panel__line" role={job.recoveryRequired ? "alert" : "status"}>
          {t("upload.delete.panel.latestJob", {
            status: t(`upload.delete.status.${job.status}`),
            expected: formatNumber(job.expectedDeleteKeys),
            deleted: formatNumber(job.deletedKeys),
          })}
          {job.errorCode ? <span>{t("upload.delete.panel.reason", { reason: localizeDeleteReason(job.errorCode, t) })}</span> : null}
        </div>
      ) : null}
      {latestDeleteJobError ? (
        <div className="error-banner" role="alert">
          {t("upload.delete.latestError")}: {latestDeleteJobError.message}
        </div>
      ) : null}
    </section>
  );
}

function DeleteConfirmationModal({
  preflight,
  pending,
  onCancel,
  onConfirm,
}: {
  preflight: DeletePreflightResponse;
  pending: boolean;
  onCancel: () => void;
  onConfirm: (confirmation: {
    preflightId: string;
    expectedDeleteKeys: number;
    typedDeleteKeys: string;
    acknowledgeNoUndo: boolean;
    acknowledgeRollbackRequiresFreshPreviewAndStartUpload: boolean;
  }) => void;
}) {
  const { t } = useTranslation();
  const [typedRows, setTypedRows] = useState("");
  const [ackNoUndo, setAckNoUndo] = useState(false);
  const [ackRollback, setAckRollback] = useState(false);
  const expectedRows = String(preflight.selectedKeyCount);
  const ready = preflight.status === "ready" && preflight.rollbackReady && preflight.dbTargetGuard.status === "passed";
  const confirmAllowed = ready && ackNoUndo && ackRollback && typedRows.replace(/,/g, "").trim() === expectedRows;
  const blockedReasons = [
    preflight.status !== "ready" ? localizeDeleteReason(preflight.reasonCode, t) : null,
    !preflight.rollbackReady ? t("upload.delete.review.blocked.rollback") : null,
    preflight.dbTargetGuard.status !== "passed" ? localizeDeleteReason(preflight.dbTargetGuard.reasonCode, t) : null,
  ].filter((reason): reason is string => Boolean(reason));
  const counts: Array<{ id: string; label: string; value: string | number }> = [
    { id: "preflightId", label: t("upload.delete.review.preflightId"), value: preflight.preflightId },
    { id: "selectedItems", label: t("upload.delete.review.selectedItems"), value: preflight.selectedItemCount },
    { id: "selectedKeys", label: t("upload.delete.review.selectedKeys"), value: formatNumber(preflight.selectedKeyCount) },
    { id: "dbGuard", label: t("upload.delete.review.dbGuard"), value: t(`upload.delete.guard.${preflight.dbTargetGuard.status}`) },
    { id: "targetClass", label: t("upload.delete.review.targetClass"), value: preflight.dbTargetGuard.targetClass },
    { id: "rollback", label: t("upload.delete.review.rollback"), value: preflight.rollbackReady ? t("status.ready") : t("status.blocked") },
    { id: "expiresAt", label: t("upload.delete.review.expiresAt"), value: formatDateTime(preflight.expiresAt) },
  ];
  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-labelledby="delete-review-title"
        aria-modal="true"
        className="start-upload-modal"
        role="dialog"
      >
        <div className="start-upload-modal__header">
          <div>
            <span className="panel-eyebrow">{t("upload.delete.review.eyebrow")}</span>
            <h2 id="delete-review-title">{t("upload.delete.review.title")}</h2>
          </div>
          <StatusBadge tone={confirmAllowed ? "risk" : "blocked"} label={t("upload.delete.review.badge")} />
        </div>

        <div className="start-upload-modal__warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <span>
            {t("upload.delete.review.warning", {
              rowsFormatted: formatNumber(preflight.selectedKeyCount),
              items: preflight.selectedItemCount,
            })}
          </span>
        </div>

        <dl className="start-upload-modal__counts">
          {counts.map(({ id, label, value }) => (
            <div className="start-upload-modal__count" key={id}>
              <dt>{label}</dt>
              <dd className="num">{value}</dd>
            </div>
          ))}
        </dl>

        <p className="start-upload-modal__note">
          {t("upload.delete.review.countSemantics")}
        </p>

        {preflight.rollbackBlockers.length > 0 ? (
          <div className="start-upload-modal__blocked" role="alert">
            <strong>{t("upload.delete.review.rollbackBlockers")}</strong>
            <ul>
              {preflight.rollbackBlockers.map((reason) => (
                <li key={reason}>{localizeDeleteReason(reason, t)}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {blockedReasons.length > 0 ? (
          <div className="start-upload-modal__blocked" role="alert">
            <strong>{t("upload.delete.review.blocked.title")}</strong>
            <ul>
              {blockedReasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <label className="start-upload-modal__input">
          <span>{t("upload.delete.review.inputLabel", { rows: expectedRows })}</span>
          <input
            autoComplete="off"
            inputMode="numeric"
            pattern="[0-9,]*"
            value={typedRows}
            onChange={(event) => setTypedRows(event.target.value.replace(/[^\d,]/g, ""))}
            placeholder={expectedRows}
          />
        </label>

        <label className="start-upload-modal__check">
          <input
            type="checkbox"
            checked={ackNoUndo}
            onChange={(event) => setAckNoUndo(event.target.checked)}
          />
          <span>{t("upload.delete.review.ackNoUndo")}</span>
        </label>
        <label className="start-upload-modal__check">
          <input
            type="checkbox"
            checked={ackRollback}
            onChange={(event) => setAckRollback(event.target.checked)}
          />
          <span>{t("upload.delete.review.ackRollback")}</span>
        </label>

        <div className="start-upload-modal__actions">
          <button className="button button--secondary" type="button" onClick={onCancel}>
            {t("upload.delete.review.cancel")}
          </button>
          <button
            className="button button--danger"
            type="button"
            disabled={!confirmAllowed || pending}
            onClick={() =>
              onConfirm({
                preflightId: preflight.preflightId,
                expectedDeleteKeys: preflight.selectedKeyCount,
                typedDeleteKeys: typedRows,
                acknowledgeNoUndo: ackNoUndo,
                acknowledgeRollbackRequiresFreshPreviewAndStartUpload: ackRollback,
              })
            }
          >
            {pending
              ? t("upload.delete.review.pending")
              : t("upload.delete.review.confirm", { rowsFormatted: formatNumber(preflight.selectedKeyCount) })}
          </button>
        </div>
      </section>
    </div>
  );
}

function localizeDeleteReason(reasonCode: string | null | undefined, translate: (key: string) => string): string {
  if (!reasonCode) return translate("upload.delete.reason.unknown");
  const key = `upload.delete.reason.${reasonCode}`;
  const translated = translate(key);
  return translated === key ? reasonCode : translated;
}

function PreviewSummaryStrip({
  summary,
  interim,
}: {
  summary: PreviewResponse["run"]["summary"];
  interim: boolean;
}) {
  const { t } = useTranslation();
  const items: Array<[PreviewItemStatus, number]> = [
    ["target", summary.target],
    ["already_in_db", summary.alreadyInDb],
    ["partial_overlap", summary.partialOverlap],
    ["risky", summary.risky],
    ["excluded", summary.excluded],
  ];
  return (
    <div className={`preview-summary-strip ${interim ? "preview-summary-strip--interim" : ""}`}>
      {interim ? (
        <div className="preview-summary-note" role="status">
          {t("upload.preview.interimSummary")}
        </div>
      ) : null}
      {items.map(([status, value]) => (
        <div className="preview-summary-cell" key={status}>
          <StatusBadge tone={statusTone[status]} label={t(`upload.status.${status}`)} />
          <strong>{formatNumber(value)}</strong>
        </div>
      ))}
      <div className="preview-summary-cell">
        <span>{t("upload.preview.uploadRows")}</span>
        <strong>{formatNumber(summary.uploadRows)}</strong>
      </div>
      <div className="preview-summary-cell">
        <span>{t("upload.preview.targetRows")}</span>
        <strong>{formatNumber(summary.targetRows)}</strong>
      </div>
      <div className="preview-summary-cell">
        <span>{t("upload.preview.partialOverlapRows")}</span>
        <strong>{formatNumber(summary.partialOverlapRows)}</strong>
      </div>
    </div>
  );
}

function PreviewTable({
  items,
  selectedDeleteItemIds,
  onToggleDeleteItem,
}: {
  items: PreviewItem[];
  selectedDeleteItemIds: number[];
  onToggleDeleteItem: (itemId: number, selected: boolean) => void;
}) {
  const { i18n, t } = useTranslation();
  const selectedIds = new Set(selectedDeleteItemIds);
  if (items.length === 0) {
    return <div className="panel--loading">{t("upload.empty.noRows")}</div>;
  }
  return (
    <div className="table-scroll">
      <table className="data-table data-table--preview">
        <thead>
          <tr>
            <th>{t("upload.delete.table.select")}</th>
            <th>{t("upload.table.status")}</th>
            <th>{t("upload.table.filename")}</th>
            <th>{t("upload.table.kind")}</th>
            <th>{t("upload.table.fileDate")}</th>
            <th>{t("upload.table.rows")}</th>
            <th>{t("upload.table.dbMatch")}</th>
            <th>{t("upload.table.uploadRows")}</th>
            <th>{t("upload.table.reason")}</th>
            <th>{t("upload.table.modified")}</th>
            <th>{t("upload.table.path")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr className={`row--${statusTone[item.status]}`} key={item.previewItemId}>
              <td className="preview-select-cell">
                {item.status === "already_in_db" ? (
                  <input
                    aria-label={t("upload.delete.table.selectRow", { filename: item.filename })}
                    checked={selectedIds.has(item.previewItemId)}
                    type="checkbox"
                    onChange={(event) => onToggleDeleteItem(item.previewItemId, event.target.checked)}
                  />
                ) : (
                  <span aria-hidden="true">-</span>
                )}
              </td>
              <td><StatusBadge tone={statusTone[item.status]} label={t(`upload.status.${item.status}`)} /></td>
              <td className="preview-file-cell">
                <strong>{item.filename}</strong>
                <span>{item.folderLabel}</span>
              </td>
              <td>{t(`upload.kind.${item.kind}`)}</td>
              <td className="num">{item.fileDate ?? "-"}</td>
              <td className="num">{formatNumber(item.rowCount)}</td>
              <td className="num">{formatNumber(item.dbMatchCount)}</td>
              <td className="num">{formatNumber(item.uploadRowEstimate)}</td>
              <td className="preview-reason">
                {formatPreviewReason(item.reasonCode, item.reasonText, t, (key) => i18n.exists(key))}
              </td>
              <td className="num">{formatDateTime(item.modifiedAt)}</td>
              <td className="preview-path" title={item.path}>{item.path}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JobTab({
  detail,
  loading,
  retryPending,
  error,
  onPause,
  onResume,
  onCancel,
  onRetry,
}: {
  detail: UploadJobDetail | null;
  loading: boolean;
  retryPending: boolean;
  error: Error | null;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRetry: (approval: { expectedRemainingRows: number; expectedRetryFiles: number }) => void;
}) {
  const { t } = useTranslation();
  const [retryReviewOpen, setRetryReviewOpen] = useState(false);
  if (loading && !detail) {
    return <section className="panel panel--loading">{t("upload.job.loading")}</section>;
  }
  if (error && !detail) {
    return <div className="error-banner" role="alert">{formatOperatorError(error, t("upload.job.loadError"))}</div>;
  }
  if (!detail) {
    return (
      <section className="panel placeholder-panel">
        <div className="panel__header">
          <h2>{t("upload.job.title")}</h2>
        </div>
        <p>{t("upload.job.placeholder")}</p>
      </section>
    );
  }
  const { job } = detail;
  const progress = job.summary.totalRows > 0
    ? Math.min(100, Math.round((job.summary.processedRows / job.summary.totalRows) * 100))
    : job.summary.totalFiles > 0
      ? Math.round(((job.summary.succeededFiles + job.summary.failedFiles + job.summary.cancelledFiles) / job.summary.totalFiles) * 100)
      : 0;
  const canPause = job.status === "running";
  const canResume = job.status === "paused";
  const canCancel = ["queued", "running", "pausing", "paused"].includes(job.status);
  const canRetry = ["failed", "partial_failed", "interrupted"].includes(job.status) &&
    detail.files.some((file) => ["failed", "interrupted"].includes(file.status));
  return (
    <>
      <section className="upload-job">
        <div className="panel upload-job__header">
          <div className="panel__header">
            <h2>{t("upload.job.title")}</h2>
            <div className="upload-job__actions">
              {canPause ? <button className="button button--secondary" type="button" onClick={onPause}><Pause size={16} />{t("upload.job.actions.pause")}</button> : null}
              {canResume ? <button className="button button--primary" type="button" onClick={onResume}><Play size={16} />{t("upload.job.actions.resume")}</button> : null}
              {canCancel ? <button className="button button--danger" type="button" onClick={onCancel}><Square size={16} />{t("upload.job.actions.cancel")}</button> : null}
              {canRetry ? (
                <button
                  className="button button--secondary"
                  type="button"
                  disabled={retryPending}
                  onClick={() => setRetryReviewOpen(true)}
                >
                  <RotateCcw size={16} />
                  {t("upload.job.actions.retry")}
                </button>
              ) : null}
            </div>
          </div>
          <div className="upload-job__summary">
            <div className="upload-job__identity">
              <StatusBadge tone={jobTone[job.status]} label={t(`upload.job.status.${job.status}`)} />
              <span>{t("upload.job.jobId")}: <code>{job.jobId}</code></span>
              <span>{t("upload.job.mode")}: {t(`upload.job.modeValue.${job.mode}`)}</span>
              <span>{t("upload.job.started")}: {formatDateTime(job.startedAt ?? job.requestedAt)}</span>
            </div>
            <div className="progress progress--job">
              <div className="progress__meta">
                <span>{t("upload.job.progress")}</span>
                <strong>{progress}%</strong>
              </div>
              <div className="progress__track" aria-label={t("upload.job.progress")}>
                <span style={{ width: `${progress}%` }} />
              </div>
            </div>
            <div className="upload-job__metrics">
              <Metric label={t("upload.job.metrics.files")} value={`${formatNumber(job.summary.succeededFiles)}/${formatNumber(job.summary.totalFiles)}`} />
              <Metric label={t("upload.job.metrics.rows")} value={`${formatNumber(job.summary.processedRows)}/${formatNumber(job.summary.totalRows)}`} />
              <Metric label={t("upload.job.metrics.accepted")} value={formatNumber(job.summary.acceptedRows)} />
              <Metric label={t("upload.job.metrics.failures")} value={formatNumber(job.summary.failedFiles)} danger={job.summary.failedFiles > 0} />
            </div>
            {job.errorMessage ? <div className="error-banner" role="alert">{job.errorMessage}</div> : null}
          </div>
        </div>
        <JobFileTable files={detail.files} />
        <JobEvents events={detail.events} />
      </section>
      {retryReviewOpen ? (
        <RetryConfirmationModal
          detail={detail}
          pending={retryPending}
          onCancel={() => setRetryReviewOpen(false)}
          onConfirm={(approval) => {
            onRetry(approval);
            setRetryReviewOpen(false);
          }}
        />
      ) : null}
    </>
  );
}

function RetryConfirmationModal({
  detail,
  pending,
  onCancel,
  onConfirm,
}: {
  detail: UploadJobDetail;
  pending: boolean;
  onCancel: () => void;
  onConfirm: (approval: { expectedRemainingRows: number; expectedRetryFiles: number }) => void;
}) {
  const { t } = useTranslation();
  const [typedRows, setTypedRows] = useState("");
  const breakdown = buildRetryGateBreakdown(detail);
  const confirmationRows = String(breakdown.remainingPhysicalRows);
  const formattedRemainingRows = formatNumber(breakdown.remainingPhysicalRows);
  const confirmAllowed = breakdown.retryFiles > 0 && breakdown.remainingPhysicalRows > 0 && typedRows.trim() === confirmationRows;
  const blockedReasons = [
    breakdown.retryFiles <= 0 ? t("upload.retryReview.blocked.noRetryFiles") : null,
    breakdown.remainingPhysicalRows <= 0 ? t("upload.retryReview.blocked.noRows") : null,
  ].filter((reason): reason is string => Boolean(reason));
  const unavailable = t("upload.retryReview.unavailable");
  const countItems: Array<{ id: string; label: string; value: string | number }> = [
    { id: "jobId", label: t("upload.retryReview.jobId"), value: detail.job.jobId },
    { id: "retryFiles", label: t("upload.retryReview.retryFiles"), value: breakdown.retryFiles },
    { id: "physicalRows", label: t("upload.retryReview.physicalRows"), value: formatNumber(breakdown.physicalRows) },
    { id: "uniqueUploadKeys", label: t("upload.retryReview.uniqueUploadKeys"), value: unavailable },
    { id: "duplicateKeyCount", label: t("upload.retryReview.duplicateKeyCount"), value: unavailable },
    { id: "dbMatchedKeys", label: t("upload.retryReview.dbMatchedKeys"), value: unavailable },
    { id: "resumeOffsetRows", label: t("upload.retryReview.resumeOffsetRows"), value: formatNumber(breakdown.resumeOffsetRows) },
    { id: "remainingPhysicalRows", label: t("upload.retryReview.remainingPhysicalRows"), value: formattedRemainingRows },
    { id: "expectedUploadRows", label: t("upload.retryReview.expectedUploadRows"), value: unavailable },
    { id: "acceptedRows", label: t("upload.retryReview.acceptedRows"), value: formatNumber(breakdown.acceptedRows) },
  ];

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-labelledby="retry-upload-review-title"
        aria-modal="true"
        className="start-upload-modal"
        role="dialog"
      >
        <div className="start-upload-modal__header">
          <div>
            <span className="panel-eyebrow">{t("upload.retryReview.eyebrow")}</span>
            <h2 id="retry-upload-review-title">{t("upload.retryReview.title")}</h2>
          </div>
          <StatusBadge tone={confirmAllowed ? "attention" : "blocked"} label={t("upload.retryReview.badge")} />
        </div>

        <div className="start-upload-modal__warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <span>{t("upload.retryReview.warning", { rowsFormatted: formattedRemainingRows })}</span>
        </div>

        <dl className="start-upload-modal__counts">
          {countItems.map(({ id, label, value }) => (
            <div className="start-upload-modal__count" key={id}>
              <dt>{label}</dt>
              <dd className="num">{value}</dd>
            </div>
          ))}
        </dl>

        <p className="start-upload-modal__note">
          {t("upload.retryReview.countSemantics")}
        </p>

        {blockedReasons.length > 0 ? (
          <div className="start-upload-modal__blocked" role="alert">
            <strong>{t("upload.retryReview.blocked.title")}</strong>
            <ul>
              {blockedReasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <label className="start-upload-modal__input">
          <span>{t("upload.retryReview.inputLabel", { rows: confirmationRows })}</span>
          <input
            autoComplete="off"
            inputMode="numeric"
            pattern="[0-9]*"
            value={typedRows}
            onChange={(event) => setTypedRows(event.target.value.replace(/[^\d]/g, ""))}
            placeholder={confirmationRows}
          />
        </label>

        <div className="start-upload-modal__actions">
          <button className="button button--secondary" type="button" onClick={onCancel}>
            {t("upload.retryReview.cancel")}
          </button>
          <button
            className="button button--danger"
            type="button"
            disabled={!confirmAllowed || pending}
            onClick={() => onConfirm({
              expectedRemainingRows: breakdown.remainingPhysicalRows,
              expectedRetryFiles: breakdown.retryFiles,
            })}
          >
            {pending ? t("upload.retryReview.pending") : t("upload.retryReview.confirm", { rowsFormatted: formattedRemainingRows })}
          </button>
        </div>
      </section>
    </div>
  );
}

function formatOperatorError(error: Error, fallback: string): string {
  if (isLocalTokenApiError(error)) return error.message;
  return fallback;
}

function Metric({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="upload-job__metric">
      <span>{label}</span>
      <strong className={danger ? "num num--danger" : "num"}>{value}</strong>
    </div>
  );
}

function JobFileTable({ files }: { files: UploadJobDetail["files"] }) {
  const { t } = useTranslation();
  if (files.length === 0) return <section className="panel panel--loading">{t("upload.job.emptyFiles")}</section>;
  return (
    <section className="panel">
      <div className="panel__header">
        <h2>{t("upload.job.filesTitle")}</h2>
      </div>
      <div className="table-scroll">
        <table className="data-table data-table--job-files">
          <thead>
            <tr>
              <th>{t("upload.job.table.status")}</th>
              <th>{t("upload.job.table.filename")}</th>
              <th>{t("upload.job.table.kind")}</th>
              <th>{t("upload.job.table.progress")}</th>
              <th>{t("upload.job.table.rows")}</th>
              <th>{t("upload.job.table.uploaded")}</th>
              <th>{t("upload.job.table.accepted")}</th>
              <th>{t("upload.job.table.resume")}</th>
              <th>{t("upload.job.table.retry")}</th>
              <th>{t("upload.job.table.error")}</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => {
              const fileProgress = file.rowCount ? Math.min(100, Math.round((file.processedRows / file.rowCount) * 100)) : 0;
              return (
                <tr className={`row--${fileTone[file.status]}`} key={file.jobFileId}>
                  <td><StatusBadge tone={fileTone[file.status]} label={t(`upload.job.fileStatus.${file.status}`)} /></td>
                  <td className="preview-file-cell"><strong>{file.filename}</strong><span>{file.folderLabel}</span></td>
                  <td>{t(`upload.kind.${file.kind}`, { defaultValue: file.kind })}</td>
                  <td>
                    <div className="mini-progress"><span style={{ width: `${fileProgress}%` }} /></div>
                  </td>
                  <td className="num">{formatNumber(file.processedRows)} / {formatNumber(file.rowCount)}</td>
                  <td className="num">{formatNumber(file.uploadedRows)}</td>
                  <td className="num">{formatNumber(file.acceptedRows)}</td>
                  <td className="num">{formatNumber(file.resumeOffset)}</td>
                  <td className="num">{formatNumber(file.retryCount)}</td>
                  <td className="preview-reason">{file.lastErrorMessage ?? "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function JobEvents({ events }: { events: JobEvent[] }) {
  const { t } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));
  return (
    <section className="panel">
      <div className="panel__header">
        <h2>{t("upload.job.eventsTitle")}</h2>
      </div>
      <div className="job-log-viewer" role="log" aria-live="polite">
        {events.length === 0 ? (
          <div className="job-log-line job-log-line--muted">{t("upload.job.emptyEvents")}</div>
        ) : events.map((event) => (
          <div className={`job-log-line job-log-line--${event.level}`} key={event.seq}>
            <span className="job-log-line__time">{formatDateTime(event.ts)}</span>
            <span className="job-log-line__level">{event.level}</span>
            <span className="job-log-line__type">{event.eventType}</span>
            <span className="job-log-line__message">{localizeJobEvent(event, translate)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
