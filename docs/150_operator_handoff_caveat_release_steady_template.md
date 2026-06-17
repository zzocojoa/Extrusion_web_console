# Operator Handoff Caveat, Release, And Steady Period Template

Date: 2026-06-17 Asia/Seoul

Scope: docs-only P2 handoff clarification after legacy GUI hard-retirement
acceptance and recent upload gate/source binding hardening.

Verdict: `handoff_caveats_documented_release_tag_not_required_steady_template_ready`

Match Rate: `100%`

## Summary

This document clarifies the final handoff decision boundaries for the Web
Console operator workflow.

It covers:

- Grafana and Vector non-core caveat policy;
- whether a GitHub Release or tag is required for the current handoff state;
- a reusable steady operating period acceptance template.

This document does not create a release, tag, package zip, checksum, deployment,
Preview run, Start Upload job, Retry job, database change, Docker action, or
operator source mutation.

## Non-Developer Explanation

The Web Console can be the normal operator tool even if a monitoring-only
component, such as Grafana, is unavailable, as long as the core upload path still
works.

Core means the local web app, configuration, database, Edge upload function,
Preview, Upload jobs, Logs, and Audit evidence. If one of those stops working,
the caveat becomes a blocker.

A GitHub release or tag is not required just because the operator workflow is
accepted. A release/tag is only needed when the team chooses to hand off a
versioned package artifact through the formal release process.

## Evidence Chain

| Evidence | Role |
| --- | --- |
| `docs/32_operator_package_handoff_runbook.md` | Operator package handoff procedure |
| `docs/33_operator_release_tag_checklist.md` | Optional formal release/tag checklist |
| `docs/36_operator_handoff_caveat_closure.md` | Earlier default launcher caveat closure |
| `docs/147_operator_package_e2e_current_main_recheck.md` | Current-main package E2E state-context evidence |
| `docs/148_operator_legacy_gui_hard_retirement_review.md` | Legacy GUI hard-retirement final decision |
| `docs/149_operator_post_dedupe_retry_db_delta_recheck.md` | Post-retry DB delta evidence cleanup |

## Non-Core Caveat Policy

### Non-Core Caveats

Grafana and Vector are non-core only when all core gates below remain healthy.
Core gates are API, DB, Studio, Edge, Dashboard, Upload, Logs/Audit, local token
guard, and state context. Grafana is represented in the runtime API/UI as a
status/link-only service. Vector remains a documented observability caveat in
this runbook unless a later implementation adds a sanitized runtime API row for
it.

| Core gate | Required state |
| --- | --- |
| API health | reachable and `ok` |
| Config API | reachable; state context expected for the runtime |
| Source binding | expected source class, accessible, expected CSV count class |
| Target classes | `passed` |
| DB | ready |
| Studio | ready when used as runtime visibility evidence |
| Edge | ready; no-auth probes return auth-class response |
| Dashboard | route/API readable |
| Upload Preview | can run only after separate approval and preflight |
| Upload Job | latest/detail APIs readable |
| Logs/Audit | readable and safe for evidence |
| Local token guard | mutating APIs remain protected |

If these pass, the following remain caveats rather than blockers:

| Caveat | Classification | Required note |
| --- | --- | --- |
| Grafana unreachable | non-core caveat | status/link dashboard unavailable, Core Ops still usable |
| Vector unavailable or restarting | document-only non-core caveat | log shipping/observability reduced, local app logs/audit still authoritative |
| Browser network artifact incomplete | evidence caveat | API/route smoke can substitute only if console errors are zero or unavailable by tool limitation |

### Promote To Blocker

Promote Grafana, Vector, or any observability caveat to a blocker if it causes
or hides any of the following:

| Trigger | Action |
| --- | --- |
| API, DB, Studio, or Edge readiness fails | stop Preview/Upload, investigate core runtime |
| Dashboard, Settings, Upload, Logs, or Audit cannot load | stop handoff acceptance |
| Upload Preview result cannot be verified | do not approve Start Upload |
| Upload Job final state or audit trail is unavailable | do not approve retry or final acceptance |
| Token guard or API docs hardening regresses | block release/handoff |
| Operator cannot distinguish package/API-mode state from dev/mock state | block hard retirement or package handoff |

Do not classify Studio or Edge as a non-core caveat. If either is unavailable,
the upload runtime gate is blocked even when Grafana is the only visible
monitoring link failure.

## Release And Tag Decision

Current decision:

| Question | Decision |
| --- | --- |
| Is a GitHub Release required for current Web Console operator workflow acceptance? | no |
| Is a git tag required for current handoff caveat closure? | no |
| Is a package zip/checksum required for day-to-day accepted package-path use? | no, unless formal artifact handoff is requested |
| Can a release/tag be created later? | yes, through `docs/33_operator_release_tag_checklist.md` and separate approval |
| Does this document approve a release/tag? | no |

A release/tag becomes appropriate only when the maintainer wants a versioned
operator package artifact with zip, checksum, final smoke, and release notes.

Before any release or tag:

- follow `docs/33_operator_release_tag_checklist.md`;
- ensure package output stays outside the repository;
- verify zip checksum and redaction scans;
- confirm the accepted package label and source commit;
- request separate explicit approval for tag/release creation.

## Steady Operating Period Acceptance Template

Use this template when a maintainer or operator needs to accept a controlled
steady period before final handoff, retirement, or package replacement.

```text
Steady Operating Period Acceptance

Period:
- Start:
- End:
- Operator package/source commit:
- Runtime path class:
- State context:

Core checks:
- Dashboard:
- Settings/config:
- Runtime API:
- Upload page:
- Logs/Audit:
- API health:
- Target classes:
- Edge auth boundary:
- Source binding:

Observed operations during period:
- Upload Preview runs:
- Start Upload jobs:
- Retry jobs:
- Settings saves:
- Runtime lifecycle actions:
- Unexpected failures:

Non-core caveats:
- Grafana:
- Vector:
- Browser/network artifact:
- Other:

Acceptance decision:
- Verdict:
- Accepted caveats:
- Blockers:
- Required follow-up:

Controls retained:
- Fresh Preview-only before every upload:
- Target row review:
- Separate Start Upload approval:
- Separate Retry Failed approval:
- No DB reset/destructive cleanup:
- Rollback knowledge retained:

Approver:
- Name/role:
- Date/time:
```

## Handoff Go/No-Go Checklist

| Gate | Required result |
| --- | --- |
| Package or development runtime identity understood | yes |
| API-mode source of truth is `/api/config` | yes |
| State context is expected | yes |
| Target classes pass | yes |
| API/DB/Studio/Edge core runtime ready | yes |
| Grafana/Vector caveats classified | yes |
| Upload gates retained | yes |
| Release/tag need explicitly decided | yes |
| Rollback knowledge retained | yes |
| No destructive cleanup used as handoff fix | yes |

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
- package zip or checksum creation;
- operational source mutation.

## Redaction Policy

This document must remain safe to commit.

Do not include:

- raw operational source locators;
- raw operational filenames or row contents;
- raw DB URLs;
- credentials, tokens, Authorization values, or JWT-shaped values;
- local package output paths;
- logs containing secrets or local token material.

Use only state context classes, sanitized runtime classes, aggregate counts, and
document references.

## Next Action

Use this document as the final handoff decision aid.

No release/tag is needed for the current accepted operator workflow unless the
maintainer separately requests a formal package artifact release.

Future uploads still require fresh Preview-only, target count review, and
separate Start Upload or Retry Failed approval.
