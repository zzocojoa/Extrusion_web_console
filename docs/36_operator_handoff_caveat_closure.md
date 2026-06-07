# Operator Handoff Caveat Closure Smoke

Date: 2026-06-07

Branch: `codex/operator-handoff-caveat-closure`

Base commit: `416ad9b2e6f8fb7295858c6fc3570e61622b2d5e`

Scope: report-only smoke for closing the default-launcher caveat recorded in `docs/35_operator_handoff_acceptance.md`.

This report does not change product code, launcher behavior, backend behavior, frontend behavior, package assembly, GitHub Release assets, tags, local runtime policy, AppData state, Docker state, database state, shortcut state, or operational data.

## Summary

Caveat closure is blocked.

The default launcher smoke was attempted with the released operator package on the default launcher port. The environment was not clean: the default port was already serving a dev-mode backend without the local token bootstrap page. The packaged launcher correctly refused to reuse that backend.

Because the clean-port precondition was not met, the caveat cannot be closed in this run. The acceptance verdict remains `accepted with caveats`.

## Target Release

| Item | Result |
| --- | --- |
| Release URL | `https://github.com/zzocojoa/Extrusion_web_console/releases/tag/operator-package-v0.1.0.0` |
| Tag | `operator-package-v0.1.0.0` |
| Package label | `ewc-final-release-smoke-20260607-rc1` |
| Package runtime label | `operator-package-folder` |

## Closure Preconditions

| Precondition | Result |
| --- | --- |
| Use released operator package | passed |
| Use default shortcut/launcher path | attempted |
| Default launcher port is free | failed |
| No GitHub Release/tag mutation | passed |
| No production deploy | passed |
| No feature code changes | passed |

## Smoke Result

| Check | Result | Notes |
| --- | --- | --- |
| Default launcher start | blocked | Existing healthy backend was detected on the default port |
| Token bootstrap on default port | failed | Existing backend did not expose the operator local token bootstrap page |
| Launcher safety behavior | passed | Launcher refused to reuse the non-bootstrap backend |
| `/` on default port | not accepted | Existing service responded, but it was not accepted as packaged operator runtime |
| `/upload` | not run | Closure stopped after default-port precondition failed |
| `/logs` | not run | Closure stopped after default-port precondition failed |
| `/settings` | not run | Closure stopped after default-port precondition failed |
| Read-only API smoke | not accepted | Existing dev-mode backend was not accepted as packaged runtime evidence |
| Mutating no-token `403` | not run | Closure stopped after default-port precondition failed |
| API docs hardening `404` | not run | Closure stopped after default-port precondition failed |

## Observed Launcher Behavior

The launcher reported that an existing backend was healthy but did not expose the local token bootstrap page, then exited instead of reusing it.

This is the expected safety behavior. It prevents a dev-mode backend from being mistaken for the packaged operator runtime.

## Findings

### Blocker

The default launcher port was still occupied by a dev-mode backend during the caveat closure attempt.

### Non-blocking

No package defect was found in this closure attempt. The run stopped because the environment did not satisfy the clean default-port requirement.

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
- launcher log file paths

## Closure Verdict

`blocked`

Reason: the default launcher port was not clean. The packaged launcher correctly rejected the existing dev-mode backend, so the caveat remains open.

## Next Step

Close the pre-existing default-port backend, then rerun the default shortcut/launcher smoke. If the released package runtime starts on the default port and `/`, `/upload`, `/logs`, `/settings`, read-only APIs, mutating no-token `403`, and API docs hardening `404` all pass, update this report or add a follow-up report with closure verdict `accepted`.
