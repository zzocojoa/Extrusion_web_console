# Independent Local Supabase Plan

Date: 2026-06-08

Branch: `codex/independent-local-supabase-plan`

PDCA phase: Plan

Scope: document-only plan for moving `Extrusion_web_console` from the legacy `Extrusion_data` local Supabase runtime to an independent local Supabase project, asset set, and runtime identity.

This plan does not modify feature code, launcher code, backend code, frontend code, packaging scripts, local Supabase data, Docker data, database data, GitHub Releases, tags, or production deployments.

No Supabase init/bootstrap/start/reset command was run for this plan. No DB migration was executed. No Edge Function was executed. No Upload Preview or Start Upload was run.

## Summary

`Extrusion_web_console` must stop treating the legacy `Extrusion_data` local Supabase stack as its default runtime. The target is an independent local Supabase project owned by this repository, with repository-local `supabase/` assets, a distinct project id, a distinct container namespace, and operator packaging that carries the required Supabase assets without carrying data, secrets, logs, or operational CSV material.

Decision summary:

| Area | Decision |
| --- | --- |
| Scope | Full independent local Supabase transition, not only config default changes. |
| Assets | Add repo-owned `supabase/config.toml`, `supabase/functions/upload-metrics`, and `supabase/migrations` in a later assets PR. |
| Runtime identity | Use project id `Extrusion_web_console` and generated containers named `supabase_*_Extrusion_web_console`. |
| Ports | Use independent ports by default so legacy and new stacks can run at the same time during rollout. |
| Data | Start with an empty independent DB by default; optional export/import is a separate maintainer-approved migration path. |
| Upload safety | Preserve `public.all_metrics`, unique `(timestamp, device_id)`, and Edge `onConflict: "timestamp,device_id"`. |
| Runtime control | Generalize status/start/stop to settings-derived project id/path/container names, while keeping destructive commands forbidden. |
| Packaging | Include Supabase assets in operator packages, but never include DB state, raw `.env`, operational CSV data, logs, screenshots, package outputs, or generated artifacts. |
| Rollout | Keep `Extrusion_data` as fallback until independent Preview and Start Upload smoke are accepted. |

## Phase 1 Assets Implementation Status

Status: implemented on branch `codex/independent-supabase-assets`.

Phase 1 adds static repo-owned Supabase assets only:

- `supabase/config.toml` with project id `Extrusion_web_console` and independent local ports;
- `supabase/functions/upload-metrics`;
- `supabase/migrations/20260608000001_create_all_metrics_upload_contract.sql`;
- `supabase/README.md` and `supabase/.gitignore` guardrails for generated/runtime files.

This phase does not change backend runtime control, launcher behavior, frontend behavior, or package assembly. It also does not run Supabase init/bootstrap/start/reset, DB migrations, Edge Function deploy/execution, Upload Preview, or Start Upload.

## Phase 2 Runtime/Config Generalization Status

Status: implemented on branch `codex/independent-runtime-config-generalization`.

Phase 2 updates backend runtime/config defaults and command policy only:

- backend defaults now point to the repo-owned `supabase/` project with project id `Extrusion_web_console`;
- default API, DB, Studio, and computed Edge ports match `supabase/config.toml`;
- runtime command allowlists are derived from configured project id as `supabase_*_<project_id>`;
- local token blocked audit target ids use the configured project id;
- Settings copy no longer describes the legacy stack as the default.

This phase does not run Supabase init/bootstrap/start/reset, DB migrations, Edge Function calls, Upload Preview, Start Upload, package assembly, production deploy, or GitHub Release/tag operations.

## Current Architecture Problem

At plan approval time, the web console was still coupled to the legacy local Supabase runtime:

- backend defaults pointed the local Supabase project path and WSL path at the legacy project;
- `local_supabase_project_id` defaulted to `Extrusion_data`;
- command policy allowlisted exact `supabase_*_Extrusion_data` containers;
- readiness messages and config checks referred to the legacy project;
- local token blocked-audit target ids used `Extrusion_data` for runtime start/stop routes;
- runtime control is designed around existing containers and does not bootstrap a new stack;
- operator package manifest does not include `supabase/` assets;
- README and planning docs described the legacy runtime as the default;
- PR #61 readiness remains blocked for Start Upload because Edge runtime is unreachable, no-auth Edge route returns `503`, and the latest Preview has `dbStatus=not_checked`.

Phase 2 removes the default runtime/config coupling, but independent runtime acceptance still requires packaging updates and controlled readiness, Preview, Start Upload, and final operator package smoke PRs. Until those are complete, rollback to the legacy runtime remains explicit config/env override only.

