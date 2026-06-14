# Operator Legacy GUI Replacement Readiness

Date: 2026-06-14 Asia/Seoul

Branch: `codex/operator-legacy-gui-replacement-readiness`

Scope: docs-only final operational transition checklist before fully replacing
the legacy Tkinter GUI with Extrusion Web Console

Verdict: `ready_for_controlled_operator_transition_with_caveats`

Match Rate: `100%`

## Summary

Extrusion Web Console has enough Core Ops coverage to proceed toward controlled
operator transition from the legacy Tkinter GUI, but it should not be treated as
an unrestricted upload system.

The accepted production-like evidence is bounded:

- Stage 4 Preview succeeded for an approved operational source scope.
- Stage 4 Start Upload succeeded once for the reviewed `17179` target rows.
- Dashboard now shows real active backend state and a sanitized state context
  label so operators can distinguish operator/package, development, QA
  temporary, configured, unknown, or inaccessible state contexts.
- Edge runtime mount recovery evidence exists, but the later `15096` new-file
  upload target has not yet completed successfully after recovery.

Operational transition can continue only with the existing gated process:
fresh Preview-only, target count review, and separate explicit approval before
any upload action.

## Non-Developer Explanation

The web console is now close to replacing the old desktop GUI for the normal
operator workflow.

What is already proven: the browser app can find upload candidates, compare
them with the database, upload an approved bounded target, record audit/job
evidence, and show real Dashboard state instead of fake demo data.

What is still not automatic: every new file or new upload batch still needs a
fresh Preview first. Preview is the "look before touching the database" step.
Only after the reviewed target count matches expectations should Start Upload
or Retry Failed be approved separately.

If something looks wrong, do not reset the DB and do not press retry. Preserve
the evidence, check Dashboard state context, review logs/audit, and decide from
a read-only investigation.

## Completed

| Area | Current status | Evidence |
| --- | --- | --- |
| Core product scope | Implemented for Dashboard, Settings, Upload, Logs, runtime status, audit, launcher | `README.md`, `docs/00_product_scope.md`, `docs/01_development_roadmap.md` |
| Upload Preview | Implemented with exact-key DB reconciliation and audit logging | README verification notes |
| Upload Job | Implemented with Start Upload, Retry Failed, job/file/event state, SSE/event replay, accepted row counters | README, Stage 4 docs |
| Audit Logs | Implemented with redacted safe params and append-only behavior | README, Audit QA sections |
| Settings | Implemented with read/write config, env override blocking, secret hiding, audit rows | README |
| Launcher/package | Implemented with localhost backend, built frontend serving, local token guard, shortcut installer, package assembly controls | README, `docs/32_operator_package_handoff_runbook.md` |
| Dashboard real state | Implemented, no scaffold mock running job in API mode | Dashboard post-merge smoke and `docs/132_operator_dashboard_state_context_visibility.md` |
| Dashboard state context | Implemented, sanitized state context visible in Dashboard/Runtime/Settings | `docs/132_operator_dashboard_state_context_visibility.md` |
| Stage 4 accepted upload | Accepted for one approved target | `docs/110_operator_stage_4_final_acceptance_summary.md` |
| Stage 4 accepted row evidence | `17179 / 17179 / 17179` processed/uploaded/accepted, DB delta `17179` | `docs/110_operator_stage_4_final_acceptance_summary.md` |
| Edge runtime rebind | Runtime rebound to current repo function source, entrypoint present, no-auth `401_auth_class` | `docs/125_operator_edge_runtime_rebind_execution.md` |

## Needs Work Before Full Cutover

| Area | Required before hard retirement of legacy GUI | Reason |
| --- | --- | --- |
| Operator PC E2E expansion | Run a final controlled E2E on the actual operator PC/package context | Current evidence is strong but still split across QA/runtime contexts |
| New-file upload after Edge rebind | Reconfirm gates and run only after separate approval if business requires the `15096` target | Edge rebind recovered mount, but upload retry was not executed after rebind |
| Default runtime context hardening | Verify package/operator state context stays stable across launcher restarts | Prior evidence showed state/reference drift can confuse operators |
| Final package handoff smoke | Use handoff runbook from package folder, not source dev server | Replacement depends on the exact operator launch path |
| Legacy behavior comparison | Keep representative file detection, duplicate handling, failure reporting checks in the final E2E | Product scope requires parity before hard replacement |
| Operator training | Confirm operator understands Preview, target count review, separate upload approval, and rollback | Prevents accidental retry/full rollout |

## Operational Controls To Keep

These controls remain mandatory after transition:

| Control | Keep? | Rationale |
| --- | --- | --- |
| Fresh Preview-only before upload | yes | Prevents stale source/reference mistakes |
| Target count review | yes | Operator must confirm files/rows before DB mutation |
| Separate explicit upload approval | yes | Preview success is not upload approval |
| Start Upload exactly once per approved target | yes | Avoids accidental duplicate run paths |
| Retry Failed only by separate approval | yes | Retry is still a product upload action |
| No duplicate rerun by default | yes | Duplicate-safe DB upsert is final guard, not a reason to rerun casually |
| Dashboard state context review | yes | Confirms which state DB the Dashboard is reading |
| Audit/log review after upload | yes | Required operational evidence |
| No destructive DB/Docker/Supabase cleanup as fallback | yes | Preserves evidence and prevents data loss |
| Legacy GUI fallback window | yes | Keep until operator PC E2E and first steady operating period are accepted |

## Production Deploy Decision

Production deploy is not required for legacy GUI replacement.

This product is a localhost-only operator PC application. Normal release is an
operator package/handoff flow, not cloud production deployment. A production
deploy would be out of scope unless the product is explicitly re-scoped away
from local-only operation.

