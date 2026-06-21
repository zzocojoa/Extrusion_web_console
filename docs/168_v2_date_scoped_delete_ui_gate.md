# V2 Date-Scoped Delete UI Gate Evidence

Date: 2026-06-22 Asia/Seoul

Status: `default_off_non_mutating_review_shell`

## Purpose

This record documents the V2 item 3 implementation boundary for the
date-scoped delete UI.

The business goal is to make the future maintainer-only date-scoped delete
workflow reviewable without exposing a normal operator cleanup action or
creating any new destructive backend path.

This document does not approve Upload Preview, Start Upload, Retry Failed,
Delete, Settings save, feature-gate enablement, LAN exposure, Supabase
reset/cleanup, Docker cleanup, deployment, or operational DB mutation.

## Implemented Scope

- Backend settings now define these independent V2 gates, all defaulting to
  `false`:
  - `v2_delete_expansion_enabled`
  - `v2_date_scoped_delete_ui_enabled`
  - `v2_lan_access_enabled`
- `GET /api/config` exposes those gates under `featureGates` with:
  - safe gate key;
  - enabled state;
  - source class of `default` or `env`;
  - `mutable=false`;
  - required role;
  - status and reason code.
- Env-requested enablement for delete expansion, date-scoped delete UI, or LAN
  remains `enabled=false` with `status=blocked_not_implemented` until the
  matching executable capability and role model are implemented.
- The date-scoped delete UI gate is intentionally absent from the Settings save
  allowlist and config JSON key map.
- Settings save with `v2DateScopedDeleteUiEnabled` is rejected as an unknown
  key and writes a failed `settings.save` audit row.
- The Upload page reads `featureGates.v2DateScopedDeleteUi`.
- When the gate is absent or disabled, the date-scoped delete panel is not
  rendered.
- The Upload page renders the panel only when the effective gate is `enabled`.
  In the current implementation, env-requested enablement is blocked before it
  reaches the frontend, so normal operators still do not see the panel.
- English and Korean i18n copy is present for the gated panel.

## Not Implemented

This change does not implement:

- a date-scoped delete API;
- a date-scoped delete preflight;
- a date-scoped delete job start;
- broader delete selection policy;
- numeric delete limits;
- production approval record storage;
- operator role enforcement;
- LAN identity or LAN sessions;
- Supabase schema changes;
- operational DB delete verification.

The existing selected `already_in_db` exact-key hard delete path is unchanged.

## UI Safety

The gated date-scoped panel is deliberately non-mutating:

- it does not call `createDeletePreflight`;
- it does not call `startDeleteJob`;
- it does not call `reconcileDeleteJob`;
- it does not save Settings;
- it does not enable a feature gate;
- its only action is a disabled button with blocked-state copy.

Default behavior remains normal-operator hidden because the effective
`v2DateScopedDeleteUi` gate is `enabled=false`. The current shell does not
perform role enforcement; `requiredRole` is metadata for the future executable
policy, and env-requested enablement stays blocked until that role model exists.

## Runbook

Before any future operator-visible or maintainer-visible executable
date-scoped delete flow is enabled, a separate approval record must define:

- exact role matrix for operator, maintainer, and admin;
- delete policy id and allowed DB scope;
- maximum file, item, key, and physical-row limits;
- fixture DB destructive validation evidence;
- production approval wording and storage location;
- no-undo acknowledgement text;
- rollback evidence and recovery path;
- audit rows and DB delta evidence required before and after mutation;
- gate enablement and rollback steps.

Enabling the UI gate is not a Settings page action. It requires separate
feature-gate approval and a reviewed startup/runtime configuration change.

## Rollback

Before commit:

```powershell
git restore backend/app/core/settings.py backend/app/schemas/config.py backend/app/services/config_service.py
git restore tests/backend/test_config_api.py
git restore frontend/src/api/config.ts frontend/src/pages/UploadPage.tsx frontend/src/styles/components.css
git restore frontend/src/i18n/locales/en.json frontend/src/i18n/locales/ko.json
git restore CHANGELOG.md docs/160_v2_delete_lan_audit_rollback_technical_design.md docs/161_v2_open_decisions_review.md docs/165_v2_status_matrix.md
Remove-Item -LiteralPath docs/168_v2_date_scoped_delete_ui_gate.md
```

After commit, revert the commit. If the gate was ever enabled in a local
runtime, set `v2_date_scoped_delete_ui_enabled` back to `false` through the
approved startup configuration path and restart the local API. Do not delete
operational DB rows, local state DB evidence, audit logs, Docker volumes, or
package output as rollback for this UI gate.

## Validation

Validation completed:

```powershell
.\.venv\Scripts\python -m pytest tests\backend\test_config_api.py
node -e "JSON.parse(require('fs').readFileSync('frontend/src/i18n/locales/en.json','utf8')); JSON.parse(require('fs').readFileSync('frontend/src/i18n/locales/ko.json','utf8')); console.log('i18n json ok')"
cd frontend; npm run typecheck
.\.venv\Scripts\python -m pytest tests\backend
cd frontend; npm run build:api
.\packaging\assemble_operator_package.ps1 -FrontendMode api
.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip
```

Results:

- `tests\backend\test_config_api.py`: `22 passed, 2 warnings`
- i18n JSON parse: `i18n json ok`
- frontend typecheck: passed
- full backend tests: `348 passed, 18 warnings`
- frontend API build: passed
- package assembly without zip: passed
- package assembly with zip: passed

Package metadata:

- `packageLabel`: `ExtrusionWebConsole-a3cb3c5-20260621-184752-991`
- `sourceCommit`: `a3cb3c5`
- `frontendMode`: `api`
- `runtimeMode`: `operator-ready`
- `zipCreated`: `true`
- SHA-256:
  `3bc1b9813dd9db5f3617bbdaba8ad520cc1284709a0cb08d249640fa50a98c6d`

Package smoke:

- `launcher\start_web_console.ps1 -CheckOnly`: passed
- `launcher\install_shortcuts.ps1 -CheckOnly`: passed
- read-only HTTP smoke on isolated loopback port `18082`: `/`, `/upload`,
  `/logs`, `/settings`, `/api/health`, `/api/config`, and
  `/api/audit?limit=1` all returned HTTP `200`
- The smoke command discarded response bodies and stopped the launcher-owned
  backend after the read-only checks.
