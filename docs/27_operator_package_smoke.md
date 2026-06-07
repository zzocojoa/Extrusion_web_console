# Prepared Operator Package Smoke QA

Date: 2026-06-07

Branch: `codex/operator-package-smoke`

Scope: report-only QA for the prepared operator folder flow after Windows shortcut packaging v1.

## Summary

Prepared operator package smoke passed for the v1 package shape.

The smoke used a temporary package under `C:\tmp` with sanitized label `temp_operator_package_smoke_20260607_040953`. The report does not include token values, DB URLs, operational CSV paths, CSV contents, or raw row contents.

No feature code was changed. No DB reset/delete/cleanup/prune command was run. No Docker volume/container cleanup command was run. The untracked operational CSV fixture was not read, copied, committed, or deleted.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `aa220ee` |
| QA branch | `codex/operator-package-smoke` |
| Package label | `temp_operator_package_smoke_20260607_040953` |
| Package root | Temporary folder under `C:\tmp` |
| Frontend build | Present |
| Python runtime | Present via copied local `.venv` |
| Local Supabase runtime | Not required for this smoke |
| Operational CSV fixture | Not copied |

## Package Contents

| Package item | Result |
| --- | --- |
| `backend/` | Present |
| `frontend/dist/index.html` | Present |
| `launcher/start_web_console.ps1` | Present |
| `launcher/install_shortcuts.ps1` | Present |
| `.venv/Scripts/python.exe` | Present |
| `README.md` | Present |
| `docs/26_windows_shortcut_packaging_plan.md` | Present |
| `tests/backend/fixtures` | Absent |

The package includes enough runtime material for launcher smoke. It does not include the untracked operational CSV fixture.

## Shortcut Smoke

| Check | Result |
| --- | --- |
| `install_shortcuts.ps1 -CheckOnly` | Passed |
| Temp Desktop shortcut install | Passed |
| Temp Start menu shortcut install | Passed |
| Repeated install count | Passed |
| Desktop shortcut count after two installs | `1` |
| Start menu shortcut count after two installs | `1` |
| Shortcut target | Package-local `launcher/start_web_console.bat` |
| Shortcut working directory | Prepared package root |
| Unsafe `ShortcutName` | Failed before writing shortcuts |
| Unsafe-name `.lnk` count | `0` |

The smoke used temp Desktop and temp Start menu directories only. It did not touch the real user Desktop or real user Start menu.

## Launcher Smoke

| Check | Result |
| --- | --- |
| `start_web_console.ps1 -CheckOnly` | Passed |
| Token policy check | Required in operator mode, value hidden |
| API docs policy check | Disabled in operator mode |
| Backend process start | Passed |
| Browser open | Skipped with `-NoBrowser` |
| Post-smoke backend shutdown | Confirmed |
| Post-smoke `/api/health` | `000` after cleanup |

The launcher wrote logs under the documented AppData launcher log location. No AppData config, state database, or logs were deleted.

## HTTP Smoke

| Request | Result |
| --- | --- |
| `GET /` | `200` |
| `GET /upload` | `200` |
| `GET /logs` | `200` |
| `GET /settings` | `200` |
| `GET /api/health` | `200` |
| `GET /api/config` | `200` |
| `GET /api/audit?limit=1` | `200` |
| `PUT /api/config` without local token | `403` |
| `GET /api/docs` | `404` |
| `GET /api/openapi.json` | `404` |
| `GET /api/redoc` | `404` |

The served app shell included the runtime bootstrap marker. The token value was not recorded in this report.

## Redaction Checks

Count-only scans across package smoke logs and AppData launcher logs found no matches for:

- runtime local token marker
- `X-EWC-Local-Token`
- Authorization header marker
- auth-header credential marker
- DB URL marker
- service role assignment marker
- anon key assignment marker
- JWT-like marker

## Verification Commands

| Command | Result |
| --- | --- |
| Targeted launcher tests | `17 passed` |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `npm run qa:screenshots` | Passed |
| Package contents smoke | Passed |
| Shortcut idempotency smoke | Passed |
| Unsafe shortcut name smoke | Passed |
| Launcher `-CheckOnly` smoke | Passed |
| Package HTTP/token/docs smoke | Passed |
| `git diff --check` | Passed |

## Findings

No package smoke blockers were found.

Observed behavior matches the v1 prepared operator folder plan:

- Node/npm are needed to build `frontend/dist` before package assembly, not during operator launcher startup.
- `.venv` must be prepared for the target PC before handoff.
- Shortcuts can be refreshed without duplicate `.lnk` files.
- API docs remain disabled in operator mode.
- Mutating API calls without the local token are blocked.
- Read-only APIs remain token-free.

## Remaining Risks

- The `.venv` remains target-PC and Python-version sensitive. This is a maintainer handoff responsibility, not an operator task.
- This smoke used a temp package assembled locally, not a signed zip, installer, MSI, service, or machine-wide install.
- Local Supabase runtime readiness was not part of this package smoke because the target flows were launcher, shortcut, token, docs, and static frontend serving.

## Merge Blocker Assessment

No merge blocker from this QA report.

## Follow-Up

Recommended next branch: `codex/operator-package-manifest`.

That branch should define an explicit package manifest or packaging script that assembles the same allowed contents and excludes `.git`, `.gstack`, `frontend/node_modules`, raw `.env`, logs, state DB files, operational CSV fixtures, and generated screenshots.
