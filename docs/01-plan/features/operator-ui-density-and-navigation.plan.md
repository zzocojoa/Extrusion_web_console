# operator-ui-density-and-navigation - Plan Document

> Version: 0.2.0 | Date: 2026-06-22 | Status: Implemented Candidate
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose

Improve the operator console UI so operators can inspect operational data without
losing values to narrow columns, ellipsis-only cells, excessive whitespace, or
navigation movement during page scroll.

This is an operator productivity and evidence-readability improvement. It must
make the same data easier to inspect without changing Upload Preview, Start
Upload, Retry Failed, Delete, Settings save, Supabase, LAN, package, or database
semantics.

### 1.2 Background

The current UI works functionally, but several screens are hard to use for real
operations:

- Dashboard runtime timestamps can wrap in the check-time column.
- Upload Preview rows can truncate filenames, paths, reasons, and timestamps.
- Job Logs sit too low on the Logs page and have limited vertical reading space.
- Audit Logs parameter chips can hide evidence values that operators must check.
- Settings exposes implementation-heavy text to normal operators.
- The sidebar scrolls with content and cannot be collapsed.

The product direction remains the local, dense, quiet operator console described
by `docs/00_product_scope.md`, `docs/03_ui_ux_plan.md`,
`docs/04_design_system.md`, and `DESIGN.md`. `DESIGN.md` is treated as the
visual reference for restrained typography, calm surfaces, a single blue action
accent, and low visual noise. It must not be interpreted as permission to add
marketing heroes, product tiles, cinematic spacing, or decorative imagery.

## 2. Goals

### 2.1 Primary Goals

- [ ] Keep required operational values visible or one action away from full
      inspection.
- [ ] Add reusable table behavior for Upload Preview and Audit Logs where
      practical.
- [ ] Support resizable columns, persisted column widths, sticky headers,
      horizontal overflow, and page-size persistence.
- [ ] Keep the sidebar accessible on desktop and usable as a drawer on narrow
      screens.
- [ ] Increase Job Logs usable height and reduce dead space.
- [ ] Simplify Settings copy so normal operators see action-oriented wording.

### 2.2 Non-Goals

- Do not change Upload Preview execution, reconciliation, file eligibility, or
  row classification logic.
- Do not change Start Upload, Retry Failed, Delete, or operational DB mutation
  behavior.
- Do not change Supabase settings, feature gates, LAN exposure, packaging
  policy, or schema/migration behavior.
- Do not expose raw secrets, DB URLs, raw operational paths, raw SQL, tokens,
  Authorization headers, JWTs, or unredacted audit values.
- Do not solve readability by shrinking fonts below the existing operator
  design system density.
- Do not persist operational data in localStorage. localStorage may store only
  UI preferences such as column widths, page sizes, and sidebar state. It must
  never store paths, filenames, params, errors, source configuration, DB URLs,
  tokens, or secrets.

## 3. Scope

### 3.1 In Scope

- Dashboard runtime status table layout and last-check column nowrap behavior.
- Upload Preview table rendering, detail inspection, copy affordances, and
  client-side display pagination.
- Job Logs layout height, spacing, and optional viewer controls.
- Audit Logs table rendering, parameter detail inspection, and existing API
  pagination UI.
- Settings page operator-facing copy cleanup and advanced-information hiding.
- Sidebar fixed/collapsible desktop behavior and mobile drawer behavior.
- Shared frontend table utilities and localStorage-backed UI preferences.
- Mock-mode and API-mode browser QA without running operational mutations.

### 3.2 Baseline Boundary

This document is the P0 implementation baseline only. It does not approve or
request Upload Preview, Start Upload, Retry Failed, Delete, Settings save,
feature gate enablement, Supabase lifecycle work, LAN exposure, schema
migration, deployment, package policy changes, operational folder access, or
operational DB mutation.

### 3.3 Out of Scope

- Backend Upload Preview or Upload Job behavior changes.
- Audit log storage, redaction, or query semantics changes, except consuming the
  existing safe API fields in the UI.
- Runtime start/stop command behavior changes.
- Feature gate enablement.
- Operational folder access, operational DB access, or Supabase lifecycle work.
- Deployment or package policy changes.

