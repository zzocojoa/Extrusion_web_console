# V1 Cutover Go/No-Go Validation Plan

Status: `no_go_cutover_execution_conditional_go_candidate_hard_gates_pending_no_data_mutation`

## Executive Summary

This document is a decision package for deciding whether the legacy Tkinter GUI
can be replaced by `Extrusion_web_console` for V1 Core Ops.

It does not approve Upload Preview, Start Upload, Retry Failed, DB delete,
Settings save, Supabase start/stop, Supabase reset, Docker cleanup, schema
migration, LAN exposure, deployment, production DB access, or source-file
mutation by itself. Any action that writes local state, mutates the DB, changes
runtime state, exposes the app, or deploys a package needs the separate approval
gate named in the relevant source document.

The current cutover decision is evidence-led. `docs/175` found no broad
unimplemented Core Ops blocker. V2 WP-01 on `main` and the approved post-merge
operator-PC Preview-only run and later read-only observations now prove
representative CSV compatibility, synthetic large-Preview behavior, real
`folder_all` Preview completion, API/DB readiness, failure visibility, Job Logs
visibility, and Core Ops route rendering. The current recommendation is
`NO-GO` for cutover execution. `docs/182` records package/inventory baseline
evidence but not an executing package, complete operator/source binding, or
approved Preview. Production atomic content-manifest/snapshot binding retained
through Preview, Start, and Retry plus deterministic
replacement/concurrency/tamper/replay tests must pass first, followed by a
rebuilt and verified executing package. A separately controlled, pre-provisioned
verified target baseline must already exist. Only then may an execution-adjacent
successor inventory, separately approved protected manifest preparation,
separately approved read-only target-identity preparation with human exact-match
review, and a later separately approved current Preview be prepared. This plan
does not authorize baseline provisioning/rotation. Any required disposition of
partial-overlap rows, final sign-off, and explicit ownership of the non-core
Grafana/Vector attention state also remain hard gates before a `CONDITIONAL GO`
candidate can proceed.

## Decision Scope

This plan can decide:

- whether current evidence is sufficient for `GO`, `CONDITIONAL GO`, `NO-GO`,
  or `BLOCKED` for replacing the legacy GUI for V1 Core Ops;
- whether a non-destructive operator-PC validation package is complete;
- whether a Preview-only approval package is ready to request;
- whether a Start Upload or Retry Failed approval package is ready to request
  after Preview evidence exists;
- whether deferred or excluded items are correctly kept out of the V1 cutover
  decision.

This plan cannot decide or approve:

- operational Start Upload, Retry Failed, or DB delete execution;
- Upload Preview execution before atomic content binding is implemented and
  tested, or without the later Preview-only approval required by `docs/164` and
  `docs/173`;
- Supabase reset, migration, backfill, bootstrap, cleanup, prune, Docker delete,
  Docker volume delete, or broad DB cleanup;
- executable operator-facing date-scoped delete UI or delete expansion;
- LAN enablement, non-loopback bind, LAN CORS widening, LAN auth/session rollout,
  or deployment;
- import of legacy GUI upload state as a default migration path.

Relationship to source documents:

- `docs/175_legacy_gui_replacement_gap_audit.md` is the gap audit that this plan
  turns into evidence and approval work packages.
- `docs/173_v2_operational_upload_verification_gate.md` defines the operational
  upload evidence chain: inventory, separately approved protected manifest
  preparation, separately approved read-only target-identity preparation plus
  human exact-match review, Preview-only, Start Upload, and Retry Failed.
- `docs/164_operator_data_mutation_safety_gate.md` defines exact approval
  wording and separates read-only checks from local-state writes and DB
  mutations.
- `docs/165_v2_status_matrix.md` classifies deferred V2 items, including LAN,
  executable date-scoped delete UI, delete expansion, operational delete
  verification, and Supabase schema attribution.
- `docs/171_v2_operational_delete_verification_gate.md` is the separate gate for
  any operational destructive delete. This plan only excludes delete or points to
  that package.

## Go/No-Go Decision States

| State | Meaning | Required evidence | Example |
| --- | --- | --- | --- |
| `GO` | V1 Core Ops replacement is approved only for the named package, inventory record, manifest-preparation approval, protected manifest/snapshot, pre-existing verified target baseline, consumed target-identity preparation approval, exact target binding/state/validity/evidence, Preview approval/run, atomic snapshot binding evidence, operator PC, privacy-safe exact-source alias, source class, and evidence window. | All identifiers exactly match the consumed manifest, trusted target chain, succeeded Preview, and same-snapshot Start/Retry evidence when those stages occurred; all required evidence is current; Audit/Job Logs visibility and final sign-off are complete. | Preview consumes the named manifest, reads the protected snapshot, and revalidates the exact target against the trusted baseline; a separately approved Start reads only that same snapshot, no retryable rows remain, and sanitized evidence is reviewed. |
| `CONDITIONAL GO` | Replacement may proceed only inside the same complete package/inventory/manifest/Preview/operator/source bindings and evidence window, with explicit residual risk acceptance. | The same exact lifecycle identifiers required for `GO` are present and equal, all hard stops are clear, and only a named non-core caveat remains with an owner and rollback/stop procedure. | Grafana status is attention-only while the bound API, DB, manifest, Preview, Audit, and upload evidence are normal. |
| `NO-GO` | Replacement must not proceed. | One or more required V1 cutover evidence items failed or is missing. | Large Preview soak fails, Audit Logs do not show failure rows, or target row counts mismatch between UI/API/approval. |
| `BLOCKED` | The decision cannot be made because evidence or approval is unavailable. | The blocker is documented and no workaround is allowed without violating a safety gate. | Operator PC cannot reach the configured local Supabase DB, or package metadata cannot be matched to source commit. |
| `DEFERRED / NOT V1 SCOPE` | Item is intentionally excluded from the V1 cutover decision. | Source document classification shows deferred or excluded status. | Multi-user LAN, executable date-scoped delete UI, Supabase schema attribution migration, and legacy upload state import. |

## WP-02 Evidence Consolidation And Recommendation

Evidence window: 2026-07-13 Asia/Seoul. This version-controlled section is the
sanitized attestation for the listed observations once merged; it does not
replace a missing pre-Preview inventory/approval record, raw execution logs, or
package metadata. It does not fill the human approver fields and does not
approve any future Preview, upload, retry, delete, Settings, runtime lifecycle,
LAN, deployment, migration, reset, cleanup, or data mutation.

| Evidence id | Observation | Result |
| --- | --- | --- |
| `wp02-main-5695b93` | `main` and `origin/main` matched `5695b93802f78f2e04a1aa83662e9400e1d49db2`, containing merged PR #229 and V2 WP-01 PR #230. | Pass |
| `wp02-wp01-automated-5695b93` | Full backend suite previously passed with 437 tests; frontend unit, typecheck, build, and routing checks passed. Representative UTF-8/CP949/integrated fixtures, deterministic 25,000-row Preview soak, DB-status semantics, and Audit failure paths are covered. | Pass |
| `wp02-config-runtime-20260713` | Sanitized config target classes passed and upload/runtime targets were aligned. Docker, WSL, CLI, API, DB, Studio, and Edge were ready with no missing required container. Overall status was `attention` because Grafana was unreachable and Vector unhealthy. | Conditional: core ready, non-core caveat open |
| `wp02-preview-prv_ca38650a9e7d` | Separately approved `folder_all` large-source Preview persisted local run/audit state and completed `succeeded/reachable`: 12 total, 11 already in DB, 1 partial overlap, 0 target, 0 risky, 0 excluded, 0 target rows, 64,766 partial-overlap rows, 3,386,260 DB-matched rows, and Start Upload disabled. Partial-overlap rows are excluded from the target-only upload path. | Preview behavior passed; the run predates `docs/182`, and partial-overlap disposition remains pending |
| `wp02-audit-readonly-20260713` | Read-only Audit API inspection returned existing success, failure, blocked, and cancelled classes; the approved Preview had matching success evidence. No new failure was manufactured. | Pass |
| `wp02-joblogs-readonly-20260713` | Latest Upload Job was terminal `succeeded` with persisted files/events, and Job Logs rendered without browser errors. No job was created. | Pass |
| `wp02-responsive-core-routes-20260713` | Dashboard, Upload Preview, Upload Job, Job Logs, Audit Logs, and Settings passed the existing 390-1440 px backend-served QA with zero layout issues, console errors, or failed requests. | Pass |
| `wp02-safety-exclusions-20260713` | WP-02 performed no Preview creation, Start Upload, Retry Failed, delete, Settings save, runtime start/stop, LAN, deployment, migration, reset, cleanup, or data mutation. | Pass |

Technical recommendation: `NO-GO` for V1 Core Ops cutover execution on the
current evidence set. The implementation and Preview behavior support a future
`CONDITIONAL GO` candidate. `docs/182` binds a later package artifact to a
human-confirmed inventory baseline, but it does not prove the artifact is
installed or executing, supply complete operator/source binding, or
retroactively validate the earlier Preview. Exact executing-package
verification remains downstream of production atomic content-manifest/snapshot
binding retained through Preview, Start, and Retry,
deterministic replacement/concurrency/tamper/replay tests, and a rebuilt package.
After those pass, a separately controlled pre-provisioned verified target
baseline must already exist; then an execution-adjacent successor inventory
record, separately approved protected manifest preparation, separately approved
read-only target-identity preparation and human exact-match review, and a later
separately approved current Preview may be prepared. Baseline provisioning/
rotation is not authorized here. Any required disposition of partial-overlap rows, final sign-off,
and a Grafana/Vector acceptance owner remain pending.

Conditions to reach a `CONDITIONAL GO` candidate:

1. Implement and regression-test atomic content binding so Preview verifies and
   parses a protected immutable snapshot retained through later approved Start/
   Retry actions; those workers must never reopen operational source and any
   pre-mutation mismatch must produce zero DB writes. The current size/mtime
   signature and a separate pre-call scan are insufficient.
2. Build the package containing that implementation and verify its label, ZIP
   hash, and source commit against the artifact the operator will actually run.
3. Confirm an immutable/authenticated owner-only trusted target baseline already
   exists in verified, non-revoked state from separately controlled installation/
   runtime provenance. This plan does not authorize creating or rotating it.
4. Use `docs/182` only as baseline evidence. Repeat the inventory and create a
   successor record bound to a human-supplied safe operator PC class and
   privacy-safe alias for the exact configured source.
5. Under a separate exact approval, atomically claim the immutable/authenticated
   `manifestPreparationApprovalId` and prepare exactly one protected,
   tamper-evident, single-use private content-manifest record bound to that
   approval, successor inventory, and package. Reject concurrent/duplicate
   claims. Do not publish raw identities, paths, filenames, digests, or entries.
6. Under a separate read-only approval, atomically claim
   `targetIdentityPreparationApprovalId`, compare the observed authenticated DB
   instance/database identity to the owner-only trusted baseline, and publish at
   most one opaque `targetDbBindingId`. Human review must confirm exact match,
   prepared state, safe evidence, and unexpired validity; mismatch stops.
7. Issue a later exact Preview approval naming the protected manifest/snapshot,
   trusted baseline, consumed target-identity preparation approval, and prepared
   unexpired target binding.
   Require a human-approved maximum age/deadline, repeat the metadata scan, and
   have Preview atomically claim/verify/consume the record while parsing the
   same immutable bytes.
8. Record human disposition of the 64,766 partial-overlap rows, which remain
   excluded from target-only upload, without treating them as zero unmatched
   local rows.
9. Resolve Grafana/Vector attention or record explicit residual-risk acceptance,
   an owner, and the non-destructive stop/rollback procedure.
10. Complete the final human sign-off record below for the exact package,
   execution-adjacent inventory record id, operator PC class, privacy-safe
   exact-source alias, source class, and evidence window.

The zero-target Preview supports `no target-only upload` for this evidence
window. It does not mean every local row is DB-matched: 64,766 rows are in the
partial-overlap class and remain excluded from Start Upload. No upload or retry
should be created merely to turn a not-applicable gate into a test case.

## Required Cutover Evidence Matrix

