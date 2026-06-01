# Dashboard Implementation Spec

This document finalizes the React/Vite implementation specification for the selected Figma Dashboard Variant D.

Variant D direction: **Data Table-Oriented Console**.

This is not an app implementation. It is the screen contract that lets a frontend implementer build the Dashboard with mock data first, then wire it to the backend APIs defined in `docs/02_engineering_plan.md`.

## Implementation Status

Status on branch `codex/web-console-scaffold` after commit `95ec996`:

- Implemented: React + Vite + TypeScript frontend scaffold.
- Implemented: FastAPI backend scaffold.
- Implemented: Dashboard Variant D mock UI using the component structure in this document.
- Implemented: App shell with Sidebar, Topbar, Dashboard content area, and placeholder pages for Upload, Logs, and Settings.
- Implemented: Sidebar navigation limited to Dashboard, Upload, Logs, Settings.
- Implemented: TanStack Query Dashboard query with mock-first behavior.
- Implemented: frontend mock state switching via `?state=ready|attention|blocked|running`.
- Implemented: Korean/English i18n baseline with persisted language selection in `localStorage`.
- Implemented: backend mock endpoints `/api/health`, `/api/dashboard`, and `/api/dashboard/summary`.
- Implemented: backend tests for health and Dashboard mock contracts.

Not implemented in this scaffold:

- Real upload jobs.
- Real local Supabase start/stop/status probing.
- Real Grafana health probing beyond mock display/link behavior.
- Audit log persistence.
- SSE progress/log streaming.
- Legacy `core/*` extraction.
- Double-click launcher.

Verified after implementation:

- `npm run typecheck`
- `npm run build`
- `.\.venv\Scripts\python -m pytest tests\backend`
- Browser QA for `ready`, `attention`, `blocked`, and `running` states.
- Responsive QA at `1440x900`, `1366x768`, `1024x768`, and `720x900`.

Known scaffold limitations:

- `?state=ready|attention|blocked|running` applies to the frontend mock data path. In `VITE_API_MODE="api"`, the backend mock currently returns the running Dashboard payload.
- On `codex/web-console-scaffold`, Upload, Logs, and Settings were placeholder pages.
- On `codex/upload-preview-reconciliation`, Upload Preview reconciliation and the Preview tab UI are implemented. Upload Job, Logs, and Settings remain placeholders.
- Dashboard actions are visual/non-mutating shortcuts in the scaffold. They do not start uploads or runtime operations.
- At `720px` width, the safety banner may exceed the desktop `72-96px` target because Korean/English text wraps for readability.

Current branch update:

- Implemented after this Dashboard spec: Upload Preview API, SQLite `preview_runs` / `preview_items`, local CSV candidate scanning, row-streamed exact-key extraction, chunked DB matching, Supabase exact reconciliation, DB unreachable handling, Upload Preview UI, polling, mock data, and Korean/English Upload Preview i18n. See `docs/07_upload_preview_plan.md`.
- Still not implemented: real upload job execution, Retry Failed execution, SSE progress/log streaming, local Supabase start/stop/status controls, audit log persistence, and launcher integration.

## Source Of Truth

