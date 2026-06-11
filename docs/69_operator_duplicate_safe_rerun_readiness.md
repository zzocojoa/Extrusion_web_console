# Operator Package Duplicate-Safe Rerun Readiness QA

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-duplicate-safe-rerun-readiness`
- Base commit: `8bdbf16c59d8437de8f9aa2b933ee8b59d15652e`
- QA mode: report-only readiness gate
- Package path class: assembled operator package, not repo dev backend
- Readiness verdict: `ready_with_caveats`
- Duplicate-safe rerun allowed next step: `yes_with_caveats`

This QA verifies whether the operator package path is ready for a separate bounded duplicate-safe rerun. It does not execute the duplicate rerun and does not run Upload Start.

Readiness is satisfied for the required gate:

- Package-local `supabase/config.toml` is present through package assembly.
- DB target class is independent.
- Edge target class is independent.
- Independent API, DB, Studio, and Edge are reachable.
- Direct no-auth Edge `GET` and `POST {}` return auth-class `401`.
- Package-local `/api/runtime/local-supabase` reports Edge `ready`.
- The independent DB exact-key baseline remains total `5`, distinct exact keys `5`, duplicate exact keys `0`.

The next duplicate-safe rerun should be a separate bounded QA PR. Expected DB row-count delta for that rerun is `0`.

## Scope And Guardrails

This QA did not modify feature code, launcher code, backend code, frontend code, packaging scripts, production deployment, GitHub Release, or GitHub tag.

This QA did not run:

- Supabase init/bootstrap/reset
- DB migration/reset/delete/cleanup/prune/drop/truncate
- Docker volume/container/image/network deletion
- Upload Start
- duplicate rerun
- Edge authenticated upload call
- Authorization header or token usage
- operational full-source upload
- operational source modification/deletion
- Upload Preview

Preview-only was not performed because the readiness gate could be proven with package runtime readiness, Edge no-auth probes, package-local config classification, read-only DB exact-key counts, and read-only audit redaction checks.

## QA Environment

| Item | Result |
| --- | --- |
| Operator package frontend mode | api |
| Package required paths | present |
| Package Supabase assets | present |
| Package denylist matches | 0 |
| Package redaction matches | 0 |
| Package launcher `-CheckOnly` | passed |
| Shortcut installer `-CheckOnly` | passed |
| Package backend smoke | alternate loopback port |
| Browser/page smoke | `/`, `/upload`, `/logs`, `/settings` all `200` |
| Raw package output path | not recorded |

The assembled package included repository-owned Supabase source assets. Package output, zip, checksum, logs, cache, local DB state, and operational CSV data were not committed.

## Package Runtime Readiness

| Check | Result |
| --- | --- |
| `/api/health` | ok |
| `/api/config` | reachable |
| `/api/runtime/local-supabase` | reachable |
| `/api/audit?limit=10` | reachable |
| Project id | `Extrusion_web_console` |
| `config_toml_missing` | resolved |
| Supabase API | ready |
| Supabase DB | ready |
| Supabase Studio | ready |
| Supabase Edge | ready |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Grafana | unreachable |

The `attention` status is caused by a non-core runtime dependency, not by the Edge upload path. Edge is ready in the package-local runtime response.

## Edge Health

| Check | Result |
| --- | --- |
| Direct no-auth Edge `GET` | `401` auth-class |
| Direct no-auth Edge `POST {}` | `401` auth-class |
| Edge runtime container | running |
| Edge readiness in package runtime | ready |
| Edge authenticated upload call | not run |
| Authorization header/token use | not run |

This confirms the PR #83 Edge recovery state is still intact for the operator package path.

## DB And Target Alignment

Package-local `/api/config` classified the targets as follows:

| Setting | Result |
| --- | --- |
| `localSupabaseApiPort` | independent |
| `localSupabaseDbPort` | independent |
| `localSupabaseStudioPort` | independent |
| `supabaseDbUrl` | hidden |
| `supabaseEdgeUrl` | hidden |
| `supabaseUrl` | process/package target class |
| DB target class | independent |
| Edge target class | independent |
| DB/Edge target alignment | aligned |

The operator package path still points DB reconciliation and Edge routing at the independent `Extrusion_web_console` stack class.

## DB Exact-Key Baseline

Read-only exact-key baseline against the independent DB:

| Metric | Result |
| --- | --- |
| DB reachable | yes |
| Total rows | 5 |
| Distinct `(timestamp, device_id)` keys | 5 |
| Duplicate exact keys | 0 |

Interpretation:

- The bounded rows from the prior approved upload remain present.
- The exact-key uniqueness/upsert safety is intact at the observable DB state level.
- A bounded duplicate-safe rerun should accept/upsert the same bounded input while producing expected DB row-count delta `0`.
- This QA did not execute that rerun.

## Duplicate-Safe Preconditions

| Precondition | Result |
| --- | --- |
| Expected rerun source class | bounded prior upload class |
| Expected rerun row scope | `5` rows |
| Expected DB row-count delta | `0` |
| Existing exact keys present | yes |
| Duplicate exact keys before rerun | `0` |
| DB target independent | yes |
| Edge target independent | yes |
| Edge no-auth auth boundary reachable | yes |
| Actual duplicate rerun | not run |
| Upload Start | not run |

Readiness decision: a separate bounded duplicate-safe rerun QA can proceed with caveats. It must remain bounded and must not use an operational full-source upload.

## Audit And Redaction

Read-only audit checks:

| Marker | Result |
| --- | --- |
| DB URL marker | not found |
| Authorization marker | not found |
| Bearer marker | not found |
| JWT marker | not found |
| User-local path marker | not found |
| CSV filename marker | not found |

Report redaction:

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Raw Supabase status output | absent |
| Raw package output path | absent |
| Raw CSV path/content/filename in report | absent |
| Operational source path/content/filename in report | absent |

`supabase status` returned availability markers with raw output suppressed. The raw output contained credential-like markers, so only class-level availability was recorded.

## Blockers And Caveats

Blockers:

- None for duplicate-safe rerun readiness.

Caveats:

1. `grafana_unreachable`: package runtime remains `attention` because Grafana is unreachable. Grafana is link/status-only and not the Edge upload path.
2. `vector_restarting`: the vector service is still restarting. Core API/DB/Studio/Edge readiness is intact.
3. `supabase_status_stopped_services_marker`: sanitized `supabase status` still reported stopped service markers. Raw service output was suppressed because status output includes credential-like material.
4. `preview_not_rerun`: Preview-only was not run in this readiness gate.
5. `bounded_only`: the next duplicate-safe rerun must use the same bounded source class and must remain outside operational full-source upload.

## Validation

| Command/check | Result |
| --- | --- |
| Targeted package/runtime/upload preview/upload job tests | `140 passed` |
| `npm run typecheck` | passed |
| `npm run build:api` | passed |
| `npm run build` | passed |
| `npm run qa:screenshots` | passed |
| Package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local API smoke | passed |
| Direct no-auth Edge probes | auth-class |
| Read-only DB exact-key baseline | reachable, `5` total, `5` distinct, `0` duplicate |
| Audit marker scan | clean |

## Final Judgment

| Question | Answer |
| --- | --- |
| Is package `supabase/config.toml` present? | yes |
| Is `config_toml_missing` resolved? | yes |
| Is DB target class independent? | yes |
| Is Edge target class independent? | yes |
| Is Edge no-auth route auth-class? | yes |
| Is package runtime Edge ready? | yes |
| Are bounded exact keys present? | yes |
| Is duplicate-safe rerun expected DB delta `0`? | yes |
| Was duplicate rerun executed? | no |
| Was Upload Start executed? | no |
| Is duplicate-safe rerun allowed next? | yes, with caveats |

## Next Step

Proceed to a separate `operator package duplicate-safe rerun` QA PR only after this readiness report is reviewed and merged. The rerun PR should execute exactly one bounded duplicate-safe rerun, verify accepted/upsert class results, and confirm DB row-count delta remains `0`. Operational full-source upload remains out of scope.
