# Upload Job Browser Screenshot QA

Status: report-only QA for branch `codex/upload-job-browser-screenshot-qa`

Date: 2026-06-04

Scope: Upload Job, Audit Logs, and `acceptedRows` operator-facing UI clarity after PR #19.

## Summary

Upload Job / Audit Logs browser screenshot QA was attempted without feature code changes.

The local backend and Vite dev server were reachable, backend and frontend validation passed, and HTTP smoke covered Upload, Logs, Settings, Dashboard root, Vite proxy, and `/api/audit?action=upload.start`.

Screenshot capture was not completed. The available `node_repl` browser path still failed with the existing kernel asset path error, and local Playwright was not installed. Playwright installation was not attempted because this QA-only task did not include dependency installation approval. This report records the screenshot tooling blocker instead of forcing an unsupported workaround.

## Environment

| Item | Result |
| --- | --- |
| Branch | `codex/upload-job-browser-screenshot-qa` |
| Base commit | `5a69281b15675f02a48f99844b27e0498dcfaae7` |
| Backend health | `200` |
| Vite root | `200` |
| Backend port | `8000` listening |
| Vite port | `5173` listening |
| Operational CSV fixture | Untracked, not committed |
| Feature code changes | None |

No secret values, DB URLs, auth keys, tokens, Authorization headers, raw operational CSV paths, CSV filenames, or CSV contents are included in this report.

## Browser Tooling Diagnosis

| Tooling path | Result |
| --- | --- |
| `node_repl` | Failed before JavaScript execution with `failed to write kernel assets` path error |
| Local Playwright import | Unavailable; package was not installed in the frontend workspace |
| Browser screenshot capture | Blocked by unavailable screenshot path |
| Dependency install | Not attempted |

Screenshot artifacts were therefore not produced for:

- `1440x900`
- `1366x768`
- `1024x768`
- `720x900`

## HTTP Smoke

| Smoke | Result |
| --- | --- |
| Backend `/api/health` | `200`, no sampled secret marker hits |
| Vite `/` | `200`, no sampled secret marker hits |
| Vite `/upload` | `200`, no sampled secret marker hits |
| Vite `/logs` | `200`, no sampled secret marker hits |
| Vite `/settings` | `200`, no sampled secret marker hits |
| Vite proxy `/api/health` | `200`, no sampled secret marker hits |
| Backend `/api/audit?action=upload.start&limit=5` | `200`, no sampled secret marker hits |
| Vite proxy `/api/audit?action=upload.start&limit=5` | `200`, no sampled secret marker hits |

Sampled marker checks looked for credential-bearing URL markers, Authorization/Bearer markers, service role markers, anon-key wording, and raw operational fixture markers. Response bodies were not copied into this report.

## UI Wording Checks

Source and built frontend output were checked for Upload Job count terminology.

| Check | Result |
| --- | --- |
| `acceptedRows` canonical frontend/API field | Present |
| English Upload Job metric/table label | `Accepted` |
| Korean Upload Job metric/table label | `수락` |
| Korean Upload Preview `already_in_db` label | `DB에 있음` |
| `Inserted` in frontend source/build output | Not found |
| Korean inserted-row wording markers | Not found |
| Deprecated `insertedRows` API compatibility field | Still present, not operator-facing |

Interpretation: the source/build evidence supports PR #19 semantics. The UI no longer labels Edge/Supabase upsert-accepted rows as physical net-new inserted rows. Direct visual layout fit still needs browser screenshot evidence after the screenshot tooling blocker is cleared.

## Viewport QA

| Viewport | Screenshot result | Evidence |
| --- | --- | --- |
| `1440x900` | Not captured | Screenshot tooling blocked |
| `1366x768` | Not captured | Screenshot tooling blocked |
| `1024x768` | Not captured | Screenshot tooling blocked |
| `720x900` | Not captured | Screenshot tooling blocked |

The following visual checks remain unproven by screenshot evidence:

- Korean/English wrapping in real browser layout
- Table overflow behavior in Upload Job and Audit Logs
- Status badge clarity under each viewport
- Visible layout overlap
- Browser console errors
- Browser-level failed requests

## Validation

| Check | Result |
| --- | --- |
| Targeted Upload Job/Audit backend tests | Passed, 35 tests |
| Full backend tests | Passed, 133 tests |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `git diff --check` before report | Passed |
| Backend/Vite HTTP smoke | Passed |
| Frontend source/build wording check | Passed |

Backend tests were run with local `.env` temporarily moved to a local temp backup and restored immediately after each test run, so local secret-bearing settings did not affect missing-config tests or appear in output.

Warnings observed:

- Existing FastAPI/Starlette `TestClient` deprecation warning.
- Existing HTTP 422 deprecation warning.
- Existing pytest cache write warning under repository `.pytest_cache`.

## Findings

### Blocked: screenshot evidence unavailable

Browser screenshot QA could not be completed because the available `node_repl` path failed with the existing kernel asset path error and local Playwright was not installed.

This is a QA evidence blocker, not a feature-code blocker. No feature code was changed in this report-only branch.

### Passed: acceptedRows wording source/build checks

The source and built frontend output use `Accepted` / `수락` for the operator-facing Upload Job accepted/upserted row count. No operator-facing `Inserted` wording was found in frontend source or build output.

### Passed: HTTP smoke and audit reachability

Upload, Logs, Settings, backend health, Vite proxy health, and `/api/audit?action=upload.start` responded successfully. Sampled responses did not include raw secret/path marker hits.

## Follow-Up

Recommended next branch:

```text
codex/upload-job-browser-tooling-setup
```

Goal: fix the local screenshot tooling path or add an approved Playwright dependency/setup path, then rerun screenshot QA on:

- Upload page
- Upload Preview tab
- Upload Job tab
- Upload Job progress/events table
- Logs page
- Audit Logs tab
- Dashboard and Settings smoke

## Merge Readiness

This PR is mergeable as a report-only QA artifact if the team accepts that screenshot evidence is explicitly blocked and not completed.

It does not prove visual layout quality at the requested viewport sizes. It does prove that validation, HTTP smoke, and source/build wording checks passed without feature code changes.