## 4. Functional Requirements

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| UI-1 | Dashboard Runtime Status last-check column keeps header and date/time values on one line on desktop, with horizontal table overflow on narrow screens. | P0 | Completed |
| UI-2 | Upload Preview table supports horizontal scroll, non-wrapping key columns, full-value inspection for filename/path/reason, page-size persistence, and page reset on new Preview. | P0 | Completed |
| UI-3 | Job Logs panel sits directly under the Logs tabs and uses most remaining viewport height, with internal scrolling. | P1 | Completed |
| UI-4 | Audit Logs table supports readable parameter evidence through chips plus full-detail inspection while preserving redaction. | P0 | Completed |
| UI-5 | Settings page removes or hides implementation-heavy operator copy behind advanced information. | P2 | Completed |
| UI-6 | Sidebar remains available on desktop, supports collapsed/expanded state persistence, and uses a mobile drawer on narrow screens. | P0 | Completed |
| UI-7 | Upload Preview and Audit Logs share a reusable table utility where the abstractions reduce duplicated behavior. | P1 | Completed |

## 5. Non-Functional Requirements

| Category | Criteria | Measurement Method |
| --- | --- | --- |
| Operator readability | Required values are visible, non-wrapped, or available through tooltip/popover/detail panel. | Browser QA at required viewports |
| Responsiveness | Desktop uses dense layouts; narrow screens use horizontal scroll or drawer/compact pagination without breaking layout. | Playwright screenshots |
| Persistence | Column widths, page sizes, and sidebar collapsed state survive reload. | LocalStorage tests/browser QA |
| Security | Detail panels and copy actions preserve existing redaction boundaries. | Marker scan and manual review |
| Accessibility | Resizers, popovers, drawer, pagination, and icon buttons are keyboard reachable and labelled. | Playwright + manual keyboard pass |
| Maintainability | Upload Preview and Audit Logs reuse table primitives where appropriate without forcing mismatched renderers. | Code review |

## 6. Screen Requirements

### 6.1 Dashboard Runtime Status

- Give the runtime card enough desktop width relative to the warning/failure
  card.
- Set a minimum width for the last-check column in the 112-132px range.
- Apply nowrap to the last-check header and time values.
- Let detail/status columns shrink first.
- On narrow screens, stack cards and allow table-level horizontal scrolling.

### 6.2 Upload Preview Table

- Use horizontal overflow for the table container.
- Keep filename, path, modified date, file date, and numeric columns on one
  line.
- Allow reason to show a short multi-line preview while exposing full reason in
  a detail popover or panel.
- Provide full-value inspection for truncated filename/path values.
- Provide copy action for path-like values only through safe UI, without adding
  raw values to logs or audit records.
- Add display pagination:
  - default page size: 15
  - options: 5 / 15 / 30 / 60 / 100
  - page size persisted in localStorage
  - current page resets to 1 when a new Preview result is loaded
  - desktop pagination may show first/previous/numbers/next/last
  - narrow pagination uses compact current/total controls

### 6.3 Job Logs

- Place the Job Logs panel immediately below the Logs tabs.
- Reduce dead vertical spacing between tabs and content.
- Let the panel fill remaining viewport height through flex layout.
- Keep the log body internally scrollable.
- Desktop terminal minimum height: 420px.
- Large desktop target height: 60-70vh.
- Optional controls after the base layout fix:
  - jump to bottom
  - auto-scroll toggle
  - wrap toggle
  - log-level filter
  - copy visible logs

### 6.4 Audit Logs

- Use the same table utility as Upload Preview when it fits.
- Keep sticky header and horizontal overflow.
- Persist page size with options 5 / 15 / 30 / 60 / 100.
- Reset current page to 1 on filter change; do not persist current page.
- Parameter column shows the most important chips plus a `+N` affordance.
- Full parameter detail view must show all key/value pairs, preserve redaction,
  and render object values structurally instead of `[object Object]` where
  possible.
- Error cells must expose full error code/message without forcing the table row
  to become tall.

### 6.5 Settings Copy

- Remove implementation-heavy text from the default operator view.
- Move necessary diagnostics to an advanced/collapsible area.
- Search and review at least these terms before implementation:
  `v1`, `v2`, `bootstrap`, `reset`, `cleanup`, `command policy`,
  `allowlist`, `env`, `override`, `source class`, `target class`,
  `feature gate`, `migration`, `schema`, `WSL`, `maintainer`, `admin`.
- Replace the visible runtime command-policy copy with shorter operator wording
  or hide it behind advanced information.

### 6.6 Sidebar

- Desktop:
  - left navigation remains available while main content scrolls
  - expanded width near 216-220px
  - collapsed width near 64-72px
  - collapsed state shows icons only with tooltip/accessible labels
  - collapsed state persists in localStorage
- Mobile/narrow screens:
  - sidebar is hidden by default
  - top control opens drawer
  - outside click and Escape close the drawer
  - overlay is shown while drawer is open
  - main content uses full width

## 7. Success Criteria

