# Operator Edge Runtime Container Recreate Plan Review

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-edge-runtime-container-recreate-plan-review`

Scope: plan/review only. No Edge runtime recreate or rebind was executed.

Verdict: `replacement_required_but_not_executed`

## Summary

Edge runtime container replacement/rebind is necessary before any upload retry.

The evidence chain is consistent across docs/121, docs/122, and docs/123:

- the repository-owned `upload-metrics` function entrypoint exists;
- no-auth Edge `GET` and `POST {}` reach `401_auth_class`;
- the active Edge runtime container is still bound to a stale temp source class;
- the stale source no longer exists on the host;
- the container-internal `upload-metrics/index.ts` entrypoint remains
  `missing`;
- starting or restarting the existing container can recover process state, but
  cannot change an existing Docker bind mount.

Because the failure is the container mount itself, not the function source, an
Edge runtime container replacement or equivalent rebind is required. This
document defines the exact command plan for a future approved recovery. The
plan was not executed in this task.

## Explicitly Not Performed

- Edge runtime container recreate or rebind;
- Docker container delete or prune;
- Docker volume delete or prune;
- Supabase reset;
- DB reset, init, delete, truncate, drop, or prune;
- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- source file mutation.

## Baseline Evidence

| Check | Result |
| --- | --- |
| Local `main` equals `origin/main` before branch | yes |
| Base commit | `ca4c11c28dc07ab8140e2cd36d87cc8a009bf845` |
| Working branch | `codex/operator-edge-runtime-container-recreate-plan-review` |
| Prior docs read | docs/121, docs/122, docs/123 |
| Repository function source | present |
| Function file count | `1` |
| Active Edge container status | `running` |
| Active Edge mount source class | `temp_package_source` |
| Active Edge mount source exists | no |
| Active container entrypoint presence | `missing` |
| No-auth Edge probe class | `401_auth_class` |

## Decision

| Question | Answer |
| --- | --- |
| Is replacement/rebind necessary? | yes |
| Can `docker start` or `docker restart` fix the mount? | no |
| Can this task execute replacement? | no |
| Is upload retry allowed after this document? | no |

Docker bind mounts are created with the container. Re-starting the existing
Edge container cannot replace a stale host source with the current repository
function source. The next recovery needs either a new Edge runtime container or
a Supabase-managed equivalent that creates the container from the current
repository workdir.

## Preferred Recovery Plan

This plan is intentionally Edge-focused and non-destructive. It avoids DB
commands, DB reset, volume deletion, prune operations, and source mutation.

Run only after separate explicit approval.

```powershell
$ErrorActionPreference = "Stop"

$ProjectId = "Extrusion_web_console"
$ProjectRoot = (Resolve-Path .).Path
$Edge = "supabase_edge_runtime_$ProjectId"
$Hold = "supabase_edge_runtime_${ProjectId}_stale_hold_$(Get-Date -Format yyyyMMdd_HHmmss)"

$ProtectedContainers = @(
  "supabase_db_$ProjectId",
  "supabase_kong_$ProjectId",
  "supabase_rest_$ProjectId",
  "supabase_studio_$ProjectId"
)

foreach ($name in $ProtectedContainers + @($Edge)) {
  docker inspect $name *> $null
  if ($LASTEXITCODE -ne 0) {
    throw "Required container missing before recovery: $name"
  }
}

$BeforeIds = @{}
foreach ($name in $ProtectedContainers) {
  $BeforeIds[$name] = docker inspect --format "{{.Id}}" $name
}

if (-not (Test-Path ".\supabase\functions\upload-metrics\index.ts")) {
  throw "Repository function entrypoint missing before recovery."
}

docker stop $Edge
docker rename $Edge $Hold

supabase start --workdir . --yes `
  --exclude gotrue,realtime,storage-api,imgproxy,kong,mailpit,postgrest,postgres-meta,studio,logflare,vector,supavisor

docker inspect $Edge *> $null
if ($LASTEXITCODE -ne 0) {
  throw "New Edge runtime container was not created."
}

foreach ($name in $ProtectedContainers) {
  $after = docker inspect --format "{{.Id}}" $name
  if ($after -ne $BeforeIds[$name]) {
    throw "Protected non-Edge container changed: $name"
  }
}

$entrypointPresent = docker exec $Edge sh -lc `
  "test -f /home/deno/functions/upload-metrics/index.ts || test -f /root/functions/upload-metrics/index.ts || test -f /functions/upload-metrics/index.ts"
