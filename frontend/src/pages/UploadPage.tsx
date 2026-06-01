import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Ban, Database, FileSearch, Play, Search } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  cancelUploadPreview,
  createDefaultPreviewRequest,
  createUploadPreview,
  fetchLatestUploadPreview,
  fetchUploadPreview,
  type PreviewItem,
  type PreviewItemStatus,
  type PreviewQueryParams,
  type PreviewRangeMode,
  type PreviewResponse,
  type PreviewRunStatus,
  type PreviewSortKey,
} from "../api/uploadPreview";
import { StatusBadge } from "../components/status/StatusBadge";
import type { StatusTone } from "./dashboard/dashboardTypes";
import { getMockUploadPreview } from "./upload/mockUploadPreview";

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

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat().format(value);
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return value.replace("T", " ").replace(/\.\d+/, "").replace("+09:00", "");
}

function mockRunId() {
  return `mock_${Date.now()}`;
}

export function UploadPage() {
  const { i18n, t } = useTranslation();
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

  const latestQuery = useQuery({
    queryKey: ["upload-preview", "latest", queryParams],
    enabled: activeTab === "preview" && !previewRunId && API_MODE,
    queryFn: () => fetchLatestUploadPreview(queryParams),
    retry: false,
  });

  const previewQuery = useQuery({
    queryKey: ["upload-preview", previewRunId, mockStartedAt, mockCancelled, queryParams, i18n.language],
    enabled: activeTab === "preview" && Boolean(previewRunId),
    queryFn: async () => {
      if (!previewRunId) return null;
      if (!API_MODE) {
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

  const currentPreview = previewQuery.data ?? latestQuery.data ?? null;

  const createMutation = useMutation({
    mutationFn: async () => {
      const request = createDefaultPreviewRequest(
        rangeMode,
        rangeMode === "custom" ? startDate || null : null,
        rangeMode === "custom" ? endDate || null : null,
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
  });

  const cancelMutation = useMutation({
    mutationFn: async () => {
      if (!previewRunId) throw new Error("No preview run");
      if (!API_MODE) return { previewRunId, status: "cancelled" as const, pollUrl: "" };
      return cancelUploadPreview(previewRunId);
    },
    onSuccess: () => {
      if (!API_MODE) setMockCancelled(true);
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
          loading={previewQuery.isLoading || latestQuery.isLoading || createMutation.isPending}
          error={previewQuery.error ?? latestQuery.error ?? createMutation.error}
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
          cancelling={cancelMutation.isPending}
          onRangeModeChange={setRangeMode}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          onRunPreview={() => createMutation.mutate()}
          onCancel={() => cancelMutation.mutate()}
          onStatusFilterChange={setStatusFilter}
          onSearchChange={setSearch}
          onSortChange={setSort}
        />
      ) : (
        <JobPlaceholder />
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
  cancelling: boolean;
  onRangeModeChange: (value: PreviewRangeMode) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onRunPreview: () => void;
  onCancel: () => void;
  onStatusFilterChange: (value: PreviewItemStatus | "all") => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: PreviewSortKey) => void;
}

function PreviewTab(props: PreviewTabProps) {
  const { t } = useTranslation();
  const run = props.currentPreview?.run;
  const summary = run?.summary;
  const dbWarning = run?.dbStatus === "unreachable" || run?.status === "partial_failed";

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
            <button className="button button--primary" type="button" onClick={props.onRunPreview}>
              <FileSearch size={16} aria-hidden="true" />
              {t("upload.actions.runPreview")}
            </button>
            <button
              className="button button--secondary"
              type="button"
              disabled
              title={t("upload.actions.startUploadDisabledReason")}
              aria-label={t("upload.actions.startUploadDisabledReason")}
            >
              <Play size={16} aria-hidden="true" />
              {t("upload.actions.startUploadUnavailable")}
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
        </div>
      </div>

      {run ? (
        <div className={`preview-status-strip ${dbWarning ? "preview-status-strip--warning" : ""}`} role={dbWarning ? "alert" : "status"}>
          <StatusBadge tone={runTone[run.status]} label={t(`upload.runStatus.${run.status}`)} />
          <span>{t("upload.preview.runId")}: <code>{run.previewRunId}</code></span>
          <span>{t("upload.preview.db")}: {t(`upload.dbStatus.${run.dbStatus}`)}</span>
          <span>{t("upload.preview.updated")}: {formatDateTime(run.finishedAt ?? run.startedAt ?? run.requestedAt)}</span>
          {run.errorMessage ? <strong>{run.errorMessage}</strong> : null}
        </div>
      ) : null}

      {summary ? <PreviewSummaryStrip summary={summary} /> : null}

      {props.error ? (
        <div className="error-banner" role="alert">
          {t("upload.preview.error")}
        </div>
      ) : null}

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
          <PreviewTable items={props.currentPreview.items} />
        ) : (
          <div className="upload-empty">
            <FileSearch aria-hidden="true" />
            <strong>{t("upload.empty.title")}</strong>
            <span>{t("upload.empty.detail")}</span>
          </div>
        )}
      </div>
    </section>
  );
}

function PreviewSummaryStrip({ summary }: { summary: PreviewResponse["run"]["summary"] }) {
  const { t } = useTranslation();
  const items: Array<[PreviewItemStatus, number]> = [
    ["target", summary.target],
    ["already_in_db", summary.alreadyInDb],
    ["partial_overlap", summary.partialOverlap],
    ["risky", summary.risky],
    ["excluded", summary.excluded],
  ];
  return (
    <div className="preview-summary-strip">
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
    </div>
  );
}

function PreviewTable({ items }: { items: PreviewItem[] }) {
  const { t } = useTranslation();
  if (items.length === 0) {
    return <div className="panel--loading">{t("upload.empty.noRows")}</div>;
  }
  return (
    <div className="table-scroll">
      <table className="data-table data-table--preview">
        <thead>
          <tr>
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
                {t(`upload.reason.${item.reasonCode}`, { defaultValue: item.reasonText })}
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

function JobPlaceholder() {
  const { t } = useTranslation();
  return (
    <section className="panel placeholder-panel">
      <div className="panel__header">
        <h2>{t("upload.job.title")}</h2>
      </div>
      <p>{t("upload.job.placeholder")}</p>
    </section>
  );
}