| Evidence area | Required artifact | Allowed command or observation class | Forbidden actions | Pass condition | Fail / stop condition | Evidence owner | Source reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Package/source commit verification | Package label, source commit, build metadata, and source tree commit record | Read-only package metadata inspection; `git rev-parse HEAD`; `git show --stat --oneline --name-status HEAD` | Rebuilding, deploying, or editing package metadata during evidence capture | Package source commit and label match the accepted package and docs | Missing, stale, or mismatched package metadata | Maintainer | `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| README/API no-live-smoke and schema contract verification | Contract note proving live Preview/Upload Job POST examples are intentionally absent while backend schema/API retain `previewRunId`, `expectedTargetRows`, and `expectedTargetFiles` | Read-only README, schema, API, and automated-test inspection | Start Upload execution or ad hoc live POST | README keeps live POST commands omitted until the protected runtime lifecycle exists; API source rejects missing/non-positive target rows and automated tests cover missing and positive-count mismatch paths | Live POST example is reintroduced, required fields drift, claimed test coverage exceeds the actual suite, or an ad hoc payload is treated as evidence | Maintainer | `README.md`; `backend/app/api/upload_jobs.py`; `backend/app/schemas/upload_jobs.py`; `tests/backend/test_upload_jobs_api_contract.py` |
| GET `/api/config` safe snapshot | Sanitized config evidence showing source class, target classes, mode, and override classes | `GET /api/config` against an already running local operator backend; store sanitized classes only | `PUT /api/config`, Settings save, raw path or secret capture | Snapshot confirms expected API mode/source class without raw paths or secret values | Config source class is wrong, raw sensitive value would be recorded, or endpoint unavailable | Maintainer/operator | `backend/app/api/config.py`; `backend/app/services/config_service.py`; `README.md` |
| Local Supabase status evidence | Sanitized runtime readiness/status-class output | Read-only dashboard/runtime status observation and existing status endpoints | Start/stop/reset/cleanup/init/migration | Status proves local Supabase readiness class or a clear blocked class | DB-dependent class is blocked and unresolved | Maintainer/operator | `docs/00_product_scope.md`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Local Supabase start/stop evidence, only if separately approved | Operation id, event ids, before/after status classes, and audit ids | Runtime start/stop only after separate approval and no active job/preview | Supabase init/reset, Docker create/rm/prune/up/down, volume deletion | Start/stop is bounded, audited, and returns expected readiness or stopped class | Required containers missing, active job/preview, broad cleanup requested, or audit unavailable | Maintainer/operator | `backend/app/services/runtime_control.py`; `backend/app/services/command_runner.py` |
| Read-only inventory precheck | Filled inventory template with random record id, operator PC class, privacy-safe exact-source alias, counts, row ceiling, excluded data, and reviewer | Read-only file inventory/count procedure that stores no raw names, paths, content, or keys | Preview, upload, delete, settings save, cleanup, LAN, deployment | Exact bindings, file count, and approved physical row ceiling are current and reviewer-signed | Missing/mismatched binding, guessed count, stale inventory, source class mismatch, or raw sensitive evidence | Maintainer with operator review | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md` |
| Protected content-manifest preparation | Approval id, human claim/completion deadline, opaque manifest/snapshot ids, observed/approved bytes, retention/disposition fields, inventory observation/max-age and package/source bindings, safe counts/timestamps, and lifecycle classes | One separately approved protected local full-byte evidence write with pre-authorized bounded disposal after implementation/package/inventory gates pass | Preview, operational DB access, upload, retry, delete, Settings save, runtime lifecycle, source mutation, unbounded/manual snapshot cleanup | Human explicitly acknowledges full-byte copying and automatic cryptographic disposal; claim and completed publication occur before the human deadline within inventory validity; protected capacity/confidentiality controls pass; records are tamper-evident, inventory-bound, unexpired, and single-use; only opaque safe evidence is published | Missing/inferred observation/max-age/deadline or informed scope/byte ceiling/capacity/confidentiality/retention/disposal, late claim/completion, mismatch, tamper, prior claim/use, mutable snapshot, raw private publication, failed disposal without blocking/alert evidence | Backend maintainer with operator approval | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md` |
| Preview-only evidence | Preview approval id, preview run id, inventory/manifest/snapshot record ids, observation/deadline/lifecycle fields, consumed target-identity preparation approval id/deadline, target DB binding id/state/validity/evidence, operator PC class, privacy-safe source alias, final unchanged-snapshot check, opaque atomic snapshot binding evidence id, summary counts, DB status class, audit evidence | Exactly one separately approved Preview-only run after atomic content and exact target-identity binding are implemented/tested, manifest preparation is separately approved, and the target-identity preparation result is human-reviewed | Start Upload, Retry Failed, Delete, Settings save, reset, cleanup, LAN, deployment | Preview atomically claims the protected records before deadline, verifies private digests, parses the same immutable snapshot, revalidates the protected exact target identity and unexpired validity on its DB session, and terminally consumes the manifest while retaining the snapshot/target binding for later approved actions; it then succeeds with DB reachable | Manifest/snapshot, atomic binding, target-identity preparation approval, or target DB binding unavailable, expired/reused/tampered/mismatched, same-host/port target replacement, failed unchanged-snapshot check, risky count > 0, DB unreachable, stale preview, or conflict unresolved | Maintainer/operator | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_preview.py`; `backend/app/services/upload_preview.py` |
| Start Upload approval package, separate and optional | Immutable/authenticated single-use approval naming package/operator/source, Preview run, exact target rows/files, protected exact target DB binding, deadline, duration/margin, snapshot/binding ids, and one mutation id | Approval preparation only after lifecycle/target-fenced lease, exact DB-identity binding, durable outcome-marker implementation/tests, and fresh Preview | Running Start Upload from this plan; source-path reopen; replay/concurrent claim; bundling Retry Failed/Delete/Settings save | Approval and `previewed` snapshot are atomically claimed with one upload job, unrenewable lease, target DB binding, and mutation id; exact target identity is revalidated and all action writes plus commit marker share one authoritative target transaction; local state releases only from marker evidence | Zero target rows, stale/mismatched Preview, missing/substituted target DB binding or same-port target swap, absent lifecycle/fence/marker, insufficient retention margin, expired/substituted/replayed approval, missing/tampered snapshot, source reopen, non-atomic job creation, `commit_unknown_blocked`, or disposition/lease race | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_jobs.py` |
| Retry Failed approval package, separate and conditional | Immutable/authenticated single-use approval naming package/operator/source, source job, fresh reconciled still-absent subset, protected exact target DB binding, failure class, deadline, duration/margin, snapshot/binding ids, and one mutation id | Approval preparation only after lifecycle/target-fenced lease, exact DB-identity binding, durable outcome-marker implementation/tests, authoritative rollback, and fresh exact DB reconciliation | Automatic retry, worker-cursor remainder, source-path reopen, broad cleanup, reset, replay/concurrent claim, target-binding substitution, or retry without exact reconciled rows | Approval and same `retryable` snapshot subset are atomically claimed with one retry job/event, unrenewable lease, target DB binding, and mutation id; exact target identity is revalidated and all retry writes plus commit marker share one authoritative target transaction; local state releases only from marker evidence | No retryable rows, target DB binding/identity mismatch, count/reconciliation/failure mismatch, absent lifecycle/fence/marker, insufficient retention margin, expired/substituted/replayed approval, missing/tampered snapshot, source reopen, non-atomic retry creation, `commit_unknown_blocked`, or disposition/lease race | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_jobs.py`; `frontend/src/pages/UploadPage.tsx` |
| Audit Logs success/failure visibility | Sanitized Audit Logs API/UI evidence for success, failure, and blocked classes | `GET /api/audit?limit=1`; UI Audit Logs observation; non-destructive failure-path validation | Raw params JSON search, arbitrary SQL, secret capture, destructive failure creation | Operators can see relevant safe action/result/reason evidence | Audit unavailable, missing failure rows, unsafe raw values displayed | Maintainer QA and operator | `backend/app/api/audit.py`; `backend/app/db/audit_repository.py`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Job Logs visibility | Upload Job tab or API event evidence for latest job states | Read-only job/detail/event observation; SSE replay observation | Creating upload/retry jobs without approval | Job events and final states are visible and understandable | Missing events, final status unclear, or errors hidden | Maintainer QA and operator | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/pages/UploadPage.tsx`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Representative legacy CSV fixture coverage | Test or review evidence for known legacy edge cases | Non-operational fixture tests or Preview-only fixture evidence in disposable/non-production context | Operational upload mutation; raw operational CSV content in evidence | Representative fixtures cover expected legacy parsing/classification cases | Known legacy CSV shape untested or classification drift found | Maintainer QA | `docs/01_development_roadmap.md`; `docs/175_legacy_gui_replacement_gap_audit.md`; `docs/00_product_scope.md` |
| Large real CSV Preview soak | Preview-only soak evidence with sanitized counts and timing | Only after atomic content binding implementation/tests, rebuilt-package verification, and separate Preview-only approval for the real source class | Start Upload, Retry Failed, Delete, cleanup, raw file evidence | Large Preview consumes the same immutable content it verified, completes within accepted bounds, and produces stable classifications | Atomic binding unavailable, timeout, memory failure, risky rows, DB unreachable, or count mismatch | Maintainer/operator | `docs/01_development_roadmap.md`; `docs/175_legacy_gui_replacement_gap_audit.md`; `docs/173_v2_operational_upload_verification_gate.md` |
| Operator-PC browser/UI evidence | Sanitized route screenshots or observations for `/`, `/upload`, `/logs`, `/settings` | Browser route load checks against already running local package; screenshots only after redaction review | Capturing secrets, raw paths, filenames, DB URLs, tokens, internal URLs, CSV content | Routes load in API mode and show expected readiness/log surfaces | Route unavailable, mock mode mistaken as operational, or sensitive data visible | Maintainer/operator | `backend/app/main.py`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Rollback / stop procedure evidence | Runbook record for stopping app use and reverting to legacy GUI/manual procedure | Documentation review and operator acknowledgement | DB reset/cleanup as rollback; deleting evidence | Stop procedure is understood and no destructive cleanup is required | Rollback depends on destructive cleanup or unavailable legacy fallback | Release owner/operator | `docs/173_v2_operational_upload_verification_gate.md`; `docs/171_v2_operational_delete_verification_gate.md`; `README.md` |
| Destructive delete exclusion | Explicit exclusion from this V1 cutover decision | Documentation-only exclusion | Any operational DB delete from this plan; importing a separate delete run as cutover evidence | No delete ran or is authorized by this cutover; any future delete uses a completely separate hardened plan and sign-off | Request bundles or credits delete with Preview/Start/Retry/settings/reset/LAN | Release owner/operator | `docs/171_v2_operational_delete_verification_gate.md`; `docs/164_operator_data_mutation_safety_gate.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| LAN exclusion | Localhost-only sign-off | Config/doc review; `/api/health` sanitized LAN state if available | LAN enablement, non-loopback bind, LAN CORS widening, auth/session rollout | V1 remains localhost-only and LAN stays deferred | Non-loopback access requested or LAN feature gate enabled | Release owner | `docs/00_product_scope.md`; `backend/app/core/lan_security.py`; `docs/165_v2_status_matrix.md` |
| Supabase reset/cleanup exclusion | Explicit exclusion record | Documentation review and command-policy review | `supabase init`, `supabase db reset`, Docker rm/prune/compose up/down, volume delete | No reset/cleanup/create command is part of cutover evidence | Missing containers trigger cleanup request instead of blocked evidence | Release owner/maintainer | `README.md`; `backend/app/services/command_runner.py` |
| Security/secrets redaction | Sanitized evidence review checklist | Redaction review before attaching evidence | Raw paths, filenames, CSV content, DB URLs, tokens, JWTs, Authorization values, exact keys, internal URLs, secrets | Evidence contains only path-independent ids, safe classes/counts, approved package hashes, and reason codes | Sensitive value or a deterministic raw-path-derived digest would be written, or screenshot cannot be safely redacted | Maintainer/security reviewer | `README.md`; `backend/app/db/audit_repository.py`; `docs/171_v2_operational_delete_verification_gate.md` |
| Final sign-off record | Completed decision-conditional sign-off table with all package/inventory/manifest/Preview/operator/source fields, blockers, residual risks, and next action | Documentation-only sign-off | Treating old evidence, reused manifest state, future folder growth, or successful intermediate evidence as cutover approval | `GO`/`CONDITIONAL GO` requires exact complete bindings; stop/defer decisions preserve actual ids/states for stages reached and use explicit unavailable markers only for stages not reached, while decision metadata and reasons remain mandatory | A proceed decision has any missing/invalid/mismatched field, or a stop/defer record erases/fabricates observed evidence or omits mandatory decision data | Release owner/operator approver | `docs/173_v2_operational_upload_verification_gate.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |

## Non-Destructive Validation Package

These validations can be prepared or run without mutation approval when they only
observe an already running local operator package and store sanitized output.

Allowed read-only commands or observations:

```powershell
git rev-parse HEAD
git status --short --branch
git show --stat --oneline --name-status HEAD
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health |
  ConvertTo-Json -Depth 8
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/config |
  ConvertTo-Json -Depth 8
```

Store only sanitized source classes, target classes, modes, override classes,
safe booleans, and non-secret status fields from `/api/config`. Do not store raw
source paths, DB URLs, anon keys, service role values, tokens, JWTs, or
Authorization values.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?limit=1" |
  ConvertTo-Json -Depth 8
```

```powershell
Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/upload -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/logs -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/settings -UseBasicParsing
```

