# API-Mode Operator Package Release-Candidate Smoke QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-release-candidate-smoke`

Base commit: `f8f0310e466c6ba5e826416c1187560ef3597dbe`

Scope: report-only QA for an API-mode operator package release candidate built with `npm run build:api` and assembled with `packaging/assemble_operator_package.ps1 -FrontendMode api -CreateZip`.

This report does not change feature code, launcher code, backend code, frontend source, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Summary

Final verdict: `blocked`.

The API-mode build and package metadata path worked: `frontendMode=api` was recorded in `frontend/dist/frontend-build-info.json`, the assembled package folder, and zip-internal package metadata. Zip/checksum creation and checksum verification passed. Launcher `-CheckOnly`, shortcut installer `-CheckOnly`, package import smoke, HTTP route smoke, no-token mutation guard, and operator API docs hardening smoke passed.

Release-candidate acceptance is blocked by two findings:

1. The zip-entry denylist scan found dependency-provided `.agents` entries under the packaged runtime. The package assembly script reported denylist `0`, but the broader zip-entry scan found `6` denylist-class entries.
2. Local Supabase readiness was unavailable: Docker was unavailable, local Supabase API/Studio/DB ports were unreachable, and the runtime API reported `docker_unavailable`. Upload Preview was not executed.

Additional caveats:

- The default-port launcher smoke reused an already healthy backend on port `8000`, so a clean package-owned default-port launch was not proven in this run.
- The package `GET /api/config` response returned `200`, but marker-class scanning detected a Windows absolute path class in the response. DB URL, token, Authorization, JWT, operational filename-family, and mock marker classes were not detected.
- The built frontend bundle still contains static mock-related i18n text, but browser-visible Dashboard, Upload, Logs, and Settings pages did not show `mock://`, `mock_`, `mock mode`, or token-like markers.

No Upload Start action was clicked. No DB reset/delete/cleanup/prune command was run. No Docker volume/container delete command was run.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `f8f0310e466c6ba5e826416c1187560ef3597dbe` |
| QA branch | `codex/operator-api-mode-release-candidate-smoke` |
| Package label | `ewc-api-mode-rc-smoke-20260608-rc1` |
| Package output | Repo-external temp output root |
| Extract output | Separate repo-external temp output root |
| Package version | `0.1.0.0` |
| Runtime mode | `operator-ready` |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, or documented by path/content |

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
| Runtime metadata preserved | `275` |
| Package folder metadata | `frontendMode=api` |
| Package dist metadata | `frontendMode=api` |
| Zip creation | Passed |
| Checksum file creation | Passed |
| SHA-256 verification | Passed |

The package folder metadata recorded the actual zip SHA-256. The zip-internal metadata uses the adjacent-checksum marker as designed.

## Zip Entry Scan

| Check | Count | Result |
| --- | ---: | --- |
| Entry count | 2429 | Informational |
| Cache/bytecode entries | 0 | Pass |
| Runtime test segment entries | 0 | Pass |
| Marker-heavy docs | 0 | Pass |
| Denylist-class entries | 6 | Blocker |
| Zip-internal frontend mode | `api` | Pass |

The denylist-class entries are dependency-provided `.agents` paths inside the packaged runtime. They were not created by source-control `.agents` content and no secret marker was detected in them, but they still match the package denylist class in a zip-entry scan.

## Redaction Scan

Count-only redaction scan on package text files outside `.venv`:

| Marker class | Count | Result |
| --- | ---: | --- |
| Credential-like marker | 0 | Pass |
| DB URL marker | 0 | Pass |
| Authorization bearer marker | 0 | Pass |
| JWT-like marker | 0 | Pass |
| Service role assignment marker | 0 | Pass |
| Anon key assignment marker | 0 | Pass |
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
| Pre-smoke cache/bytecode count | 0 |
| Pre-smoke runtime test segment count | 0 |
| Packaged import smoke | `import_ok` |
| Launcher `-CheckOnly` | Passed |
| Shortcut installer `-CheckOnly` | Passed |

## Launcher And HTTP Smoke

| Check | Result |
| --- | --- |
| Default-port launcher smoke | Caveat: reused an already healthy backend on port `8000` |
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
| Browser-visible `mock://` / `mock_` / `mock mode` marker | 0 observed |
| Browser-visible token-like marker | 0 observed |
| Static bundle mock-related i18n text | Present |

The browser-visible pages did not show mock markers. The static API-mode bundle still contains mock-related i18n text, so release evidence should rely on rendered page checks and API-mode metadata rather than a broad string absence assertion over the full JavaScript bundle.

## Local Supabase Readiness

| Check | Result |
| --- | --- |
| Runtime API overall status | `blocked` |
| Runtime reason code | `docker_unavailable` |
| Docker status | Unavailable |
| Local Supabase API port | Unreachable |
| Local Supabase Studio port | Unreachable |
| Local Supabase DB port | Unreachable |
| Edge runtime | Unreachable |
| Container readiness | Blocked |

Because local Supabase readiness failed, Upload Preview was not executed. This follows the stop condition in the API-mode package plan.

## Upload Preview And Audit

| Check | Result |
| --- | --- |
| Upload Preview executed | No |
| Reason | Runtime readiness blocked |
| Upload Start clicked | No |
| `/api/audit?action=upload.preview&limit=1` | `200` |
| New upload.preview audit row | Not expected, Preview was not run |

## Findings

### Blockers

1. `zip_denylist_match`: broader zip-entry scan found dependency-provided `.agents` entries under packaged runtime.
2. `runtime_unavailable`: local Supabase readiness is blocked by unavailable Docker/local Supabase endpoints.

### Caveats

1. `default_port_reused_existing_backend`: default-port launcher did not prove a clean package-owned default-port start because port `8000` already had a healthy backend.
2. `api_config_windows_path_marker`: `GET /api/config` returned a Windows absolute path marker class. No DB URL, token, Authorization, JWT, operational filename-family, or mock marker classes were detected in that response.
3. `static_bundle_mock_i18n`: rendered pages showed no mock marker, but the static JavaScript bundle still includes mock-related i18n text.

## Reproduction Conditions

1. Build frontend with `npm run build:api`.
2. Assemble package with `-FrontendMode api -CreateZip`.
3. Verify frontend and package metadata record `frontendMode=api`.
4. Verify zip checksum.
5. Run zip-entry denylist and redaction scans.
6. Extract package into a separate repo-external temp folder.
7. Run package import smoke.
8. Run launcher and shortcut `-CheckOnly`.
9. Start package runtime on a free loopback test port.
10. Smoke UI routes, read-only APIs, no-token mutation guard, and docs hardening routes.
11. Check local Supabase readiness.
12. Do not run Upload Preview unless readiness passes.
13. Do not click Upload Start.

## Verdict

`blocked`

Reason: API-mode metadata and package launcher/API smoke largely pass, but the release candidate does not satisfy the zip-entry denylist scan and cannot proceed to API-mode Upload Preview because local Supabase readiness is unavailable.

## Next Step

Recommended next branch: `codex/operator-package-runtime-agents-prune`

That branch should decide whether dependency-provided `.agents` runtime files should be pruned, allowlisted as harmless runtime metadata, or excluded by a refined denylist policy. After that, rerun API-mode release-candidate smoke with local Supabase/Docker readiness available before attempting Upload Preview.
