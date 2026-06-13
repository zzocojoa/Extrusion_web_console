# Operator New File Edge Recovery Upload Completion

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-new-file-edge-503-recovery-upload`

Scope: Stage 4 new-file Edge 503 recovery check and exactly one product upload
retry for Preview `prv_da7bfe752c18`

Verdict: `blocked_retry_failed_edge_503_no_db_mutation`

## Summary

The recovery upload gate was run against the reviewed Preview reference
`prv_da7bfe752c18`.

Preflight passed before upload:

- active backend identity was reachable and unchanged;
- `/api/config` target classes passed;
- runtime API, DB, Studio, and Edge were ready;
- direct Edge no-auth `GET` and `POST {}` returned `401` auth-class;
- active backend source class matched the approved operational source class;
- source shape remained `3` CSV, `3` eligible, `file_date_missing=0`,
  zero-row `0`, total physical rows `52494`;
- approved Preview was still the latest completed Preview;
- Preview status was `succeeded`, `dbStatus=reachable`, target files `1`,
  already-in-DB files `2`, and upload target rows `15096`;
- failed job `upl_944412eae94d` was still the only job for this Preview and
  had one failed target file with `15096` rows, processed/uploaded/accepted
  `0 / 0 / 0`;
- no retry job existed before this task.

Because the failed job safely represented the same target file and the same
`15096` rows, the normal product `Retry Failed` path was selected instead of
creating a second Start Upload from the Preview.

`Retry Failed` was executed exactly once. It created job `upl_89cbe4f2e447`.
The retry job failed with the same `edge_503` class before any rows were
processed, uploaded, or accepted. DB row-count delta remained `0`.

No additional retry, duplicate rerun, Start Upload, Preview, authenticated
manual Edge call, or full rollout was performed.

## Explicitly Not Performed

- additional Upload Preview;
- Start Upload from Preview after the retry;
- second Retry Failed;
- duplicate rerun;
- manual authenticated Edge upload call;
- full rollout beyond the approved `15096` target rows;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset;
- Docker delete or prune;
- operational source mutation, rename, or deletion.

## Branch And Baseline

| Check | Result |
| --- | --- |
| Local `main` equals `origin/main` before branch | yes |
| Base commit | `840a690ae9ee8f30fdc5179a3950cd5b04727749` |
| Working branch | `codex/operator-new-file-edge-503-recovery-upload` |
| Report scope | docs/120 only |

Protected untracked files and local report drafts were left uncommitted.

## Read-Only Preflight

| Gate | Result |
| --- | --- |
| `/api/health` reachable | yes |
| Backend startup id | `api_690c15af41a7` |
| Backend process id | `20968` |
| `/api/config` response shape | `items_array` |
| Target-class status | `passed` |
| Target-class reason | `target_class_preflight_passed` |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | true |
| Runtime API | `ready` |
| Runtime DB | `ready` |
| Runtime Studio | `ready` |
| Runtime Edge | `ready` |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Edge no-auth `GET` | `401` auth-class |
| Edge no-auth `POST {}` | `401` auth-class |
| DB read-only row count before retry | `58737` |

No Edge runtime recovery action was run because Edge route and runtime readiness
gates were already passing at the no-auth/auth-boundary level.

## Source And Preview Confirmation

| Check | Result |
| --- | ---: |
| Active backend source class | `unc` |
| Active source setting source | `env` |
| Active source exists | yes |
| Active source is directory | yes |
| CSV file count | `3` |
| Filename-date eligible CSV count | `3` |
| `file_date_missing` | `0` |
| Zero-row files | `0` |
| Total physical source rows | `52494` |

| Preview check | Result |
| --- | --- |
| Approved Preview run id | `prv_da7bfe752c18` |
| Latest completed Preview run id | `prv_da7bfe752c18` |
| Preview final status | `succeeded` |
| Preview `dbStatus` | `reachable` |
| Preview item count | `3` |
| Target files | `1` |
| Already-in-DB files | `2` |
| Excluded files | `0` |
| Risky files | `0` |
| Reason classes | `db_full_match:2`, `db_no_match:1` |
| Upload target rows | `15096` |

## Retry Target Confirmation

| Check | Before retry |
| --- | ---: |
| Upload jobs total | `5` |
| Active upload jobs | `0` |
| Jobs for Preview `prv_da7bfe752c18` | `1` |
| Retry jobs for failed job `upl_944412eae94d` | `0` |
| `upload.start` audit rows | `5` |
| `upload.retry` audit rows | `0` |

| Failed source job check | Result |
| --- | --- |
| Source failed job id | `upl_944412eae94d` |
| Source job Preview id | `prv_da7bfe752c18` |
| Source job status | `failed` |
| Source job total files | `1` |
| Source job failed files | `1` |
| Source job total rows | `15096` |
| Source job processed/uploaded/accepted | `0 / 0 / 0` |
| Source file retry count before this task | `0` |
| Source file error class | `edge_503` |

This satisfied the preference for `Retry Failed`: the retry copied the same
failed target file and did not create a second Start Upload from the Preview.

## Upload Execution

| Item | Result |
| --- | --- |
| Product upload path used | `Retry Failed` |
| Retry POST execution count | `1` |
| Retry POST HTTP status | `202` |
| Retry job id | `upl_89cbe4f2e447` |
| Retry job mode | `retry_failed` |
| Retry-of job id | `upl_944412eae94d` |
| Preview run id | `prv_da7bfe752c18` |
| Final status | `failed` |
| Error code | `upload_failed` |
| File error class | `edge_503` |
| Target files | `1` |
| Succeeded files | `0` |
| Failed files | `1` |
| Cancelled files | `0` |
| Total rows | `15096` |
| Processed rows | `0` |
| Uploaded rows | `0` |
| Accepted rows | `0` |
| Warning count | `0` |

The retry reproduced the Edge 503 failure before upload progress advanced.

## DB And Audit Evidence

| Check | Before | After | Delta |
| --- | ---: | ---: | ---: |
| DB row count | `58737` | `58737` | `0` |
| Upload jobs total | `5` | `6` | `1` |
| Active upload jobs | `0` | `0` | `0` |
| Jobs for Preview | `1` | `2` | `1` |
| Retry jobs for failed job | `0` | `1` | `1` |
| `upload.start` audit rows | `5` | `5` | `0` |
| `upload.retry` audit rows | `0` | `1` | `1` |

The single new job and single new `upload.retry` audit row are expected from
the approved Retry Failed attempt. No DB data rows were inserted.

## Job Event Evidence

| Event class | Result |
| --- | --- |
| `job.created` | observed |
| `job.started` | observed |
| `file.started` | observed |
| `file.failed` | observed with `edge_503` class |
| `job.failed` | observed |

## Post-Execution Runtime Evidence

| Gate | Result |
| --- | --- |
| Runtime API | `ready` |
| Runtime DB | `ready` |
| Runtime Studio | `ready` |
| Runtime Edge | `ready` |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Edge no-auth `GET` after retry | `401` auth-class |
| Edge no-auth `POST {}` after retry | `401` auth-class |

Read-only sanitized container/log class inspection after the retry showed:

| Component | Status class | Sanitized log class |
| --- | --- | --- |
| Supabase gateway | `up`, healthy | function-route `503` class present |
| Supabase Edge runtime | `up` | function marker and generic error classes present |
| Supabase DB | `up`, healthy | no DB error class in inspected window |
| Supabase REST | `up` | no DB or server error class in inspected window |

This keeps the root cause classification at the gateway/Edge worker path. The
core DB and REST services did not show matching DB error classes in the
inspected window.

## Decision

| Gate | Result |
| --- | --- |
| Fresh backend guard | passed |
| Runtime gates | passed |
| DB/Edge target-class alignment | passed |
| Active source scope | passed |
| Active Preview reference | passed |
| Retry target count confirmation | passed |
| Edge no-auth auth-class before retry | passed |
| Exactly one product upload retry | passed |
| Retry job succeeded | no |
| DB delta `0` | passed |
| Additional retry allowed now | no |
| Additional Start Upload allowed now | no |
| Additional Preview allowed now | no |

The task result is a blocker, not a completed upload. The authenticated Edge
upload path still returns `503` even when no-auth route readiness and backend
runtime gates pass.

## Redaction Result

This document records only sanitized source classes, target classes, backend
identity fields, safe run/job identifiers, component status classes, and
aggregate counts.

- no raw source locator;
- no raw source filename;
- no source row content;
- no full local source path;
- no raw DB URL;
- no token, Authorization header, JWT, or secret;
- no raw Docker or Supabase status output;
- no raw Edge logs.

## Validation

| Check | Result |
| --- | --- |
| Targeted backend runtime/config/upload job tests | `42 passed` |
| `npm run typecheck` | passed from `frontend/` |
| `npm run build:api` | passed from `frontend/` |
| `npm run build` | passed from `frontend/` |
| `git diff --check` | passed |
| New document raw marker scan | passed |
| PR file scope | docs/120 only |

Validation note: root-level `npm run typecheck` and `npm run build:api` were
attempted first and failed with `package.json` not found because this repository
keeps npm scripts under `frontend/`. The same checks passed from the correct
package directory.

## Next Safe Action

Do not retry again.

The next task should be a focused Edge gateway/worker investigation or an
approved Edge runtime recovery task. A future upload attempt needs fresh
runtime gates, fresh Preview/reference confirmation, and separate explicit
approval. The allowed upload target remains bounded to the reviewed `15096`
rows unless a new Preview-only gate is separately approved.