Docs-disabled route checks, when the package is in operator launcher mode:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/docs -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/openapi.json -UseBasicParsing
```

Expected result is disabled or unavailable docs in operator mode, not secret or
token output.

Not allowed in this package:

- creating a Preview run;
- cancelling a Preview run;
- starting upload jobs;
- retrying failed upload jobs;
- upload delete preflight/start/reconcile;
- Settings save;
- Local Supabase start/stop;
- Supabase init/reset/migration/backfill/cleanup;
- Docker create/rm/prune/volume delete/compose up/down;
- LAN enablement or non-loopback testing;
- production DB mutation.

## Read-Only Inventory Precheck Template

Use this template only after atomic content binding implementation/tests and
rebuilt-package verification pass, and before requesting Preview-only approval.
It records counts and classes, not raw operational data.

| Field | Value |
| --- | --- |
| Inventory evidence record id | `<inventoryEvidenceRecordId>` |
| Inventory observed at UTC | `<inventoryObservedAtUtc>` |
| Human-approved maximum age in seconds | `<inventoryMaxAgeSeconds>` |
| Preview execution deadline UTC | `<previewExecuteByUtc>` |
| Operator PC class | `<operatorPcClass>` |
| Package source commit | `<sourceCommit>` |
| Package label | `<packageLabel>` |
| Privacy-safe exact-source alias | `<sourceAlias>` |
| Source class, not raw path | `<sourceClass>` |
| Observed file count | `<fileCount>` |
| Approved physical row ceiling | `<rowLimit>` |
| Observed source bytes | `<inventoryObservedBytes>` |
| Human-approved full-byte snapshot ceiling | `<contentSnapshotMaxBytes>` |
| Excluded data | `<excludedDataClasses>` |
| Stop condition result | `<clear \| blocked: reason>` |
| Reviewer | `<reviewer>` |

Do not record raw filenames, raw paths, raw CSV content, raw timestamp/device_id
keys, DB URLs, tokens, JWTs, Authorization values, internal URLs, or secrets.
The record id must be random and path-independent. Do not publish a
deterministic hash or fingerprint derived from a raw path; it can disclose the
path through candidate-path guessing. The human must confirm out of band that
the privacy-safe source alias maps to the exact configured source.

## Protected Content-Manifest Preparation Template

This is a separate local evidence write after the implementation/tests, rebuilt
package verification, and fresh inventory pass. It copies all approved
operational CSV bytes into protected immutable storage, not only hashes or
metadata. It is not read-only and requires its own exact human approval. It does
not approve Preview.

```text
The manifest-preparation approval id is <manifestPreparationApprovalId> and both claim and completed protected publication must occur by <manifestPreparationExecuteByUtc>.
I approve exactly one protected local content-manifest plus full-byte immutable snapshot preparation from package sourceCommit <sourceCommit> for inventory record <inventoryEvidenceRecordId>.
That inventory was observed at <inventoryObservedAtUtc> and is approved for at most <inventoryMaxAgeSeconds> seconds; the preparation deadline above is within that window.
The approved operator PC class is <operatorPcClass>, source alias is <sourceAlias>, source class is <sourceClass>, expected files is <fileCount>, expected physical rows is <= <rowLimit>, and full-byte snapshot size is <= <contentSnapshotMaxBytes> bytes.
The snapshot may be read only by the later separately approved Preview/Start/Retry chain and only until <contentSnapshotRetainUntilUtc>.
I approve automatic bounded cryptographic disposal at terminal chain completion (zero-target Preview or completed Start/Retry), invalidation, or that deadline, whichever occurs first: stop active access, clear buffers, destroy the per-snapshot encryption key first, remove the byte file, verify absence, and record <snapshotDispositionEvidenceId>. A failed removal must leave keyless bytes unreadable, alert the operator, block new snapshot preparation, and retry idempotently only for the same record.
I acknowledge that this write stores a confidential complete copy of the approved operational CSV bytes in owner-restricted protected storage.
This approval permits only that protected manifest/snapshot write and its bounded automatic disposal described above. It does not approve Upload Preview, Start Upload, Retry Failed, Delete, Settings save, DB access, runtime lifecycle, source mutation, any other cleanup, LAN, or deployment.
```

The approval id must resolve to an immutable/authenticated protected approval
record, not an arbitrary request string or Markdown alone. Creation atomically
claims it once, rejects duplicate/concurrent claims, and ends `consumed` with one
manifest and one immutable exact-byte snapshot or `invalid` on failure. The
claim and completed publication must both occur by the human-supplied
`manifestPreparationExecuteByUtc`, no later than inventory expiry. An expired
claim fails before copying; expiry during copying invalidates and disposes any
partial bytes without publishing `prepared`. The
private records bind that approval plus canonical file identities/content
digests and snapshot bytes to the inventory/package/operator/source/scope in an
owner-restricted, confidentiality-protected, tamper-evident protected store with
capacity verified before copying. Publish only:

| Field | Value |
| --- | --- |
| Manifest-preparation approval id | `<manifestPreparationApprovalId>` |
| Manifest-preparation claim/completion deadline UTC | `<manifestPreparationExecuteByUtc>` |
| Manifest-preparation approval terminal state | `<consumed \| invalid>` |
| Protected content manifest record id | `<contentManifestRecordId>` |
| Protected immutable content snapshot record id | `<contentSnapshotRecordId>` |
| Content snapshot state | `<prepared \| invalid>` |
| Observed/approved snapshot bytes | `<inventoryObservedBytes> / <contentSnapshotMaxBytes>` |
| Snapshot retention deadline UTC | `<contentSnapshotRetainUntilUtc>` |
| Snapshot disposition state | `<scheduled \| in_progress \| disposed \| disposal_failed_blocked>` |
| Snapshot disposition evidence id | `<snapshotDispositionEvidenceId \| not_triggered>` |
| Inventory evidence record id | `<inventoryEvidenceRecordId>` |
| Prepared at UTC | `<contentManifestPreparedAtUtc>` |
| Preview execution deadline UTC | `<contentManifestExecuteByUtc>` |
| Safe binding/count result | `<match \| blocked: reason>` |
| Lifecycle state | `<prepared \| invalid>` |

Raw paths, filenames, identities, content digests, manifest entries, snapshot
bytes, and store authentication material must remain private and confidential.
Stop on insufficient protected capacity, missing confidentiality/access control,
missing observation/max-age/preparation-deadline binding, late claim/completion,
missing retention/disposition policy, tamper, mismatch, expiry, prior claim/use,
or inability to prove the lifecycle. The exact preparation approval must
pre-authorize the bounded key-destruction/file-removal lifecycle and safe
`snapshotDispositionEvidenceId`; manual or unbounded cleanup is not approved.
Follow the stage transition table in `docs/173`: before Preview claim the
preparation and target-identity preparation approvals are `consumed`, manifest,
snapshot, and target DB binding are `prepared`, and Preview approval is
`available`; during Preview the manifest, target binding, and Preview approval
are claimed. Preview success consumes the manifest/approval and leaves the
snapshot/target binding `previewed` for later separately approved actions. A
post-claim Preview failure invalidates the claimed chain without changing either
already-consumed preparation approval.

## Protected Target-Identity Preparation Template

Inventory performs no DB query and manifest preparation approves no DB access.
After snapshot preparation and before Preview approval, use this separate
single-use read-only approval; do not infer or guess a target binding.
This plan does not authorize trusted-baseline creation or rotation. If the
pre-existing verified baseline is absent, stop and require a separate security-
reviewed installation/provisioning work package and explicit approval.

```text
The target-identity preparation approval id is <targetIdentityPreparationApprovalId>; claim and protected publication must complete by <targetIdentityPreparationExecuteByUtc>.
I approve exactly one read-only target-identity preparation for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, inventory <inventoryEvidenceRecordId>, manifest <contentManifestRecordId>, snapshot <contentSnapshotRecordId>, and configured safe target class <targetClassStatus>.
The expected exact target is anchored by pre-existing protected baseline <trustedTargetBaselineId> in state <trustedTargetBaselineState>, human-reviewed privacy-safe alias <trustedTargetAlias>, and safe out-of-band verification evidence <trustedTargetBaselineEvidenceId>. This preparation may not create, replace, or self-attest that baseline from the first DB observation.
The baseline/evidence ids must be random, opaque, path-independent, and not derived from DB URL, cluster/system id, database name, or other target material; the alias must be human-supplied and not a deterministic target derivative. Exact identity and all keyed integrity values remain owner-only.
This approval binds exact-target singleton coordinator <targetGlobalCoordinatorId> as either the existing coordinator for that trusted identity or the one pre-reserved random id that exact-match publication may uniqueness-CAS-create. It may not create a sibling coordinator.
The resulting opaque target DB binding may remain valid only until <targetDbBindingValidUntilUtc>, no later than snapshot retention <contentSnapshotRetainUntilUtc>.
This approval permits only authenticated DB-instance/database identity metadata read and one protected local evidence/audit write. It does not approve operational table row/key queries, Upload Preview, Start Upload, Retry Failed, Delete, Settings save, DB mutation, runtime lifecycle, cleanup, LAN, or deployment.
```

Before any DB connection/read, production code must atomically claim the
immutable/authenticated approval once, record opaque owner
`targetIdentityPreparationClaimId` and monotonic
`targetIdentityPreparationFence`, and recheck the deadline and already verified/
non-revoked trusted baseline. Only that token/fence holder may perform one bounded
identity read. Publication must compare the observed authenticated exact identity
to its owner-only expected identity and CAS-recheck the same claim id/fence,
`claimed` state, deadline, baseline state/evidence, and approval bindings before
publishing at
most one opaque random owner-only binding, return the same record on response
loss without another DB read, and advance the fence/end `invalid` on pre-
publication crash/restart/expiry/invalidation, missing/revoked baseline, first-observation wrong DB,
mismatch/expiry/failure. Exact identity and
versioned domain-separated keyed integrity material remain owner-only. Human
review of this safe result is required before Preview approval:

| Field | Value |
| --- | --- |
| Target-identity preparation approval id | `<targetIdentityPreparationApprovalId>` |
| Claim/publication deadline UTC | `<targetIdentityPreparationExecuteByUtc>` |
| Approval terminal state | `<consumed \| invalid>` |
| Claim owner id/fence | `<targetIdentityPreparationClaimId> / <targetIdentityPreparationFence>` |
| Exact-target singleton coordinator id/state/generation/evidence | `<targetGlobalCoordinatorId> / <idle \| terminal \| invalidated_terminal> / <targetGlobalCoordinatorGeneration> / <targetGlobalCoordinatorEvidenceId>` |
| Trusted target baseline id/alias/state/evidence | `<trustedTargetBaselineId> / <trustedTargetAlias> / <verified \| revoked \| invalid> / <trustedTargetBaselineEvidenceId>` |
| Protected exact target DB binding id | `<targetDbBindingId>` |
| Target DB binding state | `<prepared \| invalid>` |
| Target DB binding validity UTC | `<targetDbBindingValidUntilUtc>` |
| Safe target DB binding evidence id | `<targetDbBindingEvidenceId>` |
| Configured safe target class | `<targetClassStatus>` |

Tests must cover every binding/deadline/trusted-baseline/alias/evidence
substitution, concurrent/replay claims, owner/fence substitution, failure before/
after claim/read/publication, response-loss recovery without a second read,
restart/expiry/invalidation racing a delayed reader/publisher, same-host/port cluster or database swap before
first observation and after binding, wrong DB present at first observation,
missing/revoked/rotated baseline, candidate-enumeration resistance for baseline/
evidence ids and alias, private
identity/all keyed-integrity-value redaction, cross-chain reuse, and zero
operational-table reads/DB writes.

## Preview-Only Approval Template

This approval is separate from the validation plan. It must be filled from a
fresh read-only inventory precheck and the later protected manifest-preparation
result.

```text
The Preview approval id is <previewApprovalId> and it binds manifest-preparation approval <manifestPreparationApprovalId>.
It binds pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId>.
It also binds consumed target-identity preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and prepared target DB binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>.
It binds singleton exact-target coordinator <targetGlobalCoordinatorId> in expected state <idle | terminal | invalidated_terminal>, expected owner <targetGlobalCoordinatorOwnerFenceId or none>, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, safe evidence <targetGlobalCoordinatorEvidenceId>, and pre-reserved next chain fence <targetOperationFenceId>. Preview claim must atomically CAS that generation and install only that fence; any nonterminal older chain or stale owner/generation must fail.
I approve exactly one Upload Preview-only run from package sourceCommit <sourceCommit>.
The approved inventory record is <inventoryEvidenceRecordId> on operator PC class <operatorPcClass>.
The approved protected content manifest is <contentManifestRecordId>, prepared at <contentManifestPreparedAtUtc>, and it must be consumed no later than <contentManifestExecuteByUtc>.
The approved immutable content snapshot is <contentSnapshotRecordId> in state prepared.
Its approved maximum size is <contentSnapshotMaxBytes> bytes, it may be read only until <contentSnapshotRetainUntilUtc>, and its disposition state is scheduled.
The approved source alias is <sourceAlias>.
The approved source class is <sourceClass>.
The approved file count is <fileCount>.
The approved physical row ceiling is <rowLimit>.
The approved exact operational DB target is protected binding <targetDbBindingId>; safe target/readiness classes do not replace it.
The inventory was observed at <inventoryObservedAtUtc>, its approved maximum age is <inventoryMaxAgeSeconds> seconds, and Preview must start no later than <previewExecuteByUtc>.
This approval does not approve Start Upload, Retry Failed, Delete, Settings save,
feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN, or deployment.
```

Immediately before the API call, repeat the read-only scan and record only the
safe check timestamp plus `preCallSnapshotUnchanged=true`. Stop if the deadline
or maximum age is exceeded, or if the exact file set, scope, size/mtime metadata,
file count, physical-row ceiling, package, operator PC class, source alias, or
source class differs from the approved inventory evidence.

Do not call Preview under the current implementation. The separate metadata
check does not prevent replacement after the check or equal-size/equal-mtime
content substitution. Production Preview must first verify the approved
content-based manifest and parse the same protected immutable snapshot retained
for later approved actions, with deterministic regression coverage.
For positive target rows it must also persist the exact distinct target-only
keyset inside that snapshot's protected encrypted boundary, expose only
`actionApprovedAbsentSetBindingId` plus exact
`actionApprovedAbsentKeyCount`, and dispose the private set with the snapshot.

## Preview-Only Evidence Template

| Field | Value |
| --- | --- |
| Preview approval id | `<previewApprovalId>` |
| Preview approval terminal state | `<consumed \| invalid>` |
| Preview run id | `<previewRunId>` |
| Inventory evidence record id | `<inventoryEvidenceRecordId>` |
| Manifest-preparation approval id | `<manifestPreparationApprovalId>` |
| Manifest-preparation approval terminal state | `<consumed>` |
| Protected content manifest record id | `<contentManifestRecordId>` |
| Protected immutable content snapshot record id | `<contentSnapshotRecordId>` |
| Content snapshot terminal state after Preview | `<previewed \| invalid>` |
| Snapshot retention deadline UTC | `<contentSnapshotRetainUntilUtc>` |
| Snapshot disposition state | `<scheduled \| in_progress \| disposed \| disposal_failed_blocked>` |
| Snapshot disposition evidence id | `<snapshotDispositionEvidenceId \| not_triggered>` |
| Content manifest prepared at UTC | `<contentManifestPreparedAtUtc>` |
| Content manifest execution deadline UTC | `<contentManifestExecuteByUtc>` |
| Content manifest terminal state | `<consumed \| invalid>` |
| Inventory observed at UTC | `<inventoryObservedAtUtc>` |
| Approved maximum age in seconds | `<inventoryMaxAgeSeconds>` |
| Preview execution deadline UTC | `<previewExecuteByUtc>` |
| Final snapshot check observed at UTC | `<preCallSnapshotCheckObservedAtUtc>` |
| Final snapshot unchanged | `<preCallSnapshotUnchanged>` |
| Atomic snapshot binding evidence id | `<atomicSnapshotBindingEvidenceId>` |
| Protected target-only absent-set binding/distinct-key count | `<actionApprovedAbsentSetBindingId> / <actionApprovedAbsentKeyCount> \| not_created for zero target>` |
| Operator PC class | `<operatorPcClass>` |
| Privacy-safe exact-source alias | `<sourceAlias>` |
| Source class | `<sourceClass>` |
| Status | `<succeeded \| failed \| blocked \| cancelled>` |
| Total files | `<totalFiles>` |
| Target files | `<targetFiles>` |
| Already-in-DB count | `<alreadyInDbCount>` |
| Partial-overlap count | `<partialOverlapCount>` |
| Risky count | `<riskyCount>` |
| Target-only rows | `<targetRows>` |
| Partial-overlap rows | `<partialOverlapRows>` |
| DB status class | `<dbStatusClass>` |
| Runtime readiness class | `<runtimeReadinessClass>` |
| Target-identity preparation approval id/state/deadline/claim owner/fence | `<targetIdentityPreparationApprovalId> / <consumed \| invalid> / <targetIdentityPreparationExecuteByUtc> / <targetIdentityPreparationClaimId> / <targetIdentityPreparationFence>` |
| Trusted target baseline id/alias/state/evidence | `<trustedTargetBaselineId> / <trustedTargetAlias> / <verified> / <trustedTargetBaselineEvidenceId>` |
| Protected exact target DB binding id | `<targetDbBindingId>` |
| Target DB binding state/validity/evidence | `<previewed when positive target rows await Start \| upload_completed_delete_ready when zero target but eligible already_in_db Delete branch remains \| completed after all branches terminal/excluded \| invalid> / <targetDbBindingValidUntilUtc> / <targetDbBindingEvidenceId>` |
| Exact-target global coordinator id/state/owner/consumer/generation/evidence | `<targetGlobalCoordinatorId> / <chain_ready \| terminal \| invalidating \| invalidated_terminal> / <targetOperationFenceId> / <targetGlobalCoordinatorConsumer> / <targetGlobalCoordinatorGeneration> / <targetGlobalCoordinatorEvidenceId>` |
| Target operation fence id/chain state/upload branch/Delete branch/consumer/generation/evidence | `<targetOperationFenceId> / <idle \| terminal \| invalid> / <preview_ready \| terminal \| not_eligible \| invalid> / <delete_preflight_ready \| terminal \| not_eligible \| invalid> / <empty> / <targetOperationFenceGeneration> / <targetOperationFenceEvidenceId>` |
| Audit evidence | `<auditEvidenceId>` |
| Confirmation no mutation actions were bundled | `<yes/no plus note>` |

Pass requires unexpired inventory and manifest deadlines, immutable/authenticated
approval records, unchanged `manifestPreparationApprovalId` and
trusted target baseline id/alias/state/evidence,
`targetIdentityPreparationApprovalId`/`previewApprovalId` across all stages, all
three approvals terminally `consumed`, and
 a protected manifest atomically claimed and terminally marked `consumed`,
 an immutable snapshot with stage state `previewed`,
`preCallSnapshotUnchanged=true`, a valid opaque
`atomicSnapshotBindingEvidenceId`, `status=succeeded`, DB reachable/expected,
one protected exact `targetDbBindingId` revalidated unexpired against the owner-
only expected trusted baseline on the Preview DB session,
`riskyCount=0`, matching counts across UI/API/evidence, and—when target rows are
positive—one protected exact target-only distinct-set binding. A count-only or
reconstructed/substituted set is invalid.
If target rows are zero, the upload branch is terminal and disposition must reach
`disposed` with valid `snapshotDispositionEvidenceId`, and target DB binding
state is `upload_completed_delete_ready` only while an independently eligible,
separately gated Delete branch remains; a cutover proceed decision requires that
branch explicitly excluded/terminal and binding `completed`. Delete may never
reuse the disposed upload snapshot. If target rows are
positive, disposition remains `scheduled` only until the later separately
approved Start/Retry chain completes or the retention deadline triggers, and
target DB binding state remains `previewed` until that next claim.
A Preview with zero target rows may
support `no target-only upload`; it is not proof that partial-overlap rows are
absent and it is not Start Upload evidence.

## Start Upload Approval Template

This is separate and not approved by this validation plan. Request it only after
a fresh, succeeded Preview-only run proves exact target-only rows and production
code/tests provide an immutable/authenticated, expiring, single-use Start
approval record atomically claimed with the `previewed` immutable snapshot and
upload-job creation. The worker must use only that snapshot and never reopen the
operational source.
Follow the Start transition table in `docs/173`: `invalid` is allowed only when
no job commits; once one job commits the approval remains `consumed` regardless
of response loss or later job outcome.

```text
The Start Upload approval id is <startUploadApprovalId> and it must be claimed by <startUploadExecuteByUtc>.
I approve exactly one Start Upload for preview run <previewRunId> with target files <targetFiles> and target rows <targetRows>.
The protected exact target-only set binding is <actionApprovedAbsentSetBindingId> with distinct keys <actionApprovedAbsentKeyCount>.
This approval is for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, source alias <sourceAlias>, and source class <sourceClass>.
It binds the same pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId> used by Preview.
It binds protected target operation fence <targetOperationFenceId> in chain state idle, upload branch preview_ready, with exact generation <targetOperationFenceGeneration> and safe evidence <targetOperationFenceEvidenceId>. Job creation must atomically claim that generation for consumer start; a concurrent Delete preflight or any stale/terminal generation must fail.
It binds exact-target singleton coordinator <targetGlobalCoordinatorId>, sole owner fence <targetOperationFenceId>, state chain_ready, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>. Job creation must atomically claim both generations for consumer start; any different Preview-chain owner or concurrent target consumer must fail.
The approved exact operational DB target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. It must be unexpired and revalidated on the authoritative target transaction; safe target/readiness classes do not replace it.
It is bound to immutable content snapshot <contentSnapshotRecordId> and atomic snapshot binding evidence <atomicSnapshotBindingEvidenceId> from that Preview.
That snapshot may be read only until <contentSnapshotRetainUntilUtc>; this approval does not authorize snapshot deletion or extend retention.
The action maximum duration is <actionMaxDurationSeconds> seconds and the required disposition margin is <snapshotDispositionMarginSeconds> seconds. Job creation must atomically create one unrenewable snapshot action lease whose expiry is claim time plus that duration and whose expiry plus that margin is no later than both <targetDbBindingValidUntilUtc> and <contentSnapshotRetainUntilUtc>, and claim the pre-reserved <actionMutationId>.
The random unique actionMutationId above is pre-reserved in this immutable approval and may only be claimed with this approval, snapshot, exact subset, duration, margin, lease, and job.
As part of that one Start action, I approve creation of exactly one target-side prepared outcome/fence marker for the same actionMutationId before any all_metrics write; it authorizes no other DB mutation. Every action write and the prepared-to-committed marker transition must share one authoritative target transaction; a guarded prepared-to-aborted finalization may occur only after non-commit is authoritative.
That transaction must first revalidate the exact target identity and unexpired target binding using the authoritative target DB clock, then serializably revalidate every key in the protected approved-absent set, use canonical key fences honored by every application writer and conflict-rejecting conditional inserts, and commit only if the exact inserted keyset/count equals the binding. Any expired/substituted target, preexisting/concurrent key, or mismatch must roll back every action all_metrics write without overwrite and require a fresh Preview and approval.
I approve bounded read-only target-outcome reconciliation for that same actionMutationId within this window and, only if its immutable aborted marker is finalized and observed before lease expiry, exactly one whole-attempt exact DB reconciliation plus protected retry-reconciliation evidence record. Timeout, response loss, or lease expiry must become commit_unknown_blocked unless the immutable target marker proves committed or aborted/complete rollback.
This authorization explicitly excludes Start target-absence drift/conflict. For that failure class the reconciliation-creation entitlement must become invalid, no reconciliation DB read or record is allowed, and a fresh Preview/manifest/snapshot approval chain is required.
Any eligible reconciliation must atomically claim the source action's unique single-use creation entitlement before any DB read, durably recording and binding its source action class, safe terminal failure class, owner claim id, monotonic fence, and absolute publication deadline no later than the source lease, target-binding validity, and snapshot boundaries. Publication must compare-and-set that exact eligible action/failure class, unexpired token/fence, the same unexpired target binding, and current rollback/snapshot/disposition state; invalidation advances the fence, so a delayed publisher cannot succeed. Duplicate or response-loss recovery may return only the same record. Its exact private subset must remain owner-only, tamper-evident, per-record encrypted, use the named snapshot retention deadline as its non-extendable access ceiling, and be cryptographically disposed earlier on terminal Retry, invalidation, expiry, or snapshot disposition.
This approval does not approve Retry Failed, Delete, Settings save, or feature gate enablement.
```

Required before approval:

- fresh succeeded Preview-only evidence;
- preview run id;
- exact target-only rows;
- exact target file count;
- protected exact target-only `actionApprovedAbsentSetBindingId` and distinct
  `actionApprovedAbsentKeyCount` produced by the same Preview;
- the same verified/non-revoked trusted target baseline id/alias/state/evidence
  reviewed before Preview;
- protected target operation fence id is in chain state `idle`, upload branch
  `preview_ready`, Delete unowned, and its exact generation/evidence is bound for
  atomic Start claim with the approval/snapshot/job;
- consumed target-identity preparation approval id/state/deadline and protected
  exact `targetDbBindingId`/state/validity/evidence produced/verified by the same
  Preview; the binding is `previewed`, unexpired, and revalidated on each Start/
  marker/reconciliation DB session/transaction;
- operator PC class and privacy-safe source alias;
- source class;
- package source commit;
- protected immutable content snapshot record id in state `previewed` and the
  matching atomic snapshot binding evidence id;
- snapshot retention deadline has not passed and disposition is `scheduled`;
- human-approved action maximum duration plus exact
  `snapshotDispositionMarginSeconds` fits before both the target-binding and
  snapshot-retention deadlines; the action lease plus that margin ends no later
  than their minimum, and a
  random unique `actionMutationId` is pre-reserved in the immutable approval and
  can be claimed with an unrenewable target-fenced DB mutation lease atomically
  with the job;
- confirmation partial-overlap rows are not included unless separately approved;
- confirmation `expectedTargetRows` and `expectedTargetFiles` match the latest
  Preview detail.
- protected Start approval state is `available` and its package/operator/source/
  Preview/count/deadline/snapshot/atomic-evidence bindings are exact;
- deterministic tests prove source replacement after Preview, equal-size/equal-
  mtime replacement, concurrent writes, missing/tampered snapshots, and worker
  source-reopen attempts cannot change uploaded bytes and produce zero DB writes
  on any pre-mutation mismatch; they also reject substituted/duplicate/cross-
  approval/cross-snapshot mutation ids and exercise the post-commit/pre-release
  crash window, target insert after Preview and during the transaction, same-
  count key substitution, missing writer fence, serialization/unique conflicts,
  and any path that could overwrite or retain partial action writes. They must
  also bind/substitute the reconciliation source action/failure class and prove
  Start target-absence drift/conflict permits zero reconciliation DB reads or
  record publication and requires a fresh chain. They must reject a missing/
  substituted target DB binding and same-loopback/same-port cluster/database
  replacement before Preview, Start, target marker, or reconciliation. They also
  cover target-binding expiry immediately before/at/after atomic claim, marker,
  transaction, and reconciliation, and reject a lease/publication deadline beyond
  the minimum target-binding/snapshot ceiling.

## Start Upload Evidence Template

| Field | Value |
| --- | --- |
| Start approval id | `<startUploadApprovalId>` |
| Start approval deadline UTC | `<startUploadExecuteByUtc>` |
| Start approval terminal state | `<consumed \| invalid>` |
| Preview run id | `<previewRunId>` |
| Protected immutable content snapshot record id | `<contentSnapshotRecordId>` |
| Content snapshot terminal state | `<upload_bound \| retryable \| completed \| invalid>` |
| Snapshot retention deadline UTC | `<contentSnapshotRetainUntilUtc>` |
| Snapshot disposition state | `<scheduled \| in_progress \| disposed \| disposal_failed_blocked>` |
| Snapshot disposition evidence id | `<snapshotDispositionEvidenceId>` |
| Atomic snapshot binding evidence id | `<atomicSnapshotBindingEvidenceId>` |
| Action maximum duration seconds | `<actionMaxDurationSeconds>` |
| Snapshot disposition margin seconds | `<snapshotDispositionMarginSeconds>` |
| Snapshot action lease id | `<snapshotActionLeaseId>` |
| Snapshot action lease expiry UTC | `<snapshotActionLeaseExpiresAtUtc>` |
| Snapshot action lease terminal state | `<released_committed \| released_rolled_back \| expired_rolled_back \| commit_unknown_blocked>` |
| Action mutation id | `<actionMutationId>` |
| Action mutation outcome/evidence id | `<committed \| rolled_back \| commit_unknown_blocked> / <actionMutationOutcomeEvidenceId>` |
| Protected approved-absent set binding/distinct-key count | `<actionApprovedAbsentSetBindingId> / <actionApprovedAbsentKeyCount>` |
| Target absence revalidation evidence id | `<actionTargetAbsenceRevalidationEvidenceId>` |
| Trusted target baseline id/alias/state/evidence | `<trustedTargetBaselineId> / <trustedTargetAlias> / <verified> / <trustedTargetBaselineEvidenceId>` |
| Exact-target global coordinator id/state/owner/consumer/generation/evidence | `<targetGlobalCoordinatorId> / <targetGlobalCoordinatorState> / <targetGlobalCoordinatorOwnerFenceId> / <targetGlobalCoordinatorConsumer> / <targetGlobalCoordinatorGeneration> / <targetGlobalCoordinatorEvidenceId>` |
| Target operation fence id/chain state/upload branch/Delete branch/consumer/generation/evidence | `<targetOperationFenceId> / <targetOperationFenceState> / <targetUploadBranchState> / <targetDeleteBranchState> / <targetOperationConsumer> / <targetOperationFenceGeneration> / <targetOperationFenceEvidenceId>` |
| Target-identity preparation approval id/state/deadline/claim owner/fence | `<targetIdentityPreparationApprovalId> / <consumed> / <targetIdentityPreparationExecuteByUtc> / <targetIdentityPreparationClaimId> / <targetIdentityPreparationFence>` |
| Protected exact target DB binding id | `<targetDbBindingId>` |
| Target DB binding state/validity/evidence | `<upload_bound \| retryable \| completed \| invalid> / <targetDbBindingValidUntilUtc> / <targetDbBindingEvidenceId>` |
| Retry reconciliation source action/failure class, creation state/owner claim/fence/expiry/evidence and record id/state/observation/claim deadline, only after an eligible retryable rollback | `<retryReconciliationSourceActionClass> / <retryReconciliationSourceFailureClass> / <retryReconciliationCreationState> / <retryReconciliationCreationClaimId> / <retryReconciliationCreationFence> / <retryReconciliationCreationExpiresAtUtc> / <retryReconciliationCreationEvidenceId> / <retryReconciliationRecordId> / <available \| consumed \| invalid> / <retryReconciliationObservedAtUtc> / <retryReconciliationExecuteByUtc> \| not_created>` |
| Retry reconciliation private-subset retention/disposition/evidence | `<retryReconciliationRetainUntilUtc> / <scheduled \| in_progress \| disposed \| disposal_failed_blocked> / <retryReconciliationDispositionEvidenceId> \| not_created>` |
| Upload job id | `<uploadJobId>` |
| Approved target-only row count | `<targetRows>` |
| Approved target file count | `<targetFiles>` |
| Job final status | `<succeeded \| failed \| blocked \| cancelled>` |
| Processed rows | `<processedRows>` |
| Uploaded rows | `<uploadedRows>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| DB delta evidence, only if explicitly approved and enabled | `<dbDeltaEvidenceId \| not approved>` |
| Row attribution evidence, only if explicitly approved and enabled | `<rowAttributionEvidenceId \| not approved>` |
| Unresolved failure condition | `<none \| reason>` |

