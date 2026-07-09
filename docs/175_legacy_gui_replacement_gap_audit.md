# Legacy GUI Replacement Gap Audit

## Executive Summary

Core Ops is mostly implemented in the current repository. The actual code has
Upload Preview, Start Upload, Retry Failed, upload progress/event logs, Audit
Logs, Settings save, local Supabase status/start/stop, Grafana status/link, and
the selected `already_in_db` exact-key delete path.

The remaining legacy-GUI-replacement work is not mainly new feature
implementation. The cutover still needs fresh operational evidence, operator
approval records for mutation flows, broader representative CSV validation,
operator-PC local Supabase E2E evidence, and final Audit Logs failure reporting
validation.

The following are not v1 cutover blockers unless separately re-scoped:
Multi-user LAN, executable date-scoped delete UI, delete expansion beyond the
selected `already_in_db` exact-key contract, Supabase schema attribution
migration/backfill, legacy GUI state import, and local Supabase
bootstrap/create/reset/cleanup.

## Evidence Matrix

| Area | Current classification | Actual code behavior | Documentation evidence | Remaining gate | Business risk | Recommended next action | Evidence paths with line references |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Upload Preview | Implemented Core Ops | `POST /api/upload/preview`, latest/detail/cancel routes exist; results are persisted and exact DB reconciliation is supported when DB URL is configured. | Roadmap marks backend API, persistence, scanning, key extraction, DB reconciliation, DB-unreachable handling, and UI done. | Fresh operational Preview evidence is still required before mutation gates. | Medium: stale or wrong source binding can produce misleading upload readiness. | Capture one fresh read-only Preview evidence package on the operator PC. | `backend/app/api/upload_preview.py:245`; `backend/app/api/upload_preview.py:461`; `backend/app/api/upload_preview.py:517`; `docs/01_development_roadmap.md:63`; `docs/01_development_roadmap.md:69`; `README.md:12` |
| Start Upload | Implemented Core Ops with safety gate | API rejects missing/non-positive `expectedTargetRows`, checks runtime/upload config, and repository requires latest fresh succeeded DB-reachable preview with target rows and matching expected counts. Frontend sends target row/file approval counts. | V2 upload verification document says Start Upload still requires separate exact approval after Preview evidence. | Exact approval and fresh Preview evidence before any operational Start Upload. | High: running against stale preview/source can upload unintended rows. | Use `docs/173` four-step chain and record approved target-only row count. | `backend/app/api/upload_jobs.py:318`; `backend/app/api/upload_jobs.py:340`; `backend/app/db/upload_job_repository.py:312`; `backend/app/db/upload_job_repository.py:367`; `frontend/src/api/uploadJobs.ts:133`; `frontend/src/pages/UploadPage.tsx:971`; `docs/173_v2_operational_upload_verification_gate.md:125` |
| Retry Failed | Implemented Core Ops with safety gate | Retry API rejects missing/non-positive `expectedRemainingRows`, checks runtime/upload config, and creates retry jobs only after repository validation. Frontend sends expected remaining rows/files. | V2 upload verification allows Retry Failed only after separate approval and only if failed/retryable rows remain. | Separate retry approval naming remaining physical rows. | Medium-high: retrying wrong job or count can duplicate work or hide failure cause. | Record failed-job evidence first, then request retry approval only when needed. | `backend/app/api/upload_jobs.py:449`; `backend/app/api/upload_jobs.py:471`; `frontend/src/api/uploadJobs.ts:164`; `frontend/src/pages/UploadPage.tsx:747`; `docs/173_v2_operational_upload_verification_gate.md:30` |
| Upload progress/logs | Implemented Core Ops | SQLite job events are appended/listed; SSE endpoint streams event replay/heartbeats; frontend opens `EventSource` and renders job events/progress. | Roadmap marks Upload Job API, SQLite job/file/event state, SSE replay, and Upload Job tab UI done. | Operator-PC E2E evidence with real failure and recovery paths. | Medium: without operator validation, failures may be technically logged but not actionable. | Include progress/log observation in operator-PC E2E evidence. | `backend/app/api/upload_jobs.py:622`; `backend/app/db/upload_job_repository.py:1116`; `backend/app/db/upload_job_repository.py:1137`; `frontend/src/pages/UploadPage.tsx:592`; `frontend/src/pages/UploadPage.tsx:2033`; `docs/01_development_roadmap.md:70` |
| Audit Logs | Implemented Core Ops | `GET /api/audit` supports filters/pagination; audit table has append-only triggers; query search is limited to safe scalar fields. | Scope requires dangerous operations to be audit logged; roadmap marks audit API/UI done. | Final operator validation that failure reporting is visible across Audit Logs. | High: invisible failures would make cutover unsafe. | Run non-destructive failure-path checks and capture sanitized evidence. | `backend/app/api/audit.py:24`; `backend/app/db/audit_repository.py:151`; `backend/app/db/audit_repository.py:180`; `backend/app/db/audit_repository.py:236`; `backend/app/db/audit_repository.py:282`; `docs/00_product_scope.md:110`; `docs/01_development_roadmap.md:127` |
| Local Supabase status/start/stop | Implemented Core Ops, non-destructive only | Runtime start blocks when required containers are missing, starts only stopped allowed containers or `supabase start` after container precheck, and writes runtime audits. Command runner forbids init/reset/create/rm/prune/up/down. | Scope includes status/start/stop only; README states runtime control is intentionally non-destructive. | Operator-PC local Supabase E2E evidence. | High: cutover depends on operator PC runtime readiness. | Validate status/start/stop on the target PC without reset/cleanup. | `backend/app/services/runtime_control.py:117`; `backend/app/services/runtime_control.py:123`; `backend/app/services/runtime_control.py:141`; `backend/app/services/runtime_control.py:147`; `backend/app/services/runtime_control.py:241`; `backend/app/services/command_runner.py:30`; `backend/app/services/command_runner.py:144`; `README.md:282` |
| Grafana status/link | Implemented Core Ops, link only | Dashboard exposes Grafana chip/status and an external `Open Grafana` link; no iframe behavior is implemented. | Scope includes Grafana status/link only and excludes iframe embedding. | None for v1 unless Grafana availability becomes part of a specific operational evidence run. | Low-medium: Grafana attention is non-core unless it affects upload evidence. | Keep as status/link only; do not embed. | `backend/app/api/dashboard.py:79`; `backend/app/api/dashboard.py:105`; `backend/app/api/dashboard.py:110`; `backend/app/api/dashboard.py:371`; `docs/00_product_scope.md:35`; `docs/00_product_scope.md:48`; `README.md:460` |
| Settings save | Implemented Core Ops | `GET /api/config` and `PUT /api/config` exist; save validates payload, blocks env-overridden keys, writes config atomically, clears settings cache, and records `settings.save` audit rows. | Roadmap marks config API and Settings save UI done. | Operator validation only; no new feature implementation needed. | Medium: wrong settings can bind wrong source/target if operator process is not controlled. | Include read-only `GET /api/config` snapshot before Preview evidence. | `backend/app/api/config.py:24`; `backend/app/api/config.py:29`; `backend/app/services/config_service.py:258`; `backend/app/services/config_service.py:269`; `backend/app/services/config_service.py:294`; `backend/app/services/config_service.py:393`; `docs/01_development_roadmap.md:73`; `docs/01_development_roadmap.md:74` |
| Already-in-DB exact-key delete | Implemented backend/API/UI path, operator mutation requires separate approval | Backend preflight/start/reconcile only accepts selected Preview items still classified as `already_in_db`; frontend selection is limited to `already_in_db` rows and requires preflight, typed count, and rollback acknowledgement. | v1 scope includes this only when separately approved and guarded. README describes it as production-critical maintenance, not general cleanup. | Destructive operational DB delete verification and exact approval before any operational delete. | Production-critical: irreversible DB mutation if approval or evidence is wrong. | Treat as available code path but blocked for operational execution until `docs/171` approval package exists. | `backend/app/services/upload_delete.py:316`; `backend/app/services/upload_delete.py:337`; `backend/app/services/upload_delete.py:446`; `backend/app/services/upload_delete.py:760`; `frontend/src/pages/UploadPage.tsx:523`; `frontend/src/pages/UploadPage.tsx:1428`; `frontend/src/pages/UploadPage.tsx:1647`; `frontend/src/pages/UploadPage.tsx:1761`; `docs/00_product_scope.md:32`; `README.md:42` |
| Operator-facing date-scoped delete UI | Review shell only, not executable UI | Backend feature gate reports `implemented=False` with `review_shell_implemented=True`; frontend renders a blocked disabled panel only when `reviewShellVisible`; frontend API wrapper does not send timestamp scope. | `docs/168` states the shell is non-mutating and no date-scoped API/preflight/job start is implemented. `docs/165` classifies executable UI as deferred. | Role model, policy/preflight/start, fixture evidence, production approval, rollback, and explicit gate enablement. | High if misunderstood as executable cleanup capability. | Do not expose as normal operator action; keep deferred. | `backend/app/services/config_service.py:136`; `backend/app/services/config_service.py:139`; `backend/app/services/config_service.py:140`; `frontend/src/api/uploadDelete.ts:81`; `frontend/src/pages/UploadPage.tsx:1136`; `frontend/src/pages/UploadPage.tsx:1208`; `frontend/src/pages/UploadPage.tsx:1249`; `docs/168_v2_date_scoped_delete_ui_gate.md:35`; `docs/168_v2_date_scoped_delete_ui_gate.md:57`; `docs/168_v2_date_scoped_delete_ui_gate.md:72`; `docs/165_v2_status_matrix.md:86` |
| Delete expansion | Deferred V2 feature | Feature gate is `implemented=False`; no broader delete policy is executable. Current code remains selected `already_in_db` exact-key only. | `docs/170` says the only baseline delete path is selected `already_in_db` exact-key and any expansion needs explicit policy and fixture proof. | Policy limits, fixture DB evidence, production approval format, reconcile/audit/rollback proof. | Production-critical if broadened without proof. | Keep out of v1 cutover; prepare future fixture-first design only. | `backend/app/services/config_service.py:126`; `backend/app/services/config_service.py:129`; `docs/170_v2_delete_expansion_fixture_gate.md:18`; `docs/170_v2_delete_expansion_fixture_gate.md:32`; `docs/170_v2_delete_expansion_fixture_gate.md:167`; `docs/165_v2_status_matrix.md:87`; `docs/165_v2_status_matrix.md:107` |
| Operational DB delete verification | Deferred pending approval/evidence | Code path exists for selected exact-key delete, but operational DB mutation was not run in this audit and remains gated. | `docs/171` explicitly does not approve operational DB access/delete/reconcile and defines the approval record and checklist. | Immutable/append-only approval record, exact scope, fresh preflight, post-run evidence, rollback evidence. | Production-critical. | Build a destructive-operation approval package separately; do not bundle with cutover docs. | `docs/171_v2_operational_delete_verification_gate.md:12`; `docs/171_v2_operational_delete_verification_gate.md:17`; `docs/171_v2_operational_delete_verification_gate.md:71`; `docs/171_v2_operational_delete_verification_gate.md:119`; `docs/171_v2_operational_delete_verification_gate.md:124` |
| Operational upload verification | Deferred pending approval/evidence | Preview/Start/Retry code exists with approval-count gates, but this audit did not run operational Preview, Start Upload, or Retry Failed. | `docs/173` defines the four-step evidence chain and says it does not approve Preview, Start Upload, Retry Failed, or operational writes. `docs/165` classifies item 1 as deferred. | Exact operational approval and fresh evidence for inventory, Preview-only, Start Upload, and Retry Failed when needed. | High: cutover without upload evidence leaves the core business workflow unproven. | Run the `docs/173` chain on the accepted package and operator PC. | `backend/app/api/upload_jobs.py:318`; `backend/app/api/upload_jobs.py:449`; `docs/173_v2_operational_upload_verification_gate.md:11`; `docs/173_v2_operational_upload_verification_gate.md:24`; `docs/173_v2_operational_upload_verification_gate.md:100`; `docs/173_v2_operational_upload_verification_gate.md:127`; `docs/165_v2_status_matrix.md:84` |
| Multi-user LAN | Deferred V2 feature, default-off guard implemented | `v2_lan_access_enabled` exists, LAN health state reports blocked reasons, and HTTP middleware rejects non-loopback server/client access. If LAN flag is enabled, missing auth/session/concurrency reasons are reported. | `docs/172` says the slice does not implement Multi-user LAN and does not approve non-loopback bind/CORS/auth/session rollout. | Auth/authz, sessions, actor audit, concurrency model, CORS/bind approval, tests, explicit rescope. | High if accidentally exposed; current guard reduces risk. | Keep localhost-only for v1; future LAN work must start from `docs/172`. | `backend/app/core/settings.py:90`; `backend/app/core/settings.py:95`; `backend/app/core/lan_security.py:55`; `backend/app/core/lan_security.py:65`; `backend/app/main.py:168`; `backend/app/main.py:176`; `docs/172_v2_lan_security_gate.md:11`; `docs/172_v2_lan_security_gate.md:56`; `docs/00_product_scope.md:47` |
| Supabase schema attribution | Deferred V2 feature; local sidecar foundation exists | Local SQLite `row_attribution_ledger` schema exists with append-only triggers and default-off writes. No Supabase migration/backfill is approved or implemented. | `docs/169` approves only local sidecar phase and defines future `public.metric_row_attribution_evidence` as deferred shape. | Written approval before Supabase migration/backfill/fixture mutation/operational DB access. | Medium: current audit depth is local sidecar, not Supabase-native row attribution. | Keep sidecar only for v1; use future migration design gate if needed. | `backend/app/db/row_attribution_repository.py:186`; `backend/app/db/row_attribution_repository.py:211`; `backend/app/db/row_attribution_repository.py:263`; `backend/app/db/row_attribution_repository.py:307`; `docs/169_v2_supabase_schema_attribution_design.md:17`; `docs/169_v2_supabase_schema_attribution_design.md:23`; `docs/169_v2_supabase_schema_attribution_design.md:43`; `docs/169_v2_supabase_schema_attribution_design.md:51`; `docs/169_v2_supabase_schema_attribution_design.md:197` |
| Legacy upload state import | Intentional v1 exclusion | No default legacy GUI `uploader_state.db` import path was found or required; new state store is the intended path. | Product scope and README say the legacy GUI state is not imported by default and the new app starts with a new state store. | None for v1; only re-scope if business explicitly requires import. | Low if operators understand Preview reconciliation replaces state import. | Keep excluded; rely on Supabase-backed Preview/reconciliation. | `docs/00_product_scope.md:55`; `docs/00_product_scope.md:56`; `docs/00_product_scope.md:99`; `README.md:34`; `AGENTS.md:71`; `AGENTS.md:73` |
| Local Supabase bootstrap/create/reset/cleanup | Intentional v1 exclusion and safety restriction | Command runner forbids `supabase init`, reset, Docker create/rm/prune/up/down. Runtime start blocks missing containers instead of creating a stack. | README says runtime control does not run bootstrap/reset/cleanup/create/delete/volume/prune and v1 does not create a new stack. | Maintainer-only setup outside the app if the stack is missing. | High if bypassed; destructive cleanup can destroy evidence or data. | Preserve non-destructive runtime control; document manual recovery separately. | `backend/app/services/command_runner.py:30`; `backend/app/services/command_runner.py:144`; `backend/app/services/command_runner.py:151`; `backend/app/services/command_runner.py:170`; `backend/app/services/command_runner.py:172`; `backend/app/services/runtime_control.py:123`; `README.md:184`; `README.md:282` |
| Legacy CSV fixture and soak validation | Test/evidence gap | Code has preview/upload logic, but roadmap still calls out broader legacy CSV fixture coverage, large real CSV Preview soak, local Supabase E2E, and Audit Logs failure reporting validation. | Roadmap marks transition partially unblocked, not complete. | Representative CSV behavior, large CSV soak, operator-PC runtime E2E, failure reporting evidence. | High: core workflow may diverge from legacy GUI on edge CSVs. | Prioritize non-destructive validation before cutover. | `docs/01_development_roadmap.md:126`; `docs/01_development_roadmap.md:127`; `docs/01_development_roadmap.md:133`; `docs/01_development_roadmap.md:141`; `docs/00_product_scope.md:138` |
| README/API smoke instruction consistency | Documentation inconsistency fixed in this audit | Backend requires `expectedTargetRows` for Upload Job start and validates optional `expectedTargetFiles`; README smoke now fetches preview detail and posts both fields. | Existing start-upload contract analysis says missing/non-positive expected target rows are blocked by design. | None after this docs-only correction; future smoke docs must track approval-count contracts. | Medium: stale smoke docs cause false negative API checks or unsafe ad hoc workarounds. | Keep API smoke examples tied to backend approval contracts. | `backend/app/api/upload_jobs.py:313`; `backend/app/api/upload_jobs.py:318`; `backend/app/db/upload_job_repository.py:367`; `docs/03-analysis/start-upload-expected-count-contract.analysis.md:32`; `docs/03-analysis/start-upload-expected-count-contract.analysis.md:76`; `README.md:358` |
| Cleanup candidates | Low-risk cleanup only | `settings.py` declares `v2_lan_access_enabled` twice with the same default. `UploadDbEvidenceClient` raises `NotImplementedError`, but `UploadJobService` defaults to concrete `PsycopgUploadDbEvidenceClient`, so this is not an operational gap. | No doc marks either as release blocker. | Optional cleanup PR with tests. | Low: duplicate setting can confuse maintainers; base interface is normal abstraction/test seam. | File a cleanup task; do not block cutover on it. | `backend/app/core/settings.py:90`; `backend/app/core/settings.py:95`; `backend/app/services/upload_jobs.py:163`; `backend/app/services/upload_jobs.py:171`; `backend/app/services/upload_jobs.py:265`; `backend/app/services/upload_jobs.py:276` |

