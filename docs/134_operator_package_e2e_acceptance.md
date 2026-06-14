# Operator Package E2E Acceptance

Date: 2026-06-14 Asia/Seoul

Branch: `codex/operator-package-e2e-acceptance`

Scope: docs-only operator PC/package final E2E acceptance check based on
`docs/133_operator_legacy_gui_replacement_readiness.md`

Verdict: `blocked_for_hard_legacy_gui_retirement_with_runtime_evidence`

Match Rate: `82%`

## Summary

The operator-package E2E gate was performed without Upload Preview, Start
Upload, Retry Failed, duplicate rerun, authenticated Edge upload call, full
rollout, DB/Supabase/Docker lifecycle operation, production deploy, or GitHub
Release/tag creation.

Core runtime and UI route evidence is good:

- API-mode package candidate exists outside the repository.
- package launcher `-CheckOnly` passed.
- shortcut installer `-CheckOnly` passed.
- Dashboard, Upload, Logs, and Settings routes returned `200`.
- Dashboard API showed the latest real upload job as `succeeded` with
  `15096` processed/uploaded/accepted rows.
- runtime API, DB, Studio, and Edge were reachable.
- Edge no-auth `GET` and `POST {}` returned `401_auth_class`.
- Grafana and Vector remained non-core caveats.

Hard retirement of the legacy Tkinter GUI is not accepted yet because two
operator-package cutover gates are not fully proven:

- the newest located package candidate was built from an older source commit
  than current `main`;
- the active backend did not expose the expected sanitized state context payload,
  so Dashboard state context could not be proven as `operator/package` or an
  approved configured class.

## Non-Developer Explanation

The web console itself is working: the pages open, the backend answers, the
database and Edge runtime are reachable, and the Dashboard shows the latest
successful upload result.

The part that is not ready is the final handoff confidence. The package found
on this PC is not clearly the latest accepted version, and the Dashboard did
not show the safe "which state file am I reading?" label that operators need
before the old Tkinter GUI is fully retired.

So the correct decision is: keep using the web console as the preferred path,
but do not remove the legacy GUI fallback yet. First prepare or identify a
current operator package, launch through that package path, and confirm the
Dashboard state context label.

## Completed

| Area | Result | Evidence |
| --- | --- | --- |
| Current branch | passed | `codex/operator-package-e2e-acceptance` from current `main` |
| Package candidate discovery | passed with caveat | repo-external operator package output found |
| Package runtime mode | passed | package metadata reports `operator-ready` |
| Package frontend mode | passed | package metadata reports `api` |
| Required package shape | passed | package root, launcher, built frontend, and packaged Python runtime present |
| Launcher check-only | passed | `launcher/start_web_console.ps1 -CheckOnly` completed without starting backend |
| Shortcut check-only | passed | `launcher/install_shortcuts.ps1 -CheckOnly` completed without writing shortcuts |
| Dashboard route load | passed | package/API origin route returned `200` |
| Upload route load | passed | package/API origin route returned `200` |
| Logs route load | passed | package/API origin route returned `200` |
| Settings route load | passed | package/API origin route returned `200` |
| Read-only API routes | passed | `/api/health`, `/api/config`, `/api/dashboard`, `/api/audit` returned `200` |
| Dashboard real-state evidence | passed | latest active job `succeeded`, rows `15096 / 15096 / 15096` |
| Runtime API | passed | reachable |
| Runtime DB | passed | reachable |
| Runtime Studio | passed | reachable |
| Runtime Edge | passed | reachable |
| Edge no-auth boundary | passed | `GET` and `POST {}` returned `401_auth_class` |
| Target class alignment | passed | DB/Edge target class preflight `passed` |
| Audit read-only smoke | passed | recent audit rows loaded with safe action/result/job summaries |
| Upload actions avoided | passed | no Preview, Start Upload, Retry Failed, duplicate rerun, or full rollout executed |
| Release/deploy avoided | passed | no production deploy and no GitHub Release/tag operation |

## Still Needed Before Hard Cutover

| Area | Status | Required next evidence |
| --- | --- | --- |
| Current package candidate | blocked | build or identify an API-mode operator package from current accepted `main` |
| Package-path first launch | blocked | launch through the current package path, not a stale package or source dev context |
| Dashboard state context | blocked | Dashboard/Runtime/Settings must show `operator/package` or approved configured state context |
| Browser console/network evidence | caveat | browser-level console/network capture was not available in this session; HTTP route smoke passed |
| Steady operating period | pending | keep legacy GUI fallback through first accepted steady period |

## Operational Controls To Keep

| Control | Keep? | Reason |
| --- | --- | --- |
| Fresh Preview-only before future upload | yes | prevents stale source/reference mistakes |
| Target count review | yes | confirms expected files and rows before DB mutation |
| Separate explicit upload approval | yes | Preview success is not upload approval |
| Start Upload exactly once per approved target | yes | prevents accidental repeated mutation |
| Retry Failed only by separate approval | yes | retry is still a product upload action |
| No duplicate rerun by default | yes | upsert safety is not permission to rerun casually |
| Dashboard state context review | yes | confirms the Dashboard is reading the intended state DB context |
| Audit/log review after upload | yes | creates operator evidence for every mutation |
| No DB/Docker/Supabase destructive fallback | yes | preserves data and investigation evidence |
| Legacy GUI fallback | yes | required until package E2E and steady period are accepted |

