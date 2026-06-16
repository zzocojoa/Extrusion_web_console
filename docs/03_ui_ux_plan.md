# Extrusion Web Console UI/UX Plan

This document is the v1 Core Ops UI decision record. It follows `docs/00_product_scope.md`, `docs/01_development_roadmap.md`, and `docs/02_engineering_plan.md`.

## Product Frame

Extrusion Web Console is a local factory operations console. It is not a landing page, not a dashboard showcase, and not a web clone of the Tkinter GUI.

Primary operator question:

> Is upload, database, and runtime state safe right now?

The first viewport must answer that question without scrolling.

## Design Principles

- Dense, quiet, operational UI.
- Status before decoration.
- Tables for comparison, not card grids.
- Buttons only for clear commands.
- Audit trail over repeated confirmation dialogs.
- Korean and English strings must fit without changing layout.
- Every failed background task must be visible in Dashboard, Logs, and Audit Logs.

## Information Architecture

V1 navigation has four primary pages:

1. Dashboard
2. Upload
3. Logs
4. Settings

Runtime status is not a separate page in v1. Local Supabase and Grafana appear on Dashboard and Settings.

Out-of-scope legacy GUI tabs are not shown in navigation:

- Work Log
- Cycle Ops
- Data Mgmt
- Supabase Mgmt delete UI
- Training Dataset Builder

## App Shell

Desktop layout:

```text
+------------------+--------------------------------------------------+
| Sidebar          | Top status bar                                   |
|                  +--------------------------------------------------+
| Dashboard        | Page content                                     |
| Upload           |                                                  |
| Logs             |                                                  |
| Settings         |                                                  |
|                  |                                                  |
| App status       |                                                  |
+------------------+--------------------------------------------------+
```

Sidebar:

- Width: 220 px desktop, collapses to icon-only below 900 px.
- Items: Dashboard, Upload, Logs, Settings.
- Bottom area: language switch, localhost badge, app version.
- Active nav item uses left accent border and slightly stronger background.

Top status bar:

- Left: current page title and short current state.
- Right: compact status chips for Supabase, Grafana, Upload job, Audit.
- No marketing copy, no large hero message.

Mobile/small layout:

- Below 720 px, sidebar becomes a top tab bar.
- V1 supports read and simple actions on small screens, but bulk table work is desktop-first.
- Tables use horizontal scroll, sticky first column, and density is preserved.

## Page 1: Dashboard

Dashboard first viewport layout:

```text
+-------------------------------------------------------------------+
| Safety Summary: Ready / Attention / Blocked / Running              |
+-----------------------+----------------------+--------------------+
| Upload State          | Local Supabase       | Grafana            |
| last preview/job      | status/start/stop    | status/open link   |
+-----------------------+----------------------+--------------------+
| Current Job / Latest Failure                                      |
+-------------------------------------------------------------------+
| Recent Activity: job events + audit failures                       |
+-------------------------------------------------------------------+
```

Primary summary states:

- `Ready`: Supabase reachable, config valid, no failed retry state, latest preview has upload targets or no targets.
- `Attention`: retryable failures, partial overlap, risky preview items, stale preview, Grafana unavailable.
- `Blocked`: invalid config, local Supabase down for local target, state store blocked, upload job interrupted.
- `Running`: upload or runtime start/stop job active.

Dashboard components:

- `SafetySummaryBanner`
  - Shows one dominant state, 1-line reason, and next safe action.
  - Height is fixed between 72 and 96 px.
  - Uses icon + label, not a decorative hero.
- `StatusChipGroup`
  - Supabase, Grafana, Upload, State Store.
- `UploadStatePanel`
  - Latest preview timestamp.
  - Counts: target, already in DB, partial overlap, risky, excluded.
  - Buttons: Preview, Start Upload, Retry Failed.
- `RuntimePanel`
  - Local Supabase status.
  - Buttons: Start, Stop.
  - Grafana status.
  - Button: Open Grafana.
- `CurrentJobPanel`
  - Progress bar, current file, processed rows, failed count.
  - Shows Pause/Resume/Cancel only while supported by backend state.
- `LatestFailurePanel`
  - Latest failed job/file with error and link to Logs.
- `RecentActivityList`
  - Last 10 job/audit events.

Dashboard does not include:

