# API-Mode Operator Package Preview-Ready Rerun QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-preview-ready-rerun`

Base commit: `5fb48810a149ed5447825e79256fc3543addf1a0`

Scope: report-only rerun QA for API-mode operator package Upload Preview after Docker/local Supabase core readiness was restored.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Summary

Final verdict: `blocked`.

API-mode package build, metadata, package assembly, zip/checksum verification, zip-entry hygiene, package redaction scan, extracted package smoke, packaged import smoke, launcher check-only, shortcut check-only, route smoke, token guard smoke, API docs hardening smoke, browser-visible mock marker checks, and local Supabase core readiness checks passed.

Upload Preview was executed against the API-mode package runtime. The request was accepted with `202`, but the run finished as `failed` with `source_not_configured`. The package runtime did not proceed to real DB reconciliation, so this is not yet a successful Preview-ready release-candidate smoke.

An `upload.preview` audit row was created with `failure/source_not_configured`. Audit marker scan found no DB URL, token, Authorization, JWT, timestamp-style CSV, operational filename-family, or Windows path marker classes.

Upload Start was not clicked.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `5fb48810a149ed5447825e79256fc3543addf1a0` |
| QA branch | `codex/operator-api-mode-preview-ready-rerun` |
| Package label | `ewc-api-mode-preview-ready-rerun-20260608-rc1` |
| Package output | Repo-external temp output root |
| Extract output | Separate repo-external temp output root |
| Package version | `0.1.0.0` |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, or documented by path/content |

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker | `ready` |
| Local Supabase API | Reachable |
| Local Supabase Studio | `200` |
| Local Supabase DB TCP | Connected |
| Edge route no-auth | `401`, reachable |
| Web console runtime overall | `attention` |
| Runtime reason code | `non_core_runtime_attention` |
| Grafana | Unreachable |

Grafana is recorded as a caveat. It is not a blocker for Upload Preview reconciliation.

## API-Mode Build

| Check | Result |
| --- | --- |
| `npm run build:api` | Passed |
| Build output mode line | `frontend build mode: api` |
| `frontend/dist/frontend-build-info.json` present | Passed |
| Frontend build metadata | `frontendMode=api` |

## Package Assembly

| Check | Result |
| --- | --- |
| Assembly command | `-FrontendMode api -CreateZip` |
| Required paths | Present |
| Operator readiness | Ready |
| Assembly denylist validation | `0` matches |
| Assembly redaction validation | `0` matches |
| Source cache pruned | `42` |
| Runtime cache pruned | `1644` |
| Runtime test segments pruned | `8` |
| Runtime agent entries pruned | `8` |
| Runtime metadata preserved | `275` |
| Package folder metadata | `frontendMode=api` |
| Package dist metadata | `frontendMode=api` |
| Zip-internal metadata | `frontendMode=api` |
| Zip creation | Passed |
| Checksum file creation | Passed |
| SHA-256 verification | Passed |

The package folder metadata hash matched the generated zip, and the adjacent checksum file matched the zip.

## Zip Entry Scan

| Check | Count | Result |
| --- | ---: | --- |
| `.agents` entries | 0 | Pass |
| Runtime test segment entries | 0 | Pass |
| Cache/bytecode entries | 0 | Pass |
| Marker-heavy docs | 0 | Pass |
| CSV files | 0 | Pass |
| Raw env files | 0 | Pass |

The `.agents` blocker remains resolved.

## Package Redaction Scan

Count-only scan using the package assembly release marker set:

| Marker class | Count | Result |
| --- | ---: | --- |
| Database URL marker | 0 | Pass |
| Authorization bearer marker | 0 | Pass |
| Credential-like marker | 0 | Pass |
| JWT-like marker | 0 | Pass |
| Service role marker | 0 | Pass |
| Anon key marker | 0 | Pass |
| Timestamp-style CSV marker | 0 | Pass |
| Operational filename-family marker | 0 | Pass |
| Windows absolute path marker | 0 | Pass |

This report intentionally excludes raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, and full local package paths.

## Extracted Package Smoke

| Check | Result |
| --- | --- |
| Separate extract directory | Passed |
| Package root present | Passed |
| `frontend/dist/index.html` present | Passed |
| `.venv/Scripts/python.exe` present | Passed |
| Extracted `.agents` count | 0 |
| Extracted runtime test segment count | 0 |
| Extracted cache/bytecode count | 0 |
| Packaged import smoke | `import_ok` |
| Launcher `-CheckOnly` | Passed |
| Shortcut installer `-CheckOnly` | Passed |

## Launcher And HTTP Smoke