## Package And Launcher Evidence

| Check | Result |
| --- | --- |
| Package location class | repo-external operator package output |
| Latest located package source commit | older than current `main` |
| Package runtime mode | `operator-ready` |
| Package frontend mode | `api` |
| Built frontend present | yes |
| Packaged Python runtime present | yes |
| Launcher `-CheckOnly` | passed |
| Shortcut installer `-CheckOnly` | passed |
| Backend process started by check-only | no |
| Shortcuts written by check-only | no |

The package candidate is structurally valid, but it is not sufficient for hard
cutover because it is not current with `main`.

## Dashboard And UI Route Evidence

| Route | Result |
| --- | --- |
| `/` | `200` |
| `/upload` | `200` |
| `/logs` | `200` |
| `/settings` | `200` |

The routes loaded from the localhost API/package origin. This confirms basic
page availability for Dashboard, Upload, Logs/Audit, and Settings.

Browser-level console and network capture was not available in this session, so
the result is route-level acceptance, not full visual/browser acceptance.

## Dashboard State Evidence

| Item | Result |
| --- | --- |
| Dashboard API reachable | yes |
| Latest job status | `succeeded` |
| Latest job mode | `retry_failed` |
| Latest job rows | `15096 / 15096 / 15096` |
| Latest job failed files | `0` |
| Dashboard scaffold mock job visible | no evidence of scaffold mock job |
| Sanitized state context payload | missing |
| Required state context gate | blocked |

The Dashboard showed real latest backend state, not scaffold mock running state.
However, the active backend did not include the expected state context metadata.
This blocks hard GUI retirement because the operator cannot prove from the UI
that the Dashboard is reading `operator/package` or an approved configured state
context.

## Runtime Readiness

| Runtime gate | Result |
| --- | --- |
| API | ready |
| DB | ready |
| Studio | ready |
| Edge | ready |
| DB/Edge target alignment | passed |
| Edge no-auth `GET` | `401_auth_class` |
| Edge no-auth `POST {}` | `401_auth_class` |
| Overall runtime | `attention` |
| Runtime attention reason | `non_core_runtime_attention` |

The core runtime gates passed. The overall attention state is caused by
non-core runtime caveats, not by API, DB, Studio, or Edge upload readiness.

## Grafana And Vector Caveat

| Component | Result | Cutover treatment |
| --- | --- | --- |
| Grafana | unreachable/timed out | non-core caveat |
| Vector | restarting/stopped class observed through runtime summary | non-core caveat |

Grafana and Vector do not block Core Ops if API, DB, Studio, Edge, Upload,
Dashboard, Logs, and Settings are usable. They remain handoff caveats and must
not trigger DB reset, Docker cleanup, or Supabase reset.

## Legacy GUI Fallback

| Fallback condition | Decision |
| --- | --- |
| Package candidate not current | keep legacy GUI available |
| Dashboard state context missing | keep legacy GUI available |
| Browser-level acceptance incomplete | keep legacy GUI available |
| Future upload needed | require fresh Preview-only, count review, and separate approval |
| Emergency operator continuity | use legacy GUI only under maintainer-approved fallback procedure |

The legacy Tkinter GUI should remain available until a current package passes
operator-path E2E and the first steady operating period is accepted.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- Settings save;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase lifecycle or destructive operation;
- Docker lifecycle or destructive operation;
- production deploy;
- GitHub Release or tag creation/modification;
- operational source mutation.

## Redaction Result

This document records only sanitized package classes, safe route names, runtime
classes, reviewed job identifiers, and aggregate counts.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no token value;
- no Authorization header value;
- no JWT value;
- no secret value.

## Validation

| Check | Result |
| --- | --- |
| Required acceptance topics covered | passed |
| Match Rate | `82%` |
| Launcher `-CheckOnly` | passed |
| Shortcut installer `-CheckOnly` | passed |
| UI route HTTP smoke | passed |
| Read-only API smoke | passed |
| Runtime readiness smoke | passed with non-core caveat |
| Upload Preview executed | no |
| Start Upload executed | no |
| Retry Failed executed | no |
| duplicate rerun executed | no |
| authenticated Edge call executed | no |
| full rollout executed | no |
| DB/Supabase/Docker lifecycle or destructive action executed | no |
| production deploy executed | no |
| GitHub Release/tag created or modified | no |
| `git diff --check` | passed |
| marker scan | passed |
| PR file scope | docs/134 only |

## Next Action

Prepare or identify a current API-mode operator package from accepted `main`,
launch through that package path, and re-run this E2E gate. Hard legacy GUI
retirement should remain blocked until Dashboard state context is visible as
`operator/package` or an approved configured class and the first steady
operating period is accepted.