## Must-Fix Before Legacy GUI Replacement

### Functional blockers

- No unimplemented Core Ops code blocker was found in this audit for Preview,
  Start Upload, Retry Failed, progress/logs, Audit Logs, Settings, local
  Supabase status/start/stop, Grafana link/status, or selected `already_in_db`
  exact-key delete.

### Operational validation blockers

- Fresh operational upload verification is still required through the
  `docs/173` inventory, Preview-only, Start Upload, and Retry Failed evidence
  chain.
- Broader legacy CSV fixture coverage and large real CSV Preview soak remain
  required.
- Operator-PC local Supabase status/start/stop E2E evidence remains required.
- Final operator validation of Audit Logs failure reporting remains required.

### Documentation blockers

- README Upload Job API smoke instructions were stale because they omitted
  `expectedTargetRows`. This audit updates the smoke example to post
  `expectedTargetRows` and `expectedTargetFiles` from the preview detail.
- No other direct doc/code contradiction was found in the mandatory files.

### Operator approval blockers

- Any operational Start Upload still needs exact approval after fresh Preview
  evidence.
- Retry Failed needs a separate approval and exact remaining-row count only if
  a retryable failure remains.
- Any operational DB delete needs the `docs/171` approval record and evidence
  package before execution.

## Deferred / Not Required For V1 Cutover

