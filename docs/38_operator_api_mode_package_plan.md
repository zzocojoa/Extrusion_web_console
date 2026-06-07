# API-Mode Operator Package Release Plan

Status: plan, build metadata implementation started on `codex/operator-api-mode-build-metadata`

Date: 2026-06-07

Branch: `codex/operator-api-mode-package-plan`

Scope: engineering plan for a future API-mode operator package release.

This plan does not change feature code, launcher behavior, backend behavior, frontend behavior, package assembly scripts, packaging manifests, GitHub Release assets, tags, production deployment, local Supabase data, Docker data, database data, AppData state, or operational CSV data.

## Goal

Create a separate operator package release line for real backend/API/local Supabase operation.

The existing `operator-package-v0.1.0.0` release remains the accepted mock-mode/operator-shell package. It must not be edited, retagged, replaced, or used ambiguously for API-mode handoff.

API-mode package release readiness requires:

- built frontend compiled with API mode
- package metadata that records the runtime mode
- local Supabase readiness gates before Upload Preview smoke
- Upload Preview API-mode browser smoke
- explicit proof that Upload Start was not clicked before separate approval
- the same package hygiene, token, API docs hardening, redaction, rollback, and handoff controls as the existing operator package flow

## Current Evidence

| Evidence | Decision impact |
| --- | --- |
| `docs/31_operator_package_release_smoke_final.md` | Existing package assembly, zip, launcher, token guard, docs hardening, and redaction hygiene passed. Reuse these gates. |
| `docs/36_operator_handoff_caveat_closure.md` | Default-port launcher behavior is accepted when stale dev-mode backends are closed. Reuse this as a required smoke. |
| `docs/37_operator_api_mode_preview_smoke.md` | Existing release cannot prove API-mode Preview because the frontend remained mock-mode built and local Supabase readiness was unavailable. This is the direct release gap. |
| `packaging/operator-package.manifest.json` | Existing allowlist/denylist is appropriate. Future work should not broaden package contents for API mode. |
| `packaging/assemble_operator_package.ps1` | Existing script is safe for package assembly. The next implementation must record and enforce frontend build mode as a first-class release contract. |

## Decision Summary

1. API-mode operator package uses a distinct release tag and package label.
2. The mock-mode release is preserved and never mutated.
3. API mode is selected at frontend build time with `VITE_API_MODE=api`.
4. Package metadata must record `frontendMode=api`.
5. Package contents stay on the current manifest allowlist.
6. API-mode package includes only an API-mode `frontend/dist`.
7. Runtime prerequisites are verified by presence/status only; secret values are never packaged or documented.
8. Upload Preview API-mode smoke is required before API-mode handoff acceptance.
9. Upload Start remains out of scope until a separate approval.
10. Production deploy remains out of scope.

## 1. API-Mode Package Naming

Use a tag and package label that cannot be confused with the existing mock-mode package.

Recommended tag:

```text
operator-package-api-v0.1.0.0
```

Recommended package label:

```text
ewc-api-mode-release-20260607-rc1
```

Rationale:

- Prefixing the tag with `operator-package-api-` is clearer than suffixing the base package tag.
- It avoids implying that the existing `operator-package-v0.1.0.0` release was replaced.
- It keeps API-mode release notes visually distinct in GitHub Releases.

Rejected naming:

| Option | Reason |
| --- | --- |
| `operator-package-v0.1.0.0` reused | Would mutate accepted release history. |
| `operator-package-v0.1.0.1-api` | Suggests a patch release of the same line instead of a separate mode line. |
| Same zip label with `api` only in notes | Too easy for a maintainer/operator to confuse during handoff. |

## 2. Build Mode

API-mode release build must set:

```text
VITE_API_MODE=api
```

The build must be a release-maintainer step before assembly. The operator double-click flow must not run `npm run build`.

Implementation contract:

| Decision | Requirement |
| --- | --- |
| Build command | Maintainer runs `npm run build:api` from `frontend/` for API-mode packages. |
| Mock/API distinction | `npm run build` writes mock/default frontend metadata; `npm run build:api` writes API-mode frontend metadata. |
| Package metadata | `package-build-info.json` includes `frontendMode` and source commit. |
| Validation gate | `packaging/assemble_operator_package.ps1 -FrontendMode api` fails if `frontend/dist` is mock-mode or missing mode metadata. |
| Release note | GitHub Release notes must state `API mode frontend build`. |
| Existing mock build | Keep available for screenshot QA and mock-mode package line. |