If Start Upload fails, the action transaction must roll back every action DB
write before lease release or disposition. Any evidence of partial mutation is a
contract violation: preserve job, audit, DB delta, and row attribution evidence,
mark the chain blocked, and do not run Retry Failed or cleanup.

A succeeded Start with no retryable remainder requires target outcome
`committed`, lease `released_committed`, snapshot state `completed`, disposition
`disposed`, and valid outcome/disposition evidence. A failed job is eligible for
a separately approved Retry only after authoritative outcome evidence proves
complete rollback and fresh exact DB reconciliation of the entire attempted
subset records every still-absent row; then lease state is
`released_rolled_back`, snapshot state is `retryable`, and disposition remains
`scheduled` only until the retention deadline. `commit_unknown_blocked`, partial
mutation, or failed disposition blocks Retry and cutover.

## Retry Failed Approval And Evidence Template

Retry Failed is separate and conditional. It is not automatic rollback.
It remains blocked until production code/tests provide an immutable/
authenticated, expiring, single-use Retry approval record atomically claimed
with the source job's `retryable` immutable snapshot and retry-job/event
creation. The worker must use only that same snapshot and never reopen the
operational source.
Follow the Retry transition table in `docs/173`: `invalid` is allowed only when
no retry job/event commits; once one action commits the approval remains
`consumed` regardless of response loss or later retry outcome.

Required before requesting approval:

- failed or retryable upload job evidence;
- job id;
- exact remaining physical rows;
- exact remaining file count;
- operator PC class and privacy-safe source alias;
- source class and package commit;
- the same verified/non-revoked trusted target baseline id/alias/state/evidence
  used by Preview, the source action, and reconciliation;
- the same target operation fence is in chain state `idle`, upload branch `retryable`,
  Delete unowned, and its exact generation/evidence is bound for atomic Retry
  claim with the approval/snapshot/reconciliation record/job;
- protected immutable content snapshot record id in state `retryable` and the
  matching atomic snapshot binding evidence id from the source job;
- protected `retryReconciliationRecordId` is `available`, unexpired, and binds
  the source action/mutation/outcome evidence, snapshot, entire attempted subset,
  private exact still-absent subset, safe counts, observation, deadline, and the
  same consumed target-identity preparation approval plus protected exact
  `targetDbBindingId`/state/validity/evidence; the binding is `retryable`,
  unexpired, and revalidated before reconciliation or mutation reads;
- that record is the protected `actionApprovedAbsentSetBindingId` and binds exact
  distinct `actionApprovedAbsentKeyCount`, not merely physical rows/files;
