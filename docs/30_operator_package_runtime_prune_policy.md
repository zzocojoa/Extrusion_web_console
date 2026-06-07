# Operator Package Runtime Prune / Redaction Policy

Status: implemented

Date: 2026-06-07

Scope: plan-stage engineering review for resolving operator package release-candidate blockers found in `docs/29_operator_package_release_smoke.md`.

## Goal

Make the prepared operator package release-ready without weakening runtime safety.

The next implementation must remove package-only hygiene blockers while preserving the operator launch path:

- FastAPI static serving from the package root.
- launcher local token enforcement for mutating APIs.
- API docs disabled in operator mode.
- prepared `.venv/Scripts/python.exe` available for non-developer launch.
- no Node/npm requirement in operator mode.

This policy is implemented in `packaging/operator-package.manifest.json` and `packaging/assemble_operator_package.ps1`. The implementation changes package assembly hygiene only; it does not change product API behavior, frontend behavior, launcher local token enforcement, AppData state, local Supabase, Docker, or package outputs.

Implementation notes:

- Runtime `.venv` copy now prunes cache/test-only content and preserves dependency metadata/license files.
- Operator package docs now use a sanitized package runtime note instead of copying marker-heavy source docs into release artifacts.
- Package redaction checks now include credential-like assignment markers, operational filename-family markers, and Windows absolute path markers.
- Assembly output remains count-oriented and does not print secret values.

PR #38 QA result:

- Targeted packaging tests: 11 passed.
- Full backend tests from clean cwd: 176 passed.
- Frontend typecheck, build, and screenshot QA: passed.
- Package assembly with `-CreateZip`: passed.
- Zip-entry scan: dependency test segments `0`, cache/bytecode entries `0`, marker-heavy docs `0`, denylist matches `0`.
- Redaction scan: credential marker `0`, operational filename-family marker `0`, Windows path marker `0`, DB URL marker `0`, Authorization marker `0`, JWT marker `0`.
- Runtime `.py`, native files, dist-info metadata, `METADATA`, `RECORD`, and license/notice/copying material were preserved.
- Packaged import smoke returned `import_ok`.
- Launcher `-CheckOnly`, shortcut installer `-CheckOnly`, HTTP route smoke, no-token `PUT /api/config` returning `403`, and `/api/docs`, `/api/openapi.json`, `/api/redoc` returning `404` all passed.
- Python cache generated after package import or HTTP smoke is treated as post-runtime output and is distinct from clean zip contents.

Known future hardening: split redaction marker tests into marker-specific parametrized fixtures so each marker class has an independent assertion.

## Release Blocker Analysis

PR #36 release-candidate smoke found two blocker classes:

| Blocker | Evidence | Product runtime risk | Release readiness risk |
| --- | --- | --- | --- |
| Runtime `.venv` includes dependency-internal test path segments | extracted package count-only scan found 8 runtime test segment matches | Low, package still launched and HTTP smoke passed | Medium, package ships unnecessary test material and violates denylist intent |
| Packaged text includes marker-heavy strings | extracted package redaction scan found credential-marker policy strings and an operational CSV filename-family marker | Low, no live secret value was found | High, package policy says release artifacts should not carry marker-heavy strings or operational filename-family markers |

The second blocker is not the same as a live secret leak. The smoke found marker/policy/source text, not actual DB URLs, token values, JWT values, raw `.env` files, CSV files, or CSV contents. It is still a release blocker because operator packages should be stricter than source repositories.

## Current Package Pipeline

```text
repo allowlist
  -> Copy-ManifestFile / Copy-ManifestDirectory
  -> package folder under C:\tmp
  -> required path validation
  -> denylist path validation
  -> redaction text validation
  -> optional zip
  -> checksum
  -> extracted package smoke
```

What already exists:

| Existing piece | Reuse decision |
| --- | --- |
| manifest include allowlist | Reuse. Do not introduce repo-root recursive copy. |
| manifest denylist | Extend. It currently blocks repo tests, cache, raw env, logs, DB files, CSV files, frontend source, and generated artifacts. |
| runtime cache filter | Extend. It currently filters `__pycache__`, compiled Python bytecode, and optimized bytecode during copy. |
| redaction scan | Extend. It currently scans package text outside `.venv` for secret-like marker classes. |
| package output root guard | Reuse. Output must stay outside the repo. |
| zip/checksum metadata behavior | Reuse. The zip-internal metadata cannot know the final zip hash. |
| launcher and shortcut `-CheckOnly` smoke | Reuse. These prove extracted package viability. |

## Decision Summary

1. Prune `.venv` only for cache and test-only content.
2. Preserve dependency metadata needed for support, license review, import resolution, and package diagnostics.
3. Treat package docs as a release artifact, not a source-doc mirror.
4. Keep source docs free to describe redaction policy, but do not ship marker-heavy source docs in the operator package by default.
5. Add a small operator-safe package note if maintainers still need package-specific guidance inside the zip.
6. Expand release-candidate redaction scan to include credential marker text, operational filename-family markers, and Windows absolute path markers.
7. Do not suppress false positives silently. Every allowlisted false positive must be named by package-relative path and marker class in tests, not by raw sensitive value.

## `.venv` Prune Policy

Prune these runtime `.venv` path classes during package copy:

| Class | Decision | Rationale |
| --- | --- | --- |
| `__pycache__/` | Remove | Generated cache, not required for launch. |
| Python bytecode artifacts | Remove | Generated cache, can be recreated. |
| pytest/cache artifacts | Remove | Test runner cache, not operator runtime. |
| dependency test directories named `test`, `tests`, or `testing` | Remove by default | Not required for normal imports and caused the release smoke blocker. |
| dependency test data directories | Remove only when inside a test/tester namespace | Avoid deleting runtime package data that happens to use sample-like names. |
| top-level repo tests | Already excluded | Keep excluded. |
| package metadata directories | Preserve | Required for dependency diagnostics, version checks, support, and license review. |
| license, notice, copying, metadata, record, wheel metadata files | Preserve | Required for compliance and traceability. |
| entry-point scripts and runtime DLL/PYD/native files | Preserve | Required for launch and imports. |
| type marker and stub files | Preserve | Low size, harmless, useful for diagnostics. |

The implementation should add a distinct function for runtime package pruning, separate from source denylist validation. The current cache filter is too narrow but should remain the base.

### Import Safety Check

Pruning must not be accepted only because package assembly succeeds. The implementation branch must run import and launch checks from the packaged `.venv`:

```text
package .venv python
  -> import backend.app.main
  -> launcher -CheckOnly
  -> start package backend
  -> GET /api/health
  -> GET /
```

If an import fails after pruning, the policy is too broad. Restore the removed class or add a package-specific exception.

## Dependency Metadata Policy

Preserve these inside `.venv`:

- dependency metadata directories
- license and notice files
- wheel metadata and entry point metadata
- package resources loaded through importlib or package data APIs
- native runtime files

Do not preserve test directories just because they are inside dependency packages. Test content is not compliance metadata.

If a dependency uses a directory named `tests` as runtime package data, that dependency needs a named exception in the manifest or script tests. No broad exception.

## Packaged Text Redaction Policy

Source docs can keep detailed engineering policy. Operator packages should not ship every source doc verbatim.

Decision:

- Keep marker-heavy source docs in the repository.
- Exclude marker-heavy source docs from the operator package docs subset when they are not needed by the operator.
- Add or generate an operator-safe package note if package-local guidance is needed.
- Keep `README.md` only if it can pass release-candidate redaction scan after replacing marker-heavy examples with placeholder-free prose.

Recommended package docs subset:

| Package doc | Decision |
| --- | --- |
| operator launcher usage | Include only if marker-safe. |
| shortcut usage | Include only if marker-safe. |
| package manifest summary | Replace with package-safe note or omit if marker-heavy. |
| release smoke reports | Exclude from operator package by default. They are QA artifacts, not operator runtime docs. |
| local token engineering plan | Exclude from operator package by default unless sanitized. |
| raw engineering plans with marker examples | Exclude. |

