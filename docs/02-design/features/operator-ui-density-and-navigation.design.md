# operator-ui-density-and-navigation - Design Document

> Version: 0.1.0 | Date: 2026-06-22 | Status: Ready for P0 Implementation
> Level: Dynamic | Plan: docs/01-plan/features/operator-ui-density-and-navigation.plan.md

---

## 1. Overview

### 1.1 Purpose

Define the frontend design for operator UI density, table inspection, logs
layout, settings copy cleanup, and sidebar navigation. This design is
documentation-first and does not authorize operational mutations or backend
workflow changes.

### 1.2 Design Goals

- Preserve the existing operator console architecture.
- Improve data inspection without reducing font size as the primary fix.
- Keep required operational values visible or inspectable.
- Share table behavior between Upload Preview and Audit Logs where it reduces
  duplicated implementation.
- Keep mobile behavior explicit instead of relying on accidental wrapping.
- Follow `DESIGN.md` as a restrained visual reference: quiet surfaces, single
  blue action accent, clear typography, and low decorative noise.

### 1.3 Design Constraints

- This is an operator console, not a marketing site. Do not add hero sections,
  photography-led layouts, decorative product tiles, large whitespace, or
  gradient backgrounds.
- Preserve the existing dense dashboard and panel model.
- Use existing app tokens and CSS modules before adding new visual grammar.
- Keep card radius at the existing operator system scale, prefer 8px or less
  unless an existing component already requires otherwise.
- Use icons for compact controls where available, with accessible names.
- Do not introduce a second accent color beyond the existing blue action/focus
  color family.

## 2. Architecture

### 2.1 Current Frontend Surfaces

| Surface | Current file | Planned role |
| --- | --- | --- |
| App shell/sidebar | `frontend/src/components/app/AppShell.tsx`, `SidebarNav.tsx` | Add collapsed desktop shell and mobile drawer state. |
| Dashboard runtime table | `frontend/src/components/dashboard/RuntimeCheckPanel.tsx` | Apply table layout fixes and responsive widths. |
| Upload Preview table | `frontend/src/pages/UploadPage.tsx` | Extract table rendering into screen-specific table using shared primitives. |
| Job Logs | `frontend/src/pages/LogsPage.tsx` | Rework panel height and viewer controls. |
| Audit Logs | `frontend/src/pages/LogsPage.tsx` | Extract audit table rendering into screen-specific table using shared primitives. |
| Settings copy | `frontend/src/pages/SettingsPage.tsx`, `frontend/src/i18n/locales/*.json` | Simplify default operator copy and move diagnostics to advanced UI. |
| CSS | `frontend/src/styles/layout.css`, `tables.css`, `components.css` | Add shell, table, drawer, popover, pagination, and log viewer styles. |

### 2.2 Proposed Shared Components

Add frontend-only table primitives under `frontend/src/components/table/` or a
similar local path:

```text
ResizableDataTable
- column definitions
- default/min/max widths
- drag resize handle
- persisted widths
- reset widths
- horizontal scroll container
- sticky header
- empty state
- pagination slot
- cell renderer hooks

TablePagination
- page size selector
- desktop full pagination
- compact mobile pagination
- page-size localStorage persistence

CellDetailPopover
- click/focus triggered full value
- copy button when allowed
- safe rendering of redacted values
```

Keep screen-specific concerns in wrappers:

```text
UploadPreviewTable
- status badges
- file/path/date/reason renderers
- reason detail display
- new Preview resets page to 1

AuditLogTable
- result badges
- target renderer
- parameter chip renderer
- error detail renderer
- filter changes reset page to 1
```

Do not force every dashboard table into the shared abstraction during the first
pass. The runtime table only needs targeted CSS/layout fixes unless shared table
use is clearly cheaper.

## 3. State And Persistence

### 3.1 LocalStorage Keys

Use explicit versioned keys so future migrations can reset stale UI preference
state safely:

| Preference | Suggested key | Value |
| --- | --- | --- |
| Sidebar collapsed | `ewc.ui.sidebarCollapsed.v1` | `"true"` / `"false"` |
| Upload Preview page size | `ewc.ui.uploadPreview.pageSize.v1` | number |
| Upload Preview column widths | `ewc.ui.uploadPreview.columnWidths.v1` | JSON object |
| Audit Logs page size | `ewc.ui.auditLogs.pageSize.v1` | number |
| Audit Logs column widths | `ewc.ui.auditLogs.columnWidths.v1` | JSON object |
| Job Logs wrap | `ewc.ui.jobLogs.wrap.v1` | `"true"` / `"false"` |
| Job Logs autoscroll | `ewc.ui.jobLogs.autoscroll.v1` | `"true"` / `"false"` |

