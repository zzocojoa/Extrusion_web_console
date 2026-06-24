# upload-preview-preferences-and-audit-panel-polish - Plan Document

> Version: 1.0.0 | Date: 2026-06-24 | Status: Ready for Review
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Improve operator continuity on the Upload Preview page and fix the Audit Logs panel surface so dense table content remains visually contained.

### 1.2 Background
Upload Preview now supports wider range modes, but the selected range still resets to `today` when the Upload page remounts. Audit Logs uses `ResizableDataTable` and shared pagination, but the panel surface does not visually wrap the full table and pagination area in the current layout.

## 2. Classification

| Item | Classification | Reason |
| --- | --- | --- |
| Upload Preview range selection persistence | Existing UI state retention improvement | No API or backend behavior change; stores only a safe UI preference. |
| Audit Logs panel surface height/background | CSS/layout improvement | No data or API behavior change; fixes visual containment. |

## 3. Goals

- [x] Persist the last selected Upload Preview `rangeMode` across page transitions and reloads.
- [x] Store only the range mode value, not custom dates, paths, filenames, params, errors, tokens, secrets, or DB URLs.
- [x] Validate stored range modes against the current frontend union and fail closed to `today` for invalid/stale values.
- [x] Keep `custom` dates empty after remount; only the mode is restored.
- [x] Make `logs-panel--audit` wrap toolbar, summary, table, empty/loading/error state, and pagination as one continuous `var(--color-surface)` panel.
- [x] Preserve responsive behavior and existing table horizontal scrolling.

## 4. Non-Goals

- Do not add backend persistence for Upload Preview UI preferences.
- Do not store `startDate` or `endDate`.
- Do not execute Upload Preview, Start Upload, Retry Failed, Delete, Settings save, Supabase/Docker cleanup, LAN/deploy, or operational DB mutation.
- Do not change Audit API pagination, filters, sort, or data contract.
- Do not regenerate package/NSIS outputs in this implementation task.

## 5. Functional Requirements

| ID | Requirement |
| --- | --- |
| R1 | On first load, Upload Preview uses stored `rangeMode` when it is one of `today`, `yesterday`, `last_2_days`, `last_7_days`, `last_30_days`, `folder_all`, or `custom`. |
| R2 | If stored `rangeMode` is missing or invalid, default to `today`. |
| R3 | Changing the Upload Preview range updates localStorage key `ewc.ui.uploadPreview.rangeMode.v1`. |
| R4 | Persistence failure must be non-fatal; localStorage denial or invalid values must not break Upload page rendering. |
| R5 | Only the mode is persisted. `custom` dates are not persisted and must remain blank on a new page mount. |
| R6 | Audit Logs panel background covers the filter toolbar, summary, table area, and pagination without leaving a visual gap below the table. |
| R7 | Empty/loading/error Audit states remain visually inside the same panel surface. |

## 6. Storage Policy

Allowed localStorage key:

```text
ewc.ui.uploadPreview.rangeMode.v1
```

Allowed values:

```text
today
yesterday
last_2_days
last_7_days
last_30_days
folder_all
custom
```

Disallowed values and data:

- raw local or network paths
- filenames
- custom `startDate` / `endDate`
- audit params or error text
- tokens, secrets, Authorization headers, JWTs, DB URLs
- source configuration values

## 7. Success Criteria

- [x] `rangeMode` survives page navigation/remount and browser reload.
- [x] Invalid localStorage values fall back to `today`.
- [x] `custom` mode can persist without persisting dates.
- [x] Audit Logs panel visually contains `ResizableDataTable` plus pagination on desktop and narrow viewports.
- [x] `git diff --check`, frontend typecheck, frontend API build, and screenshot QA pass.
- [x] No operational mutation or package generation is executed.

## 8. Risks And Mitigations

| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Persisting sensitive values by accident | High | Low | Store only a validated enum string. Do not serialize result rows, paths, params, or dates. |
| Stale localStorage value after enum changes | Low | Medium | Validate against explicit allowed set and fallback to `today`. |
| `custom` mode restores without dates | Medium | Medium | Accept as safe default; user must re-enter dates before Preview can run. |
| CSS fix breaks table horizontal scroll | Medium | Low | Keep `.table-scroll` ownership and test screenshot QA. |

## 9. Validation Plan

- `git diff --check`
- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`
- `cd frontend; $env:EWC_SCREENSHOT_QA_PORT='5176'; npm run qa:screenshots`
- Manual browser smoke:
  - change Upload Preview range, navigate away/back, confirm persisted mode
  - set invalid localStorage value, reload, confirm fallback to `today`
  - confirm `custom` restores the mode only, with empty date inputs
  - inspect Audit Logs panel surface around table and pagination

## 10. Rollback

- Before commit: `git restore` changed files and remove new docs.
- After merge: revert the feature commit.
- Do not delete operational evidence, local state DB rows, Supabase data, Docker state, package outputs, or AppData logs as rollback for this UI-only work.
