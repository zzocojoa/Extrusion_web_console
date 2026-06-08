# API-Mode Preview Source-Ready Rerun QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-preview-source-ready-rerun`

Base commit: `fb759aebfa4d9f2d48b67b82c9910819f14eb1c0`

Scope: report-only QA rerun for API-mode operator package Upload Preview readiness after PR #55 documented the source readiness checklist.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Summary

Final verdict: `blocked`.

API-mode frontend build, package assembly, package metadata, zip/checksum verification, zip-entry hygiene, package redaction scan, launcher check-only, shortcut check-only, HTTP route smoke, browser page smoke, no-token mutation guard, API docs hardening, and mock marker absence checks passed.

Upload Preview was not executed. PR #55 stop conditions were met before Preview:

1. Required Preview source config was missing.
2. Real DB reconciliation config was missing.
3. Docker/local Supabase core readiness was blocked.

Upload Start was not clicked.

No DB reset, delete, cleanup, prune, migration, Docker volume deletion, Docker container deletion, GitHub Release/tag change, or production deploy was performed.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `fb759aebfa4d9f2d48b67b82c9910819f14eb1c0` |
| QA branch | `codex/operator-api-mode-preview-source-ready-rerun` |
| Package label | `ewc-api-mode-preview-source-ready-rerun` timestamped label |
| Package output | Repo-external temp output root |
| Package version | `0.1.0.0` |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, edited, or documented by path/content |

## Source Readiness

Presence-only results from the package runtime config API:

| Field | Presence | Source | Env/repo override | Path check |
| --- | --- | --- | --- | --- |
| `plcDataDir` | `missing` | `default` | `absent` | `not_checked` |
| `temperatureDataDir` | `missing` | `default` | `absent` | `not_checked` |
| `supabaseDbUrl` | `missing` | `default` | `absent` | `not_checked` |

`plcDataDir` is required for the default Preview source selection. Because it was missing, source path existence was intentionally not probed with a raw value. `temperatureDataDir` is recorded because it is part of the checklist, but the default Preview request selects PLC only. `supabaseDbUrl` was missing, so real exact DB reconciliation was not ready.

Stop condition result: `source_not_configured` and `preconfigured_env_missing`.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Runtime overall status | `blocked` |
| Runtime reason code | `docker_unavailable` |
| Docker | Unavailable |
| Local Supabase API | Unreachable |
| Local Supabase Studio | Unreachable |
| Local Supabase DB | Unreachable |
| Edge route | Unreachable |
| Grafana | Unreachable |

This is a core runtime blocker for Preview. The rerun did not attempt Upload Preview after this gate failed.

## API-Mode Build

| Check | Result |
| --- | --- |
| `npm run build:api` | Passed |
| Build output mode line | `frontend build mode: api` |
| `frontend/dist/frontend-build-info.json` | Present |
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
| Package metadata | `frontendMode=api` |
| Dist metadata | `frontendMode=api` |
| Zip creation | Passed |
| Checksum verification | Passed |

## Zip Entry And Redaction Scan

| Check | Count | Result |
| --- | ---: | --- |
| `.agents` entries | 0 | Pass |
| Runtime test segment entries | 0 | Pass |
| Cache/bytecode entries | 0 | Pass |
| CSV entries | 0 | Pass |
| Raw env entries | 0 | Pass |

Package text redaction scan:

| Marker class | Count | Result |
| --- | ---: | --- |
| Database URL marker | 0 | Pass |
| Authorization marker | 0 | Pass |
| Credential-like marker | 0 | Pass |
| JWT marker | 0 | Pass |
| Timestamp-style CSV marker | 0 | Pass |
| Operational filename-family marker | 0 | Pass |
| Windows absolute path marker | 0 | Pass |

The previous `.agents` package blocker remains resolved.

## Launcher And HTTP Smoke

| Check | Result |
| --- | --- |
| `launcher/start_web_console.ps1 -CheckOnly` | Passed |
| `launcher/install_shortcuts.ps1 -CheckOnly` | Passed |
| Package runtime launch | Passed |
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

