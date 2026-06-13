# Operator Dashboard State Context Plan

Date: 2026-06-14 Asia/Seoul

Branch: `codex/operator-dashboard-state-context-plan`

Scope: docs-only implementation plan for Dashboard state context visibility

Verdict: `plan_ready_for_small_implementation_pr`

Match Rate: `100%`

## Summary

The Dashboard now uses real API-mode backend state, not scaffold mock data.
The remaining operational caveat is context visibility: the Dashboard can show
a real latest upload job from whichever active state DB the backend process is
using. If the backend is launched against a different state DB context than the
one expected by an operator or QA reviewer, the Dashboard can show a different
latest job/count while still being technically correct.

This document defines a small implementation plan to make that state context
visible without changing upload execution behavior.

## Problem Statement

API-mode Dashboard currently aggregates:

- latest upload job state from the active state DB;
- runtime readiness summary;
- safe audit summary.

That behavior is correct, but the UI does not clearly identify the state DB
context class behind the latest job. Operators can see a real success count and
still not know whether it came from the intended operator/package context, a
development context, or a QA recovery context.

This creates a human verification gap. It is not a mock-data bug. It is a
source-of-truth labeling problem.

## Non-Developer Explanation

Think of the Dashboard like a scoreboard. The scoreboard is no longer fake. It
shows real scores.

The remaining issue is that the scoreboard does not clearly say which game it
is watching. If the backend points to one saved history, the Dashboard shows one
latest upload. If it points to another saved history, it shows another latest
upload. Both can be real, but the operator needs to know which one is active
before using the result as evidence.

The improvement is simple: show the operator which state context the Dashboard
is using, and label the latest job with that same context. That reduces
confusion without resetting data or re-running uploads.

## Current Dashboard State Source

Current API-mode behavior, based on the merged Dashboard real-state work:

- `/api/dashboard` and `/api/dashboard/summary` read backend state in read-only
  mode.
- The latest upload job is read from the active state DB.
- Runtime readiness is included from the local runtime summary.
- Audit summary is redacted and omits raw params.
- Empty or missing state returns neutral unknown/empty Dashboard content instead
  of a fake running upload.

Current caveat, based on post-merge smoke and mock usage audit:

- Dashboard and Upload Job can agree with each other while still reflecting a
  different active state DB context than a reviewed QA evidence context.
- A different latest count is not automatically a Dashboard bug.
- The first check after unexpected Dashboard output should be backend process
  identity and active state DB context.

## Operator Confusion Scenarios

| Scenario | What The Operator Sees | Why It Is Confusing | Desired UI Signal |
| --- | --- | --- | --- |
| Expected accepted upload evidence exists in one state context, but backend is using another | Dashboard shows a different real latest count | Looks like upload evidence changed or disappeared | State context class and latest job context label |
| Development backend is left running in API mode | Dashboard shows real dev/latest state | Looks operational because API mode is active | Dev/operator/package mode distinction |
| State DB is empty or newly initialized by configuration | Dashboard shows neutral or empty latest job | Could be mistaken for data loss | Clear state source class and empty-state reason |
| Upload page and Dashboard agree on same wrong context | Screens appear internally consistent | Consistency hides the context mismatch | Shared context banner or runtime panel field |
| QA restored a previous Preview/job reference in a process-only context | Dashboard may not show that evidence later | Evidence seems inconsistent across sessions | Latest job source and backend identity summary |

## Improvement Candidates

### 1. Dashboard State Context Class

Add a small, non-secret field to the Dashboard runtime/state section:

- `State context: operator package`
- `State context: development`
- `State context: QA temporary`
- `State context: unknown`

The label must be class-based only. It must not expose raw state DB paths,
machine-local paths, or connection strings.

### 2. Latest Job Source/Context Label

Add a compact context label near the current/latest job card:

- latest job status;
- latest job row counts;
- latest job state context class;
- backend startup identity class if already safely available.

This helps the operator distinguish "latest job from the active operator state"
from "latest job from a dev or recovery state".

### 3. Settings Or Runtime Panel State DB Source

Expose the same state context class in Settings or the Runtime panel. This gives
operators and QA reviewers a second place to verify the backend state source
without reading logs.

The field should use sanitized classifications only:

- configured;
- default app state;
- package-local;
- temporary QA;
- unknown;
- inaccessible.

### 4. Package/Operator Mode Versus Dev State

Show whether the frontend/backend pair appears to be running in operator/package
mode or development mode. This should be based on existing safe build/runtime
metadata where possible.

The UI should avoid alarm language when a development context is intentional,
but it should make the distinction visible.

## What Not To Do

Do not use destructive or upload-side actions to resolve a display context
question:

- Do not reset the DB.
- Do not initialize, delete, truncate, drop, or prune database data.
- Do not copy, delete, or replace state DB files as part of Dashboard display
  work.
- Do not re-run Upload Preview.
- Do not run Start Upload.
- Do not run Retry Failed.
- Do not run duplicate rerun.
- Do not run authenticated Edge upload calls.
- Do not run full rollout.

The correct fix is context visibility, not data mutation.

## Acceptance Criteria

The next implementation PR should be accepted only if all criteria are met:

1. API-mode Dashboard shows a sanitized active state DB context class.
2. Latest upload job display includes or links to the same context class.
3. Settings or Runtime view exposes the same sanitized state context class.
4. Empty/missing state remains neutral and does not fabricate a running job.
5. Frontend mock/default mode and `?state=` demo states remain unchanged.
6. No raw state DB path, source path, source filename, source content, DB URL,
   token, Authorization header, JWT, or secret appears in API responses, UI, logs,
   tests, docs, or screenshot artifacts.
7. Upload execution behavior is unchanged.
8. Tests cover at least:
   - operator/package context class;
   - dev/default context class;
   - unknown/inaccessible context class;
   - latest succeeded job with context label;
   - empty state with context label;
   - redaction contract.
9. Browser smoke covers Dashboard, Upload, Logs/Audit, and Settings in API mode.
10. Documentation explains that context mismatch is not a reason to reset DB or
    retry upload.

## Next Implementation PR Scope

Recommended branch:

`codex/operator-dashboard-state-context-visibility`

Recommended implementation scope:

- Backend: add sanitized state context metadata to Dashboard and runtime/config
  responses where it naturally belongs.
- Frontend: display the context class in Dashboard latest job area and Settings
  or Runtime panel.
- Tests: add backend contract tests and frontend type/build validation.
- Docs: update README or a short operator note after implementation.

Out of scope for that PR:

- upload execution changes;
- Preview/Start/Retry behavior changes;
- DB reset or state file migration;
- Edge runtime work;
- broad UI redesign.

## Validation Plan For This Docs-Only PR

- `git diff --check`
- marker scan for raw source path/name/content, DB URL, token, Authorization
  header, JWT, and secret markers
- PR file scope check: `docs/131_operator_dashboard_state_context_plan.md` only

## Explicitly Not Performed

- Upload Preview
- Start Upload
- Retry Failed
- duplicate rerun
- authenticated Edge upload call
- full rollout
- DB reset/init/delete/truncate/drop/prune
- Supabase lifecycle or destructive operation
- Docker lifecycle or destructive operation
- protected untracked item commit/delete

## Next Action

Open this docs-only plan for review. If approved and merged, implement
Dashboard state context visibility in a separate small PR before relying on
Dashboard latest job/counts as standalone operator evidence.
