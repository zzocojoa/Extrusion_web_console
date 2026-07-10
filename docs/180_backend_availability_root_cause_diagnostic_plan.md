# Backend Availability Root-Cause Diagnostic Plan

## Status

`diagnostic_plan_only_no_runtime_commands_run`

## Purpose

WP-A remains blocked because `/api/health` did not respond on
`127.0.0.1:8000` after a completed `docs/178` approval record and a human
statement that the backend/package was already running.

This document defines a non-mutating diagnostic protocol only. It does not
execute diagnostics, does not approve runtime lifecycle actions, and does not
change the V1 cutover state.

## Scope Boundary

This plan does not approve:

- backend/app/package start;
- backend/app/package stop;
- restart;
- Supabase start/stop/init/reset/migration/backfill/cleanup;
- Docker start/stop/rm/prune/volume delete/compose up/down;
- Upload Preview creation/cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- Settings save;
- LAN enablement or non-loopback testing;
- deployment;
- production DB access;
- source-file mutation;
- feature gate changes.

## Source Documents

| Source | Relevant boundary |
| --- | --- |
| `docs/176_v1_cutover_go_no_go_validation_plan.md` | WP-A is limited to non-destructive route/config/audit smoke evidence against an already running local package. |
| `docs/177_operator_pc_read_only_smoke_evidence.md` | First WP-A attempt was blocked because the local backend was not already running or did not respond. |
| `docs/178_operator_backend_readiness_approval_package.md` | Backend/package readiness needs bounded human approval; the next collector may run only WP-A read-only checks after backend availability. |
| `docs/179_operator_pc_read_only_smoke_evidence_after_backend_readiness.md` | Approval record was valid, but `/api/health` still did not respond; config/audit/route checks remain missing. |
| `docs/32_operator_package_handoff_runbook.md` | Handoff expects package metadata checks, launcher `-CheckOnly`, hidden tray shortcut lifecycle, and safe stop verification. |
| `docs/operator_package_runtime_note.md` | The package starts/reuses localhost backend through the tray supervisor and uses `-CheckOnly` for validation without starting or writing. |
| `README.md` | Read-only APIs are token-free; mutating APIs remain protected; operator launcher mode disables docs routes. |
| `AGENTS.md` | V1 is localhost-only Core Ops; LAN, reset/cleanup, and destructive work remain out of default scope. |

## Current Blocked Evidence

- `docs/177`: first WP-A attempt was blocked because the backend was not already
  running or did not respond to `/api/health`.
- `docs/178`: approval package prepared bounded wording for exactly one human
  backend/package readiness attempt.
- `docs/179`: approval record was valid and the human stated the backend was
  already running, but `/api/health` still did not respond on `127.0.0.1:8000`.
- `/api/config`, `/api/audit?limit=1`, `/`, `/upload`, `/logs`, `/settings`,
  `/api/docs`, and `/api/openapi.json` evidence remains missing because health
  did not prove the backend.
- Full V1 cutover GO is not supported by the current evidence.

## Diagnostic Hypotheses

