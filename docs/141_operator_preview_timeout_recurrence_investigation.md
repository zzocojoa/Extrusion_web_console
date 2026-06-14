# Operator Preview Timeout Recurrence Investigation

> Date: 2026-06-15
> Scope: read-only investigation and implementation planning
> Verdict: `implementation_required_before_next_large_source_preview`
> Match Rate: `94%`

## Non-Developer Summary

새 운영 CSV가 추가될 때 Preview가 반복해서 timeout 되는 주된 이유는 데이터나 DB가 깨졌기 때문이 아닙니다.

현재 기본 Preview는 빠른 확인용 시간 제한을 그대로 사용합니다. 운영 source처럼 큰 CSV가 섞인 폴더에서는 이 기본 제한이 너무 짧습니다. 더 큰 문제는 새 파일 1개를 확인할 때도 기존에 이미 DB와 일치한다고 확인된 큰 파일들을 다시 읽고 DB와 다시 대조한다는 점입니다.

그래서 운영자가 `Large source` 모드를 직접 고르지 않으면, Preview는 매번 제한 시간 안에 끝나기 어렵습니다. Start Upload는 여전히 금지 상태이며, 성공한 Preview와 target row 검토, 별도 승인이 없으면 진행하면 안 됩니다.

## Investigation Boundary

Performed:

- Read-only backend health/config/runtime inspection.
- Read-only latest Preview state inspection.
- Read-only code inspection for Preview deadline and reconciliation behavior.
- Documentation-only planning.

Not performed:

- Upload Preview.
- Start Upload.
- Retry Failed.
- Duplicate rerun.
- Authenticated Edge upload call.
- Full rollout.
- DB reset, delete, truncate, migration, cleanup, or prune.
- Supabase or Docker lifecycle/destructive work.
- Operational CSV mutation.

## Current Evidence

Worktree and runtime sync evidence:

- Branch: `codex/preview-auto-safe-mode-investigation`.
- Local branch head: `6db5497912711789110802395578e4d0e1e4add6`.
- `origin/main`: `6db5497912711789110802395578e4d0e1e4add6`.
- Local branch was created from current `origin/main` for investigation.
- Backend health startup identity: `api_3f9cc6b24c94`.
- Backend process identity: `42252`.
- Frontend was reachable in API mode through the local backend-served app.
- Built frontend bundle contains the large-source Preview mode code path.

Runtime evidence:

- Backend health: reachable.
- Active source class: `approved_operational_source_class`.
- Runtime target classes: passed.
- API, DB, Studio, and Edge core readiness: ready.
- Overall runtime caveat: non-core observability attention only.

Latest Preview evidence:

- Preview status: `timed_out`.
- `dbStatus`: `not_checked`.
- Total files: `8`.
- Target files: `1`.
- Already-in-DB files: `4`.
- Risky files: `2`.
- Excluded files: `1`.
- Upload target rows reported by the incomplete run: `711488`.
- Timeout stage: `before_extract`.
- Run duration: about `120s`.
- Options profile: `default`.
- Default budget: `120s` run limit and `30s` file limit.
- Options included `chunkRows=20000`, `forceFullScan=false`, `sampleRows=200`, and `stableLagMinutes=3`.

Important interpretation:

- The latest timed-out Preview is not valid upload evidence.
- The target row count from that incomplete run must not be used to approve Start Upload.
- `dbStatus=not_checked` means the run ended before a reliable final DB reconciliation verdict.

### Item-Level Sanitized Evidence

The latest run processed files in the selected source scope, not only the newly added target file.

| Item | File date class | Status | Reason | Rows | Local keys | DB matches | Upload rows | Key timing / progress |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | dated | `already_in_db` | `db_full_match` | 21769 | 21769 | 21769 | 0 | extract about 0.6s, DB match about 1.5s, temp-table complete |
| 2 | dated | `already_in_db` | `db_full_match` | 24888 | 24888 | 24888 | 0 | extract about 0.6s, DB match about 1.8s, temp-table complete |
| 3 | dated | `already_in_db` | `db_full_match` | 15096 | 15096 | 15096 | 0 | extract about 0.5s, DB match about 1.4s, temp-table complete |
| 4 | dated | `already_in_db` | `db_full_match` | 17179 | 17179 | 17179 | 0 | extract about 0.5s, DB match about 1.3s, temp-table complete |
| 5 | dated | `excluded` | `outside_date_range` | not read | not read | not checked | 0 | metadata-only exclusion |
| 6 | dated large historical file | `risky` | `timeout` | 902440 | 902440 | 0 | 0 | extract about 24.7s; timeout during DB match staging after 290000 of 902440 keys |
| 7 | dated small remaining file | `risky` | `timeout` | 0 | 0 | 0 | 0 | run deadline reached before extraction |
| 8 | dated new target file | `target` | `db_no_match` | 711488 | 711488 | 0 | 711488 | extract about 18.7s, DB match about 47.5s, temp-table complete |

Run-level timeout:

- Run timeout stage: `before_extract`.
- Item-level timeout stages: one `db_match`, one `before_extract`.
- DB progress confirms staging/temp-table reconciliation was active.
- The 902440-row historical file reached `stage_keys` and staged only 290000 keys before the run budget expired.

## Code Path Findings

The Preview service uses a run deadline derived from request options. With the default profile, the run deadline is 120 seconds.

When the deadline expires before the next candidate starts extraction, remaining files are marked with `timeoutStage=before_extract`, and the run finishes as `timed_out`.

DB reconciliation uses the staging/temp-table strategy. That confirms the PR #137-style reconciler is active. However, the service still performs per-file extraction and DB key reconciliation for existing large files in the selected source scope.

