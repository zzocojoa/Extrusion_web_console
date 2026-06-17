# Preview Approval Scope Contract Analysis

Date: 2026-06-17 Asia/Seoul

Verdict: `implemented_for_review`

Match Rate: `96%`

## Summary

This change adds a machine-checkable approval scope to Upload Preview creation.

Before a Preview run can be created, the frontend sends the operator-approved
source class, range, and expected applied profile. The backend compares that
approval scope with the active backend settings and the request after safe-mode
profile adjustment. Missing or mismatched scope is blocked before run creation
and recorded as a blocked `upload.preview` audit row.

## Non-Developer Explanation

Preview is still not an upload. It only checks what would be uploaded.

The new guard makes sure the Preview being started is the same Preview that was
approved: same source class, same date range, and same large-source mode. If the
backend has drifted to a different source or mode, Preview does not start.

Start Upload still needs a separate approval after Preview succeeds and target
rows are reviewed.

## Scope

Included:

- Preview request schema with `approvalScope`.
- Backend pre-run approval-scope validation.
- Blocked `upload.preview` audit evidence for missing or mismatched scope.
- Success/failure Preview audit evidence with expected/actual scope.
- Upload page API-mode request construction from `/api/config`.
- Operator-facing sanitized approval-scope label.
- Runbook and investigation follow-up documentation.

Not included:

- Upload Preview execution.
- Start Upload execution.
- Retry Failed execution.
- Full rollout.
- DB, Supabase, or Docker lifecycle work.
- Settings save.

## Compatibility

Risk: high.

Existing API-mode callers that post `/api/upload/preview` without
`approvalScope` are now blocked with `422 preview_approval_scope_required`.
The bundled frontend is updated in the same change to send the required scope.

Rollback path: revert this PR.

## Security And Safety

The approval scope records source class only, not raw source paths. It does not
include DB URLs, tokens, Authorization headers, JWT values, source filenames, or
source content.

The audit row records expected and actual scope for review without creating a
Preview run when the scope is missing or mismatched.

## Validation Plan

- Targeted backend Preview API/audit tests.
- Frontend typecheck and builds.
- i18n JSON parse.
- `git diff --check`.
- Marker scan for raw source path/content and credential material.

## Next Action

Review and merge this contract before using Preview as the gate for future
operational uploads. Any actual Preview-only run still requires separate
explicit approval.
