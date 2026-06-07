# Operator Handoff Caveat Closure Smoke

Date: 2026-06-07

Branch: `codex/operator-handoff-caveat-closure`

Base commit: `416ad9b2e6f8fb7295858c6fc3570e61622b2d5e`

Scope: report-only smoke for closing the default-launcher caveat recorded in `docs/35_operator_handoff_acceptance.md`.

This report does not change product code, launcher behavior, backend behavior, frontend behavior, package assembly, GitHub Release assets, tags, local runtime policy, AppData state, Docker state, database state, shortcut state, or operational data.

## Summary

Caveat closure is accepted.

The default launcher smoke was attempted with the released operator package on the default launcher port. The first attempt confirmed the previous caveat: the default port was still serving a dev-mode backend without the local token bootstrap page, and the packaged launcher correctly refused to reuse it.

After that stale dev-mode backend was closed, the same released package runtime started on the default launcher port and passed the UI route, read-only API, no-token mutating API guard, and operator API docs hardening checks.

The acceptance caveat recorded in `docs/35_operator_handoff_acceptance.md` is closed for a clean default-port environment. The package acceptance status is `accepted`.

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
| Use default shortcut/launcher path | passed |
| Default launcher port is free | passed after stale dev-mode backend was closed |
| No GitHub Release/tag mutation | passed |
| No production deploy | passed |
| No feature code changes | passed |

## Smoke Result

| Check | Result | Notes |
| --- | --- | --- |
| Default launcher start | passed | Released package runtime started on the default launcher port after the stale dev-mode backend was closed |
| Token bootstrap on default port | passed | Packaged operator runtime exposed the local token bootstrap page; token value was not recorded |
| Launcher safety behavior | passed | Initial non-bootstrap dev backend was rejected before the clean-port rerun |
| `/` on default port | `200` | Packaged operator runtime served the app shell |
| `/upload` | `200` | Upload route served successfully |
| `/logs` | `200` | Logs route served successfully |
| `/settings` | `200` | Settings route served successfully |
| Read-only API smoke | `200` | `/api/health`, `/api/config`, and `/api/audit?limit=1` succeeded |
| Mutating no-token `403` | `403` | No-token `PUT /api/config` was blocked |
| API docs hardening `404` | `404` | `/api/docs`, `/api/openapi.json`, and `/api/redoc` were disabled |

## Observed Launcher Behavior

The first launcher attempt reported that an existing backend was healthy but did not expose the local token bootstrap page, then exited instead of reusing it.

This is the expected safety behavior. It prevents a dev-mode backend from being mistaken for the packaged operator runtime.

After the stale dev-mode backend was closed, the released package launcher started the packaged runtime on the default port. The smoke used only sanitized pass/fail and HTTP status evidence.

## Findings

### Resolved caveat

The default launcher port caveat is closed for a clean-port environment.

### Non-blocking

No package defect was found. The initial dev-mode port conflict was environmental and the packaged runtime passed after the default port was freed.

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

`accepted`

Reason: the released package runtime passed default-port UI route, read-only API, local token guard, and API docs hardening smoke after the stale dev-mode backend was closed. The earlier launcher refusal remains valid safety behavior and no longer blocks acceptance in a clean-port environment.

## Next Step

Proceed with operator handoff using the released package and handoff runbook. Before routine launch, verify that the default launcher port is free or close any stale dev-mode backend first.
