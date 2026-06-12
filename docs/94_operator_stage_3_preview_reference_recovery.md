# Operator Stage 3 Preview Reference Recovery QA

## Summary

- Date: 2026-06-13
- Branch: `codex/operator-stage-3-preview-reference-recovery`
- Base commit: `d4ba62effe0f4d369355d7aa0918cd8a02cf4ae9`
- QA mode: report-only Preview reference recovery
- Stage: Stage 3 Profile A corrected bounded source
- Sanitized source label: `profile_a_corrected_bounded_source`
- Source scope class: `batch_bounded`
- Source kind class: `plc`
- Upload Preview executions during this QA: `1`
- Start Upload executions during this QA: `0`
- Duplicate rerun executions: `0`
- Retry Failed executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Verdict: `blocked`

The fresh backend guard, runtime target alignment, and corrected source scope
checks passed. The recovery Preview was then executed exactly once against the
same active backend state DB.

The Preview did not create a usable uploadable reference. It finished as
`timed_out` with `dbStatus=not_checked`, `target=0`, and one `risky/timeout`
item. Because this triggered a Stage 3 stop condition, no second Preview was
run and Start Upload remains blocked.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- second Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun or forced duplicate upload;
- manual Edge authenticated upload call;
- full operational dataset rollout;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- operational source mutation or deletion;
- production deploy;
- GitHub Release or tag creation;
- feature branch deletion.

## Fresh Backend Identity

| Check | Result |
| --- | --- |
| QA API `/api/health` | reachable |
| Health `startup_id` | `api_439f9a7ea290` |
| Health `started_at` | `2026-06-12T15:03:09.733443+00:00` |
| Health `process_id` | `44988` |
| QA port pre-start state | not listening |
| QA port post-run state | not listening |
| Stale backend reuse | not observed |

The launched backend served a fresh non-secret `startup_id`. The process was
stopped after evidence collection. Supabase and Docker runtime state were not
stopped, reset, deleted, or cleaned.

## Runtime Preflight

| Check | Result |
| --- | --- |
| API reachable | passed |
| DB direct read | reachable |
| Studio TCP check | reachable |
| Runtime API core services | API, DB, Studio, and Edge ready |
| Edge no-auth `GET` | auth-class |
| Edge no-auth `POST {}` | auth-class |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | `true` |
| Upload target preflight status | `passed` |
| Upload target preflight reason | `target_class_preflight_passed` |
| DB/Edge target class alignment | aligned independent |

No Authorization header was used for Edge probes. No raw DB URL, token,
Authorization header, JWT, source path, source filename, source content, or full
local path is recorded.

## Corrected Source Recheck

| Check | Result |
| --- | --- |
| Sanitized source label | `profile_a_corrected_bounded_source` |
| Source scope class | `batch_bounded` |
| Source kind class | `plc` |
| Source exists | yes |
| Source is directory | yes |
| CSV file count | `1` |
| Physical source row count | `24515` |
| Eligible file count | `1` |
| `file_date_missing` count | `0` |
| Profile A file range `1-3` | passed |
| Profile A row range `1-25000` | passed |
| Full operational dataset used | no |
| Operational source modified | no |

The source itself still matches the corrected Profile A bounded source evidence.
The recovery failure happened during Preview execution, not source eligibility.

## Preview Reference Recovery Result

| Metric | Result |
| --- | ---: |
| Preview execution count | `1` |
| Preview create status | `202` |
| Preview final status | `timed_out` |
| `dbStatus` | `not_checked` |
| Total files | `1` |
| Target files | `0` |
| Upload target rows | `0` |
| Already-in-db files | `0` |
| Excluded files | `0` |
| Risky files | `1` |
| Partial-overlap files | `0` |
| Failed files | `0` |
| Invalid files | `0` |
| `file_date_missing` count | `0` |
| Reason class | `timeout` |

The active backend state DB now has the recovery Preview as its latest Preview,
but that latest Preview is not uploadable. It is not valid input for Stage 3
Start Upload.

## Active State DB Evidence

| Check | Result |
| --- | ---: |
| Preview runs before recovery | `1` |
| Preview runs after recovery | `2` |
| Preview run delta | `1` |
| Upload jobs after recovery | `0` |
| `upload.start` audit rows after recovery | `0` |
| Latest Preview class | `timed_out/risky` |
| Latest Preview target files | `0` |
| Latest Preview upload target rows | `0` |

This proves the recovery Preview was created in the active backend state DB, but
it did not become a corrected uploadable reference.

## DB Non-Mutation Evidence

| Check | Result |
| --- | ---: |
| Independent DB row count before Preview | `20225` |
| Independent DB row count after Preview | `20225` |
| DB row-count delta after Preview | `0` |
| Processed rows | `0` |
| Uploaded rows | `0` |
| Accepted rows | `0` |

Preview did not mutate the independent DB.

## Start Upload Go/No-Go

| Question | Answer |
| --- | --- |
| Did Preview run exactly once? | yes |
| Did Preview complete successfully? | no |
| Did Preview reach `dbStatus=reachable`? | no |
| Are target files and rows uploadable? | no |
| Did Preview mutate DB rows? | no |
| Is Start Upload allowed now? | no |
| Was Start Upload executed in this QA? | no |

Start Upload remains blocked. Running it from this active state would violate
the `dbStatus=reachable`, target file, target row, and stop-condition gates.

## Stop Condition Result

| Stop condition | Result |
| --- | --- |
| Preview target `0` | triggered |
| `dbStatus != reachable` | triggered |
| Recovery Preview timed out | triggered |
| DB delta after Preview != `0` | not triggered |
| `file_date_missing > 0` | not triggered |
| DB/Edge target mismatch | not triggered |
| Edge 503 | not triggered |
| Start Upload 1회 초과 risk | avoided, Start Upload not executed |
| Raw source path/name/content/secret exposure risk | not triggered |

No second Preview was run after the timeout. The exact-once Preview constraint
was preserved.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Row content recorded | no |
| Full local path recorded | no |
| Raw DB URL recorded | no |
| Token, Authorization header, or JWT recorded | no |
| Operational source modified | no |

## Validation

| Command or check | Result |
| --- | --- |
| Fresh backend guard | passed |
| Runtime target class preflight | passed |
| Corrected source recheck | passed |
| Upload Preview execution count | exactly `1` |
| Start Upload execution count | `0` |
| Upload job count in active state | `0` |
| DB row-count delta after Preview | `0` |
| Targeted backend package/runtime/upload tests | passed, `182` tests |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed, `1` Playwright test |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | passed, QA report document only |

## Next Step

Do not proceed to Start Upload. Do not run full rollout.

Recommended next action is an investigation or procedure update for the Preview
timeout class. A future attempt must be explicitly approved because this QA has
already consumed its one allowed Preview execution.

If a new recovery attempt is approved, it should change only the Preview runtime
parameters or procedure needed to avoid timeout, keep the same corrected bounded
source class, and still keep Start Upload blocked until a `succeeded`,
`dbStatus=reachable`, `target=1`, `uploadRows=24515` Preview exists in the same
active backend state.
