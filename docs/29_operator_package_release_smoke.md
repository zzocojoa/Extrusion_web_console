# Operator Package Release-Candidate Smoke QA

Date: 2026-06-07

Branch: `codex/operator-package-release-smoke`

Scope: report-only QA for an operator package release candidate assembled with `packaging/assemble_operator_package.ps1`.

## Summary

Release-candidate package assembly, zip creation, checksum generation, zip extraction, launcher `-CheckOnly`, shortcut installer `-CheckOnly`, HTTP smoke, token smoke, API docs hardening smoke, and repeated assembly smoke were completed.

The runnable package smoke passed, but the release candidate is **not release-ready** because package content scans found two blocker-class packaging hygiene issues:

- `.venv` dependency-internal test path segments are present in the package.
- redaction marker scan found credential-marker policy strings and one operational CSV filename-family marker inside packaged text files.

No feature code was changed. No DB reset/delete/cleanup/prune command was run. No Docker volume/container cleanup command was run. AppData config/state/logs were not deleted. The untracked operational CSV fixture was not copied, committed, or deleted.

## Environment

| Item | Result |
| --- | --- |
| Source branch | `main` |
| Source commit | `4258b02` |
| QA branch | `codex/operator-package-release-smoke` |
| Package label | `ewc-release-candidate-smoke-20260607-rc1` |
| Repeated package label | `ewc-release-candidate-smoke-20260607-rc2` |
| Package root | repo-external folder under `C:\tmp` |
| Extract root | separate repo-external folder under `C:\tmp` |
| Frontend build | Present |
| Python runtime | Present via prepared local `.venv` |
| Local Supabase runtime | Not required for this smoke |
| Operational CSV fixture | Not copied or committed |

## Release Candidate Output

| Item | Result |
| --- | --- |
| Package output | `C:\tmp\ExtrusionWebConsole-packages\ewc-release-candidate-smoke-20260607-rc1\ExtrusionWebConsole` |
| Zip output | `C:\tmp\ExtrusionWebConsole-packages\ewc-release-candidate-smoke-20260607-rc1.zip` |
| Checksum output | `C:\tmp\ExtrusionWebConsole-packages\ewc-release-candidate-smoke-20260607-rc1.zip.sha256` |
| SHA-256 | `97882a94b565b744ad2e1abffd8477ae71f57bf83e837c78e9e8dd7dbbaf8079` |
| Package size class | medium, about 44 MB folder contents |
| Zip size class | small, about 13 MB |

Top-level package entries:

```text
.venv
backend
docs
frontend
launcher
CHANGELOG.md
package-build-info.json
README.md
VERSION
```

## Assembly Results

| Check | Result |
| --- | --- |
| Required paths | Present |
| Operator readiness | Ready |
| Assembly denylist validation | `0` matches |
| Assembly redaction validation | `0` matches |
| Zip creation | Passed |
| Zip checksum file | Created |
| Repeated assembly | Passed, rc1 output remained present after rc2 assembly |

Folder metadata records the actual zip SHA-256. Zip-internal metadata records `zipCreated=true` and points to the adjacent checksum file, which matches the planned metadata behavior.

## Zip Extract Smoke

| Check | Result |
| --- | --- |
| Separate extract directory | Passed |
| Extracted package root | Present |
| Extracted launcher scripts | Present |
| Extracted frontend build | Present |
| Extracted `.venv/Scripts/python.exe` | Present |

## Denylist And Redaction Scan

Count-only scan on the extracted package:

| Class | Count | Assessment |
| --- | ---: | --- |
| `.git` | 0 | Pass |
| `.gstack` | 0 | Pass |
| `frontend/node_modules` | 0 | Pass |
| `frontend/src` | 0 | Pass |
| `frontend/qa` | 0 | Pass |
| repo `tests` directory | 0 | Pass |
| runtime `.venv` dependency test segments | 8 | Blocker |
| raw `.env*` files | 0 | Pass |
| CSV files | 0 | Pass |
| logs | 0 | Pass |
| state DB files | 0 | Pass |
| generated screenshots | 0 | Pass |

