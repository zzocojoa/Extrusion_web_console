# Operator Stage 1 Preview-Only QA

## Summary

- Date: 2026-06-12
- Branch: `codex/operator-stage-1-preview-only`
- Base commit: `2fa0fbea25d9b5566f2d48024f4295d018f37f9e`
- QA mode: report-only
- Stage: 1, small operational sample Preview-only
- Verdict: `blocked`
- Stage 2 small operational sample Start Upload allowed next step: `no`

This QA run attempted to advance from Stage 0 readiness recheck into Stage 1
small operational sample Preview-only. The stage was stopped before any Preview
because the independent Edge runtime precondition failed: the Edge container was
not running and direct no-auth Edge probes returned `503`.

No operational source was uploaded, no Start Upload was run, and no duplicate
rerun or authenticated Edge call was performed.

## Explicitly Not Performed

- feature code, launcher, backend, frontend, or packaging script edits;
- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Upload Preview, because the Edge precondition failed before the Preview gate;
- Upload Start;
- duplicate rerun;
- Edge authenticated upload call;
- Authorization header or token use;
- full operational dataset rollout;
- production deploy;
- GitHub Release or tag creation.

## QA Environment

| Area | Result |
| --- | --- |
| Package path class | `repo-external-temp-package` |
| Frontend package mode for assembly | `api` |
| Runtime target | independent `Extrusion_web_console` |
| Legacy fallback | not used |
| Source scope | no operational source selected or consumed |
| Preview execution | not run due to stop condition |

The package path and local source details are intentionally recorded as
sanitized classes only. No raw package output path, operational CSV path,
operational filename, full local path, CSV content, or row content is recorded.

## Package Smoke

| Check | Result |
| --- | --- |
| Package assembly | `passed` |
| Package `supabase/config.toml` | present |
| Package `upload-metrics` function asset | present |
| Package migration assets | present |
| Package forbidden asset scan | `0` matches |
| Package launcher `-CheckOnly` | exit code `0` |
| Launcher raw-value leak scan | clean |
| Package zip/checksum | not created |

The package was assembled only for QA smoke. Package output was not committed.

## Runtime Readiness Results

| Check | Result | Notes |
| --- | --- | --- |
| Sanitized package Supabase status | exit code `0` | Raw status output was suppressed. |
| API port | `reachable` | Independent API port class. |
| DB port | `reachable` | Independent DB port class. |
| Studio port | `reachable` | Independent Studio port class. |
| Edge runtime container | `not_running` | Stop condition. |
| Edge no-auth `GET` | `503` server-error class | No Authorization header used. |
| Edge no-auth `POST {}` | `503` server-error class | Safe empty object body only. |
| Package-local `/api/health` | `ok` | Temporary package-local backend only. |
| Package-local `/api/config` | `passed` | Secret fields stayed hidden. |
| Package-local `/api/runtime/local-supabase` | `edge_not_ready` | Confirms the Edge blocker from package path. |

The runtime gate failed before the Preview step. API, DB, and Studio were
reachable, but Stage 1 requires Edge no-auth auth-class readiness to remain
current before touching an operational sample.

## Config And Target Class

| Config item | Presence result | Raw value policy |
| --- | --- | --- |
| `plcDataDir` | configured from process env | value not recorded |
| `supabaseDbUrl` | configured from process env, secret field hidden | value not recorded |
| `supabaseUrl` | configured from process env | value not recorded |
| `supabaseAnonKey` | configured from process env, secret field hidden | value not recorded |
| `supabaseEdgeUrl` | configured from process env, secret field hidden | value not recorded |

DB and Edge target class remained intended for the independent
`Extrusion_web_console` stack. However, target class alignment cannot advance
Stage 1 while the Edge runtime is stopped and no-auth probes return `503`.

## Source Scope

| Check | Result |
| --- | --- |
| Bounded source selected | not selected |
| Operational source consumed | no |
| Operational original modified | no |
| Operational full dataset used | no |
| Sanitized source label | not applicable |
| Sample row count | not applicable |

The source gate was intentionally not opened after the Edge stop condition was
confirmed.

## Preview Result

| Metric | Result |
| --- | --- |
| Preview status | not run |
| `dbStatus` | not checked |
| total file count | not applicable |
| already-in-db count | not applicable |
| upload-target count | not applicable |
| excluded count | not applicable |
| failed/invalid count | not applicable |
| DB row-count delta | not checked |

No Preview API call was made in the successful gated QA path. This preserves
Stage 1 safety and keeps the blocker isolated to runtime readiness.

## Stop Conditions Triggered

| Stop condition | Result |
| --- | --- |
| Edge unhealthy or `503` | triggered |
| Docker/Supabase instability | carried forward; Edge not running and vector remains a caveat |
| DB/Edge target mismatch | not observed as the primary issue |
| `dbStatus=not_checked` | not applicable because Preview did not run |
| unexpected target count | not applicable |
| failed/invalid count above threshold | not applicable |
| raw secret/path/token exposure | not observed |
| operator cannot confirm bounded source scope | avoided by stopping before source selection |

## Caveats

| Caveat | Current state | Impact |
| --- | --- | --- |
| Edge runtime | container `not_running`; no-auth route `503` | Blocks Stage 1 Preview-only. |
| Vector | previously carried as restarting/stopped caveat | Continue to record separately from core API/DB/Studio readiness. |
| Grafana | previously carried as status/link caveat | Not a core upload gate unless operator requires it. |
| Supabase start instability history | start/stop was not run in this QA | Requires separate approved recovery if Edge remains stopped. |

## Redaction Result

- Raw secret values were not recorded.
- Raw DB URL was not recorded.
- Token, Authorization header, and JWT values were not used or recorded.
- Operational CSV path, content, filename, and full local path were not
  recorded.
- Raw Supabase status output was suppressed.
- Package output path was not recorded in this report.
- Launcher and API smoke output were reduced to class, presence, and status
  results.

## Stage 1 Verdict

Stage 1 is `blocked`.

The next step is not Stage 2 Start Upload. The next step is an operator package
Edge runtime recovery or investigation QA PR that is explicitly allowed to use
maintainer-approved `supabase stop` / `supabase start` if needed, while still
forbidding reset, migration, Docker delete, Upload Preview, Upload Start,
duplicate rerun, and authenticated Edge upload calls.

## Validation

| Command or check | Result |
| --- | --- |
| Targeted backend package/runtime/upload preview/upload job tests | `125 passed` |
| `npm run typecheck` | passed from `frontend` |
| `npm run build:api` | passed from `frontend` |
| API-mode package assembly smoke | passed |
| Package launcher `-CheckOnly` | passed |
| Package-local API smoke | health/config passed; runtime Edge not ready |
| Edge no-auth `GET` / `POST {}` | both `503` |
| `npm run build` | passed from `frontend` |
| `npm run qa:screenshots` | passed |

## Next Action

Create an Edge runtime recovery or investigation QA PR before retrying Stage 1.
Do not run Stage 2 Start Upload or any full operational dataset rollout while
Edge no-auth probes return `503`.
