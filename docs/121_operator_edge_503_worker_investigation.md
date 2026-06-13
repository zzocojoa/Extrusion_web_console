# Operator Edge 503 Worker Investigation

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-edge-503-worker-investigation`

Scope: read-only investigation of repeated Stage 4 upload `edge_503`

Verdict: `blocked_edge_runtime_stale_function_mount_missing_entrypoint`

## Summary

The repeated Stage 4 upload failure is best classified as an Edge runtime worker
boot failure caused by a stale or missing function mount, not a source file,
Preview, DB reconciliation, backend target-class, or payload validation issue.

Both product upload attempts reached the Edge upload path and failed before any
row progress:

- Start Upload job `upl_944412eae94d` failed with `edge_503`;
- Retry Failed job `upl_89cbe4f2e447` also failed with `edge_503`;
- processed/uploaded/accepted stayed `0 / 0 / 0`;
- DB row count stayed `58737`, so DB delta stayed `0`.

No additional Upload Preview, Start Upload, Retry Failed, duplicate rerun,
authenticated manual Edge call, full rollout, DB mutation, Supabase reset, or
Docker destructive action was performed during this investigation.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated manual Edge upload call;
- full rollout;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset;
- Supabase start or stop;
- Docker delete, prune, or lifecycle operation;
- operational source mutation, rename, or deletion.

## Baseline

| Check | Result |
| --- | --- |
| Local `main` equals `origin/main` before branch | yes |
| Base commit | `dbd391572da73f767dca68b5af0a8c824d4efdf2` |
| Working branch | `codex/operator-edge-503-worker-investigation` |
| PR #128 merge commit present | yes |
| Report scope | docs/121 only |

Protected untracked files and local report drafts were left uncommitted.

## Failed Upload Evidence

| Check | Start Upload job | Retry job |
| --- | --- | --- |
| Job id | `upl_944412eae94d` | `upl_89cbe4f2e447` |
| Mode | `preview_targets` | `retry_failed` |
| Preview run id | `prv_da7bfe752c18` | `prv_da7bfe752c18` |
| Retry-of job id | n/a | `upl_944412eae94d` |
| Final status | `failed` | `failed` |
| Error code | `upload_failed` | `upload_failed` |
| File error class | `edge_503` | `edge_503` |
| Target files | `1` | `1` |
| Failed files | `1` | `1` |
| Total rows | `15096` | `15096` |
| Processed rows | `0` | `0` |
| Uploaded rows | `0` | `0` |
| Accepted rows | `0` | `0` |

Both jobs have the same event sequence:

1. `job.created`
2. `job.started`
3. `file.started`
4. `file.failed` with `edge_503`
5. `job.failed`

Classification: failure occurs after backend job creation and after file-level
upload begins, but before the first batch records any processed, uploaded, or
accepted rows.

## Runtime And Target-Class Evidence

| Check | Result |
| --- | --- |
| `/api/health` reachable | yes |
| Backend startup id | `api_690c15af41a7` |
| Backend process id | `20968` |
| `/api/config` response shape | `items_array` |
| Source class | `unc` |
| Source config source | `env` |
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
| Runtime Grafana | `unreachable` |

The core upload gates still point at the expected independent target classes.
Grafana remains a non-core runtime caveat for this blocker.

## Direct Edge Probe

The direct no-auth probe used the configured Supabase URL class from
`/api/config`, not a hardcoded legacy port.

No Authorization header, token, JWT, or upload payload was used.

| Probe | Result |
| --- | --- |
| Edge no-auth `GET` | `401_auth_class` |
| Edge no-auth `POST {}` | `401_auth_class` |

This proves the gateway route and JWT boundary are reachable. It does not prove
the authenticated upload worker can boot, because no-auth requests return before
the function worker is created.

## Container And Log-Class Evidence

Read-only Docker and log-class inspection found:

| Component | Status class | Health class | Evidence class |
| --- | --- | --- | --- |
| Supabase gateway | `running` | `healthy` | upload route `503` classes present |
| Supabase Edge runtime | `running` | `not_reported` | worker boot failure classes present |
| Supabase DB | `running` | `healthy` | no matching DB failure class |
| Supabase REST | `running` | `not_reported` | no matching REST 5xx class |
| Supabase vector | `restarting` | `unhealthy` | non-core caveat |

Sanitized log-class counts from the inspected window:

| Log class | Count / result |
| --- | ---: |
| Gateway upload-route lines | `2738` |
| Gateway upload-route `503` class | `8` |
| Gateway upload-route `401` class | `2722` |
| Edge runtime worker boot failure class | `24` |
| Edge runtime upload marker lines | `8` |
| Edge runtime upload + DB connection class | `0` |
| Edge runtime upload + payload parse class | `0` |
| DB error-class lines | `1` |
| REST 5xx lines | `0` |

The Edge runtime boot failure class was sanitized as:

`worker boot error: failed to bootstrap runtime: failed to determine entrypoint`

That class maps to a worker boot failure, which the local Supabase Edge runtime
gateway returns as HTTP `503`.

## Function Mount Evidence

The local repository still contains the `upload-metrics` function entrypoint.
The active Edge runtime container does not have the referenced entrypoint
available inside the container.

| Check | Result |
| --- | --- |
| Project function entrypoint exists | yes |
| Project function file count | `1` |
| Edge runtime function config includes `upload-metrics` | yes |
| Function config entrypoint basename | `index.ts` |
| Function config entrypoint exists inside container | no |
| Edge runtime bind source class | `temp_package_source` |
| Host bind source exists | no |
| Container bind mount file count | `0` |

This explains the otherwise confusing split:

- no-auth probes return `401_auth_class` because JWT verification happens before
  worker boot;
- authenticated product uploads pass JWT and then try to create the function
  worker;
- worker creation fails because the function entrypoint is unavailable in the
  active Edge runtime container;
- gateway returns `503`, and backend records `Edge server error 503`.

## Root Cause Classification

Root cause hypothesis:
`edge_runtime_stale_temp_function_mount_missing_entrypoint`.

Supported:

- both upload attempts fail with the same `edge_503` class before row progress;
- no-auth route probes return `401_auth_class`, proving route/auth boundary only;
- Edge runtime logs show worker boot failure class;
- active Edge runtime function config references `upload-metrics`;
- the referenced function entrypoint is missing inside the running container;
- the active bind source is a temp package source class and no longer exists on
  the host;
- DB and REST do not show matching failure classes;
- backend target classes still pass and align to the independent target.

Weakened:

- `source_scope_or_filename_failure`: Preview succeeded and source eligibility
  was already proven;
- `preview_reference_mismatch`: both failed jobs use `prv_da7bfe752c18` with
  `15096` target rows;
- `backend_target_drift`: `/api/config` target classes pass;
- `db_unreachable`: read-only DB count succeeds at `58737`;
- `payload_validation_failure`: handler validation should return `400` or
  handler-level `500`, not worker boot `503`;
- `auth_rejection`: no-auth route returns auth-class, and failed product
  uploads reach worker boot rather than auth rejection.

Unresolved:

- whether the temp package bind source disappeared after package cleanup,
  process reuse, or a previous Edge rerun package lifecycle;
- whether a fresh Supabase Edge runtime process bound to the repository
  function directory would boot cleanly;
- whether the next authenticated upload would pass after Edge runtime recovery.
  This was not tested because upload retry and authenticated manual Edge calls
  are forbidden in this task.

## Recovery Conditions Before Any Upload Retry

Do not retry upload until all of these are true:

1. user separately approves any Supabase lifecycle action needed for Edge
   runtime recovery;
2. no DB reset, DB destructive action, Docker delete, or Docker prune is part of
   the recovery plan;
3. Edge runtime is rebound to an existing function source class, preferably the
   current project `supabase/functions` class or an approved package-accessible
   source that is still present;
4. active Edge runtime container reports the `upload-metrics` function
   entrypoint present inside the container;
5. sanitized Edge runtime logs no longer show fresh worker boot failure classes
   for the upload route after recovery;
6. `/api/config` target classes still pass;
7. runtime API, DB, Studio, and Edge are ready;
8. direct no-auth Edge `GET` and `POST {}` still return `401_auth_class`;
9. read-only DB row count is recorded before the next upload attempt;
10. Preview reference and upload target count are reconfirmed, or a new
    Preview-only gate is separately approved;
11. the user separately approves exactly one Retry Failed or exactly one Start
    Upload attempt.

## Next Safe Action

Recommended next action:
`edge_runtime_recovery_with_function_mount_recheck`.

This should be a recovery task, not an upload task.

The recovery task may need a separately approved Supabase lifecycle action to
refresh the Edge runtime container. It must not include DB reset, DB destructive
operations, Docker delete/prune, Upload Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated manual Edge upload call, or full rollout.

After recovery, run only read-only gates first. A new upload attempt remains
forbidden until the function entrypoint is present, worker boot failures stop,
the target count is reconfirmed, and the user separately approves one bounded
upload action.

## Redaction Result

This document records only sanitized source classes, target classes, component
status classes, safe run/job identifiers, and aggregate counts.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no token, Authorization header, JWT, or secret;
- no raw Docker or Supabase log output.

## Validation

| Check | Result |
| --- | --- |
| Targeted backend runtime/config/upload job tests | `62 passed`, 4 warnings |
| `git diff --check` | passed |
| New document raw marker scan | passed |
| PR file scope | docs/121 only |

Validation note: the first pytest invocation hit a local Windows import-path
collision with an installed external `tests` package. The same targeted test set
passed after using a temporary import shim that prepended this repository's
`tests/` directory. No project source file was changed for that shim.
