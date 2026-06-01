# Dashboard Variant D HTML/React Specification

This document converts **Variant D: Data Table-Oriented Console** into a React-implementable screen specification.

It does not add application code. It defines the target DOM structure, component tree, layout rules, data contracts, and styling constraints for the future Dashboard implementation.

## Source References

- Figma: [Extrusion Web Console Dashboard Design Shotgun](https://www.figma.com/design/xuI1kMSJs44UQGIO87pG7R)
- Variant: `Variant D · Data Table-Oriented Console`
- UI/UX source: `docs/03_ui_ux_plan.md`
- Design system source: `docs/04_design_system.md`
- Dashboard design review: `docs/05_dashboard_design_review.md`

## Design-Html Mode

- Mode: plan-driven, Figma-informed.
- Target framework: React + TypeScript, per `docs/02_engineering_plan.md`.
- Pretext classification: card/grid dashboard.
- Pretext API tier if a standalone HTML prototype is generated later: `prepare()` + `layout()` for resize-aware text height in cards, banners, and table expandable detail rows.

The project currently has no `package.json` or React scaffold, so this file is an implementation spec rather than a generated component.

## Variant D Intent

Variant D is the most table-oriented Dashboard direction.

Primary goal:

> Make repeated operator checks fast by presenting upload, runtime, warnings, and audit-relevant activity as compact status rows and tables.

Use Variant D for the lower Dashboard structure, but apply the corrections from `docs/05_dashboard_design_review.md`:

- Keep status-first safety banner at the top.
- Add an explicit State Store panel.
- Use lucide icons instead of text-symbol status icons.
- Use mono data typography for numbers, timestamps, job IDs, and URLs.
- Preserve bordered panels and 8px max radius.

## First Viewport Layout

Desktop target: `1440 x 900`.

The first viewport must show:

1. Sidebar navigation.
2. Top status bar.
3. Safety summary banner.
4. Compact runtime/status matrix.
5. Recent jobs table.
6. Runtime check table.
7. Warning/failure queue.
8. Audit summary table or compact list.

At `1366 x 768`, the safety banner, status matrix, and at least the top of Recent Jobs must be visible without scrolling.

## Page Grid

Use the app shell from `docs/04_design_system.md`.

```text
+----------------------+-----------------------------------------------+
| Sidebar 220px       | Topbar 52px                                   |
|                      +-----------------------------------------------+
|                      | Dashboard content                             |
|                      | 20px page padding desktop                     |
|                      |                                               |
+----------------------+-----------------------------------------------+
```

CSS layout:

```css
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  grid-template-rows: var(--topbar-height) minmax(0, 1fr);
  background: var(--color-bg);
}

.sidebar {
  grid-row: 1 / span 2;
  grid-column: 1;
}

.topbar {
  grid-row: 1;
  grid-column: 2;
}

.dashboard-page {
  grid-row: 2;
  grid-column: 2;
  padding: var(--space-5);
  min-width: 0;
  overflow: auto;
}
```

Responsive:

- `>= 1200px`: full desktop layout.
- `< 900px`: sidebar collapses to icon rail, content grid keeps table scroll.
- `< 720px`: navigation becomes top tabs, content remains table-first with horizontal scroll.

## Component Tree

```tsx
<AppShell>
  <SidebarNav activePage="dashboard" />
  <TopStatusBar>
    <PageTitle />
    <StatusChipGroup />
  </TopStatusBar>

  <DashboardPage>
    <SafetySummaryBanner />
    <DashboardStatusMatrix />
    <RecentJobsPanel />

    <DashboardLowerGrid>
      <RuntimeCheckPanel />
      <WarningQueuePanel />
      <AuditSummaryPanel />
    </DashboardLowerGrid>
  </DashboardPage>
</AppShell>
```

Recommended file split after scaffold exists:

```text
frontend/src/pages/DashboardPage.tsx
frontend/src/components/app/AppShell.tsx
frontend/src/components/app/SidebarNav.tsx
frontend/src/components/app/TopStatusBar.tsx
frontend/src/components/status/StatusBadge.tsx
frontend/src/components/dashboard/SafetySummaryBanner.tsx
frontend/src/components/dashboard/DashboardStatusMatrix.tsx
frontend/src/components/dashboard/RecentJobsPanel.tsx
frontend/src/components/dashboard/RuntimeCheckPanel.tsx
frontend/src/components/dashboard/WarningQueuePanel.tsx
frontend/src/components/dashboard/AuditSummaryPanel.tsx
```

## Semantic HTML Structure

```html
<div class="app-shell">
  <aside class="sidebar" aria-label="Primary navigation">
    <div class="sidebar__brand">
      <span class="sidebar__product">Extrusion</span>
      <span class="sidebar__subtitle">Web Console</span>
    </div>

    <nav class="sidebar__nav">
      <a aria-current="page">대시보드</a>
      <a>업로드</a>
      <a>로그</a>
      <a>설정</a>
    </nav>

    <div class="sidebar__meta">
      <span class="status-badge status-badge--ready">localhost</span>
      <button type="button">한국어</button>
      <span>v1 Core Ops</span>
    </div>
  </aside>

  <header class="topbar">
    <div class="topbar__title">
      <h1>대시보드</h1>
      <p>현재: 실행 중인 업로드 1개</p>
    </div>

    <div class="topbar__status" aria-label="System status">
      <!-- Status chips -->
    </div>
  </header>

  <main class="dashboard-page" aria-labelledby="dashboard-title">
    <section class="safety-summary" aria-live="polite">
      <!-- Current overall state -->
    </section>

    <section class="status-matrix" aria-label="Runtime and upload summary">
      <!-- Upload, Supabase, WSL/Storage, Grafana, State Store -->
    </section>

    <section class="panel recent-jobs" aria-labelledby="recent-jobs-title">
      <header class="panel__header">
        <h2 id="recent-jobs-title">최근 업로드 작업</h2>
      </header>
      <div class="table-wrap">
        <table>
          <!-- Recent jobs rows -->
        </table>
      </div>
    </section>

    <section class="dashboard-lower-grid">
      <section class="panel runtime-checks" aria-labelledby="runtime-checks-title">
        <!-- Runtime table -->
      </section>

      <section class="panel warning-queue" aria-labelledby="warning-queue-title">
        <!-- Warning/failure queue table -->
      </section>

      <section class="panel audit-summary" aria-labelledby="audit-summary-title">
        <!-- Audit summary table/list -->
      </section>
    </section>
  </main>
</div>
```

## Dashboard Content Layout

Desktop grid:

```css
.dashboard-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-4);
}

.safety-summary {
  min-height: 72px;
  max-height: 96px;
}

.status-matrix {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-3);
}

.dashboard-lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-4);
}

.audit-summary {
  grid-column: 1 / -1;
}
```

For `1440px` desktop content, the Variant D visual order should be:

```text
Safety banner:        full width
Status matrix:        full width, 5 compact cells
Recent jobs table:    full width
Lower grid row 1:     Runtime checks | Warning queue
Lower grid row 2:     Audit summary full width or compact right column if height is tight
```

At `1366x768`, reduce vertical gaps from `16px` to `12px` if needed, but do not shrink table row height below `36px`.

## Components

### SafetySummaryBanner

Purpose: Answer the main operator question immediately.

Variant D default example:

```text
업로드 실행 중
현재 12/18 파일 처리, 실패 0, 평균 처리 속도 24,000 rows/min.
Action: Job 보기
```

Props:

```ts
type OverallSystemState = "ready" | "attention" | "blocked" | "running";

interface SafetySummaryBannerProps {
  state: OverallSystemState;
  title: string;
  message: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}
```

Rules:

- Height: `72-96px`.
- Use state icon + text + semantic background.
- No hero typography.
- No centered marketing layout.
- If `blocked`, action should point to the blocked recovery path, usually Supabase start/status or Logs.

### DashboardStatusMatrix

Variant D uses a compact matrix instead of large cards.

Required cells:

1. Upload.
2. Local Supabase.
3. WSL/Storage.
4. Grafana.
5. State Store.

Props:

```ts
interface StatusMatrixItem {
  id: "upload" | "supabase" | "storage" | "grafana" | "state_store";
  label: string;
  state: OverallSystemState | "muted" | "failed";
  value: string;
  detail: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

interface DashboardStatusMatrixProps {
  items: StatusMatrixItem[];
}
```

Layout:

- Desktop: 5 equal columns.
- `1024px`: 3 columns then 2 columns.
- `< 720px`: horizontal scroll with fixed-width cells, `min-width: 180px`.

Cell visual:

```html
<article class="status-cell">
  <div class="status-cell__label">업로드</div>
  <StatusBadge tone="running">실행 중</StatusBadge>
  <div class="status-cell__value">12/18 files</div>
  <div class="status-cell__detail">실패 0 · ETA 4분</div>
</article>
```

### StatusBadge

Use lucide icons in implementation.

```ts
type StatusTone =
  | "ready"
  | "running"
  | "attention"
  | "risk"
  | "failed"
  | "blocked"
  | "muted";

interface StatusBadgeProps {
  tone: StatusTone;
  children: React.ReactNode;
}
```

Mapping:

| Tone | Icon | Use |
|------|------|-----|
| ready | `CheckCircle` | safe/complete |
| running | `Activity` | active job/runtime |
| attention | `TriangleAlert` | inspect soon |
| risk | `AlertTriangle` | risky preview item |
| failed | `CircleX` | failed operation |
| blocked | `OctagonAlert` | action unavailable |
| muted | `Circle` | inactive/unknown |

Badge CSS:

```css
.status-badge {
  height: 22px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  line-height: 1;
  white-space: nowrap;
}

.status-badge svg {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
}
```

### RecentJobsPanel

This is the primary table surface in Variant D.

Columns:

| Column | Width | Align | Notes |
|--------|-------|-------|-------|
| Status | 96px | left | badge |
| Started | 116px | left | KST time/date |
| Mode | 96px | left | upload / retry |
| Files | 92px | right | data font |
| Rows | 120px | right | data font |
| Failures | 88px | right | data font, semantic color if > 0 |
| Latest message | minmax | left | truncated with title |

Props:

```ts
interface RecentJobRow {
  jobId: string;
  status: "running" | "succeeded" | "partial_failed" | "failed" | "cancelled" | "interrupted";
  startedAt: string;
  mode: "upload" | "retry_failed" | "preview";
  filesDone: number;
  filesTotal: number;
  rowsSent: number;
  failureCount: number;
  warningCount: number;
  latestMessage: string;
}

interface RecentJobsPanelProps {
  jobs: RecentJobRow[];
}
```

Table rules:

- Row height: `36px`.
- Header height: `36px`.
- Sticky header if panel scrolls.
- Failed/interrupted rows get semantic left border, not full red fill.
- `failed` and `interrupted` rows stay visible above old success rows if sorting by priority.
- Job ID should be available in expanded row or details link, not necessarily always visible in the compact row.

Example row:

```html
<tr class="job-row job-row--attention">
  <td><StatusBadge tone="attention">일부 실패</StatusBadge></td>
  <td><time dateTime="2026-06-01T09:12:00+09:00">오늘 09:12</time></td>
  <td>retry</td>
  <td class="num">21/23</td>
  <td class="num">204,118</td>
  <td class="num danger">2</td>
  <td class="truncate">TEMP 파일 2개 재시도 필요</td>
</tr>
```

### RuntimeCheckPanel

Purpose: show local runtime health as a compact operational table.

Rows:

- Local Supabase.
- Database.
- Edge Function.
- WSL Storage.
- Grafana.
- State Store.

Columns:

| Column | Width | Notes |
|--------|-------|-------|
| Service | 144px | `Local Supabase`, `Edge Function` |
| Status | 96px | badge |
| Endpoint / Detail | minmax | URL, probe, or storage metric |
| Last Check | 96px | data font |

Grafana row rules:

- Action is link only.
- No iframe, preview, or dashboard management.
- If unreachable, show URL and last error.

### WarningQueuePanel

Purpose: summarize risks that change operator behavior.

Rows:

- `partial_overlap`.
- `failed_retry`.
- `risky`.
- `stale_preview`.
- `supabase_unreachable`.

Columns:

| Column | Width | Notes |
|--------|-------|-------|
| Type | 160px | technical key or localized label |
| Status | 96px | badge |
| Count | 80px | data font |
| Operator impact | minmax | concise Korean sentence |

Rules:

- `risky` uses risk tone, not attention.
- `partial_overlap` uses attention tone and must mention default exclusion.
- `supabase_unreachable` uses blocked tone.
- Count `0` rows may remain visible but muted if they help scanning.

### AuditSummaryPanel

Purpose: show audit-relevant recent actions without replacing the full Audit Logs page.

Rows:

- Upload start.
- Upload preview.
- Upload retry.
- Supabase start/stop.
- Failed operation.

Columns:

| Column | Width | Notes |
|--------|-------|-------|
| Time | 96px | data font |
| Result | 96px | badge |
| Action | 160px | `upload.start`, `supabase.start` |
| Actor | 120px | OS/local actor |
| Summary | minmax | redacted params summary |

Rules:

- No delete/edit controls.
- Secret values are never shown.
- Failed, blocked, cancelled results must stand out.

## Data Contract For Dashboard API

Recommended endpoint:

```text
GET /api/dashboard
```

Response shape:

```ts
interface DashboardResponse {
  overall: {
    state: "ready" | "attention" | "blocked" | "running";
    title: string;
    message: string;
    action: "preview" | "start_upload" | "retry_failed" | "open_job" | "start_supabase" | "open_logs" | null;
  };
  statusMatrix: StatusMatrixItem[];
  currentJob: {
    jobId: string;
    status: "queued" | "running" | "succeeded" | "partial_failed" | "failed" | "paused" | "cancelled" | "interrupted";
    progressPct: number;
    filesDone: number;
    filesTotal: number;
    rowsSent: number;
    failureCount: number;
    currentFile?: string;
  } | null;
  recentJobs: RecentJobRow[];
  runtimeChecks: RuntimeCheckRow[];
  warningQueue: WarningQueueRow[];
  auditSummary: AuditSummaryRow[];
}
```

Type details:

```ts
interface RuntimeCheckRow {
  id: "supabase" | "database" | "edge_function" | "wsl_storage" | "grafana" | "state_store";
  label: string;
  status: StatusTone;
  detail: string;
  lastCheckedAt: string;
  href?: string;
}

interface WarningQueueRow {
  id: "partial_overlap" | "failed_retry" | "risky" | "stale_preview" | "supabase_unreachable";
  label: string;
  status: StatusTone;
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

## State Priority

Overall Dashboard state should be computed in backend or a shared frontend selector with this priority:

```text
blocked
  > running
  > attention
  > ready
```

Blocked examples:

- Local Supabase unavailable for local target.
- Config invalid.
- State store blocked.
- Upload job interrupted.

Running examples:

- Upload job running.
- Supabase start/stop running.

Attention examples:

- Failed retry state exists.
- Partial overlap preview exists.
- Risky preview items exist.
- Grafana unreachable.
- Preview stale.

Ready examples:

- Config valid.
- Local Supabase reachable.
- State store ready.
- No blocking or retryable failures.

## CSS Token Usage

Use only project tokens from `docs/04_design_system.md`.

Minimum token block needed by this screen:

```css
:root {
  --font-sans: "Geist", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-data: "Geist Mono", "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;

  --color-bg: #f6f7f9;
  --color-surface: #ffffff;
  --color-surface-raised: #fbfcfd;
  --color-surface-muted: #f1f4f7;
  --color-border: #d7dde5;
  --color-border-strong: #b9c2ce;
  --color-text: #17202a;
  --color-text-muted: #5d6978;
  --color-text-subtle: #7a8594;
  --color-primary: #005ea8;
  --color-ready: #1f7a4d;
  --color-ready-soft: #e7f4ee;
  --color-running: #2563eb;
  --color-running-soft: #e9f0ff;
  --color-attention: #b7791f;
  --color-attention-soft: #fff4dc;
  --color-risk: #c05621;
  --color-risk-soft: #fff0e6;
  --color-danger: #c2413a;
  --color-danger-soft: #fdeceb;
  --color-blocked: #8b1e1e;
  --color-blocked-soft: #f7e7e7;
  --color-muted: #687386;
  --color-muted-soft: #edf0f3;

  --text-xs: 12px;
  --text-sm: 13px;
  --text-md: 14px;
  --text-body: 15px;
  --text-lg: 18px;
  --text-page: 26px;

  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;

  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-pill: 999px;

  --sidebar-width: 220px;
  --topbar-height: 52px;
  --control-height: 36px;
  --table-row-height: 36px;
}
```

## Table CSS Structure

```css
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel__header {
  height: 44px;
  padding: 0 var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
}

.table-wrap {
  overflow: auto;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.data-table th {
  height: 36px;
  padding: 0 10px;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-align: left;
}

.data-table td {
  height: 36px;
  padding: 0 10px;
  border-top: 1px solid var(--color-border);
  font-size: var(--text-sm);
  color: var(--color-text);
  vertical-align: middle;
}

.num,
.timestamp,
.job-id,
.endpoint {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}

.truncate {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.row--failed,
.row--blocked {
  box-shadow: inset 3px 0 0 var(--color-danger);
}

.row--attention {
  box-shadow: inset 3px 0 0 var(--color-attention);
}
```

Note: `box-shadow: inset` is allowed here as a semantic row marker, not decorative elevation.

## React JSX Skeleton

```tsx
export function DashboardPage({ data }: { data: DashboardResponse }) {
  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <SafetySummaryBanner
        state={data.overall.state}
        title={data.overall.title}
        message={data.overall.message}
        action={resolveDashboardAction(data.overall.action)}
      />

      <DashboardStatusMatrix items={data.statusMatrix} />

      <RecentJobsPanel jobs={data.recentJobs} />

      <section className="dashboard-lower-grid" aria-label="Dashboard details">
        <RuntimeCheckPanel rows={data.runtimeChecks} />
        <WarningQueuePanel rows={data.warningQueue} />
        <AuditSummaryPanel rows={data.auditSummary} />
      </section>
    </main>
  );
}
```

Status badge skeleton:

```tsx
const statusIcon = {
  ready: CheckCircle,
  running: Activity,
  attention: TriangleAlert,
  risk: AlertTriangle,
  failed: CircleX,
  blocked: OctagonAlert,
  muted: Circle,
} satisfies Record<StatusTone, LucideIcon>;

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  const Icon = statusIcon[tone];

  return (
    <span className={`status-badge status-badge--${tone}`}>
      <Icon aria-hidden="true" />
      <span>{children}</span>
    </span>
  );
}
```

## Empty, Loading, Failure States

Dashboard no jobs:

```text
아직 업로드 작업 없음
미리보기를 실행하면 업로드 대상과 DB 적재 여부가 여기에 표시됩니다.
```

Runtime checking:

```text
로컬 Supabase 상태 확인 중
DB, Edge Function, WSL 저장소를 확인하고 있습니다.
```

Blocked:

```text
업로드 차단됨
로컬 Supabase DB에 연결할 수 없습니다. Supabase 상태를 확인한 뒤 다시 시도하세요.
```

Rules:

- No toast-only failures.
- Every failed background task must appear in Dashboard, Job Logs, and Audit Logs.
- Loading tables use skeleton rows with stable 36px row height.

## Accessibility Requirements

- `main` must have an accessible Dashboard label.
- `SafetySummaryBanner` uses `aria-live="polite"`.
- Blocked/failure banners should use `role="alert"` only when newly triggered by user action.
- Status must be icon + text + color.
- Tables use real `<table>`, `<thead>`, `<tbody>`, `<th scope="col">`.
- Action buttons use real `<button>` or `<a>` based on behavior.
- `Open Grafana` is an `<a>` with `target="_blank"` and `rel="noreferrer"`.
- Keyboard focus is visible on nav, buttons, links, and table rows if selectable.

## Internationalization Rules

All visible text must come from i18n keys.

Recommended key groups:

```text
dashboard.title
dashboard.topbar.current_running
dashboard.safety.running.title
dashboard.safety.running.message
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
```

Korean labels must fit the fixed compact layout. Keep command labels short:

- `Job 보기`
- `미리보기`
- `업로드 시작`
- `실패 재시도`
- `Grafana 열기`

## Not In Scope For This Screen

- Full Upload Preview table.
- Full Audit Logs table.
- Full Job Logs stream viewer.
- Data archive/delete.
- Supabase delete management.
- Cycle Ops.
- Training Dataset Builder.
- Grafana iframe embedding.
- Multi-user LAN controls.
- Theme picker.

## Acceptance Checklist

- Uses Variant D table-oriented structure.
- Includes explicit State Store status cell.
- Safety banner stays within 72-96px.
- Dashboard answers safe / attention / blocked / running within 3 seconds.
- Topbar height is 52px.
- Sidebar width is 220px on desktop.
- Panel radius is max 8px.
- Status badges are 22px, with lucide icon + label + color.
- Buttons are 36px high and use 6px radius.
- Numeric values use data font and tabular numbers.
- Tables use real table markup and 36px rows.
- Grafana is status/link only.
- No v1-excluded navigation items appear.
- No marketing hero, product imagery, decorative gradients, or card-heavy landing layout.
