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
`NO-GO` for cutover execution. Accepted package metadata, a compliant
pre-Preview inventory record, human disposition of partial-overlap rows, final
sign-off, and explicit ownership of the non-core Grafana/Vector attention state
remain hard gates before a `CONDITIONAL GO` candidate can proceed.

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
- Upload Preview execution without the Preview-only approval required by
  `docs/164` and `docs/173`;
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
  upload evidence chain: inventory, Preview-only, Start Upload, and Retry Failed.
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
| `GO` | V1 Core Ops replacement is approved for the named package, operator PC, source class, and evidence window. | All required non-destructive evidence is current; Preview-only evidence is fresh and succeeded; Start Upload evidence exists if target rows were approved; Audit Logs and Job Logs visibility are proven; final sign-off is complete. | Preview proves target rows, a separately approved Start Upload succeeds, no retryable rows remain, and sanitized evidence is reviewed. |
| `CONDITIONAL GO` | Replacement may proceed only inside named limits with explicit residual risk acceptance. | All hard stop conditions are clear, but one non-core caveat remains documented with an owner and rollback/stop procedure. | Grafana status is attention-only while API, DB, Preview, Audit, and upload evidence are normal. |
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
| `wp02-preview-prv_ca38650a9e7d` | Separately approved `folder_all` large-source Preview persisted local run/audit state and completed `succeeded/reachable`: 12 total, 11 already in DB, 1 partial overlap, 0 target, 0 risky, 0 excluded, 0 target rows, 64,766 partial-overlap rows, 3,386,260 DB-matched rows, and Start Upload disabled. Partial-overlap rows are excluded from the target-only upload path. | Preview behavior passed; formal inventory/package gate and partial-overlap disposition pending |
| `wp02-audit-readonly-20260713` | Read-only Audit API inspection returned existing success, failure, blocked, and cancelled classes; the approved Preview had matching success evidence. No new failure was manufactured. | Pass |
| `wp02-joblogs-readonly-20260713` | Latest Upload Job was terminal `succeeded` with persisted files/events, and Job Logs rendered without browser errors. No job was created. | Pass |
| `wp02-responsive-core-routes-20260713` | Dashboard, Upload Preview, Upload Job, Job Logs, Audit Logs, and Settings passed the existing 390-1440 px backend-served QA with zero layout issues, console errors, or failed requests. | Pass |
| `wp02-safety-exclusions-20260713` | WP-02 performed no Preview creation, Start Upload, Retry Failed, delete, Settings save, runtime start/stop, LAN, deployment, migration, reset, cleanup, or data mutation. | Pass |

Technical recommendation: `NO-GO` for V1 Core Ops cutover execution on the
current evidence set. The implementation and Preview behavior support a future
`CONDITIONAL GO` candidate, but the executing artifact is not bound to accepted
package metadata, the required pre-Preview inventory record is not identified,
64,766 partial-overlap rows have no recorded human disposition, final sign-off
is blank, and Grafana/Vector attention has no acceptance owner.

Conditions to reach a `CONDITIONAL GO` candidate:

1. Verify the accepted package label and `package-build-info.json` source commit
   against the artifact that the operator will actually run.
2. Identify the compliant inventory evidence created before Preview approval,
   including source class, observed files, physical-row ceiling, record id, and
   reviewer. If it does not exist, do not infer or autofill it from Preview;
   repeat the precheck/Preview chain only under a future separate approval.
3. Record human disposition of the 64,766 partial-overlap rows, which remain
   excluded from target-only upload, without treating them as zero unmatched
   local rows.
4. Resolve Grafana/Vector attention or record explicit residual-risk acceptance,
   an owner, and the non-destructive stop/rollback procedure.
5. Complete the final human sign-off record below for the exact package,
   operator PC class, source class, and evidence window.

The zero-target Preview supports `no target-only upload` for this evidence
window. It does not mean every local row is DB-matched: 64,766 rows are in the
partial-overlap class and remain excluded from Start Upload. No upload or retry
should be created merely to turn a not-applicable gate into a test case.

