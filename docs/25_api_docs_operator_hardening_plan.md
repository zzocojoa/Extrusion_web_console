# API Docs Operator Hardening Plan

Status: implemented on branch `codex/api-docs-operator-hardening-impl`

Date: 2026-06-07

Scope: FastAPI `/api/docs`, `/api/openapi.json`, and any future ReDoc route in launcher operator mode.

Implementation result:

- Added `EWC_API_DOCS_MODE` with `auto`, `enabled`, and `disabled`.
- FastAPI now sets `docs_url`, `openapi_url`, and `redoc_url` from the docs mode decision.
- Operator launcher mode sets `EWC_API_DOCS_MODE=disabled`.
- Operator mode returns API-style `404` for `/api/docs`, `/api/openapi.json`, and ReDoc-style docs routes.
- Dev/test docs-enabled mode keeps Swagger/OpenAPI available with `EWC_API_DOCS_MODE=enabled`.
- OpenAPI contract tests run under docs-enabled dev/test settings.
- The route is disabled in operator mode; docs routes are not token-gated.
- Read-only API and mutating local-token policies remain unchanged.

## Decision Summary

- Disable FastAPI Swagger UI and OpenAPI JSON routes in launcher operator mode.
- Keep Swagger UI and OpenAPI JSON available in developer mode.
- Keep ReDoc disabled. If ReDoc is added later, it must follow the same operator-mode disable rule.
- Do not protect docs routes with the local token. In operator mode the routes should be absent, not token-gated.
- Keep the current read-only API token exceptions unchanged.
- Preserve `/api/*` route precedence over the SPA fallback. Disabled docs routes must return an API-style `404`, not the frontend shell.

## Why Route Disable Wins

The per-run local token is a same-machine safety guard for mutating API calls. It is not a full authentication or authorization system. Using it to expose operator-mode API documentation would make the token a documentation access credential and would expand token handling without reducing the discovery surface enough.

Operator mode should instead remove the documentation routes from the served app. This gives the clearest policy:

- operators can use the UI;
- mutating API calls remain protected by the local token;
- developer documentation remains available only in explicit developer mode.

## Current State

The backend currently creates the FastAPI app with:

```text
openapi_url="/api/openapi.json"
docs_url="/api/docs"
redoc_url=None
```

Launcher phase 2 sets `EWC_LOCAL_TOKEN_MODE=required` and passes `EWC_LOCAL_API_TOKEN` through process environment. The frontend receives the token through backend-served HTML bootstrap and sends `X-EWC-Local-Token` only for same-origin mutating `/api/*` requests.

Read-only APIs, upload/job status reads, SSE events, `/api/health`, `/api/config`, and `/api/audit` remain token-free. `/api/docs` is currently also localhost-readable; this plan changes that only for operator mode.

## Mode Matrix

| Runtime mode | Signal | `/api/docs` | `/api/openapi.json` | ReDoc | Mutating API token |
| --- | --- | --- | --- | --- | --- |
| Operator launcher | `EWC_API_DOCS_MODE=disabled` and `EWC_LOCAL_TOKEN_MODE=required` | disabled | disabled | disabled | required |
| Developer default | no operator docs-disable signal | enabled | enabled | disabled | existing mode behavior |
| Vite dev opt-out | `EWC_LOCAL_TOKEN_MODE=dev-disabled` | enabled | enabled | disabled | disabled by explicit dev mode |
| Test override enabled | `EWC_API_DOCS_MODE=enabled` | enabled | enabled | disabled unless explicitly implemented later | existing mode behavior |
| Test override disabled | `EWC_API_DOCS_MODE=disabled` | disabled | disabled | disabled | existing mode behavior |

Implementation should introduce `EWC_API_DOCS_MODE` with allowed values:

```text
auto
enabled
disabled
```

Recommended default is `auto`. In `auto`, docs are disabled when the local token mode is `required`; otherwise they stay enabled. The launcher should still set `EWC_API_DOCS_MODE=disabled` explicitly so operator behavior is not accidentally changed by a future token-mode refactor.

## Route Behavior

Operator mode expected responses:

| Request | Expected behavior |
| --- | --- |
| `GET /api/docs` | `404` JSON API response |
| `GET /api/openapi.json` | `404` JSON API response |
| `GET /docs` | no new route |
| `GET /redoc` or `/api/redoc` | no new route |
| `GET /api/health` | unchanged read-only success |
| `GET /api/config` | unchanged read-only success with secret values hidden |
| `GET /api/audit` | unchanged read-only success |
| Unknown `/api/*` | unchanged API-style `404`, never SPA fallback |
| `/`, `/upload`, `/logs`, `/settings` | unchanged frontend static or SPA fallback behavior |

Disabled documentation routes should not emit audit rows. They are read-only discovery attempts, and auditing them would add noise without improving operator traceability.

## Implementation Plan

1. Add a settings field for API docs exposure.
   - Name: `api_docs_mode`
   - Env key: `EWC_API_DOCS_MODE`
   - Values: `auto`, `enabled`, `disabled`
   - Default: `auto`
   - Validation: reject unknown values during settings validation.

