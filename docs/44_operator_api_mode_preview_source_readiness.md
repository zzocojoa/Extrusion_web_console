# API-Mode Preview Source Readiness Plan

Status: plan

Date: 2026-06-08

Branch: `codex/operator-api-mode-preview-source-readiness`

Scope: document-only readiness plan for rerunning API-mode operator package Upload Preview after the previous rerun stopped at `source_not_configured`.

This plan does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Goal

Make the next API-mode Upload Preview rerun fail only for meaningful runtime or reconciliation reasons, not because the package runtime lacks a configured Preview source.

The previous rerun proved the API-mode package and local Supabase core readiness were far enough to submit Upload Preview, but the run ended before file scanning and DB reconciliation with:

```text
source_not_configured
```

The next rerun must prepare and verify Preview source configuration using presence-only checks. It must not disclose raw source paths, CSV filenames, CSV contents, DB URLs, tokens, Authorization headers, JWTs, or secrets in chat, logs, documents, PR body, screenshots, or audit notes.

## Decision Summary

1. `plcDataDir` is required when Upload Preview includes the PLC source.
2. `temperatureDataDir` is required only when the Temperature source is selected for Preview.
3. `supabaseDbUrl` is required for exact real DB reconciliation.
4. Local Supabase API, Studio, DB, and the runtime status endpoint must be reachable before Preview.
5. API-mode package metadata must still report `frontendMode=api`.
6. Settings values are verified by presence, source, hidden-secret state, and reachability only.
7. Upload Start remains out of scope and must not be clicked during the Preview-only rerun.
8. Any redaction failure stops the rerun.

## Required Configuration

Record only `present`, `missing`, `hidden`, `overridden`, `reachable`, or `unreachable`.

| Purpose | Config key | Env key | Required for Preview-only rerun |
| --- | --- | --- | --- |
| PLC source folder | `plcDataDir` | `EWC_PLC_DATA_DIR` | Yes, when `sources` includes `plc` |
| Temperature source folder | `temperatureDataDir` | `EWC_TEMPERATURE_DATA_DIR` | Yes, only when `sources` includes `temperature` |
| Exact DB reconciliation | `supabaseDbUrl` | `EWC_SUPABASE_DB_URL` | Yes |
| State DB location | `state_db_path` runtime setting | `EWC_STATE_DB_PATH` | Presence check only outside `GET /api/config`; default is acceptable if runtime state works |
| Local Supabase API port | `localSupabaseApiPort` | `EWC_LOCAL_SUPABASE_API_PORT` | Yes |
| Local Supabase DB port | `localSupabaseDbPort` | `EWC_LOCAL_SUPABASE_DB_PORT` | Yes |
| Local Supabase Studio port | `localSupabaseStudioPort` | `EWC_LOCAL_SUPABASE_STUDIO_PORT` | Yes |

`supabaseUrl`, `supabaseAnonKey`, and `supabaseEdgeUrl` are useful for Upload Job and Edge smoke, but they are not the primary blocker for Preview-only source readiness. If the rerun scope expands to Upload Job, those keys become required and must still be verified without exposing values.

## Configuration Channels

Use one of the existing local configuration channels. Do not ask anyone to paste raw values into chat or PR comments.

| Channel | Use | Safety rule |
| --- | --- | --- |
| Settings UI | Preferred when the field is editable | Secret fields must remain hidden; source paths are sensitive and should not be copied into reports |
| `PUT /api/config` | Maintainer-only scripted update for editable fields | Payload must include only keys being intentionally set; never send unchanged secret placeholders |
| Environment or repo `.env` override | For fields intentionally controlled outside config JSON | Backend marks the field overridden; Settings save must not bypass this |
| Operator AppData config | Normal operator runtime config store | Refer to it only as the operator config store, not by full local path |

Backend precedence remains:

```text
process env / repo .env > operator config JSON > defaults
```

If a field is env-overridden, update it through the local env/config owner. Do not try to save over it from the UI.

## Readiness Procedure

### 1. Package And Mode Gate

Confirm the package runtime is the API-mode package under test:

| Check | Expected result |
| --- | --- |
| Package metadata | `frontendMode=api` |
| Browser-visible mock marker scan | No mock-mode markers |
| API docs hardening | `/api/docs`, `/api/openapi.json`, `/api/redoc` return disabled/not found in operator mode |
| Token guard | Read-only APIs succeed; mutating no-token API returns `403` |

Stop with `frontend_mode_mismatch` if the package is not API mode.

### 2. Runtime Gate

Use status checks only. Do not run reset, cleanup, prune, bootstrap, or destructive Docker commands.

| Check | Expected result |
| --- | --- |
| Docker/runtime | Ready |
| Local Supabase API | Reachable |
| Local Supabase Studio | Reachable |
| Local Supabase DB | Reachable |
| Runtime status API | No core runtime blocker |

Grafana can remain a caveat for Preview-only smoke unless the test scope explicitly includes Grafana.

Stop with `runtime_unavailable` if Docker, API, Studio, or DB is unavailable.

### 3. Config Presence Gate

Call `GET /api/config` and record only field-level status for fields exposed by the config API.

For each required field, capture:

