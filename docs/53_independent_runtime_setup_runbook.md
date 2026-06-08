# Independent Runtime Setup Runbook

Date: 2026-06-08

Branch: `codex/independent-runtime-setup-runbook`

PDCA phase: Plan

Scope: maintainer-only runbook for preparing the independent local Supabase runtime for `Extrusion_web_console`.

This is a documentation-only runbook. This PR does not modify feature code, launcher code, backend code, frontend code, packaging scripts, local Supabase data, Docker data, database data, GitHub Releases, tags, production deployment, or operational data.

No Supabase init/bootstrap/start/reset command was run for this runbook. No DB migration was executed. No Docker container or volume delete was run. No Edge Function was executed. No Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

PR #65 left independent runtime readiness blocked as `blocked|required_container_missing`. That is the expected result before a maintainer prepares the repository-owned local Supabase stack. This runbook defines the maintainer-only setup order, safety gates, stop conditions, and follow-up smoke checks required to move from "assets and config exist" to "independent runtime is ready for Preview and Start Upload smoke".

The independent runtime target is:

| Item | Target |
| --- | --- |
| Supabase project path | repository-owned `supabase/` project |
| Project id | `Extrusion_web_console` |
| Container family | `supabase_*_Extrusion_web_console` |
| Upload function | `upload-metrics` |
| Upload table | `public.all_metrics` |
| Duplicate safety | unique `(timestamp, device_id)` plus Edge upsert conflict target |

This runbook is not an operator procedure. Normal operator launch must not bootstrap, reset, migrate, create, delete, prune, or repair the Supabase stack.

## Current Blocker

Independent readiness currently fails because the required independent container family does not exist. Legacy `Extrusion_data` containers may exist on the same machine, but they must not satisfy independent runtime readiness.

Required outcome after maintainer setup:

- Docker is reachable.
- Supabase CLI is available.
- `supabase/config.toml` matches backend runtime defaults.
- Independent containers named `supabase_*_Extrusion_web_console` exist.
- API, DB, Studio, and Edge route checks use independent ports.
- Settings and runtime status clearly identify `Extrusion_web_console`, not the legacy fallback.

## Purpose And Scope

Purpose:

- prepare an independent local Supabase runtime owned by `Extrusion_web_console`;
- remove default dependence on the legacy `Extrusion_data` runtime;
- provide a safe path to resolve `blocked|required_container_missing`;
- keep all destructive and data-changing operations outside this document-only PR.

In scope for the future maintainer setup:

- verify repository root and `supabase/` project location;
- verify `project_id = "Extrusion_web_console"`;
- verify configured independent ports;
- perform a maintainer-approved first stack start only after safety gates pass;
- rerun readiness smoke with sanitized evidence.

Out of scope:

- operator self-service bootstrap;
- launcher-managed Supabase setup;
- database reset, cleanup, pruning, truncation, or destructive repair;
- Docker container, volume, network, or image deletion;
- migration execution without separate approval;
- Edge Function authenticated execution without a separate smoke task;
- Upload Preview or Start Upload execution in this setup runbook PR;
- production deploy, release, tag, or legacy runtime decommission.

## Prerequisites

Before a maintainer setup attempt, confirm:

| Prerequisite | Required state |
| --- | --- |
| Docker Desktop | Running and daemon reachable. |
| Supabase CLI | Available on the maintainer shell path. |
| Repository assets | `supabase/config.toml`, `supabase/functions/upload-metrics`, and `supabase/migrations` exist. |
| Backend install | Backend dependencies are installed for API-mode smoke. |
| Frontend install | Frontend dependencies and API-mode build path are available for UI smoke. |
| Secrets | Raw `.env` values, DB URLs, tokens, Authorization headers, JWTs, and generated Supabase credentials are not documented. |
| Data | Operational source files are not copied, staged, or quoted in evidence. |

The maintainer must use local environment/config values only in their shell or config files. Do not paste raw secret values into docs, PR bodies, logs, screenshots, chat, or audit evidence.

## Pre-Run Safety Checks

Run these checks before any maintainer setup command is considered:

```powershell
git status --short --branch
git rev-parse HEAD
supabase --version
docker version
```

Safety rules:

- confirm the worktree does not contain unintended staged files;
- do not stage untracked operational source fixtures;
- do not stage `.gstack`, `frontend/dist`, package output folders, zips, or checksum files;
- do not stage raw `.env` files, local DB state, logs, screenshots, or generated Supabase runtime files;
- verify whether the legacy runtime is already using conflicting ports;
- redact local usernames, full local paths, secrets, DB URLs, tokens, Authorization headers, JWTs, and operational filenames from evidence;
- stop if any planned step requires reset, delete, cleanup, prune, or migration repair.

## Project And Port Verification

The repository source of truth is `supabase/config.toml`.