2. Add a small backend helper to decide docs exposure.
   - `disabled` returns disabled.
   - `enabled` returns enabled.
   - `auto` returns disabled when `local_token_mode == "required"` and enabled otherwise.
   - The helper must not inspect or log token values.

3. Wire the helper into `create_app()`.
   - If enabled:
     - `openapi_url="/api/openapi.json"`
     - `docs_url="/api/docs"`
     - `redoc_url=None`
   - If disabled:
     - `openapi_url=None`
     - `docs_url=None`
     - `redoc_url=None`

4. Keep static frontend fallback unchanged.
   - The existing catch-all already returns JSON `404` for unknown `/api/*`.
   - This is the desired response once docs routes are disabled.
   - SPA fallback must not serve the frontend shell for `/api/docs` or `/api/openapi.json`.

5. Update the Windows launcher.
   - Set `EWC_API_DOCS_MODE=disabled` for operator mode backend process.
   - `-CheckOnly` should report API docs policy as disabled/enabled by policy only.
   - `-CheckOnly` must not print token values or secret-bearing config values.

6. Keep developer mode simple.
   - Backend development without operator launcher keeps docs enabled by default.
   - Vite development with `EWC_LOCAL_TOKEN_MODE=dev-disabled` keeps docs enabled.
   - Developers can force-disable with `EWC_API_DOCS_MODE=disabled` when testing operator hardening.

## Local Token Relationship

Local token enforcement and docs exposure are related but separate controls.

- Local token protects mutating `/api/*` calls.
- Docs hardening removes the documentation routes in operator mode.
- Read-only APIs remain token-free by design.
- Missing or invalid local tokens should still produce `403 local_token_required` only for protected mutating requests.
- Disabled docs routes should produce `404`, not `403`, because no token exchange is expected.

This avoids presenting the local token as complete authentication.

## Tests

Backend tests:

- Developer/default app exposes `/api/docs`.
- Developer/default app exposes `/api/openapi.json`.
- Operator-style settings disable `/api/docs`.
- Operator-style settings disable `/api/openapi.json`.
- Disabled docs routes return JSON `404`, not the frontend shell.
- `/api/health`, `GET /api/config`, and `GET /api/audit` still work without a token in operator-style settings.
- Mutating token enforcement tests still pass unchanged.
- Unknown `/api/*` static fallback behavior remains JSON `404`.
- Existing OpenAPI contract tests run with docs enabled or explicit developer-mode settings.

Launcher tests:

- Default operator launcher sets `EWC_API_DOCS_MODE=disabled`.
- `-CheckOnly` reports docs policy without printing token or secret values.
- Existing token policy, port conflict, build check, and redaction tests still pass.

HTTP smoke after implementation:

- Operator backend origin:
  - `/api/docs` returns `404`.
  - `/api/openapi.json` returns `404`.
  - `/api/health` returns success.
  - `/` returns the built frontend when present.
- Developer backend:
  - `/api/docs` is reachable.
  - `/api/openapi.json` is reachable.

Frontend screenshot QA:

- No new screenshot assertion is required for docs routes.
- Existing `npm run qa:screenshots` should still pass because pages are unchanged.
- Generated `.gstack` artifacts remain ignored and uncommitted.

## Documentation Updates

Implementation PR should update:

- `README.md`
  - Operator launcher section: `/api/docs` and `/api/openapi.json` disabled in operator mode.
  - Developer section: docs remain available in dev mode.
- `docs/02_engineering_plan.md`
  - Security section and launcher phase 2 status.
- `docs/23_launcher_integration_plan.md`
  - Static serving/API route precedence and operator launcher policy.
- `docs/24_launcher_local_token_phase2_plan.md`
  - Clarify that docs hardening is route disable, not token-gating.
- `CHANGELOG.md`
  - Add concise hardening note when implementation lands.

## Migration And Rollout

- No database migration.
- No config JSON migration is required.
- Operator launcher behavior changes on the next launched backend process after implementation.
- Developer mode remains backward compatible because docs stay enabled by default.
- Rollback path: revert the implementation commit or set `EWC_API_DOCS_MODE=enabled` for developer/test runs.

## Out Of Scope

- Full authentication or authorization.
- LAN or multi-user access.
- Token-gating `/api/docs`.
- Changing CORS policy.
- Changing Upload Preview, Upload Job, Settings save, Runtime start/stop, or Audit Logs behavior.
- Changing Supabase, Docker, WSL, reset, cleanup, prune, or bootstrap policy.
- Serving source files, operational fixtures, generated screenshots, or build artifacts beyond `frontend/dist`.

## Acceptance Criteria

- Operator launcher starts backend with API docs disabled.
- `/api/docs` and `/api/openapi.json` return API-style `404` in operator mode.
- Developer mode keeps `/api/docs` and `/api/openapi.json` available.
- ReDoc remains disabled.
- Read-only API exceptions remain token-free.
- Mutating API token enforcement remains unchanged.
- Static frontend serving and SPA fallback behavior remain unchanged.
- Tests document both operator and developer behavior.
- No token, DB URL, service role, authorization header, or operational CSV path/content is introduced into docs, logs, audit rows, screenshots, or generated artifacts.