Persistence failure must be non-fatal. If localStorage is unavailable, fall back
to defaults without showing an error.

### 3.2 Page Reset Rules

- Upload Preview current page resets to 1 when the Preview result identity
  changes.
- Audit Logs current page resets to 1 when filters or page size change.
- Current page is not persisted.
- Sidebar collapsed state is persisted.

## 4. Screen Design

### 4.1 App Shell And Sidebar

Desktop layout:

```text
app-shell
- sidebar
- main-shell
  - top-status-bar
  - page content
```

Implementation notes:

- `app-shell` remains grid-based.
- Expanded sidebar width uses the existing 220px token or a nearby 216px value.
- Collapsed sidebar width uses 64-72px.
- Main content occupies the remaining viewport width.
- Main content scrolls independently of the sidebar on desktop.
- Collapsed nav buttons show icons only, retain accessible labels, and use
  native or custom tooltips for menu names.

Mobile layout:

- Sidebar is hidden by default.
- A top control opens a drawer.
- Drawer overlays content.
- Outside click and Escape close the drawer.
- Main content is full width.
- Drawer state is not persisted as "open"; only desktop collapsed state is
  persisted.

### 4.2 Dashboard Runtime Table

Targeted table changes:

- Add a stable min width for the last-check column.
- Apply nowrap to the last-check header and timestamp cell.
- Keep `.table-scroll` horizontal overflow.
- Let detail column shrink before time/status columns.
- On desktop, adjust the runtime/warning card grid so runtime receives more
  width when space is constrained.

Acceptance:

- The Korean or English last-check header and values do not wrap on desktop.
- Narrow screens scroll horizontally rather than wrapping timestamp values.

### 4.3 Upload Preview Table

Column behavior:

| Column class | Behavior |
| --- | --- |
| status/action | compact, fixed/min width |
| filename | nowrap, ellipsis, detail popover |
| path | nowrap, ellipsis, detail popover, copy action when safe |
| modified/file date | nowrap, fixed/min width |
| numeric counts | nowrap, right-aligned |
| reason | 2-3 line clamp, detail popover |

Pagination:

- Default: 15 rows.
- Options: 5 / 15 / 30 / 60 / 100.
- Desktop: first/previous/numbers/next/last.
- Narrow: previous, current/total, next, page-size selector.

Column resizing:

- Header boundary drag changes width.
- Width is clamped between min/max.
- Widths are saved after resize.
- Reset button clears the localStorage key and restores defaults.

Full-value inspection:

- Trigger by click and keyboard focus/activation.
- Popover or side detail panel shows the full value.
- Path copy action copies the rendered value only. It does not log, audit, or
  persist the value.

### 4.4 Job Logs

Layout:

- `.page--logs` becomes a vertical flex container.
- Tabs remain at the top.
- Active Job Logs panel follows immediately after tabs.
- `.logs-panel` and `.job-log-viewer` fill the remaining viewport space.
- Desktop minimum terminal height: 420px.
- Large viewport target: 60-70vh.

Autoscroll behavior:

- Default autoscroll is on.
- If the operator scrolls away from the bottom, do not force scroll to bottom.
- Provide a jump-to-bottom control when the viewer is not at bottom.

Optional controls:

- wrap on/off
- level filter
- copy visible logs

### 4.5 Audit Logs Table

Default column widths:

| Column | Width |
| --- | ---: |
| Time | 180px |
| Result | 120px |
| Action | 180px |
| Target | 220px |
| Actor | 150px |
| Job ID | 220px |
| Params | 360px minimum |
| Error | 260px |

Parameter rendering:

- Show up to three useful key/value chips in the cell.
- Show `+N` when more values exist.
- Clicking the cell or `+N` opens full parameter detail.
- Object and array values should render as nested safe structures when possible.
- `[redacted]` stays visibly redacted.
- Copy actions must not expose values beyond what the API already returned.

Error rendering:

- Show error code inline.
- Long localized message goes into detail popover/panel.
- The row should not become excessively tall due to error text.

Pagination:

- Use existing Audit API `limit` and `offset`.
- Default page size changes to 15 unless implementation risk argues for keeping
  backend default and only changing UI default after review.
- Options: 5 / 15 / 30 / 60 / 100.
- Filter changes reset page to 1.
- Current page is not persisted.

