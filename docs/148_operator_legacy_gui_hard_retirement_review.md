# Operator Legacy GUI Hard Retirement Review

Date: 2026-06-16 Asia/Seoul

Branch: `codex/operator-legacy-gui-hard-retirement-review`

Scope: docs-only final review for retiring the legacy Tkinter GUI from the
active operator workflow after package-path steady period acceptance.

Verdict: `legacy_gui_hard_retirement_go_with_rollback_retained`

Match Rate: `100%`

## Summary

The remaining hard-retirement blocker from the package transition sequence is
cleared by explicit operator acceptance of the controlled package-path steady
period.

Accepted evidence chain:

- `docs/133_operator_legacy_gui_replacement_readiness.md` established that Core
  Ops coverage was ready for controlled transition with the legacy GUI fallback
  retained.
- `docs/134_operator_package_e2e_acceptance.md` blocked hard retirement because
  the package candidate was stale and state context evidence was missing.
- `docs/135_operator_package_state_context_recheck.md` cleared the stale package
  and state-context blockers for a current API-mode operator package, while
  retaining the legacy fallback through the first steady operating period.
- `docs/147_operator_package_e2e_current_main_recheck.md` rechecked the latest
  accepted `main` package path and confirmed `operator_package` state context on
  Dashboard, Settings/config, and Runtime.
- Repeated GET-only steady-period samples after PR #164 showed
  `operator_package` state context, target class preflight `passed`, API/DB/
  Studio/Edge `ready`, and no new upload/retry event created by those checks.
- The operator has now explicitly accepted that the package-path controlled
  steady period was used without abnormal signs.

Decision: the Web Console can become the active operator path, and the legacy
Tkinter GUI can be retired from normal operations. This document does not delete
the legacy project, remove rollback knowledge, approve a new upload, or change
runtime state.

## Non-Developer Explanation

The browser console has now proven enough of the job the old desktop GUI used
to do.

The package version opens through the operator path, reads the operator package
state, shows real upload state, and can be checked through Dashboard, Settings,
Runtime, Logs, and Audit without falling back to fake demo data. The operator
also used the package path for a steady period and approved that no abnormal
signs appeared.

So the old Tkinter GUI no longer needs to be the normal operating tool.

It should still remain available as rollback knowledge until the team decides
to remove or archive it separately. Future uploads are not automatic. Every new
upload still starts with a fresh Preview-only gate, target row review, and a
separate Start Upload or Retry Failed approval.

## Final Gate Review

| Gate | Result | Evidence |
| --- | --- | --- |
| Core Ops parity | passed | Dashboard, Settings, Upload, Logs/Audit, runtime status, local package launcher |
| Accepted upload evidence | passed | reviewed prior Stage 4 upload and retry reports |
| Current package candidate | passed | `docs/147_operator_package_e2e_current_main_recheck.md` |
| Package launcher path | passed | current-main package E2E recheck |
| Dashboard state context | passed | `operator_package` / `Operator/package state` / `present` |
| Settings/config state context | passed | `operator_package` / `Operator/package state` / `present` |
| Runtime state context | passed | `operator_package` / `Operator/package state` / `present` |
| Target class preflight | passed | DB, upload Edge, and runtime Edge aligned |
| Core runtime | passed | API/DB/Studio/Edge `ready` in repeated read-only samples |
| Browser console artifact | passed with caveat | browser smoke observed console errors `0`; network resource timing was not available in this runtime |
| Steady operating period | accepted | operator explicitly approved package-path steady period with no abnormal signs |
| Future upload control | must remain | fresh Preview-only, target count review, separate approval |
| Production deploy | not needed | localhost-only operator package product |
| GitHub Release/tag | not required | optional only for a separately accepted package release process |

## Hard Retirement Decision

| Decision point | Result |
| --- | --- |
| Use Web Console as active operator path | go |
| Keep using legacy Tkinter GUI as normal path | no |
| Delete legacy project/files now | no |
| Remove fallback knowledge now | no |
| Keep rollback path documented | yes |
| Allow future upload without Preview review | no |
| Allow Retry Failed without separate approval | no |
| Treat Grafana caveat as hard blocker | no |

Final decision:

`go` for operational hard retirement of the legacy Tkinter GUI as the normal
operator path.

`go` for Web Console package path as the active operator workflow.

