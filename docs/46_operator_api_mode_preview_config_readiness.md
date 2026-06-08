# API-Mode Preview Config Readiness QA

Date: 2026-06-08

Branch: `codex/operator-api-mode-preview-config-readiness`

Base commit: `72131eca4144dc98507aca32f835d922953590bb`

Scope: report-only QA for preparing and verifying operator config readiness before an API-mode Upload Preview rerun.

This report does not change feature code, launcher code, backend code, frontend code, package assembly scripts, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, or operational CSV data.

Upload Preview was not executed. Upload Start was not clicked.

## Summary

Final verdict: `blocked`.

Operator config readiness was prepared through the config API. Required Preview source and DB reconciliation fields are now configured in the operator config store and verified by presence-only checks. The source folder existence check passed using a sanitized `source-folder` label only.

The run remains blocked because Docker/local Supabase core readiness is not available. The next Preview-only rerun must not proceed until Docker and local Supabase API, Studio, and DB TCP checks are reachable.

## Source Documents

| Document | Use |
| --- | --- |
| `docs/44_operator_api_mode_preview_source_readiness.md` | Readiness checklist and stop conditions |
| `docs/45_operator_api_mode_preview_source_ready_rerun.md` | Prior blocked rerun evidence |
| `docs/32_operator_package_handoff_runbook.md` | Operator config and non-destructive handoff rules |
| `README.md` | Config precedence, Settings save, local token, and runtime policy |

## Configuration Preparation

| Item | Result |
| --- | --- |
| Config write path | `config_api` |
| Config write status | `success` |
| Saved key count | 2 |
| Settings save audit row | Found |
| Settings save audit result | `success` |
| Raw config values printed | No |
| Raw config values documented | No |

The config API was run from a temporary local API-mode runtime so repo `.env` key presence would not block operator config writes as env overrides. The temporary runtime was stopped after the readiness checks.

## Operator Config Presence

Presence-only results after preparation:

| Field | Presence | Source | Env/repo override | Secret display |
| --- | --- | --- | --- | --- |
| `plcDataDir` | `configured` | `config` | `absent` | `not_secret` |
| selected `temperatureDataDir` | `not_required` | `default` | `absent` | `not_secret` |
| `supabaseDbUrl` | `configured` | `config` | `absent` | `hidden` |

`temperatureDataDir` is marked `not_required` because the next Preview-only rerun should use the default PLC source selection unless the rerun scope explicitly includes Temperature.

## Source Path Readiness

| Check | Result |
| --- | --- |
| Source label | `source-folder` |
| Source configured | Yes |
| Source exists | Yes |
| Raw path printed | No |
| Raw path documented | No |
| Operational CSV filename/content documented | No |

No operational CSV file was copied, modified, deleted, or committed.

## Runtime Readiness

| Check | Result |
| --- | --- |
| Docker available | No |
| Local Supabase API reachable | No |
| Studio reachable | No |
| DB TCP reachable | No |
| Edge reachable | No |
| Grafana reachable | No |
| Runtime overall status | `blocked` |
| Runtime reason code | `docker_unavailable` |

Grafana is not a Preview blocker, but Docker, local Supabase API, Studio, and DB TCP are blockers for the next Preview-only rerun.

## Stop Conditions

| Stop condition | Result |
| --- | --- |
| Source config missing | No |
| DB config missing | No |
| Source folder missing | No |
| Docker/local Supabase missing | Yes |
| Preview executed | No |
| Upload Start clicked | No |

The config readiness portion passed, but the runtime readiness portion failed. The next Preview-only rerun remains blocked until Docker/local Supabase core readiness is restored.

## Audit And Redaction

Runtime response marker scan:

| Response | DB URL | Token-like | Authorization | JWT | Timestamp CSV | Operational filename-family | Windows path class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `/api/config` | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `/api/audit?action=settings.save&limit=10` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The `/api/config` path-class count is expected because non-secret path fields can be represented in config responses. This report records only the marker count and does not copy raw values.

This report intentionally excludes raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, and full local package paths.

## Safety

| Operation | Result |
| --- | --- |
| Upload Preview | Not run |
| Upload Start | Not clicked |
| DB reset/delete/cleanup/prune | Not run |
| Docker volume/container delete | Not run |
| GitHub Release/tag create or update | Not run |
| Production deploy | Not run |
| Feature code change | None |
| Launcher/backend/frontend/packaging script change | None |

## Findings

### Passed

1. `config_api_preparation`: operator config was prepared through the config API.
2. `settings_save_audit`: `settings.save` audit row was found with success result.
3. `source_config_presence`: `plcDataDir` is configured.
4. `source_exists`: source-folder existence check passed without raw path disclosure.
5. `db_config_presence`: `supabaseDbUrl` is configured and hidden.
6. `redaction`: reportable config/audit evidence did not expose DB URL, token, Authorization, JWT, timestamp-style CSV, or operational filename-family marker classes.

### Blockers

1. `runtime_unavailable`: Docker/local Supabase core readiness is blocked.

### Caveats

1. `api_config_local_path_marker`: `/api/config` contains path-class output. Raw values are not recorded here.
2. `temperature_not_required`: Temperature source readiness was not required for the default PLC-only Preview rerun path.

## Verdict

`blocked`

Reason: operator config source/DB readiness is prepared, but Docker/local Supabase core readiness is still missing. Preview-only rerun must wait until the runtime gate passes.

## Next Step

Restore Docker/local Supabase core readiness first:

1. Docker available: `yes`
2. Local Supabase API reachable: `yes`
3. Studio reachable: `yes`
4. DB TCP reachable: `yes`

After those are ready, proceed with a Preview-only rerun branch. Do not click Upload Start during that rerun.
