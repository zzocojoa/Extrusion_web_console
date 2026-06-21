# V2 LAN Security Gate

Date: 2026-06-22 Asia/Seoul

Status: `deferred_default_off_code_guard`

## Purpose

This document records the V2 item 6 LAN security gate implementation slice.

The slice does not implement Multi-user LAN. It adds a default-off backend guard
so accidental LAN exposure fails closed before the app can be described as LAN
ready.

This document does not approve non-loopback bind, LAN CORS widening, LAN
authentication rollout, LAN sessions, LAN user administration, Settings save,
Upload Preview, Start Upload, Retry Failed, Delete, feature-gate enablement,
Supabase reset/cleanup, Docker cleanup, deployment, or LAN exposure.

## Implemented Guard

The backend now has an explicit `v2_lan_access_enabled` setting. Its default is
`false`.

At startup, the app blocks unsafe LAN states:

- non-loopback configured host class while the LAN gate is disabled;
- non-loopback or wildcard CORS class while the LAN gate is disabled;
- `v2_lan_access_enabled=true` before LAN authentication, actor sessions, and
  operation concurrency controls are implemented.

The request middleware also blocks non-loopback clients and non-loopback request
server hosts after the HTTP request reaches the application. This rejects remote
requests and non-loopback request server scope, but it is not a substitute for
socket-bind policy in unsupported direct Uvicorn starts. Supported operator and
package starts must use the launcher, which binds the backend to `127.0.0.1`.
Direct `uvicorn ... --host 0.0.0.0` starts remain out of scope and must not be
used as a LAN enablement path.

## Health Evidence

`GET /api/health` now returns sanitized LAN gate state:

- whether the LAN gate is enabled;
- LAN gate status;
- bind host class, not a raw host value;
- CORS origin classes, not raw origins;
- whether the shared local token may be used as LAN identity;
- safe reason codes for blocked states.

The shared local API token is reported as not allowed for LAN identity. This is
intentional: the token protects one local launcher session, not a human actor.

## Remaining Gate

V2 Multi-user LAN remains `Deferred`.

Before LAN can move beyond this default-off guard, a later approved change must
implement and test:

- explicit product/security approval for LAN exposure;
- per-user authentication;
- session expiry and logout;
- failed-login audit and rate limiting;
- backend authorization for operator, maintainer, and admin roles;
- actor and role attribution in every mutating audit row;
- CSRF-safe mutating request behavior for the chosen frontend delivery model;
- operation-level concurrency locks for Preview, Upload, Delete, Settings, and
  Runtime actions;
- exact CORS allowlist with no wildcard credentials;
- rollback to localhost-only operation.

## Validation

Required validation for this slice:

```powershell
.\.venv\Scripts\python -m pytest tests\backend\test_health.py tests\backend\test_lan_security_gate.py tests\backend\test_static_frontend_serving.py tests\backend\test_launcher_scripts.py
git diff --check
```

Full backend validation is recommended before merge:

```powershell
.\.venv\Scripts\python -m pytest tests\backend
```

Current PR validation evidence:

- Targeted backend: `37 passed, 2 warnings`.
- Full backend: `350 passed, 18 warnings`.
- Frontend: `npm run typecheck` passed.
- Frontend API build: `npm run build:api` passed.
- Package assembly: `.\packaging\assemble_operator_package.ps1 -FrontendMode api -CreateZip` passed.
- Package label: `ExtrusionWebConsole-ce2c07b-20260621-212525-838`.
- Package source commit: `ce2c07b`.
- Package zip SHA-256:
  `11851b0857844a93ad8b8bb488f3620bbd6b5a3a27331d28e9f51ebcef4517de`.
- Package launcher `-CheckOnly`: passed; no backend process started.
- Package shortcut installer `-CheckOnly`: passed; no shortcuts were written.
- Package read-only HTTP smoke: `/`, `/upload`, `/logs`, `/settings`,
  `/api/health`, `/api/config`, and `/api/audit?limit=1` returned 200;
  `/api/docs` and `/api/openapi.json` returned 404.
- Package health LAN state: `lanStatus=localhost_only`,
  `lanEnabled=false`, `sharedLocalTokenAllowed=false`.
- `$review` adversarial after fixes: `No actionable findings.`
- `$review` structured after fixes: no blocking correctness or security
  finding.

## Rollback

Before commit:

```powershell
git restore CHANGELOG.md README.md docs\165_v2_status_matrix.md
git restore backend\app\api\health.py backend\app\core\settings.py backend\app\main.py backend\app\schemas\health.py
git restore tests\backend\test_health.py
git rm --cached --ignore-unmatch backend\app\core\lan_security.py tests\backend\test_lan_security_gate.py docs\172_v2_lan_security_gate.md
Remove-Item -LiteralPath backend\app\core\lan_security.py
Remove-Item -LiteralPath tests\backend\test_lan_security_gate.py
Remove-Item -LiteralPath docs\172_v2_lan_security_gate.md
```

After commit, revert the LAN gate commit.

No operational evidence, local state DB, Supabase data, Docker state, package
output, or LAN configuration should be deleted as rollback for this slice.
