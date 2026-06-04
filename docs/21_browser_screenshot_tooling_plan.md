# Browser Screenshot Tooling Plan

Status: decision-complete plan for branch `codex/upload-job-browser-tooling-setup`

Date: 2026-06-04

Scope: make Upload Job / Audit Logs browser screenshot QA reproducible on the Windows operator/developer environment without depending on Docker, local Supabase, operational CSV files, or secret-bearing configuration.

## Summary

PR #20 proved that Upload Job / Audit Logs screenshot QA is currently blocked by tooling, not by the app HTTP surface:

- `node_repl` fails before browser automation with a kernel asset path error.
- Local Playwright is not installed in the frontend workspace.
- The requested viewport screenshots for `1440x900`, `1366x768`, `1024x768`, and `720x900` were not captured.

Decision: add a project-owned Playwright screenshot QA path in a follow-up implementation PR. Keep it local-first, mock-first, and explicitly non-destructive.

## Goals

- Capture deterministic screenshots for Upload Job, Audit Logs, Dashboard, and Settings smoke.
- Verify `acceptedRows` wording does not regress to inserted-row wording.
- Capture console errors and failed browser requests.
- Run on Windows without local Supabase, Docker, or operational CSV fixtures.
- Keep screenshots and traces out of git.
- Avoid exposing secrets, DB URLs, tokens, Authorization headers, operational CSV paths, filenames, CSV contents, or row contents.

## Non-Goals

- Do not fix application layout bugs in the tooling setup PR.
- Do not run real upload jobs.
- Do not upload operational CSV data.
- Do not require local Supabase or Docker.
- Do not use production deploy or production URLs.
- Do not replace backend contract tests, frontend typecheck, or build.

## Decisions

### 1. Chosen Tool

Use Playwright as a project devDependency under `frontend/`.

Rationale:

- It gives deterministic viewport screenshots, console capture, request failure capture, and browser context control.
- It does not rely on the currently broken `node_repl` asset path.
- It is standard enough to run locally on Windows and optionally in CI later.

Planned package changes:

```text
frontend/package.json
frontend/package-lock.json
```

Planned devDependency:

```text
@playwright/test
```

The implementation PR should run:

```powershell
cd frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

If browser binary installation requires network access, that approval belongs to the implementation PR, not this planning PR.

### 2. QA Script

Add a dedicated local QA command:

```json
{
  "scripts": {
    "qa:screenshots": "playwright test --config qa/playwright.config.ts"
  }
}
```

Recommended files:

```text
frontend/qa/playwright.config.ts
frontend/qa/upload-job-audit-screenshots.spec.ts
frontend/qa/README.md
```

The script should be independent from normal unit tests so screenshot QA can be run intentionally without slowing every build.

### 3. Screenshot Output Path

Use a repo-local, ignored artifact path:

```text
.gstack/screenshots/upload-job-browser-qa/<timestamp>/
```

Each run should create:

```text
summary.json
console.jsonl
network-failures.jsonl
1440x900-upload-job-ko.png
1440x900-audit-logs-ko.png
1440x900-upload-job-en.png
...
```

Screenshots are QA artifacts, not source artifacts. They should not be committed.

### 4. `.gitignore` Policy

Current `.gitignore` already ignores:

```text
.gstack/
```

The implementation PR may keep this unchanged if screenshots are written under `.gstack/`.

If a more explicit path is preferred, add only:

```text
.gstack/screenshots/
```

Do not ignore broad source paths such as `docs/`, `tests/`, `frontend/src/`, or operational fixture directories.

### 5. Dev Server Mode

Use Vite mock mode for screenshot QA:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Leave `VITE_API_MODE` unset.

Rationale:

- Upload Preview and Upload Job already have mock data.
- Logs page has mock Audit Logs when not in API mode.
- This avoids local Supabase, Docker, DB URLs, auth keys, and operational CSV paths.
- It makes screenshot QA reproducible on a clean developer machine after npm install.

Backend server is optional for this screenshot QA. The script may still perform a non-blocking backend `/api/health` probe for environment context, but screenshot pass/fail must not depend on backend availability.

### 6. API Mode Coverage

API mode screenshot QA should be a separate follow-up, not the default.

Use API mode only when the goal is to validate Vite proxy and persisted backend rows. It requires a running backend and may depend on local state DB contents. It must still avoid real upload execution unless explicitly requested.

### 7. Fixture And Mock Data Strategy

Default screenshot QA should use frontend mock data only.

Coverage targets:

- Upload Preview tab with target, already-in-DB, partial, risky, and excluded rows.
- Upload Job tab with running or completed mock job rows.
- Upload Job events table with several event rows.
- Logs page with Job Logs and Audit Logs tabs.
- Audit Logs rows for success, blocked, and failure states.
- Dashboard and Settings smoke pages.

The current frontend mock rows already avoid raw operational CSV paths. The implementation PR should keep that invariant and add only sanitized mock labels if more coverage is needed.

Allowed mock values:

```text
mock_preview
mock_upload_job
mock_req_upload
mock-target-1
integrated_plc_sample
```

Forbidden mock values:

- Real operational CSV filename.
- Absolute Windows user paths.
- DB URLs.
- Auth keys.
- Bearer tokens.
- Authorization headers.
- CSV contents or row contents.

### 8. `acceptedRows` Wording Automation

The Playwright spec should assert visible text and forbidden text.

Required visible assertions:

- English Upload Job metric or table uses `Accepted`.
- Korean Upload Job metric or table uses `수락`.
- Korean Upload Preview `already_in_db` row uses `DB에 있음`.

Forbidden visible assertions:

- `Inserted`
- `적재`
- `삽입`
- `새로 삽입`

The implementation should also keep the existing source/build grep check as a separate non-browser guard:

```powershell
rg -n "Inserted|적재|삽입|새로 삽입" frontend/src frontend/dist
```

Expected result: no matches.

### 9. Console And Network Capture

The Playwright runner should record:

- `page.on("console")` messages, with type, URL, and text.
- `page.on("pageerror")` exceptions.
- `page.on("requestfailed")` failures, with URL redacted before writing.
- HTTP responses with status `>= 400`, excluding Vite HMR noise if any.

Fail the screenshot QA on:

- Any uncaught page error.
- Any failed document/script/style/API request for app routes.
- Any unredacted credential-like marker in captured console/network artifact.

Do not write raw response bodies to screenshot artifacts.

### 10. Viewport Matrix

Run all required pages at:

| Viewport | Purpose |
| --- | --- |
| `1440x900` | Wide desktop operator screen |
| `1366x768` | Common laptop/operator PC first viewport |
| `1024x768` | Narrow desktop/tablet-like layout |
| `720x900` | Small layout boundary and table horizontal scroll |

Minimum page matrix:

| Page | Route | State |
| --- | --- | --- |
| Dashboard | `/` | mock running |
| Upload Preview | `/upload` | Preview tab |
| Upload Job | `/upload` | Job tab after mock start |
| Logs Job Logs | `/logs` | Job Logs tab |
| Logs Audit Logs | `/logs` | Audit Logs tab |
| Settings | `/settings` | read-only runtime settings |

### 11. Interaction Flow

Recommended browser flow:

1. Start at `/`.
2. Set language to Korean and capture Dashboard smoke.
3. Navigate to `/upload`.
4. Capture Upload Preview tab.
5. Click Start Upload in mock mode if required to populate mock job state.
6. Click Job tab and capture Upload Job table/events.
7. Navigate to `/logs`.
8. Capture Job Logs tab.
9. Click Audit Logs tab and capture Audit Logs table.
10. Switch language to English and repeat Upload Job and Audit Logs wording captures.
11. Navigate to `/settings` and capture smoke.

The flow must not call real `POST /api/upload/jobs` because mock mode is required.

### 12. CI Decision

Keep screenshot QA local-only for the first implementation.

Reasons:

- Browser binary installation increases CI setup complexity.
- The current repo appears to report no GitHub checks for these PRs.
- The immediate need is reproducible local evidence for operator UI review.

Future CI path:

- Add a separate GitHub Actions workflow only after local Playwright is stable.
- Run on manual dispatch or PR label, not every PR.
- Upload screenshot artifacts through GitHub Actions artifact storage, never commit them.

### 13. Windows Stability Rules

Use PowerShell-safe commands and explicit localhost ports.

Recommended local command:

```powershell
cd frontend
npm run qa:screenshots
```

The Playwright config should:

- Start Vite with `webServer`.
- Use `127.0.0.1`, not `localhost`, to avoid IPv6 ambiguity.
- Use fixed port `5173`.
- Reuse an existing Vite server when available.
- Write artifacts under the repo root `.gstack/screenshots/...`.
- Set a conservative timeout for slower operator PCs.
- Avoid shell-dependent cleanup.

### 14. Security And Redaction Policy

The screenshot runner must not load `.env` values into the frontend.

Artifact redaction should replace:

- DB URL-like strings.
- Authorization headers.
- Bearer tokens.
- JWT-like strings.
- Supabase anon/service-role-like labels when followed by values.
- Absolute Windows user paths.
- Operational CSV filenames.

Recommended artifact policy:

- Screenshots may show sanitized UI text only.
- Console/network JSONL must store redacted URLs.
- Do not store request or response bodies.
- Do not store raw local file paths.
- Do not write any artifact outside `.gstack/screenshots/`.

### 15. Tests And Checks

Implementation PR should validate:

```powershell
cd frontend
npm run typecheck
npm run build
npm run qa:screenshots
```

Repository-level checks:

```powershell
git diff --check
```

Optional backend regression:

```powershell
.\.venv\Scripts\python -m pytest tests\backend\test_upload_jobs_api_contract.py tests\backend\test_audit_api_contract.py
```

Full backend tests are not required for a frontend-only tooling PR unless backend files are touched.

### 16. Implementation Order

1. Add `@playwright/test` devDependency under `frontend/`.
2. Add `frontend/qa/playwright.config.ts`.
3. Add screenshot artifact helper with redaction.
4. Add Upload Job / Audit Logs screenshot spec.
5. Add `npm run qa:screenshots`.
6. Confirm `.gstack/` ignore policy is sufficient.
7. Run `npm run typecheck`.
8. Run `npm run build`.
9. Run `npm run qa:screenshots`.
10. Record screenshot artifact paths in the QA report.
11. Keep feature code unchanged unless a real visual bug is found and a separate fix PR is requested.

## Open Risks

- Playwright browser binary install may need network access on first setup.
- Font rendering may differ slightly between developer PCs.
- Mock data can prove layout and wording but not persisted backend state.
- API mode screenshot QA still needs a separate plan if persisted audit rows or SSE replay need visual proof.

## Rollback

Tooling setup can be reverted by removing:

- `@playwright/test` from frontend devDependencies.
- `frontend/qa/` files.
- `qa:screenshots` script.
- Any explicit screenshot artifact ignore line if added.

No application data, local Supabase state, upload state, or production deploy is affected.