### 4.6 Settings Copy

Default operator copy should focus on status and available action:

```text
Connected
Unavailable
Saved
Save failed
Restart required
This setting cannot be changed here
Only status check, start, and stop are supported
```

Move diagnostics to advanced information:

- v1/v2 labels
- bootstrap/reset/cleanup details
- allowlist/command policy wording
- env override implementation details
- source class/target class/feature gate/schema/migration wording
- WSL path implementation details unless the operator must edit the field

The existing `settings.runtime.commandPolicyTitle` and
`settings.runtime.commandPolicy` strings are the first known cleanup target.

## 5. API And Data Model

No new backend endpoint is required.

No database schema change is required.

Allowed frontend state only:

- local React state for pagination and popovers
- localStorage for UI preferences
- existing Audit API `limit` and `offset`
- existing Upload Preview result data already loaded into the page

Do not add new audit records for UI-only inspection, resize, pagination, or
copy actions.

## 6. Security And Privacy

- Popovers and panels may show only data already present in the sanitized UI/API
  response.
- Do not query raw audit params, raw error message fields, operational source
  paths, DB URLs, tokens, Authorization headers, JWTs, or secrets.
- Existing redaction strings remain redacted in chips, panels, and copied text.
- localStorage must store only UI preferences, never cell values, paths,
  filenames, params, errors, tokens, or source configuration values.
- Do not write UI preference changes to backend config or audit.

## 7. Accessibility

- Sidebar collapse button has an accessible name and visible focus state.
- Mobile drawer traps focus while open or returns focus safely after close.
- Escape closes drawer and popovers.
- Resize handles have labels and are keyboard reachable when practical.
- Table detail popovers are reachable by keyboard.
- Icon-only controls use `aria-label` and tooltip text.
- Pagination controls expose current page and disabled states.
- Log viewer keeps `role="log"` and does not spam screen readers during large
  updates.

## 8. Test Plan

### 8.1 Static And Build Checks

- `git diff --check`
- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`

### 8.2 Browser QA Viewports

- 1920x1080
- 1600x900
- 1366x768
- 1024x768
- 768x1024
- 390x844

### 8.3 Browser Assertions

- Runtime last-check column does not wrap on desktop.
- Upload Preview filename/path/reason full values are inspectable.
- Upload Preview page size persists after reload.
- Upload Preview current page resets after a new Preview result.
- Audit Logs parameters and errors are inspectable.
- Audit Logs page size persists after reload.
- Audit Logs filters reset current page to 1.
- Column resize persists after reload and reset restores defaults.
- Sidebar collapsed state persists after reload.
- Mobile drawer opens, closes by outside click, and closes by Escape.
- Job Logs panel has at least 420px terminal height on desktop.
- Settings default view no longer shows command-policy implementation copy.

### 8.4 Regression Boundaries

- No Upload Preview request is triggered by opening detail UI or changing table
  preferences.
- No Start Upload, Retry Failed, Delete, Settings save, runtime start/stop, LAN,
  reset/cleanup, deployment, or operational DB action is triggered by this UI
  work.
- Existing mock-mode pages still render for screenshot QA.
- Existing API-mode calls continue to use the same endpoints and payload
  semantics.

## 9. Implementation Order

1. App shell/sidebar state and layout.
2. Table primitives for persisted widths, overflow, details, and pagination.
3. Upload Preview table wrapper.
4. Audit Logs table wrapper.
5. Dashboard runtime last-check column/layout fix.
6. Job Logs layout height and optional controls.
7. Settings copy cleanup and advanced-info placement.
8. Viewport screenshot QA and regression review.

## 10. Rollback

Before commit, rollback is `git restore` for the frontend files changed by the
implementation.

After commit, rollback is a normal git revert of the UI implementation commit.
Do not delete operational evidence, local state DB rows, Supabase data, Docker
state, package outputs, or AppData logs as rollback for this UI work.

## 11. Open Decisions

| Decision | Default recommendation |
| --- | --- |
| Upload Preview pagination source | Client-side display pagination over current Preview result rows. |
| Audit Logs default page size | 15 if backend behavior remains compatible; otherwise keep backend default until reviewed. |
| Popover vs side panel | Popover for short values; side panel for multi-field params/errors if layout becomes cramped. |
| Column resize keyboard behavior | At minimum provide reset and full-value inspection; add keyboard resize if implementation remains ergonomic. |
| Job Logs optional controls | Implement after base layout if low risk. |