- Full upload preview table.
- Full audit log table.
- Archive/delete controls.
- Grafana embedded panels.

## Page 2: Upload

Upload page is split into Preview and Job tabs.

```text
Upload
  [Preview] [Job]
```

### Upload Preview Tab

Header controls:

- Range selector: Today, Yesterday, Last 2 Days, Custom.
- Custom start/end date fields when Custom is selected.
- File source summary: PLC dir, temp dir if enabled later.
- Buttons: Run Preview, Start Upload.
- Current scaffold: Start Upload is visible but disabled because real upload job execution is not implemented yet.
- Future upload job phase: Start Upload remains disabled when preview is stale, blocked, or absent.

Preview summary row:

```text
Targets 124 | Already in DB 82 | Partial 3 | Risky 2 | Excluded 14 | Total 225
```

Preview table columns:

| Column | Purpose |
|--------|---------|
| Status | target, already in DB, partial, risky, excluded |
| Filename | CSV filename, sticky first data column |
| Kind | PLC, temperature |
| File Date | Parsed KST date |
| Rows | parsed row count if known |
| DB Match | exact `(timestamp, device_id)` match count |
| Upload Rows | estimated rows to upload |
| Reason | excluded/risky/partial explanation |
| Modified | file mtime |
| Path | truncated path with copy action |

Status meanings:

- `target`: local rows are not represented in DB and file is safe to upload.
- `already_in_db`: all extracted exact `(timestamp, device_id)` keys are represented in Supabase.
- `partial_overlap`: some exact `(timestamp, device_id)` keys exist and some do not. This is not included by default in v1.
- `risky`: DB unreachable, parse incomplete, schema uncertain, or state mismatch.
- `excluded`: out of range, locked, unstable, unsupported, empty, already completed in new state store.

Preview interactions:

- Search filename/path.
- Filter by status.
- Sort by status, date, filename, upload rows.
- Row expand shows detailed reasons and exact key counts.
- Bulk selection is not needed for v1. When upload jobs are implemented, Start Upload uses eligible `target` rows by default.

Risk handling:

- `risky` files are never uploaded by default.
- `partial_overlap` appears in warning color and remains excluded by default.
- A future include-partial control, if added, must be visible and audit logged as part of upload start params.

### Upload Job Tab

Job screen layout:

```text
+-------------------------------------------------------------------+
| Job Header: status, started at, duration, mode                      |
+-------------------------------------------------------------------+
| Overall progress bar | files done | rows sent | failures            |
+-------------------------------------------------------------------+
| Current files table                                                  |
+-------------------------------------------------------------------+
| Live job events                                                      |
+-------------------------------------------------------------------+
```

Job table columns:

- Status
- Filename
- Kind
- Progress
- Rows processed
- Resume offset
- Retry count
- Last error

Failure behavior:

- Failed files stay visible at top after job completes.
- `Retry Failed` button appears when failed files exist.
- A failed upload must show the same job id in job table, logs, and audit table.

## Page 3: Logs

Logs page has two tabs:

```text
Logs
  [Job Logs] [Audit Logs]
```

### Job Logs

Purpose: runtime and upload diagnostics.

Controls:

- Job selector.
- Level filter: all, info, warning, error.
- Text search.
- Auto-scroll toggle.
- Export visible logs as text.

Columns:

- Time
- Level
- Job id
- Event type
- Message
- Details

Job logs are append-only in UI. No delete.

### Audit Logs

Purpose: operator action trail.

Controls:

- Date range.
- Action filter.
- Result filter.
- Job id search.

Columns:

- Time
- Actor
- Action
- Target
- Result
- Params
- Job id
- Error

Audit styling:

- Success is quiet.
- Failed/cancelled/blocked is always visually prominent.
- Redacted secrets display as `••••••`.

Logs and Audit Logs must not be merged. Operators need to distinguish "what the system did" from "who requested what".

## Page 4: Settings

Settings uses sections, not one long unstructured form.

Sections:

1. Runtime
   - App bind mode: fixed `localhost`.
   - State DB path.
   - Config file path.
   - Backend version.
2. Connection
   - Supabase URL.
   - Anon key.
   - Edge Function URL.
   - Derived upload URL preview.
3. Folders
   - Process data directory.
   - Production daily report directory, displayed only if backend supports it in v1.
   - WSL VHDX path.
