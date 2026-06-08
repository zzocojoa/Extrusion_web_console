# API-Mode Start Upload Edge/Auth Readiness QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-start-upload-auth-readiness`

Base commit: `4d6ac79d071c814c6c8ab4fbd98150b016e1df5a`

Scope: report-only QA for DB/Edge/auth/source readiness before any API-mode Start Upload smoke.

This report does not change feature code, launcher code, backend code, frontend code, packaging scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, or operational CSV data.

Upload Start was not clicked. Authenticated Edge upload was not attempted.

## Summary

Final verdict: `blocked`.

Operator config presence is now ready for DB, API, anon/auth key, Edge URL, and PLC source. The configured secret-bearing values are provided through local env override and remain hidden in Settings/API output. The PLC source folder exists.

Docker/local Supabase core readiness passed: Docker, local Supabase API, Studio, and DB TCP were ready.

Start Upload readiness remains blocked because Edge runtime is unreachable and the no-auth Edge route smoke did not return the expected auth-required response. The current latest Preview record is not sufficient as a Start Upload precondition because its DB status is `not_checked`. Previous Preview success evidence still exists in `docs/47_operator_api_mode_preview_config_ready_rerun.md`, but a fresh DB-reachable Preview should be rerun after Edge readiness is fixed and before any Start Upload attempt.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker available | yes |
| Local Supabase API reachable | yes |
| Studio reachable | yes |
| DB TCP reachable | yes |
| Edge runtime reachable | no |
| Grafana reachable | no |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |

Grafana is recorded as a caveat. It is not a direct Start Upload blocker.

## Operator Config Presence

| Field | Presence | Display | Source |
| --- | --- | --- | --- |
| `supabaseDbUrl` | `configured` | `hidden` | env override present |
| `supabaseUrl` | `configured` | `not_secret` | env override present |
| `supabaseAnonKey` | `configured` | `hidden` | env override present |
| `supabaseEdgeUrl` | `configured` | `hidden` | env override present |
| `plcDataDir` | `configured` | `not_secret` | env override present |
| source-folder exists | yes | not recorded by path | env override present |

The config API intentionally does not return raw secret values for secret-bearing fields. Presence was confirmed through local env key presence and non-empty status only; raw values are not recorded here.

## Auth And Edge Behavior

| Check | Result |
| --- | --- |
| Edge URL presence | `configured` |
| Edge no-auth response | `503` |
| Edge no-auth interpretation | `blocked/unavailable` |
| Expected no-auth response | `401` or equivalent auth-required/validation response |
| Authenticated Edge call | not run |
| Authorization header/token output | absent |

The no-auth Edge route did not prove route/auth readiness. A future readiness rerun should reach either expected `401` or an equivalent auth-required/validation response before Start Upload is considered.

## Preview Precondition

| Check | Result |
| --- | --- |
| Previous Preview success evidence | present in prior QA report |
| Current latest Preview status | `succeeded` |
| Current latest Preview DB status | `not_checked` |
| Current latest Preview target count | `0` |
| Current latest Preview upload rows | `0` |
| Current latest Preview audit rows | present |
| Fresh Preview rerun in this pass | not run |

The current latest Preview is not a Start Upload precondition pass because DB status is `not_checked`. Since Edge readiness already failed, this QA did not run a fresh Preview-only request.

## Start Upload Decision

| Decision item | Result |
| --- | --- |
| Start Upload allowed | no |
| Upload Start clicked | no |
| Duplicate rerun | not run |
| Authenticated Edge upload | not run |
| Large operational source upload | not run |
| DB row count delta | not measured |
| `upload.start` audit row expected | no, because Start Upload was not clicked |

Start Upload remains blocked until Edge runtime and no-auth route readiness pass and a fresh Preview finishes with DB status `reachable`.

## Stop Conditions

| Stop condition | Status |
| --- | --- |
| `edge_runtime_unreachable` | active |
| `edge_auth_unavailable` | active |
| `preview_not_uploadable` | active for current latest Preview |
| `preconfigured_env_missing` | cleared |
| `runtime_unavailable` | cleared for core local Supabase runtime |
| `sample_unsafe` | not evaluated because Start Upload is blocked earlier |

## Redaction And Artifact Policy

| Check | Result |
| --- | --- |
| Raw DB URL in report | absent |
| Raw token/auth/JWT in report | absent |
| Raw Authorization header in report | absent |
| Raw operational CSV path/content/filename in report | absent |
| Full local package path in report | absent |
| Package output/zip/checksum committed | no |
| `.gstack` artifacts committed | no |
| `frontend/dist` committed | no |
| Operational CSV fixture committed | no |

## Safety

| Operation | Result |
| --- | --- |
| DB reset/delete/cleanup/prune | not run |
| Docker volume/container delete | not run |
| GitHub Release/tag create or update | not run |
| Production deploy | not run |
| Feature code change | none |
| Launcher/backend/frontend/packaging script change | none |

## Findings

### Passed

1. `config_presence_ready`: required DB/API/auth/Edge/source config keys are present through local env override.
2. `secret_hidden`: secret-bearing config values are not exposed by Settings/API evidence.
3. `source_ready`: PLC source is configured and source-folder existence passed.
4. `runtime_core_ready`: Docker, local Supabase API, Studio, and DB TCP are ready.

### Blockers

1. `edge_runtime_unreachable`: runtime status reports Edge runtime unreachable.
2. `edge_no_auth_unavailable`: no-auth Edge route returned `503` instead of expected auth-required reachability.
3. `preview_precondition_not_current`: current latest Preview DB status is `not_checked`; a fresh DB-reachable Preview is required after Edge readiness is fixed.

### Caveats

1. `grafana_unreachable`: Grafana remains unreachable, but it is not a direct Start Upload blocker.
2. `preview_not_rerun`: Preview-only rerun was skipped because Edge readiness already blocked Start Upload.

## Verdict

`blocked`

Reason: DB/API/auth/source config presence is ready, but Edge runtime and Edge no-auth route readiness are not ready. Current latest Preview evidence is not sufficient for Start Upload because DB status is `not_checked`.

## Next Step

Fix local Edge runtime readiness first. Then rerun this presence-only readiness check. If Edge reaches expected no-auth behavior and a fresh Preview finishes with `dbStatus=reachable`, create a separate QA-only Start Upload smoke branch and run exactly one approved Start Upload using a minimal duplicate-safe sample.