- Multi-user LAN web access.
- Executable operator-facing date-scoped delete UI.
- Delete expansion beyond selected `already_in_db` exact-key delete.
- Operational DB delete verification unless a destructive maintenance run is
  explicitly part of the cutover acceptance.
- Supabase schema attribution migration/backfill.
- Legacy GUI upload state import.
- Local Supabase bootstrap/create/reset/cleanup, Docker cleanup, volume delete,
  prune, `supabase init`, and `supabase db reset`.
- Data Mgmt archive/delete flows, Supabase Mgmt delete UI, Cycle Ops, Training
  Dataset Builder, Cloud Supabase migration, and Grafana iframe embedding.

## Risk Register

| Risk | Severity | Likelihood | Mitigation | Owner or approval gate | Required evidence |
| --- | --- | --- | --- | --- | --- |
| Cutover proceeds without fresh operational upload evidence. | High | Medium | Use `docs/173` sequence and stop on stale/mismatched package/source/preview evidence. | Operator approval plus maintainer evidence capture. | Inventory, Preview-only result, approved Start Upload result when target rows exist, Retry Failed result only when needed. |
| Legacy CSV edge cases diverge from the Tkinter behavior. | High | Medium | Expand representative CSV fixtures and run large CSV Preview soak. | Maintainer validation. | Fixture results, large-source Preview duration/status counts, no raw sensitive paths in artifacts. |
| Operator-PC local Supabase behavior is unproven at cutover. | High | Medium | Run status/start/stop E2E on the target PC without reset/cleanup. | Maintainer/operator. | Runtime status, operation events, audit rows, blocked-path evidence for missing containers if applicable. |
| Audit Logs do not surface critical failures clearly to operators. | High | Medium | Validate failure paths for Preview, upload, settings, runtime, and delete gates. | Maintainer QA and operator sign-off. | Audit rows with safe params and UI screenshots or sanitized API output. |
| Destructive DB delete is run without exact approval/evidence. | Production-critical | Low if gates are followed | Keep operational delete blocked until `docs/171` record exists. | Operator destructive approval. | Approval record, ready preflight, exact key count, hashes, rollback readiness, post-run evidence. |
| LAN exposure is mistaken as available because a guard exists. | High | Low | Keep localhost-only and classify LAN as deferred. | Future LAN security gate. | Auth/session/concurrency/CORS/bind tests and explicit rescope. |
| Supabase-native attribution is assumed complete. | Medium | Medium | Document local sidecar-only state and defer migration/backfill. | Future schema attribution gate. | Migration design, rollback, fixture mutation proof, operational approval. |
| Smoke docs drift from backend approval contracts. | Medium | Low after this update | Keep README smoke examples aligned with required approval fields. | Maintainer docs review. | `git diff --check` and API contract review. |

