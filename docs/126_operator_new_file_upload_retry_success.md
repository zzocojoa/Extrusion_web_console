# Operator New File Upload Retry Success

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-new-file-upload-retry-success`

Scope: docs-only QA evidence for the approved Stage 4 new-file upload retry after
Edge runtime rebind

Verdict: `upload_retry_succeeded`

## Summary

The approved upload retry for Preview run `prv_da7bfe752c18` was executed
exactly once after the Edge runtime rebind evidence from PR #131 was merged.

The retry used failed retry job `upl_89cbe4f2e447` as the source and created
one new product retry job, `upl_60696bdb4a0e`. The new retry job completed with
status `succeeded`.

Processed, uploaded, and accepted rows all matched the reviewed target count:
`15096 / 15096 / 15096`.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- second Retry Failed;
- duplicate rerun;
- authenticated manual Edge call;
- full rollout;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase lifecycle or destructive operation;
- Docker destructive operation;
- operational source mutation, rename, or deletion;
- function source mutation.

## Preflight Gates

The retry was allowed only after the pre-upload gates were rechecked.

| Gate | Result |
| --- | --- |
| Backend health identity | present |
| Runtime API | `ready` |
| Runtime DB | `ready` |
| Runtime Studio | `ready` |
| Runtime Edge | `ready` |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Target-class status | `passed` |
| DB/Edge target alignment | `true` |
| Edge no-auth `GET` | `401_auth_class` |
| Edge no-auth `POST {}` | `401_auth_class` |
| Active upload jobs before retry | `0` |

The runtime `attention` state was the already-known non-core class. The required
API, DB, Studio, Edge, target-class, and Edge auth-boundary gates passed.

## Edge Rebind Relation

PR #131 documented the Edge runtime rebind execution evidence:

- active Edge runtime running;
- function mount source class `current_repo_source`;
- `upload-metrics/index.ts` entrypoint present;
- no-auth Edge `GET` and `POST {}` returning `401_auth_class`;
- protected DB/data containers and DB volumes preserved;
- upload retry still forbidden until a separate retry approval and gate recheck.

This retry was executed only after that evidence was merged and the user
separately approved exactly one upload retry for the reviewed target count.

## Corrected Entrypoint Interpretation

An initial entrypoint recheck reported `missing` because it used a fixed
container path assumption, `/home/deno/functions/...`.

That was a false negative for the active Edge container layout. The active
container mounts the current repository function source at a runtime package
mount destination. Rechecking the actual active mount destination confirmed the
`upload-metrics/index.ts` entrypoint was `present` before the retry was run.

No raw local mount path is recorded here.

## Preview And Target Confirmation

| Check | Result |
| --- | --- |
| Approved Preview run id | `prv_da7bfe752c18` |
| Latest completed Preview run id | `prv_da7bfe752c18` |
| Preview final status | `succeeded` |
| Preview `dbStatus` | `reachable` |
| Total files | `3` |
| Target files | `1` |
| Already-in-DB files | `2` |
| Excluded files | `0` |
| Risky files | `0` |
| Expected upload target rows | `15096` |
| Confirmed upload target rows | `15096` |

The retry source job also matched the approved Preview reference and expected
row count before the retry was executed.

## Retry Execution Result

| Item | Result |
| --- | --- |
| Retry execution count | `1` |
| Retry source job | `upl_89cbe4f2e447` |
| New retry job | `upl_60696bdb4a0e` |
| New retry job mode | `retry_failed` |
| Retry job final status | `succeeded` |
| Total files | `1` |
| Succeeded files | `1` |
| Failed files | `0` |
| Cancelled files | `0` |
| Total rows | `15096` |
| Processed rows | `15096` |
| Uploaded rows | `15096` |
| Accepted rows | `15096` |
| Warning count | `0` |
| Error code | none |

## DB Delta

| Check | Before | After | Delta |
| --- | ---: | ---: | ---: |
| DB row count | `58737` | `73833` | `15096` |

The DB row-count delta matches the approved upload target rows and the retry
job accepted-row count.

## Audit And Event Evidence

| Check | Before | After | Delta |
| --- | ---: | ---: | ---: |
| Upload jobs total | `6` | `7` | `1` |
| Active upload jobs after completion | n/a | `0` | n/a |
| `upload.start` audit rows | `5` | `5` | `0` |
| `upload.retry` audit rows | `1` | `2` | `1` |

The new job event sequence included:

- `job.created`;
- `job.started`;
- `file.started`;
- progress events;
- `file.succeeded`;
- `job.succeeded`.

This is the expected event shape for one successful product retry. No new
`upload.start` audit row was created.

## Decision

| Gate | Result |
| --- | --- |
| Edge rebind evidence merged before retry | yes |
| Separate retry approval obtained | yes |
| Fresh backend/runtime gates rechecked | passed |
| Edge entrypoint presence rechecked | passed |
| Active Preview reference confirmed | passed |
| Target count confirmation | passed |
| Exactly one upload retry executed | passed |
| Retry job succeeded | passed |
| DB delta matches expected rows | passed |
| Additional retry allowed now | no |
| Additional upload allowed now | no |

The Stage 4 new-file upload retry completed successfully for the reviewed
`15096` target rows.

## Redaction Result

This document records only sanitized runtime classes, safe run/job identifiers,
and aggregate counts.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no token, Authorization header, JWT, or secret;
- no raw Edge authenticated request payload;
- no destructive command output.

## Validation

| Check | Result |
| --- | --- |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | docs/126 only |

## Next Safe Action

Create and review this docs-only QA evidence PR.

Future uploads require a new Preview-only gate, reviewed target counts, and
separate explicit approval before any Upload Preview, Start Upload, Retry
Failed, duplicate rerun, authenticated manual Edge call, or full rollout.