| Service | Current repo config | Expected for independent runtime |
| --- | ---: | --- |
| Project id | `Extrusion_web_console` | must match exactly |
| API | `55321` | API and Edge route base |
| DB | `25433` | current source-of-truth DB port |
| Studio | `55323` | Studio UI |
| Edge route | `55321/functions/v1/upload-metrics` | derived from API port |

Port discrepancy note:

- The requested setup checklist referenced DB port `55432`.
- Current committed `supabase/config.toml`, backend defaults, and PR #65 readiness report use DB port `25433`.
- Treat `25433` as the current source of truth.
- If the team wants DB port `55432`, stop this runbook and create a separate config-change PR that updates `supabase/config.toml`, backend defaults, tests, and docs before any runtime setup.

Do not silently remap ports during setup. Silent remapping makes DB URLs, Edge URLs, runtime evidence, and rollback decisions ambiguous.

## Maintainer-Only Setup Procedure

This section describes the approved order for a future setup attempt. It was not executed in this document-only PR.

1. Confirm repository root.

   ```powershell
   git rev-parse --show-toplevel
   Test-Path .\supabase\config.toml
   ```

2. Confirm Supabase project identity.

   ```powershell
   Select-String -Path .\supabase\config.toml -Pattern 'project_id|port'
   ```

   Expected identity is `Extrusion_web_console`. Expected containers after setup use `supabase_*_Extrusion_web_console`.

3. Confirm port availability.

   ```powershell
   Test-NetConnection 127.0.0.1 -Port 55321
   Test-NetConnection 127.0.0.1 -Port 25433
   Test-NetConnection 127.0.0.1 -Port 55323
   ```

   A listening legacy or unrelated service on any required independent port is a stop condition unless it is already the intended independent service.

4. Confirm current Supabase status without repair.

   ```powershell
   supabase status
   ```

   Record only sanitized availability states. Do not record generated credentials, connection strings, or secret values.

5. Maintainer-only first stack start.

   ```powershell
   supabase start
   ```

   This command is allowed only as a separately approved maintainer action from the repository-owned `supabase/` project context. It must not be exposed in the operator UI, double-click launcher, package default startup, or automatic readiness repair path.

6. Verify independent container family.

   ```powershell
   docker ps --format "{{.Names}}"
   ```

   Expected result is the presence of required `supabase_*_Extrusion_web_console` containers. Do not use legacy `supabase_*_Extrusion_data` containers as substitutes.

7. Stop immediately if setup produces a mismatch.

   Mismatches include wrong project id, wrong ports, missing required containers, unexpected legacy targeting, or any prompt to run reset/delete/cleanup/prune.

## Migration And Edge Preparation

Migration execution is not part of this runbook PR.

Future migration preparation rules:

- apply migrations only after separate maintainer approval;
- do not use `supabase db reset` as an acceptance shortcut;
- do not delete or truncate existing data to force a clean result;
- confirm `public.all_metrics` exists after migration;
- confirm the unique `(timestamp, device_id)` constraint exists;
- confirm the Edge Function upsert uses `onConflict: "timestamp,device_id"`;
- record schema/constraint presence as sanitized pass/fail evidence only.

Edge Function preparation rules:

- keep `upload-metrics` as the function name;
- separate Edge serve/deploy or route smoke from DB migration approval;
- no authenticated Edge call is allowed in this runbook PR;
- unauthenticated route reachability smoke may be used later only to classify route availability, not to expose secret values.

## Readiness Smoke Procedure

After maintainer setup is approved and completed, rerun independent readiness smoke before any Preview or Start Upload work.