## Recommended Next Work Packages

### WP1: documentation consistency fixes

- Review README smoke examples against current API schemas after this update.
- Add a short note in any operational runbook that Upload Job start requires
  `expectedTargetRows` and should normally use the UI review modal or the
  updated README smoke pattern.

### WP2: non-destructive validation coverage

- Expand legacy CSV fixture coverage against Preview classification and
  transform/key extraction behavior.
- Run a large real CSV Preview soak without Start Upload.
- Capture failure-path Audit Logs evidence for DB unreachable, malformed
  request, active preview conflict, settings validation failure, and runtime
  blocked states.

### WP3: operator-PC E2E evidence capture

- On the target PC, capture `GET /api/config`, local Supabase status,
  start/stop operation evidence, Preview-only evidence, Job Logs visibility, and
  Audit Logs visibility.
- Do not run reset, cleanup, container deletion, or upload mutation in this
  package.

### WP4: destructive operation approval package

- Prepare a separate approval package for operational Start Upload and Retry
  Failed following `docs/173`.
- Prepare a separate package for selected `already_in_db` exact-key delete only
  if cutover acceptance requires destructive delete evidence, following
  `docs/171`.

### WP5: future LAN design gate

- Start only after v1 cutover readiness is resolved.
- Define auth, sessions, roles, actor audit, concurrency, CORS, bind policy,
  rollback, and test strategy before changing runtime exposure.

