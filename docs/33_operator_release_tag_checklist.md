# Operator Package Release Tag / Checklist Plan

Status: planned

Date: 2026-06-07

Scope: document-only engineering plan for tagging and preparing an operator package release after final package smoke and handoff runbook readiness.

This plan does not create a git tag, GitHub Release, package zip, checksum, production deploy, launcher change, backend change, frontend change, or packaging script change.

## Goal

Define the final maintainer checklist that must pass before an operator package is tagged and handed off.

The checklist keeps these decisions explicit:

- release readiness criteria
- version and tag naming convention
- package zip and checksum verification
- package output location and repo exclusion
- final smoke evidence
- handoff runbook evidence
- rollback criteria
- operator replacement and support checklist
- release note content
- GitHub tag/release preflight
- security and redaction policy

## Decision Summary

| Topic | Decision |
| --- | --- |
| Tag creation in this PR | Out of scope |
| GitHub Release creation in this PR | Out of scope |
| Production deploy | Forbidden until separately approved |
| Feature branch deletion | Forbidden by default |
| Package output location | Repo-external only |
| Release evidence | Final smoke report plus handoff runbook |
| Release artifact policy | Zip plus adjacent checksum, never package temp outputs into git |
| Secret policy | No raw secret, DB URL, token, Authorization header, or operational data exposure |

## Release Readiness Criteria

A package is release-ready only when every criterion below is true:

| Criterion | Required evidence |
| --- | --- |
| Source branch is `main` | Maintainer records source commit |
| `VERSION` is reviewed | Version value matches intended release line |
| Changelog is reviewed | Operator-facing additions and known limitations are documented |
| Package assembly passed | Manifest validation reports required paths, operator readiness, denylist `0`, redaction `0` |
| Zip and checksum created | Zip exists outside repo and adjacent checksum exists |
| Checksum verified | SHA-256 of zip matches checksum file |
| Zip-entry scan passed | cache/test/docs/denylist counts are `0`, runtime files and metadata are present |
| Redaction scan passed | credential, operational filename-family, Windows path, DB URL, Authorization, and JWT markers are `0` |
| Extracted package smoke passed | Import, launcher, shortcut, HTTP, token guard, and API docs hardening checks passed |
| Handoff runbook reviewed | Operator handoff steps and rollback path are current |
| Package outputs are not tracked | Git status does not include package output, zip, checksum, `.gstack`, `frontend/dist`, or operational CSV fixtures |

If any criterion fails, do not tag the release. Record the blocker and open a follow-up branch.

## Version And Tag Naming

The repository `VERSION` file remains the source of the semantic package version.

Recommended tag format:

```text
operator-package-v<VERSION>
```

Examples:

```text
operator-package-v0.1.0.0
```

If more than one package candidate is produced for the same version before handoff, use package labels for candidate identity and keep the git tag for the accepted release only.

Recommended package label format:

```text
ewc-operator-<VERSION>-<YYYYMMDD>-rc<N>
```

Example:

```text
ewc-operator-0.1.0.0-20260607-rc1
```

Tag naming rules:

- tag points at the accepted `main` commit
- tag is created only after release readiness is approved
- tag name does not include local paths, operator names, machine names, tokens, or data source names
- do not create multiple tags for rejected package candidates

## Package Output Policy

Package output must stay outside the repository.

Recommended output root:

```text
C:\tmp\ExtrusionWebConsole-packages\
```

Required release artifacts:

| Artifact | Commit to git? | Handoff? |
| --- | --- | --- |
| package folder | No | Optional maintainer staging only |
| package zip | No | Yes |
| package checksum | No | Yes |
| final smoke report | Yes, as docs | Optional maintainer evidence |
| handoff runbook | Yes, as docs | Yes |

Never commit:

- package output folders
- package zip files
- checksum files
- `.gstack` artifacts
- `frontend/dist`
- raw `.env` files
- logs
- state databases
- operational CSV fixtures, paths, or contents

## Package Zip And Checksum Verification

Before any release tag is created, verify the package zip against the adjacent checksum.

Maintainer check:

```powershell
$zip = "<package-label>.zip"
$checksum = "<package-label>.zip.sha256"
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLowerInvariant()
$expected = (Get-Content -LiteralPath $checksum -Raw).Split()[0].ToLowerInvariant()
if ($actual -ne $expected) { throw "Package checksum mismatch" }
```

The checksum file is required for operator handoff. A package without a checksum is not release-ready.

## Final Smoke Confirmation

Use `docs/31_operator_package_release_smoke_final.md` as the final smoke evidence source.

Before tagging, confirm the accepted package has evidence for:

| Smoke area | Required result |
| --- | --- |
| Targeted packaging tests | Passed |
| Full backend clean-cwd tests | Passed or explicitly waived with reason |
| Frontend typecheck/build/screenshot QA | Passed |
| Package assembly with `-CreateZip` | Passed |
| Zip checksum verification | Passed |
| Zip-entry scan | Required blocker classes count `0` |
| Redaction scan | Required marker classes count `0` |
| Extracted import smoke | Passed |
| Launcher and shortcut `-CheckOnly` | Passed |
| HTTP smoke | `/`, `/upload`, `/logs`, `/settings`, `/api/health`, `/api/config`, `/api/audit?limit=1` passed |
| Token smoke | no-token mutating request returns `403`; read-only no-token requests pass |
| API docs hardening | `/api/docs`, `/api/openapi.json`, `/api/redoc` return `404` in operator mode |

