# Backend-Served Responsive Overflow Fix Design

## Design Direction

Follow `DESIGN.md`: quiet operator console, dense information, restrained
surfaces, no marketing layout, no decorative media, and no font-size reduction
as the primary fix. The UI should preserve operational clarity while fitting
small screens.

## Layout Strategy

### Topbar

- Desktop keeps a single-row topbar.
- The page title area no longer renders the former subtitle line. Dashboard,
  Upload, Logs, and Settings should show only the page title plus the status
  chips.
- Below `900px`, status chips may wrap instead of horizontal scrolling out of
  view.
- Below `720px`, the app shell top row becomes content-sized and the status
  chip group moves to a second row inside the topbar.
- Status chip text is contained with ellipsis when a chip label is longer than
  the available row.

### Dashboard Status Matrix

- Desktop keeps the five-column matrix.
- Mid-width keeps the existing three-column matrix.
- Mobile uses an auto-fit grid with no horizontal card overflow.
- Status cells may stack vertically, but each cell remains within the content
  column.
- The dashboard safety summary removes fixed-height pressure on mobile so
  wrapped status text stays inside the card.

### Upload Actions

- Desktop actions remain inline with wrapping.
- Mobile Upload Preview actions become a one-column grid.
- Mobile Upload Job actions use auto-fit columns when space allows and fall
  back to one column at narrow widths.
- Upload Job progress metric cards use responsive grid tracks, not horizontal
  scrolling, so row counts remain visible at `390px`.
- The Already in DB hard delete status panel uses direct card padding and
  key-value metric groups so latest job result values do not split away from
  their labels or feel clipped on mobile.

### Table Pagination

- Desktop pagination keeps full controls and numeric pages.
- Mobile hides the numeric page list, keeps the compact page indicator, and
  constrains first/previous/next/last buttons to compact 44px controls.
- Pagination can wrap to multiple rows, but the control group must not extend
  beyond the viewport.
- Resizable table action buttons, such as reset column widths, stack to the
  available mobile width instead of extending past the panel edge.

## Verification

`npm run qa:backend-served-responsive` should inspect these views at every
target width:

- Dashboard, with 10 second wait.
- Upload Preview.
- Upload Job.
- Logs Job.
- Audit Logs.
- Settings.

The script should fail if critical selectors such as `.topbar__status`,
`.status-chip`, `.dashboard-status-matrix`, `.upload-preview__actions`,
`.upload-job__metrics`, `.upload-job__actions`, `.table-pagination`, or
`.settings-save-bar__actions` extend outside `window.innerWidth`. Dense table
cells inside `.table-scroll` remain horizontally scrollable by design.
Expected navigation cancellations are reported as `ignoredFailedRequests`;
any other request failure is reported as `unexpectedFailedRequests` and fails
the run.

`npm run qa:backend-served-screenshots` should capture Dashboard, Upload
Preview, Upload Job, Logs Job, Audit Logs, and Settings at top, middle, and
bottom scroll positions for every target width. The expected output is `126`
screenshots plus a `summary.json` with `layoutIssueCount: 0` and
`unexpectedFailedRequests: []`. By default, artifacts are written below
Node's `os.tmpdir()`; `EWC_RESPONSIVE_SCREENSHOT_DIR` may override the output
directory for handoff or CI.

## Non-Goals

This design does not change Upload Preview semantics, Start Upload, Retry
Failed, Delete, Settings save, Supabase runtime behavior, Docker behavior, LAN
exposure, package generation, deployment, or operational database state.
