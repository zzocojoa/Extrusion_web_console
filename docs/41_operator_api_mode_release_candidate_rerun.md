# API-Mode Operator Package Release-Candidate Rerun QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-release-candidate-rerun`

Base commit: `118499e3726f541c7ccfe43b8e19bc9644b23acb`

Scope: report-only rerun QA after the operator package `.agents` runtime prune implementation landed on `main`.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Summary

Final verdict: `blocked`.

The package hygiene blocker from the previous API-mode release-candidate smoke is resolved. The API-mode frontend build, build metadata, package metadata, zip/checksum verification, zip-entry hygiene scan, redaction scan, extracted package smoke, packaged import smoke, launcher check-only, shortcut check-only, route smoke, token guard smoke, API docs hardening smoke, and browser-visible mock marker check passed.

Release-candidate acceptance remains blocked because local Supabase readiness is unavailable. Docker was unavailable, local Supabase API/Studio/DB ports were unreachable, and the runtime status API reported `docker_unavailable`. Upload Preview was not executed.

Additional caveats:

- Default port `8000` was already occupied, so a clean package-owned default-port launcher start was not proven in this run.
- `GET /api/config` returned `200`, and DB URL/token/Authorization/JWT/operational filename marker classes were not detected. A Windows-path marker class was present in config output, consistent with local config/state path reporting, and raw values are intentionally not included in this report.

No Upload Start action was clicked. No DB reset/delete/cleanup/prune command was run. No Docker volume/container delete command was run.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `118499e3726f541c7ccfe43b8e19bc9644b23acb` |
| QA branch | `codex/operator-api-mode-release-candidate-rerun` |
| Package label | `ewc-api-mode-rc-rerun-20260608-rc1` |
| Package output | Repo-external temp output root |
| Extract output | Separate repo-external temp output root |
| Package version | `0.1.0.0` |
| Runtime mode | Operator package |
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
| Runtime agent entries pruned | `8` |
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
| `.agents` entries | 0 | Pass |
| Runtime test segment entries | 0 | Pass |
| Cache/bytecode entries | 0 | Pass |
| Marker-heavy docs | 0 | Pass |
| CSV files | 0 | Pass |
| Raw env files | 0 | Pass |
| Zip-internal frontend mode | `api` | Pass |

PR #49's `.agents` package hygiene blocker is resolved.

## Redaction Scan

Count-only redaction scan on package text files outside `.venv`:

| Marker class | Count | Result |
| --- | ---: | --- |
| Credential-like marker | 0 | Pass |
| DB URL marker | 0 | Pass |
| Authorization marker | 0 | Pass |
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
| Default-port launcher smoke | Caveat: port `8000` was already occupied |
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

Because local Supabase readiness failed, Upload Preview was not executed. This follows the stop condition for API-mode package release-candidate QA.

## Upload Preview And Audit

| Check | Result |
| --- | --- |
| Upload Preview executed | No |
| Reason | Runtime readiness blocked |
| Upload Start clicked | No |
| `/api/audit?action=upload.preview&limit=1` | `200` |
| New upload.preview audit row | Not expected, Preview was not run |

## Findings

### Resolved

1. `zip_agents_entries`: `.agents` package and zip-entry count is now `0`.
2. `api_mode_metadata`: build, package, and zip metadata consistently record `frontendMode=api`.
3. `operator_api_smoke`: route, token guard, and API docs hardening smoke passed.

### Blockers

1. `runtime_unavailable`: local Supabase readiness is blocked by unavailable Docker/local Supabase endpoints.

### Caveats

1. `default_port_occupied`: default-port package-owned launch was not proven because port `8000` was already occupied.
2. `api_config_local_path_marker`: `/api/config` includes local path-class output. No raw path is recorded here, and no DB URL/token/Authorization/JWT/operational filename marker class was detected.

## Reproduction Conditions

1. Build frontend with `npm run build:api`.
2. Assemble package with `-FrontendMode api -CreateZip`.
3. Verify frontend and package metadata record `frontendMode=api`.
4. Verify zip checksum.
5. Run zip-entry hygiene and redaction scans.
6. Extract package into a separate repo-external temp folder.
7. Run package import smoke.
8. Run launcher and shortcut `-CheckOnly`.
9. Start package runtime on a free loopback test port.
10. Smoke UI routes, read-only APIs, no-token mutation guard, and docs hardening routes.
11. Check browser-visible pages for mock-mode markers.
12. Check local Supabase readiness.
13. Do not run Upload Preview unless readiness passes.
14. Do not click Upload Start.

## Verdict

`blocked`

Reason: the previous `.agents` package hygiene blocker is resolved, but API-mode release-candidate acceptance still requires local Supabase/Docker readiness and a Preview-only smoke. That readiness was unavailable in this rerun.

## Next Step

Recommended next branch: `codex/operator-api-mode-release-candidate-ready-smoke`

Rerun this same QA after Docker and local Supabase are reachable. If readiness passes, execute Upload Preview only, verify audit visibility, and still do not click Upload Start.