The PR #148 extraction fix is also unlikely to be missing from the active path. The large historical file extraction completed in about 25 seconds, which matches the expected post-fix range and does not look like the previous per-row SQLite cancel-check bottleneck.

The newest runtime behavior is therefore not a regression to the older extraction or non-staging reconciliation path. The recurrence is caused by the selected Preview profile and repeated full reconciliation of historical large files.

## Root Cause

Root cause classification: `operator_default_preview_profile_too_small_for_operational_source_with_repeated_full_reconciliation`.

Contributing causes:

- Default Preview is optimized for fast/small checks.
- Operational source contains multiple large files.
- Existing DB-full-match files still consume extraction and reconciliation time.
- New target file processing is queued behind or beside historical full-match reconciliation work.
- Operator workflow can still invoke default Preview instead of large-source mode.

Weakened hypotheses:

- Runtime DB/Edge target drift: weakened by current targetClasses passed evidence.
- Source binding mismatch: weakened by approved source class evidence.
- Edge worker failure: not relevant to Preview reconciliation.
- PR #148 extraction fix regression: weakened by large file extraction timing staying in the expected range.

## Why Adding a CSV Repeats the Timeout

The current Preview gate evaluates the selected source scope as a set. When a new CSV is added, Preview does not only reconcile the new file. It scans the source, revalidates historical candidates, extracts keys from DB-full-match files, and reconciles them with the database again.

This preserves duplicate safety, but it means every new file addition can trigger repeated work on old large files. With the default budget, a single new large target plus one old large full-match file can exceed the run deadline even when the database and parser are healthy.

## Option Review

| Option | Assessment | Decision |
| --- | --- | --- |
| Keep default and large mode as-is | Unsafe for operations because the operator must remember the correct mode. | Reject |
| Remove default mode entirely | Safer for operations, but could slow developer/small-source diagnostics. | Partial |
| Automatically select safe mode for operational source | Best immediate fix. Keeps small/test defaults while protecting operational Preview. | Adopt |
| Cache/skip unchanged DB-full-match files | Valuable, but needs strict DB/source invalidation to avoid false duplicate confidence. | Defer to second PR |
| Per-file selected Preview | Useful later for diagnosis, but not sufficient as the main operating gate. | Defer |

## Recommended Implementation Direction

Implement automatic safe mode for operational source Preview.

Minimum behavior:

- Normal operator Preview should automatically use large-source-safe options when the active source class is the approved operational source or the candidate scope is large.
- The UI should not require operators to choose `Large source` for routine operations.
- Advanced/manual profile choice may remain for diagnostics, screenshot QA, and controlled test flows.
- Start Upload gates must remain unchanged.
- If a Preview uses automatic safe mode, the response and UI should show that the safe mode was applied.

Safe default thresholds:

- Use large-source budget when source class is operational.
- Use large-source budget when candidate file count or known row estimate indicates a large source.
- Keep explicit bounded QA profiles unchanged.
- Preserve demo/mock mode behavior.

## Cache / Skip Decision

Do not implement DB-full-match skip in the first fix.

Reason:

- Skipping unchanged files can reduce repeated work substantially.
- But a wrong cache hit could hide a DB reset, import drift, or source replacement.
- A safe skip needs a DB context fingerprint and file signature validation, not only filename/date.

Second-step cache requirements:

- Match source class, file date, size, mtime/signature, row count, local key count, first/last timestamp, and device summary.
- Invalidate on DB context change, target class change, reset/import evidence, or changed latest accepted upload state.
- Surface skipped-full-match counts separately from freshly reconciled counts.
- Keep Start Upload blocked unless the current run finishes `succeeded` with `dbStatus=reachable`.

## Proposed Minimal PR Scope

Backend:

- Add an auto profile resolver for upload Preview requests.
- Preserve `default` semantics for explicit test/demo/default calls where appropriate.
- Return sanitized applied-profile metadata if the request is upgraded to safe mode.
- Add tests for operational source auto-upgrade and bounded profile preservation.

Frontend:

- Change the operator-facing default to automatic safe Preview.
- Keep manual profile controls behind a diagnostic/advanced affordance or preserve them only for non-operational contexts.
- Display concise applied-mode/timing expectations.
- Do not change Start Upload behavior.

Docs:

- Add operator note that Preview mode is automatically sized for operational source.
- Keep explicit approval requirement for Start Upload.

## Test Plan

Automated checks:

- Backend profile resolver tests.
- Backend Preview DTO tests.
- Backend runtime/config tests where source class is used.
- Frontend typecheck.
- Frontend build.
- i18n JSON parse.
- `git diff --check`.
- Marker scan for raw source data and credentials.

Manual/read-only QA:

- Dashboard/Upload page loads in API mode.
- Operational Preview button shows automatic safe mode before execution.
- No Start Upload is executed during the UI smoke.

Not part of the implementation PR:

- Upload Preview execution.
- Start Upload execution.
- Retry or duplicate upload flows.
- DB/Supabase/Docker lifecycle work.

## Operational Controls

Continue to enforce:

- Fresh Preview-only gate before any future upload.
- Target row count review.
- Separate explicit approval for Start Upload.
- No retry after failure without root-cause review and separate approval.
- No full rollout wording for bounded or single-target upload evidence.

## Start Upload Go / No-Go

Current status: `no_go`.

Reason:

- Latest Preview timed out.
- `dbStatus` is `not_checked`.
- Risky file count is non-zero.
- Upload target rows came from an incomplete run.

Next safe action:

- Implement automatic safe Preview mode.
- After merge, run one explicitly approved Preview-only QA.
- Review the completed target counts before any Start Upload approval.

## Redaction Result

This document uses only sanitized source class labels, counts, statuses, timings, and run identifiers. It does not include raw operational source paths, source filenames, row content, raw connection values, or credentials.
