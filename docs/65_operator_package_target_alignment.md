# Operator Package Target Alignment QA

Date: 2026-06-09

Branch: `codex/operator-package-target-alignment`

Base commit: `7dff3a3138d7bd4d56ebf47c3c33b626b8e6b5cf`

Scope: report-only QA for the PR #77 caveat. This run checks whether the operator launcher/package execution path preserves the same independent `Extrusion_web_console` Supabase target class for Upload Preview DB reconciliation and Start Upload Edge routing.

This QA did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag. No Supabase init/bootstrap/start/reset, DB migration, DB reset/delete/truncate/drop/cleanup/prune, Docker container/volume/image/network delete, Upload Start, duplicate rerun, authenticated Edge upload call, Authorization header, token use, operational full-source upload, operational source modification, or operational source deletion was run.

## Summary

Alignment verdict: `blocked`.

The operator package was assembled from the repo in API-mode frontend packaging and launched through the package launcher path on an alternate local backend port. This was not the repo dev backend path. Raw package output paths, operator state paths, secret values, DB URLs, Edge URLs, tokens, and source paths were not recorded.

The package-launched backend became reachable, and the host independent Supabase runtime was reachable on API port `55321`, DB port `25433`, and Studio port `55323`. Direct no-auth Edge `GET` and `POST {}` probes against the independent API port returned auth-class `401`, so the independent Edge route is alive and reaches the auth boundary.

The package path is blocked for target alignment because the assembled operator package does not include repo-owned `supabase/` assets. The package-launched runtime readiness endpoint reported overall status `blocked` with reason `config_toml_missing`. Since the package default local Supabase project path resolves within the package root, the package cannot verify its repo-owned `supabase/config.toml` or prove package-local runtime ownership until Supabase assets are included in the package.

Config presence also remains incomplete for package-path alignment: the package-launched backend reported independent local Supabase project id and ports, hidden/configured DB and anon-key presence, but `supabaseUrl` was missing/default and `supabaseEdgeUrl` was missing/default. Therefore this QA cannot prove that Preview DB reconciliation and Start Upload Edge routing are aligned through the operator package path.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Execution path | operator package launcher path |
| Backend port | alternate local port |
| Frontend mode | API-mode packaged frontend |
| Package output | repo-external temporary package |
| Package Supabase assets | absent |
| Runtime setup action | not run |
| Supabase status | checked with raw output suppressed |
| Upload Preview | not run |
| Upload Start | not run |
| Duplicate rerun | not run |
| Edge authenticated upload call | not run |
| Authorization header or token | not used |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Operator Path Evidence

| Check | Result |
| --- | --- |
| Package assembly | succeeded |
| Package readiness denylist matches | `0` |
| Package readiness redaction matches | `0` |
| Package frontend mode | `api` |
| Package includes `supabase/config.toml` | no |
| Package includes `supabase/functions` | no |
| Package launcher backend | reachable |
| Package launcher path class | operator package path |
| Repo dev backend path | not used |

The package assembly succeeded as a distributable artifact, but the artifact does not contain the independent Supabase project assets required by the independent runtime plan.

## Target Class Comparison

| Target | Evidence | Class |
| --- | --- | --- |
| `supabaseDbUrl` | Config API reported configured hidden value from persisted config | unknown |
| `supabaseUrl` | Config API reported missing/default | unknown |
| `supabaseEdgeUrl` | Config API reported missing/default | unknown |
| `supabaseAnonKey` | Config API reported configured hidden value from persisted config | configured/hidden |
| `localSupabaseProjectId` | Config API reported `Extrusion_web_console` | independent |
| `localSupabaseApiPort` | Config API reported `55321` | independent |
| `localSupabaseDbPort` | Config API reported `25433` | independent |
| `localSupabaseStudioPort` | Config API reported `55323` | independent |
| `plcDataDir` | Config API reported configured presence only | configured |

Conclusion: local project id and local runtime ports are independent, but DB URL and Edge URL class alignment is not proven through the package path. Missing packaged Supabase assets block runtime ownership verification, and missing/default Edge URL config blocks explicit Start Upload Edge target-class proof.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker daemon | reachable |
| Independent container family | present |
| Independent API port `55321` | reachable |
| Independent DB port `25433` | reachable |
| Independent Studio port `55323` | reachable |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Package runtime overall status | `blocked` |
| Package runtime reason | `config_toml_missing` |
| Package Docker / API / DB / Studio / Edge | `ready` / `ready` / `ready` / `ready` / `ready` |
| Missing required containers | `0` |
| Grafana | unreachable |

Legacy Supabase runtime was also present side by side on the host. This QA classified only the independent target ports and did not assume a single running stack.

## Read-Only DB Evidence

