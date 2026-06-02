import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useTranslation } from "react-i18next";

import { fetchAuditLogs, type AuditLog, type AuditLogListResponse, type AuditQuery, type AuditResult } from "../api/audit";
import { fetchLatestUploadJob, type JobEvent } from "../api/uploadJobs";
import { StatusBadge } from "../components/status/StatusBadge";
import type { StatusTone } from "./dashboard/dashboardTypes";

const API_MODE = import.meta.env.VITE_API_MODE === "api";

type LogsTab = "job" | "audit";
type RecentWindow = "all" | "24h" | "7d" | "30d";

const resultTone: Record<AuditResult, StatusTone> = {
  success: "ready",
  failure: "failed",
  cancelled: "attention",
  blocked: "blocked",
};

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return value.replace("T", " ").replace(/\.\d+/, "").replace("+09:00", "");
}

function recentWindowStart(window: RecentWindow): string | undefined {
  if (window === "all") return undefined;
  const hours = window === "24h" ? 24 : window === "7d" ? 24 * 7 : 24 * 30;
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

function clean(value: string) {
  return value.trim() || undefined;
}

function mockAuditLogs(query: AuditQuery, language: string): AuditLogListResponse {
  const now = new Date();
  const items: AuditLog[] = [
    {
      auditId: 3,
      ts: now.toISOString(),
      actor: "local_operator",
      action: "runtime.start",
      targetType: "local_supabase",
      targetId: "Extrusion_data",
      params: { operationId: "mock_runtime_start" },
      result: "success",
      errorCode: null,
      errorMessage: null,
      jobId: null,
      requestId: "mock_req_runtime",
      createdAt: now.toISOString(),
    },
    {
      auditId: 2,
      ts: new Date(now.getTime() - 12 * 60 * 1000).toISOString(),
      actor: "local_operator",
      action: "upload.start",
      targetType: "upload_job",
      targetId: "mock_upload_job",
      params: { previewRunId: "mock_preview", mode: "preview_targets" },
      result: "blocked",
      errorCode: "active_upload_job",
      errorMessage: language === "ko" ? "진행 중인 업로드 작업이 있습니다." : "An upload job is already active.",
      jobId: "mock_upload_job",
      requestId: "mock_req_upload",
      createdAt: new Date(now.getTime() - 12 * 60 * 1000).toISOString(),
    },
    {
      auditId: 1,
      ts: new Date(now.getTime() - 35 * 60 * 1000).toISOString(),
      actor: "local_operator",
      action: "upload.retry",
      targetType: "upload_job",
      targetId: "mock_retry_job",
      params: { includeInterrupted: true, token: "[redacted]" },
      result: "failure",
      errorCode: "edge_function_unreachable",
      errorMessage: language === "ko" ? "Edge Function에 연결할 수 없습니다." : "Edge Function is unreachable.",
      jobId: "mock_retry_job",
      requestId: "mock_req_retry",
      createdAt: new Date(now.getTime() - 35 * 60 * 1000).toISOString(),
    },
  ];
  const filtered = items.filter((item) => {
    if (query.result && item.result !== query.result) return false;
    if (query.action && item.action !== query.action) return false;
    if (query.jobId && item.jobId !== query.jobId) return false;
    if (query.requestId && item.requestId !== query.requestId) return false;
    if (query.q) {
      const haystack = [item.action, item.targetType, item.targetId, item.jobId, item.requestId, item.errorCode, item.errorMessage]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(query.q.toLowerCase())) return false;
    }
    return true;
  });
  const limit = query.limit ?? 50;
  const offset = query.offset ?? 0;
  return {
    items: filtered.slice(offset, offset + limit),
    page: {
      limit,
      offset,
      totalItems: filtered.length,
      hasNext: offset + limit < filtered.length,
      hasPrevious: offset > 0,
    },
    filters: query,
  };
}