Implemented first step:

1. `npm run build` keeps the mock/default package path.
2. `npm run build:api` creates API-mode `frontend/dist`.
3. `frontend/dist/frontend-build-info.json` records frontend mode.
4. Assembly records `frontendMode` in package metadata.
5. Explicit API-mode assembly fails fast on mode mismatch.

Remaining future work is to run API-mode package assembly, smoke, tag, and release only after separate approval.

## 3. Package Contents

Reuse the existing manifest allowlist.

Expected package tree remains:

```text
ExtrusionWebConsole/
  backend/
  frontend/dist/
  launcher/
  docs/operator_package_runtime_note.md
  .venv/
  README.md
  CHANGELOG.md
  VERSION
  package-build-info.json
```

API-mode-specific package rule:

```text
frontend/dist/ must be the API-mode build artifact.
```

Keep excluding:

- raw `.env` files
- secret-bearing config files
- local tokens
- operational CSV data
- operational CSV paths or filenames
- logs
- state databases
- `.git`
- `.gstack`
- `frontend/node_modules`
- `frontend/src`
- `frontend/qa`
- `tests`
- package outputs, zips, and checksums from source control

No new runtime source directories are needed for API mode.

## 4. Runtime Prerequisites

API-mode package handoff requires a pre-smoke readiness gate.

Presence-only checks:

| Readiness item | Required evidence |
| --- | --- |
| Docker Desktop/runtime | Available |
| Local Supabase API | Reachable |
| Local Supabase Studio | Reachable |
| Local Supabase DB port | Reachable |
| Edge runtime | Reachable if Upload Job smoke is in scope |
| Source config | Present |
| State config | Present |
| DB URL config | Present, value hidden |
| Supabase API URL config | Present, value hidden if treated as sensitive |
| Auth key config | Present, value hidden |
| Settings UI | Secret fields hidden |

Do not ask the operator or user to paste secret values into chat, PR body, release notes, reports, or logs.

Do not include secret values in the package. Runtime configuration remains outside the package under the existing local config and environment precedence model.

Stop conditions:

| Stop condition | Required action |
| --- | --- |
| Docker unavailable | Stop and report `runtime_unavailable`. |
| Local Supabase endpoint unreachable | Stop and report `runtime_unavailable`. |
| Required config missing | Stop and report `preconfigured_env_missing` or `config_missing`. |
| Settings exposes raw secret | Stop and report redaction failure. |
| Preview would use mock mode | Stop and report `frontend_mode_mismatch`. |
| Sample/source unsafe | Stop and report `sample_unsafe`. |

## 5. Validation And Smoke

API-mode package release must pass the existing package gates plus API-mode Preview gates.

### Package Hygiene

| Check | Expected result |
| --- | --- |
| Checksum verification | Passed |
| Zip-entry scan | No denylist or marker matches |
| Package redaction scan | No raw secret/path/token/operational data markers |
| Runtime prune scan | No cache/test-only content in clean zip |
| Package metadata | Includes source commit, package label, zip status, and `frontendMode=api` |

### Launcher And HTTP

| Check | Expected result |
| --- | --- |
| `launcher/start_web_console.ps1 -CheckOnly` | Passed |
| `launcher/install_shortcuts.ps1 -CheckOnly` | Passed |
| Default-port launcher smoke | Passed on clean default port |
| `/` | `200` |
| `/upload` | `200` |
| `/logs` | `200` |
| `/settings` | `200` |
| `/api/health` | `200` |
| `/api/config` | `200`, secret values hidden |
| `/api/audit?limit=1` | `200` |
| No-token mutating API | `403` |
| `/api/docs`, `/api/openapi.json`, `/api/redoc` | `404` |

### Browser Smoke

Use the in-app Browser or project-owned browser tooling against the package runtime.

Required pages:

- Dashboard
- Upload
- Logs
- Settings

Required assertions:

- Settings does not show mock mode.
- Settings fields load from API.
- Secret fields remain hidden.
- Upload Preview button is visible.
- Upload Start is not clicked.
- Preview result does not contain mock-only markers.
- Browser console errors are captured.
- Failed requests are captured when tooling supports it.

### Upload Preview API-Mode Smoke

Run Upload Preview only.

Record sanitized counts:

| Metric | Required |
| --- | --- |
| Preview status | Yes |
| DB status | Yes |
| Target file count | Yes |
| Already in DB count | Yes |
| Partial overlap count | Yes |
| Risky count | Yes |
| Excluded count | Yes |
| Upload row estimate | Yes |
| DB matched rows | Yes |
| Audit row present | Yes |
| Redaction result | Yes |

Do not record raw source paths, filenames, CSV contents, row contents, DB URLs, tokens, authorization headers, JWTs, or local package paths.

If Preview is blocked, document the blocker instead of forcing config or mutating runtime state.

## 6. Release And Tag Policy

The existing release remains immutable:

```text
operator-package-v0.1.0.0
```

Future API-mode release should use:

```text
operator-package-api-v0.1.0.0
```

Release notes must clearly state:

- API-mode frontend build
- local Supabase readiness required
- Upload Preview API-mode smoke result
- Upload Start not included unless separately approved
- package zip/checksum asset names
- checksum verification requirement
- no production deploy
- no secret/package config values included
- rollback to previous known-good package folder remains supported

Do not:

- replace existing mock-mode release assets
- move the existing tag
- edit existing release notes to imply API-mode readiness
- create a production deployment from package release
- delete feature branches as part of release

## 7. Rollback And Handoff

Rollback remains package-folder based.

Recommended API-mode handoff relationship:

| Package | Role |
| --- | --- |
| Existing mock-mode release | Known-good shell and launcher fallback |
| New API-mode release | Real API/local Supabase Preview candidate |

If API-mode handoff fails:

1. Stop the current package runtime.
2. Keep the failed API-mode package for maintainer inspection.
3. Reinstall shortcuts from the previous known-good package folder.
4. Verify Dashboard, Settings, and Logs load.
5. Do not delete AppData config, state DB, logs, Docker resources, database data, or operational CSV data.

The handoff runbook should receive a future API-mode appendix or update after implementation. Required additions:

- API-mode package label recognition
- `frontendMode=api` metadata check
- local Supabase readiness checklist
- Upload Preview-only acceptance path
- explicit Upload Start approval gate
- support escalation for `frontend_mode_mismatch`, `runtime_unavailable`, and `config_missing`

API-mode handoff acceptance requires:

- checksum passed
- launcher and shortcut check-only passed
- default-port launcher smoke passed
- Settings API mode confirmed
- local Supabase readiness passed
- Upload Preview API-mode smoke passed or caveat accepted
- redaction passed
- Upload Start not clicked unless separately approved

## 8. Out Of Scope

This plan explicitly excludes:

- feature code changes
- launcher changes
- backend changes
- frontend changes
- packaging script changes
- actual package build
- zip or checksum creation
- GitHub Release or tag creation
- production deployment
- DB reset/delete/cleanup/prune
- Docker volume/container delete or prune
- local Supabase bootstrap/create/init
- Upload Start execution
- raw secret value documentation
- existing release asset replacement

## 9. Implementation Order

Future implementation should proceed in small PRs:

1. Add package build-mode metadata and validation plan implementation.
2. Add maintainer command or flag for API-mode frontend build.
3. Build API-mode `frontend/dist` in a release-maintainer environment.
4. Assemble package with existing manifest allowlist and API-mode dist.
5. Run package hygiene, zip, checksum, prune, and redaction scans.
6. Run launcher, shortcut, HTTP, token, and API docs smoke.
7. Run API-mode browser smoke for Dashboard, Upload, Logs, and Settings.
8. Run Upload Preview only.
9. Verify `upload.preview` audit row.
10. Write API-mode release smoke report.
11. After explicit approval, create API-mode tag and GitHub Release assets.
12. Run API-mode handoff acceptance.

## Engineering Review Verdict

Plan verdict: ready for implementation planning.

The key engineering decision is to treat API-mode packaging as a distinct release line, not a mutation of the accepted mock-mode release. This avoids operator confusion and preserves rollback while allowing the next release to prove real local Supabase Upload Preview behavior.