| Field evidence | Allowed values |
| --- | --- |
| Presence | `present` or `missing` |
| Source | `config`, `env`, or `default` |
| Override | `overridden` or `editable` |
| Secret display | `hidden` for secret fields |

Do not record `config_file_path` or any raw path value in the QA report. A path-class redaction marker in config output must be treated as a caveat or blocker according to the scan result, but the raw value must not be copied.

Stop with `source_not_configured` before Preview if `plcDataDir` is missing while `plc` is selected, or if all selected source folders are missing.

Stop with `preconfigured_env_missing` before Preview if `supabaseDbUrl` is missing for real DB reconciliation.

`state_db_path` is a runtime setting, not a config API field in the current implementation. Treat it as healthy when the runtime can persist Preview and Audit state; do not record its local value.

### 4. Source Safety Gate

Before clicking Preview, verify the configured source without printing it.

| Check | Expected result |
| --- | --- |
| Source label | Sanitized label only |
| Directory presence | Exists and is readable |
| Scope | Minimal expected source set only |
| Operational CSV handling | Read-only; no copy, delete, edit, or commit |
| Report content | No raw path, filename, CSV content, or row content |

Stop with `source_missing` if the configured source does not exist.

Stop with `sample_unsafe` if the only available path would require broad upload, destructive changes, or raw path/content disclosure.

### 5. Preview-Only Rerun

Run Upload Preview only after gates 1-4 pass.

Expected outcomes:

| Result | Interpretation |
| --- | --- |
| `succeeded` with `dbStatus=reachable` | Preview source and DB reconciliation passed |
| `partial_failed` with `db_unreachable` | Source scan began, but DB was unavailable |
| `failed` with `source_not_configured` | Readiness failed; this plan was not satisfied |
| `failed` with `source_missing` | Source config was present but not usable |

The next rerun should not accept `source_not_configured` as a release-candidate pass.

## Audit And Redaction Checks

After Preview, check:

```text
/api/audit?action=upload.preview
```

Record only:

- audit row exists or missing
- action
- result
- reason code
- sanitized source label if needed
- marker scan counts

Required marker classes:

| Marker class | Expected count |
| --- | ---: |
| DB URL | 0 |
| Token-like value | 0 |
| Authorization header | 0 |
| JWT-like value | 0 |
| Timestamp-style CSV filename | 0 |
| Operational filename-family | 0 |
| Windows absolute path | 0 in reports and audit notes |

If a runtime API response includes local path-class data, do not copy it into the report. Record only the class count and whether it is accepted as a known config-response caveat.

## Acceptance Criteria

The rerun is acceptable only if all of these are true:

1. API-mode package and metadata are confirmed.
2. Local Supabase core readiness is confirmed.
3. Required Preview source config is present before Preview.
4. Required source folders are reachable without raw path disclosure.
5. Upload Preview is executed and does not end with `source_not_configured`.
6. Exact DB reconciliation either succeeds or fails with a clear DB-specific reason after source scanning begins.
7. `upload.preview` audit evidence is present when Preview runs.
8. Secret/path/CSV redaction scan is clean for reports, docs, PR body, screenshots, and audit notes.
9. Upload Start is not clicked.

## Stop Conditions

Stop before Preview when any of these occur:

| Stop condition | Required report label |
| --- | --- |
| Required source config missing | `source_not_configured` |
| Configured source folder unavailable | `source_missing` |
| Source cannot be verified safely | `sample_unsafe` |
| Local Supabase core runtime unavailable | `runtime_unavailable` |
| DB URL config missing for real reconciliation | `preconfigured_env_missing` |
| API-mode metadata mismatch | `frontend_mode_mismatch` |
| Local token unavailable for mutating Preview request | `token_unavailable` |
| Raw secret/path/CSV content exposed | `redaction_failure` |

## Out Of Scope

- Upload Start
- Upload Job authenticated Edge smoke
- DB reset, delete, cleanup, prune, or migration
- Docker volume or container deletion
- Supabase bootstrap or project creation
- Feature code changes
- Launcher, backend, frontend, or packaging script changes
- GitHub Release or tag changes
- Production deploy
- Operational CSV fixture copy, edit, delete, or commit

## Implementation Order

1. Confirm the API-mode package and branch under test.
2. Run package metadata and API-mode marker checks.
3. Confirm local Supabase core readiness.
4. Confirm `GET /api/config` presence-only status for required fields.
5. Confirm selected source folder reachability using sanitized labels only.
6. Execute Upload Preview only.
7. Poll Preview status until terminal.
8. Check Preview item status and counts.
9. Check `upload.preview` audit row.
10. Run redaction scans on reportable evidence.
11. Write a QA report that records statuses and counts without raw values.

## Reviewer Checklist

- The report does not include raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, or full local package paths.
- `source_not_configured` is treated as a blocker, not as an acceptable Preview smoke result.
- `plcDataDir` and selected `temperatureDataDir` readiness are checked before Preview.
- `supabaseDbUrl` presence is checked before real DB reconciliation.
- Upload Start remains explicitly out of scope.
- Any config response path-class caveat is described without copying raw paths.
- No generated package output, `.gstack` artifacts, `frontend/dist`, checksum files, or operational CSV fixtures are committed.
