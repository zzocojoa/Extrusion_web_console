# Operator Mock Usage Full Audit

Date: 2026-06-14 Asia/Seoul

Branch: `codex/operator-mock-usage-full-audit`

Scope: broad repository and browser-visible audit for remaining mock, demo,
scaffold, fixture, placeholder, fake, sample, and stub usage

Verdict: `api_mode_runtime_not_mock_backed_with_caveats`

Match Rate: `100%`

## Summary

The broad mock usage audit is complete.

Current API-mode runtime screens do not appear to be backed by scaffold mock
Dashboard data. The live browser smoke showed Dashboard, Upload, Logs, and
Settings loading real API-backed state, with no visible ASCII mock markers.

Mock paths still exist in the repository, but they are primarily default
frontend development paths, screenshot/demo support, tests, fixtures, package
compatibility, and older planning documentation. They should not be treated as
current operator API-mode evidence.

## Non-Developer Explanation

There are two different meanings of "mock" in this project.

The first is dangerous for operations: the running operator screen pretends to
show real upload status but is actually using made-up data. That was the old
Dashboard problem. This audit did not find that problem in the current API-mode
runtime smoke.

The second is normal development support: fake data used only when the frontend
is run in mock/default mode, or in tests and old design documents. That still
exists. It is useful for screenshot QA and development, but it must stay clearly
separated from API-mode operator use.

What should improve next: the docs and default developer flow still make mock
mode too easy to confuse with operator mode. The README also has stale scaffold
language that says the backend Dashboard is mock-backed, even though current
API-mode Dashboard uses real state.

## Evidence Sources Checked

| Area | Evidence |
| --- | --- |
| Repository text search | `mock`, `demo`, `fake`, `fixture`, `sample`, `scaffold`, `placeholder`, `dummy`, `stub` |
| Source files | `backend`, `frontend`, `launcher`, `packaging`, `supabase`, `tests` |
| Documentation | `README.md`, `docs/*.md` |
| Frontend runtime split | `VITE_API_MODE`, `npm run build`, `npm run build:api` |
| Backend Dashboard | `/api/dashboard`, `/api/dashboard/summary` source and tests |
| Browser smoke | Dashboard, Upload, Logs, Settings via `127.0.0.1:5173` |

## Current Runtime Findings

| Surface | Finding | Runtime Risk |
| --- | --- | --- |
| Dashboard API | `/api/dashboard` aggregates real upload job, runtime, and audit state. | low |
| Dashboard browser | Visible state matched real latest upload job class and had no visible mock marker. | low |
| Upload browser | Preview and job views loaded API-backed state in the live smoke. | low |
| Logs browser | Job log view loaded persisted latest job events in the live smoke. | low |
| Settings browser | Settings loaded `/api/config` and did not show mock mode text. | low |
| Runtime config | Current dev backend source binding is environment-driven and should be treated as a context caveat before future upload work. | medium |
| Operator source display | Upload/Logs can display source locator and filename detail to the operator UI. This is not mock usage, but reports must continue to redact it. | medium |

## Remaining Mock Usage Classification

### Frontend Development And Demo Paths

| File | Classification | Operator API-Mode Impact |
| --- | --- | --- |
| `frontend/src/pages/dashboard/mockDashboardData.ts` | frontend mock Dashboard scenarios | none when `VITE_API_MODE=api` |
| `frontend/src/pages/dashboard/dashboardQuery.ts` | chooses mock Dashboard unless `VITE_API_MODE=api` | safe in API mode, confusing in default dev mode |
| `frontend/src/pages/upload/mockUploadPreview.ts` | frontend mock Preview scenarios | none when `VITE_API_MODE=api` |
| `frontend/src/pages/upload/mockUploadJob.ts` | frontend mock Upload Job scenarios | none when `VITE_API_MODE=api` |
| `frontend/src/pages/SettingsPage.tsx` | local mock config fallback | none when `VITE_API_MODE=api` |
| `frontend/src/pages/LogsPage.tsx` | local mock audit/job display fallback | none when `VITE_API_MODE=api` |

These files are still useful for local screenshot/demo testing, but they are
not suitable as operator validation evidence.

### Build And Packaging Modes

| File | Classification | Note |
| --- | --- | --- |
| `frontend/package.json` | default `npm run build` builds mock mode | API release requires `npm run build:api` |
| `frontend/scripts/build.mjs` | explicit `mock` and `api` build modes | expected |
| `packaging/assemble_operator_package.ps1` | supports mock/default and API package modes | API package has mode mismatch guards |

The main caveat is developer ergonomics: the default build is still mock mode.
That is intentional compatibility, but operator work should use API mode.

### Tests And Fixtures

Tests use stubs, fake runners, temporary fixtures, and fixture CSVs. This is
expected and is not operator runtime mock usage.

The protected operational fixture remains uncommitted and outside this audit
PR scope.

### Documentation

Older docs and README sections still contain scaffold-era statements such as
mock backend Dashboard, mock-first Dashboard, placeholder pages, and mock
Upload Preview defaults.

Some of that text is historical, but parts of `README.md` are now stale for the
current API-mode operator state. This is the main cleanup candidate from the
audit.

## Browser Smoke Result

The browser smoke used the current local frontend on `127.0.0.1:5173`.

| Page | Visible Mock Marker | API-backed Evidence |
| --- | --- | --- |
| Dashboard | no | called Dashboard and runtime APIs |
| Upload | no | called latest Preview and Dashboard APIs |
| Logs | no | called latest Upload Job API |
| Settings | no | called Config API |

No failed browser requests were observed during the smoke.

## Caveats

- URL path navigation is not the app routing model. The app uses internal
  sidebar state, so page smoke used sidebar navigation.
- Current runtime config must be rechecked before any future upload. This audit
  was about mock usage, not source eligibility or upload approval.
- Browser smoke can prove current visible behavior, but it does not remove mock
  code used by non-API development mode.
- Documentation search found many historical mock/scaffold references. They
  should be cleaned selectively, not bulk-deleted, because some are useful
  project history.

## Decision

Current API-mode operator runtime is not mock-backed based on this audit.

Remaining mock code is acceptable only as non-API dev/demo/test support. The
next product hardening step should reduce operator confusion by making API mode
more explicit in docs and startup guidance.

## Recommended Next Work

Create a docs-only README freshness update that:

1. marks scaffold-era mock Dashboard statements as historical;
2. states that API-mode Dashboard now uses real state;
3. clarifies that default frontend build/dev mode can still be mock-backed;
4. tells operator validation to use API mode only;
5. preserves screenshot/mock QA instructions as development-only.

No upload work is needed for this cleanup.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase lifecycle or destructive operation;
- Docker lifecycle or destructive operation;
- operational source mutation, deletion, or rename;
- protected untracked artifact commit or deletion.

## Redaction Result

This document records only repo-relative paths, sanitized runtime classes, and
aggregate audit conclusions.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no token, credential-bearing header value, JWT, or secret;
- no raw Edge authenticated request payload;
- no destructive command output.

## Validation

| Check | Result |
| --- | --- |
| Repository mock keyword search | completed |
| Runtime browser smoke | completed |
| whitespace check | passed |
| New document marker scan | passed |
| PR file scope | docs/130 only expected |

## Next Safe Action

Open this docs-only mock usage audit PR for review.

After merge, the next safest task is README/docs freshness cleanup for
API-mode versus mock-mode language. Future upload work still starts from a fresh
Preview-only gate and separate explicit approval.
