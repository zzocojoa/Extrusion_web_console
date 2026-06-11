# Operator Final Runtime Smoke

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-final-runtime-smoke`
- Base commit: `549b352f86bf3d32926560d196ebda46fda40015`
- QA mode: report-only, no code changes
- Verdict: `ready_with_caveats`

This smoke confirms that the current operator package runtime target is usable
for the next planning step before any full operational dataset rollout. Core
runtime checks were read-only. Upload Preview, Start Upload, duplicate rerun,
and Edge authenticated upload calls were not executed.

## Scope

This QA run checked only runtime availability and target-class consistency:

- Docker/local Supabase current state;
- package launcher `-CheckOnly` behavior;
- package-like backend API smoke for `/api/health`, `/api/config`, and
  `/api/runtime/local-supabase`;
- direct no-auth Edge route class;
- DB and Edge target class alignment;
- vector and Grafana caveat state.

## Explicitly Not Performed

- Supabase init, bootstrap, reset, start, or stop;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Upload Preview;
- Start Upload;
- duplicate rerun;
- Edge authenticated upload call;
- Authorization header or token use;
- production deploy;
- GitHub Release or tag creation.

## Runtime Smoke Results

| Area | Result | Notes |
| --- | --- | --- |
| Supabase status | `ok` | Checked as sanitized availability state only. Raw status output was not recorded. |
| Independent API port | `reachable` | Port class matches the independent stack. |
| Independent DB port | `reachable` | Port class matches the independent stack. |
| Independent Studio port | `reachable` | Port class matches the independent stack. |
| Grafana port | `unreachable` | Existing non-core caveat remains. |
| Edge no-auth `GET` | `401` auth-class | Rechecked with no Authorization header. |
| Edge no-auth `POST {}` | `401` auth-class | Rechecked with no Authorization header and safe empty object body. |
| Package launcher `-CheckOnly` | `passed` | Completed without starting a backend process. Raw values were hidden. |
| Package-like backend `/api/health` | `ok` | Temporary API smoke process was stopped after checks. |
| Package-like backend `/api/config` | `passed` | DB URL, Edge URL, and anon key remained hidden/secret fields. |
| Package-like backend `/api/runtime/local-supabase` | `attention` | Core API, DB, Studio, and Edge were ready; non-core caveats remained. |

The final Edge status class is based on no-auth requests only. No
authenticated Edge upload call was made.

## Target Class Alignment

| Target | Class | Evidence |
| --- | --- | --- |
| Project id | `independent` | Runtime API reported the independent project class. |
| API target | `independent` | Config and runtime ports matched the independent stack. |
| DB reconciliation target | `independent` | Config DB port class matched the independent stack; raw DB URL stayed hidden. |
| Edge upload target | `independent` | Config Edge target stayed hidden and matched the independent API/Edge port class. |
| Legacy stack | `not active for core path` | Only stopped legacy vector class was observed in sanitized Docker state. |

## Caveats

| Caveat | Current state | Impact |
| --- | --- | --- |
| Vector | `restarting` in Docker summary and `stopped` in runtime API class | Still a runtime caveat. It did not block API, DB, Studio, or Edge readiness in this smoke. |
| Grafana | `unreachable` | Non-core operator visibility caveat. Grafana remains status/link-only for this scope. |
| Full operational dataset | Not run | Full dataset rollout still requires a separate plan, approval, and staged execution. |
| PowerShell GET probe | One client-side inconclusive result before curl recheck | Final status used direct no-auth curl class: `401`. |

## Redaction Result

- Raw secret values were not recorded.
- Raw DB URL was not recorded.
- Token, Authorization header, and JWT values were not used or recorded.
- Operational CSV path, content, filename, and full local path were not recorded.
- Raw Supabase status output was not recorded.
- Package launcher output was reduced to pass/fail and hidden-value markers.

## Go/No-Go Assessment

Full operational dataset rollout execution is not approved by this smoke.

The next step can proceed to a dedicated rollout plan because:

- independent API, DB, Studio, and Edge were reachable/ready;
- Edge no-auth `GET` and `POST {}` returned auth-class instead of `503`;
- package launcher `-CheckOnly` passed without exposing raw values;
- DB and Edge target classes remained aligned to the independent stack.

Verdict: proceed to `codex/operator-full-dataset-rollout-plan` with caveats.

## Next Sequence

1. Create the full operational dataset rollout plan.
2. Review rollback, sampling, audit, and operator stop conditions.
3. Run a small operational sample rollout under separate approval.
4. Stage the full operational dataset rollout only after the sample evidence is accepted.