| # | Hypothesis | Safe way to classify later | Stop condition |
| --- | --- | --- | --- |
| 1 | Backend was not actually running despite human state. | Read-only process observation and launcher log class inspection after separate diagnostic approval. | Process evidence would require killing, starting, or modifying anything. |
| 2 | Backend started on a different port. | Read-only port-listener observation limited to class-level port ownership and no raw command-line capture. | Port scan would broaden beyond approved local diagnostic scope. |
| 3 | Backend started but failed during boot. | Sanitized launcher log class inspection, recording only failure classes and safe timestamps. | Full logs, secrets, DB URLs, raw paths, or stack traces with sensitive values would be captured. |
| 4 | Backend bound to a different host or was blocked by localhost-only policy. | Compare sanitized bind class to expected `localhost-only / 127.0.0.1`; use `/api/health` only if reachable. | Non-loopback testing or LAN exposure would be required. |
| 5 | Package/start command exited early. | Inspect tray/start launcher latest log class and process absence class. | Re-running the start command would be required. |
| 6 | Tray supervisor is running but backend child process is absent. | Read-only process class observation and tray log class inspection. | Sending tray `Open` or `Exit` signals would be required. |
| 7 | Port 8000 is occupied by another service. | Read-only port-listener observation and, if approved, health probe to classify service mismatch. | Stop/killing process would be requested. |
| 8 | Windows firewall or security product blocked loopback request. | Record safe local security-block class from operator-maintainer observation only. | Changing firewall/security settings would be requested. |
| 9 | Package metadata/source mismatch caused start refusal. | Read-only package metadata inspection against approved source commit and package label. | Package rebuild, reinstall, or shortcut rewrite would be requested. |
| 10 | Missing package prerequisite such as runtime folder, frontend build output, or launcher dependency. | Read-only package folder structure check using expected-present/absent classes only. | Installing dependencies or repairing package files would be requested. |
| 11 | Config or environment points to an invalid host/port. | Read-only config source/override class inspection, without raw values. | Settings save or config file edit would be requested. |
| 12 | Log file exists but contains startup failure class. | Sanitized log class inspection only. | Full log upload or raw path/secret capture would be required. |
| 13 | Docs-disabled/operator mode policy is unrelated and should not block `/api/health`. | Confirm from code that docs route disabling affects docs URLs, not `/api/health`. | Treating docs route status as health evidence would be required. |

## Allowed Diagnostic Classes

These classes are allowed only after a separate human diagnostic approval is
filled. They are observation classes, not execution approval.

| Class | Allowed observation | Sanitization rule |
| --- | --- | --- |
| Package metadata inspection | Compare approved package/source commit, package label, frontend mode, runtime mode, and expected metadata presence. | Record commit/label/classes only; no raw install path. |
| Launcher `-CheckOnly` where documented | Verify package prerequisites and launcher/shortcut checks without starting or writing. | Record pass/fail class only; no raw paths or full output. |
| Read-only process list observation | Determine whether tray supervisor and backend process classes appear present or absent. | Record process class and count only; no raw command lines, user names, or paths. |
| Read-only port listener observation | Determine whether port `8000` is closed, EWC-owned class, or other-service class. | Record port state and owner class only; no raw process path. |
| Read-only loopback health probe | Probe `/api/health` only after approval and only on loopback. | Store service/status/localhost class only; no body beyond sanitized fields. |
| Read-only launcher log inspection | Inspect latest launcher/tray/stop log classes. | Record failure class and safe timestamp only; no full logs. |
| Read-only Windows shortcut target class inspection | Confirm shortcut class targets hidden tray supervisor pattern and package root class. | Record target class only; no raw absolute path. |
| Read-only package folder structure check | Confirm expected-present/absent package structure classes. | Record class-level presence only; no full file list. |
| Read-only config source/override class inspection | Classify config source and override classes without saving settings. | No raw values, DB URLs, tokens, or operational paths. |
| Read-only route availability check after health passes | Check `/`, `/upload`, `/logs`, `/settings`, docs-disabled routes only after health passes. | Record status code class only; no HTML, OpenAPI body, or screenshots with sensitive data. |

Do not include raw command output in evidence. Do not store raw paths, tokens, DB
URLs, filenames, internal URLs, full logs, raw config dumps, OpenAPI JSON, raw
process command lines, or credentials.

## Forbidden Diagnostic Actions

- starting backend/app/package;
- stopping backend/app/package;
- killing processes;
- restart scripts;
- sending tray `Open` or `Exit` signals;
- Supabase lifecycle commands;
- Docker lifecycle or destructive commands;
- Settings save;
- config file edits;
- feature gate edits;
- Upload Preview creation/cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- LAN enablement or non-loopback testing;
- deployment;
- production DB access;
- source-file mutation;
- manual DB cleanup.

## Diagnostic Approval Requirement

