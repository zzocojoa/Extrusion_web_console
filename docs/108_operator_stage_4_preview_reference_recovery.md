# Operator Stage 4 Preview Reference Recovery

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-preview-reference-recovery`

Base: `f10bf1d0fbaaa132b0df47f0d76c05b15a0b14d8`

Scope: Stage 4 active source and Preview reference recovery investigation

Verdict: `recovered_with_caveats`

## Summary

PR #121 and PR #122 are both merged into `main`. This investigation did not run
Upload Preview or Start Upload.

The PR #122 mismatch was caused by QA runtime context drift, not by a failed
upload. The default active `.env` runtime state did not contain the PR #121
Preview run and pointed at a different source scope. The approved PR #121
Preview run still exists in a temporary QA state DB and can be made active again
with process-only backend environment restoration.

After process-only restore, `/api/upload/preview/latest` returned the PR #121
Preview reference again with `succeeded`, `dbStatus=reachable`, item status
counts `target:1` and `already_in_db:1`, and reason counts `db_no_match:1` and
`db_full_match:1`.

Start Upload remains forbidden until the user separately approves it after
reviewing this recovery report.

## Match Rate

| Gate | Result |
| --- | --- |
| PR #121 merged in `main` | passed |
| PR #122 merged in `main` | passed |
| Fresh backend identity captured | passed |
| DB/Edge target class alignment | passed |
| PR #121 Preview reference found | passed, in temp QA state DB |
| PR #121 Preview reference active after restore | passed |
| Approved target file count recovered | passed, `1` |
| Approved upload target rows recovered | passed, `17179` |
| Approved already-in-DB files recovered | passed, `1` |
| Source locator class restored | passed with caveat, process-only `unc` |
| Source accessibility restored | passed by Python/backend-style check |
| Durable default runtime state fixed | not changed |

Match rate: `10/12`

The two non-passing items are operational caveats, not evidence failures. The
recovery was process-only and did not rewrite the default config/state DB.

## Merged Evidence Gate

| Check | Result |
| --- | --- |
| Local `main` matched `origin/main` before branch | yes |
| PR #121 state | `MERGED` |
| PR #121 merge commit | `399400883a479b09595aff9222c60568ec27e54e` |
| PR #122 state | `MERGED` |
| PR #122 merge commit | `f10bf1d0fbaaa132b0df47f0d76c05b15a0b14d8` |
| QA branch created | yes |

## Fresh Backend Evidence

| Check | Result |
| --- | --- |
| Fresh backend startup id before restore | `api_a94bde27152e` |
| Fresh backend process id before restore | `49640` |
| Restored backend startup id | `api_d6286c36b861` |
| Restored backend process id | `8800` |
| Stale backend reuse observed | no |
| QA backend cleanup | stopped after evidence capture |

## Runtime And Target Class

| Check | Result |
| --- | --- |
| API reachable | passed |
| DB reachable | passed |
| Studio reachable | passed |
| Edge runtime reachable | passed |
| Runtime overall status | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | `true` |
| Target class preflight | `passed` |

## Default Active State Before Recovery

| Check | Result |
| --- | --- |
| Source config delivery | `.env` |
| Source locator class | `drive_letter` |
| Source accessible | yes |
| CSV count | `3` |
| Filename-date eligible CSV | `1` |
| `file_date_missing` count | `2` |
| Zero-row files | `0` |
| Total physical rows | `20223` |
| Latest Preview run | `prv_d670d87da757` |
| Latest Preview status | `succeeded` |
| Latest Preview `dbStatus` | `reachable` |
| Latest Preview target files | `0` |
| Latest Preview already-in-DB files | `1` |
| Latest Preview excluded files | `2` |
| Latest Preview upload target rows | `0` |
| Latest Preview reason counts | `db_full_match:1`, `file_date_missing:2` |

This state matches the PR #122 hard stop and does not match the approved PR #121
Preview evidence.

## State DB Read-Only Evidence

| Check | Default active state DB | Restored PR #121 state DB |
| --- | ---: | ---: |
| Preview run count | `15` | `1` |
| Preview item count | `31` | `2` |
| Upload job count | `4` | `0` |
| Upload jobs for PR #121 Preview | not present | `0` |
| `upload.start` audit count | `4` | `0` |
| `upload.preview` audit count | `12` | `1` |
| PR #121 Preview run present | no | yes |
| PR #122 mismatch run present | yes | no |

The PR #121 Preview reference is not recoverable from the default active state
DB. It is recoverable from the temporary QA state DB used by the PR #121
Preview-only run.

## Restored Preview Reference

| Check | Result |
| --- | --- |
| Preview run | `prv_93e72aa21581` |
| Preview status | `succeeded` |
| `dbStatus` | `reachable` |
| Total files | `2` |
| Target files | `1` |
| Already-in-DB files | `1` |
| Excluded files | `0` |
| Upload target rows | `17179` |
| DB matched rows | `20219` |
| Item status counts | `target:1`, `already_in_db:1` |
| Reason counts | `db_no_match:1`, `db_full_match:1` |
| Upload jobs for this Preview | `0` |
| `upload.start` audit in restored state | `0` |

No Preview rerun was required to recover this evidence.

## Root Cause Classification

Root cause: `qa_runtime_context_drift_with_temp_state_reference`

Contributing factors:

- PR #121 Preview evidence was created in a temporary QA state DB.
- The default `.env` runtime state DB did not contain the PR #121 Preview run.
- The default `.env` source scope differed from the refreshed Stage 4 source and
  produced the later PR #122 mismatch run.
- The PR #122 source-missing observation was partly a probe issue: the config API
  exposes `plcDataDir` under `items`, not as a top-level response field. Reading
  a top-level field can classify the source as missing even when the config item
  exists.

This is not an upload failure and not evidence of DB mutation.

## Recovery Decision

| Question | Answer |
| --- | --- |
| Is the PR #121 Preview reference recoverable? | yes, from temporary QA state DB |
| Can it be made active without Preview rerun? | yes, with process-only backend env restore |
| Is the default runtime state fixed by this investigation? | no |
| Is active source restored without DB/source mutation? | yes, for process-only restored backend |
| Is Preview-only rerun required immediately? | no, if using the recovered PR #121 state DB |
| Is Preview-only rerun required if temp QA DB is discarded? | yes |
| Is Start Upload allowed now? | no |

Start Upload remains no-go because this task did not include Start Upload
approval, and the recovery depends on a process-only state/source restoration
that should be reviewed before any upload attempt.

## Forbidden Operations Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset, start, or stop;
- Docker delete or prune;
- operational source mutation or deletion.

## Redaction Result

This report does not include raw source locators, source names, source row
content, DB URL, credential material, or connection strings. Source and state
locations are recorded only as sanitized classes.

## Validation

| Check | Result |
| --- | --- |
| Active config/runtime read-only checks | passed |
| Active state DB read-only inspection | passed |
| PR #121 temporary state DB read-only inspection | passed |
| PR #121 reference process-only restore check | passed |
| Targeted backend config/runtime/state tests | `52 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope check | passed, PR #123 includes this document only |

## Next Safe Action

Review this recovery report.

If accepted, request separate explicit approval for a Stage 4 Start Upload using
the recovered PR #121 Preview reference and the same process-only source/state
restore procedure. Before Start Upload, rerun fresh backend guard, runtime
target class alignment, source accessibility, and target count confirmation.

If the temporary QA state DB is no longer available, request separate explicit
approval for a Stage 4 Preview-only rerun instead.