## Required Cutover Evidence Matrix

| Evidence area | Required artifact | Allowed command or observation class | Forbidden actions | Pass condition | Fail / stop condition | Evidence owner | Source reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Package/source commit verification | Package label, source commit, build metadata, and source tree commit record | Read-only package metadata inspection; `git rev-parse HEAD`; `git show --stat --oneline --name-status HEAD` | Rebuilding, deploying, or editing package metadata during evidence capture | Package source commit and label match the accepted package and docs | Missing, stale, or mismatched package metadata | Maintainer | `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| README/API smoke contract verification | Contract note proving README smoke uses `previewRunId`, `expectedTargetRows`, and `expectedTargetFiles` | Read-only README and schema inspection | Start Upload execution | README snippet matches backend required approval-count contract | Missing `expectedTargetRows`, stale camelCase fields, or ad hoc payload | Maintainer | `README.md`; `backend/app/api/upload_jobs.py`; `backend/app/schemas/upload_preview.py` |
| GET `/api/config` safe snapshot | Sanitized config evidence showing source class, target classes, mode, and override classes | `GET /api/config` against an already running local operator backend; store sanitized classes only | `PUT /api/config`, Settings save, raw path or secret capture | Snapshot confirms expected API mode/source class without raw paths or secret values | Config source class is wrong, raw sensitive value would be recorded, or endpoint unavailable | Maintainer/operator | `backend/app/api/config.py`; `backend/app/services/config_service.py`; `README.md` |
| Local Supabase status evidence | Sanitized runtime readiness/status-class output | Read-only dashboard/runtime status observation and existing status endpoints | Start/stop/reset/cleanup/init/migration | Status proves local Supabase readiness class or a clear blocked class | DB-dependent class is blocked and unresolved | Maintainer/operator | `docs/00_product_scope.md`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Local Supabase start/stop evidence, only if separately approved | Operation id, event ids, before/after status classes, and audit ids | Runtime start/stop only after separate approval and no active job/preview | Supabase init/reset, Docker create/rm/prune/up/down, volume deletion | Start/stop is bounded, audited, and returns expected readiness or stopped class | Required containers missing, active job/preview, broad cleanup requested, or audit unavailable | Maintainer/operator | `backend/app/services/runtime_control.py`; `backend/app/services/command_runner.py` |
| Read-only inventory precheck | Filled inventory template with counts, row ceiling, excluded data, and reviewer | Read-only file inventory/count procedure that stores no raw names, paths, content, or keys | Preview, upload, delete, settings save, cleanup, LAN, deployment | File count and approved physical row ceiling are current and reviewer-signed | Guessed count, stale inventory, source class mismatch, or raw sensitive evidence | Maintainer with operator review | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md` |
| Preview-only evidence | Preview approval id, preview run id, summary counts, DB status class, audit evidence | Exactly one separately approved Preview-only run | Start Upload, Retry Failed, Delete, Settings save, reset, cleanup, LAN, deployment | Preview is latest, fresh, succeeded, DB reachable, and counts match approval ceiling | Risky count > 0, DB unreachable, count mismatch, stale preview, active conflict unresolved | Maintainer/operator | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_preview.py` |
| Start Upload approval package, separate and optional | Exact approval text and record naming preview run, target rows, source class, and package commit | Approval preparation only until the operator explicitly approves | Running Start Upload from this plan; bundling Retry Failed/Delete/Settings save | Fresh Preview proves target rows and approval text matches exact target-only rows | Zero target rows, mismatch across UI/API/approval, stale preview, or missing approval | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_jobs.py` |
| Retry Failed approval package, separate and conditional | Retry approval record naming job id and remaining physical rows | Approval preparation only after failed/retryable job evidence | Automatic retry, broad cleanup, DB reset, or retry without exact remaining rows | Failed/retryable rows are known and separate approval exists | No retryable rows, count unknown, root failure not preserved, or approval missing | Operator approval with maintainer evidence | `docs/164_operator_data_mutation_safety_gate.md`; `docs/173_v2_operational_upload_verification_gate.md`; `backend/app/api/upload_jobs.py`; `frontend/src/pages/UploadPage.tsx` |
| Audit Logs success/failure visibility | Sanitized Audit Logs API/UI evidence for success, failure, and blocked classes | `GET /api/audit?limit=1`; UI Audit Logs observation; non-destructive failure-path validation | Raw params JSON search, arbitrary SQL, secret capture, destructive failure creation | Operators can see relevant safe action/result/reason evidence | Audit unavailable, missing failure rows, unsafe raw values displayed | Maintainer QA and operator | `backend/app/api/audit.py`; `backend/app/db/audit_repository.py`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Job Logs visibility | Upload Job tab or API event evidence for latest job states | Read-only job/detail/event observation; SSE replay observation | Creating upload/retry jobs without approval | Job events and final states are visible and understandable | Missing events, final status unclear, or errors hidden | Maintainer QA and operator | `backend/app/api/upload_jobs.py`; `backend/app/db/upload_job_repository.py`; `frontend/src/pages/UploadPage.tsx`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Representative legacy CSV fixture coverage | Test or review evidence for known legacy edge cases | Non-operational fixture tests or Preview-only fixture evidence in disposable/non-production context | Operational upload mutation; raw operational CSV content in evidence | Representative fixtures cover expected legacy parsing/classification cases | Known legacy CSV shape untested or classification drift found | Maintainer QA | `docs/01_development_roadmap.md`; `docs/175_legacy_gui_replacement_gap_audit.md`; `docs/00_product_scope.md` |
| Large real CSV Preview soak | Preview-only soak evidence with sanitized counts and timing | Only after separate Preview-only approval for the real source class | Start Upload, Retry Failed, Delete, cleanup, raw file evidence | Large Preview completes within accepted bounds and produces stable classifications | Timeout, memory failure, risky rows, DB unreachable, or count mismatch | Maintainer/operator | `docs/01_development_roadmap.md`; `docs/175_legacy_gui_replacement_gap_audit.md`; `docs/173_v2_operational_upload_verification_gate.md` |
| Operator-PC browser/UI evidence | Sanitized route screenshots or observations for `/`, `/upload`, `/logs`, `/settings` | Browser route load checks against already running local package; screenshots only after redaction review | Capturing secrets, raw paths, filenames, DB URLs, tokens, internal URLs, CSV content | Routes load in API mode and show expected readiness/log surfaces | Route unavailable, mock mode mistaken as operational, or sensitive data visible | Maintainer/operator | `backend/app/main.py`; `README.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| Rollback / stop procedure evidence | Runbook record for stopping app use and reverting to legacy GUI/manual procedure | Documentation review and operator acknowledgement | DB reset/cleanup as rollback; deleting evidence | Stop procedure is understood and no destructive cleanup is required | Rollback depends on destructive cleanup or unavailable legacy fallback | Release owner/operator | `docs/173_v2_operational_upload_verification_gate.md`; `docs/171_v2_operational_delete_verification_gate.md`; `README.md` |
| Destructive delete exclusion or separate `docs/171` package | Either explicit exclusion or a complete destructive approval package | Documentation-only exclusion for V1 cutover; `docs/171` package if delete is requested | Operational DB delete from this plan | Delete is excluded from cutover or separately approved with exact-key scope | Request bundles delete with Preview/Start/Retry/settings/reset/LAN | Operator approval plus maintainer evidence | `docs/171_v2_operational_delete_verification_gate.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |
| LAN exclusion | Localhost-only sign-off | Config/doc review; `/api/health` sanitized LAN state if available | LAN enablement, non-loopback bind, LAN CORS widening, auth/session rollout | V1 remains localhost-only and LAN stays deferred | Non-loopback access requested or LAN feature gate enabled | Release owner | `docs/00_product_scope.md`; `backend/app/core/lan_security.py`; `docs/165_v2_status_matrix.md` |
| Supabase reset/cleanup exclusion | Explicit exclusion record | Documentation review and command-policy review | `supabase init`, `supabase db reset`, Docker rm/prune/compose up/down, volume delete | No reset/cleanup/create command is part of cutover evidence | Missing containers trigger cleanup request instead of blocked evidence | Release owner/maintainer | `README.md`; `backend/app/services/command_runner.py` |
| Security/secrets redaction | Sanitized evidence review checklist | Redaction review before attaching evidence | Raw paths, filenames, CSV content, DB URLs, tokens, JWTs, Authorization values, exact keys, internal URLs, secrets | Evidence contains only safe ids, classes, counts, hashes, and reason codes | Sensitive value would be written or screenshot cannot be safely redacted | Maintainer/security reviewer | `README.md`; `backend/app/db/audit_repository.py`; `docs/171_v2_operational_delete_verification_gate.md` |
| Final sign-off record | Completed sign-off table with decision, evidence ids, accepted package, residual risks, and next action | Documentation-only sign-off | Treating old evidence or future folder growth as approval | Approver accepts exact evidence set and residual risks | Evidence ids missing, package mismatch, stale preview, or unresolved stop condition | Release owner/operator approver | `docs/173_v2_operational_upload_verification_gate.md`; `docs/175_legacy_gui_replacement_gap_audit.md` |

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