- its source action's unique reconciliation-creation entitlement is
  `record_available`, bound to only that record and an eligible source action/
  failure class, and cannot publish a sibling; its creation evidence binds the
  successful owner claim id, monotonic fence, absolute expiry, and publication
  CAS against current action/failure-class eligibility plus source lease/target-
  binding/rollback/snapshot/disposition state;
  the private subset is owner-only/tamper-evident/per-record encrypted, its
  retention is no later than snapshot retention, and disposition is `scheduled`;
- snapshot retention deadline has not passed and disposition is `scheduled`;
- human-approved action maximum duration plus exact
  `snapshotDispositionMarginSeconds` fits before both the target-binding and
  snapshot-retention deadlines; the action lease plus that margin ends no later
  than their minimum, and a
  random unique `actionMutationId` is pre-reserved in the immutable approval and
  can be claimed with an unrenewable target-fenced DB mutation lease atomically
  with the retry action;
- root failure class preserved;
- confirmation no broad cleanup is requested;
- protected Retry approval state is `available` and its package/operator/source/
  source-job/remaining-count/deadline/snapshot/atomic-evidence bindings are exact;
- deterministic tests prove source change before Retry, equal-size/equal-mtime
  replacement, concurrent writes, missing/tampered snapshots, and worker source-
  reopen attempts cannot change retried bytes and produce zero DB writes on any
  pre-mutation mismatch; they also reject mutation-id substitution and stale/
  replayed/equal-count-different-subset reconciliation records, cursor-derived
  scope, concurrent creation/claim, sibling creation, response-loss/crash before
  and after publication, delayed publication racing expiry/invalidation/restart,
  stale claim/fence rejection, multi-Retry record reuse, and missing/failed private-
  subset cryptographic disposition. They also cover a target insert after
  reconciliation and during the Retry transaction, same-count key substitution,
  missing writer fence, serialization/unique conflict, and zero-write/no-
  overwrite rollback, plus missing/substituted target DB bindings and same-host/
  same-port cluster/database replacement before reconciliation/Retry/marker.
  They also cover target-binding expiry immediately before/at/after Retry claim,
  marker, transaction, outcome/whole-attempt reconciliation and publication CAS,
  and reject a lease/publication deadline beyond the minimum target-binding/
  snapshot ceiling.

Approval wording:

```text
The Retry Failed approval id is <retryApprovalId> and it must be claimed by <retryExecuteByUtc>.
I approve exactly one Retry Failed using protected reconciliation record <retryReconciliationRecordId>, observed at <retryReconciliationObservedAtUtc> and claimable by <retryReconciliationExecuteByUtc>, for upload job <jobId> with freshly reconciled still-absent files <remainingFiles> and physical rows <remainingRows> from the entire prior attempted subset, preserving root failure class <rootFailureClass>.
That reconciliation record is the protected approved-absent set binding <actionApprovedAbsentSetBindingId> with distinct keys <actionApprovedAbsentKeyCount>.
This approval is for package sourceCommit <sourceCommit>, operator PC class <operatorPcClass>, source alias <sourceAlias>, and source class <sourceClass>.
It binds the same pre-existing trusted target baseline <trustedTargetBaselineId> in verified/non-revoked state <trustedTargetBaselineState>, privacy-safe alias <trustedTargetAlias>, and safe evidence <trustedTargetBaselineEvidenceId> used by Preview/source action/reconciliation.
It binds protected target operation fence <targetOperationFenceId> in chain state idle, upload branch retryable, with exact generation <targetOperationFenceGeneration> and safe evidence <targetOperationFenceEvidenceId>. Retry creation must atomically claim that generation for consumer retry; any Delete owner or stale/terminal generation must fail.
It binds exact-target singleton coordinator <targetGlobalCoordinatorId>, sole owner fence <targetOperationFenceId>, state chain_ready, empty consumer, exact generation <targetGlobalCoordinatorGeneration>, and safe evidence <targetGlobalCoordinatorEvidenceId>. Retry creation must atomically claim both generations for consumer retry; any different Preview-chain owner or concurrent target consumer must fail.
The approved exact operational DB target comes from consumed preparation approval <targetIdentityPreparationApprovalId>, completed by <targetIdentityPreparationExecuteByUtc>, and is protected binding <targetDbBindingId> in state <targetDbBindingState>, valid only until <targetDbBindingValidUntilUtc>, with safe evidence <targetDbBindingEvidenceId>. It must match Preview, the source action, reconciliation record, marker, and authoritative Retry transaction.
It is bound to immutable content snapshot <contentSnapshotRecordId> and atomic snapshot binding evidence <atomicSnapshotBindingEvidenceId> from the source job.
That snapshot may be read only until <contentSnapshotRetainUntilUtc>; this approval does not authorize snapshot deletion or extend retention.
The action maximum duration is <actionMaxDurationSeconds> seconds and the required disposition margin is <snapshotDispositionMarginSeconds> seconds. Retry creation must atomically create one unrenewable snapshot action lease whose expiry is claim time plus that duration and whose expiry plus that margin is no later than both <targetDbBindingValidUntilUtc> and <contentSnapshotRetainUntilUtc>, and claim the pre-reserved <actionMutationId>.
The random unique actionMutationId above is pre-reserved in this immutable approval and may only be claimed with this approval, reconciliation record, snapshot, exact subset, duration, margin, lease, and retry action.
As part of that one Retry action, I approve creation of exactly one target-side prepared outcome/fence marker for the same actionMutationId before any all_metrics write; it authorizes no other DB mutation. Every retry write and the prepared-to-committed marker transition must share one authoritative target transaction; a guarded prepared-to-aborted finalization may occur only after non-commit is authoritative.
That transaction must first revalidate the exact target identity and unexpired target binding using the authoritative target DB clock, then serializably revalidate every key in the protected still-absent set, use canonical key fences honored by every application writer and conflict-rejecting conditional inserts, and commit only if the exact inserted keyset/count equals the binding. Any expired/substituted target, preexisting/concurrent key, or mismatch must roll back every action all_metrics write without overwrite and require a fresh whole-attempt reconciliation and approval.
I approve bounded read-only target-outcome reconciliation for that same actionMutationId within this window and, only if its immutable aborted marker is finalized and observed before lease expiry, exactly one whole-attempt exact DB reconciliation plus a new protected retry-reconciliation evidence record. Timeout, response loss, or lease expiry must become commit_unknown_blocked unless the immutable target marker proves committed or aborted/complete rollback.
That reconciliation must atomically claim the source action's unique single-use creation entitlement before any DB read, durably recording and binding source action class retry, its safe terminal failure class, an owner claim id, monotonic fence, and absolute publication deadline no later than the source lease, target-binding validity, and snapshot boundaries. Publication must compare-and-set that exact eligible action/failure class, unexpired token/fence, the same unexpired target binding, and current rollback/snapshot/disposition state; invalidation advances the fence, so a delayed publisher cannot succeed. Duplicate or response-loss recovery may return only the same record. Its exact private subset must remain owner-only, tamper-evident, per-record encrypted, use the named snapshot retention deadline as its non-extendable access ceiling, and be cryptographically disposed earlier on terminal Retry, invalidation, expiry, or snapshot disposition.
This approval does not approve Start Upload, Delete, Settings save, or feature gate enablement.
```

Evidence after retry:

| Field | Value |
| --- | --- |
| Retry approval id | `<retryApprovalId>` |
| Retry approval deadline UTC | `<retryExecuteByUtc>` |
| Retry approval terminal state | `<consumed \| invalid>` |
| Source upload job id | `<jobId>` |
| Protected immutable content snapshot record id | `<contentSnapshotRecordId>` |
| Content snapshot terminal state | `<upload_bound \| retryable \| completed \| invalid>` |
| Snapshot retention deadline UTC | `<contentSnapshotRetainUntilUtc>` |
| Snapshot disposition state | `<scheduled \| in_progress \| disposed \| disposal_failed_blocked>` |
| Snapshot disposition evidence id | `<snapshotDispositionEvidenceId>` |
| Atomic snapshot binding evidence id | `<atomicSnapshotBindingEvidenceId>` |
| Action maximum duration seconds | `<actionMaxDurationSeconds>` |
| Snapshot disposition margin seconds | `<snapshotDispositionMarginSeconds>` |
| Snapshot action lease id | `<snapshotActionLeaseId>` |
| Snapshot action lease expiry UTC | `<snapshotActionLeaseExpiresAtUtc>` |
| Snapshot action lease terminal state | `<released_committed \| released_rolled_back \| expired_rolled_back \| commit_unknown_blocked>` |
| Action mutation id | `<actionMutationId>` |
| Action mutation outcome/evidence id | `<committed \| rolled_back \| commit_unknown_blocked> / <actionMutationOutcomeEvidenceId>` |
| Protected approved-absent set binding/distinct-key count | `<actionApprovedAbsentSetBindingId> / <actionApprovedAbsentKeyCount>` |
| Target absence revalidation evidence id | `<actionTargetAbsenceRevalidationEvidenceId>` |
| Trusted target baseline id/alias/state/evidence | `<trustedTargetBaselineId> / <trustedTargetAlias> / <verified> / <trustedTargetBaselineEvidenceId>` |
| Exact-target global coordinator id/state/owner/consumer/generation/evidence | `<targetGlobalCoordinatorId> / <targetGlobalCoordinatorState> / <targetGlobalCoordinatorOwnerFenceId> / <targetGlobalCoordinatorConsumer> / <targetGlobalCoordinatorGeneration> / <targetGlobalCoordinatorEvidenceId>` |
| Target operation fence id/chain state/upload branch/Delete branch/consumer/generation/evidence | `<targetOperationFenceId> / <targetOperationFenceState> / <targetUploadBranchState> / <targetDeleteBranchState> / <targetOperationConsumer> / <targetOperationFenceGeneration> / <targetOperationFenceEvidenceId>` |
| Target-identity preparation approval id/state/deadline/claim owner/fence | `<targetIdentityPreparationApprovalId> / <consumed> / <targetIdentityPreparationExecuteByUtc> / <targetIdentityPreparationClaimId> / <targetIdentityPreparationFence>` |
| Protected exact target DB binding id | `<targetDbBindingId>` |
| Target DB binding state/validity/evidence | `<upload_bound \| retryable \| completed \| invalid> / <targetDbBindingValidUntilUtc> / <targetDbBindingEvidenceId>` |
| Retry reconciliation source action/failure class and creation state/owner claim/fence/expiry/evidence id | `<retryReconciliationSourceActionClass=retry> / <retryReconciliationSourceFailureClass> / <record_consumed \| invalid> / <retryReconciliationCreationClaimId> / <retryReconciliationCreationFence> / <retryReconciliationCreationExpiresAtUtc> / <retryReconciliationCreationEvidenceId>` |
| Claimed retry reconciliation record id/state | `<retryReconciliationRecordId> / <consumed \| invalid>` |
| Retry reconciliation observation/deadline UTC | `<retryReconciliationObservedAtUtc> / <retryReconciliationExecuteByUtc>` |
| Retry reconciliation retention/disposition/evidence | `<retryReconciliationRetainUntilUtc> / <scheduled \| in_progress \| disposed \| disposal_failed_blocked> / <retryReconciliationDispositionEvidenceId>` |
| Reconciled attempted/still-absent safe counts | `<attemptedFiles>/<attemptedRows> -> <remainingFiles>/<remainingRows>` |
| Retry job id or event id | `<retryJobOrEventId>` |
| Approved freshly reconciled still-absent physical rows | `<remainingRows>` |
| Approved freshly reconciled still-absent file count | `<remainingFiles>` |
| Root failure class | `<rootFailureClass>` |
| Final status | `<succeeded \| failed \| blocked \| cancelled>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| Stop-after-failure confirmation | `<yes/no plus reason>` |

If Retry fails and authoritative evidence proves non-commit, the retry
transaction must have rolled back every retry DB write before
`released_rolled_back`; fresh exact reconciliation is required before any later
Retry scope. If outcome is unknown, use `commit_unknown_blocked` and do not infer
rollback. Stop and preserve evidence. Any partial mutation is a blocking
contract violation; do not run broad DB cleanup, reset, or manual delete as a
workaround.

A succeeded Retry with no remainder requires target outcome `committed`, lease
`released_committed`, snapshot state `completed`, disposition `disposed`, and
valid outcome/disposition evidence. Any retryable remainder, unresolved/unknown
outcome, nonterminal state, or failed disposition blocks cutover.

## Audit Logs Failure-Path Validation

Prove failure visibility without destructive production mutation where possible.
Use sanitized evidence only.

Required failure or blocked classes:

- DB unreachable or DB-dependent blocked class;
- malformed request or validation failure;
- active Preview conflict;
- Settings validation failure;
- runtime blocked state;
- upload config missing or auth invalid class.

Allowed validation methods:

- fixture or development-only malformed requests that do not touch operational
  data;
- read-only inspection of existing Audit Logs for recent blocked/failure rows;
- operator UI observation of Audit Logs filters and safe params;
- runtime status blocked evidence when required containers are missing, without
  cleanup or create commands.

Stop if producing a failure would require operational upload, operational delete,
Settings save, DB reset, Docker cleanup, LAN exposure, or recording raw sensitive
data.

## Operator-PC E2E Checklist

| Item | Evidence id | Status | Notes |
| --- | --- | --- | --- |
| Browser `/` route loads from current backend-served source | `wp02-responsive-core-routes-20260713` | `pass` | Accepted package binding remains a final condition. |
| Browser `/upload` route loads in API mode | `wp02-responsive-core-routes-20260713` | `pass` | Approved Preview state was rendered; no action was triggered. |
| Browser `/logs` route shows Job Logs and Audit Logs | `wp02-responsive-core-routes-20260713` | `pass` | No raw params or secrets were recorded. |
| Browser `/settings` route loads read-only before mutation | `wp02-responsive-core-routes-20260713` | `pass` | Settings save was not executed. |
| API mode confirmation | `wp02-config-runtime-20260713` | `pass` | Sanitized target/mode classes only. |
| Local token protection confirmation, if available | `not assessed` | `pending/not applicable to read-only route smoke` | Config secret masking was observed, but token enforcement was not exercised and is not claimed here. |
| Config snapshot | `wp02-config-runtime-20260713` | `pass` | Only classes and booleans are retained here. |
| Runtime readiness | `wp02-config-runtime-20260713` | `conditional` | Core services ready; Grafana/Vector non-core attention remains. |
| Preview-only readiness | `wp02-preview-prv_ca38650a9e7d`; `docs/182` | `blocked` | The earlier execution remains historical evidence. A new Preview is blocked until protected atomic binding/target-identity lifecycles and deterministic replacement/concurrency/tamper/replay/wrong-initial-target tests pass and the rebuilt package is verified; a separately controlled verified baseline must already exist, then successor inventory, separate manifest preparation, separate target-identity preparation/exact-match review, and later Preview approval may proceed. |
| Logs/audit visibility | `wp02-audit-readonly-20260713`; `wp02-joblogs-readonly-20260713` | `pass` | Existing success/failure/blocked and terminal-job evidence were visible. |

Screenshots are allowed only if they do not expose secrets, raw paths, filenames,
raw DB URLs, tokens, JWTs, Authorization values, internal URLs, raw CSV content,
or exact keys.

## Go/No-Go Checklist

| Item | Required before GO | Evidence id | Status | Approver | Notes |
| --- | --- | --- | --- | --- | --- |
| Accepted package/source commit | Yes | `wp02-main-5695b93` | `pending: hard stop` | `<approver>` | Source tree is known; accepted executing package label/build metadata is not yet bound. |
| README/API no-live-smoke and schema contract | Yes | `wp02-wp01-automated-5695b93` | `pass` | `<approver>` | Live Preview/Upload Job POST examples are intentionally omitted; API source enforces missing/non-positive target-row rejection and tests cover missing/mismatch paths. |
| Sanitized config snapshot | Yes | `wp02-config-runtime-20260713` | `pass` | `<approver>` | Safe classes only. |
| Local Supabase readiness | Yes | `wp02-config-runtime-20260713` | `pass` | `<approver>` | API/DB/Studio/Edge ready; non-core attention recorded separately. |
| Read-only inventory precheck | Yes | `docs/182`; `inv_20260815T031829Z_0d41338f` | `partial: baseline only` | `human_operator` | Do not refresh for approval yet. Atomic binding implementation/tests and rebuilt-package verification come first; the later successor record also needs safe operator/source bindings. |
| Protected content-manifest/snapshot preparation | Yes before a new Preview | `not_created` | `blocked: implementation and approval absent` | `<approver>` | Requires a separate approval after the rebuilt package and successor inventory pass; creates protected manifest plus immutable snapshot and does not itself approve Preview. |
| Trusted target baseline and target-identity preparation | Yes before a new Preview | `not_provisioned / not_approved / not_created` | `blocked: separately controlled baseline and approval/result absent` | `<approver>` | Baseline provisioning/rotation is not authorized here. After manifest preparation, separately approve the read-only identity comparison and human-review the exact-match opaque binding before Preview approval. |
| Preview-only evidence | Yes, if upload cutover is being evaluated | `wp02-preview-prv_ca38650a9e7d` | `blocked for new run` | `<approver>` | The earlier run remains historical evidence. Implementation/tests and package verification must pass before successor inventory; protected manifest preparation and target-identity preparation/exact-match review then need separate approvals before a later Preview approval. |
| Start Upload evidence | Yes when Preview proves approved target rows | `wp02-preview-prv_ca38650a9e7d` | `not applicable` | `<approver>` | Target rows were zero; Start Upload was disabled and not executed. A future job must bind and read only the Preview snapshot under a bounded active-use lease with all-or-nothing rollback. |
| Retry Failed evidence | Conditional | `wp02-preview-prv_ca38650a9e7d` | `not applicable` | `<approver>` | No new upload or retryable rows. A future retry must bind and read only the source-job snapshot under a bounded active-use lease with all-or-nothing rollback. |
| Audit Logs failure visibility | Yes | `wp02-audit-readonly-20260713` | `pass` | `<approver>` | Existing safe success/failure/blocked classes visible. |
| Job Logs visibility | Yes | `wp02-joblogs-readonly-20260713` | `pass` | `<approver>` | Latest terminal status and events visible. |
| Representative CSV fixture coverage | Yes | `wp02-wp01-automated-5695b93` | `pass` | `<approver>` | UTF-8/CP949/integrated legacy classes covered. |
| Large real CSV Preview soak | Yes | `wp02-preview-prv_ca38650a9e7d` | `pass for execution behavior` | `<approver>` | Completed without risky/target rows; 64,766 partial-overlap rows remain excluded from target-only upload and require disposition. |
| Operator-PC UI route evidence | Yes | `wp02-responsive-core-routes-20260713` | `pass` | `<approver>` | Six Core Ops views, seven viewports, zero QA errors. |
| Rollback/stop procedure | Yes | `docs/173`; `README.md` | `pending: hard stop` | `<approver>` | Final approver must acknowledge legacy/manual fallback and non-destructive stop. |
| Delete strictly excluded from this cutover | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Delete was excluded; a separate delete plan cannot be credited toward this sign-off. |
| LAN excluded | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Localhost-only. |
| Reset/cleanup excluded | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | No Supabase/Docker destructive cleanup. |
| Secrets redaction complete | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Only safe ids/classes/counts are retained. |
| Final sign-off record | Yes | `<evidenceId>` | `pending: hard stop` | `<approver>` | `GO`/`CONDITIONAL GO` must bind every exact field. Stop/defer decisions preserve actual evidence for completed stages and mark only unobserved/unreached stages unavailable with reasons; decision metadata, blockers, and next action remain mandatory. |

## Risk Register

| Risk statement | Severity | Likelihood | Mitigation | Owner or approval gate | Required evidence |
| --- | --- | --- | --- | --- | --- |
| Accepted package metadata is not bound to the verified source tree before final sign-off. | High | Medium | Verify `package-build-info.json`, package label, and source commit for the executing artifact. | Release owner/operator | Accepted package metadata and final sign-off |
| The later `docs/182` inventory is misapplied retroactively to the old zero-target Preview, reused without exact operator/source/target binding, or unresolved partial-overlap rows are hidden. | High | Medium | Treat `docs/182` as baseline only; first complete atomic binding implementation/tests and rebuilt-package verification, confirm a separately controlled verified target baseline already exists, then create a successor inventory, separately approve protected manifest preparation, separately approve/read-only-run and human-review exact-match target-identity preparation, and record any required partial-overlap disposition before later Preview approval. | Backend maintainer, then separate operator approvals plus maintainer evidence capture | Production implementation/tests, trusted baseline and target-preparation/binding evidence, current inventory/manifest/Preview records, executing-package metadata, partial-overlap disposition; Start only if target rows exist |
| The approved source changes after inventory but before Preview. | High | Medium | Bind a human-approved maximum age/deadline and repeat the full read-only unchanged-snapshot check immediately before the API call; do not call Preview on expiry or mismatch. | Operator approval plus maintainer evidence capture | Observation/deadline fields and `preCallSnapshotUnchanged=true` with safe check timestamp |
| Source content changes after the final metadata check or is replaced with equal-size/equal-mtime content. | Production-critical | Medium | Keep Preview blocked until protected manifest/snapshot lifecycles exist; Preview verifies and parses the immutable snapshot, and that snapshot is retained through later approved Start/Retry actions. Cover replacement, tamper, expiry, replay, and source-reopen windows deterministically. | Backend maintainer plus separate manifest-preparation and Preview approvals | Production implementation/tests, opaque `contentManifestRecordId`, `contentSnapshotRecordId`, and `atomicSnapshotBindingEvidenceId` |
| Full operational CSV bytes are copied without informed scope, capacity, confidentiality, retention, or bounded disposition controls. | Production-critical | Medium until lifecycle exists | Exact preparation approval states full-byte copying/ceiling and pre-authorizes automatic per-snapshot key destruction plus verified byte removal at terminal/invalidation/deadline; failed removal leaves keyless data, alerts, and blocks new preparation. | Backend maintainer plus manifest-preparation approver | Approved byte ceiling/deadline, protected-store evidence, disposition state/evidence id, and deterministic deadline/crash/failure recovery tests |
| Start Upload or Retry Failed approval is replayed/concurrent, binds different bytes, outlives retention, or loses the remote-commit/local-release acknowledgement. | Production-critical | Medium until lifecycle exists | Keep both actions blocked until approvals atomically claim the same snapshot with one job/event, one unrenewable bounded lease, and one target-fenced mutation id; writes and durable outcome marker share the authoritative target transaction; timeouts never infer rollback; `commit_unknown_blocked` prevents Retry/cutover; disposition cannot race an active/pending outcome. | Backend maintainer plus separate mutation approval | Production implementation/tests, approval/snapshot/lease/outcome terminal states, duration/margin, target marker/reconciliation evidence, atomic binding evidence, job/event id, and audit evidence |
| Grafana/Vector non-core attention is silently ignored or confused with core readiness. | Medium | Medium | Resolve it or record owner, residual-risk acceptance, and non-destructive stop/rollback procedure. | Release owner/operator | Sanitized runtime state and signed caveat |
| A new CSV or failure class escapes the current fixture/Audit coverage. | High | Low-medium | Add representative fixtures and keep failure-path API/UI checks in regression and approved operations. | Maintainer QA and operator sign-off | Fixture/soak and safe Audit/Job Logs evidence |
| Accidental destructive delete or cleanup is bundled into validation, or delete preflight/delete approval text is replayed. | Production-critical | Low | Treat delete, reset, cleanup, and Docker destructive commands as hard exclusions. A future delete requires every `docs/164`/`docs/171` hardened gate: target-global coordination across Preview chains; fenced single-use preflight claim/result with completion deadline; owner-only canonical-root source-provenance snapshot; complete typed DB before-image captured atomically with DELETE/marker under exact schema/column/side-effect/ceiling/capacity/confidentiality/retention bindings; an engine-appropriate DDL/schema fence proving every DELETE and restore-INSERT secondary relation or externally observable effect absent/inert; committed dual-record versus aborted source-only cleanup with split authority; exact restore/disposition approvals; and a single-use Delete approval/run with marker-first reconcile. Source CSV never proves exact rollback. No separate Delete evidence may be imported into this cutover, and any Delete here forces NO-GO. | Hardened destructive plan plus operator approvals | Exclusion record or full implemented/tested coordinator/preflight/source-provenance/schema-fence/side-effect/DB-before-image/restore/disposition/marker lifecycles and exact package |
| Package/source mismatch leads to testing the wrong build. | High | Low | Verify package metadata and source commit before every evidence package. | Release owner | Package commit, label, and hash/metadata evidence |
| Secrets or raw operational data leak into evidence. | High | Medium | Store externally only opaque random ids, safe classes/counts, approved package hashes, and reason codes; keep exact operational material plus any keyed integrity data owner-only and review screenshots before attachment. | Security reviewer/maintainer | Redaction checklist and sanitized artifacts |

## Stop Conditions

Stop before any `GO`/`CONDITIONAL GO`, Preview, Start Upload, Retry Failed,
delete, or other proceed action when any of these are true. A `NO-GO`, `BLOCKED`,
or `DEFERRED` record may and should still be completed with explicit missing or
not-applicable values and reasons:

- package metadata, source commit, or package label is missing, unbound, stale,
  or mismatched;
- the compliant pre-Preview inventory record cannot be identified and must not
  be inferred or autofilled from Preview output;
- read-only inventory is missing, stale, broader than the requested scope, or
  guessed;
- inventory observation time, human-approved maximum age, or Preview execution
  deadline is missing, inferred, expired, or mismatched;
- the immediately-before-call read-only scan is missing or does not confirm the
  exact file set, scope, size/mtime metadata, counts, package, operator PC,
  source alias, and source class are unchanged;
- the stage-specific approval/manifest state differs from the `docs/173`
  transition table; before Preview claim the preparation approval must be
  `consumed`, manifest `prepared`, and Preview approval `available`;
- an approval/record is missing, expired, tampered, unauthenticated, mismatched,
  regressed, double-claimed, or reused outside its valid stage, or private
  manifest material would be exposed in published evidence;
- `manifestPreparationApprovalId` or `previewApprovalId` is arbitrary,
  unresolvable, in a state invalid for the current stage, or differs between
  protected approval records, manifest creation, atomic claim/run, terminal
  evidence, and final sign-off;
- `manifestPreparationExecuteByUtc` is missing/inferred, exceeds the inventory
  observation plus human-approved maximum age, or either preparation claim or
  completed protected publication occurs after it;
- Start Upload or Retry Failed approval is missing, unresolvable, expired,
  substituted, mismatched, double-claimed, replayed, or not atomically claimed
  with creation of exactly one corresponding job/event;
- Start Upload or Retry Failed lacks a human-approved action maximum duration,
  exact pre-retention disposition margin, one unrenewable target-fenced active-
  use lease and the exact random mutation id pre-reserved in its immutable
  approval, a durable outcome marker in the same authoritative transaction as
  all action writes, or protection against disposition racing an active/pending
  outcome;
- a Start/Retry action lease plus approved margin, or reconciliation deadline,
  exceeds the minimum of
  `targetDbBindingValidUntilUtc` and the snapshot-retention boundary, or target-
  binding expiry is not atomically rechecked with the target DB clock before
  claim, marker, transaction, outcome read, and reconciliation publication;
- Start Upload or Retry Failed lacks the protected exact absent-set binding and
  distinct-key count, serializable whole-set transaction-time absence
  revalidation, canonical fencing for every application writer, conflict-
  rejecting conditional inserts, or exact committed-keyset evidence; target
  drift can overwrite an existing row or retain partial action writes;
- Start Upload/Retry outcome is inferred from timeout, response loss, local job
  state, or lease expiry; target commit/non-commit is not authoritatively proven;
  or `commit_unknown_blocked` is treated as rollback, retryability, or GO;
- Retry scope comes from a worker cursor/pre-rollback remainder instead of fresh
  exact DB reconciliation of the entire prior attempted snapshot subset after
  authoritative rollback evidence;
- Retry lacks an unexpired protected reconciliation record atomically claimed
  once with its approval/snapshot/job/lease, or its source action/mutation/
  outcome, whole attempted subset, private still-absent subset, safe counts,
  observation, or deadline is substituted, stale, replayed, or mismatched;
- a source action can create more than one reconciliation record, its protected
  creation entitlement is absent/regressed/replayed/not bound to an eligible
  source action/failure class, Start target-absence drift/conflict can cause any
  reconciliation DB read or record publication, or concurrency/crash/
  response-loss recovery can publish or retain a usable sibling;
- reconciliation publication lacks a durable owner claim id, monotonic fence,
  absolute deadline, and CAS recheck of source action/failure-class eligibility
  plus source lease/target-binding/rollback/snapshot/
  disposition state, or a delayed claimant can publish after invalidation/
  expiry/restart recovery;
- reconciliation private subset storage is not owner-only, tamper-evident,
  per-record encrypted, bounded by snapshot retention, and cryptographically
  disposed with safe evidence on terminal Retry/invalidation/expiry/snapshot
  disposition, or a failed disposal does not block;
- atomic snapshot binding is absent or untested, or Preview cannot prove it
  parsed the same immutable bytes verified against the approved content
  manifest or prevent replay of that record;
- `contentSnapshotRecordId`, its stage state, or
  `atomicSnapshotBindingEvidenceId` is missing/mismatched, the protected snapshot
  is mutable/tampered, Start/Retry would reopen the operational source, or a
  pre-mutation mismatch cannot guarantee zero DB writes;
- physical row count or target row count is guessed;
- Preview is not fresh, latest, succeeded, and DB reachable;
- risky count is greater than zero;
- partial-overlap row count differs from Preview/final sign-off, or disposition
  lacks exact `excluded_and_human_accepted` (or separately approved policy), a
  named human approver, and opaque evidence id;
- target rows mismatch between UI, API, approval text, and evidence;
- Audit Logs evidence is unavailable;
- Job Logs evidence is unavailable for an upload decision;
- inventory evidence record id, operator PC class, or privacy-safe source alias
  differs between inventory, Preview approval/evidence, and final sign-off;
- target-identity preparation approval id/state/deadline is missing, inferred,
  replayed, not terminal `consumed`, was claimed/published after its deadline, or
  differs across its protected
  result, Preview approval/evidence, and final sign-off;
- trusted target baseline id/alias/state/evidence is missing, unresolved,
  substituted, revoked, created from the first observation, or differs across
  target preparation/Preview/Start/Retry/marker/reconciliation/final sign-off;
  observed exact identity was not compared to the owner-only expected identity;
- target DB binding state/validity/evidence id is missing, was expired at any DB
  access/action/reconciliation deadline, was not `prepared` before Preview claim,
  was not `previewed`/`retryable` at the respective
  Start/Retry claim, or regresses/diverges from the state table;
- protected exact `targetDbBindingId` is missing/unresolvable/substituted, relies
  only on safe target/port/readiness classes, differs across Preview/Start/Retry/
  marker/reconciliation/final sign-off, or a same-port instance/database swap is
  not rejected on the authoritative DB session/transaction; or the target-
  identity preparation approval id/state/deadline and target binding id/state/
  validity/evidence are not exactly equal across those stages;
- the protected target operation fence id/generation/evidence is missing,
  substituted, stale, terminally replayed, or not atomically claimed with its
  exact stage approval/action; Start, Retry, Delete preflight, or Delete can own
  overlapping consumers; the upload/Delete branch state is inconsistent with
  Preview counts; or a zero-target Delete-eligible branch cannot be closed
  independently without reusing the disposed upload snapshot;
- the exact-target singleton coordinator id/state/owner/generation/evidence is
  missing or differs across Preview chains, a new Preview can claim while an
  older chain is ready/active/retryable/delete-ready/commit-unknown, or any
  Start/Retry/Delete action can claim without CAS-checking the same target-global
  owner and generation;
- a prior Delete leaves target-global/chain/Delete-branch
  `recovery_disposition_pending`, unresolved restore/disposal, or failed cleanup;
  any new Preview/Start/Retry/Delete can race that state; or a coordinator is
  released before key-first verified terminal disposition of every recovery
  record that actually exists: both source provenance and DB before-image for a
  committed Delete, or source provenance only with verified before-image
  `not_created` for an authoritative aborted Delete;
- manifest-preparation approval id, protected content manifest/snapshot record
  id, Preview approval id, Preview run id, snapshot stage state, or atomic
  snapshot binding evidence id is missing, invalid, reused, or differs between
  the consumed manifest, succeeded Preview evidence, Start/Retry job binding,
  and final sign-off;
- a requested operational delete lacks an implemented/tested protected expiring
  single-use preflight approval atomically bound to exactly one
  `deletePreflightId`, an unexpired `ready_available` preflight result with a
  protected single-consumer lifecycle, or a separate protected expiring
  single-use delete approval atomically claimed with that result and exactly one
  `deleteRunId`;
- a requested operational delete lacks the singleton target-global coordinator,
  fenced preflight owner/completion CAS, canonical-root exact-byte source-
  provenance snapshot, protected complete-row DB before-image with schema/column/
  side-effect/ceiling/capacity/confidentiality/retention bindings, committed dual-
  record versus aborted source-only cleanup with split authority and exact
  restore/disposition approvals plus an unrenewable restore action lease and
  reconcile/disposition margin, or pre-reserved target mutation marker with
  atomic before-image + Delete + marker commit and marker-first outcome proof
  required by `docs/164`/`docs/171`;
- full-byte snapshot preparation lacks an explicit approved byte ceiling,
  protected capacity/confidentiality controls, retention deadline, or human
  acknowledgement of automatic cryptographic disposal; or disposal cannot
  destroy the per-snapshot key, remove/verify the byte file, record evidence, and
  block/alert safely on failure;
- source class differs between inventory, Preview, approval, and config evidence;
- Grafana/Vector attention lacks resolution or explicit residual-risk acceptance,
  an owner, and a non-destructive stop/rollback procedure;
- final release-owner/operator sign-off is incomplete;
- raw sensitive data would be written to evidence;
- request bundles Preview, Start Upload, Retry Failed, Delete, Settings save,
  reset, cleanup, LAN, migration, deployment, Docker destructive command, or
  feature gate enablement;
- request asks for Supabase init/reset/migration/backfill/cleanup, Docker
  create/rm/prune/volume delete/compose up/down, LAN exposure, or production DB
  mutation without a separate approved plan.

## Final Sign-Off Record

| Field | Value |
| --- | --- |
| Decision | `<GO \| CONDITIONAL GO \| NO-GO \| BLOCKED \| DEFERRED / NOT V1 SCOPE>` |
| Evidence ids | `<all actual available ids; complete for GO/CONDITIONAL GO \| none: reason only if none exist>` |
| Accepted package commit | `<actual if observed; exact for GO/CONDITIONAL GO \| unknown/not_observed/not_applicable: reason only if unavailable>` |
| Accepted package label | `<actual if observed; exact for GO/CONDITIONAL GO \| unknown/not_observed/not_applicable: reason only if unavailable>` |
| Package ZIP created/applicability | `<true with exact checksum \| false/not_applicable with reason>` |
| Package ZIP SHA-256 | `<exact when zipCreated=true \| not_applicable: zipCreated=false>` |
| Inventory evidence record id | `<actual if created; exact for GO/CONDITIONAL GO \| not_created/not_observed/not_applicable: reason only if unavailable>` |
| Inventory observed at UTC | `<exact for GO/CONDITIONAL GO \| not_observed/not_applicable: reason>` |
| Inventory approved maximum age seconds | `<exact human-approved value for GO/CONDITIONAL GO \| not_approved/not_applicable: reason>` |
| Preview execution deadline UTC | `<exact for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Manifest-preparation approval id | `<actual if issued; required for GO/CONDITIONAL GO \| not_approved/not_applicable: reason only if unavailable>` |
| Manifest-preparation claim/completion deadline UTC | `<exact human-supplied value if issued; required for GO/CONDITIONAL GO \| not_approved/not_applicable: reason>` |
| Manifest-preparation approval terminal state | `<actual if issued; consumed for GO/CONDITIONAL GO \| not_approved/not_applicable: reason only if unavailable>` |
| Protected content manifest record id | `<actual if created; required for GO/CONDITIONAL GO \| not_created/not_applicable: reason only if unavailable>` |
| Protected content manifest prepared at UTC | `<exact for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Protected content manifest execution deadline UTC | `<exact for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Protected content manifest terminal state | `<actual terminal state if stage ran; consumed for GO/CONDITIONAL GO \| not_created/not_run/not_applicable: reason only if unreached>` |
| Protected immutable content snapshot record id | `<actual if created; required for GO/CONDITIONAL GO \| not_created/not_applicable: reason only if unavailable>` |
| Protected content snapshot terminal state | `<previewed only for zero-target no_upload GO/CONDITIONAL GO \| completed when Start/Retry occurred \| actual non-proceed state for NO-GO/BLOCKED \| not_created/not_run/not_applicable: reason>` |
| Protected content snapshot byte ceiling | `<actual approved ceiling; required if created \| not_created/not_applicable: reason>` |
| Protected content snapshot retention deadline | `<actual deadline; required if created \| not_created/not_applicable: reason>` |
| Protected content snapshot disposition state | `<actual state; required if created \| not_created/not_applicable: reason>` |
| Snapshot disposition evidence id | `<actual after disposal \| not_triggered: reason only while valid access remains>` |
| Preview approval id | `<actual if issued; required for GO/CONDITIONAL GO \| not_approved/not_applicable: reason only if unavailable>` |
| Preview approval terminal state | `<actual if issued; consumed for GO/CONDITIONAL GO \| not_approved/not_applicable: reason only if unavailable>` |
| Preview run id | `<actual if created; required for GO/CONDITIONAL GO \| not_run/not_applicable: reason only if unreached>` |
| Preview partial-overlap rows | `<exact count from the same Preview; required for GO/CONDITIONAL GO>` |
| Partial-overlap disposition/approver/evidence id | `<excluded_and_human_accepted / <named approver> / <opaque evidence id> for the current target-only policy, or exact separately approved policy result; required for GO/CONDITIONAL GO>` |
| Final pre-call snapshot check observed at UTC | `<exact for GO/CONDITIONAL GO \| not_observed/not_applicable: reason>` |
| Final pre-call snapshot unchanged | `<true for GO/CONDITIONAL GO \| not_observed/not_applicable: reason>` |
| Atomic snapshot binding evidence id | `<actual if created; required for GO/CONDITIONAL GO \| not_created/not_applicable: reason only if unavailable>` |
| Trusted target baseline id/alias/state/evidence | `<same opaque id/privacy-safe alias/verified state/safe evidence across every target stage; required for GO/CONDITIONAL GO \| not_provisioned/not_applicable: reason>` |
| Target-identity preparation approval id/state/deadline/claim owner/fence | `<actual / consumed / exact deadline / exact owner id / fence for GO/CONDITIONAL GO \| not_approved/not_applicable: reason>` |
| Protected exact target DB binding id | `<same opaque id verified by Preview and every Start/Retry/marker/reconciliation stage; required for GO/CONDITIONAL GO \| not_observed/not_applicable: reason>` |
| Target DB binding terminal state/validity/evidence id | `<completed for an accepted zero-target no_upload or terminal accepted Start/Retry chain; exact validity/evidence required for GO/CONDITIONAL GO \| actual/not_observed/not_applicable: reason>` |
| Exact-target global coordinator id/state/owner/consumer/generation/evidence | `<same singleton id; terminal state; final chain owner/no active consumer/generation/evidence required for GO/CONDITIONAL GO; recovery_disposition_pending is never proceed \| actual/not_created/not_applicable: reason>` |
| Target operation fence id/chain state/upload branch/Delete branch/consumer/generation/evidence | `<same protected fence id; terminal chain state; upload and Delete branches terminal or not_eligible; no active consumer; exact final generation/evidence for GO/CONDITIONAL GO \| actual/not_created/not_applicable: reason>` |
| Start Upload approval id/state/deadline | `<actual if issued; consumed when one job committed \| not_approved/not_applicable: reason>` |
| Start Upload action maximum duration seconds | `<actual if Start approval issued \| not_approved/not_applicable: reason>` |
| Start Upload snapshot disposition margin seconds | `<actual if Start approval issued \| not_approved/not_applicable: reason>` |
| Start Upload snapshot action lease id/expiry/state | `<actual if Start job created; released_committed or released_rolled_back for an accepted recovered chain \| not_created/not_applicable: reason>` |
| Start Upload pre-reserved mutation id/outcome/evidence id | `<exact approval-bound id if Start job created; authoritative committed or rolled_back evidence required for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Start Upload approved-absent set binding/distinct-key count/target-revalidation evidence | `<exact protected binding/count/evidence if Start created \| not_created/not_applicable: reason>` |
| Upload job id | `<actual if created \| not_created/not_applicable: reason>` |
| Upload job terminal status | `<succeeded, or failed/retryable/cancelled only with authoritative rollback plus a later accepted successful Retry \| actual/not_applicable: reason>` |
| Retry approval id/state/deadline, repeat per action | `<every actual issued approval; consumed when its action record committed \| not_approved/not_applicable: reason>` |
| Retry reconciliation source action/failure class, creation state/owner claim/fence/expiry/evidence plus record id/state/observation/claim deadline and source action/mutation/outcome binding, repeat per action | `<every source entitlement and protected record claimed by Retry; exact eligible-class fenced publication and record_consumed/consumed for an accepted chain \| not_created/not_applicable: reason>` |
| Retry reconciliation retention/disposition/evidence, repeat per action | `<every private subset; disposed with safe evidence for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Retry action maximum duration/disposition margin, repeat per action | `<every actual approved pair \| not_approved/not_applicable: reason>` |
| Retry snapshot action lease id/expiry/state, repeat per action | `<every actual created lease; released_committed for final success or released_rolled_back for an accepted prior retry \| not_created/not_applicable: reason>` |
| Retry pre-reserved mutation id/outcome/evidence id, repeat per action | `<every exact approval-bound mutation; authoritative committed or rolled_back evidence required for GO/CONDITIONAL GO \| not_created/not_applicable: reason>` |
| Retry approved-absent set binding/distinct-key count/target-revalidation evidence, repeat per action | `<every exact protected binding/count/evidence for an accepted action \| not_created/not_applicable: reason>` |
| Retry job/event id, repeat per action | `<every actual if created \| not_created/not_applicable: reason>` |
| Retry terminal status, repeat per action | `<final action succeeded; earlier failure/cancellation allowed only with authoritative rollback and fresh reconciliation \| actual/not_applicable: reason>` |
| Remaining retryable physical rows | `<0 for GO/CONDITIONAL GO \| actual/not_observed/not_applicable: reason>` |
| Final operational decision | `<no_upload \| upload_succeeded \| failed_preserved \| blocked>` |
| Delete execution in this cutover | `<excluded required for GO/CONDITIONAL GO \| actual violation: force NO-GO/BLOCKED>` |
| Operator PC class | `<actual if observed; exact for GO/CONDITIONAL GO \| unknown/not_observed/not_applicable: reason only if unavailable>` |
| Privacy-safe exact-source alias | `<actual if observed; exact for GO/CONDITIONAL GO \| unknown/not_observed/not_applicable: reason only if unavailable>` |
| Source class | `<actual if observed; exact for GO/CONDITIONAL GO \| unknown/not_observed/not_applicable: reason only if unavailable>` |
| Reviewer | `<reviewer; mandatory for every decision>` |
| Approver | `<approver; mandatory for every decision>` |
| Date/time | `<ISO-8601 local time; mandatory for every decision>` |
| Blocking or missing-evidence reasons | `<none for GO/CONDITIONAL GO \| required reason list for stop/defer>` |
| Residual risks | `<acceptedRisks>` |
| Next action | `<nextAction; mandatory for every decision>` |