export function LogsPage() {
  const { i18n, t } = useTranslation();
  const [activeTab, setActiveTab] = useState<LogsTab>("job");
  const [recentWindow, setRecentWindow] = useState<RecentWindow>("7d");
  const [result, setResult] = useState<AuditResult | "all">("all");
  const [action, setAction] = useState("");
  const [jobId, setJobId] = useState("");
  const [requestId, setRequestId] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(50);

  const auditQuery: AuditQuery = useMemo(
    () => ({
      fromTs: recentWindowStart(recentWindow),
      result: result === "all" ? undefined : result,
      action: clean(action),
      jobId: clean(jobId),
      requestId: clean(requestId),
      q: clean(search),
      limit,
      offset,
      sort: "ts",
      order: "desc",
    }),
    [action, jobId, limit, offset, recentWindow, requestId, result, search],
  );

  const auditLogs = useQuery({
    queryKey: ["audit-logs", auditQuery, i18n.language],
    enabled: activeTab === "audit",
    queryFn: async () => {
      if (!API_MODE) return mockAuditLogs(auditQuery, i18n.language);
      return fetchAuditLogs(auditQuery);
    },
    retry: false,
  });

  const latestJob = useQuery({
    queryKey: ["logs", "latest-job"],
    enabled: activeTab === "job" && API_MODE,
    queryFn: fetchLatestUploadJob,
    retry: false,
  });

  function resetFilters() {
    setRecentWindow("7d");
    setResult("all");
    setAction("");
    setJobId("");
    setRequestId("");
    setSearch("");
    setOffset(0);
  }

  function updateFilter(update: () => void) {
    update();
    setOffset(0);
  }

  return (
    <main className="page page--logs">
      <section className="upload-tabs" aria-label={t("logs.tabs.label")}>
        <button
          type="button"
          className={`tab ${activeTab === "job" ? "tab--active" : ""}`}
          onClick={() => setActiveTab("job")}
        >
          {t("logs.tabs.jobLogs")}
        </button>
        <button
          type="button"
          className={`tab ${activeTab === "audit" ? "tab--active" : ""}`}
          onClick={() => setActiveTab("audit")}
        >
          {t("logs.tabs.auditLogs")}
        </button>
      </section>
      {activeTab === "job" ? (
        <JobLogsPanel
          events={latestJob.data?.events ?? []}
          isLoading={latestJob.isLoading}
          isError={latestJob.isError}
          showMock={!API_MODE}
        />
      ) : (
        <AuditLogsPanel
          action={action}
          auditLogs={auditLogs.data ?? null}
          isError={auditLogs.isError}
          isLoading={auditLogs.isLoading}
          jobId={jobId}
          limit={limit}
          offset={offset}
          recentWindow={recentWindow}
          requestId={requestId}
          result={result}
          search={search}
          onActionChange={(value) => updateFilter(() => setAction(value))}
          onClear={resetFilters}
          onJobIdChange={(value) => updateFilter(() => setJobId(value))}
          onLimitChange={(value) => updateFilter(() => setLimit(value))}
          onNext={() => setOffset((value) => value + limit)}
          onPrevious={() => setOffset((value) => Math.max(0, value - limit))}
          onRecentWindowChange={(value) => updateFilter(() => setRecentWindow(value))}
          onRequestIdChange={(value) => updateFilter(() => setRequestId(value))}
          onResultChange={(value) => updateFilter(() => setResult(value))}
          onSearchChange={(value) => updateFilter(() => setSearch(value))}
        />
      )}
    </main>
  );
}

interface JobLogsPanelProps {
  events: JobEvent[];
  isLoading: boolean;
  isError: boolean;
  showMock: boolean;
}