- Product scope: `docs/00_product_scope.md`
- Engineering plan: `docs/02_engineering_plan.md`
- UI/UX plan: `docs/03_ui_ux_plan.md`
- Design system: `docs/04_design_system.md`
- Dashboard design review: `docs/05_dashboard_design_review.md`
- Prior Variant D HTML spec: `docs/06_dashboard_variant_d_html_spec.md`
- Figma file: [Extrusion Web Console Dashboard Design Shotgun](https://www.figma.com/design/xuI1kMSJs44UQGIO87pG7R)

`docs/04_design_system.md` is the primary implementation reference. `DESIGN.md` remains a broad visual reference only.

## Product Frame

Dashboard's job is to answer this in the first viewport:

> Is upload, database, and runtime state safe right now?

Variant D answers with compact status cells and first-class tables instead of large cards. It should feel like a factory operations console, not a SaaS landing page.

## Non-Negotiable Decisions

- Light-first theme only.
- Localhost-only local web app.
- Grafana is status/link only, never iframe.
- Sidebar navigation is exactly: Dashboard, Upload, Logs, Settings.
- No v1-excluded navigation: Data Mgmt, Supabase delete UI, Cycle Ops, Training Dataset Builder, Work Log.
- Status is always icon + label + color.
- Tables are primary surfaces.
- All background failures are visible in Dashboard, Logs, and Audit Logs.
- Korean UI text is the baseline for layout fit.

## Layout Grid

### App Shell

```text
+----------------------+-----------------------------------------------+
| Sidebar 220px       | Topbar 52px                                   |
|                     +-----------------------------------------------+
|                     | Dashboard content                             |
|                     | padding 20px desktop                          |
+----------------------+-----------------------------------------------+
```

CSS structure:

```css
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  grid-template-rows: var(--topbar-height) minmax(0, 1fr);
  background: var(--color-bg);
}

.sidebar {
  grid-column: 1;
  grid-row: 1 / span 2;
}

.topbar {
  grid-column: 2;
  grid-row: 1;
}

.dashboard-page {
  grid-column: 2;
  grid-row: 2;
  min-width: 0;
  overflow: auto;
  padding: var(--space-5);
}
```

### Dashboard Content Order

```text
1. SafetySummaryBanner, full width, 72-96px
2. DashboardStatusMatrix, full width, compact status cells
3. RecentJobsPanel, full width table
4. LowerGrid:
   - RuntimeCheckPanel
   - WarningQueuePanel
   - AuditSummaryPanel
```

Desktop CSS:

```css
.dashboard-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-4);
}

.dashboard-status-matrix {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-3);
}

.dashboard-lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-4);
}

.audit-summary-panel {
  grid-column: 1 / -1;
}
```

## Responsive Breakpoints

Use the breakpoints from `docs/04_design_system.md`.

| Width | Behavior |
|-------|----------|
| `>= 1200px` | Full desktop shell. Sidebar 220px. Five status cells in one row. Recent jobs full width. Lower grid two columns. |
| `1024-1199px` | Sidebar remains if space allows. Status matrix becomes 3 columns then 2 columns. Recent jobs remains table with horizontal scroll if needed. |
| `< 900px` | Sidebar collapses to icon rail. Topbar status chips may collapse into a compact status summary button or horizontally scroll. |
| `< 720px` | Nav becomes top tabs. Tables keep real table markup inside horizontal scroll containers. Do not convert critical tables into cards for v1. |
| `375px` | Readable status and logs only. Bulk table review is horizontally scrollable. Primary status and latest failure must remain visible. |

First viewport requirement:

- At `1366x768`, SafetySummaryBanner and DashboardStatusMatrix must fit without scrolling.
- At least the RecentJobsPanel header and first table rows should be visible.
- Do not reduce table row height below `36px` to force fit.
- Tune the first viewport for operator PCs: safety banner `80-88px`, status cells `88-104px`, vertical gaps `12-16px`, and at least 3 recent job rows visible at `1366x768`.
- Minimum table content widths: Recent Jobs `760px`, Runtime/Warning `560px`, Audit `720px`. Below available width, wrap each table in horizontal overflow instead of reshaping rows into cards.

## Component Hierarchy

```tsx
<AppShell>
  <SidebarNav activePage="dashboard" />
  <TopStatusBar titleKey="dashboard.title">
    <StatusChipGroup chips={data.topbarChips} />
  </TopStatusBar>

  <DashboardPage>
    <SafetySummaryBanner overall={data.overall} />
    <DashboardStatusMatrix items={data.statusMatrix} />
    <RecentJobsPanel jobs={data.recentJobs} currentJob={data.currentJob} />

    <DashboardLowerGrid>
      <RuntimeCheckPanel rows={data.runtimeChecks} />
      <WarningQueuePanel rows={data.warningQueue} />
      <AuditSummaryPanel rows={data.auditSummary} />
    </DashboardLowerGrid>
  </DashboardPage>
</AppShell>
```

Recommended file names after React scaffold exists:

```text
frontend/src/pages/DashboardPage.tsx
frontend/src/pages/dashboard/mockDashboardData.ts
frontend/src/pages/dashboard/dashboardTypes.ts
frontend/src/pages/dashboard/dashboardQuery.ts
frontend/src/api/dashboard.ts
frontend/src/mocks/dashboard.ts
frontend/src/components/app/AppShell.tsx
frontend/src/components/app/SidebarNav.tsx
frontend/src/components/app/TopStatusBar.tsx
frontend/src/components/status/StatusChipGroup.tsx
frontend/src/components/status/StatusBadge.tsx
frontend/src/components/dashboard/SafetySummaryBanner.tsx
frontend/src/components/dashboard/DashboardStatusMatrix.tsx
frontend/src/components/dashboard/RecentJobsPanel.tsx
frontend/src/components/dashboard/RuntimeCheckPanel.tsx
frontend/src/components/dashboard/WarningQueuePanel.tsx
frontend/src/components/dashboard/AuditSummaryPanel.tsx
```

## Semantic HTML Skeleton

```html
<div class="app-shell">
  <aside class="sidebar" aria-label="Primary navigation">
    <div class="sidebar__brand">
      <span class="sidebar__product">Extrusion</span>
      <span class="sidebar__subtitle">Web Console</span>
    </div>

    <nav class="sidebar__nav">
      <a aria-current="page" href="/dashboard">대시보드</a>
      <a href="/upload">업로드</a>
      <a href="/logs">로그</a>
      <a href="/settings">설정</a>
    </nav>

    <div class="sidebar__meta">
      <span class="status-badge status-badge--ready">localhost</span>
      <button type="button">한국어</button>
      <span>v1 Core Ops</span>
    </div>
  </aside>

  <header class="topbar">
    <div class="topbar__title">
      <h1 id="dashboard-title">대시보드</h1>
      <p>현재: 실행 중인 업로드 1개</p>
    </div>
    <div class="topbar__status" aria-label="System status"></div>
  </header>

  <main class="dashboard-page" aria-labelledby="dashboard-title">
    <section class="safety-summary" aria-live="polite"></section>
    <section class="dashboard-status-matrix" aria-label="Runtime and upload summary"></section>
    <section class="panel recent-jobs-panel" aria-labelledby="recent-jobs-title"></section>
    <section class="dashboard-lower-grid" aria-label="Dashboard detail summaries"></section>
  </main>
</div>
```

## Status Strip Structure

Topbar status strip shows only compact state.

Required chips:

1. Local Supabase.
2. Upload job.
3. Grafana.
4. State Store.

Example:

```tsx
<StatusChipGroup
  chips={[
    { id: "supabase", label: "Supabase", tone: "ready", value: "정상" },
    { id: "upload", label: "업로드", tone: "running", value: "실행 중" },
    { id: "grafana", label: "Grafana", tone: "ready", value: "연결됨" },
    { id: "state_store", label: "State Store", tone: "ready", value: "WAL" },
  ]}
/>
```

Topbar rules:

- Height is fixed at `52px`.
- Background is `--color-surface-raised`.
- Border-bottom is `1px --color-border`.
- It must not become a black Apple-style global nav.

## Dashboard Status Matrix

Variant D's status matrix replaces large decorative cards.

Required cells:

| Cell | Purpose | Example Value |
|------|---------|---------------|
| Upload | current upload state | `12/18 files` |
| Local Supabase | local runtime readiness | `DB + Edge OK` |
| WSL/Storage | WSL/Docker/storage health | `126GB free` |
| Grafana | status/link only | `Open link only` |
| State Store | new SQLite state store health | `WAL ready` |

Each cell:

```tsx
<article className="status-cell">
  <div className="status-cell__label">업로드</div>
  <StatusBadge tone="running">실행 중</StatusBadge>
  <div className="status-cell__value">12/18 files</div>
  <div className="status-cell__detail">실패 0 · ETA 4분</div>
</article>
```

Cell rules:

- Use panel treatment: surface, `1px --color-border`, `8px` radius.
- Keep value text compact, not hero-like.
- Values and numbers use `--font-data`.
- Grafana cell action is link only, no iframe.

## Status Badge Variants

```ts
type StatusTone =
  | "ready"
  | "running"
  | "attention"
  | "risk"
  | "failed"
  | "blocked"
  | "muted";
```

| Tone | Icon | Foreground | Background | Use |
|------|------|------------|------------|-----|
| ready | `CheckCircle` | `--color-ready` | `--color-ready-soft` | safe/complete |
| running | `Activity` | `--color-running` | `--color-running-soft` | active job/runtime |
| attention | `TriangleAlert` | `--color-attention` | `--color-attention-soft` | inspect soon |
| risk | `AlertTriangle` | `--color-risk` | `--color-risk-soft` | risky preview candidate |
| failed | `CircleX` | `--color-danger` | `--color-danger-soft` | operation failed |
| blocked | `OctagonAlert` | `--color-blocked` | `--color-blocked-soft` | action unavailable |
| muted | `Circle` | `--color-muted` | `--color-muted-soft` | inactive/unknown |

Implementation:

```tsx
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Circle,
  CircleX,
  OctagonAlert,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";

const statusIcon: Record<StatusTone, LucideIcon> = {
  ready: CheckCircle,
  running: Activity,
  attention: TriangleAlert,
  risk: AlertTriangle,
  failed: CircleX,
  blocked: OctagonAlert,
  muted: Circle,
};
```

Never use color alone.

## Component Props And Data Types

```ts
type OverallSystemState = "ready" | "attention" | "blocked" | "running";

type UploadJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "pausing"
  | "paused"
  | "cancelling"
  | "cancelled"
  | "interrupted";

interface DashboardResponse {
  overall: OverallState;
  topbarChips: TopbarStatusChip[];
  statusMatrix: StatusMatrixItem[];
  currentJob: CurrentJobSummary | null;
  recentJobs: RecentJobRow[];
  runtimeChecks: RuntimeCheckRow[];
  warningQueue: WarningQueueRow[];
  auditSummary: AuditSummaryRow[];
}

interface OverallState {
  state: OverallSystemState;
  title: string;
  message: string;
  action: DashboardAction | null;
}

type DashboardAction =
  | "preview"
  | "start_upload"
  | "retry_failed"
  | "open_job"
  | "start_supabase"
  | "open_logs";

interface StatusMatrixItem {
  id: "upload" | "supabase" | "storage" | "grafana" | "state_store";
  label: string;
  tone: StatusTone;
  value: string;
  detail: string;
  action?: DashboardLinkAction;
}

interface DashboardLinkAction {
  label: string;
  href?: string;
  target?: "_self" | "_blank";
}

interface TopbarStatusChip {
  id: "supabase" | "upload" | "grafana" | "state_store";
  label: string;
  tone: StatusTone;
  value: string;
}

interface CurrentJobSummary {
  jobId: string;
  status: UploadJobStatus;
  progressPct: number;
  filesDone: number;
  filesTotal: number;
  rowsSent: number;
  startedAt: string;
  latestMessage: string;
}

interface RecentJobRow {
  jobId: string;
  status: UploadJobStatus;
  startedAt: string;
  mode: "upload" | "retry_failed";
  filesDone: number;
  filesTotal: number;
  rowsSent: number;
  failureCount: number;
  warningCount: number;
  latestMessage: string;
}

interface RuntimeCheckRow {
  id: "supabase" | "database" | "edge_function" | "wsl_storage" | "grafana" | "state_store";
  label: string;
  tone: StatusTone;
  detail: string;
  lastCheckedAt: string;
  href?: string;
}

interface WarningQueueRow {
  id: "partial_overlap" | "failed_retry" | "risky" | "stale_preview" | "supabase_unreachable";
  label: string;
  tone: StatusTone;
  count: number;
  impact: string;
}

interface AuditSummaryRow {
  auditId: string;
  time: string;
  result: "success" | "failure" | "cancelled" | "blocked";
  action: string;
  actor: string;
  summary: string;
  jobId?: string;
}
```

## Mock Data Contract

Dashboard must be runnable with local mock data before backend wiring.

```ts
export const mockDashboardData: DashboardResponse = {
  overall: {
    state: "running",
    title: "업로드 실행 중",
    message: "현재 12/18 파일 처리, 실패 0, 평균 처리 속도 24,000 rows/min.",
    action: "open_job",
  },
  topbarChips: [
    { id: "supabase", label: "Supabase", tone: "ready", value: "정상" },
    { id: "upload", label: "업로드", tone: "running", value: "실행 중" },
    { id: "grafana", label: "Grafana", tone: "ready", value: "연결됨" },
    { id: "state_store", label: "State Store", tone: "ready", value: "WAL" },
  ],
  statusMatrix: [
    {
      id: "upload",
      label: "업로드",
      tone: "running",
      value: "12/18 files",
      detail: "실패 0 · ETA 4분",
    },
    {
      id: "supabase",
      label: "Local Supabase",
      tone: "ready",
      value: "DB + Edge OK",
      detail: "127.0.0.1:54321",
    },
    {
      id: "storage",
      label: "WSL 저장소",
      tone: "ready",
      value: "126GB free",
      detail: "Docker / VHDX 정상",
    },
    {
      id: "grafana",
      label: "Grafana",
      tone: "ready",
      value: "연결됨",
      detail: "Open link only",
      action: { label: "Grafana 열기", href: "http://localhost:3001", target: "_blank" },
    },
    {
      id: "state_store",
      label: "State Store",
      tone: "ready",
      value: "WAL ready",
      detail: "%APPDATA% state DB",
    },
  ],
  currentJob: {
    jobId: "job_20260601_0912",
    status: "running",
    progressPct: 67,
    filesDone: 12,
    filesTotal: 18,
    rowsSent: 182440,
    startedAt: "2026-06-01T09:12:00+09:00",
    latestMessage: "PLC 2026-06-01 데이터 업로드 중",
  },
  recentJobs: [
    {
      jobId: "job_20260601_0912",
      status: "running",
      startedAt: "2026-06-01T09:12:00+09:00",
      mode: "upload",
      filesDone: 12,
      filesTotal: 18,
      rowsSent: 182440,
      failureCount: 0,
      warningCount: 0,
      latestMessage: "PLC 2026-06-01 데이터 업로드 중",
    },
    {
      jobId: "job_20260531_1745",
      status: "partial_failed",
      startedAt: "2026-05-31T17:45:00+09:00",
      mode: "retry_failed",
      filesDone: 21,
      filesTotal: 23,
      rowsSent: 204118,
      failureCount: 2,
      warningCount: 3,
      latestMessage: "TEMP 파일 2개 재시도 필요",
    },
  ],
  runtimeChecks: [
    {
      id: "supabase",
      label: "Local Supabase",
      tone: "ready",
      detail: "127.0.0.1:54321",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
    {
      id: "edge_function",
      label: "Edge Function",
      tone: "ready",
      detail: "upload-metrics reachable",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
    {
      id: "grafana",
      label: "Grafana",
      tone: "ready",
      detail: "http://localhost:3001",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
      href: "http://localhost:3001",
    },
    {
      id: "state_store",
      label: "State Store",
      tone: "ready",
      detail: "web_console_state.db WAL mode",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
  ],
  warningQueue: [
    {
      id: "partial_overlap",
      label: "일부 중복",
      tone: "attention",
      count: 3,
      impact: "기본 제외, Upload Preview에서만 포함 가능",
    },
    {
      id: "failed_retry",
      label: "실패 재시도",
      tone: "attention",
      count: 2,
      impact: "재시도 가능한 TEMP 실패",
    },
    {
      id: "risky",
      label: "위험 후보",
      tone: "ready",
      count: 0,
      impact: "위험 후보 없음",
    },
  ],
  auditSummary: [
    {
      auditId: "audit_001",
      time: "2026-06-01T09:15:00+09:00",
      result: "success",
      action: "upload.start",
      actor: "local\\operator",
      summary: "대상 18개, partial=false",
      jobId: "job_20260601_0912",
    },
  ],
};
```

## TanStack Query Strategy

Create a mock-first query wrapper.

```ts
const USE_MOCK_DASHBOARD = import.meta.env.VITE_API_MODE === "mock";

export function useDashboardQuery() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: USE_MOCK_DASHBOARD ? getMockDashboard : fetchDashboard,
    refetchInterval: 5000,
  });
}

async function fetchDashboard(): Promise<DashboardResponse> {
  const response = await fetch("/api/dashboard");
  if (!response.ok) throw new Error("Dashboard load failed");
  return response.json();
}

async function getMockDashboard(): Promise<DashboardResponse> {
  return mockDashboardData;
}
```

Until `/api/dashboard` exists, compose dashboard data from existing planned endpoints:

- `GET /api/runtime/supabase/status`
- `GET /api/runtime/grafana/status`
- `GET /api/upload/jobs`
- `GET /api/audit`
- `GET /api/logs`

Long term, `GET /api/dashboard` is recommended as a backend aggregator to keep first-paint simple.

Dashboard action mapping:

| UI action | Backend API |
|-----------|-------------|
| Open Upload Preview | `POST /api/upload/preview` after navigating to Upload |
| Open current job | `GET /api/upload/jobs/{job_id}` or Upload Job route state |
| Start Upload | `POST /api/upload/jobs` from Upload screen, not Dashboard-only |
| Retry Failed | `POST /api/upload/jobs/{job_id}/retry` from Upload screen |
| Start Supabase | `POST /api/runtime/supabase/start` |
| Stop Supabase | `POST /api/runtime/supabase/stop` |
| Open Grafana | external `<a>` link only |

Dashboard should not invent new destructive controls. If a Dashboard shortcut triggers a runtime mutation, it must reuse the backend audit behavior from `docs/02_engineering_plan.md`.

## Overall State Priority

Use this priority when deriving `overall.state`:

```text
blocked > running > attention > ready
```

Blocked:

- Supabase required but down.
- Config invalid.
- State store blocked.
- Upload job interrupted.

Running:

- Upload job running.
- Supabase start/stop in progress.

Attention:

- Failed retry items exist.
- Partial overlap preview exists.
- Risky preview items exist.
- Preview stale.
- Grafana unreachable.

Ready:

- Config valid.
- Supabase reachable.
- State store ready.
- No failed retry state.

## Table Columns

### Recent Jobs

| Column | Width | Align | Notes |
|--------|-------|-------|-------|
| Status | 104px | left | `StatusBadge` |
| Started | 128px | left | KST time |
| Mode | 104px | left | upload/retry |
| Files | 96px | right | data font |
| Rows | 128px | right | data font |
| Failures | 96px | right | danger color if `> 0` |
| Latest message | minmax | left | truncated |

### Runtime Checks

| Column | Width | Notes |
|--------|-------|-------|
| Service | 150px | Local Supabase, Edge Function |
| Status | 104px | badge |
| Detail | minmax | endpoint, URL, probe result |
| Last check | 112px | data font |

### Warning Queue

| Column | Width | Notes |
|--------|-------|-------|
| Type | 150px | localized label |
| Status | 104px | badge |
| Count | 80px | data font |
| Impact | minmax | concise Korean impact |

### Audit Summary

| Column | Width | Notes |
|--------|-------|-------|
| Time | 112px | data font |
| Result | 104px | badge |
| Action | 160px | action key |
| Actor | 140px | local actor |
| Summary | minmax | redacted params |

## CSS And Token Mapping

Use tokens from `docs/04_design_system.md`. Do not hardcode new colors in components.

```css
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel__header {
  min-height: 44px;
  padding: 0 var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
}

.table-scroll {
  overflow-x: auto;
  overflow-y: hidden;
}

.data-table {
  width: 100%;
  min-width: var(--table-min-width, 760px);
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  height: var(--table-row-height);
  padding: 0 10px;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-align: left;
}

.data-table td {
  height: var(--table-row-height);
  padding: 0 10px;
  border-top: 1px solid var(--color-border);
  font-size: var(--text-sm);
  line-height: var(--line-table);
}

.num,
.timestamp,
.job-id,
.endpoint {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}

.num {
  text-align: right;
}

.truncate {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
```

Action controls:

```css
.button {
  min-height: 32px;
  min-width: 96px;
  padding: 0 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}

.button:focus-visible,
.sidebar__nav a:focus-visible,
.data-table tr[data-clickable="true"]:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: var(--shadow-focus);
}

.status-badge {
  min-height: 22px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: var(--radius-pill);
  padding: 0 8px;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  white-space: nowrap;
}

.status-badge__icon {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
}

.status-badge--ready {
  color: var(--color-ready);
  background: var(--color-ready-soft);
}

.status-badge--running {
  color: var(--color-running);
  background: var(--color-running-soft);
}

.status-badge--attention {
  color: var(--color-attention);
  background: var(--color-attention-soft);
}

.status-badge--risk {
  color: var(--color-risk);
  background: var(--color-risk-soft);
}

.status-badge--failed {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.status-badge--blocked {
  color: var(--color-blocked);
  background: var(--color-blocked-soft);
}

.status-badge--muted {
  color: var(--color-muted);
  background: var(--color-muted-soft);
}
```

Semantic row emphasis:

```css
.row--attention {
  box-shadow: inset 3px 0 0 var(--color-attention);
}

.row--risk {
  box-shadow: inset 3px 0 0 var(--color-risk);
}

.row--failed,
.row--blocked {
  box-shadow: inset 3px 0 0 var(--color-danger);
}
```

This inset marker is semantic, not decorative elevation.

## Empty, Loading, Error States

### Empty

No jobs:

```text
아직 업로드 작업 없음
미리보기를 실행하면 업로드 대상과 DB 적재 여부가 여기에 표시됩니다.
```

No warnings:

```text
주의 항목 없음
위험 후보, 일부 중복, 실패 재시도 대상이 없습니다.
```

### Loading

- Use skeleton rows in tables.
- Keep row height fixed at `36px`.
- Loading copy must say what is being checked: config, Supabase, files, DB reconciliation.

Example:

```text
로컬 Supabase 상태 확인 중
DB, Edge Function, WSL 저장소를 확인하고 있습니다.
```

### Error

Dashboard load failure:

```text
Dashboard 상태를 불러오지 못했습니다.
로컬 백엔드가 실행 중인지 확인하고 Logs에서 자세한 오류를 확인하세요.
```

Rules:

- No toast-only failures.
- Failed background tasks must appear in Dashboard, Job Logs, and Audit Logs.
- Error rows use semantic left marker and failure badge.
- Blocked overall state must disable upload-start actions.

## Accessibility Requirements

- `main` uses `aria-labelledby="dashboard-title"`.
- Safety summary uses `aria-live="polite"`.
- New user-triggered blocking failures may use `role="alert"`.
- Status uses icon + visible text + color.
- Status icons are `aria-hidden="true"` because the visible label carries the state.
- Tables use real semantic table markup.
- Table headers use `<th scope="col">`.
- Timestamps render with `<time dateTime={iso}>`.
- Links and buttons use native elements.
- `Grafana 열기` is `<a target="_blank" rel="noreferrer">`.
- Keyboard focus is visible on nav, buttons, links, and selectable rows.
- Only actionable rows receive `tabIndex={0}`. Non-actionable table rows are not focus stops.
- Selectable rows support Enter and Space with the same behavior as click.
- Any collapsed status summary uses `aria-expanded` and `aria-controls`.
- Icon-only buttons require tooltip and accessible name.

## i18n Requirements

All visible text must come from i18next keys.

Suggested keys:

```text
dashboard.title
dashboard.topbar.current_running
dashboard.safety.running.title
dashboard.safety.running.message
dashboard.safety.blocked.title
dashboard.safety.blocked.message
dashboard.status.upload
dashboard.status.supabase
dashboard.status.storage
dashboard.status.grafana
dashboard.status.state_store
dashboard.jobs.title
dashboard.runtime.title
dashboard.warnings.title
dashboard.audit.title
status.ready
status.running
status.attention
status.risk
status.failed
status.blocked
status.muted
action.preview
action.start_upload
action.retry_failed
action.open_grafana
action.open_logs
empty.no_jobs.title
empty.no_jobs.message
empty.no_warnings.title
empty.no_warnings.message
error.dashboard_load.title
error.dashboard_load.message
```

Korean command labels should stay short:

- `미리보기`
- `업로드 시작`
- `실패 재시도`
- `Grafana 열기`
- `Logs 보기`
- `Job 보기`

Long explanations go in detail text, not buttons or badges.

## Forbidden Visual Patterns

- Marketing hero.
- Cinematic image or product photography.
- Apple branding imitation.
- Black Apple-style global nav.
- Decorative gradients, blobs, bokeh, or orbs.
- Nested cards.
- Card-heavy SaaS dashboard mosaic.
- Negative letter-spacing.
- Viewport-based font scaling.
- Grafana iframe.
- V1-excluded navigation items.

## Screenshot QA Checklist

Capture after implementation:

- `1366x768`
- `1920x1080`
- `1024x768`
- `720x900`
- `375x812`

Verify:

- First viewport answers safe / attention / blocked / running within 3 seconds.
- Safety banner is `72-96px`.
- Topbar is `52px`.
- Sidebar is `220px` on desktop.
- Status matrix includes Upload, Supabase, WSL/Storage, Grafana, State Store.
- Status badges are readable in Korean and English.
- Tables keep `36px` row height unless expanded.
- Table text does not overlap or clip at 1024px.
- Tables horizontally scroll below 720px.
- Numeric values use data font and tabular numbers.
- Numeric columns align right.
- Failed/blocked rows are visually stronger than ready rows.
- Focus ring is visible on nav, buttons, Grafana link, and actionable job rows.
- A failed job's `jobId` can be traced consistently from Dashboard to Logs and Audit.
- Grafana is link/status only.
- Empty/loading/error states are visible inline.
- No v1-excluded pages or actions appear.
- Page does not read as a landing page.

## Acceptance Checklist

- Dashboard Variant D is implemented as a table-oriented operator console.
- Mock data can render the full screen without backend.
- TanStack Query wrapper can switch from mock to real API.
- Layout follows AppShell + Topbar + Dashboard grid.
- Component names match this spec.
- Design tokens come from `docs/04_design_system.md`.
- `docs/05_dashboard_design_review.md` corrections are applied.
- Status uses lucide icon + label + semantic color.
- Korean UI text fits fixed controls.
- Audit summary is visible but not a full audit table.
- Latest warning/failure is visible in WarningQueuePanel.
- Local Supabase start/stop status is represented, but destructive controls are not added to Dashboard unless backend supports them.
- Grafana is never embedded.
