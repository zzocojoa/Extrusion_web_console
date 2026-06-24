# upload-preview-preferences-and-audit-panel-polish - Design Document

> Version: 1.0.0 | Date: 2026-06-24 | Status: Ready for Review
> Level: Dynamic | Plan: docs/01-plan/features/upload-preview-preferences-and-audit-panel-polish.plan.md

---

## 1. Overview

This design adds a small frontend-only preference for Upload Preview range selection and adjusts Audit Logs layout styles so the table and pagination remain visually inside the audit panel surface.

No backend endpoint, database migration, package script, launcher, Supabase, Docker, LAN, or operational workflow change is required.

## 2. Upload Preview Range Preference

### 2.1 Storage Key

```ts
const uploadPreviewRangeModeStorageKey = "ewc.ui.uploadPreview.rangeMode.v1";
```

### 2.2 Allowed Values

Use a single source of truth near `UploadPage`:

```ts
const previewRangeModes = [
  "today",
  "yesterday",
  "last_2_days",
  "last_7_days",
  "last_30_days",
  "folder_all",
  "custom",
] as const satisfies readonly PreviewRangeMode[];
```

### 2.3 Read Behavior

`useState` initializes `rangeMode` with `readStoredPreviewRangeMode()`.

Rules:

- SSR/non-browser fallback: `today`
- missing value fallback: `today`
- invalid value fallback: `today`
- valid value: return as `PreviewRangeMode`

The reader must catch localStorage failures.

### 2.4 Write Behavior

When `rangeMode` changes, write only the enum string to localStorage.

Do not write:

- custom dates
- source class
- preview run id
- result rows
- file names or paths
- audit params or errors
- token, secret, Authorization header, JWT, DB URL

Write failures are ignored because preference persistence must not block the Upload page.

### 2.5 Custom Date Behavior

If stored value is `custom`, the page shows the custom date controls but leaves `startDate` and `endDate` blank. This is safer than persisting date values and makes the operator re-confirm the date scope before running Preview.

## 3. Audit Logs Panel Surface

### 3.1 Current Structure

```tsx
<section className="panel logs-panel logs-panel--audit">
  <div className="panel__header" />
  <div className="audit-toolbar" />
  <div className="audit-summary-strip" />
  <AuditTable />
  <TablePagination />
</section>
```

`AuditTable` renders `ResizableDataTable`, and pagination is a sibling. The panel should own the surface for both.

### 3.2 CSS Strategy

Use existing design tokens:

- `var(--color-surface)`
- `var(--color-border)`
- `var(--radius-lg)` or existing panel radius

Recommended classes:

```css
.logs-panel--audit {
  overflow: visible;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
}

.logs-panel--audit .resizable-table {
  background: var(--color-surface);
}

.logs-panel--audit .table-scroll {
  background: var(--color-surface);
}

.logs-panel--audit .table-pagination {
  flex-shrink: 0;
  background: var(--color-surface);
}
```

If the panel needs to fill available page height on desktop, prefer `min-height` over fixed height so responsive layouts and long result pages still work.

### 3.3 Responsive Behavior

- Keep horizontal scroll inside `.table-scroll`.
- Do not force the table wider than its existing min-width.
- Pagination can wrap on narrow screens using existing `.table-pagination` rules.
- Empty/loading/error states keep their current minimum height and sit inside the same panel.

## 4. Tests

Static and build:

- `git diff --check`
- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`

Browser QA:

- `cd frontend; $env:EWC_SCREENSHOT_QA_PORT='5176'; npm run qa:screenshots`

Manual smoke:

- Persist `last_30_days` or `folder_all`, navigate away/back, confirm restored.
- Set invalid `ewc.ui.uploadPreview.rangeMode.v1`, reload, confirm `today`.
- Persist `custom`, reload, confirm custom controls are visible and date fields are empty.
- Inspect `.panel.logs-panel.logs-panel--audit` with enough audit rows to confirm background contains table and pagination.

## 5. Security And Operations

- localStorage stores only a validated UI enum.
- No operator secrets or raw source paths are stored.
- No audit record is created for preference changes.
- No operational command or mutation is executed.

## 6. Rollback

Revert the frontend/docs change commit. No DB rollback, state cleanup, or package cleanup is required. Existing localStorage keys can be left in place; ignored or invalid values fall back safely.