This plan itself does not authorize diagnostics. A future read-only diagnostic
attempt needs a filled approval record before any observation beyond repository
metadata review.

Required approval wording:

```text
I approve one read-only backend availability diagnostic attempt for `Extrusion_web_console`.

Approved evidence scope: backend availability root-cause diagnosis only.
Approved package/source commit: <sourceCommit>
Approved package label: <packageLabel>
Approved operator PC class: <operatorPcClass>
Approved bind scope under review: localhost-only / 127.0.0.1
Approved diagnostic classes: <metadata inspection | check-only | process-list observation | port-listener observation | log-class inspection | loopback health probe>

This approval does not approve backend/app/package start, backend/app/package stop, restart, Preview, Start Upload, Retry Failed, upload delete, Settings save, Local Supabase lifecycle, Supabase reset/migration/cleanup, Docker lifecycle/destructive commands, LAN exposure, deployment, production DB access, source-file mutation, feature gate changes, or raw sensitive evidence capture.
```

## Approval Record Template

| Field | Value |
| --- | --- |
| Diagnostic approval id | `<diagnosticApprovalId>` |
| Exact approval text | `<exact text from Diagnostic Approval Requirement>` |
| Approved package/source commit | `<sourceCommit>` |
| Approved package label | `<packageLabel>` |
| Approved operator PC class | `<operatorPcClass>` |
| Approved bind scope under review | `localhost-only / 127.0.0.1` |
| Approved diagnostic classes | `<approved class list>` |
| Approver | `<approver or safe approver class>` |
| Date/time | `<ISO-8601 local time>` |
| Explicit exclusions acknowledged | `<yes/no>` |
| Sensitive evidence redaction acknowledged | `<yes/no>` |

## Diagnostic Protocol

This protocol is for a future approved diagnostic run. It is not executed by
this document.

1. Confirm package/source identity.
   - Compare approved package/source commit and package label to package
     metadata classes.
   - Stop if the package identity is unknown, mismatched, or stale.
2. Confirm package prerequisites by observation class.
   - Verify runtime folder class, built frontend class, launcher script class,
     and package metadata class.
   - Stop if repair, install, rebuild, or file mutation would be needed.
3. Confirm launcher `-CheckOnly` only if the approval names that class.
   - Record pass/fail class.
   - Stop if a start, shortcut write, or installer action would be needed.
4. Confirm process and tray state by observation class only.
   - Record tray supervisor class and backend process class.
   - Stop if the next action would be `Open`, `Exit`, stop, restart, or kill.
5. Confirm port `8000` listener class.
   - Record closed, EWC-owned class, or other-service class.
   - Stop if resolving it would require stopping or changing another process.
6. Probe loopback health only if approved and only against localhost.
   - Record service class, status class, and localhost-only class.
   - Stop if service is not `extrusion-web-console-api` or is not
     localhost-only.
7. Inspect launcher logs by class only if needed.
   - Record startup failure class, missing prerequisite class, source mismatch
     class, port conflict class, or unknown class.
   - Stop before capturing raw logs or sensitive values.
8. Decide next evidence path.
   - If health passes, request a new WP-A read-only smoke retry approval using
     `docs/176` and `docs/178`.
   - If health remains blocked, create a sanitized blocked diagnostic evidence
     record and do not run config/audit/route checks.

## Evidence Template

| Evidence field | Allowed value class |
| --- | --- |
| Diagnostic approval id | Safe id |
| Diagnostic evidence id | Safe id |
| Package/source commit | Commit hash |
| Package label | Safe package label |
| Operator PC class | Safe class |
| Package metadata class | `matched`, `mismatched`, `missing`, `unknown` |
| Prerequisite class | `present`, `missing`, `unknown`, `not inspected` |
| Check-only class | `passed`, `failed`, `not approved`, `not run` |
| Tray supervisor class | `present`, `absent`, `unknown`, `not inspected` |
| Backend process class | `present`, `absent`, `unknown`, `not inspected` |
| Port 8000 class | `closed`, `ewc_service`, `other_service`, `unknown`, `not inspected` |
| Health class | `ok_localhost_only`, `unreachable`, `wrong_service`, `not_localhost_only`, `not run` |
| Launcher log class | `startup_failed`, `missing_prerequisite`, `port_conflict`, `source_mismatch`, `none`, `not inspected` |
| Sensitive evidence review | `passed`, `blocked`, `not reviewed` |
| Recommended next action | `retry_wp_a`, `blocked_evidence`, `maintainer_package_fix`, `new_approval_required` |

