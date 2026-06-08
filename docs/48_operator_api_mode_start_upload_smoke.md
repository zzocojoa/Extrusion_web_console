# API-Mode Start Upload Smoke QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-start-upload-smoke`

Base commit: `3f0a16a7ea545752623427a68dfd8db955adde0b`

Scope: report-only QA for the API-mode operator package Start Upload smoke after the Preview config-ready rerun.

This report does not change feature code, launcher code, backend code, frontend code, packaging scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, or operational CSV data.

Upload Preview was not rerun. Upload Start was not clicked.

## Summary

Final verdict: `blocked`.

API-mode build and operator package assembly passed. The package launcher started successfully, served the built frontend, preserved API route precedence, and kept operator API docs disabled. Read-only HTTP smoke passed, and mutating API requests without a valid local token were blocked with `403`.

Start Upload smoke was blocked before Preview/Start execution because required upload readiness was not present in the package runtime:

- `supabaseDbUrl`: `missing`
- `supabaseUrl`: `missing`
- `supabaseAnonKey`: `missing`
- `supabaseEdgeUrl`: `missing`
- Edge runtime: `unreachable`

`plcDataDir` was configured, but this report records only presence and does not include the raw local path.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `3f0a16a7ea545752623427a68dfd8db955adde0b` |
| QA branch | `codex/operator-api-mode-start-upload-smoke` |
| Package label | `ewc-api-mode-start-upload-smoke` timestamped label |
| Package output | Repo-external temp output root |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, edited, uploaded, or documented by path/content |

## Package Preparation

| Check | Result |
| --- | --- |
| `npm run build:api` | Passed |
| Assembly command | `-FrontendMode api -CreateZip` |
| Assembly required paths | Present |
| Assembly operator readiness | Ready |
| Assembly denylist validation | `0` matches |
| Assembly redaction validation | `0` matches |
| Package metadata | `frontendMode=api` |
| Dist metadata | `frontendMode=api` |
| Zip creation | Passed |
| Checksum creation | Passed |
| Launcher `-CheckOnly` | Passed |
| Package launcher execution | Passed |

Generated package output, zip, checksum, and `frontend/dist` were not committed.

## Readiness Gates

### Operator Config

| Field | Presence | Secret display |
| --- | --- | --- |
| `plcDataDir` | `configured` | `not_secret` |
| `supabaseDbUrl` | `missing` | `hidden_when_configured` |
| `supabaseUrl` | `missing` | `not_secret` |
| `supabaseAnonKey` | `missing` | `hidden_when_configured` |
| `supabaseEdgeUrl` | `missing` | `hidden_when_configured` |

No raw config values, source paths, DB URLs, tokens, anon keys, Authorization headers, JWTs, operational CSV identifiers, CSV contents, or row contents are recorded here.

### Runtime

| Check | Result |
| --- | --- |
| Overall status | `attention` |
| Reason code | `non_core_runtime_attention` |
| Docker | `ready` |
| WSL | `ready` |
| Supabase CLI | `ready` |
| Local Supabase API | `ready` |
| Local Supabase DB TCP | `ready` |
| Local Supabase Studio | `ready` |
| Edge runtime | `unreachable` |
| Grafana | `unreachable` |

Docker/local Supabase core readiness passed, but Start Upload requires upload auth and Edge readiness. The Edge runtime and upload config gates did not pass.

## HTTP And Token Smoke

| Route | Result |
| --- | --- |
| `/` | `200` |
| `/upload` | `200` |
| `/logs` | `200` |
| `/settings` | `200` |
| `/api/health` | `200` |
| `/api/config` | `200` |
| `/api/audit?limit=1` | `200` |
| `/api/docs` | `404` |
| `/api/openapi.json` | `404` |
| `/api/redoc` | `404` |

| Token check | Result |
| --- | --- |
| Frontend bootstrap local token | `present` |
| Token in URL query | `absent` |
| `PUT /api/config` without token | `403` |
| `PUT /api/config` with invalid token | `403` |

No valid-token mutating request was executed because the Start Upload prerequisites failed.

## Upload Preview And Start Upload

| Step | Result |
| --- | --- |
| Preview rerun | Not run |
| Start Upload | Not clicked |
| Reason | `preconfigured_env_missing` plus `edge_runtime_unreachable` |
| Large operational CSV upload | Not run |
| Minimal sample preparation | Not run |
| Duplicate rerun | Not run |
| DB row count delta | Not measured |
| Upload Job status/progress | Not created |
| Job events/SSE replay | Not available because no job was created |
| `upload.start` audit row | Not expected because Start Upload was not clicked |

The QA did not proceed to Preview or Start because the required source/DB/auth/Edge readiness could not prove a safe no-new-row or duplicate-safe upload condition.

## Redaction And Artifact Policy

| Check | Result |
| --- | --- |
| Raw DB URL in report | Absent |
| Raw token/auth/JWT in report | Absent |
| Raw Authorization header in report | Absent |
| Raw operational CSV path/content/filename in report | Absent |
| Full local package path in report | Absent |
| Package output/zip/checksum committed | No |
| `.gstack` artifacts committed | No |
| `frontend/dist` committed | No |
| Operational CSV fixture committed | No |

This report intentionally uses sanitized labels and presence-only status. Runtime responses may contain local path-class fields, but raw values are not copied into this report.

## Findings

### Passed

1. `api_mode_package_ready`: API-mode frontend build and package assembly passed with metadata set to `api`.
2. `launcher_ready`: launcher `-CheckOnly` and package runtime startup passed.
3. `static_and_api_routes`: UI routes and read-only API routes returned expected HTTP statuses.
4. `docs_hardening`: operator API docs routes returned `404`.
5. `local_token_guard`: missing and invalid token mutating requests returned `403`.
6. `local_supabase_core_ready`: Docker, WSL, Supabase CLI, API, DB TCP, and Studio were ready.

### Blockers

1. `preconfigured_env_missing`: required upload settings were missing for DB URL, Supabase URL, anon/auth key, and Edge URL.
2. `edge_runtime_unreachable`: Edge runtime was unreachable.
3. `start_upload_not_safe`: without DB/auth/Edge readiness, the QA could not prove a safe no-new-row or duplicate-safe condition before Start Upload.

### Caveats

1. Grafana remained unreachable. This does not block Upload Start directly, but it keeps runtime overall status at attention.
2. No browser screenshot capture was run in this pass. HTTP route smoke was used for package UI reachability.

## Verdict

`blocked`

Reason: API-mode package and launcher behavior passed, but Start Upload smoke must not proceed until upload config and Edge runtime readiness pass. Upload Preview was not rerun and Upload Start was not clicked.

## Next Step

Prepare the actual operator config with source and DB/Edge/auth readiness using presence-only checks first. After `supabaseDbUrl`, `supabaseUrl`, `supabaseAnonKey`, `supabaseEdgeUrl`, and Edge runtime are ready without exposing raw values, rerun this Start Upload smoke with a minimal duplicate-safe sample and one approved Upload Start only.
