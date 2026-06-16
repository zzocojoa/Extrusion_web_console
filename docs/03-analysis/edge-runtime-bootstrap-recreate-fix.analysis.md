# Gap Analysis: edge-runtime-bootstrap-recreate-fix

> Date: 2026-06-16 | Scope: Edge runtime recovery launcher

## Match Rate: 96%

## Summary

The Edge recovery failure was traced to manual container/bootstrap recreation,
not to Upload Preview, Start Upload, DB reconciliation, or source eligibility.
Recreating the Edge runtime from extracted Docker command metadata is fragile
because the bootstrap command can lose TypeScript import string quoting and boot
with invalid source.

The implemented fix adds a small operator launcher script that uses the supported
Supabase CLI path, `supabase functions serve --workdir <current-repo> --yes`,
then checks that the local upload-metrics route reaches the no-auth auth boundary
and that the container exposes an upload-metrics entrypoint. It does not mutate
DB state, source files, upload jobs, Preview runs, or Supabase volumes.

## Implemented Items

- [x] Added an Edge runtime launcher for current repository function source.
- [x] The launcher first checks existing Edge readiness and exits without
      starting a duplicate process when the route and entrypoint are healthy.
- [x] The launcher starts Supabase functions through the CLI-supported serve
      path when recovery is needed.
- [x] The launcher checks no-auth `GET` and `POST {}` classification and treats
      401/403 as auth-class readiness.
- [x] The launcher checks container entrypoint presence when Docker inspection is
      available.
- [x] The launcher redacts token, secret, Authorization, JWT, credential URL, and
      password-like markers in its own log output.
- [x] Tests verify the script uses `supabase functions serve` and does not use
      Docker/Supabase destructive or lifecycle reset commands.

## Non-Goals Confirmed

- [x] No Upload Preview execution.
- [x] No Start Upload execution.
- [x] No Retry Failed execution.
- [x] No duplicate rerun.
- [x] No authenticated manual Edge upload call.
- [x] No full rollout.
- [x] No DB reset/init/delete/truncate/drop/prune.
- [x] No Docker delete/prune/volume action.
- [x] No Supabase reset.
- [x] No operational CSV mutation.

## Root Cause Classification

`manual_edge_bootstrap_recreate_command_corruption`

The strongest evidence is that the direct runtime boot path succeeded when
delegated to Supabase CLI `functions serve`, while manual reconstruction of the
Edge runtime command repeatedly failed at bootstrap/entrypoint handling. The
manual approach was therefore the wrong layer to preserve as operator procedure.

## Risk Review

- Risk level: medium. This touches operator runtime recovery, not upload
  execution.
- Rollback path: stop using `launcher/start_edge_runtime.ps1` and revert the
  script/test commit.
- Compatibility impact: existing `launcher/start_web_console.ps1` behavior is
  unchanged.
- Observability impact: recovery attempts write redacted launcher logs under the
  existing launcher log area.
- Security: raw source paths, DB URLs, tokens, Authorization headers, JWTs, and
  secrets are not documented. The script redacts these classes in its own log
  messages.
- Failure mode: if an existing stale Edge container still owns the expected name
  and cannot be rebound non-destructively, the script fails closed and reports
  non-ready instead of deleting containers or attempting upload.

## Validation Plan

- Targeted launcher tests for script scope and PowerShell syntax.
- Runtime check-only run after recovery to confirm no-auth auth-class and
  entrypoint presence without starting upload flow.
- `git diff --check`.
- Marker scan for raw operational source content/path and secret classes.

## Next Step

Create a PR for review. Upload retry remains forbidden until the Edge runtime
check passes and the user separately approves exactly one retry.