## Stop Conditions

Stop the diagnostic attempt when any of these are true:

- diagnostic approval is missing, incomplete, ambiguous, or broader than this
  plan permits;
- package/source commit or package label is unknown or mismatched;
- operator PC class is unknown or mismatched;
- requested diagnostic class is not listed in the approval record;
- an observation would capture raw paths, filenames, CSV content, DB URLs,
  tokens, JWTs, Authorization values, credentials, internal URLs, full logs,
  full HTML, full OpenAPI JSON, raw config dumps, or raw process command lines;
- backend/app/package start, stop, restart, tray signal, kill, Settings save,
  Supabase lifecycle, Docker lifecycle, LAN exposure, deployment, production DB
  access, source-file mutation, or feature-gate change would be needed;
- `/api/health` reports a non-EWC service or non-localhost-only class;
- port ownership cannot be safely classified without stopping or changing a
  process;
- the diagnostic request bundles WP-A retry, Preview, Start Upload, Retry
  Failed, delete, inventory precheck, Settings save, deployment, or cutover GO.

## Relationship To Cutover Gates

This plan addresses only backend/package availability root cause. It does not
complete any of these gates:

- WP-A read-only route/config/audit smoke pass evidence;
- WP-B read-only inventory precheck;
- WP-C Preview-only approval/evidence;
- WP-D Start Upload approval after Preview proves exact target rows;
- WP-E Retry Failed approval when failed/retryable rows remain;
- destructive delete approval package;
- final V1 cutover GO sign-off.

## Recommended Next Work Packages

- WP-A0: read-only backend availability diagnostic approval and sanitized
  evidence capture.
- WP-A1: WP-A read-only smoke retry only after health proves the expected
  localhost-only EWC service.
- WP-B: read-only inventory precheck, separate from Preview.
- WP-C: Preview-only approval/evidence, separate and not bundled with upload.
- WP-D: Start Upload approval package, only after Preview proves target rows.
- WP-E: Retry Failed approval package, only if retryable rows remain.

## Verification Performed

Commands run while creating this documentation-only plan:

```powershell
git switch main
git pull --ff-only origin main
git switch -c docs/backend-availability-root-cause-diagnostic-plan
git status --short --branch
Test-Path docs/180_backend_availability_root_cause_diagnostic_plan.md
rg -n "<targeted safety, launcher, package, and endpoint patterns>" AGENTS.md README.md docs backend launcher packaging
rg --files packaging scripts
Get-Content -Raw <mandatory source documents and reference files>
git diff --check
git diff --name-status origin/main...HEAD
```

`scripts/` was not present in the repository during reference-file discovery.

Commands intentionally not run:

- backend/app/package start;
- backend/app/package stop;
- launcher start;
- tray supervisor start;
- stop/restart scripts;
- Supabase commands;
- Docker commands;
- HTTP checks;
- Upload Preview creation/cancellation;
- Start Upload;
- Retry Failed;
- upload delete preflight/start/reconcile;
- Settings save;
- LAN or deployment actions;
- production DB access;
- source-file mutation outside this documentation-only change;
- feature gate changes.

Tests run: none.

Tests not run: backend/frontend runtime tests were skipped because this is a
documentation-only diagnostic plan and no runtime code changed.

Files changed:

- `README.md`
- `docs/180_backend_availability_root_cause_diagnostic_plan.md`