The package runtime was stopped after smoke. Only the launcher-owned backend process was stopped.

## Browser Smoke

Headless browser smoke opened the package runtime pages:

| Page | HTTP status | Non-blank | Mock markers |
| --- | ---: | --- | ---: |
| Dashboard | 200 | Yes | 0 |
| Upload | 200 | Yes | 0 |
| Logs | 200 | Yes | 0 |
| Settings | 200 | Yes | 0 |

Mock marker checks:

| Marker | Count |
| --- | ---: |
| `mock://` | 0 |
| `mock_` | 0 |
| Mock-mode UI label | 0 |

## Upload Preview

| Check | Result |
| --- | --- |
| Upload Preview executed | No |
| Reason | Stop condition before Preview |
| Stop condition | `source_not_configured`, `preconfigured_env_missing`, `runtime_unavailable` |
| Upload Start clicked | No |
| Preview terminal status | Not available |
| Preview counts | Not available |
| New `upload.preview` audit row | Not expected |

Preview was intentionally not forced because the checklist requires stopping when source config or Docker/local Supabase core readiness is missing.

## Audit And Redaction

Read-only audit endpoint smoke passed.

Runtime response marker scan:

| Response | DB URL | Token-like | Authorization | JWT | Timestamp CSV | Operational filename-family | Windows path class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `/api/config` | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `/api/audit?action=upload.preview&limit=5` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The config response path-class count is recorded as a caveat without raw value disclosure. This report intentionally excludes raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, and full local package paths.

## Findings

### Passed Checks

1. `api_mode_build`: `npm run build:api` passed and produced API-mode metadata.
2. `api_mode_package`: package and dist metadata recorded `frontendMode=api`.
3. `zip_checksum`: zip checksum verification passed.
4. `zip_hygiene`: `.agents`, tests, cache, bytecode, CSV, and raw env zip counts were `0`.
5. `package_redaction`: package redaction marker counts were `0`.
6. `launcher_check_only`: launcher and shortcut check-only passed.
7. `operator_http_smoke`: pages, read-only APIs, token guard, and docs hardening passed.
8. `browser_smoke`: Dashboard, Upload, Logs, and Settings were non-blank.
9. `mock_marker_absence`: browser-visible mock markers were absent.

### Blockers

1. `source_not_configured`: required Preview source config was missing.
2. `preconfigured_env_missing`: `supabaseDbUrl` was missing for real DB reconciliation.
3. `runtime_unavailable`: Docker/local Supabase core readiness was blocked.

### Caveats

1. `api_config_local_path_marker`: `/api/config` contains path-class output. Raw values are not recorded in this report.
2. `preview_not_executed`: Upload Preview was correctly skipped because stop conditions were met.

## Reproduction Conditions

1. Start from `main` at the recorded base commit.
2. Build the frontend with `npm run build:api`.
3. Assemble an API-mode operator package with `-FrontendMode api -CreateZip` into a repo-external temp output root.
4. Verify package and dist metadata are `frontendMode=api`.
5. Verify zip checksum and zip-entry hygiene.
6. Run launcher and shortcut `-CheckOnly`.
7. Start the package runtime on a free loopback port.
8. Smoke pages, read-only APIs, no-token mutation guard, and docs hardening routes.
9. Check browser-visible pages for mock markers.
10. Check config presence using `GET /api/config` without recording raw values.
11. Check local Supabase runtime readiness.
12. Stop before Preview if source config or runtime readiness is missing.

## Verdict

`blocked`

Reason: package build and smoke gates passed, but the source readiness and runtime gates failed before Upload Preview. The rerun complied with PR #55 by not forcing Preview when `source_not_configured`, `preconfigured_env_missing`, and `runtime_unavailable` conditions were present.

## Next Step

Prepare local operator config and local Supabase runtime so that:

1. `plcDataDir` is configured and the source exists.
2. `supabaseDbUrl` is configured and hidden.
3. Docker/local Supabase API, Studio, and DB are reachable.

Then rerun Preview-only smoke on a new QA branch. Do not click Upload Start during that rerun.