`no-go` for deleting legacy assets, deleting rollback procedures, or weakening
upload gates in this docs-only step.

## Runtime State At Final Review

Latest read-only sample for this document:

| Check | Result |
| --- | --- |
| `/api/health` | `200`, `ok` |
| `/api/config` state context | `operator_package`, storage `present` |
| `/api/config` target classes | `passed`, upload/runtime aligned `true` |
| `/api/dashboard` state context | `operator_package` |
| Dashboard latest job status | `succeeded` |
| `/api/runtime/local-supabase` state context | `operator_package` |
| Runtime API | `ready` |
| Runtime DB | `ready` |
| Runtime Studio | `ready` |
| Runtime Edge | `ready` |
| Runtime overall | `attention` |
| Runtime reason | `non_core_runtime_attention` |
| Grafana | `unreachable` |
| `/api/audit?limit=5` | reachable |

The current audit top included upload-related historical rows. This document did
not create those rows and did not execute Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated Edge call, or full rollout.

## Non-Core Caveat Policy

Grafana remains unreachable at the time of this review. It is a monitoring and
handoff caveat, not a blocker for Core Ops hard retirement, because API, DB,
Studio, Edge, Dashboard, Settings, Upload, Logs/Audit, and package state-context
checks passed.

If Grafana or another non-core service starts affecting API, DB, Studio, Edge,
Preview, Upload Job, Dashboard, Settings, or Logs/Audit behavior, promote the
issue to a blocker and investigate without destructive cleanup.

## Operating Controls To Keep

| Control | Required after hard retirement? | Reason |
| --- | --- | --- |
| Fresh Preview-only before upload | yes | prevents stale source/reference mistakes |
| Target count review | yes | confirms file and row scope before DB mutation |
| Separate Start Upload approval | yes | Preview success is not upload permission |
| Start Upload exactly once per approved target | yes | avoids accidental duplicate mutation |
| Retry Failed separate approval | yes | retry is still an upload action |
| Dashboard state context check | yes | confirms operator/package state context |
| Logs/Audit review after mutation | yes | preserves operator evidence |
| No DB reset/cleanup as fallback | yes | prevents data loss and evidence loss |
| Legacy rollback knowledge | yes | supports emergency rollback without making GUI the default path |

## Rollback Policy

Hard retirement means the old Tkinter GUI is no longer the normal operator path.
It does not mean deleting evidence, state, or rollback knowledge.

Rollback triggers:

| Situation | Safe rollback action |
| --- | --- |
| Web Console package fails to launch | use previous accepted package or approved legacy GUI fallback |
| Dashboard state context is unexpected | stop, inspect state context and logs, do not upload |
| Preview target count is unexpected | stop, investigate source/runtime/config, do not upload |
| Upload job fails | preserve job/audit evidence, investigate, do not retry automatically |
| Operator continuity is urgent | use maintainer-approved fallback procedure |

Rollback must not delete AppData config/state/logs, operational CSV files,
local Supabase data, Docker containers, Docker volumes, or database rows.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Docker volume delete or prune;
- Supabase reset;
- Supabase lifecycle or destructive operation;
- Docker lifecycle or destructive operation;
- production deploy;
- GitHub Release or tag creation/modification;
- operational source mutation;
- legacy project deletion.

## Redaction Result

This document records only sanitized state context classes, safe route names,
aggregate status values, and reviewed document references.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no credential value;
- no raw auth header value;
- no signed session assertion value;
- no private credential value.

## Validation

| Check | Result |
| --- | --- |
| Match Rate | `100%` |
| Operator steady period acceptance | passed |
| Required prior docs reviewed | passed |
| `git status --short --branch` | checked |
| Read-only API smoke | passed |
| Runtime smoke | passed with non-core caveat |
| Upload Preview executed | no |
| Start Upload executed | no |
| Retry Failed executed | no |
| duplicate rerun executed | no |
| authenticated Edge call executed | no |
| full rollout executed | no |
| Settings save executed | no |
| DB/Supabase/Docker lifecycle or destructive action executed | no |
| production deploy executed | no |
| GitHub Release/tag created or modified | no |

## Next Action

Use Web Console package path as the active operator workflow.

Keep future upload gates unchanged: fresh Preview-only, target rows review, and
separate explicit Start Upload or Retry Failed approval.

Keep legacy GUI rollback knowledge available until a separate archival/removal
decision is made.
