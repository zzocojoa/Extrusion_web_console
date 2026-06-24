# Backend-Served Responsive Overflow Fix Plan

## Purpose

Fix backend-served operator UI overflow and clipped controls at narrow
viewports without changing backend contracts or operator mutations.

This work targets the real `127.0.0.1:8000` served app, not only the Vite
development surface. The operator must be able to see primary status chips,
action buttons, and table pagination without controls extending outside the
viewport.

## Scope

In scope:

- Frontend CSS containment for topbar status chips.
- Removal of the topbar page subtitle line for Dashboard, Upload, Logs, and
  Settings.
- Dashboard runtime/upload status matrix responsive layout.
- Upload Preview and Upload Job action button containment.
- Upload Job progress metric card containment.
- Resizable table pagination containment.
- Backend-served browser QA at `390`, `480`, `640`, `834`, `1024`, `1280`,
  and `1440` px widths.
- Backend-served screenshot QA for each page/tab at top, middle, and bottom
  scroll positions.

Out of scope:

- Backend API contract changes.
- Upload Preview execution.
- Start Upload, Retry Failed, Delete, or Settings save.
- Supabase or Docker cleanup.
- LAN exposure, deploy, package, or NSIS generation.
- Operational DB mutation.

## Acceptance Criteria

- At `390/480/640/834/1024/1280/1440` px widths, Dashboard, Upload Preview,
  Upload Job, Logs Job, Audit Logs, and Settings keep primary buttons, status
  chips, and pagination controls within the viewport.
- Dashboard safety summary text, including wrapped upload count text, remains
  inside the summary card instead of clipping past the bottom edge.
- Upload Preview delete selection status text, including the latest delete job
  result sentence, keeps readable padding and wraps inside its card.
- Upload Job metric cards keep row counts inside the content column at narrow
  widths.
- Dashboard, Upload, Logs, and Settings do not render the former topbar
  subtitle line below the page title.
- Dashboard is checked after a 10 second wait so runtime cards are verified
  after live data has settled.
- `npm run qa:backend-served-screenshots` captures `126` backend-served images
  covering `7` viewports, `6` pages/tabs, and `3` scroll stops, and reports
  `layoutIssueCount: 0`.
- The screenshot QA default output directory is under Node's `os.tmpdir()` so
  it is portable across Windows users, CI, and developer machines; callers may
  override it with `EWC_RESPONSIVE_SCREENSHOT_DIR`.
- Backend-served QA separates expected navigation aborts into
  `ignoredFailedRequests` and fails on any non-empty `unexpectedFailedRequests`.
- Horizontal scroll remains allowed for dense data tables, but page controls
  around those tables must remain contained.
- `git diff --check` passes.
- `npm run typecheck` passes.
- `npm run build:api` passes.
- `npm run qa:screenshots` passes.
- `npm run qa:backend-served-responsive` passes against
  `http://127.0.0.1:8000/` with `unexpectedFailedRequests: []`.
- `npm run qa:backend-served-screenshots` passes against
  `http://127.0.0.1:8000/` with `unexpectedFailedRequests: []`.

## Risk And Mitigation

- Mobile topbar may grow taller. Mitigation: let the app shell top row size to
  content only at mobile widths.
- Buttons may become taller or stacked. Mitigation: use full-width stacked
  controls only on narrow widths.
- Dense table pagination may lose numeric page buttons on mobile. Mitigation:
  keep compact current page text and first/previous/next/last controls.

## Rollback

Before commit, restore the touched files:

```powershell
git restore frontend/package.json frontend/qa/backend-served-responsive-overflow.mjs frontend/qa/backend-served-responsive-screenshots.mjs frontend/src/components/app/AppShell.tsx frontend/src/components/app/TopStatusBar.tsx frontend/src/i18n/locales/en.json frontend/src/i18n/locales/ko.json frontend/src/pages/UploadPage.tsx frontend/src/styles/layout.css frontend/src/styles/components.css frontend/src/styles/tables.css CHANGELOG.md docs/01-plan/features/backend-served-responsive-overflow-fix.plan.md docs/02-design/features/backend-served-responsive-overflow-fix.design.md
```

After merge, revert the squash merge commit.
