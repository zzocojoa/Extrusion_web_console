# Operator Package Dependency Agents Prune Policy

Status: implemented on branch `codex/operator-package-runtime-agents-prune-impl`

Date: 2026-06-08

Scope: document-only engineering policy for dependency-provided `.agents` entries found in API-mode operator package release-candidate smoke.

This implementation changes package manifest, assembly script, packaging tests, and documentation only. It does not change product API behavior, launcher behavior, backend runtime behavior, frontend runtime behavior, local Supabase data, Docker data, AppData state, package outputs, release tags, or GitHub Release assets.

Implementation result:

- `packaging/operator-package.manifest.json` now lists `.agents` as a runtime `.venv` exclude class and records the package/zip `.agents` count `0` smoke contract.
- `packaging/assemble_operator_package.ps1` now prunes `.agents` paths under `.venv`, reports a count-only `runtime agent entries pruned` metric, and keeps root/source `.agents` denylist validation unchanged.
- `tests/backend/test_operator_package_assembly.py` now creates a synthetic dependency `.agents` fixture, asserts package output contains no `.agents` entries, and asserts zip output contains no `.agents` entries.
- Dependency metadata, license, notice, copying, native/runtime files, and runtime `.py` preservation policy remains unchanged.

## Goal

Resolve the API-mode release-candidate blocker from `docs/39_operator_api_mode_release_candidate_smoke.md`: dependency-provided `.agents` entries appeared inside the packaged Python runtime zip.

The package must stay operator-focused:

- no developer-agent material in package root or source tree
- no dependency-internal agent skill docs in packaged runtime
- no raw secret, DB URL, token, Authorization header, JWT, operational CSV path, operational CSV filename, CSV content, or full local path in package docs or validation output
- runtime imports and launcher/API smoke must still pass after pruning

## Decision Summary

Decision: prune dependency-provided `.agents` runtime entries.

Do not allowlist them for release packages.

Keep zip-entry expected count for `.agents` at `0` for both mock-mode and API-mode packages.

Rationale:

- `.agents` directories are developer-agent skill/documentation content, not Python import metadata.
- They are not dependency metadata such as dist-info, `METADATA`, `RECORD`, license, notice, copying, wheel metadata, native files, runtime `.py`, package data, or entry points.
- PR #49 evidence says the package still had `0` cache/bytecode entries, `0` runtime test segment entries, and no secret marker matches, but `.agents` remained as a denylist-class zip entry blocker.
- Allowlisting them would weaken the existing package root/source tree `.agents` prohibition and make package validation harder to explain.

## What Already Exists

| Existing mechanism | Reuse decision |
| --- | --- |
| Manifest allowlist-only copy | Reuse. Do not introduce recursive repo copy. |
| Package root/source tree `.agents` denylist | Keep. This remains a hard package rule. |
| `.venv` cache/test prune | Extend. Add dependency-internal `.agents` as a runtime prune class. |
| Metadata/license preservation | Keep. `.agents` is not metadata/license/native/runtime material by default. |
| Redaction scan | Keep. No new raw marker examples are needed. |
| Zip-entry scan | Strengthen. Assert `.agents` count remains `0`. |
| Packaged import smoke | Keep mandatory. This proves pruning did not break runtime imports. |
| API-mode metadata validation | Keep mandatory for API-mode release packages. |

## Package Pipeline

```text
repo allowlist
  -> runtime copy filter
       -> prune cache/test/.agents runtime-only content
       -> preserve metadata/license/native/runtime content
  -> package folder validation
       -> required paths
       -> denylist path scan
       -> redaction marker scan
  -> optional zip
  -> zip-entry denylist scan
  -> extracted package import + launcher/API smoke
```

The `.agents` decision belongs in the runtime copy filter and the zip-entry denylist scan. It is not a redaction exception.

## Runtime Need Criteria

A dependency-internal path may be preserved only when at least one criterion is true:

| Criterion | Evidence required |
| --- | --- |
| Import-time code | Packaged import or HTTP smoke fails without the file, and the path is referenced by import/runtime code. |
| Package data | The package loads it through runtime resource APIs and tests prove the read path. |
| Native/runtime binary | File is required for extension module load or subprocess/runtime execution. |
| Dependency metadata | Path is dist-info metadata, `METADATA`, `RECORD`, `WHEEL`, entry point metadata, or version/support metadata. |
| License/compliance | Path is license, notice, copying, or equivalent compliance material. |