- [x] Runtime last-check header and date/time values do not wrap on desktop.
- [x] Upload Preview long filename, path, and reason can be inspected in full.
- [x] Upload Preview pagination works and page size survives reload.
- [x] Audit Logs parameters and errors can be inspected in full.
- [x] Audit Logs pagination works and page size survives reload.
- [x] Column resize works on target tables and widths survive reload.
- [x] Reset column widths is available.
- [x] Sidebar collapsed/expanded state survives reload.
- [x] Mobile sidebar drawer opens/closes with button, outside click, and Escape.
- [x] Job Logs panel is directly below tabs and uses a substantially taller
      reading area.
- [x] Settings default page no longer surfaces unnecessary technical policy copy.
- [x] Browser QA covers 1920x1080, 1600x900, 1366x768, 1024x768, 768x1024,
      and 390x844.
- [x] Frontend typecheck and build pass.
- [x] Existing upload/delete/runtime behavior remains unchanged.

## 8. Risks And Mitigations

| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Reusable table abstraction becomes too generic and slows delivery. | Medium | Medium | Build only shared primitives needed by Upload Preview and Audit Logs; keep screen-specific renderers. |
| Popovers expose values that should remain redacted. | High | Medium | Render only already-redacted API/UI values; do not access raw params or raw backend diagnostics. |
| Sidebar fixed layout breaks mobile or table widths. | Medium | Medium | Implement layout shell first, then verify table widths at all required viewports. |
| Pagination accidentally changes Preview execution limits. | High | Low | Keep Upload Preview pagination client-side over displayed result rows only. |
| Column resize hurts keyboard accessibility. | Medium | Medium | Provide keyboard-accessible reset and ensure resize handles have labels; do not make resize the only way to inspect values. |
| Settings copy removal hides useful operator status. | Medium | Low | Keep action-oriented statuses visible; move diagnostics to advanced information. |

## 9. Implementation Priority

`Ready for P0 Implementation` means the Plan/Design pair is ready to start the
first implementation branch. It does not reclassify every listed requirement as
P0. The first implementation branch should complete only the P0 group below
unless the scope is explicitly expanded; Job Logs remain P1 and Settings copy
cleanup remains P2.

### P0

1. Sidebar fixed/collapsible shell.
2. Upload Preview table readability and full-value inspection.
3. Audit Logs parameter/error inspection.

### P1

4. Upload Preview pagination.
5. Audit Logs pagination.
6. Job Logs height and spacing.

### P2

7. Resizable table commonization if not already delivered in P0/P1.
8. Column width persistence and reset.
9. Settings copy cleanup.
10. Optional Job Logs controls.

## 10. Validation Plan

- `git diff --check`
- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`
- Playwright screenshot QA at:
  - 1920x1080
  - 1600x900
  - 1366x768
  - 1024x768
  - 768x1024
  - 390x844
- Browser checks:
  - runtime timestamp nowrap
  - Upload Preview full filename/path/reason inspection
  - Upload Preview pagination and persisted page size
  - Audit Logs parameter/error inspection
  - Audit Logs pagination and persisted page size
  - column width resize and reset
  - sidebar persistence and mobile drawer
  - Job Logs height
  - Settings copy cleanup

## 11. Implementation Evidence

Implemented on branch `codex/operator-ui-density-navigation` as frontend-only
UI work. No backend upload/delete/runtime logic, operational DB access,
Supabase lifecycle action, feature gate enablement, LAN exposure, packaging
policy, deployment, or schema migration was changed.

Validation completed:

- `cd frontend; npm run typecheck`
- `cd frontend; npm run build:api`
- `cd frontend; npm run qa:screenshots`
- `git diff --check`
- Changed-frontend diff marker scan for raw DB URL markers, credential header
  markers, service role values, anon key assignments, and Windows user/source
  paths.

Browser interaction smoke additionally confirmed Upload Preview column resize
persists only numeric UI preference data, full-value popovers open, Job Logs
height is above the 420px desktop minimum, Audit Logs parameter detail opens,
sidebar collapsed state persists, and the mobile drawer opens.

## 12. References

- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/03_ui_ux_plan.md`
- `docs/04_design_system.md`
- `docs/06_dashboard_implementation_spec.md`
- `frontend/src/components/app/AppShell.tsx`
- `frontend/src/components/app/SidebarNav.tsx`
- `frontend/src/components/dashboard/RuntimeCheckPanel.tsx`
- `frontend/src/pages/UploadPage.tsx`
- `frontend/src/pages/LogsPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/styles/layout.css`
- `frontend/src/styles/tables.css`
- `frontend/src/styles/components.css`
