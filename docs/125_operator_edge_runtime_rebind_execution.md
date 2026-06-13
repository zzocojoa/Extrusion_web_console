# Operator Edge Runtime Rebind Execution

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-edge-runtime-rebind-execution`

Scope: Edge runtime replacement/rebind execution result documentation only

Verdict: `edge_runtime_rebind_succeeded_upload_retry_still_forbidden`

## Summary

The Edge runtime replacement/rebind was executed after PR #130 was merged and
separately approved.

The active Edge runtime now runs with the current repository function source
class. The `upload-metrics/index.ts` entrypoint is present inside the function
mount, and direct no-auth Edge `GET` and `POST {}` probes both return
`401_auth_class`.

No Upload Preview, Start Upload, Retry Failed, duplicate rerun, authenticated
Edge upload call, full rollout, DB reset, DB destructive operation, Docker
volume delete/prune, Supabase reset, or source mutation was performed.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Docker volume delete or prune;
- Supabase reset;
- operational source mutation;
- function source mutation.

## Before Evidence

Before the replacement/rebind execution, the approved PR #130 plan was based on
the following runtime evidence:

| Evidence | Before result |
| --- | --- |
| Active Edge runtime status | `running` |
| Active Edge mount source class | `temp_package_source` |
| Active Edge mount source existed on host | no |
| Container entrypoint presence | `missing` |
| No-auth Edge `GET` | `401_auth_class` |
| No-auth Edge `POST {}` | `401_auth_class` |
| Repository function source | present |
| Repository function file count | `1` |

Protected container IDs captured before execution:

| Component | Before container ID | Status / health |
| --- | --- | --- |
| DB | `cfdc5b8b379c9b78b4249f04ee83769ff302c0e80914a9d0ba71e4c236186dd0` | `running` / `healthy` |
| Kong | `94e1de58520f189614d6ce6eae62b7ce842a6d2c22f02bfcb06ca60f2761fe6a` | `running` / `healthy` |
| REST | `9ffa5c226bae245e5cd9134830abde033a5488f088484ae9d106ddb263029dc7` | `running` / `not_reported` |
| Studio | `caa478b4e424a834730e5d58d7e074168ba185fdc504e9ec217fc6155bca3637` | `running` / `healthy` |

DB volume IDs captured before execution:

| Volume class | Volume ID |
| --- | --- |
| DB data/config volume | `supabase_db_Extrusion_web_console` |
| DB data/config volume | `supabase_config_Extrusion_web_console` |

## Execution Summary

The approved recovery plan stopped the stale Edge runtime container and
preserved it under a hold name instead of deleting it.

The first manual create attempt produced a new container with the intended Edge
name, but that container exited during bootstrap. It was not deleted. It was
renamed to a failed-rebind hold name.

The second manual create used the same Edge-only intent, with the bootstrap
script delivered through a temporary helper mount so shell quoting did not
corrupt the runtime bootstrap script. That active container started
successfully.

No Docker container deletion, Docker prune, Docker volume deletion, Docker
volume prune, Supabase reset, or DB destructive operation was used.

## After Evidence

Protected container IDs after execution:

| Component | After container ID | Same as before | Status / health |
| --- | --- | --- | --- |
| DB | `cfdc5b8b379c9b78b4249f04ee83769ff302c0e80914a9d0ba71e4c236186dd0` | yes | `running` / `healthy` |
| Kong | `94e1de58520f189614d6ce6eae62b7ce842a6d2c22f02bfcb06ca60f2761fe6a` | yes | `running` / `healthy` |
| REST | `9ffa5c226bae245e5cd9134830abde033a5488f088484ae9d106ddb263029dc7` | yes | `running` / `not_reported` |
| Studio | `caa478b4e424a834730e5d58d7e074168ba185fdc504e9ec217fc6155bca3637` | yes | `running` / `healthy` |

DB volume IDs after execution:

| Volume class | Volume ID | Preserved |
| --- | --- | --- |
| DB data/config volume | `supabase_db_Extrusion_web_console` | yes |
| DB data/config volume | `supabase_config_Extrusion_web_console` | yes |

Active Edge runtime after execution:

| Evidence | Result |
| --- | --- |
| Active Edge container status | `running` |
| Active Edge container health | `not_reported` |
| Active Edge container ID | `ba5f64bf3531d454f460eee2115a8149453d7741f98c52fba452dcfb1b95a135` |
| Function mount source class | `current_repo_source` |
| Function mount source exists | yes |
| Function entrypoint presence | `present` |
| Deno cache volume ID | `supabase_edge_runtime_Extrusion_web_console` |
| Bootstrap helper mount class | `temp_source` |

Direct no-auth Edge probe after execution:

| Probe | Result |
| --- | --- |
| Edge no-auth `GET` | `401_auth_class` |
| Edge no-auth `POST {}` | `401_auth_class` |

## Hold Container Caveat

Two inactive Edge containers are intentionally preserved:

| Hold class | Status | Reason |
| --- | --- | --- |
| stale Edge hold | `exited` | original stale temp-mount container preserved for rollback/inspection |
| failed rebind hold | `exited` | first manual create attempt preserved after bootstrap failure |

These containers were not deleted because the approved recovery explicitly
avoided container deletion and prune actions. They should remain untouched until
a separately approved cleanup/recovery review decides otherwise.

## Upload Retry Status

Upload retry remains forbidden after this document.

The Edge mount and auth-boundary gates are now recovered, but upload retry still
requires a separate approval after the next pre-upload gates pass.

## Required Next Gate Before Upload Retry

Before any Retry Failed or Start Upload action, run a separate gated QA step
that confirms:

1. backend `/api/health` is reachable with fresh backend identity;
2. `/api/config` target classes still pass;
3. `/api/runtime/local-supabase` reports API/DB/Studio/Edge readiness;
4. DB/Edge target class alignment passes;
5. latest active Preview reference is the approved target reference;
6. expected upload target rows are `15096`;
7. DB read-only before count is recorded;
8. upload job count is unchanged before retry;
9. `upload.start` audit count is unchanged before retry;
10. no extra Upload Preview, Start Upload, Retry Failed, duplicate rerun,
    authenticated Edge upload call, or full rollout occurred during the
    recovery.

Only after those gates pass should the user separately approve exactly one
bounded upload retry.

## Redaction Result

This document records only sanitized source classes, runtime classes, safe
container identifiers, volume identifiers, and aggregate evidence.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw database locator;
- no credential-bearing header value;
- no signed token value;
- no secret value.

## Validation

| Check | Result |
| --- | --- |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | docs/125 only |
