# Operator Package Handoff Dry-Run QA

Date: 2026-06-07

Branch: `codex/operator-handoff-dry-run`

Base commit: `014ddaaa2a432f1b9224dad89b44d0fd8e29cc04`

Scope: report-only dry-run of the operator handoff flow for release `operator-package-v0.1.0.0`.

This report does not change product code, launcher behavior, backend behavior, frontend behavior, package assembly, local runtime policy, AppData state, Docker state, database state, shortcut state, or operational data.

## Summary

The release asset handoff procedure is executable as a maintainer/operator dry-run.

The GitHub Release is published as a normal release, the release tag resolves to the intended `main` commit, both release assets are present, the checksum verification procedure passed against the release-candidate artifact, the package zip contains the expected handoff files, and the handoff runbook covers checksum verification, extraction, pre-launch checks, shortcut install, first launch, Settings verification, log locations, rollback, replacement, and support escalation.

No production deploy was performed. No real operator PC install or deployment was performed. No shortcut was installed or refreshed during this dry-run.

## Target Release

| Item | Result |
| --- | --- |
| Release URL | `https://github.com/zzocojoa/Extrusion_web_console/releases/tag/operator-package-v0.1.0.0` |
| Release name | `Operator Package v0.1.0.0` |
| Release type | normal release |
| Draft | `false` |
| Prerelease | `false` |
| Tag | `operator-package-v0.1.0.0` |
| Tag target commit | `014ddaaa2a432f1b9224dad89b44d0fd8e29cc04` |
| VERSION | `0.1.0.0` |
| Artifact label | `ewc-final-release-smoke-20260607-rc1` |

## Release Assets

| Asset | Result |
| --- | --- |
| `ewc-final-release-smoke-20260607-rc1.zip` | present, uploaded |
| `ewc-final-release-smoke-20260607-rc1.zip.sha256` | present, uploaded |
| Zip digest | `58bfcd499b8bbadf85f082261f99a2e62aa1ee1c4b4bf72824ba135804a69300` |
| Local checksum verification | passed |

The release note and this report use the sanitized artifact label only. Full local package output paths are intentionally not recorded.

## Dry-Run Checks

| Check | Result | Evidence |
| --- | --- | --- |
| GitHub Release status | passed | Release is normal, not draft, not prerelease |
| Release tag target | passed | Tag resolves to the intended `main` commit |
| Zip/checksum assets | passed | Both expected asset names are uploaded |
| Checksum procedure | passed | Recomputed zip SHA-256 matched adjacent checksum |
| Package handoff contents | passed | Package docs, launcher scripts, built frontend, and prepared Python runtime were present in the zip |
| Package denylist | passed | Denylist scan returned `0` matches |
| Redaction scan | passed | Sensitive marker scan returned `0` matches |
| Release note consistency | passed | Release note references the same tag, commit, artifact label, checksum, readiness evidence, handoff runbook, limitations, rollback, and no production deploy |
| Handoff runbook consistency | passed | Runbook covers delivered artifacts, checksum, extraction, pre-launch checks, shortcut install, first launch, Settings, logs, rollback, replacement, support, and acceptance |

## Package Contents Spot Check

The package zip was checked for the handoff-critical entries below:

| Package entry | Result |
| --- | --- |
| `README.md` | present |
| `CHANGELOG.md` | present |
| `VERSION` | present |
| `docs/operator_package_runtime_note.md` | present |
| launcher start script | present |
| shortcut installer script | present |
| built frontend app shell | present |
| prepared Python runtime | present |

Denylist scan result: `0` matches.

## Redaction Result

Count-only scan result for package text files outside the prepared runtime:

| Marker class | Count |
| --- | ---: |
| credential-like marker | 0 |
| operational filename-family marker | 0 |
| Windows absolute path marker | 0 |
| database connection marker | 0 |
| bearer-header marker | 0 |
| JWT-shaped marker | 0 |

This dry-run did not record secret-bearing values, local write-guard values, database connection strings, raw environment content, operational data paths, operational data filenames, operational data contents, or raw row contents.

## Operator Handoff Procedure Review

| Runbook step | Dry-run result |
| --- | --- |
| Handoff artifacts | actionable: deliver zip and adjacent checksum only |
| Checksum verification | actionable: stop if checksum does not match |
| Extraction location | actionable: use a stable operator-owned folder, not a source repo or temporary download folder |
| Pre-launch checks | actionable: run launcher and shortcut installer in check-only mode before writing shortcuts |
| Shortcut install | actionable: install or refresh shortcuts only after checks pass |
| First launch | actionable: launcher starts localhost backend, serves built frontend, opens Dashboard |
| Settings verification | actionable: verify Settings loads, override fields are read-only, and secret fields remain hidden |
| Runtime smoke | actionable: Dashboard, Upload, Logs, and Settings are the acceptance pages |
| Log locations | actionable: launcher logs and app state locations are documented without collecting sensitive values |
| Rollback | actionable: keep previous known-good package and restore shortcuts to it if needed |
| Replacement policy | actionable: extract into a new versioned folder and keep previous package until acceptance |
| Support escalation | actionable: collect package label, version, checksum status, check-only status, failed step, timestamp, and sanitized summary |

## Findings

No release handoff blockers found.

The release asset names, checksum, release note, final smoke report, release checklist, and handoff runbook align for an operator handoff dry-run.

## Limitations

- This was a dry-run against the release asset and documented handoff flow.
- No real operator PC install was performed.
- No production deploy was performed.
- No shortcut was installed or refreshed.
- No local runtime, database, Docker, or AppData destructive action was performed.
- Local runtime readiness remains a target-machine acceptance check.

## Merge Blocker Assessment

No merge blocker for this report-only QA PR.

Recommended next step: perform the operator handoff using the release assets and `docs/32_operator_package_handoff_runbook.md`, then record operator acceptance or support findings in a follow-up report if needed.