Decision-conditional rules:

- `GO` or `CONDITIONAL GO` requires every lifecycle identifier above, including
  exact equality of trusted target baseline id/alias/state/evidence, target-
  identity preparation approval id/state/deadline/claim owner/fence, and
  target DB binding id/state/validity/evidence across the protected result,
  Preview, every Start/Retry/marker/reconciliation stage, and final sign-off;
  exact equality of target operation fence id plus every observed generation/
  evidence transition, with one consumer at a time and both upload/Delete
  branches terminal or `not_eligible` at final sign-off;
  exact equality of the singleton target-global coordinator id and its owner/
  consumer/generation/evidence transitions, with no overlapping older/newer
  Preview chain;
  exact equality with the consumed protected manifest and succeeded Preview
  evidence; plus the exact immutable snapshot id/state and exact Start/Retry
  approval/job identifiers when those stages occurred,
  and the proceed acknowledgement below.
- `GO` or `CONDITIONAL GO` requires the exact `partialOverlapRows` count to equal
  the bound Preview evidence and a named human approver plus opaque evidence id
  for `excluded_and_human_accepted`, or an exact separately approved policy
  result. Missing, inferred, or mismatched disposition forces `NO-GO`/`BLOCKED`.
- For `GO`/`CONDITIONAL GO`, snapshot state `previewed` is permitted only when
  the bound Preview has zero target rows and `finalDecision=no_upload`. If Start
  or Retry occurred, snapshot state must be `completed` and the final mutation
  must be target-marker-proven `committed`, lease `released_committed`, and job/
  action terminal `succeeded`, and `finalDecision` must be `upload_succeeded`.
  Conversely, `finalDecision=failed_preserved|blocked` cannot support a proceed
  decision. An earlier failed/retryable/cancelled Start or
  Retry is allowed in an accepted recovered sequence only when its target marker
  proves complete rollback, its lease is `released_rolled_back`, a protected
  fresh exact DB-reconciliation record of its entire attempted subset defines
  and is consumed by the next Retry scope, and every later approval/action
  binding, including the trusted target baseline id/alias/state/evidence, target-
  identity preparation approval id/state/deadline/claim owner/fence, and protected exact target DB
  binding id/state/validity/evidence, is preserved,
  remains within its approved validity for every DB read/write, and is
  revalidated. Every consumed/invalid reconciliation private subset is
  `disposed` with safe evidence. Every committed action also has exact protected
  absent-set/distinct-key bindings and transaction-time absence/committed-set
  evidence proving no overwrite. Remaining retryable
  physical rows must be zero. For either proceed path,
  snapshot disposition must be `disposed` with a
  valid `snapshotDispositionEvidenceId`. `upload_bound`, `retryable`, `claimed`, `invalid`,
  `disposal_failed_blocked`, `expired_rolled_back`, `commit_unknown_blocked`, an
  active/missing lease or missing authoritative mutation-outcome evidence for a
  created action, an unproven/partial rollback, nonterminal jobs, or remaining
  retryable rows force `NO-GO` or `BLOCKED`.
  A Start target-state-drift/conflict abort is never an accepted recovered action
  in that chain: it invalidates the chain and requires an independent fresh
  Preview/manifest/snapshot approval chain. Retry target drift may recover only
  through its new whole-attempt reconciliation record and separate approval.