| Check | Result |
| --- | --- |
| Package-owned alternate-port launcher smoke | Passed |
| `GET /` | `200` |
| `GET /upload` | `200` |
| `GET /logs` | `200` |
| `GET /settings` | `200` |
| `GET /api/health` | `200` |
| `GET /api/config` | `200` |
| `GET /api/audit?limit=1` | `200` |
| No-token `PUT /api/config` | `403` |
| `GET /api/docs` | `404` |
| `GET /api/openapi.json` | `404` |
| `GET /api/redoc` | `404` |

Read-only APIs succeeded without a token. The mutating no-token request was blocked. Operator API docs routes stayed disabled.

## API-Mode UI Marker Check

| Check | Result |
| --- | --- |
| Dashboard visible via browser navigation | Passed |
| Upload visible via browser navigation | Passed |
| Logs visible via browser navigation | Passed |
| Settings visible via browser navigation | Passed |
| Browser-visible `mock://` marker | 0 observed |
| Browser-visible `mock_` marker | 0 observed |
| Browser-visible mock-mode label | 0 observed |

The browser-visible pages did not expose mock-mode markers.

## Upload Preview

| Check | Result |
| --- | --- |
| Upload Preview request | Accepted, `202` |
| Preview run status | `failed` |
| Error code | `source_not_configured` |
| DB status | `not_checked` |
| Total items | 1 |
| Target count | 0 |
| Already in DB count | 0 |
| Partial overlap count | 0 |
| Risky count | 1 |
| Excluded count | 0 |
| Upload rows | 0 |
| DB matched rows | 0 |
| Upload Start clicked | No |

The run failed before DB reconciliation because the package runtime did not have a configured Preview source. No upload was started.

## Audit And Redaction

| Check | Result |
| --- | --- |
| `/api/audit?action=upload.preview&limit=5` | `200` |
| Matching audit row | Found |
| Audit action | `upload.preview` |
| Audit result | `failure` |
| Audit error code | `source_not_configured` |

Audit marker scan:

| Marker class | Count |
| --- | ---: |
| DB URL | 0 |
| Token-like | 0 |
| Authorization | 0 |
| JWT | 0 |
| Timestamp-style CSV | 0 |
| Operational filename-family | 0 |
| Windows path | 0 |

Runtime config probe caveat:

| Response | DB URL | Token-like | Authorization | JWT | Timestamp CSV | Operational filename-family | Windows path class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `/api/config` | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `/api/audit?limit=1` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The config response path-class count is recorded as a caveat without raw value disclosure.

## Findings

### Resolved

1. `runtime_core_ready`: Docker, API, Studio, DB, and Edge were reachable for Preview core readiness.
2. `zip_agents_entries`: `.agents` package and zip-entry count remains `0`.
3. `api_mode_metadata`: build, package, and zip metadata consistently record `frontendMode=api`.
4. `operator_api_smoke`: route, token guard, and API docs hardening smoke passed.
5. `mock_marker_absence`: browser-visible API-mode pages did not expose mock markers.
6. `preview_audit_created`: failed Preview wrote an `upload.preview` audit row with safe marker scan results.

### Blockers

1. `source_not_configured`: package runtime accepted the Preview request but failed before DB reconciliation because the Preview source is not configured.

### Caveats

1. `grafana_unreachable`: runtime overall status is `attention`, but Grafana is not a Preview blocker.
2. `api_config_local_path_marker`: `/api/config` includes local path-class output. No raw path is recorded here, and no DB URL/token/Authorization/JWT/operational filename marker class was detected.

## Reproduction Conditions

1. Confirm Docker/local Supabase core readiness.
2. Build frontend with `npm run build:api`.
3. Assemble package with `-FrontendMode api -CreateZip`.
4. Verify frontend and package metadata record `frontendMode=api`.
5. Verify zip checksum.
6. Run zip-entry hygiene and redaction scans.
7. Extract package into a separate repo-external temp folder.
8. Run package import smoke.
9. Run launcher and shortcut `-CheckOnly`.
10. Start package runtime on a free loopback test port.
11. Smoke UI routes, read-only APIs, no-token mutation guard, and docs hardening routes.
12. Check browser-visible pages for mock-mode markers.
13. Execute Upload Preview only.
14. Verify Preview terminal status and audit row.
15. Do not click Upload Start.

## Verdict

`blocked`

Reason: Docker/local Supabase core readiness and package smoke passed, and Upload Preview was executed, but the package runtime failed with `source_not_configured`. The release-candidate still needs Preview source configuration before a successful Preview-only smoke can pass.

## Next Step

Prepare the package runtime's Preview source configuration locally, using presence-only checks and sanitized labels. After that, rerun Preview-only smoke. Do not click Upload Start during the rerun.
