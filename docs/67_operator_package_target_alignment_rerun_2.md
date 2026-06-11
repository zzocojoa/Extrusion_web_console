# Operator Package Target Alignment Rerun 2 QA

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-package-target-alignment-rerun-2`
- Base commit: `8a13992d2ad64b066e08040116592ac459ddb288`
- QA mode: report-only, no functional changes
- Package path class: assembled operator package, not repo dev backend
- Alignment verdict: `aligned_with_caveats`
- Duplicate-safe rerun allowed next step: `no`

This rerun verifies the operator package path after the package Supabase asset work and package launcher DB target default work.

The prior blockers are resolved at the package/config target layer:

- `config_toml_missing`: resolved
- DB target class `legacy`: resolved
- DB/Edge target mismatch: resolved

The remaining caveat is runtime health, not target-class alignment: the independent Edge route still returns `503`, and the independent Edge runtime container is stopped.

## Scope

This QA checked package assembly, package file contents, package launcher `-CheckOnly`, package-local backend/API smoke, independent target-class alignment, read-only DB exact-key evidence, and audit redaction.

This QA did not run:

- Supabase init/bootstrap/reset/start
- DB migration/reset/delete/cleanup/prune/drop/truncate
- Docker volume/container/image/network deletion
- Upload Start
- duplicate rerun
- Edge authenticated upload call
- Authorization header or token usage
- operational CSV upload or mutation

## Package Asset Presence

Package assembly result:

| Check | Result |
| --- | --- |
| Required paths | present |
| Supabase source assets | present |
| Operator readiness | ready |
| Denylist matches | 0 |
| Redaction matches | 0 |
| Frontend mode | api |

Required Supabase package assets were present:

| Asset | Result |
| --- | --- |
| `supabase/config.toml` | present |
| `supabase/README.md` | present |
| `supabase/.gitignore` | present |
| `supabase/functions/upload-metrics/index.ts` | present |
| `supabase/migrations/20260608000001_create_all_metrics_upload_contract.sql` | present |

Forbidden package assets were not found in the assembled package scan:

| Class | Result |
| --- | --- |
| Raw `.env` / local Supabase state / DB state | not found |
| Generated package logs/cache/temp | not found |
| Operational CSV fixture | not found |
| `.git`, `.gstack`, `.agents`, `.codex`, `.bkit-codex` | not found |
| `frontend/src`, `frontend/node_modules`, `tests` | not found |
| Zip/checksum/database dump artifacts | not found |

## Launcher CheckOnly Result

The package launcher `-CheckOnly` completed without starting the backend.

Observed launcher policy:

- Operator package Supabase target defaults are prepared.
- Explicit process overrides are still respected.
- Raw DB URL and secret values are hidden.
- Local API token policy is required in operator mode.
- Token value is hidden.
- API docs are disabled in operator mode.

The shortcut installer `-CheckOnly` also completed without writing shortcuts.

No raw DB URL, token, Authorization header, JWT, or secret value was recorded in this report.

## Runtime Readiness

Package-local backend smoke used an alternate local backend port and read-only requests only.

| Check | Result |
| --- | --- |
| `/api/health` | ok |
| `/` | 200 |
| `/upload` | 200 |
| `/logs` | 200 |
| `/settings` | 200 |
| `/api/config` | reachable |
| `/api/runtime/local-supabase` | reachable |
| `/api/audit?limit=5` | reachable |

Independent Supabase runtime summary:

| Runtime item | Result |
| --- | --- |
| Project id | `Extrusion_web_console` |
| `config_toml_missing` | resolved |
| Docker | ready |
| Supabase CLI | ready |
| API port class | independent |
| DB port class | independent |
| Studio port class | independent |
| API reachability | ready |
| DB reachability | ready |
| Studio reachability | ready |
| Edge no-auth GET | `503` service-unavailable |
| Edge no-auth POST with empty safe body | `503` service-unavailable |
| Edge runtime container | stopped |
| Overall runtime status | attention |
| Runtime reason | `non_core_runtime_attention` |

The independent core API/DB/Studio stack is reachable. Edge remains unhealthy, so upload execution readiness is not established by this QA.

## Target Class Comparison

Package-local `/api/config` classified the package targets as follows:

| Setting | Source | Secret handling | Target class |
| --- | --- | --- | --- |
| `localSupabaseProjectPath` | env | value not recorded | independent package path |
| `localSupabaseProjectId` | env | non-secret | independent |
| `localSupabaseApiPort` | env | non-secret | independent |
| `localSupabaseDbPort` | env | non-secret | independent |
| `localSupabaseStudioPort` | env | non-secret | independent |
| `supabaseUrl` | env | raw value not recorded | independent |
| `supabaseDbUrl` | env | hidden | independent |
| `supabaseEdgeUrl` | env | hidden | independent |
| `supabaseAnonKey` | config | hidden | not configured |

Result:

- DB reconciliation target class: `independent`
- Start Upload Edge target class: `independent`
- DB/Edge target alignment: aligned

This resolves the PR #80 caveat where the assembled package path still reported DB class `legacy` while Edge class was `independent`.

## Config, Source, And Auth Presence

Presence-only checks:

| Item | Result |
| --- | --- |
| `plcDataDir` | configured; source folder exists |
| `supabaseDbUrl` | configured through process env; hidden |
| `supabaseUrl` | configured through process env; raw value not recorded |
| `supabaseAnonKey` | missing/hidden |
| `supabaseEdgeUrl` | configured through process env; hidden |
| Local API token guard | required by package launcher |

No raw source path, CSV filename, CSV content, DB URL, token, Authorization header, JWT, or secret value is included in this report.

## Read-Only Exact-Key Evidence

Read-only DB exact-key/count check against the independent DB port:

| Metric | Result |
| --- | --- |
| DB reachable | yes |
| Total rows | 5 |
| Distinct `(timestamp, device_id)` keys | 5 |
| Duplicate exact keys | 0 |

This is read-only evidence only. No upload, duplicate rerun, DB migration, reset, delete, cleanup, prune, drop, or truncate was performed.

## Preview-Only Result

Preview-only rerun was not executed.

Reason: the PR #81 target-class blocker can be verified through package launcher defaults, `/api/config`, runtime readiness, and read-only DB evidence without invoking an upload-adjacent flow. This QA intentionally stays before Upload Start and duplicate rerun execution.

## Audit And Redaction

Audit Logs were queried read-only.

| Marker | Result |
| --- | --- |
| DB URL marker | not found |
| Authorization marker | not found |
| Bearer marker | not found |
| JWT marker | not found |
| User-local path marker | not found |
| CSV filename marker | not found |

Changed-document redaction policy:

- Do not document raw DB URLs.
- Do not document token, Authorization header, JWT, or secret values.
- Do not document operational CSV paths, filenames, content, or full local paths.
- Do not commit untracked PNGs, operational CSV fixtures, `.gstack`, `frontend/dist`, package output, zip, or checksum files.

## Blockers And Caveats

Blockers for duplicate-safe rerun:

- Edge route still returns `503` for direct no-auth GET and POST.
- `supabase_edge_runtime_Extrusion_web_console` is stopped.
- Runtime status remains `attention` with `non_core_runtime_attention`.

Non-blocking for target alignment:

- Grafana was not part of this package DB/Edge target alignment QA.
- Preview-only was intentionally not rerun.
- The local config source folder exists, but its raw path and file names are not documented.

## Final Judgment

| Question | Answer |
| --- | --- |
| Is package `supabase/config.toml` included? | yes |
| Is `config_toml_missing` resolved? | yes |
| Is DB target class independent? | yes |
| Is Edge target class independent? | yes |
| Are DB and Edge target classes aligned? | yes |
| Is independent runtime fully healthy? | no |
| Is Start Upload or duplicate rerun allowed next? | no |

The package target-class implementation is behaving as intended. The next blocker is independent Edge runtime health, not package DB/Edge target configuration.

## Next Step

Run a maintainer-approved independent Edge runtime recovery/investigation QA before any duplicate-safe rerun or bounded Start Upload smoke.
