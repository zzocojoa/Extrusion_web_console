# Operator Handoff Acceptance QA

Date: 2026-06-07

Branch: `codex/operator-handoff-acceptance`

Base commit: `e9875b7d2a39a51d461997b281436c23f625a729`

Scope: report-only operator handoff acceptance record for release `operator-package-v0.1.0.0`.

This report does not change product code, launcher behavior, backend behavior, frontend behavior, package assembly, GitHub Release assets, tags, local runtime policy, AppData state, Docker state, database state, shortcut state, or operational data.

## Summary

Acceptance is `accepted with caveats` based on sanitized operator package execution evidence collected on 2026-06-07.

The release, tag, assets, checksum, final smoke, dry-run report, handoff runbook, package extraction, shortcut installation, UI routes, read-only APIs, local token guard, and API docs hardening were verified with sanitized evidence. The default port handoff path is caveated because a pre-existing dev-mode backend occupied the default launcher port during this acceptance run. The package runtime was then verified on an alternate local port without exposing token values or operational paths.

No production deploy was performed. No GitHub Release or tag was modified.

## Target Release

| Item | Result |
| --- | --- |
| Release URL | `https://github.com/zzocojoa/Extrusion_web_console/releases/tag/operator-package-v0.1.0.0` |
| Release name | `Operator Package v0.1.0.0` |
| Release type | normal release |
| Draft | `false` |
| Prerelease | `false` |
| Tag | `operator-package-v0.1.0.0` |
| Tag target | `main` |
| Package label | `ewc-final-release-smoke-20260607-rc1` |

## Handoff Date And Evidence

| Item | Result |
| --- | --- |
| Report date | 2026-06-07 |
| Evidence refresh date | 2026-06-07 |
| Operator-side handoff timestamp | 2026-06-07, local operator package session |
| Operator PC evidence | provided as sanitized pass/fail results |
| Maintainer/operator acceptance notes | default port caveat recorded |
| Sanitized extraction label | operator-package-folder |

The extraction location must be recorded only as a sanitized label when operator evidence becomes available.

Sanitized operator-side evidence was collected without recording raw local package paths, local token values, database URLs, authorization headers, operational filenames, or operational data contents.

## Acceptance Checklist

| Check | Result | Notes |
| --- | --- | --- |
| Release/tag confirmed | passed | Release exists as a normal release with the expected tag |
| Package zip asset confirmed | passed | Expected zip asset is uploaded |
| Package checksum asset confirmed | passed | Expected checksum asset is uploaded |
| Checksum verification on operator PC | passed | SHA-256 matched the release digest |
| Extraction location | passed | Sanitized label: operator-package-folder |
| Shortcut install | passed | Desktop and Start menu shortcut installation completed |
| First launch | passed with caveat | Default port was blocked by a pre-existing dev-mode backend; package runtime was verified on an alternate local port |
| Settings screen | passed | Settings route returned success in operator package runtime smoke |
| Logs/Audit screen | passed | Logs route and audit API returned success in operator package runtime smoke |
| Local token behavior | passed | Read-only APIs succeeded; mutating config write without token returned `403` in operator package runtime smoke |
| API docs hardening | passed | `/api/docs`, `/api/openapi.json`, and `/api/redoc` returned `404` in operator package runtime smoke |
| Rollback procedure delivered | passed | Handoff runbook rollback procedure was reviewed |
| Support contact/process delivered | passed | Handoff runbook support process was reviewed |

## Release Asset Baseline

| Asset | Result |
| --- | --- |
| `ewc-final-release-smoke-20260607-rc1.zip` | present, uploaded |
| `ewc-final-release-smoke-20260607-rc1.zip.sha256` | present, uploaded |
| Zip digest | `58bfcd499b8bbadf85f082261f99a2e62aa1ee1c4b4bf72824ba135804a69300` |

The release asset baseline is consistent with `docs/31_operator_package_release_smoke_final.md`, `docs/33_operator_release_tag_checklist.md`, and `docs/34_operator_handoff_dry_run.md`.

## Runbook Coverage

`docs/32_operator_package_handoff_runbook.md` contains the expected operator handoff procedure:

| Runbook area | Coverage |
| --- | --- |
| Package zip and checksum handoff | covered |
| Checksum verification | covered |
| Extraction location | covered |
| Pre-launch checks | covered |
| Shortcut install | covered |
| First launch | covered |
| Settings verification | covered |
| Runtime smoke pages | covered |
| Log locations | covered |
| Rollback | covered |
| Replacement policy | covered |
| Support escalation | covered |
| Acceptance checklist | covered |

## Findings

### Caveat

The default launcher port was already occupied by a pre-existing dev-mode backend in the acceptance environment.

The first default-port launcher attempt correctly refused to reuse that backend because it did not expose the local token bootstrap page. This protects the operator flow from accidentally accepting a dev-mode backend as the packaged runtime. After the port conflict was isolated, the same package runtime was verified on an alternate local port.

Before routine operator use on the default shortcut path, ensure no pre-existing service is occupying the launcher port.

### Non-blocking

No document/release consistency issue was found in the repository-side evidence reviewed for this report.

## Security And Redaction

This report intentionally does not include:

- raw secret values
- database connection strings
- local write-guard values
- authorization headers
- JWT-shaped values
- raw environment files
- operational data paths
- operational data filenames
- operational data contents
- raw row contents
- full local package output paths

## Acceptance Verdict

`accepted with caveats`

Reason: sanitized operator package evidence passed checksum, extraction, shortcut install, UI route, read-only API, local token guard, and API docs hardening checks. The only caveat is that the default-port launcher path was blocked by a pre-existing dev-mode backend in the acceptance environment; the packaged operator runtime passed on an alternate local port.

## Out Of Scope

- feature implementation
- launcher changes
- backend changes
- frontend changes
- packaging script changes
- GitHub Release changes
- git tag changes
- production deploy
- default-port routine operator launch on a machine already running a dev-mode backend
- database reset/delete/cleanup/prune
- Docker volume/container delete or prune
- AppData config/state/log deletion
- committing package output, zip, checksum, generated screenshots, or operational fixtures

## Next Step

If this package is handed to another operator workstation, repeat the default shortcut launch after confirming the launcher port is free. If the port is free and the same checks pass, the caveat can be closed in a follow-up report.