Use this template before requesting Preview-only approval. It records counts and
classes, not raw operational data.

| Field | Value |
| --- | --- |
| Evidence id | `<inventoryEvidenceId>` |
| Date/time | `<ISO-8601 local time>` |
| Operator PC class | `<operatorPcClass>` |
| Package source commit | `<sourceCommit>` |
| Package label | `<packageLabel>` |
| Source class, not raw path | `<sourceClass>` |
| Observed file count | `<fileCount>` |
| Approved physical row ceiling | `<rowLimit>` |
| Inventory evidence hash or internal record id | `<inventoryHashOrRecordId>` |
| Excluded data | `<excludedDataClasses>` |
| Stop condition result | `<clear \| blocked: reason>` |
| Reviewer | `<reviewer>` |

Do not record raw filenames, raw paths, raw CSV content, raw timestamp/device_id
keys, DB URLs, tokens, JWTs, Authorization values, internal URLs, or secrets.

## Preview-Only Approval Template

This approval is separate from the validation plan. It must be filled from a
fresh read-only inventory precheck.

```text
I approve exactly one Upload Preview-only run from package sourceCommit <sourceCommit>.
The approved source class is <sourceClass>.
The approved file count is <fileCount>.
The approved physical row ceiling is <rowLimit>.
This approval does not approve Start Upload, Retry Failed, Delete, Settings save,
feature gate enablement, Supabase reset/cleanup, Docker cleanup, LAN, or deployment.
```