- `GO`/`CONDITIONAL GO` requires Delete to be `excluded`. Any operational delete
  executed or authorized inside this cutover forces `NO-GO`/`BLOCKED`; a future
  hardened delete has its own plan, approval, evidence, and sign-off and cannot
  be imported into this record.
- `NO-GO`, `BLOCKED`, or `DEFERRED / NOT V1 SCOPE` uses explicit
  actual identifiers and terminal states for every stage that occurred. It uses
  `unknown`, `not_observed`, `not_created`, `not_approved`, `not_run`, or
  `not_applicable: reason` only for evidence that is genuinely unavailable or a
  stage never reached. Preserving a consumed manifest, succeeded Preview, or
  other successful intermediate evidence does not authorize `GO`. Decision,
  reviewer, approver, time, blocking/missing-evidence reasons, and next action
  remain mandatory.

Proceed acknowledgement for `GO` or `CONDITIONAL GO` only:

```text
I reviewed the evidence ids above and approve the recorded decision only for the
accepted package commit/label and ZIP checksum/applicability, inventory record
and observation/max-age/deadline fields, manifest-preparation approval plus its
claim/completed-publication deadline, consumed
protected manifest record and prepared/deadline fields, immutable content
snapshot record/state/retention/disposition fields, Preview approval/run and
final pre-call check, atomic snapshot binding evidence, the target-identity
trust anchor baseline id/privacy-safe alias/verified state/safe evidence,
preparation approval id/state/claim-publication deadline/claim owner/fence and protected exact
target DB binding id/state/validity/evidence, exact-target singleton coordinator
id/state/owner/consumer/generation/evidence, target operation fence id/chain
state/upload branch/Delete branch/consumer/generation/evidence, any Start/Retry approval,
pre-reserved mutation id, Retry reconciliation creation entitlement/record/
private-subset disposition evidence, approved-absent set and transaction-time
revalidation evidence, action-duration/
disposition-margin, lease, target-mutation outcome/evidence, and
job identifiers for stages that
occurred, the exact Preview partial-overlap row count and its
`excluded_and_human_accepted` disposition (or named separately approved policy)
with approver/evidence id, operator PC class, privacy-safe exact-source alias,
source class, and time window named in this record. Every lifecycle identifier exactly
matches the consumed manifest and succeeded Preview evidence. This sign-off does
not approve any future upload,
retry, delete, reset, cleanup, migration, LAN exposure, deployment, or feature
gate change outside the evidence and approvals listed here.
```

Stop/defer acknowledgement for `NO-GO`, `BLOCKED`, or
`DEFERRED / NOT V1 SCOPE` only:

```text
I reviewed the recorded blockers or scope decision. Every stage that occurred preserves its actual identifiers and terminal states, including consumed manifest or succeeded Preview evidence. Only genuinely unavailable or unreached fields are marked unknown, not_observed, not_created, not_approved, not_run, or not_applicable with a reason. The decision, reviewer, approver, time, blocking/missing-evidence reasons, and next action are recorded. Successful intermediate evidence does not authorize GO, upload, retry, delete, or cutover.
```

## Recommended Next Work Packages

### WP-A: non-destructive operator-PC route/config/audit smoke evidence

Status: complete for the current source-run evidence window. Sanitized route,
health, config, runtime, Audit, and Job Logs observations were captured without
mutation. Accepted package metadata remains a final sign-off condition.

### WP-B: read-only inventory precheck evidence

Status: partial baseline only in `docs/182`, record
`inv_20260815T031829Z_0d41338f`. The record binds a newly assembled package
artifact and read-only inventory counts, but the safe operator PC class and
privacy-safe exact-source alias are missing. It does not prove that package is
installed or executing and does not retroactively validate the earlier Preview.
Do not refresh for approval yet. First complete WP-C atomic binding/target-
identity lifecycles, tests, and package rebuild/verification; ensure a separately
controlled pre-provisioned verified target baseline exists; then refresh the
inventory and create a successor record before any approval.

### WP-C: atomic Preview binding, then approval and evidence capture

Status: partial for run `prv_ca38650a9e7d`. The separately approved run
succeeded with DB reachable, zero target/risky files, 64,766 partial-overlap
rows, matching Audit evidence, and no operational DB mutation. It predates
`docs/182` and cannot be bound to that later inventory retroactively. The next
action is a separately authorized production implementation and test package for
atomic content-manifest binding plus an immutable snapshot retained through
Preview, Start, and Retry, followed by package rebuild and verification.
Only after those pass and a separately controlled pre-provisioned verified target
baseline already exists may a successor inventory be refreshed. A separate exact
manifest-preparation approval must then create a protected single-use record;
after its safe result is reviewed, a separate read-only target-identity
preparation approval must compare observed exact identity to that baseline and
its opaque exact-match result must be human-reviewed. Only then may an exact
Preview approval name the entire chain. WP-C does not authorize baseline
provisioning/rotation.

### WP-D: Start Upload approval package, only if Preview proves target rows

Status: not applicable for the current evidence window because target rows were
zero and Start Upload was disabled. Future execution also requires the protected
single-use Start approval lifecycle, immutable-snapshot job binding, and bounded
active-use lease with all-or-nothing rollback implementation/tests. Prepare a
package only after that gate and a fresh Preview prove nonzero target rows; the
worker must use only that Preview snapshot and must not run without explicit
approval.

### WP-E: Retry Failed approval package, only if failed/retryable rows remain

Status: not applicable. No upload was created and no retryable rows remain from
this evidence window. Future execution also requires the protected single-use
Retry approval lifecycle, same-snapshot retry binding, and bounded active-use
lease with all-or-nothing rollback implementation/tests before any approval can
be used.

### WP-F: destructive delete approval package, only if separately required

Status: excluded from this recommendation. If delete becomes business-required,
use `docs/171` as evidence input but do not treat its wording alone as runtime
enforcement. First implement/test a protected expiring single-use preflight
approval atomically bound to exactly one preflight and a separate protected
single-consumer ready preflight result, then a separate protected expiring
single-use delete approval atomically claimed with that result and exactly one
delete run, plus the source-provenance snapshot and atomic complete-row DB-before-
image/marker, complete DELETE side-effect/recoverability binding, exact restore,
and committed dual-record versus aborted source-only disposition contract under a
separate plan; do not bundle it with upload cutover.

### WP-G: legacy CSV fixture expansion

Status: complete for V2 WP-01 scope with representative UTF-8/CP949 PLC,
temperature, and integrated fixtures. Add future fixtures only when a new legacy
shape is discovered.

### WP-H: large CSV Preview soak

Status: complete for the current evidence window. The deterministic 25,000-row
synthetic soak and separately approved real `folder_all` Preview both passed.

### WP-I: final package binding and human cutover sign-off

Goal: after WP-C implements and tests atomic content binding with an immutable
snapshot retained through Preview/Start/Retry and produces a new package, verify
that exact executing package label/source commit, repeat the
read-only inventory immediately before any Preview approval, create a successor
record with human-supplied safe operator PC and privacy-safe exact-source
bindings, confirm a separately controlled pre-provisioned verified target
baseline, separately approve and review protected manifest preparation,
separately approve read-only target-identity preparation and human-review its
exact-match opaque result, then request the later exact Preview approval. This
work does not authorize baseline provisioning/rotation. Record any required human disposition
of partial-overlap rows, resolve or accept the Grafana/Vector caveat with an
owner and stop/rollback procedure, and fill the Final Sign-Off Record. This
sign-off work does not itself approve or execute any mutation.

## WP-02 Verification Performed

Read-only checks performed on 2026-07-13:

- `git status --short --branch`, `git rev-parse HEAD`, and recent merge history;
- sanitized `GET /api/health`, `GET /api/config`, and
  `GET /api/runtime/local-supabase` observations;
- sanitized latest Preview, Audit result-class counts, and latest Upload Job
  detail/event observations;
- `npm run qa:backend-served-responsive`, covering Dashboard, Upload Preview,
  Upload Job, Job Logs, Audit Logs, and Settings at 390, 480, 640, 834, 1024,
  1280, and 1440 px.

Results:

- current `main` and `origin/main` matched `5695b93` before documentation edits;
- core runtime services were ready and target classes passed;
- Grafana/Vector produced the recorded non-core attention;
- latest approved Preview matched `wp02-preview-prv_ca38650a9e7d`;
- existing Audit success/failure/blocked classes and terminal Job events were
  visible;
- responsive QA passed with no layout issues, console errors, or failed
  requests.

The backend/frontend automated suites were not rerun for WP-02 because only
Markdown status documents changed; the merged V2 WP-01 pre-merge evidence is
437 backend tests plus frontend unit, typecheck, build, and routing checks.

WP-02 did not create a Preview, upload, retry, delete, Settings save, runtime
operation, LAN change, deployment, migration, reset, cleanup, or data mutation.

## Original Documentation Verification Performed

Commands run for this documentation update:

```powershell
git branch --show-current
git status --short --branch
Test-Path docs/176_v1_cutover_go_no_go_validation_plan.md
git switch main
git pull --ff-only origin main
git switch -c docs/v1-cutover-go-no-go-validation-plan
rg -n "docs/175|Source Documents|Upload Job API smoke|previewRunId|expectedTargetRows|expectedTargetFiles" README.md
rg -n "Core Ops|not in v1|legacy upload state|Success Criteria|localhost|Supabase|Grafana|LAN|delete" docs/00_product_scope.md
rg -n "Core Ops|implemented|validation|evidence|LAN|Supabase|delete|upload verification|large CSV|fixture|Audit Logs" docs/01_development_roadmap.md
rg -n "Implemented Core Ops|Deferred pending approval/evidence|Review shell only|Intentional v1 exclusion|Safety gate" docs/158_operator_status_language_policy.md
rg -n "approval|does not approve|Preview-only|Start Upload|Retry Failed|Delete|Settings save|feature gate|reset|cleanup|LAN|deployment" docs/164_operator_data_mutation_safety_gate.md
rg -n "upload verification|date-scoped|delete expansion|LAN|schema attribution|legacy upload state|reset|cleanup|Deferred|blocked|review shell|operational" docs/165_v2_status_matrix.md
rg -n "does not approve|Already-in-DB|exact-key|approval|preflight|hard delete|Start Upload|Retry Failed|Settings save|reset|cleanup|Docker|LAN|Stop|blocked" docs/171_v2_operational_delete_verification_gate.md
rg -n "does not approve|evidence chain|Preview-only|Start Upload|Retry Failed|approval|sourceCommit|target rows|remaining physical rows|reset|cleanup|Docker|LAN|Stop|blocked|DB delta|row attribution" docs/173_v2_operational_upload_verification_gate.md
rg -n "Core Ops|Must-Fix|Deferred|Evidence Matrix|upload evidence|legacy CSV|large real CSV|operator-PC|Audit Logs|LAN|date-scoped|schema attribution|legacy upload state|reset|cleanup|README" docs/175_legacy_gui_replacement_gap_audit.md
rg -n "class UploadJobCreateRequest|expected_target_rows|expected_target_files|class RetryFailedRequest|expected_remaining_rows|expected_retry_files" backend/app/schemas/upload_jobs.py
rg -n "expected_target_rows_required|expected_remaining_rows_required|preview_run_id|expected_target_rows|expected_target_files|expected_remaining_rows|expected_retry_files" backend/app/api/upload_jobs.py
rg -n "to_camel|populate_by_name|target_rows|partial_overlap_rows|already_in_db|partial_overlap|risky|preview_run_id" backend/app/schemas/upload_preview.py
rg -n "expectedTargetRows|expectedTargetFiles|expectedRemainingRows|expectedRetryFiles|previewRunId" frontend/src/api/uploadJobs.ts frontend/src/pages/UploadPage.tsx
rg -n "@router.get|@router.put|api/config|settings.save|save_config|secret" backend/app/api/config.py backend/app/services/config_service.py
rg -n "@router.get|Audit|limit|safe|redact|AuditLog" backend/app/api/audit.py backend/app/db/audit_repository.py
rg -n "@router.post|@router.get|active_preview|upload.preview|blocked|dbStatus|previewRunId|summary|cancel" backend/app/api/upload_preview.py
rg -n "supabase start|supabase init|supabase db reset|docker rm|docker compose down|FORBIDDEN|allowed|start|stop|reset|cleanup|prune|rm|compose down|init" backend/app/services/runtime_control.py backend/app/services/command_runner.py
```

Files changed by this documentation update:

- `README.md`
- `docs/176_v1_cutover_go_no_go_validation_plan.md`

Tests run:

- Runtime tests were not run because this is a documentation-only change.

Checks run before commit:

- `git status --short --branch`: only `README.md` and
  `docs/176_v1_cutover_go_no_go_validation_plan.md` changed.
- `git diff --check`: passed; Git reported only the existing README
  working-copy LF-to-CRLF normalization warning and no whitespace errors.
- `git diff -- README.md`: Source Documents update only.
- `git status --short --branch`: confirms the new validation-plan document is
  untracked before staging and no runtime/code files are changed.

Forbidden commands intentionally not run:

- no Start Upload;
- no Retry Failed;
- no Upload Preview execution;
- no DB delete;
- no Settings save;
- no Local Supabase start/stop;
- no Supabase init/reset/migration/backfill/cleanup;
- no Docker cleanup/rm/prune/volume delete/compose up/down;
- no LAN enablement;
- no deployment;
- no production DB access.
