# Operator Stage 3 Preview Timeout Profile

## Summary

- Date: 2026-06-13
- Branch: `codex/operator-stage-3-preview-timeout-profile`
- Scope: code, tests, and documentation for a bounded Preview timeout profile
- Related investigation: PR `#110`
- Source label class: `profile_a_corrected_bounded_source`
- Upload Preview executions during this change: `0`
- Start Upload executions during this change: `0`
- Retry Failed executions: `0`
- Duplicate rerun executions: `0`
- Edge authenticated upload calls: `0`
- Full operational dataset rollout: not performed
- Verdict: `profile_ready_for_review`

This change adds an explicit Stage 3 Profile A bounded full-scan Preview profile
so the corrected bounded source does not accidentally use the short interactive
default timeout budget.

The default Preview behavior remains unchanged. Operators must explicitly choose
the Stage 3 Profile A bounded profile for the approved bounded source.

## Problem

PR `#110` classified the failed Preview reference recovery as a CSV key
extraction timeout:

| Evidence class | Result |
| --- | --- |
| Target mismatch | weakened |
| Stale backend reuse | weakened |
| Source metadata issue | weakened |
| DB reconciliation reached | no |
| Timeout stage | CSV key extraction |
| Triggering option class | default per-file timeout with full scan |

The failed recovery used full-scan extraction with the default per-file timeout
budget. That budget is appropriate for short interactive Preview checks, but it
is too tight for the approved Profile A bounded source size observed in the
Stage 3 evidence chain.

## Added Profile

The new explicit profile is:

```text
stage3_profile_a_bounded_full_scan
```

When selected, the backend normalizes the Preview options to this bounded
budget:

| Option | Value |
| --- | ---: |
| `forceFullScan` | `true` |
| `maxFiles` | `3` |
| `maxRunSeconds` | `300` |
| `maxFileSeconds` | `120` |

The profile is intentionally bounded to Profile A file scope. It is not a full
rollout profile and does not relax Stage 3 numeric gates.

## Compatibility

Default Preview requests still use:

| Option | Default value |
| --- | ---: |
| `profile` | `default` |
| `forceFullScan` | `false` |
| `maxFiles` | `500` |
| `maxRunSeconds` | `120` |
| `maxFileSeconds` | `30` |

Existing API clients that omit `profile` keep the previous behavior.

## Safety Boundaries

This change does not:

- run Upload Preview;
- run Start Upload;
- run Retry Failed;
- run duplicate rerun or forced duplicate upload;
- call Edge upload routes with authentication;
- broaden the source scope;
- approve full operational dataset rollout;
- change DB schema or data;
- change Supabase or Docker runtime state.

The profile must be used only after:

- operator confirms the Stage 3 Profile A bounded source;
- source eligibility precheck passes;
- file count is within Profile A bounds;
- row count is within Profile A bounds;
- target class preflight passes.

## Implementation Notes

- Backend schema adds a `profile` option with default `default`.
- Backend schema applies the Stage 3 Profile A bounded preset only when
  `profile=stage3_profile_a_bounded_full_scan`.
- Frontend API types expose the profile and a helper request builder for the
  Stage 3 Profile A bounded full-scan profile.
- The normal Upload page still uses the default profile unless a caller
  explicitly chooses the Stage 3 helper/API option.

## Stage 3 Plan Update

`docs/82_operator_stage_3_bounded_rollout_plan.md` now includes a Preview
timeout profile requirement. It states that Stage 3 Profile A full-scan Preview
must use the explicit bounded profile and must stop if a default-timeout
Preview fails before any approved rerun.

## Redaction Result

| Check | Result |
| --- | --- |
| Raw source path recorded | no |
| Raw source filename recorded | no |
| Raw source content recorded | no |
| Row content recorded | no |
| Full local path recorded | no |
| Raw DB URL recorded | no |
| Token, auth header, or JWT recorded | no |
| Package output, archive, or digest recorded | no |

## Validation

Required validation for this PR:

- targeted backend upload preview tests;
- `npm run typecheck`;
- `npm run build:api`;
- `npm run build`;
- `git diff --check`;
- marker scan for secrets, raw operational source markers, package output,
  archive, and digest markers;
- PR file scope check.

## Next Safe Action

After this PR is reviewed and merged, the next branch should be:

```text
codex/operator-stage-3-preview-reference-recovery-rerun
```

That branch may run the corrected source Preview-only exactly once using the
explicit Stage 3 Profile A bounded full-scan profile. Start Upload remains
forbidden until that Preview succeeds with reachable DB evidence and acceptable
bounded counts.
