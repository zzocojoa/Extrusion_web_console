# Operator Package API-Mode Upload Preview Smoke

Date: 2026-06-07

Branch: `codex/operator-api-mode-preview-smoke`

Base commit: `5262f6da1a32c535270172a1c89adc1e24145af6`

Scope: report-only QA for validating whether the released operator package can run Upload Preview in real backend/API mode after the previous mock-mode UI smoke.

This report does not change product code, launcher behavior, backend behavior, frontend behavior, package assembly, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Target Release

| Item | Result |
| --- | --- |
| Release tag | `operator-package-v0.1.0.0` |
| Package label | `ewc-final-release-smoke-20260607-rc1` |
| Runtime label | `released_operator_package` |
| Default launcher path | Passed |
| Browser tool | In-app Browser plugin |

## Summary

Final verdict: `blocked`.

The released operator package launched from the default path and served the web console on the default local port. Dashboard, Upload, Logs, and Settings opened without blank or broken screens. Settings displayed secret fields as hidden, and Upload Preview was clickable.

However, the package UI remained in mock mode. Settings displayed `mock mode`, the built frontend artifact contained mock Preview strings, and the Preview result used `mock://` and `mock_` values. The official mode switch is a frontend build/run setting, `VITE_API_MODE=api`; it is not a Settings toggle in the released package. The current release asset was not modified or rebuilt.

Local Supabase readiness was also blocked: Docker server was unavailable from the smoke environment, the local Supabase API/Studio/DB ports were unreachable, and the runtime API returned `docker_unavailable`.

Because the API-mode prerequisites were not met, a real API-mode Upload Preview was not executed. Upload Start was not clicked.

## Mode Evidence

| Check | Result |
| --- | --- |
| Mode before | `mock` |
| Official API-mode path | `VITE_API_MODE=api` at frontend build/run time |
| Settings mode toggle available | No |
| Mode after | `mock` |
| Built frontend mock markers | Present |
| Preview mock markers | Present |
| Release/tag mutation | Not performed |

The smoke did not force a mode change by editing built assets, rebuilding the release package, changing GitHub Release assets, or modifying source code.

## Browser Smoke

| Page | Result |
| --- | --- |
| Dashboard | Opened, visible content present |
| Upload | Opened, visible content present |
| Logs | Opened, visible content present |
| Settings | Opened, visible content present |
| Browser console errors | 0 observed |

Settings checks:

| Check | Result |
| --- | --- |
| Config fields visible | Passed |
| Save button visible | Passed |
| Secret raw value hidden | Passed |
| Disabled/read-only fields visible | Passed |
| Mock mode notice visible | Passed |

## Local Supabase Readiness

| Check | Result |
| --- | --- |
| Runtime API status | `blocked` |
| Runtime reason | `docker_unavailable` |
| Docker server | Unavailable |
| Local Supabase API port | Unreachable |
| Local Supabase Studio port | Unreachable |
| Local Supabase DB port | Unreachable |
| API config required source path | Missing |
| API config DB URL presence | Missing or not confirmed through safe visible fields |
| API config Supabase API URL | Missing |
| API config Edge URL | Missing |

Secret values were not requested, printed, or documented. Hidden secret fields were treated as presence-only evidence where possible.

## Upload Preview Check

| Check | Result |
| --- | --- |
| Upload page reached | Passed |
| Preview button clicked | Passed |
| Upload Start clicked | No |
| API-mode Preview executed | No |
| Result source | Mock UI only |
| `mock://` / `mock_` absent | Failed |
| API-mode `upload.preview` audit row | Not created |

Mock-only counts observed after clicking Preview:

| Count | Value |
| --- | ---: |
| Target files | 1 |
| Already in DB files | 1 |
| Partial overlap files | 1 |
| Risky files | 0 |
| Excluded files | 0 |
| Upload row estimate | 26,750 |

These counts are not real API-mode evidence and must not be used as local Supabase reconciliation proof.

## Audit Logs

| Check | Result |
| --- | --- |
| Logs page opened | Passed |
| Audit Logs tab opened | Passed |
| Recent rows visible | Passed, mock audit rows only |
| Token redaction visible | Passed |
| API audit query for `upload.preview` | `200`, no current rows returned |
| New API-mode `upload.preview` row | Not verified because API-mode Preview was not run |

## Redaction

Browser-visible text and sampled API responses were scanned for forbidden markers.

| Marker class | Result |
| --- | --- |
| Raw token / bearer marker | Not observed |
| Authorization header | Not observed |
| JWT-shaped value | Not observed |
| DB URL | Not observed |
| Windows absolute path | Not observed |
| Operational CSV filename family | Not observed |
| Operational CSV content | Not observed |

This report intentionally excludes raw secret values, DB URLs, tokens, Authorization headers, JWTs, operational CSV paths, operational CSV filenames, CSV contents, row contents, and full local package paths.

## Blockers

1. The released package frontend is mock-mode built and cannot be switched to API mode from Settings.
2. Local Supabase runtime readiness is blocked by unavailable Docker/local Supabase endpoints.
3. Required API-mode Preview configuration is incomplete or cannot be confirmed through safe visible fields.

## Reproduction Conditions

1. Use the released operator package for `operator-package-v0.1.0.0`.
2. Start the package through the default launcher path.
3. Open the local web console in the in-app Browser.
4. Open Dashboard, Upload, Logs, and Settings.
5. Confirm Settings shows mock mode and hidden secret fields.
6. Click Upload Preview only.
7. Confirm the result is mock-only and includes mock markers.
8. Confirm local Supabase readiness is blocked without running reset, cleanup, prune, or Docker destructive operations.
9. Confirm no raw secret/path/token/operational CSV markers are visible.

## Verdict

`blocked`

Reason: the released package launches and the UI smoke passes, but the current runtime remains mock mode and local Supabase readiness is unavailable. Real backend/API/local Supabase Upload Preview was not executed, and Upload Start was not clicked.

## Next Step

Prepare an API-mode package or developer API-mode frontend run with `VITE_API_MODE=api`, ensure local Supabase readiness passes, then rerun this smoke without modifying release assets or exposing secret values.