Count-only redaction marker scan on extracted package text files:

| Marker class | Count | Assessment |
| --- | ---: | --- |
| DB URL marker | 0 | Pass |
| auth-header marker | 1 | Blocker |
| service-role assignment marker | 0 | Pass |
| anon-key assignment marker | 2 | Blocker |
| JWT-like marker | 0 | Pass |
| timestamp-style CSV marker | 0 | Pass |
| operational CSV filename-family marker | 1 | Blocker |

The marker hits appear to be source/documentation marker strings rather than live secret values. They are still release blockers because the release-candidate policy requires the package to avoid operational filename-family strings and secret-like marker strings in packaged text.

## Launcher And Shortcut Smoke

| Check | Result |
| --- | --- |
| Extracted package launcher `-CheckOnly` | Passed |
| Token policy output | Required in operator mode, token value hidden |
| API docs policy output | Disabled in operator mode |
| Extracted package shortcut installer `-CheckOnly` | Passed |
| Shortcut writes | None, check-only mode |

## HTTP, Token, And Docs Smoke

The extracted package launcher was started with `-NoBrowser` on a non-default loopback test port. The launcher-owned processes were stopped after smoke.

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
| Post-shutdown health probe | `000` |

Read-only no-token requests succeeded. Mutating no-token request was blocked. Operator API docs routes stayed disabled.

## Verification Commands

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests\backend\test_operator_package_assembly.py` | `10 passed` |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `npm run qa:screenshots` | Passed |
| `packaging/assemble_operator_package.ps1 -CreateZip` | Passed |
| Release zip extract smoke | Passed |
| Extracted launcher `-CheckOnly` | Passed |
| Extracted shortcut installer `-CheckOnly` | Passed |
| Extracted HTTP/token/docs smoke | Passed |
| Repeated assembly smoke | Passed |

Pytest emitted a cache write warning in `.pytest_cache`; it did not affect test pass/fail.

## Findings

### RC-BLOCKER-001: Runtime `.venv` includes dependency test segments

The package excludes the repository `tests` directory, but the prepared `.venv` contains dependency-internal test path segments. This conflicts with the release-candidate denylist expectation that test material is excluded from the package.

Repro:

1. Assemble the package with `-CreateZip`.
2. Extract the zip to a separate `C:\tmp` folder.
3. Run a count-only package tree scan for test path segments.

Impact:

- The package is larger than needed.
- The manifest denylist currently passes while a stricter release-candidate scan still finds test-like runtime content.
- This is a packaging hygiene issue, not a product runtime behavior failure.

### RC-BLOCKER-002: Redaction marker scan finds packaged marker strings

The extracted package text scan found credential-marker policy strings and one operational CSV filename-family marker. These appear to be marker/policy/source strings, not live secret values, but they still violate the package policy for release-candidate contents.

Repro:

1. Assemble the package with `-CreateZip`.
2. Extract the zip to a separate `C:\tmp` folder.
3. Run a count-only redaction marker scan across package text files.

Impact:

- No raw DB URL, token value, JWT value, raw `.env`, CSV file, or CSV content was found.
- Release-candidate packaging should still avoid shipping operational filename-family markers or secret-like marker strings when they are not required for operator runtime.

## Release Blocker Assessment

Release blocker: yes.

The packaged app starts and serves the expected routes, but the package content scan does not yet satisfy the release-candidate denylist/redaction policy.

## Known Limitations

- The `.venv` is target-PC and Python-version sensitive.
- This smoke used a repo-external local package under `C:\tmp`, not a signed installer, MSI, Windows service, or production deployment.
- Local Supabase runtime readiness was not part of this smoke because the target was package assembly, launcher, token, docs, and static frontend serving.
- Valid-token mutating success was not executed because the QA target was release-candidate package behavior and no token values were recorded.

## Follow-Up

Recommended next branch: `codex/operator-package-runtime-prune-policy`.

That branch should decide whether assembly should prune `.venv` dependency test folders and whether packaged backend/docs should replace concrete marker strings with generic scanner fixtures that still validate redaction behavior without shipping operational filename-family or secret-like marker text.
