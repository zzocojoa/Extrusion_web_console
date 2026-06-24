# upload-preview-range-options - Design Document

> Version: 1.0.0 | Date: 2026-06-24 | Status: Ready for Review
> Level: Dynamic | Plan: docs/01-plan/features/upload-preview-range-options.plan.md

---

## 1. Overview

### 1.1 Purpose
Add three Upload Preview range modes while preserving the existing Preview safety model and approval-scope contract.

### 1.2 Design Goals
- Make the range contract explicit and identical in backend and frontend.
- Keep range selection as an operator-controlled Preview request parameter.
- Avoid raw path, filename, DB URL, token, Authorization, JWT, and secret exposure in new docs, logs, or UI copy.
- Avoid any operational Preview execution during implementation.

## 2. Range Contract

| Range mode | Date behavior | Date fields | Scanner behavior |
|------------|---------------|-------------|------------------|
| `today` | KST current day only | `null` | Existing behavior |
| `yesterday` | KST current day minus 1 only | `null` | Existing behavior |
| `last_2_days` | KST current day minus 1 through current day | `null` | Existing behavior |
| `last_7_days` | KST current day minus 6 through current day | `null` | Same scanner gates |
| `last_30_days` | KST current day minus 29 through current day | `null` | Same scanner gates |
| `folder_all` | No date-window exclusion after file-date metadata parses | `null` | Top-level configured CSV candidates only |
| `custom` | Inclusive `startDate` through `endDate` | required | Existing behavior |

`folder_all` is not recursive. It still uses configured source folders only, top-level `.csv` enumeration, stable lag, `maxFiles`, per-run and per-file timeouts, file lock checks, and file-date metadata parsing. Files with missing or invalid file-date metadata remain excluded.

## 3. Backend Design

### 3.1 Schema
Add enum values to `PreviewRangeMode`:

```python
last_7_days = "last_7_days"
last_30_days = "last_30_days"
folder_all = "folder_all"
```

Only `custom` requires `startDate` and `endDate`. `folder_all` must validate without dates.

### 3.2 Date Window
`date_window(request, now)` returns:

- `last_7_days`: `(current - 6 days, current)`
- `last_30_days`: `(current - 29 days, current)`
- `folder_all`: `(None, None)`

The scanner treats `(None, None)` as "do not exclude by date range" after file-date parsing succeeds.

### 3.3 Auto Safe Mode
`is_large_preview_range` returns `true` for:

- `last_2_days`
- `last_7_days`
- `last_30_days`
- `folder_all`
- `custom` ranges where `(endDate - startDate).days >= 1`

This keeps wider ranges on `large_source_operational` budgets unless the request already chose another explicit profile.

### 3.4 Approval Scope
Actual approval scope stores safe summary values only:

```json
{
  "rangeMode": "folder_all",
  "startDate": null,
  "endDate": null,
  "appliedProfile": "large_source_operational"
}
```

`preview_approval_mismatch_fields` continues comparing `rangeMode`, `startDate`, `endDate`, `appliedProfile`, and `sourceClasses`. New range modes must fail closed on mismatch before `preview_runs` creation.

## 4. Frontend Design

### 4.1 API Type
`PreviewRangeMode` gains:

```ts
"last_7_days" | "last_30_days" | "folder_all"
```

### 4.2 Upload Page
The range selector adds:

- Last 7 days
- Last 30 days
- Folder all

Custom date fields remain visible only for `custom`. All other range modes send `startDate=null` and `endDate=null`.

### 4.3 Label Mapping
Use an explicit label helper instead of deriving i18n keys directly from raw enum strings:

```ts
previewRangeLabelKey("last_7_days") -> "upload.range.last7Days"
previewRangeLabelKey("last_30_days") -> "upload.range.last30Days"
previewRangeLabelKey("folder_all") -> "upload.range.folderAll"
```

This keeps approval-scope labels readable and prevents missing translation keys.

### 4.4 Operator Copy
When `folder_all` is selected, show short copy that it is a Preview-only top-level folder scan and Start Upload still requires separate approval. Do not show raw configured folder values.

## 5. Security and Operations

- No new endpoint.
- No DB schema change.
- No operational Preview run.
- No Start Upload, Retry Failed, Delete, Settings save, Supabase cleanup, Docker cleanup, LAN, deploy, or operational DB mutation.
- No new raw source path, filename, DB URL, token, Authorization, JWT, or secret exposure.
- `folder_all` expands only candidate selection for Preview. It is not upload authorization.

## 6. Test Plan

### Backend
- DTO accepts `last_7_days`, `last_30_days`, and `folder_all` without custom dates.
- `custom` still requires both dates and valid order.
- `date_window` covers exact inclusive KST boundaries.
- `folder_all` scanner includes parseable top-level CSV files regardless of date, while excluding files missing file-date metadata.
- API auto safe-mode applies to `folder_all`.
- API approvalScope range mismatch blocks before run creation.

### Frontend
- Typecheck proves the range union and selector wiring compile.
- API-mode build succeeds.
- Screenshot QA confirms Upload page renders without console/network errors and without executing Preview.

## 7. Compatibility

Existing range modes retain behavior. Existing stored preview runs can keep historical `range_mode` values; no migration is required. New enum values are accepted only for new requests and are stored as strings in the existing state table.

Upload Preview `rangeMode` UI preference persistence is intentionally handled by
`docs/02-design/features/upload-preview-preferences-and-audit-panel-polish.design.md`
so the backend range contract and the frontend preference lifecycle remain
reviewable as separate changes.

## 8. Rollback

Revert the branch or merge commit. No DB rollback is required because there is no schema change.