4. Upload Options
   - Smart Sync.
   - Upload range.
   - Custom date range.
   - mtime lag minutes.
   - check locked files.
5. Interface
   - Language: Korean, English.
   - Density: compact only for v1. No theme picker.
6. Runtime Actions
   - Local Supabase status/start/stop.
   - Grafana status/open link.

Settings field rules:

- Every field shows source: default, config file, `.env`, process env.
- Env-overridden fields are read-only and show an `Overridden` badge.
- Save button is sticky at page bottom.
- Unsaved changes show a persistent dirty-state bar.
- Validation appears inline beside the section and in a top summary.
- Secret fields are masked by default with reveal button.

Settings save:

- Saves only editable config values.
- Shows audit result after save.
- Does not use success modal unless save failed or validation blocked.

## Local Supabase And Grafana UI

Local Supabase status states:

- Checking
- Running
- Starting
- Stopping
- Stopped
- Error
- Remote target

Supabase controls:

- Start: enabled only for local target and stopped/error states.
- Stop: enabled only for local target and running/error states.
- During starting/stopping, controls are disabled and progress is shown.

Grafana status states:

- Ready
- Unreachable
- Starting
- Missing
- Unknown

Grafana controls:

- Open Grafana link only.
- No iframe, no embedded dashboard, no dashboard management UI.
- If unreachable, show URL and last check error.

## Visual System

Use a restrained utility-console palette:

- Background: `#F6F7F9`
- Surface: `#FFFFFF`
- Surface muted: `#EEF1F4`
- Border: `#D7DCE2`
- Text: `#17202A`
- Text muted: `#5D6978`
- Ready: `#1F8A5B`
- Running: `#2563EB`
- Attention: `#B7791F`
- Danger: `#C2413A`
- Blocked: `#8B1E1E`
- Info: `#2F6F8F`

No dominant purple, beige, dark-blue slate, brown/orange, or gradient theme.

Status tokens:

| Token | Color | Icon | Use |
|-------|-------|------|-----|
| ready | green | check-circle | safe to proceed |
| running | blue | activity | active job/runtime operation |
| attention | amber | triangle-alert | operator should inspect |
| blocked | dark red | octagon-alert | action unavailable |
| failed | red | circle-x | operation failed |
| muted | gray | circle | inactive/unknown |

Buttons:

- Primary: Start Upload, Run Preview, Save Settings.
- Secondary: Retry Failed, Open Grafana, Refresh.
- Destructive/stop: Stop Supabase, Cancel Job.
- Icon buttons use lucide icons with tooltips.
- Button text must not exceed 22 English chars or 12 Korean chars where possible.

Tables:

- Header height: 36 px.
- Row height: 36 px compact, 44 px when expanded.
- Sticky header.
- Sticky filename column for preview table.
- Status uses icon + short badge.
- Long paths truncate middle with copy button.

Cards:

- Use cards only for individual panels.
- Radius max 8 px.
- No cards inside cards.
- Page sections are full-width layouts, not nested decorative containers.

## Korean And English Text Rules

- Use i18n keys from day one.
- Korean labels may be longer after technical nouns are included. Components must allow wrapping in labels and fixed-height controls must use short labels.
- Avoid sentence-length button labels.
- Put long explanation text in detail rows, tooltips, or expandable panels.
- Tables use column labels short enough for both languages.

Recommended labels:

| Concept | English | Korean |
|---------|---------|--------|
| Dashboard | Dashboard | 대시보드 |
| Upload | Upload | 업로드 |
| Logs | Logs | 로그 |
| Settings | Settings | 설정 |
| Run Preview | Preview | 미리보기 |
| Start Upload | Start Upload | 업로드 시작 |
| Retry Failed | Retry Failed | 실패 재시도 |
| Open Grafana | Open Grafana | Grafana 열기 |
| Local Supabase | Local Supabase | 로컬 Supabase |
| Audit Logs | Audit Logs | 감사 로그 |
| Already in DB | Already in DB | DB 적재됨 |
| Partial Overlap | Partial | 일부 중복 |
| Risky | Risky | 주의 |
| Excluded | Excluded | 제외 |

## Empty, Loading, And Failure States

Empty states:

- Dashboard no jobs: "No upload jobs yet" / "아직 업로드 작업 없음".
- Preview no files: show checked folder, range, and next action.
- Logs empty: show selected filter and clear-filter action.
- Audit empty: show date range and action filters.

Loading states:

- Use skeleton rows for tables.
- Use progress indicator for runtime start/stop and upload jobs.
- Loading text must include what is being checked: config, Supabase, files, DB reconciliation.

Failure states:

- Inline error banner at top of affected page.
- Error row in relevant table.
- Link to Logs or Audit Logs.
- No toast-only failures.

## User Flows

### Normal Upload

```text
Dashboard -> Preview -> review counts/table -> Start Upload
  -> Job tab opens -> live progress -> completed
  -> Dashboard shows latest success
```

### Retry Failed

```text
Dashboard attention state -> Retry Failed
  -> Upload Job tab -> failed files preselected by backend
  -> live progress -> audit result
```

### Supabase Down

```text
Dashboard blocked -> Start Local Supabase
  -> Running status checks
  -> Ready or Error
  -> Upload actions enabled only after ready
```

### Preview Risk

```text
Upload Preview -> risky/partial rows visible
  -> Start Upload disabled for risky
  -> partial rows excluded by default
  -> future override behavior must be audit logged
```

### Settings Override

```text
Settings -> operator sees value + source badge
  -> env-overridden fields read-only
  -> save editable values
  -> audit log records changed keys only, secrets redacted
```

## Accessibility

- All status uses icon + text, never color alone.
- Keyboard focus is visible.
- Tables support keyboard row focus.
- Buttons have accessible names.
- Status chips expose `aria-live="polite"` when changing.
- Error banners use `role="alert"`.
- Minimum contrast target: WCAG AA.

## Responsive Scope

Desktop primary target:

- 1366 x 768
- 1920 x 1080

Small supported:

- 1024 x 768: full feature support.
- 720 px wide: navigation becomes top tabs, tables scroll horizontally.
- 375 px wide: readable status and logs, but bulk preview review is horizontal-scroll only.

Not required in v1:

- Phone-optimized bulk upload workflow.
- Offline mobile PWA behavior.

## V1 UI Not In Scope

- Data archive/delete screens, because v1 excludes Data Mgmt.
- Supabase row/date delete UI, because v1 excludes Supabase Mgmt delete controls.
- Cycle Ops screens.
- Training Dataset Builder.
- Work Log upload UI.
- Grafana iframe or dashboard authoring.
- Multi-user roles, login, or LAN access UI.
- Theme picker.
- Drag-and-drop upload source selection.
- Bulk manual file selection.

## Main Components

- `AppShell`
- `SidebarNav`
- `TopStatusBar`
- `StatusChip`
- `SafetySummaryBanner`
- `DashboardPage`
- `UploadPage`
- `PreviewSummary`
- `PreviewTable`
- `PreviewStatusBadge`
- `JobProgressPanel`
- `JobFileTable`
- `EventLogTable`
- `AuditLogTable`
- `SettingsPage`
- `SettingsSection`
- `ConfigField`
- `SourceBadge`
- `RuntimeStatusPanel`
- `ErrorBanner`
- `EmptyState`
- `LoadingTableRows`

## Design QA Checklist

Before v1 acceptance:

- Dashboard first viewport clearly answers safe/attention/blocked/running.
- Upload cannot start from stale, missing, blocked, or risky preview state.
- Partial overlap is visible and not silently uploaded.
- Background failure appears in Dashboard, Job Logs, and Audit Logs.
- Logs and Audit Logs are separate tabs with different column models.
- Settings env override is visible and read-only.
- Secret values are masked and redacted from audit/log display.
- Korean and English labels fit at 1366, 1024, 720, and 375 px widths.
- Preview table supports 200+ rows without layout shift.
- Active job SSE reconnect does not duplicate or lose visible events.
- Stop Supabase and Cancel Job are visually distinct from normal actions.
- Grafana is a link/status only, never iframe.
- No v1-excluded navigation item is visible.
- No landing-page hero, decorative gradient, nested card layout, or one-note palette.

## Design Review Scores

Initial inferred score before this plan: 5/10. The product direction was strong, but the UI surface was not decision-complete.

Final plan score: 9/10. The remaining 1 point depends on implementation screenshots and live design QA after React components exist.