### WP6: future Supabase attribution migration design gate

- Start only after local sidecar needs are proven insufficient.
- Define `public.metric_row_attribution_evidence`, migration/backfill/rollback,
  fixture mutation, and operational approval before any DB schema mutation.

## Verification Performed

### Commands run

- `git status --short`
- `rg -n "v2_lan_access_enabled|lan_auth_not_implemented|v2_date_scoped_delete_ui|v2_delete_expansion|timestamp_start_date|timestampStartDate|already_in_db|UploadDbEvidenceClient|PsycopgUploadDbEvidenceClient|row_attribution_ledger|metric_row_attribution_evidence|supabase start|supabase init|supabase db reset|docker rm|expected_target_rows|expectedTargetRows" AGENTS.md README.md docs backend frontend`
- `rg -n` targeted searches for V2 status docs, upload approval fields, delete gates, runtime command allowlist, Audit Logs, Settings save, Grafana, and row attribution.
- Targeted `Get-Content` line extraction for required source files and status/gate documents.

### Commands intentionally not run

- No actual upload to operational Supabase.
- No actual delete from operational Supabase.
- No `supabase init`.
- No `supabase db reset`.
- No `docker rm`, `docker compose down`, volume delete, prune, or cleanup.
- No schema migration or backfill.
- No LAN enablement or non-loopback exposure.

### Tests run

- `git diff --check` passed with exit code 0. Git reported an LF-to-CRLF
  working-copy normalization warning for `README.md`; no whitespace errors were
  reported.

### Tests not run and why

- Backend pytest and frontend typecheck/build/build:api were not required
  because no Python or TypeScript runtime code changed.
- Operational E2E tests were not run because they require operator approval,
  target PC/runtime evidence, and in some cases production mutation gates.

### Files changed

- `README.md`: fixed Upload Job API smoke example to include backend-required
  approval counts from preview detail.
- `docs/175_legacy_gui_replacement_gap_audit.md`: added this evidence-backed
  readiness/gap audit.