if ($LASTEXITCODE -ne 0) {
  throw "New Edge runtime container does not expose upload-metrics/index.ts."
}
```

### Why This Plan

- `docker stop` targets only the old Edge runtime container.
- `docker rename` keeps the old stale container for rollback instead of
  deleting it.
- `supabase start --workdir .` asks Supabase CLI to create runtime state from
  the current repository workdir.
- The `--exclude` list prevents optional/non-target services from being
  intentionally started by this recovery command.
- Non-Edge container IDs are captured before recovery and must match after
  recovery.

This is still a runtime lifecycle action. It must not be run without explicit
approval.

## Rollback Plan

Use this only if the new Edge runtime container fails mount or no-auth checks.
Do not delete either container during the rollback.

```powershell
$ErrorActionPreference = "Stop"

$ProjectId = "Extrusion_web_console"
$Edge = "supabase_edge_runtime_$ProjectId"
$Hold = "<held-old-edge-container-name-from-the-approved-run>"
$Failed = "supabase_edge_runtime_${ProjectId}_failed_rebind_hold_$(Get-Date -Format yyyyMMdd_HHmmss)"

docker stop $Edge
docker rename $Edge $Failed
docker rename $Hold $Edge
docker start $Edge
```

Rollback restores the previous stale Edge container so the gateway/auth boundary
can return to its prior known state. It does not make upload retry safe. It
only returns the runtime to the pre-recovery condition for further
investigation.

## Forbidden Commands

These command classes remain no-go for this recovery:

```text
docker rm
docker container prune
docker system prune
docker volume rm
docker volume prune
supabase reset
supabase db reset
supabase stop --no-backup
DROP
TRUNCATE
DELETE FROM operational tables
Upload Preview
Start Upload
Retry Failed
duplicate rerun
authenticated Edge upload call
full rollout
```

The preferred plan also avoids broad `supabase stop` because the CLI help shows
it stops local Supabase containers at project scope, not Edge-only scope.

## Data Loss Risk

| Risk | Assessment | Mitigation |
| --- | --- | --- |
| DB data deletion | low if the plan is followed | no DB commands, no volume commands, no reset |
| DB container replacement | no-go | before/after protected container IDs must match |
| Volume deletion | no-go | no volume delete or prune commands |
| Edge rollback loss | low | old Edge container is renamed, not deleted |
| Runtime outage | expected for Edge only | old Edge is stopped during replacement |
| Accidental broad lifecycle | medium if command changed | exact command review and no `supabase stop` |

No DB backup/export is required for the preferred Edge-only plan because it does
not mutate DB state or delete volumes. If the approved recovery changes to a
broad Supabase stop/start plan, take a separate approval and backup decision
first.

## Expected Before Evidence

Before any approved recovery run, record sanitized evidence:

| Evidence | Required value |
| --- | --- |
| Repository function entrypoint | present |
| Active Edge container | running or inspectable |
| Active Edge mount source class | `temp_package_source` |
| Active Edge entrypoint presence | `missing` |
| No-auth Edge `GET` | `401_auth_class` or documented pre-recovery caveat |
| No-auth Edge `POST {}` | `401_auth_class` or documented pre-recovery caveat |
| Protected non-Edge container IDs | captured |
| DB destructive commands | not executed |
| Upload actions | not executed |

## Expected After Evidence

After an approved recovery run, the recovery is successful only if all gates
pass:

| Gate | Required value |
| --- | --- |
| New Edge container exists under expected name | yes |
| Old stale Edge container retained under hold name | yes |
| Protected non-Edge container IDs unchanged | yes |
| Edge mount source class | `current_repo_source` |
| Container `upload-metrics/index.ts` presence | `present` |
| No-auth Edge `GET` | `401_auth_class` |
| No-auth Edge `POST {}` | `401_auth_class` |
| DB/Edge target-class alignment | reconfirmed if backend API is reachable |
| Upload Preview | not executed |
| Start Upload or Retry Failed | not executed |

If any after gate fails, upload retry remains forbidden and the rollback plan
should be considered before further investigation.

## Go/No-Go Before Any Upload Retry

Even after Edge recovery succeeds, upload retry is still a separate decision.

Go condition for requesting upload retry approval:

1. Edge mount source class is `current_repo_source`;
2. container entrypoint presence is `present`;
3. no-auth Edge `GET` and `POST {}` return `401_auth_class`;
4. backend `/api/health` is reachable with fresh identity;
5. backend `/api/config` target classes pass;
6. DB read-only row count succeeds;
7. latest approved Preview reference and upload target rows are reconfirmed;
8. no extra Upload Preview, Start Upload, Retry Failed, duplicate rerun, or
   authenticated manual Edge upload call occurred during recovery;
9. user separately approves exactly one bounded upload action.

No-go condition:

- any protected non-Edge container ID changes unexpectedly;
- entrypoint remains missing;
- Edge no-auth route returns `503_unavailable_class`;
- backend target classes are mismatched or unavailable without an approved
  equivalent;
- Preview reference or target rows cannot be reconfirmed;
- any forbidden command or upload action was executed.

## Redaction Result

This document records only sanitized source classes, runtime classes, command
classes, and aggregate evidence.

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
| PR file scope | docs/124 only |
