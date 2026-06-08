# API-Mode Preview Config-Ready Rerun QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-preview-config-ready-rerun`

Base commit: `b8943d8353e612141d6287a32ae6394b128e2acb`

Scope: report-only QA for rerunning API-mode operator package Upload Preview after PR #57 recorded that config readiness passed and runtime readiness remained.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, or operational CSV data.

Upload Preview was executed. Upload Start was not clicked.

## Summary

Final verdict: `passed with caveats`.

Docker/local Supabase core readiness passed for Preview: Docker was available, local Supabase API was reachable, Studio was reachable, and DB TCP was reachable. Operator config presence remained ready: `plcDataDir` was configured, `source-folder` existed, and `supabaseDbUrl` was configured with secret value hidden.

API-mode operator package runtime launched successfully. Upload Preview was executed only, finished as `succeeded`, and reported `dbStatus=reachable`. The candidate was classified as `already_in_db`, with zero upload rows estimated. An `upload.preview` audit row was found with success result.

Edge and Grafana were not reachable. They are caveats for this Preview-only smoke, not blockers for exact DB reconciliation.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `b8943d8353e612141d6287a32ae6394b128e2acb` |
| QA branch | `codex/operator-api-mode-preview-config-ready-rerun` |
| Package label | `ewc-api-mode-preview-config-ready-rerun` timestamped label |
| Package output | Repo-external temp output root |
| Frontend mode | `api` |
| Operational CSV fixture | Not copied, committed, deleted, edited, or documented by path/content |

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
| Checksum verification | Passed |
| Package launcher execution | Passed |

Generated package output, zip, checksum, and `frontend/dist` were not committed.

## Readiness Gates

### Runtime

| Check | Result |
| --- | --- |
| Docker available | Yes |
| Local Supabase API reachable | Yes |
| Studio reachable | Yes |
| DB TCP reachable | Yes |
| Edge reachable | No |
| Grafana reachable | No |
| Runtime overall status | `attention` |
| Runtime reason code | `non_core_runtime_attention` |

Edge and Grafana remained caveats. Docker, API, Studio, and DB TCP passed, so the Preview-only gate was allowed to proceed.

### Operator Config

| Field | Presence | Secret display |
| --- | --- | --- |
| `plcDataDir` | `configured` | `not_secret` |
| `source-folder` | `exists` | `not_secret` |
| `supabaseDbUrl` | `configured` | `hidden` |

No raw config values, source paths, DB URLs, tokens, or operational CSV identifiers are recorded here.

## Upload Preview

| Check | Result |
| --- | --- |
| Upload Preview request | Accepted |
| Range selection | `latest_source_date` |
| Terminal status | `succeeded` |
| DB status | `reachable` |
| Error code | `none` |
| Total items | 1 |
| Target count | 0 |
| Already in DB count | 1 |
| Partial overlap count | 0 |
| Risky count | 0 |
| Excluded count | 0 |
| Upload rows | 0 |
| DB matched rows | 20,219 |
| Upload Start clicked | No |

The Preview result indicates the selected source candidate's exact keys were already present in the DB. No upload was started.

## Audit And Redaction

| Check | Result |
| --- | --- |
| `/api/audit?action=upload.preview&limit=10` | Checked |
| Matching `upload.preview` audit row | Found |
| Audit result | `success` |
| Audit error code | `none` |

Runtime response marker scan:

| Response | DB URL | Token-like | Authorization | JWT | Timestamp CSV | Operational filename-family | Windows path class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Preview detail | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| Audit response | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The Preview detail response contains a path-class marker because the API includes local path fields in item details. This report records only the marker count and does not copy raw values.

This report intentionally excludes raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, and full local package paths.

## Safety

| Operation | Result |
| --- | --- |
| Upload Preview | Run |
| Upload Start | Not clicked |
| DB reset/delete/cleanup/prune | Not run |
| Docker volume/container delete | Not run |
| GitHub Release/tag create or update | Not run |
| Production deploy | Not run |
| Feature code change | None |
| Launcher/backend/frontend/packaging script change | None |

## Findings

### Passed

1. `runtime_core_ready`: Docker, local Supabase API, Studio, and DB TCP were reachable.
2. `config_ready`: `plcDataDir`, source existence, and `supabaseDbUrl` readiness passed.
3. `api_mode_package`: package and dist metadata recorded `frontendMode=api`.
4. `preview_succeeded`: Upload Preview completed with `succeeded` and `dbStatus=reachable`.
5. `already_in_db`: the candidate was classified as `already_in_db` with zero upload rows.
6. `preview_audit`: `upload.preview` audit row was found with success result.
7. `redaction`: reportable evidence did not expose DB URL, token, Authorization, JWT, timestamp-style CSV, or operational filename-family marker classes.

### Caveats

1. `edge_unreachable`: Edge route was not reachable. This does not block Preview-only reconciliation.
2. `grafana_unreachable`: Grafana was not reachable. This does not block Preview-only reconciliation.
3. `preview_detail_path_marker`: Preview detail response contains a path-class field. Raw values are not recorded here.

### Blockers

No blocker remains for API-mode Preview-only smoke.

## Verdict

`passed with caveats`

Reason: the source/DB config and Docker/local Supabase core runtime gates passed, Preview-only execution succeeded, audit evidence was found, and Upload Start was not clicked. Edge and Grafana remain non-Preview caveats.

## Next Step

Review and merge this QA report. The next implementation/QA decision is whether to proceed to a separately approved Upload Job/Start Upload smoke. Upload Start should remain blocked until that explicit approval.