| Check | Result |
| --- | --- |
| Independent DB port reachable | yes |
| Independent `all_metrics` total rows | `5` |
| Independent distinct `(timestamp, device_id)` keys | `5` |
| Independent rows with device id | `5` |

This confirms the independent DB remains reachable and internally consistent for the previously recorded bounded evidence. It does not prove that the package-launched Preview path is using that DB target, because Preview was not executed and the package path readiness is blocked.

## Preview And Edge Actions

| Action | Result |
| --- | --- |
| Preview-only rerun | not run |
| Upload Start | not run |
| Duplicate rerun | not run |
| Authenticated Edge upload call | not run |
| Direct no-auth Edge route | auth-class `401` |

Preview was not rerun because the package path runtime readiness was already blocked by missing `supabase/config.toml`, and this QA was not allowed to use token or Authorization-header based calls. The direct no-auth Edge check only proves the independent Edge route is alive; it does not prove Start Upload authenticated routing.

## Browser, Audit, And Redaction

| Check | Result |
| --- | --- |
| `/` HTTP smoke | `200`, marker scan clean |
| `/upload` HTTP smoke | `200`, marker scan clean |
| `/logs` HTTP smoke | `200`, marker scan clean |
| `/settings` HTTP smoke | `200`, marker scan clean |
| `/api/health` read-only smoke | `200`, marker scan clean |
| `/api/config` read-only smoke | `200`, marker scan clean |
| `/api/audit?limit=1` read-only smoke | `200`, marker scan clean |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Operational source path/content/filename in report | absent |
| Raw CSV path/content/filename in report | absent |
| Raw Supabase status output | absent |
| Raw generated credentials | absent |

## Blockers And Caveats

### Blockers

1. `package_supabase_assets_missing`: the assembled operator package does not include `supabase/config.toml`, function assets, or migrations, so package runtime readiness blocks with `config_toml_missing`.
2. `operator_path_target_alignment_unproven`: package-launched Preview DB reconciliation and Start Upload Edge target classes cannot be proven aligned until package runtime ownership and explicit target config are available.
3. `edge_target_missing_default`: package-launched config reported `supabaseEdgeUrl` missing/default, so Start Upload Edge target class is not explicitly proven through the operator package path.

### Caveats

1. `no_preview_rerun`: Preview-only was not rerun from the package path because readiness was already blocked and token/header use was out of scope.
2. `no_authenticated_edge_upload`: this QA intentionally did not run Upload Start, duplicate rerun, or authenticated Edge upload.
3. `legacy_stack_side_by_side`: legacy runtime was also present on the host, so future QA must continue to classify target ports and project ids explicitly.
4. `grafana_unreachable`: Grafana remains unreachable. Grafana is link/status-only and is not part of DB/Edge upload target alignment.

### Passed

1. `operator_launcher_backend_reachable`: the packaged launcher path started a reachable backend on the alternate local port.
2. `independent_runtime_alive`: independent API, DB, Studio, and no-auth Edge route were reachable.
3. `read_only_db_evidence_consistent`: independent DB read-only count and distinct-key count remained `5`.
4. `redaction_safe`: report, browser smoke, API smoke, and audit sample marker scans did not expose raw secrets, DB URLs, tokens, Authorization headers, JWTs, source paths, CSV filenames, or row contents.
5. `dangerous_operations_avoided`: no forbidden Supabase, DB, Docker delete, Upload Start, duplicate rerun, Edge authenticated upload, release, tag, or deploy action was run.

## Duplicate-Safe Rerun Decision

Duplicate-safe rerun allowed next step: `no`.

Do not proceed to a duplicate-safe rerun or any further upload execution from the operator package path until:

1. the operator package includes the repo-owned `supabase/` assets or has an approved equivalent runtime asset location;
2. package runtime readiness no longer blocks on `config_toml_missing`;
3. package-launched config proves DB and Edge target classes are both independent with raw values hidden;
4. a separate QA confirms Preview `dbStatus=reachable` through the operator package path.

## Validation

| Command/check | Result |
| --- | --- |
| Package assembly | passed |
| Package launcher smoke | backend reachable |
| Direct runtime reachability | API/DB/Studio reachable, Edge auth-class |
| Package backend runtime endpoint | blocked: `config_toml_missing` |
| Independent DB read-only count | reachable, total `5`, distinct keys `5` |
| Browser `/`, `/upload`, `/logs`, `/settings` HTTP smoke | loaded, marker clean |
| API `/api/health`, `/api/config`, `/api/audit?limit=1` smoke | loaded, marker clean |
| Upload Preview | not run, blocked by package runtime readiness |
| Upload Start / duplicate rerun / authenticated Edge upload | not run |

## Next Step

Open a packaging-focused implementation PR that includes repo-owned `supabase/` assets in the operator package or defines an approved equivalent asset location. After that PR lands, rerun operator package target alignment QA and require package runtime readiness to pass before any duplicate-safe upload rerun.