This avoids a circular failure where the package includes engineering docs that intentionally describe redaction markers, then the package redaction scan flags those same markers.

## Marker String Handling

The implementation should define marker classes by names and tests, not by documenting raw sensitive examples in operator-facing package files.

Required release-candidate marker classes:

| Marker class | Action in package |
| --- | --- |
| actual secret value | Block |
| DB connection marker | Block |
| local or external token marker | Block |
| auth-header credential marker | Block |
| service credential marker | Block |
| anonymous auth key assignment marker | Block |
| JWT-like marker | Block |
| operational CSV filename-family marker | Block |
| timestamp-style CSV filename marker | Block |
| Windows absolute path marker | Block unless it is a known safe package path in generated metadata |

Source code may contain regexes that detect these classes. If the assembly script itself is included in the package, it can trigger marker scans. Therefore either:

1. do not include packaging scripts in operator package, or
2. exclude scanner implementation files from the package text redaction scan only when they are not operator-executable and are included solely for maintainer diagnostics.

Recommendation: do not include `packaging/` in the operator package. Keep assembly tools in source, not in release output.

## False Positive Policy

False positives are allowed only when all are true:

1. The match is not a live secret or operational data.
2. The package-relative file is required for runtime or compliance.
3. The false-positive class is documented in a test fixture or allowlist.
4. The scan output remains count-only or class-only in normal command output.

Do not allow false positives in operator docs by default. Rewrite or exclude the doc.

Do not suppress a whole marker class globally because one file has a harmless match.

## Manifest Changes Needed

Next implementation branch should update `packaging/operator-package.manifest.json`:

- Add `.venv` prune classes for runtime test directories and pytest/cache artifacts.
- Add an explicit `preserveMetadata` policy for dependency metadata and license/notice files.
- Replace selected docs with a smaller package-safe docs subset.
- Add redaction check names for credential marker, operational filename-family marker, and Windows path marker.
- Add smoke check names for packaged import, extracted package redaction, and no repo-external generated artifacts in git.

No raw secret values, DB URLs, tokens, operational CSV paths, or operational CSV contents should appear in the manifest.

## Assembly Script Changes Needed

Next implementation branch should update `packaging/assemble_operator_package.ps1`:

1. Split runtime copy filtering into:
   - source denylist validation
   - `.venv` runtime prune filtering
   - package text redaction validation
2. Add `.venv` test segment pruning with metadata preservation.
3. Make the prune result observable through counts:
   - pruned runtime cache count
   - pruned runtime test segment count
   - preserved metadata count, optional
4. Update redaction patterns to cover the release-candidate marker classes.
5. Keep output presence/count oriented.
6. Keep `OutputRoot` outside repo.
7. Keep no-delete repeated assembly behavior.
8. Keep `-AllowIncompleteRuntime` as a maintainer escape hatch, not an operator-ready path.

The script must not delete existing package outputs, AppData config/state/logs, local Supabase data, Docker resources, or operational CSV data.

## Validation And Smoke Plan

Implementation validation must prove both packaging hygiene and runtime viability.

Required checks:

| Check | Evidence |
| --- | --- |
| targeted packaging tests | updated tests pass |
| package assembly with `.venv` present | succeeds |
| zip and checksum | generated and hash matches |
| extracted package denylist scan | zero repo tests, zero dependency test segments, zero caches, zero raw env, zero CSV files |
| extracted package redaction scan | zero marker-class matches except documented required exceptions |
| package import smoke | packaged Python imports backend app |
| launcher `-CheckOnly` | passes from extracted package |
| shortcut installer `-CheckOnly` | passes from extracted package |
| HTTP smoke | `/`, `/upload`, `/logs`, `/settings`, `/api/health`, `/api/config`, `/api/audit?limit=1` return expected statuses |
| token smoke | read-only no-token succeeds, mutating no-token returns `403` |
| docs hardening | operator docs routes return `404` |
| repeated assembly | new label does not delete existing output |
| git hygiene | `.gstack`, `frontend/dist`, package output, zip, checksum, and operational CSV fixture remain uncommitted |