`.agents` entries do not meet these criteria by default.

If a future dependency truly requires an `.agents` path at runtime, it must get a package-relative, dependency-specific exception with:

1. an import or HTTP smoke failure proving need
2. a narrow manifest/script exception
3. a test that fails if the exception expands beyond that dependency/path
4. a redaction scan proving no sensitive marker classes are introduced

No broad `.agents` allowlist.

## Prune Versus Allowlist

| Option | Decision | Reason |
| --- | --- | --- |
| Prune all dependency-internal `.agents` entries | Chosen | Matches operator package purpose and keeps zip-entry count `0`. |
| Allowlist dependency-provided `.agents` entries | Rejected | Treats developer-agent content as runtime material without proof. |
| Ignore `.agents` only in zip scan | Rejected | Hides the package hygiene issue instead of fixing package contents. |
| Convert to redaction-only check | Rejected | The blocker is unwanted runtime package content, not only sensitive text. |

## Metadata And License Compatibility

Pruning `.agents` must not weaken the existing preservation policy:

- preserve runtime `.py`
- preserve native/runtime files
- preserve package data proven to be loaded at runtime
- preserve dist-info metadata
- preserve `METADATA`, `RECORD`, `WHEEL`, and entry point metadata
- preserve `LICENSE`, `NOTICE`, `COPYING`, and equivalent compliance files

`.agents` is outside this preservation set unless a dependency-specific exception proves otherwise.

## Manifest And Script Change Scope

Future implementation branch should update only packaging implementation and tests.

Expected manifest updates:

- add a runtime prune class for dependency-internal `.agents`
- keep root/source `.agents` in `excludeDenylist`
- keep `preserveMetadata` unchanged for metadata/license/native/runtime files
- add a smoke or validation name for `zip agents entries count is 0`

Expected script updates:

- update runtime prune classification to remove any `.agents` path under `.venv`
- make prune counts observable, for example `runtime agent entries pruned`
- keep normal output count-oriented and redacted
- keep `OutputRoot` outside the repo
- keep no-delete repeated assembly behavior
- do not change launcher, backend, frontend, local token, API docs, or Supabase policies

Expected test updates:

- create a synthetic dependency `.agents` runtime fixture inside the packaging test tree
- assert assembly succeeds and the package output has no `.agents` entries
- assert zip output has no `.agents` entries
- assert metadata/license/native/runtime files are still preserved
- assert package import smoke remains required for release validation

## Scan Policy

Redaction scan:

- keep current marker classes
- do not add raw sensitive examples to docs
- do not treat `.agents` as a redaction allowlist

Denylist and zip-entry scan:

- package root/source tree `.agents`: expected count `0`
- dependency-internal `.agents`: expected count `0`
- API-mode package zip `.agents`: expected count `0`
- mock/default package zip `.agents`: expected count `0`

Validation should report counts and package-relative path classes only. It must not print full local paths or raw sensitive values.

## Mock And API Mode Coverage

Apply the same `.agents` runtime prune policy to both package modes.

| Package mode | Policy |
| --- | --- |
| Mock/default | prune `.agents`, expect zip count `0` |
| API-mode | prune `.agents`, expect zip count `0` |

Reason: `.agents` content is unrelated to frontend mode. The same package runtime hygiene rule should apply to both modes.

API-mode release packages still require `npm run build:api` and assembly with explicit API frontend mode. Mock/default packages keep the existing backward-compatible path.

## Required Smoke After Implementation

The implementation branch must run:

| Check | Required result |
| --- | --- |
| targeted packaging tests | pass |
| mock/default package assembly | pass |
| API-mode package assembly | pass |
| zip/checksum verification | pass |
| package output `.agents` count | `0` |
| zip-entry `.agents` count | `0` |
| runtime test/cache count | `0` |
| metadata/license preservation check | pass |
| packaged import smoke | pass |
| launcher `-CheckOnly` | pass |
| shortcut installer `-CheckOnly` | pass |
| HTTP smoke | `/`, `/upload`, `/logs`, `/settings`, `/api/health`, `/api/config`, `/api/audit?limit=1` |
| token smoke | read-only no-token succeeds, mutating no-token returns `403` |
| operator docs hardening | docs routes return `404` |
| git hygiene | generated package outputs, zip, checksum, `.gstack`, `frontend/dist`, and operational CSV fixture remain uncommitted |

Real local Supabase readiness is not required to prove `.agents` pruning. It is required for the later API-mode RC smoke rerun if that rerun attempts Upload Preview.

