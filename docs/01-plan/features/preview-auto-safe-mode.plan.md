# preview-auto-safe-mode - Plan Document

> Version: 1.0.0 | Date: 2026-06-15 | Status: Draft
> Level: Dynamic

## 1. Overview

### 1.1 Purpose

Prevent repeated operational Upload Preview timeouts by making the normal operator Preview path automatically use a safe large-source budget when the active source is the approved operational source or the candidate scope is large.

### 1.2 Background

The current UI exposes a default Preview mode and a large-source mode. The default mode keeps the original fast budget, while the large-source mode uses a longer budget. The latest operational Preview timed out because the default profile was used against a source containing multiple large files and historical DB-full-match files.

## 2. Goals

- Automatically protect operational Preview from the small default timeout budget.
- Preserve fast/default behavior for small sources, tests, screenshots, and demo states where appropriate.
- Keep Start Upload safety gates unchanged.
- Make applied Preview mode visible enough for operators and reviewers.
- Avoid raw source path, file content, or credential exposure.

## 3. Non-Goals

- Do not run Upload Preview as part of implementation.
- Do not run Start Upload, Retry Failed, duplicate rerun, or full rollout.
- Do not add DB-full-match cache/skip in the first implementation.
- Do not redesign the Upload page.
- Do not change upload execution semantics.
- Do not perform DB, Supabase, or Docker lifecycle/destructive work.

## 4. Scope

### 4.1 In Scope

- Backend auto profile resolution for Preview options.
- Frontend operator-facing Preview mode adjustment.
- Tests for auto-upgrade and explicit bounded profile preservation.
- Minimal copy/i18n updates.
- Documentation of operational behavior and remaining controls.

### 4.2 Out of Scope

- Cached reconciliation skip for unchanged DB-full-match files.
- Per-file selected Preview.
- Edge upload worker changes.
- Start Upload flow changes.
- Production deploy or release/tag work.

## 5. Success Criteria

- Operational source Preview requests use the large-source-safe budget automatically.
- Explicit bounded QA profiles remain unchanged.
- Missing/unknown source state fails neutral and does not invent target counts.
- UI no longer depends on the operator remembering a large-source selector for normal operational Preview.
- Tests cover default, auto-upgraded, and explicit profile cases.
- Start Upload remains forbidden unless a completed Preview succeeds, target rows are reviewed, and the user separately approves.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Auto-upgrade hides intentional small-source diagnostics | Medium | Preserve explicit profile/test/demo paths and document applied mode. |
| Longer Preview takes more time on operator PC | Medium | Apply only to operational or large candidate scope; show expected longer runtime. |
| False confidence without cache invalidation | High | Defer cache/skip until strict DB/source fingerprinting exists. |
| UI wording implies upload approval | High | Keep Preview-only and Start Upload approval language separate. |

## 7. Validation Plan

- Backend targeted Preview option/profile tests.
- Frontend typecheck and build.
- i18n JSON parse.
- `git diff --check`.
- Marker scan for raw operational source data and credentials.
- Browser smoke only if it can be performed without Preview/Start Upload execution.

## 8. References

- `docs/136_operator_preview_reconciliation_scaling_plan.md`
- `docs/137_operator_preview_reconciliation_staging_reconciler.md`
- `docs/140_operator_large_source_upload_acceptance_summary.md`
- `docs/141_operator_preview_timeout_recurrence_investigation.md`
