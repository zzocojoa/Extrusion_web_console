# Independent Runtime Setup Smoke

Date: 2026-06-08

Branch: `codex/independent-runtime-setup-smoke`

Base commit: `fbe01159b7415f6dd2e45939a34034d1ae1f65d9`

Scope: report-only QA for the maintainer-approved independent local Supabase runtime setup smoke.

This smoke used the merged maintainer-only runbook in `docs/53_independent_runtime_setup_runbook.md`. The only approved runtime-mutating command in this smoke was `supabase start` for the repository-owned independent Supabase project.

No feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag was modified. No `supabase init`, `supabase db reset`, `supabase db push`, explicit migration command, DB delete/truncate/drop/cleanup/prune command, Docker delete command, Upload Preview, Start Upload, or authenticated Edge call was run.

## Summary

Setup verdict: `ready_with_caveats`.

PR #65's `blocked|required_container_missing` state is resolved for the independent runtime. The approved `supabase start` created the expected independent Supabase container family, and API, DB TCP, Studio, and a no-auth Edge route probe were reachable on the independent ports.

The backend runtime readiness endpoint now sees the independent containers and reports core API/DB/Studio as ready, but overall status remains `attention` because the backend Edge probe reports `unreachable` or `unhealthy` and Grafana is unreachable. A direct no-auth Edge route probe returned an auth-class HTTP response, so this is a readiness-probe discrepancy to carry into the next readiness rerun before Preview or Start Upload.

## QA Environment

| Item | Result |
| --- | --- |
| QA mode | report-only |
| Runtime setup command | approved maintainer-only `supabase start` |
| Supabase project context | repository-owned `supabase/` project |
| Backend smoke | loopback API-mode app started with temporary config/state |
| Frontend smoke | API-mode build served by backend |
| Upload Preview / Start Upload | not run |
| Edge authenticated call | not run |
| Docker delete / DB reset / cleanup / prune | not run |
| Production deploy / Release / tag | not run |

## Pre-Run Checks

| Check | Result |
| --- | --- |
| Base branch/head | `main` at `fbe01159b7415f6dd2e45939a34034d1ae1f65d9` |
| Docker daemon | available |
| Supabase CLI | available |
| `supabase/config.toml` exists | pass |
| `supabase/functions/upload-metrics` exists | pass |
| `supabase/migrations` exists | pass |
| Independent containers before setup | `0` |
| Legacy container family present | yes |
| Untracked operational fixture | present but not staged |

## Config Verification

`supabase/config.toml` is consistent with the independent runtime plan.

| Field | Expected | Observed |
| --- | --- | --- |
| Project id | `Extrusion_web_console` | pass |
| API port | `55321` | pass |
| DB port | `25433` | pass |
| Studio port | `55323` | pass |
| Requested `55432` DB port | not current source of truth | documented as a stop-condition in the runbook |

No silent port remapping was observed in the smoke evidence.

## Supabase Start Result

| Item | Result |
| --- | --- |
| `supabase start` exit code | `0` |
| Started signal | present |
| Raw output | suppressed |
| Credential-like markers in raw output | present, therefore not recorded |
| Migration-related wording in raw output | present |
| Explicit migration command run | no |

Caveat: the raw `supabase start` output contained migration-related wording. This smoke did not run `supabase db push`, `supabase db reset`, or any explicit migration command. Because the raw output was suppressed to avoid credential disclosure, the report records this as a governance caveat for the next maintainer review rather than quoting the underlying output.

## Container Results

Expected independent container family: `supabase_*_Extrusion_web_console`.

| Check | Result |
| --- | --- |
| Independent container count after setup | `12` |
| Expected container family present | yes |
| Legacy container family still present | yes |
| Legacy containers used as independent readiness substitute | no |

Observed independent containers:

- `supabase_analytics_Extrusion_web_console`
- `supabase_auth_Extrusion_web_console`
- `supabase_db_Extrusion_web_console`
- `supabase_edge_runtime_Extrusion_web_console`
- `supabase_inbucket_Extrusion_web_console`
- `supabase_kong_Extrusion_web_console`
- `supabase_pg_meta_Extrusion_web_console`
- `supabase_realtime_Extrusion_web_console`
- `supabase_rest_Extrusion_web_console`
- `supabase_storage_Extrusion_web_console`
- `supabase_studio_Extrusion_web_console`
- `supabase_vector_Extrusion_web_console`

Container caveat: `supabase_vector_Extrusion_web_console` was repeatedly restarting during the smoke. Core DB/API/Studio reachability still passed, but this is a non-core runtime caveat.

## Reachability Results

| Probe | Result |
| --- | --- |
| API TCP `55321` | reachable |
| DB TCP `25433` | reachable |
| Studio TCP `55323` | reachable |
| API HTTP root | reachable with not-found class response |
| Studio HTTP root | reachable with success class response |
| Edge no-auth route | reachable with auth-required class response |