Stop if the requested source class, file count, row ceiling, package commit, or
operator PC differs from the fresh inventory evidence.

## Preview-Only Evidence Template

| Field | Value |
| --- | --- |
| Preview approval id | `<previewApprovalId>` |
| Preview run id | `<previewRunId>` |
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
| Audit evidence | `<auditEvidenceId>` |
| Confirmation no mutation actions were bundled | `<yes/no plus note>` |

Pass requires `status=succeeded`, DB reachable/expected, `riskyCount=0`, and
matching counts across UI/API/evidence. A Preview with zero target rows may
support `no target-only upload`; it is not proof that partial-overlap rows are
absent and it is not Start Upload evidence.

## Start Upload Approval Template

This is separate and not approved by this validation plan. Request it only after
a fresh, succeeded Preview-only run proves exact target-only rows.

```text
I approve exactly one Start Upload for preview run <previewRunId> with target rows <targetRows>.
This approval is for package sourceCommit <sourceCommit> and source class <sourceClass>.
This approval does not approve Retry Failed, Delete, Settings save, or feature gate enablement.
```

Required before approval:

- fresh succeeded Preview-only evidence;
- preview run id;
- exact target-only rows;
- source class;
- package source commit;
- confirmation partial-overlap rows are not included unless separately approved;
- confirmation `expectedTargetRows` and `expectedTargetFiles` match the latest
  Preview detail.

