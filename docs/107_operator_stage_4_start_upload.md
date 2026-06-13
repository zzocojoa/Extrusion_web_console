# Operator Stage 4 Start Upload QA

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-start-upload`

Base: `399400883a479b09595aff9222c60568ec27e54e`

Scope: Stage 4 Start Upload QA from reviewed Preview evidence

Verdict: `blocked`

## Summary

Stage 4 Start Upload was not executed.

The required PR #121 Preview evidence is merged into `main`, and a fresh backend
was launched with stale process reuse not observed. However, the active runtime
configuration and latest Preview reference did not match the approved Stage 4
Preview evidence required for Start Upload.

Because the latest active Preview reference no longer confirmed target file
count `1`, upload target rows `17179`, and already-in-DB files `1`, the Start
Upload hard stop condition was triggered before any upload job was created.

## Explicitly Not Performed

- Additional Upload Preview;
- Start Upload;
- second Start Upload;
- Retry Failed;
- duplicate rerun;
- manual authenticated Edge upload call;
- full rollout beyond the confirmed target;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase reset, start, or stop;
- Docker delete or prune;
- operational source mutation or deletion.

## Merge And Branch Gate

| Check | Result |
| --- | --- |
| PR #121 state | `MERGED` |
| PR #121 merge commit | `399400883a479b09595aff9222c60568ec27e54e` |
| Local `main` matched `origin/main` before branch | yes |
| QA branch created | yes |
| Approved Preview evidence head | `50df94d8dd64afe362ea48471f51ba0a0f1280a0` |

## Fresh Backend Identity

| Field | Value |
| --- | --- |
| Health status | `ok` |
| `startup_id` | `api_640d614adad5` |
| `started_at` | `2026-06-13T03:51:08.612588+00:00` |
| `process_id` | `21880` |
| Port owner matched health process | yes |
| Stale backend reuse observed | no |
| QA backend cleanup | stopped after validation |

## Runtime And Target Class Preflight

| Check | Result |
| --- | --- |
| API reachable | passed |
| DB reachable | passed |
| Studio reachable | passed |
| Edge runtime reachable | passed |
| Runtime overall status | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Active operation | none |
| Edge no-auth GET | `401 auth-class` |
| Edge no-auth POST `{}` | `401 auth-class` |
| DB target class | `loopback_expected_db_port` |
| Upload Edge target class | `loopback_expected_api_port_upload_metrics` |
| Runtime Edge target class | `loopback_expected_api_port_upload_metrics` |
| Upload/runtime Edge alignment | `true` |
| Target class preflight | `passed` |

Core runtime gates and DB/Edge target class alignment passed. The Start Upload
was still blocked by active source and latest Preview reference mismatch.

## Source Scope Recheck

| Check | Result |
| --- | --- |
| Expected sanitized source label | `stage4-full-candidate-a-refreshed` |
| Active config source locator class | `missing` |
| Active config source accessible | no |
| Raw source locator recorded | no |
| Raw source filename recorded | no |
| Raw source content opened | no |

The active backend configuration did not expose an accessible approved refreshed
Stage 4 source locator at the time of Start Upload gating. This alone is a hard
stop because the source scope could not be proven to match the reviewed Preview
evidence.

## Latest Active Preview Reference

| Check | Approved value | Active latest value |
| --- | ---: | ---: |
| Preview run | PR #121 reviewed run | `prv_d670d87da757` |
| Preview status | `succeeded` | `succeeded` |
| `dbStatus` | `reachable` | `reachable` |
| Target files | `1` | not confirmed |
| Upload target rows | `17179` | not confirmed |
| Already-in-DB files | `1` | not confirmed by run total |
| Item count | `2` expected scope | `3` |
| Target item count | `1` | `0` |
| Already-in-DB item count | `1` | `1` |
| Excluded item count | `0` | `2` |
| `db_full_match` item count | `1` | `1` |
| `file_date_missing` item count | `0` | `2` |

The active latest Preview reference is not the reviewed PR #121 evidence and
does not carry the approved target count confirmation. It also includes excluded
items with file-date-missing classification, which contradicts the refreshed
Stage 4 source gate.

## Hard Stop Evaluation

| Stop condition | Result |
| --- | --- |
| Latest active Preview reference missing or stale | stop |
| Upload target rows differ from `17179` | stop |
| Target files differ from `1` | stop |
| `dbStatus` not reachable | pass |
| DB/Edge target class mismatch | pass |
| Edge no-auth probes not auth-class | pass |
| Fresh backend guard fails | pass |
| Source scope differs from refreshed Stage 4 source | stop |
| Credential/source locator leak observed | pass |
| Runtime gate not ready | pass for core gates |

Start Upload was not allowed. No DB before/after upload delta is recorded because
the workflow stopped before upload job creation.

## DB And Job Evidence

| Check | Result |
| --- | --- |
| Start Upload execution count in this QA | `0` |
| Upload job created from this QA | no |
| Retry Failed execution count | `0` |
| Duplicate rerun execution count | `0` |
| Additional Upload Preview execution count | `0` |
| DB mutation expected from this QA | no |

The blocked result preserves the reviewed Stage 4 Preview evidence and avoids an
unsafe Start Upload attempt against a mismatched active Preview/source state.

## Redaction Result

This report does not include raw source locators, source names, source row
content, credential material, or connection strings. The source is described
only by sanitized class and count evidence.

## Validation

| Check | Result |
| --- | --- |
| Fresh backend guard | passed |
| Runtime target preflight | passed |
| Latest Preview target confirmation | blocked |
| Start Upload exactly once | not executed due hard stop |
| Targeted backend runtime/config/upload job tests | `49 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope check | passed, PR #122 includes this document only |

## Next Safe Action

Do not run Start Upload from the current active state.

First restore or recreate a safe active Preview reference for the refreshed
Stage 4 source, with target files `1`, upload target rows `17179`, already-in-DB
files `1`, and `dbStatus=reachable`. That recovery must be separately approved
because the current Start Upload approval explicitly forbids additional Preview
runs.
