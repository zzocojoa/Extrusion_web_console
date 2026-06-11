# Operator Runtime Stability Hardening

## Summary

- Date: 2026-06-11
- Branch: `codex/operator-runtime-stability-hardening`
- Base commit: `4d69d08c619b3a0c1442b49d6b7b9c446aed7cb7`
- Scope: investigation and hardening guidance for maintainer-approved local Supabase stop/start stability
- Verdict: `hardened_with_caveats`

This investigation reproduced the previously observed `supabase start`
instability without destructive recovery. The strongest confirmed cause is stale
or restarting `vector` container state after `supabase stop`, which can make a
following `supabase start` fail with a container-name conflict class before a
later retry succeeds.

No code, launcher, backend, frontend, packaging script, DB schema, Docker
deletion, DB migration, Upload Preview, Start Upload, duplicate rerun, or Edge
authenticated upload was changed or run.

## Guardrails

Allowed actions performed:

- Docker current-state inspection;
- sanitized `supabase status` inspection;
- repo-owned Supabase `supabase stop`;
- repo-owned Supabase `supabase start`;
- container state inspection for the independent and legacy stack classes;
- direct no-auth Edge route probes;
- operator launcher `-CheckOnly`;
- temporary loopback backend read-only smoke for `/api/health`, `/api/config`,
  and `/api/runtime/local-supabase`;
- sanitized log class inspection for Edge and vector.

Explicitly not performed:

- Supabase init, bootstrap, or reset;
- `supabase stop --no-backup`;
- DB migration, reset, delete, cleanup, prune, drop, or truncate;
- Docker volume, container, image, or network deletion;
- Upload Preview;
- Start Upload;
- duplicate rerun;
- Edge authenticated upload call;
- raw credential, token, DB URL, generated key, or operational source evidence
  capture;
- production deploy, GitHub Release, or tag operation;
- feature branch deletion.

## Confirmed Facts

### Initial State

| Check | Result |
| --- | --- |
| Docker Desktop | ready |
| Independent API port | reachable |
| Independent DB port | reachable |
| Independent Studio port | reachable |
| Independent Edge runtime container | running |
| Independent vector container | restarting |
| Legacy stack | stopped class only observed |
| Sanitized `supabase status` | exit `0`, raw credential-like output suppressed |

The independent core runtime was usable before the stop/start cycle, but vector
was already not stable.

### Stop/Start Reproduction

| Step | Result |
| --- | --- |
| `supabase stop` | exit `0` |
| After stop API/DB/Studio ports | closed |
| After stop independent vector | still `restarting` |
| First `supabase start` | exit `1`, `vector` container-name conflict class |
| After waiting | vector became `exited` |
| Second `supabase start` | exit `1`, same conflict class; vector entry disappeared afterward |
| Third `supabase start` | exit `0`, raw credential-like output suppressed |
| After final start API/DB/Studio ports | reachable |
| After final start Edge no-auth `GET` and `POST {}` | `401` auth-class |
| After final start vector | restarting/stopped class caveat remained |

This reproduces the same pattern from the earlier operator package recovery:
`supabase start` can fail while Docker is still resolving stale vector state,
then succeed later without Docker delete, DB reset, prune, or cleanup.

### Sanitized Log Classes

| Source | Sanitized class |
| --- | --- |
| Vector logs | `config_marker`, `error_marker`, `vector_marker` |
| Edge logs | `error_marker`; credential-like raw output suppressed |

Raw logs were not copied into this report.

### Launcher And API Visibility

| Check | Result |
| --- | --- |
| Operator launcher `-CheckOnly` | passed |
| `-CheckOnly` backend start | not started |
| `-CheckOnly` target defaults | package-local independent target defaults prepared; raw values hidden |
| Temporary read-only `/api/health` smoke | ok |
| Temporary read-only `/api/config` smoke | independent project and port classes |
| Temporary read-only `/api/runtime/local-supabase` smoke | API/DB/Studio ready, overall `attention` |
| Runtime API caveats | Grafana unreachable, vector stopped/restarting, Edge probe discrepancy under repo dev environment |

The temporary repo-dev backend smoke is not treated as the operator package
source of truth because repo-local environment files can change the runtime
target class. The operator package launcher path remains the acceptance path for
package handoff.

## Suspected Root Causes