Decision:

| Item | Decision |
| --- | --- |
| Cloud production deploy | not needed |
| Operator package build/handoff | needed for cutover |
| API-mode frontend build | required for operator package validation |
| Launcher/package smoke | required before handoff |

## GitHub Release And Tag Decision

GitHub Release or tag creation is not required for this docs-only readiness
step.

For operator handoff, a release/tag can be useful only after a final package
candidate is built, smoked, checksummed, and accepted. Do not create or modify a
GitHub Release/tag from this document.

Decision:

| Item | Decision |
| --- | --- |
| Release/tag now | no |
| Release/tag after accepted package candidate | optional, maintainer decision |
| Required for local operator cutover | no |

## Grafana And Vector Caveat Policy

Grafana and Vector remain non-core caveats unless they block API, DB, Studio,
Edge, Preview, Upload Job, Dashboard, Upload, Logs, or Settings.

Policy:

| Component | Treatment |
| --- | --- |
| Grafana unreachable | non-core caveat if upload/runtime gates pass |
| Vector unhealthy/restarting | non-core caveat if upload/runtime gates pass |
| Grafana status link broken | track as monitoring/handoff issue |
| Vector/Logflare issue causing Edge/API failure | promote to blocker |

Operator replacement should not be blocked solely by Grafana/Vector caveats if
Core Ops upload and audit evidence pass. The caveat must be documented in the
handoff report.

## Operator PC E2E Expansion

Before hard retirement of the legacy GUI, run one operator-PC E2E acceptance
cycle from the package path.

Minimum E2E checklist:

1. verify package checksum and extraction location;
2. run launcher `-CheckOnly`;
3. run shortcut installer `-CheckOnly`;
4. launch through the operator launcher, not Vite;
5. confirm Dashboard state context is operator/package or approved configured
   class;
6. confirm Settings, Upload, Logs/Audit, and Dashboard load;
7. confirm runtime API/DB/Studio/Edge readiness;
8. run fresh Preview-only for the intended source scope;
9. review file count, target file count, upload target rows, excluded/risky
   counts, and DB delta `0`;
10. request separate explicit Start Upload or Retry Failed approval only if the
    Preview target is accepted;
11. after upload, record job status, processed/uploaded/accepted rows, DB delta,
    audit rows, and Dashboard latest job/state context.

Do not include full rollout, duplicate rerun, DB reset, Docker cleanup, or
Supabase reset in this E2E.

## Future Upload Gate

All future upload work, including new operational CSV files, must follow this
gate:

| Step | Required outcome |
| --- | --- |
| Source eligibility | source accessible, CSV count known, filename-date eligible, `file_date_missing=0`, zero-row files `0` |
| Runtime preflight | API/DB/Studio/Edge ready or explicitly accepted caveat |
| Target class preflight | DB/Edge aligned to expected independent target |
| Fresh Preview-only | exactly one Preview unless separately approved otherwise |
| Count review | target files and upload target rows reviewed by operator/maintainer |
| DB non-mutation evidence | Preview DB row-count delta `0` |
| Approval | separate explicit approval for exactly one Start Upload or Retry Failed |
| Post-upload evidence | final status, row counters, DB delta, audit/job events |

Preview success alone never authorizes upload.

## Legacy GUI Rollback And Fallback

Keep the legacy Tkinter GUI available as a fallback during the controlled
transition period.

Fallback policy:

| Situation | Action |
| --- | --- |
| Web console package fails to launch | use previous known-good package or legacy GUI while preserving logs |
| Dashboard shows unexpected latest job/count | check state context first, do not reset DB |
| Preview blocked or target count unexpected | stop, investigate source/runtime/config, do not upload |
| Upload job failed before row progress | preserve job/audit evidence, investigate, do not retry automatically |
| Operator needs urgent continuity | use legacy GUI only under maintainer-approved fallback procedure |

Rollback must not delete AppData config/state/logs, operational CSV files,
local Supabase data, Docker containers, Docker volumes, or database rows.

## Final Go/No-Go

| Gate | Status | Cutover meaning |
| --- | --- | --- |
| Core Ops parity | mostly passed | Web Console covers V1 operating surface |
| Accepted bounded upload evidence | passed for `17179` target | Proves one controlled Stage 4 upload path |
| New-file post-Edge-rebind upload | pending if needed | Required only for that new file scope |
| Dashboard state context visibility | passed | Reduces state-context confusion |
| Package/handoff path | ready for final smoke | Must be verified from operator package |
| Production deploy | not needed | Local-only app |
| GitHub Release/tag | not needed now | Optional after accepted package candidate |
| Legacy GUI hard retirement | not yet | Keep fallback until operator PC E2E and steady period pass |

Readiness verdict:

`controlled_transition_ready_legacy_fallback_retained`

The web console can be treated as the preferred operator path after final
operator-package E2E passes. The legacy GUI should remain available until the
operator PC package path completes acceptance and the first steady operating
period has no blocker.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Supabase lifecycle or destructive operation;
- Docker lifecycle or destructive operation;
- production deploy;
- GitHub Release or tag creation/modification;
- operational source mutation.

## Redaction Result

This document records only sanitized runtime/source classes, safe document
references, aggregate counts, and safe run/job identifiers already present in
reviewed reports.

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
| Required readiness topics covered | passed |
| Match Rate | `100%` |
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
| PR file scope | docs/133 only |

## Next Action

Review this readiness checklist. If accepted, use it as the gate before hard
retiring the legacy Tkinter GUI: final operator-package E2E first, legacy GUI
fallback retained until the operating period is accepted.