The accepted package must be the same package named in the final smoke evidence. Do not tag a release for a different package label without rerunning or updating final smoke evidence.

## Handoff Runbook Confirmation

Use `docs/32_operator_package_handoff_runbook.md` as the operator handoff procedure.

Before tagging, confirm the runbook covers:

- delivered artifacts
- checksum verification
- extraction location
- pre-launch checks
- shortcut install
- first launch
- Settings verification
- runtime smoke pages
- log locations
- rollback
- replacement policy
- support escalation
- acceptance checklist

If a package-specific handoff condition changes, update the runbook before release tagging.

## Rollback Criteria

Do not release unless rollback is clear and non-destructive.

Rollback criteria:

| Area | Requirement |
| --- | --- |
| Previous package | Previous known-good package folder remains available until acceptance |
| Shortcuts | Shortcuts can be pointed back by running the previous package shortcut installer |
| AppData | Config, state, and logs are not deleted during rollback |
| Local Supabase | DB data, containers, and volumes are not deleted during rollback |
| Operational data | Operational CSV files are not deleted, moved, or packaged |
| Support evidence | Failed package folder can be retained for maintainer inspection |

Rollback is blocked if the previous known-good package is unavailable and no maintainer-approved recovery path exists.

## Operator Replacement Checklist

Before replacing an operator package:

| Check | Status |
| --- | --- |
| Release tag candidate approved |  |
| Zip checksum verified |  |
| Package extracted into new versioned folder |  |
| Launcher `-CheckOnly` passed |  |
| Shortcut installer `-CheckOnly` passed |  |
| Previous known-good package retained |  |
| Shortcuts updated only after checks pass |  |
| Dashboard loads |  |
| Settings loads |  |
| Logs load |  |
| Rollback path confirmed |  |

Replacement must not run database reset, database cleanup, Docker cleanup, AppData deletion, or package-output deletion.

## Support Checklist

Support notes for a release should include only safe metadata:

| Safe field | Example style |
| --- | --- |
| tag name | `operator-package-v<VERSION>` |
| package label | sanitized package label |
| source commit | git commit hash |
| checksum status | passed/failed |
| first failed step | concise step name |
| timestamp | local date/time |
| sanitized error summary | no secrets or local data paths |

Support notes must not include:

- raw secret values
- DB URLs
- local API tokens
- Authorization headers
- JWTs
- raw `.env` contents
- operational CSV paths
- operational CSV filenames
- operational CSV contents
- raw row contents

## Release Note Criteria

Release notes should be short and operator-facing.

Include:

- release version and tag
- package label
- source commit
- release readiness status
- major operator-facing capabilities
- package handoff steps reference
- known limitations
- rollback summary
- support escalation path

Do not include:

- secret values
- local data paths
- operational file names
- implementation-only scanner patterns
- raw command output containing machine-specific data

Recommended release note sections:

```text
Summary
Package
Readiness
Handoff
Known limitations
Rollback
Support
```

## GitHub Tag / Release Preflight

Before creating a GitHub tag or release, verify:

| Check | Status |
| --- | --- |
| `main` is up to date with `origin/main` |  |
| working tree has no staged changes |  |
| only allowed untracked local artifacts remain |  |
| final smoke report is on `main` |  |
| handoff runbook is on `main` |  |
| `VERSION` matches intended tag |  |
| `CHANGELOG.md` has relevant package notes |  |
| release artifacts are outside repo |  |
| zip checksum verification passed |  |
| redaction and denylist scans passed |  |
| production deploy approval is separate |  |
| feature branch deletion is separately approved, if desired |  |

GitHub release/tag creation is explicitly out of scope for this PR. The next step must be separately approved before any tag or release is created.

## Security And Redaction Rules

All release checklist records must remain safe to store in the repository.

Forbidden in release docs, PR bodies, release notes, and support notes:

- raw secret values
- DB URLs
- token values
- Authorization headers
- JWTs
- raw `.env` contents
- operational CSV paths
- operational CSV filenames
- operational CSV contents
- raw row contents

Allowed:

- count-only scan results
- pass/fail statuses
- package labels without local data identifiers
- source commit hashes
- `VERSION`
- generic placeholders

## Production Deploy Policy

Operator package release tagging is not production deployment.

Production deploy remains forbidden until a separate explicit approval exists. The release tag/checklist process must not:

- deploy a hosted service
- mutate production infrastructure
- run database migrations against production
- start or stop production services
- delete feature branches

## Implementation Order For A Future Release

1. Confirm `main` contains final smoke and handoff runbook.
2. Build frontend and prepare target-PC `.venv`.
3. Assemble package outside the repo with a release-candidate label.
4. Create zip and checksum.
5. Verify checksum.
6. Run final smoke.
7. Confirm release readiness criteria.
8. Review release notes.
9. Request explicit approval for tag/release creation.
10. Create tag and GitHub Release only after approval.
11. Hand off zip and checksum using the handoff runbook.
12. Keep previous known-good package until operator acceptance.

## Out Of Scope

- creating a git tag
- creating a GitHub Release
- changing `VERSION`
- changing `CHANGELOG.md`
- changing package assembly code
- changing launcher, backend, frontend, or packaging scripts
- creating package output, zip, or checksum
- production deploy
- feature branch deletion
- DB reset/delete/cleanup/prune
- Docker volume/container delete or prune
- AppData config/state/log deletion
- committing package output, `.gstack`, `frontend/dist`, or operational CSV fixtures