Backend/API checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/config
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/local-supabase
```

Expected readiness evidence:

| Area | Expected result |
| --- | --- |
| Health | backend returns healthy status. |
| Config | project id and independent ports match repo config. |
| Runtime endpoint | `overallStatus` is no longer blocked by `required_container_missing`. |
| Docker | daemon reachable. |
| Project config | `configExists` and port match checks pass. |
| API | independent API port reachable. |
| DB | independent DB TCP port reachable. |
| Studio | independent Studio port reachable. |
| Edge | `upload-metrics` route reachable enough to distinguish auth/validation from runtime outage. |
| Settings UI | secret fields remain hidden/replacement-only. |
| Legacy confusion | legacy `Extrusion_data` containers do not count as independent readiness. |

Browser smoke after API readiness:

- open Settings in API mode;
- confirm project id/path display identifies the independent runtime;
- confirm env-overridden values remain read-only/disabled;
- confirm raw secret values are not rendered;
- confirm runtime status does not instruct the operator to use legacy fallback unless an explicit override is active.

Do not run Upload Preview or Start Upload until readiness is accepted and a separate smoke task is approved.

## Stop Conditions

Stop the setup and record sanitized cause if any of these occur:

| Stop condition | Required response |
| --- | --- |
| Docker unavailable | stop; fix Docker outside the app. |
| Supabase CLI unavailable | stop; install or repair CLI outside this runbook. |
| Port conflict | stop; resolve by approved config change or service shutdown decision. |
| Required container missing after setup | stop; record `required_container_missing`. |
| `config.toml` mismatch | stop; fix config through a PR before setup. |
| DB port expectation mismatch | stop if a reviewer requires `55432`; current source of truth is `25433`. |
| Edge runtime unreachable | stop before Preview or Start Upload. |
| Secret/path redaction failure | stop; remove unsafe evidence and rotate if exposure occurred. |
| Any reset/delete/cleanup/prune requirement | stop; do not run the command. |
| Legacy runtime selected unintentionally | stop; remove unintended env/config override. |

## Rollback And Fallback

Rollback policy:

- keep the legacy `Extrusion_data` runtime untouched during rollout;
- use legacy fallback only through explicit env/config override;
- do not silently fall back because independent readiness failed;
- if independent setup fails, stop and record the reason with sanitized evidence;
- keep AppData config, state, and logs intact;
- do not delete Docker containers, volumes, networks, images, local DB state, or generated runtime data;
- do not delete the feature branch.

Fallback is a controlled operational decision, not an automatic repair path. A fallback run must make the selected project id/path visible in Settings and runtime status so operators do not confuse legacy and independent runtimes.

## Security And Redaction Policy

Never document or commit:

- raw `.env` values;
- DB URLs or connection strings;
- service role values, anon key values, bearer tokens, JWTs, Authorization headers, or generated Supabase credentials;
- operational source paths, filenames, contents, raw rows, or full local paths;
- screenshots containing secrets or local paths;
- AppData state, runtime logs, database files, dumps, backups, or generated Supabase state;
- `.gstack`, `frontend/dist`, package output folders, zips, or checksum files.

Allowed evidence:

- project id;
- service names;
- non-secret port numbers;
- endpoint paths without secrets;
- `configured`, `missing`, `hidden`, `reachable`, `unreachable`, `ready`, `blocked`, and reason codes;
- sanitized counts and pass/fail results.

## QA And Test Plan

Document-only validation for this PR:

- `git diff --check`;
- marker scan for raw secret, DB URL, Authorization, JWT, Windows full-path, and operational data patterns;
- PR file scope check: `docs/53_independent_runtime_setup_runbook.md` only;
- confirm untracked operational fixtures are not staged;
- confirm `.gstack`, `frontend/dist`, package output, zip, and checksum files are not staged.

Future post-setup QA:

| QA area | Required checks |
| --- | --- |
| Config API | independent defaults, env override precedence, hidden secret fields. |
| Runtime readiness | Docker, project config, containers, API, DB, Studio, Edge. |
| Command policy | destructive commands remain forbidden; operator UI cannot bootstrap. |
| Settings UI | project id/path visible; raw secret values hidden; override fields disabled. |
| Legacy confusion | legacy containers do not satisfy independent readiness. |
| Migration contract | `all_metrics(timestamp, device_id)` uniqueness and Edge upsert conflict target preserved. |
| Preview smoke | run only after readiness passes and with separately approved source scope. |
| Start Upload smoke | run only after Preview, Edge/auth, and duplicate-safety gates pass. |
| Redaction | docs, reports, screenshots, and package evidence contain no sensitive markers. |

## Implementation Sequence

1. Merge this runbook after review.
2. Approve a maintainer-only independent runtime setup smoke.
3. From the repo-owned Supabase project, run only the approved non-destructive setup/start actions.
4. Rerun independent runtime readiness smoke.
5. If readiness passes, run a fresh Preview smoke in a separate PR/task.
6. If Preview passes, run Start Upload smoke in a separate PR/task.
7. If Start Upload passes, run final API-mode operator package smoke.
8. Require separate approval for GitHub Release/tag creation, production deploy, or legacy decommission.

## Open Questions

1. Should the current DB port `25433` remain final, or should a later config-change PR move it to `55432`?
2. Should first-stack creation remain purely manual, or should a maintainer-only script be added later with explicit guardrails?
3. Which exact acceptance window is required before the legacy runtime can be considered for decommission planning?
4. Should Edge route smoke be unauthenticated reachability only, or should authenticated smoke wait until the Start Upload task?

## Merge Readiness For Future Implementation

A future setup/readiness PR is merge-ready only when:

- setup evidence is sanitized;
- `supabase/config.toml` and backend settings agree;
- independent containers exist under `supabase_*_Extrusion_web_console`;
- readiness is not blocked by `required_container_missing`;
- API, DB, Studio, and Edge route checks pass or have explicit non-blocking caveats;
- Settings and runtime status distinguish independent runtime from legacy fallback;
- no reset/delete/cleanup/prune command was run;
- no DB migration, Edge authenticated call, Upload Preview, or Start Upload was run without separate approval;
- untracked operational fixtures and generated artifacts remain uncommitted;
- rollback remains explicit config/env fallback, not data deletion.