Do not require real local Supabase runtime for this package policy branch. The target is package viability and release hygiene.

## Failure Modes

| Failure mode | Test coverage needed | Error handling expected | Operator impact |
| --- | --- | --- | --- |
| prune removes runtime package data | package import smoke and HTTP smoke fail | assembly test should fail before release acceptance | launch failure if missed |
| prune removes dependency metadata needed for diagnostics | metadata preservation test fails | package remains buildable but support quality drops | maintainer loses traceability |
| docs subset omits essential operator launch guidance | package docs smoke or README review catches gap | launcher still prints runtime guidance | operator may need maintainer help |
| redaction scan blocks scanner source text | package docs subset and scanner exception tests catch it | script reports marker class and file class, not raw value | release assembly blocked |
| false positive allowlist becomes too broad | tests must assert path-specific exception only | script still blocks other files | sensitive marker could slip if broad |
| repeated assembly overwrites prior release candidate | existing no-delete test remains | script throws on duplicate label | previous RC remains safe |

No critical silent failure is acceptable. If package startup fails after pruning, launcher output and logs must stay redacted and operator-readable.

## Implementation Order

1. Update manifest schema fields for runtime prune and docs subset.
2. Add tests that reproduce PR #36 blockers against a controlled package tree.
3. Implement `.venv` prune filtering with metadata preservation.
4. Replace package docs subset with operator-safe docs or generated package note.
5. Expand redaction scan classes and path-specific false-positive handling.
6. Run targeted packaging tests.
7. Build frontend and assemble package with `-CreateZip`.
8. Extract zip and run package import, launcher, shortcut, HTTP, token, docs, and redaction smoke.
9. Record implementation QA in a follow-up report or document-release update.

## Worktree Parallelization

| Step | Modules touched | Depends on |
| --- | --- | --- |
| Manifest schema and docs subset | `packaging/`, `docs/`, root docs | none |
| Runtime prune implementation | `packaging/` | manifest schema |
| Package tests | `tests/backend/` | manifest schema and prune implementation |
| Release smoke report | `docs/` | implementation and smoke |

Parallel lanes:

- Lane A: manifest/docs subset policy implementation in `packaging/` and docs.
- Lane B: tests in `tests/backend/`, after Lane A defines the final manifest contract.
- Lane C: script implementation in `packaging/`, after Lane A.
- Lane D: release smoke report in `docs/`, after B and C.

Execution order: A first, then B + C in coordinated worktrees if desired, then D.

Conflict flags: Lane A and C both touch `packaging/`, so keep those sequential unless the branch owner coordinates exact files.

## NOT In Scope

- Changing backend API behavior.
- Changing frontend behavior.
- Changing launcher local token enforcement.
- Changing local Supabase runtime command policy.
- Running DB reset/delete/cleanup/prune.
- Running Docker volume/container delete or prune.
- Deleting AppData config/state/logs.
- Packaging raw `.env` files.
- Packaging operational CSV fixtures, samples, paths, or contents.
- Implementing MSI, installer, Windows service, tray app, code signing, or auto-update.
- Deleting existing package output, zip, checksum, `.gstack`, or `frontend/dist`.

## Engineering Review Summary

Scope challenge: accepted as-is. The safer sequence is policy first, implementation second.

Architecture review: 2 issues addressed by policy, runtime prune boundaries and marker-heavy docs inclusion.

Code quality review: 1 issue addressed by policy, separate source denylist, runtime prune, and redaction scan responsibilities.

Test review: validation plan requires package import, extracted package smoke, count-only scans, and repeated assembly.

Performance review: package size should improve by pruning test/cache runtime content; runtime performance should be unchanged.

Failure modes: 6 listed, 0 accepted as silent.

Parallelization: 4 lanes, with `packaging/` conflict between manifest and script work.

Lake Score: 9/10. The plan chooses a complete release policy without over-pruning runtime dependencies.