## Target Architecture

The target architecture keeps the local-only product model while moving the Supabase ownership boundary into this repository.

```text
----------------------------+
| Extrusion Web Console     |
| FastAPI + React package   |
+-------------+--------------+
              |
              | local API/config/runtime control
              v
+----------------------------+
| Independent local Supabase |
| project id:                |
|   Extrusion_web_console    |
| repo assets: supabase/     |
| containers:                |
|   supabase_*_Extrusion...  |
+-------------+--------------+
              |
              | Edge Function upsert
              v
+----------------------------+
| public.all_metrics         |
| UNIQUE(timestamp,device_id)|
+----------------------------+
```

The legacy `Extrusion_data` runtime remains a fallback and behavior reference during rollout. It must not be mutated or deleted by this transition.

## Scope And Non-Scope

In scope for the full transition:

- repository-owned `supabase/` project assets;
- independent project id and container namespace;
- independent default ports;
- backend settings defaults and config source labels;
- generalized container allowlist and required-container derivation;
- generalized readiness checks and runtime audit target ids;
- operator package manifest updates to include Supabase assets;
- sanitized operator/maintainer runbook updates;
- QA gates for config, runtime readiness, Preview reconciliation, Edge auth, Start Upload smoke, packaging, and redaction.

Out of scope for this document-only PR:

- copying Supabase assets;
- changing code defaults;
- changing launcher, backend, frontend, or packaging scripts;
- running `supabase init`, bootstrap, `supabase start`, `supabase db reset`, migrations, Edge Function calls, Upload Preview, or Start Upload;
- deleting or pruning Docker containers, volumes, networks, images, DB rows, AppData, logs, package outputs, or operational CSV data;
- GitHub Release/tag creation or production deploy;
- cloud Supabase migration;
- multi-user LAN web access;
- Grafana embedding.

## Decision Matrix

| Decision | Option A | Option B | Selected | Reason |
| --- | --- | --- | --- | --- |
| Transition scope | Config defaults only | Repo assets + runtime/package ownership | B | Defaults alone still depend on legacy assets and container naming. |
| Supabase assets | Keep in legacy project | Copy into this repo | Copy into this repo | The web console package must be self-contained except for Docker/CLI/runtime data. |
| Operator package | Exclude Supabase assets | Include source assets only | Include source assets only | Assets are needed for maintainer setup; DB state and secrets remain excluded. |
| Runtime start/stop | Keep legacy-only | Generalize by project id/path | Generalize | Runtime UI must identify and control the independent stack. |
| Default ports | Reuse legacy ports | Use independent ports | Use independent ports | Allows side-by-side rollout and rollback. |
| Data migration | Auto-import legacy DB | Empty DB default, optional export/import | Empty DB default | Safer rollout; exact Preview reconciliation validates operational state. |
| Bootstrap | Operator UI creates stack | Maintainer-only setup | Maintainer-only setup | Stack creation can create containers/volumes and must not be an operator web action. |
| Grafana assets | Include now | Defer unless required | Defer | Grafana remains separate link/status only; Start Upload blockers are DB/Edge/Auth. |

## Supabase Assets Migration Plan

Future assets PR must add, at minimum:

```text
supabase/
  config.toml
  functions/
    upload-metrics/
      index.ts
      deno.json or equivalent runtime metadata if required
  migrations/
    <schema migrations for public.all_metrics>
```

Assets to migrate from the legacy reference project:

| Asset | Required | Notes |
| --- | --- | --- |
| `supabase/functions/upload-metrics` | Yes | Preserve request payload compatibility and accepted/upserted response semantics. |
| `supabase/migrations` | Yes | Include schema required by `public.all_metrics` and upload dependencies. |
| `public.all_metrics` schema | Yes | Must match transform/upload expectations. |
| `(timestamp, device_id)` unique constraint | Yes | This remains the authoritative duplicate-safety boundary. |
| Edge upsert `onConflict: "timestamp,device_id"` | Yes | Must remain unchanged unless a later design explicitly replaces it with an equal or stronger safety property. |
| seed data | No by default | Empty DB is default; seed may include schema-only reference data if later required. |
| Grafana provisioning | Defer | Include only if a later Grafana package plan decides this web-console package owns Grafana assets. |

The assets PR must be reviewable as a source copy/adaptation PR. It must not include generated DB state, local `.env`, operational CSV fixtures, logs, screenshots, `.gstack`, package folders, zips, or checksums.

## Supabase Project Structure

Target structure:

```text
Extrusion_web_console/
  supabase/
    config.toml
    functions/
      upload-metrics/
    migrations/
    README.md or runtime note if needed
```

`supabase/config.toml` policy:

- set `project_id = "Extrusion_web_console"`;
- use independent API, DB, Studio, and Edge runtime settings;
- avoid copying secret values or generated credentials into the repository;
- keep function name `upload-metrics` for backend compatibility;
- document any non-default ports in a sanitized maintainer note.

Recommended independent default ports:

| Service | Legacy default | Independent default |
| --- | ---: | ---: |
| Supabase API/Kong | `54321` | `55321` |
| Postgres DB | `25432` | `25433` |
| Studio | `54323` | `55323` |
| Edge Function URL | derived from API port | derived from API port |

The exact port set must be confirmed against the generated `supabase/config.toml` in the assets PR. If any selected port conflicts on the operator PC, runtime readiness must report a clear blocked state. The operator UI must not silently remap ports because config, Edge URL, DB URL, and audit evidence would become ambiguous.

## Runtime And Config Changes

Future runtime/config implementation PR must update these areas.

Backend settings:

- change `local_supabase_project_path` default to this repository or package-local project path;
- change `local_supabase_wsl_path` default consistently for WSL use;
- change `local_supabase_project_id` default to `Extrusion_web_console`;
- change default local Supabase ports to the independent port set;
- preserve config precedence: built-in defaults, config JSON, repo `.env` or launcher env, process environment;
- preserve env override disabled/read-only behavior in Settings.

Command policy:

- replace hardcoded `supabase_*_Extrusion_data` allowlist with settings-derived container names based on `local_supabase_project_id`;
- keep exact allowlisting, `shell=False`, bounded timeouts, and redacted command output;
- continue forbidding `supabase init`, `supabase db reset`, `docker run/create/rm/rmi/volume/prune`, `docker compose up/down/rm`, destructive SQL, and shell metacharacters;
- keep required-container precheck before any `supabase start` path;
- add tests proving an `Extrusion_data` container is not controlled when project id is `Extrusion_web_console`, and vice versa.

Runtime readiness:

- read `supabase/config.toml` from the configured project path;
- compare expected ports against settings-derived values;
- report project id and project path in status so operators can distinguish legacy vs independent runtime;
- replace legacy-specific reason text with project-id-neutral messages;
- keep Edge no-auth probe semantics: expected auth/validation responses mean route reachable, `503`/timeout means blocked or unhealthy;
- keep Grafana status/link-only behavior.

Runtime control:

- define start/stop around the independent project id and containers;
- keep stop blocked while Preview or Upload Job is active;
- keep start blocked while Preview, Upload Job, or runtime operation is active;
- do not allow operator UI bootstrap/create/reset/delete actions;
- decide whether `supabase start` is allowed only after required containers exist, or whether initial stack creation is delegated entirely to a maintainer-only setup procedure. The recommended policy is: operator UI requires existing containers; maintainer-only setup may create the first stack outside the web UI.

Local token and audit target ids:

- replace `Extrusion_data` hardcoded target id for runtime start/stop token failures with the configured project id;
- keep token values out of URL, storage, logs, audit params, screenshots, and generated artifacts.

Upload Preview:

- keep direct DB URL based exact reconciliation against `public.all_metrics`;
- keep DB-unreachable handling as `partial_failed` and `risky/db_unreachable`;
- do not weaken exact `(timestamp, device_id)` matching.

Upload Jobs:

- keep Edge URL/auth based upload execution;
- preserve `acceptedRows` as accepted/upserted rows, not net-new physical insert count;
- keep Preview-origin upload excluding `partial_overlap`, `risky`, `excluded`, and `already_in_db` by default.

## Frontend And Settings Changes

Future frontend/UI implementation PR must:

- update Settings default labels and helper text from legacy stack wording to independent stack wording;
- keep env/process and repo `.env` overrides disabled/read-only;
- show project id and project path in Runtime status and Settings source displays;
- make it visually clear whether the app is targeting `Extrusion_web_console` or legacy fallback;
- keep secret raw values hidden and replacement-only behavior for secret inputs;
- avoid adding destructive maintenance controls;
- keep operator copy short and operational, not marketing-style.

Recommended operator-facing distinction:

| Situation | UI policy |
| --- | --- |
| Independent runtime selected | Show project id `Extrusion_web_console` in Runtime and Settings. |
| Legacy fallback selected by env/config override | Show a visible fallback badge and source indicator. |
| Project path missing | Block start and report the configured project id/path presence problem without exposing secrets. |
| Port mismatch | Block start and show expected vs configured service names/ports only. |