function JobLogsPanel({ events, isError, isLoading, showMock }: JobLogsPanelProps) {
  const { t } = useTranslation();
  const visibleEvents = showMock
    ? [
        {
          seq: 1,
          ts: new Date().toISOString(),
          level: "info",
          eventType: "job.log.mock",
          message: t("logs.job.mockMessage"),
        },
      ]
    : events;

  return (
    <section className="panel logs-panel" aria-labelledby="job-logs-title">
      <div className="panel__header">
        <div>
          <h2 id="job-logs-title">{t("logs.job.title")}</h2>
          <p className="panel-subtitle">{t("logs.job.subtitle")}</p>
        </div>
      </div>
      {isLoading ? <div className="panel--loading">{t("logs.job.loading")}</div> : null}
      {isError ? <div className="panel--error" role="alert">{t("logs.job.error")}</div> : null}
      {!isLoading && !isError ? (
        <div className="job-log-viewer" role="log" aria-live="polite">
          {visibleEvents.length === 0 ? (
            <div className="job-log-line job-log-line--muted">{t("logs.job.empty")}</div>
          ) : (
            visibleEvents.map((event) => (
              <div className={`job-log-line job-log-line--${event.level}`} key={event.seq}>
                <span className="job-log-line__time">{formatDateTime(event.ts)}</span>
                <span className="job-log-line__level">{event.level}</span>
                <span className="job-log-line__type">{event.eventType}</span>
                <span className="job-log-line__message">{event.message}</span>
              </div>
            ))
          )}
        </div>
      ) : null}
    </section>
  );
}

interface AuditLogsPanelProps {
  action: string;
  auditLogs: AuditLogListResponse | null;
  isError: boolean;
  isLoading: boolean;
  jobId: string;
  limit: number;
  offset: number;
  recentWindow: RecentWindow;
  requestId: string;
  result: AuditResult | "all";
  search: string;
  onActionChange: (value: string) => void;
  onClear: () => void;
  onJobIdChange: (value: string) => void;
  onLimitChange: (value: number) => void;
  onNext: () => void;
  onPrevious: () => void;
  onRecentWindowChange: (value: RecentWindow) => void;
  onRequestIdChange: (value: string) => void;
  onResultChange: (value: AuditResult | "all") => void;
  onSearchChange: (value: string) => void;
}

