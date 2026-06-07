# API-Mode Operator Package Release-Candidate Ready Smoke QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-release-candidate-ready-smoke`

Base commit: `030ae6a9d12cc52e71403d158865fc0a24647fe1`

Scope: report-only ready smoke for an API-mode operator package release candidate after PR #52 documented that package hygiene was fixed but Docker/local Supabase readiness was unavailable.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Summary

Final verdict: `blocked`.

API-mode package build, metadata, package assembly, zip/checksum verification, zip-entry hygiene, package redaction scan, extracted package smoke, packaged import smoke, launcher check-only, shortcut check-only, route smoke, token guard smoke, API docs hardening smoke, and browser-visible mock marker checks passed.

The release-candidate remains blocked because Docker/local Supabase readiness is still unavailable. Initial host probes found Docker unavailable and local Supabase API/Studio/DB ports unreachable. The packaged runtime status API also reported `docker_unavailable`, with API, DB, Studio, and Edge unreachable. Upload Preview was not executed, and Upload Start was not clicked.

Additional caveats:

- Default port `8000` was already occupied by an existing backend process, so the default launcher path reused an existing backend. A clean package-owned default-port launch was not proven.
- Package redaction scan reported `0` matches for release marker classes. Runtime `GET /api/config` reported no DB URL, token, Authorization, JWT, timestamp CSV, or operational filename-family marker classes, but a Windows-path marker class was observed in config output. Raw values are intentionally not recorded here.

No DB reset/delete/cleanup/prune command was run. No Docker volume/container delete command was run.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `030ae6a9d12cc52e71403d158865fc0a24647fe1` |
| QA branch | `codex/operator-api-mode-release-candidate-ready-smoke` |
| Package label | `ewc-api-mode-ready-smoke-20260608-rc1` |
| Package output | Repo-external temp output root |
| Extract output | Separate repo-external temp output root |
| Package version | `0.1.0.0` |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, or documented by path/content |

## Initial Readiness

| Check | Result |
| --- | --- |
| Docker daemon | Unavailable |
| Local Supabase API port | Unreachable |
| Local Supabase Studio port | Unreachable |
| Local Supabase DB port | Unreachable |

Because readiness failed at the start of the run, Upload Preview was held until package runtime readiness could be checked. The packaged runtime readiness check later confirmed the same blocker.

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
| Default-port launcher smoke | Caveat: reused existing backend on occupied port `8000` |
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

## Runtime Readiness

| Check | Result |
| --- | --- |
| Runtime API overall status | `blocked` |
| Runtime reason code | `docker_unavailable` |
| Docker status | Unavailable |
| Local Supabase API port | Unreachable |
| Local Supabase Studio port | Unreachable |
| Local Supabase DB port | Unreachable |
| Edge runtime | Unreachable |

Because packaged runtime readiness failed, Upload Preview was not executed. This follows the ready-smoke stop condition.

## Upload Preview And Audit

| Check | Result |
| --- | --- |
| Upload Preview executed | No |
| Reason | Runtime readiness blocked |
| Preview counts | Not available |
| Upload Start clicked | No |
| `/api/audit?action=upload.preview&limit=1` | `200` |
| New upload.preview audit row | Not expected, Preview was not run |

## Runtime API Redaction Probe

| Response | DB URL | Token-like | Authorization | JWT | Timestamp CSV | Operational filename-family | Windows path class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `/api/config` | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `/api/audit?limit=1` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The config response path-class count is recorded as a caveat without raw value disclosure.

## Findings

### Resolved

1. `zip_agents_entries`: `.agents` package and zip-entry count remains `0`.
2. `api_mode_metadata`: build, package, and zip metadata consistently record `frontendMode=api`.
3. `operator_api_smoke`: route, token guard, and API docs hardening smoke passed.
4. `mock_marker_absence`: browser-visible API-mode pages did not expose mock markers.

### Blockers

1. `runtime_unavailable`: Docker/local Supabase readiness is blocked by unavailable runtime endpoints.

### Caveats

1. `default_port_occupied`: default-port package-owned launch was not proven because port `8000` was already occupied.
2. `api_config_local_path_marker`: `/api/config` includes local path-class output. No raw path is recorded here, and no DB URL/token/Authorization/JWT/operational filename marker class was detected.

## Reproduction Conditions

1. Confirm Docker/local Supabase readiness before Preview.
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
13. Check packaged runtime local Supabase readiness.
14. Do not run Upload Preview unless readiness passes.
15. Do not click Upload Start.

## Verdict

`blocked`

Reason: API-mode package hygiene and launcher/API smoke pass, but release-candidate readiness still requires Docker/local Supabase readiness and a Preview-only smoke. Runtime readiness was unavailable in this run, so Preview was not executed.

## Next Step

Prepare Docker/local Supabase so Docker, API, Studio, DB, and Edge readiness are reachable, then rerun this same branch pattern for Preview-only smoke. Do not click Upload Start during the rerun.