## Packaging Changes

Future packaging PR must update `packaging/operator-package.manifest.json` and assembly validation.

Include:

- `supabase/config.toml`;
- `supabase/functions/upload-metrics`;
- `supabase/migrations`;
- package-local sanitized Supabase runtime note if needed.

Continue excluding:

- raw `.env*`;
- DB state, dump files, backups, WAL files, generated volumes, or local Supabase data directories;
- operational CSV paths, filenames, contents, fixtures, or samples;
- logs, AppData state, screenshots, `.gstack`, package output folders, zips, and checksum files;
- `frontend/dist` from source control, while still requiring built `frontend/dist` in assembled operator packages;
- `tests/`, developer artifacts, `.agents`, `.codex`, `.bkit-codex`, caches, and compiled bytecode.

Operator package runtime policy:

- normal operator launch must not require Node/npm;
- normal operator launch must not run `supabase init`, migrations, reset, bootstrap, Docker prune, or DB cleanup;
- Supabase CLI, Docker, and WSL prerequisites must be documented as operator/maintainer environment prerequisites;
- first-time independent stack creation must be a maintainer-only setup step with explicit approval and sanitized evidence.

Prepared package target layout should become:

```text
ExtrusionWebConsole/
  backend/
  frontend/dist/
  launcher/
  supabase/
    config.toml
    functions/upload-metrics/
    migrations/
  docs/operator_package_runtime_note.md
  .venv/
```

## Runtime Command Policy

The non-destructive policy remains the default.

Always forbidden in operator UI and launcher:

- DB reset, delete, cleanup, truncate, prune, or destructive migration repair;
- Docker container/volume/network/image delete;
- Docker prune/system prune;
- arbitrary `docker compose` create/delete flows;
- arbitrary shell command input;
- arbitrary SQL execution;
- Upload Start while readiness gates are blocked.

Allowed in operator UI after implementation:

- passive runtime readiness probes;
- start existing allowlisted independent containers;
- stop existing allowlisted independent containers when no Preview/Upload Job is active;
- `supabase start` only if the policy continues to require pre-existing required containers and the precheck has passed.

Maintainer-only future setup may allow first-stack creation, but only in a separate implementation/runbook step that:

- is not exposed in the operator UI;
- is not run by double-click launcher default;
- records sanitized evidence only;
- does not run reset/delete/cleanup/prune;
- does not expose generated secrets;
- is separately approved before execution.

## Data Migration And Rollback

Default data strategy:

- independent DB starts empty;
- existing `Extrusion_data` DB remains untouched;
- operators use Upload Preview exact-key reconciliation to see what independent DB contains before upload;
- Start Upload remains blocked until DB/Edge/auth readiness and fresh Preview pass.

Optional data migration strategy:

- export/import from legacy `public.all_metrics` is a separate maintainer-approved migration plan;
- it must preserve schema, timestamp precision, device ids, and the `(timestamp, device_id)` uniqueness contract;
- it must not be executed by this plan PR or by default operator launch;
- validation must compare counts and exact-key samples without documenting raw operational data.

Operational reconciliation:

- after independent stack readiness, run fresh Upload Preview against a bounded operator-approved source scope;
- classify by exact keys, not latest timestamp;
- if DB is empty, target counts may be large; Start Upload smoke must use a minimal duplicate-safe sample or a separately approved controlled ingest.

Rollback:

- keep legacy `Extrusion_data` stack and data untouched through rollout;
- retain config override path to point the web console back to legacy runtime if independent runtime fails acceptance;
- keep previous known-good operator package;
- rollback means switching config/package target back, not deleting independent DB, Docker volumes, AppData, logs, or operational data.

Recommended preservation period:

- keep the legacy runtime and previous package until independent runtime has passed final operator package smoke and at least one approved operator acceptance cycle;
- do not delete legacy containers or data as part of this transition without a separate archived decommission plan.

## Security And Redaction Policy

Do not document or commit:

- secret values;
- DB URLs or connection strings;
- auth keys, JWTs, bearer tokens, service role values, anon key values, or Authorization headers;
- operational CSV paths, filenames, contents, raw rows, or full local source paths;
- raw `.env` content;
- generated Supabase credentials;
- package zips, checksums, screenshots, logs, or state DBs.

Allowed evidence:

- `configured`, `missing`, `hidden`, `reachable`, `unreachable`, `ready`, `blocked`;
- project id;
- service names;
- non-secret port numbers;
- sanitized target ids such as preview/job/runtime operation ids;
- redaction marker scan counts.

Audit policy:

- settings save, runtime start/stop, Preview, Upload Start/Retry, pause/resume/cancel, and failures remain audit logged;
- audit params store safe metadata only;
- runtime audit target id must match the configured project id;
- passive status polling success must not create audit spam.

## QA And Test Plan

Document-only PR validation:

- `git diff --check`;
- marker scan for raw secret, DB URL, Authorization, JWT, operational CSV filename/path/content classes;
- PR file scope check: only `docs/51_independent_local_supabase_plan.md`;
- confirm untracked operational CSV fixture is not staged;
- confirm `.gstack`, `frontend/dist`, package output, zip, and checksum files are not staged.

Future implementation test matrix:

| Area | Required tests/checks |
| --- | --- |
| Config API | independent defaults, env override precedence, disabled overridden fields, hidden secret display. |
| Runtime readiness | project path/config parsing, independent ports, project id display, Edge route status, legacy fallback distinction. |
| Command policy | settings-derived allowlist, forbidden commands, `shell=False`, missing required containers block start. |
| Local token/audit | runtime start/stop blocked token audit uses configured project id and never stores token values. |
| Upload Preview | exact `(timestamp, device_id)` reconciliation against independent `all_metrics`, DB unreachable path, latest-timestamp regression. |
| Upload Job/Edge | Edge route auth readiness, acceptedRows semantics, duplicate-safe upsert, failure visibility. |
| Packaging | manifest includes `supabase/` assets and rejects raw `.env`, DB state, CSV, logs, `.gstack`, package outputs. |
| Browser QA | Dashboard, Runtime, Upload, Logs, Settings in API mode across required viewports. |
| Redaction | source/docs/package artifact scans for secrets, DB URLs, auth headers, JWTs, operational CSV markers. |
| Git hygiene | no untracked operational CSV fixture, `.gstack`, `frontend/dist`, zips, or checksum files staged. |

Future runtime QA gates before Start Upload:

1. independent config values are present and secrets hidden;
2. Docker, local Supabase API, DB TCP, Studio, and Edge route are reachable;
3. no-auth Edge route proves auth/validation reachability, not `503`;
4. fresh Preview finishes `succeeded` with `dbStatus=reachable`;
5. sample scope is minimal and duplicate-safe or explicitly approved for controlled ingest;
6. Start Upload is approved in a separate QA task.

## Implementation Sequence

1. Plan PR: add this document only.
2. Supabase assets copy PR: add `supabase/config.toml`, `functions/upload-metrics`, and migrations with no runtime execution.
3. Runtime/config generalization PR: update backend settings, command policy, readiness, runtime audit target ids, and tests.
4. Package manifest update PR: include Supabase assets and extend denylist/redaction validation.
5. Independent runtime readiness QA PR: verify config/path/ports/container expectations without reset/delete/upload.
6. Preview smoke PR: run fresh Upload Preview against independent DB only after readiness passes.
7. Start Upload smoke PR: run exactly one approved minimal duplicate-safe upload after Preview and Edge/auth gates pass.
8. Final operator package smoke PR: assemble API-mode package, validate package contents, launcher, token guard, docs hardening, runtime status, Preview, and sanitized evidence.

GitHub Release/tag creation, production deploy, and merge to release branch require separate approval after the final operator package smoke.

## Open Questions

1. Should first-time independent stack creation be handled by a maintainer-only script in this repo, or by documented manual Supabase CLI steps outside the package?
2. Should the independent port set above be final, or should it be adjusted after reading generated `supabase/config.toml` and operator PC port inventory?
3. Should Grafana provisioning eventually move into this repo/package, or remain excluded because Grafana is link/status only?
4. Is empty DB acceptable for first operator acceptance, or is a controlled `all_metrics` export/import required before replacement?
5. How long should the legacy `Extrusion_data` runtime be retained after independent package acceptance?
6. Should README update happen with the runtime/config implementation PR or with the packaging PR?

## Merge Readiness For Future Implementation

A future implementation PR is merge-ready only when:

- it changes only the intended layer for that PR;
- all destructive commands remain forbidden;
- `all_metrics(timestamp, device_id)` unique/upsert safety is preserved;
- independent and legacy runtime identities cannot be confused in Settings/Runtime status;
- tests cover config defaults, command allowlist, readiness, audit target ids, and redaction;
- package validation rejects secrets, operational data, generated artifacts, and package outputs;
- validation results are recorded without raw secrets, DB URLs, auth headers, JWTs, operational CSV paths, filenames, or contents;
- rollback to the legacy runtime remains possible by config/package selection;
- no GitHub Release/tag or production deploy occurs without separate approval.