No authenticated Edge call was made.

## Backend Runtime Readiness

Read-only endpoint used: `GET /api/runtime/local-supabase`.

The unsupported alias `GET /api/runtime/status` was not used for readiness. A separate alias check returned not-found as expected.

| Field | Result |
| --- | --- |
| `/api/health` | `ok` |
| `/api/config` | reachable |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |
| Project id | `Extrusion_web_console` |
| Docker status | `ready` |
| Supabase CLI status | `ready` |
| API status | `ready` |
| DB status | `ready` |
| Studio status | `ready` |
| Backend Edge status | `unreachable` / `unhealthy` across repeated checks |
| Backend Edge detail class | timeout or `503` class |
| Grafana status | `unreachable` |
| Runtime container count | `12` |

Assessment: `required_container_missing` is resolved. Full runtime readiness is not clean because backend Edge probing and Grafana remain in attention states.

## Settings And Redaction

`GET /api/config` returned independent defaults without exposing raw secret values.

| Check | Result |
| --- | --- |
| Config project id | `Extrusion_web_console` |
| Config API/DB/Studio ports | `55321` / `25433` / `55323` |
| Secret-bearing config items present | yes |
| Raw secret pattern visible in config response | no |
| App shell reachable | yes |
| Raw secret pattern visible in app shell | no |
| Settings page loaded in API mode | yes |
| Settings page console errors | `0` |
| Raw secret pattern visible in Settings DOM/input scan | no |

Settings UI caveat: the headless Settings smoke did not find the project id or Studio port text in the rendered DOM, and did not find password-type inputs. API config redaction still passed, but the UI-level project identity and secret-input presentation should be rechecked in the next browser QA pass before operator acceptance.

## Legacy Runtime Confusion Check

| Check | Result |
| --- | --- |
| Legacy container family present on host | yes |
| Independent container family present after setup | yes |
| Runtime readiness accepted legacy containers for independent readiness | no |
| Runtime project id | `Extrusion_web_console` |
| Required independent containers present | yes |

The smoke confirms the app is no longer blocked simply because only legacy containers exist. The independent stack is now present and separately identified.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Generated Supabase credentials in report | absent |
| Operational source path/content/filename in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Operational source fixture committed | no |

## Validation

| Command/check | Result |
| --- | --- |
| Targeted backend runtime/config/local-token tests | `64 passed` |
| `npm run typecheck` | passed |
| `npm run build` | passed |
| `npm run build:api` | passed |
| Docker/Supabase container smoke | independent containers present |
| API/DB/Studio direct reachability | passed |
| Edge no-auth direct reachability | auth-required class response |
| Backend runtime readiness | `attention` |
| Settings redaction smoke | raw secret pattern absent |

Pre-PR hygiene checks still required after this report is staged:

- `git diff --check`;
- report marker scan;
- PR file-scope check;
- forbidden file staged check.

## Findings

### Resolved

1. `required_container_missing`: resolved. The expected independent container family now exists.
2. `independent_ports_unreachable`: resolved for API TCP, DB TCP, Studio TCP, and direct no-auth Edge route reachability.
3. `legacy_not_confused`: pass. Legacy containers are present but do not satisfy independent runtime identity.

### Caveats

1. `backend_edge_probe_attention`: backend runtime readiness still reports Edge as unreachable or unhealthy, while a direct no-auth route probe returns an auth-required class response.
2. `grafana_unreachable`: Grafana remains unreachable. This is not an independent Supabase blocker, but it contributes to runtime `attention`.
3. `vector_container_restarting`: the vector container was restarting during smoke; core services remained reachable.
4. `supabase_start_migration_wording`: approved `supabase start` output included migration-related wording; no explicit migration command was run.
5. `settings_ui_identity_visibility`: headless Settings DOM scan did not find project id or Studio port text, even though config API returned correct independent values.

### Not Tested By Design

1. Upload Preview was not run.
2. Start Upload was not run.
3. Authenticated Edge calls were not run.
4. DB schema validation and data reconciliation were not run.
5. Docker stop/delete and DB cleanup paths were not run.

## Merge Blocker Assessment

This QA report PR is documentation-only and has no feature-code merge blocker.

The runtime setup smoke is not fully clean for operator acceptance. It is acceptable to merge this report as evidence that the independent stack can be created and the original `required_container_missing` blocker is resolved, but the next readiness task must investigate the backend Edge probe discrepancy and Settings UI identity visibility before Preview smoke.

## Next Step

Run an independent runtime readiness rerun on a new branch after this report is reviewed. If the backend Edge probe becomes ready or its discrepancy is explained, proceed to a separately approved Preview smoke. Do not proceed to Start Upload until readiness and Preview gates pass.