## API-Mode RC Rerun Criteria

Rerun API-mode release-candidate smoke only after the implementation branch proves:

1. API-mode build metadata is present and records `frontendMode=api`.
2. Assembly with explicit API frontend mode passes.
3. Package folder and zip contain no `.agents` entries.
4. Packaged import, launcher, HTTP, token, and docs hardening smoke pass.
5. Redaction scan remains clean.
6. Local Supabase/Docker readiness is available if Upload Preview is in scope.

If local Supabase/Docker is still unavailable, the rerun may pass package hygiene but must keep Upload Preview blocked by runtime readiness.

## Failure Modes

| Failure mode | Test coverage needed | Expected handling | Operator impact |
| --- | --- | --- | --- |
| prune removes a runtime-required file | packaged import and HTTP smoke fail | release blocked before handoff | operator never receives broken package |
| prune removes dependency metadata | metadata preservation test fails | assembly/test failure | support traceability preserved |
| `.agents` remains in zip | zip-entry count test fails | release blocked | package hygiene blocker remains visible |
| `.agents` allowlist becomes broad | test must prove only named exception is allowed | release blocked unless exception is narrow | prevents accidental developer-agent content shipping |
| redaction scan prints sensitive context | marker scan/test fails | output stays class/count oriented | no secret/path exposure |
| API-mode rerun starts Preview without runtime readiness | QA process violation | stop condition blocks Preview | no unsafe upload action |

No silent failure is acceptable for package content validation.

## Rollback Path

If `.agents` pruning breaks runtime imports or package HTTP smoke:

1. stop release acceptance
2. restore the prior packaging script and manifest behavior
3. keep PR #49 blocker open in the release report
4. identify the exact dependency and path that needs `.agents`
5. add a dependency-specific exception only if runtime need is proven
6. rerun package import, HTTP, token, docs hardening, redaction, and zip-entry smoke

Rollback must not delete AppData config/state/logs, package outputs, local Supabase data, Docker data, operational CSV data, `.gstack`, or `frontend/dist`.

## NOT In Scope

- Implementing the prune in this document-only PR.
- Changing backend API behavior.
- Changing frontend behavior.
- Changing launcher local token enforcement.
- Changing packaging script behavior in this PR.
- Changing local Supabase runtime command policy.
- Running DB reset/delete/cleanup/prune.
- Running Docker volume/container delete or prune.
- Creating or modifying GitHub Release/tag assets.
- Packaging raw environment files.
- Packaging operational CSV fixtures, samples, paths, filenames, or contents.
- Deleting generated package outputs, zip, checksum, `.gstack`, `frontend/dist`, or untracked operational CSV fixtures.

## Implementation Order

1. Land this document-only policy.
2. Add packaging tests that reproduce dependency-internal `.agents` under `.venv`.
3. Update manifest policy fields for runtime `.agents` prune and zip expected count.
4. Update assembly script runtime prune classification.
5. Run targeted packaging tests.
6. Build mock/default and API-mode frontend artifacts as needed for package assembly smoke.
7. Assemble packages and zip outputs outside the repo.
8. Verify package and zip `.agents` count is `0`.
9. Run packaged import, launcher, shortcut, HTTP, token, docs hardening, redaction, and git hygiene checks.
10. Record implementation QA.
11. Rerun API-mode RC smoke when package hygiene passes and runtime readiness is available for Preview scope.

## Worktree Parallelization

Sequential implementation, no parallelization opportunity.

The implementation touches the same primary module set: `packaging/` and `tests/backend/`. Running it in one branch avoids manifest/script/test contract drift.

## Engineering Review Summary

Scope challenge: accepted as-is. Policy first is the right move because PR #49 found a package release blocker, not product behavior failure.

Architecture review: 1 issue addressed, dependency `.agents` must be runtime-pruned rather than allowlisted.

Code quality review: 1 issue addressed, `.agents` should be a named prune class with explicit tests rather than an ad hoc denylist scan exception.

Test review: implementation must add fixture coverage for dependency-internal `.agents`, zip-entry count `0`, metadata preservation, and packaged import smoke.

Performance review: no runtime performance impact expected; package size should shrink slightly.

Failure modes: 6 listed, 0 accepted as silent.

NOT in scope: written.

What already exists: written.

Parallelization: sequential.

Decision: prune dependency-provided `.agents` entries and keep expected package/zip count at `0`.
