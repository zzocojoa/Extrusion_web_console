# Final Operator Package Release Smoke QA

Date: 2026-06-07

Branch: `codex/operator-package-release-smoke-final`

Base commit: `5464f7f`

Scope: report-only final release smoke for the prepared operator package after runtime prune, package redaction hardening, and marker-specific packaging tests landed on `main`.

## Summary

The final release-candidate package smoke passed.

The package was assembled as a fresh `C:\tmp` output with `-CreateZip`, the SHA-256 checksum matched, zip-entry scans were clean, the extracted package imported the backend app, launcher and shortcut `-CheckOnly` passed, HTTP routes served from the extracted package, mutating no-token access returned `403`, and operator API docs routes returned `404`.

No feature code was changed. No DB reset/delete/cleanup/prune command was run. No Docker volume/container cleanup command was run. AppData config/state/logs were not deleted. Existing package outputs were not deleted. The untracked operational CSV fixture was not copied, committed, deleted, or documented by path/content.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `5464f7f` |
| QA branch | `codex/operator-package-release-smoke-final` |
| Package label | `ewc-final-release-smoke-20260607-rc1` |
| Package root | repo-external folder under `C:\tmp` |
| Extract root | separate repo-external folder under `C:\tmp` |
| Frontend build | Present |
| Python runtime | Present via prepared local `.venv` |
| Runtime mode | `operator-ready` |
| Local Supabase runtime | Not required for this smoke |
| Operational CSV fixture | Not copied or committed |

## Release Candidate Output

| Item | Result |
| --- | --- |
| Package output | `C:\tmp\ExtrusionWebConsole-packages\ewc-final-release-smoke-20260607-rc1\ExtrusionWebConsole` |
| Zip output | `C:\tmp\ExtrusionWebConsole-packages\ewc-final-release-smoke-20260607-rc1.zip` |
| Checksum output | `C:\tmp\ExtrusionWebConsole-packages\ewc-final-release-smoke-20260607-rc1.zip.sha256` |
| SHA-256 verification | Passed |
| Package size class | medium, about 42 MB folder contents |
| Zip size class | small, about 13 MB |

The package folder metadata recorded the actual zip SHA-256. The zip-internal metadata uses the planned adjacent-checksum behavior.

## Automated Validation

| Check | Result |
| --- | --- |
| Targeted packaging tests | `19 passed` |
| Full backend tests from clean cwd | `184 passed` |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `npm run qa:screenshots` | Passed |
| `git diff --check` | Passed |

Screenshot QA output was written under `.gstack/screenshots/upload-job-browser-qa/` and remains ignored.

## Assembly Result

| Check | Result |
| --- | --- |
| Required paths | Present |
| Operator readiness | Ready |
| Assembly denylist validation | `0` matches |
| Assembly redaction validation | `0` matches |
| Source cache pruned | `42` |
| Runtime cache pruned | `1644` |
| Runtime test segments pruned | `8` |
| Runtime metadata preserved | `275` |
| Zip creation | Passed |
| Zip checksum file | Created |

## Zip Entry Scan

| Class | Count | Assessment |
| --- | ---: | --- |
| Dependency test segments | 0 | Pass |
| `__pycache__`, `.pytest_cache`, `*.pyc`, `*.pyo` | 0 | Pass |
| Marker-heavy docs | 0 | Pass |
| Denylist matches | 0 | Pass |
| Runtime `.py` files | 1450 | Present |
| Native/runtime files | 11 | Present |
| Runtime metadata records | 108 | Present |
| License/notice/copying files | 35 | Present |

## Package Docs Subset

The zip contains the expected package docs subset only:

| Package doc | Result |
| --- | --- |
| `README.md` | Present |
| `CHANGELOG.md` | Present |
| `VERSION` | Present |
| `docs/operator_package_runtime_note.md` | Present |

Marker-heavy engineering docs were not present in the package zip.

## Redaction Scan

Count-only redaction scan on package text files outside `.venv`:

| Marker class | Count | Assessment |
| --- | ---: | --- |
| Credential marker | 0 | Pass |
| Operational filename-family marker | 0 | Pass |
| Windows path marker | 0 | Pass |
| DB URL marker | 0 | Pass |
| Authorization marker | 0 | Pass |
| JWT marker | 0 | Pass |

The report and PR body must continue to avoid secret values, DB URLs, token values, authorization headers, operational CSV paths, CSV content, and raw row content.

## Extracted Package Smoke

| Check | Result |
| --- | --- |
| Separate extract directory | Passed |
| Extracted package root | Present |
| Extracted `frontend/dist/index.html` | Present |
| Extracted `.venv/Scripts/python.exe` | Present |
| Pre-smoke extracted cache/bytecode count | 0 |
| Pre-smoke extracted `.venv` test segment count | 0 |
| Packaged import smoke | `import_ok` |
| Launcher `-CheckOnly` | Passed |
| Shortcut installer `-CheckOnly` | Passed |

The initial local pre-smoke scan command had a PowerShell regex escaping issue. The authoritative pre-smoke result above was rerun with a path-segment based scanner and returned `0` for cache/bytecode and `.venv` test segments.

## HTTP, Token, And Docs Smoke

The extracted package launcher was started with `-NoBrowser` on a non-default loopback test port. The launcher-owned process was stopped after smoke.

| Request | Result |
| --- | --- |
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

Read-only no-token requests succeeded. Mutating no-token request was blocked. Operator API docs routes stayed disabled.

## Post-Runtime Cache

| Check | Result |
| --- | --- |
| Post-runtime generated cache/bytecode count | 402 |
| Post-runtime `.venv` test segment count | 0 |

The post-runtime cache was generated by import and HTTP smoke after extraction. It is distinct from the clean zip contents, which had cache/bytecode count `0`.

## Findings

No release blockers found.

No raw secret values, DB URLs, token values, authorization headers, operational CSV paths, operational CSV content, or raw row content were found or documented in the package release smoke evidence.

## Known Limitations

- The prepared `.venv` remains target-PC and Python-version sensitive.
- This smoke validates a prepared folder and zip, not a signed installer, MSI, Windows service, tray app, or production deployment.
- Local Supabase runtime readiness was not part of this smoke because the target was package viability, pruning, redaction, launcher, token, docs, and static frontend serving.
- Valid-token mutating success was not executed because the release smoke target was no-token guard behavior and no token values were recorded.

## Release Readiness

Release readiness: ready as a prepared operator package release candidate from the package hygiene, runtime prune, redaction, launcher, HTTP, token-guard, and operator API docs perspectives.

Recommended next branch: `codex/operator-package-handoff-runbook`.

That follow-up should document the maintainer/operator handoff steps around prepared package placement, shortcut install, expected first launch behavior, and support escalation without adding secrets or operational CSV paths.