function AuditLogsPanel(props: AuditLogsPanelProps) {
  const { t } = useTranslation();
  const items = props.auditLogs?.items ?? [];
  const page = props.auditLogs?.page;

  return (
    <section className="panel logs-panel" aria-labelledby="audit-logs-title">
      <div className="panel__header">
        <div>
          <h2 id="audit-logs-title">{t("logs.audit.title")}</h2>
          <p className="panel-subtitle">{t("logs.audit.subtitle")}</p>
        </div>
      </div>
      <div className="audit-toolbar">
        <label>
          {t("logs.audit.filters.dateRange")}
          <select value={props.recentWindow} onChange={(event) => props.onRecentWindowChange(event.target.value as RecentWindow)}>
            <option value="24h">{t("logs.audit.recent.24h")}</option>
            <option value="7d">{t("logs.audit.recent.7d")}</option>
            <option value="30d">{t("logs.audit.recent.30d")}</option>
            <option value="all">{t("logs.audit.recent.all")}</option>
          </select>
        </label>
        <label>
          {t("logs.audit.filters.result")}
          <select value={props.result} onChange={(event) => props.onResultChange(event.target.value as AuditResult | "all")}>
            <option value="all">{t("logs.audit.results.all")}</option>
            <option value="success">{t("logs.audit.results.success")}</option>
            <option value="failure">{t("logs.audit.results.failure")}</option>
            <option value="blocked">{t("logs.audit.results.blocked")}</option>
            <option value="cancelled">{t("logs.audit.results.cancelled")}</option>
          </select>
        </label>
        <label>
          {t("logs.audit.filters.action")}
          <input value={props.action} onChange={(event) => props.onActionChange(event.target.value)} placeholder="upload.start" />
        </label>
        <label>
          {t("logs.audit.filters.jobId")}
          <input value={props.jobId} onChange={(event) => props.onJobIdChange(event.target.value)} placeholder="upl_..." />
        </label>
        <label>
          {t("logs.audit.filters.requestId")}
          <input value={props.requestId} onChange={(event) => props.onRequestIdChange(event.target.value)} placeholder="req_..." />
        </label>
        <label className="audit-search">
          {t("logs.audit.filters.search")}
          <span>
            <Search aria-hidden="true" size={16} />
            <input value={props.search} onChange={(event) => props.onSearchChange(event.target.value)} placeholder={t("logs.audit.filters.searchPlaceholder")} />
          </span>
        </label>
        <button className="button button--secondary" type="button" onClick={props.onClear}>
          {t("logs.audit.filters.clear")}
        </button>
      </div>
      <div className="audit-summary-strip">
        <span>{t("logs.audit.summary.total")}: <strong>{page?.totalItems ?? 0}</strong></span>
        <span>{t("logs.audit.summary.window")}: <strong>{t(`logs.audit.recent.${props.recentWindow}`)}</strong></span>
        <span>{t("logs.audit.summary.page")}: <strong>{Math.floor((page?.offset ?? 0) / (page?.limit ?? 1)) + 1}</strong></span>
      </div>
      {props.isLoading ? <div className="panel--loading">{t("logs.audit.loading")}</div> : null}
      {props.isError ? <div className="panel--error" role="alert">{t("logs.audit.error")}</div> : null}
      {!props.isLoading && !props.isError ? (
        <>
          <AuditTable items={items} />
          <div className="audit-pagination">
            <label>
              {t("logs.audit.pagination.limit")}
              <select value={props.limit} onChange={(event) => props.onLimitChange(Number(event.target.value))}>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </label>
            <button className="button button--secondary" type="button" disabled={!page?.hasPrevious} onClick={props.onPrevious}>
              {t("logs.audit.pagination.previous")}
            </button>
            <button className="button button--secondary" type="button" disabled={!page?.hasNext} onClick={props.onNext}>
              {t("logs.audit.pagination.next")}
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}

function AuditTable({ items }: { items: AuditLog[] }) {
  const { t } = useTranslation();
  if (items.length === 0) return <div className="audit-empty">{t("logs.audit.empty")}</div>;
  return (
    <div className="table-scroll">
      <table className="data-table data-table--audit-logs">
        <thead>
          <tr>
            <th>{t("logs.audit.columns.time")}</th>
            <th>{t("logs.audit.columns.result")}</th>
            <th>{t("logs.audit.columns.action")}</th>
            <th>{t("logs.audit.columns.target")}</th>
            <th>{t("logs.audit.columns.actor")}</th>
            <th>{t("logs.audit.columns.jobId")}</th>
            <th>{t("logs.audit.columns.params")}</th>
            <th>{t("logs.audit.columns.error")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr className={`row--${resultTone[item.result]}`} key={item.auditId}>
              <td className="num">{formatDateTime(item.ts)}</td>
              <td><StatusBadge tone={resultTone[item.result]} label={t(`logs.audit.results.${item.result}`)} /></td>
              <td className="mono-cell">{item.action}</td>
              <td>
                <span className="audit-target">{item.targetType}</span>
                <small>{item.targetId ?? "-"}</small>
              </td>
              <td>{item.actor}</td>
              <td className="mono-cell">{item.jobId ?? "-"}</td>
              <td><ParamChips params={item.params} /></td>
              <td>
                <span className={item.errorCode ? "audit-error-code" : "muted"}>{item.errorCode ?? "-"}</span>
                {item.errorMessage ? <small>{item.errorMessage}</small> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ParamChips({ params }: { params: Record<string, unknown> }) {
  const entries = Object.entries(params);
  if (entries.length === 0) return <span className="muted">-</span>;
  const visible = entries.slice(0, 3);
  const hiddenCount = entries.length - visible.length;
  return (
    <span className="param-chip-list">
      {visible.map(([key, value]) => (
        <span className={`param-chip ${value === "[redacted]" ? "param-chip--redacted" : ""}`} key={key}>
          {key}: {String(value)}
        </span>
      ))}
      {hiddenCount > 0 ? <span className="param-chip">+{hiddenCount}</span> : null}
    </span>
  );
}