| Candidate | Result | Evidence |
| --- | --- | --- |
| `vector` stale or restarting container state | confirmed strongest cause | `supabase stop` left vector restarting; following starts failed with vector container-name conflict class; later retry succeeded after stale entry changed state. |
| Edge runtime stopped/exited | not reproduced as start failure cause | Edge container was running after final start, and direct no-auth route returned auth-class. |
| Grafana unreachable | confirmed caveat, not start blocker | Runtime attention remains, but Grafana is link/status-only and not part of local Supabase start. |
| Port conflict | not reproduced | API/DB/Studio ports closed after stop and reopened after final successful start. |
| Legacy stack conflict | not reproduced | Only stopped legacy vector class was observed. |
| Docker resource pressure | unproven | Docker was reachable; logs showed vector/error classes but no safe evidence proving resource exhaustion. |
| `supabase/config.toml` mismatch | not reproduced | Independent config exists and ports match the documented package target. |
| Repo dev environment target mismatch | observed caveat | Repo-local environment key presence can make repo-dev backend smoke differ from package launcher behavior. |

## Hardening Decision

No feature code change was made in this PR.

Reasoning:

1. The reproduced failure is in the maintainer CLI `supabase start` path, not the
   normal operator launcher path.
2. The normal operator package does not bootstrap, reset, migrate, or start
   Supabase by itself.
3. The app runtime control policy remains non-destructive and already blocks
   missing-container bootstrap/create behavior.
4. The safest immediate hardening is an operator/maintainer runbook rule: treat
   vector stale state as a wait-and-retry condition, never as approval for Docker
   delete, DB reset, or prune.

Future code hardening may be useful if runtime API start/stop is expanded beyond
its current non-destructive policy. If that happens, add explicit stale-container
classification and operator-facing guidance before invoking any start command.

## Operator-Visible Response Rules

Use these rules when `supabase start` fails during maintainer-approved package
runtime recovery.

| Condition | Operator-visible action |
| --- | --- |
| Docker unavailable | Stop. Ask maintainer to start Docker Desktop and rerun readiness. |
| API/DB/Studio port conflict | Stop. Identify the owning process class. Do not silently remap ports. |
| Required independent config missing or port mismatch | Stop. Use package/repo-owned `supabase/config.toml`; do not fall back implicitly to legacy. |
| Vector container-name conflict or vector restarting | Wait 30-60 seconds, rerun sanitized status, and retry `supabase start` from the correct project context. |
| Vector conflict persists after bounded retries | Stop and record blocker. Do not delete containers, volumes, images, networks, or DB state. |
| Edge no-auth route returns `503` after start | Treat Edge as not ready. Check sanitized Edge/container state and stop before Upload Preview/Start. |
| Edge no-auth route returns auth-class | Edge route reaches the expected auth boundary. |
| Grafana unreachable | Record non-core caveat. Do not block bounded upload solely on Grafana status. |
| Raw `supabase status/start` output contains credential-like values | Suppress raw output. Record only exit code, status class, and availability class. |

## Maintainer Recovery Sequence

1. Confirm the current project context is the repo-owned or assembled
   package-local Supabase project.
2. Confirm legacy `Extrusion_data` is not the active target unless fallback was
   explicitly selected.
3. Confirm Docker is reachable.
4. Confirm expected independent ports are either reachable before recovery or
   closed after stop; do not continue on unrelated port conflicts.
5. Run `supabase stop` only without destructive flags.
6. Wait a short grace period and inspect sanitized container classes.
7. If vector is restarting or a start attempt reports vector conflict, wait
   30-60 seconds and retry `supabase start` a bounded number of times.
8. Stop if the same conflict persists. Escalate with sanitized error class only.
9. After successful start, verify API, DB, Studio, direct no-auth Edge auth-class,
   and package/local runtime readiness before any upload-related QA.
10. Keep Upload Preview, Start Upload, duplicate rerun, and Edge authenticated
    upload as separate approved QA steps.

## Remaining Caveats

1. Vector remained in restarting/stopped class after the final successful start.
2. Grafana remained unreachable and should stay a non-core caveat unless the
   acceptance owner changes the gate.
3. Repo-dev backend smoke can differ from package launcher behavior when
   repo-local environment files contain Supabase target keys.
4. Raw Supabase CLI output remains unsafe to paste into reports or PR bodies.
5. No forced Docker cleanup path was tested or approved.

## Merge Readiness For This PR

This PR is merge-ready when:

- the document remains the only intended source change unless a reviewer asks for
  code hardening;
- targeted runtime/package tests pass;
- launcher `-CheckOnly` passes;
- package/runtime smoke evidence is sanitized;
- `npm run typecheck` and `npm run build` pass;
- `git diff --check` passes;
- marker scan for new/changed docs is clean;
- untracked PNGs, operational fixtures, `.gstack`, `frontend/dist`, package
  output, zip, and checksum files are not committed.