## Start Upload Evidence Template

| Field | Value |
| --- | --- |
| Start approval id | `<startUploadApprovalId>` |
| Preview run id | `<previewRunId>` |
| Upload job id | `<uploadJobId>` |
| Approved target-only row count | `<targetRows>` |
| Job final status | `<succeeded \| failed \| blocked \| cancelled>` |
| Processed rows | `<processedRows>` |
| Uploaded rows | `<uploadedRows>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| DB delta evidence, only if explicitly approved and enabled | `<dbDeltaEvidenceId \| not approved>` |
| Row attribution evidence, only if explicitly approved and enabled | `<rowAttributionEvidenceId \| not approved>` |
| Unresolved failure condition | `<none \| reason>` |

If Start Upload fails after partial mutation, preserve job, audit, DB delta, and
row attribution evidence. Do not run Retry Failed or cleanup without a separate
approval.

## Retry Failed Approval And Evidence Template

Retry Failed is separate and conditional. It is not automatic rollback.

Required before requesting approval:

- failed or retryable upload job evidence;
- job id;
- exact remaining physical rows;
- source class and package commit;
- root failure class preserved;
- confirmation no broad cleanup is requested.

Approval wording:

```text
I approve exactly one Retry Failed for upload job <jobId> with remaining physical rows <remainingRows>.
This approval is for package sourceCommit <sourceCommit>.
This approval does not approve Start Upload, Delete, Settings save, or feature gate enablement.
```

Evidence after retry:

| Field | Value |
| --- | --- |
| Retry approval id | `<retryApprovalId>` |
| Source upload job id | `<jobId>` |
| Retry job id or event id | `<retryJobOrEventId>` |
| Approved remaining physical rows | `<remainingRows>` |
| Retry files | `<retryFiles>` |
| Final status | `<succeeded \| failed \| blocked \| cancelled>` |
| Accepted rows | `<acceptedRows>` |
| Audit evidence | `<auditEvidenceId>` |
| Job event evidence | `<jobEventEvidenceId>` |
| Stop-after-failure confirmation | `<yes/no plus reason>` |

If retry fails, stop. Preserve evidence. Do not run broad DB cleanup, reset, or
manual delete as a workaround.

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
| Preview-only readiness | `wp02-preview-prv_ca38650a9e7d` | `partial` | Execution succeeded with zero target/risky and DB reachable; inventory/package binding and disposition of 64,766 partial-overlap rows remain pending. |
| Logs/audit visibility | `wp02-audit-readonly-20260713`; `wp02-joblogs-readonly-20260713` | `pass` | Existing success/failure/blocked and terminal-job evidence were visible. |

Screenshots are allowed only if they do not expose secrets, raw paths, filenames,
raw DB URLs, tokens, JWTs, Authorization values, internal URLs, raw CSV content,
or exact keys.

## Go/No-Go Checklist

| Item | Required before GO | Evidence id | Status | Approver | Notes |
| --- | --- | --- | --- | --- | --- |
| Accepted package/source commit | Yes | `wp02-main-5695b93` | `pending: hard stop` | `<approver>` | Source tree is known; accepted executing package label/build metadata is not yet bound. |
| README/API smoke contract | Yes | `wp02-wp01-automated-5695b93` | `pass` | `<approver>` | Approval-count contract is covered. |
| Sanitized config snapshot | Yes | `wp02-config-runtime-20260713` | `pass` | `<approver>` | Safe classes only. |
| Local Supabase readiness | Yes | `wp02-config-runtime-20260713` | `pass` | `<approver>` | API/DB/Studio/Edge ready; non-core attention recorded separately. |
| Read-only inventory precheck | Yes | `<inventoryEvidenceId>` | `pending: record not identified` | `<approver>` | Preview results cannot retroactively prove the required precheck, row ceiling, record id, or reviewer. |
| Preview-only evidence | Yes, if upload cutover is being evaluated | `wp02-preview-prv_ca38650a9e7d` | `partial` | `<approver>` | Run succeeded/reachable with zero target/risky, but package/inventory record binding is pending and 64,766 partial-overlap rows need disposition. |
| Start Upload evidence | Yes when Preview proves approved target rows | `wp02-preview-prv_ca38650a9e7d` | `not applicable` | `<approver>` | Target rows were zero; Start Upload was disabled and not executed. |
| Retry Failed evidence | Conditional | `wp02-preview-prv_ca38650a9e7d` | `not applicable` | `<approver>` | No new upload or retryable rows. |
| Audit Logs failure visibility | Yes | `wp02-audit-readonly-20260713` | `pass` | `<approver>` | Existing safe success/failure/blocked classes visible. |
| Job Logs visibility | Yes | `wp02-joblogs-readonly-20260713` | `pass` | `<approver>` | Latest terminal status and events visible. |
| Representative CSV fixture coverage | Yes | `wp02-wp01-automated-5695b93` | `pass` | `<approver>` | UTF-8/CP949/integrated legacy classes covered. |
| Large real CSV Preview soak | Yes | `wp02-preview-prv_ca38650a9e7d` | `pass for execution behavior` | `<approver>` | Completed without risky/target rows; 64,766 partial-overlap rows remain excluded from target-only upload and require disposition. |
| Operator-PC UI route evidence | Yes | `wp02-responsive-core-routes-20260713` | `pass` | `<approver>` | Six Core Ops views, seven viewports, zero QA errors. |
| Rollback/stop procedure | Yes | `docs/173`; `README.md` | `pending: hard stop` | `<approver>` | Final approver must acknowledge legacy/manual fallback and non-destructive stop. |
| Delete excluded or separately approved | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Delete was excluded. |
| LAN excluded | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Localhost-only. |
| Reset/cleanup excluded | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | No Supabase/Docker destructive cleanup. |
| Secrets redaction complete | Yes | `wp02-safety-exclusions-20260713` | `pass` | `<approver>` | Only safe ids/classes/counts are retained. |
| Final sign-off record | Yes | `<evidenceId>` | `pending: hard stop` | `<approver>` | Human decision record remains blank; current execution recommendation is NO-GO. |

## Risk Register

| Risk statement | Severity | Likelihood | Mitigation | Owner or approval gate | Required evidence |
| --- | --- | --- | --- | --- | --- |
| Accepted package metadata is not bound to the verified source tree before final sign-off. | High | Medium | Verify `package-build-info.json`, package label, and source commit for the executing artifact. | Release owner/operator | Accepted package metadata and final sign-off |
| Missing pre-Preview inventory/package binding or unresolved partial-overlap rows are hidden by the zero-target result. | High | Medium | Do not infer the precheck from Preview; bind the package, locate or repeat the formal gate, and record disposition of all 64,766 partial-overlap rows. | Operator approval plus maintainer evidence capture | Fresh inventory/Preview record, package metadata, partial-overlap disposition; Start only if target rows exist |
| Grafana/Vector non-core attention is silently ignored or confused with core readiness. | Medium | Medium | Resolve it or record owner, residual-risk acceptance, and non-destructive stop/rollback procedure. | Release owner/operator | Sanitized runtime state and signed caveat |
| A new CSV or failure class escapes the current fixture/Audit coverage. | High | Low-medium | Add representative fixtures and keep failure-path API/UI checks in regression and approved operations. | Maintainer QA and operator sign-off | Fixture/soak and safe Audit/Job Logs evidence |
| Accidental destructive delete or cleanup is bundled into validation. | Production-critical | Low | Treat delete, reset, cleanup, and Docker destructive commands as hard exclusions unless separately approved. | `docs/171` or new destructive plan | Exclusion record or exact approval package |
| Package/source mismatch leads to testing the wrong build. | High | Low | Verify package metadata and source commit before every evidence package. | Release owner | Package commit, label, and hash/metadata evidence |
| Secrets or raw operational data leak into evidence. | High | Medium | Store only safe classes, counts, ids, hashes, and reason codes; review screenshots before attachment. | Security reviewer/maintainer | Redaction checklist and sanitized artifacts |

## Stop Conditions

Stop before GO, Preview, Start Upload, Retry Failed, delete, or any operator
cutover decision when any of these are true:

- package metadata, source commit, or package label is missing, unbound, stale,
  or mismatched;
- the compliant pre-Preview inventory record cannot be identified and must not
  be inferred or autofilled from Preview output;
- read-only inventory is missing, stale, broader than the requested scope, or
  guessed;
- physical row count or target row count is guessed;
- Preview is not fresh, latest, succeeded, and DB reachable;
- risky count is greater than zero;
- partial-overlap rows lack explicit human disposition for the cutover decision;
- target rows mismatch between UI, API, approval text, and evidence;
- Audit Logs evidence is unavailable;
- Job Logs evidence is unavailable for an upload decision;
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
| Evidence ids | `<evidenceIds>` |
| Accepted package commit | `<sourceCommit>` |
| Accepted package label | `<packageLabel>` |
| Operator PC | `<operatorPcClass>` |
| Reviewer | `<reviewer>` |
| Approver | `<approver>` |
| Date/time | `<ISO-8601 local time>` |
| Residual risks | `<acceptedRisks>` |
| Next action | `<nextAction>` |

Approver acknowledgement:

```text
I reviewed the evidence ids above and approve the recorded decision only for the
accepted package commit, package label, operator PC class, source class, and time
window named in this record. This sign-off does not approve any future upload,
retry, delete, reset, cleanup, migration, LAN exposure, deployment, or feature
gate change outside the evidence and approvals listed here.
```

## Recommended Next Work Packages

### WP-A: non-destructive operator-PC route/config/audit smoke evidence

Status: complete for the current source-run evidence window. Sanitized route,
health, config, runtime, Audit, and Job Logs observations were captured without
mutation. Accepted package metadata remains a final sign-off condition.

### WP-B: read-only inventory precheck evidence

Status: pending. No compliant pre-Preview inventory record is identified in this
branch. Do not infer or autofill its package/source scope, physical-row ceiling,
record id, or reviewer from the later Preview result. Locate the original record
or repeat the gate only under a future separate approval.

### WP-C: Preview-only approval and evidence capture

Status: partial for run `prv_ca38650a9e7d`. The separately approved run
succeeded with DB reachable, zero target/risky files, 64,766 partial-overlap
rows, matching Audit evidence, and no operational DB mutation. It cannot satisfy
cutover until package/inventory binding and partial-overlap disposition exist.

### WP-D: Start Upload approval package, only if Preview proves target rows

Status: not applicable for the current evidence window because target rows were
zero and Start Upload was disabled. Prepare a package only after a future fresh
Preview proves nonzero target rows; do not run without explicit approval.

### WP-E: Retry Failed approval package, only if failed/retryable rows remain

Status: not applicable. No upload was created and no retryable rows remain from
this evidence window.

### WP-F: destructive delete approval package, only if separately required

Status: excluded from this recommendation. If delete becomes business-required,
use `docs/171` and do not bundle it with upload cutover.

### WP-G: legacy CSV fixture expansion

Status: complete for V2 WP-01 scope with representative UTF-8/CP949 PLC,
temperature, and integrated fixtures. Add future fixtures only when a new legacy
shape is discovered.

### WP-H: large CSV Preview soak

Status: complete for the current evidence window. The deterministic 25,000-row
synthetic soak and separately approved real `folder_all` Preview both passed.

### WP-I: final package binding and human cutover sign-off

Goal: verify the exact executing package label/source commit, identify the
pre-Preview inventory record, record human disposition of partial-overlap rows,
resolve or accept the Grafana/Vector caveat with an owner and stop/rollback
procedure, and fill the Final Sign-Off Record. This is documentation/sign-off
work only and does not approve or execute any mutation.

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
