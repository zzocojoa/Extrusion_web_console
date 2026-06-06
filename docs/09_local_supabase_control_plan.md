# Local Supabase Control Engineering Plan

Status: decision-complete plan for branch `codex/local-supabase-control`

Scope: v1 Core Ops Local Supabase status/start/stop UI/API and Grafana status/link-only support.

This document follows `AGENTS.md`, `docs/00_product_scope.md`, `docs/02_engineering_plan.md`, `docs/03_ui_ux_plan.md`, `docs/04_design_system.md`, `docs/07_upload_preview_plan.md`, and `docs/08_upload_job_sse_plan.md`.

Reference project: `C:\Users\user\Documents\GitHub\Extrusion_data`.

## Goals

- Show whether the local Supabase runtime is safe for upload work.
- Let the operator start or stop the existing `Extrusion_data` local Supabase stack from the web console.
- Keep all runtime operations visible in UI, runtime events, and audit logs.
- Preserve the existing local Supabase project and data. Runtime control must not delete containers, volumes, backups, or database rows.
- Keep Grafana as a separate status/link-only dashboard. Do not embed it in the web app.

## Non-Goals

- Do not implement Data Mgmt, Cycle Ops, Training Dataset Builder, or Supabase delete UI.
- Do not run `supabase db reset`.
- Do not remove Docker containers, Docker volumes, Docker images, or networks.
- Do not run Docker prune or Docker compose destructive commands.
- Do not clean up operational DB data.
- Do not start Docker Desktop or install WSL/Docker from the web app. The UI reports that the operator must start/fix them manually.
- Do not bootstrap, create, or initialize a new local Supabase stack in v1.
- Do not iframe Grafana.
- Do not change Upload Preview or Upload Job semantics except to block unsafe runtime stop/start conflicts.

## Environment Decisions

Use the existing `Extrusion_data` local Supabase project as the controlled runtime.

Default runtime values:

| Setting | Default |
| --- | --- |
| Project path | `C:\Users\user\Documents\GitHub\Extrusion_data` |
| Supabase project id | `Extrusion_data` |
| API port | `54321` |
| DB port | `25432` |
| Studio port | `54323` |
| Edge function URL | `http://127.0.0.1:54321/functions/v1/upload-metrics` |
| Grafana URL | `http://localhost:3001` |
| DB container | `supabase_db_Extrusion_data` |
| Edge Runtime container | `supabase_edge_runtime_Extrusion_data` |
| Grafana container | `grafana_local` |

`startup.sh` in the reference project is behavior reference only. The web console must not call it wholesale because it also starts Grafana, syncs Grafana assets, applies a migration, and touches cron. The web console implements a narrower allowlisted runtime controller.

Start/stop control is for the existing `Extrusion_data` runtime only. If required Supabase containers do not already exist, the web console must not try to repair the environment with `supabase start`, `supabase init`, `docker compose`, or any bootstrap/create path. Missing required containers are treated as `blocked|required_container_missing` and require manual operator/developer recovery outside the web app.

## Backend Modules

Add:

```text
backend/app/api/runtime.py
backend/app/schemas/runtime.py
backend/app/services/runtime_control.py
backend/app/services/runtime_readiness.py
backend/app/services/command_runner.py
backend/app/db/runtime_repository.py
tests/backend/test_runtime_api.py
tests/backend/test_runtime_control.py
tests/backend/test_runtime_command_policy.py
```

Extend:

```text
backend/app/core/settings.py
backend/app/main.py
backend/app/db/upload_job_repository.py or extracted audit repository
frontend/src/pages/Dashboard...
frontend/src/pages/Settings...
frontend/src/i18n...
```

Implementation preference:

- Keep command execution in `services/command_runner.py`.
- Keep runtime orchestration in `services/runtime_control.py`.
- Keep passive probes in `services/runtime_readiness.py`.
- Keep SQLite operation/event persistence in `db/runtime_repository.py`.
- If audit code starts duplicating upload job audit code, extract `backend/app/db/audit_repository.py` and have upload/runtime repositories share it.

## Settings And Config

Add settings with `EWC_` env overrides:

```python
local_supabase_project_path: str = "C:\\Users\\user\\Documents\\GitHub\\Extrusion_data"
local_supabase_wsl_project_path: str = "/mnt/c/Users/user/Documents/GitHub/Extrusion_data"
local_supabase_api_port: int = 54321
local_supabase_db_port: int = 25432
local_supabase_studio_port: int = 54323
local_supabase_project_id: str = "Extrusion_data"
local_supabase_edge_container: str = "supabase_edge_runtime_Extrusion_data"
local_supabase_db_container: str = "supabase_db_Extrusion_data"
grafana_url: str = "http://localhost:3001"
grafana_container: str = "grafana_local"
runtime_command_timeout_seconds: int = 90
runtime_readiness_timeout_seconds: int = 90
```

Config priority remains:

```text
built-in defaults
< app config file
< repo .env / launcher env
< process environment
```

Settings UI should show runtime values with source badges. Env-overridden values are displayed read-only or with an "overridden by environment" indicator.

## Backend API

### `GET /api/runtime/local-supabase`

Returns current runtime status. This endpoint performs passive probes only.

Response:

```json
{
  "checkedAt": "2026-06-02T00:00:00Z",
  "overallStatus": "ready",
  "summary": {
    "label": "로컬 Supabase 실행 중",
    "message": "DB, API, Studio, Edge Runtime이 준비되었습니다.",
    "nextAction": "업로드를 진행할 수 있습니다."
  },
  "project": {
    "projectId": "Extrusion_data",
    "projectPath": "C:\\Users\\user\\Documents\\GitHub\\Extrusion_data",
    "configExists": true,
    "configPortsMatch": true
  },
  "docker": {
    "cliAvailable": true,
    "daemonReachable": true,
    "context": "desktop-linux",
    "version": "redacted-or-short",
    "errorCode": null,
    "message": null
  },
  "wsl": {
    "cliAvailable": true,
    "dockerDesktopDetected": true,
    "distributions": [
      {"name": "Ubuntu", "state": "Running", "version": "2"}
    ],
    "message": null
  },
  "supabase": {
    "cliAvailable": true,
    "api": {"status": "ready", "host": "127.0.0.1", "port": 54321},
    "db": {"status": "ready", "host": "127.0.0.1", "port": 25432},
    "studio": {"status": "ready", "host": "127.0.0.1", "port": 54323},
    "edgeRuntime": {
      "status": "ready",
      "containerName": "supabase_edge_runtime_Extrusion_data",
      "containerState": "running",
      "routeReachable": true
    },
    "containers": [
      {
        "name": "supabase_db_Extrusion_data",
        "exists": true,
        "state": "running",
        "health": "healthy",
        "allowedAction": "stop"
      }
    ]
  },
  "grafana": {
    "status": "ready",
    "url": "http://localhost:3001",
    "linkOnly": true,
    "containerName": "grafana_local",
    "containerState": "running"
  },
  "lastOperation": {
    "operationId": "rt_20260602_000001",
    "kind": "start",
    "status": "succeeded",
    "finishedAt": "2026-06-02T00:00:00Z"
  },
  "warnings": [],
  "errors": []
}
```

`overallStatus` values:

| Status | Meaning |
| --- | --- |
| `ready` | Docker is reachable and DB/API/Studio/Edge are ready. |
| `running` | A runtime start or stop operation is active. |
| `attention` | Runtime is partially available, for example Grafana down or Edge route unavailable while DB/API are ready. |
| `blocked` | Upload should not start: Docker unavailable, DB down, API down, project path missing, or config mismatch. |
| `unknown` | Probes could not complete within the status budget. |

### `POST /api/runtime/local-supabase/start`

Starts the existing local Supabase runtime.

Request:

```json
{
  "actor": "local_operator",
  "timeoutSeconds": 90
}
```

Response `202`:

```json
{
  "operationId": "rt_20260602_000002",
  "kind": "start",
  "status": "queued",
  "detailUrl": "/api/runtime/operations/rt_20260602_000002"
}
```

Rules:

- If an upload job is active, return `409 active_upload_job` and write audit `runtime.supabase.start` with result `blocked`.
- If a preview run is active, return `409 active_preview_run` and write audit `runtime.supabase.start` with result `blocked`.
- If another runtime operation is active, return `409 active_runtime_operation` and audit `blocked`.
- If Docker daemon is unavailable, fail the operation with `docker_daemon_unavailable`.
- Before any start command runs, exact required Supabase container existence must be checked.
- If any required container is missing, return or persist `blocked|required_container_missing`. Do not run `supabase start` and do not create a new stack.
- If all required services are already ready, write a `no_op` runtime event and audit success.
- Prefer `supabase start` from the fixed `Extrusion_data` project path only when Supabase CLI is available and all required containers already exist.
- If Supabase CLI is unavailable, only start exact existing containers in the allowlist. Do not create, remove, or reset containers.
- If the Edge Runtime container exists but is stopped, `docker start supabase_edge_runtime_Extrusion_data` is allowed.
- Sanitize all command output before storing events or returning API data. Never expose anon keys or service keys.

### `POST /api/runtime/local-supabase/stop`

Stops the existing local Supabase runtime without deleting data.

Request:

```json
{
  "actor": "local_operator",
  "timeoutSeconds": 90
}
```

Response `202`:

```json
{
  "operationId": "rt_20260602_000003",
  "kind": "stop",
  "status": "queued",
  "detailUrl": "/api/runtime/operations/rt_20260602_000003"
}
```

Rules:

- If an upload job is active, return `409 active_upload_job` and audit `blocked`.
- If a preview run is active, return `409 active_preview_run` and audit `blocked`.
- If another runtime operation is active, return `409 active_runtime_operation` and audit `blocked`.
- Stop uses exact `docker stop <container>` for allowlisted Supabase containers only.
- Do not call `supabase stop` in v1 because the non-destructive behavior is less explicit than exact container stop and may interact with backups differently across CLI versions.
- Do not stop Docker Desktop, WSL, Grafana, cron, or unrelated containers.
- If already stopped, write a `no_op` event and audit success.

### `GET /api/runtime/operations/{operationId}`

Returns one runtime operation and recent events.

```json
{
  "operation": {
    "operationId": "rt_20260602_000003",
    "kind": "stop",
    "status": "running",
    "requestedAt": "2026-06-02T00:00:00Z",
    "startedAt": "2026-06-02T00:00:01Z",
    "finishedAt": null,
    "actor": "local_operator",
    "errorCode": null,
    "errorMessage": null
  },
  "events": [
    {
      "seq": 1,
      "ts": "2026-06-02T00:00:01Z",
      "level": "info",
      "eventType": "runtime.stop.started",
      "message": "로컬 Supabase 종료를 시작했습니다."
    }
  ]
}
```

### Optional `GET /api/runtime/grafana`

Grafana can be returned inside `GET /api/runtime/local-supabase`. A separate endpoint is optional and should only be added if frontend polling needs a narrower query.

## DTOs

Pydantic models:

```text
RuntimeOverallStatus = ready | running | attention | blocked | unknown
RuntimeServiceStatus = ready | starting | stopping | stopped | unreachable | missing | unhealthy | unknown
RuntimeOperationKind = start | stop
RuntimeOperationStatus = queued | running | succeeded | failed | blocked | timed_out | cancelled
RuntimeEventLevel = debug | info | warning | error
```

Core DTOs:

```text
RuntimeStatusResponse
RuntimeSummary
RuntimeProjectStatus
DockerStatus
WslStatus
RuntimeContainerStatus
SupabaseRuntimeStatus
PortStatus
EdgeRuntimeStatus
GrafanaStatus
RuntimeOperationRequest
RuntimeOperationAcceptedResponse
RuntimeOperationDetailResponse
RuntimeOperation
RuntimeEvent
```

Use camelCase JSON aliases to match existing frontend API conventions.

## SQLite Schema

Add runtime operation persistence to the existing web state store.

```sql
CREATE TABLE IF NOT EXISTS runtime_operations (
  operation_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN ('start','stop')),
  status TEXT NOT NULL CHECK(status IN (
    'queued','running','succeeded','failed','blocked','timed_out','cancelled'
  )),
  requested_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  actor TEXT NOT NULL DEFAULT 'local_operator',
  command_policy_version TEXT NOT NULL,
  config_snapshot_json TEXT NOT NULL DEFAULT '{}',
  summary_json TEXT NOT NULL DEFAULT '{}',
  error_code TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  operation_id TEXT NOT NULL REFERENCES runtime_operations(operation_id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  ts TEXT NOT NULL,
  level TEXT NOT NULL CHECK(level IN ('debug','info','warning','error')),
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  data_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE(operation_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_runtime_operations_status_created
  ON runtime_operations(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_runtime_events_operation_seq
  ON runtime_events(operation_id, seq);
```

Sequence writes must use `BEGIN IMMEDIATE` or an equivalent repository method so concurrent worker/API event appends cannot collide on `(operation_id, seq)`.

Audit rows use the existing `audit_log` schema:

| Action | Result examples |
| --- | --- |
| `runtime.supabase.status` | `failure` for manual refresh failure only |
| `runtime.supabase.start` | `success`, `failure`, `blocked` |
| `runtime.supabase.stop` | `success`, `failure`, `blocked` |

Every blocked mutating request writes audit before returning.

Passive status polling success must not write audit rows. Dashboard polling would otherwise spam the audit log and hide operator actions. If status caching is needed, store it in runtime status/event cache only. Audit is reserved for manual start/stop, blocked mutating requests, mutating operation failures, and manual refresh failures.

## Command Allowlist

All commands are executed with `subprocess.run(args=[...], shell=False, cwd=<fixed path>, timeout=<bounded>)`.

No API request may pass an arbitrary command, arbitrary path, or shell fragment.

Allowed read-only detection:

```text
docker version --format {{json .}}
docker ps --format {{json .}}
docker ps -a --format {{json .}}
docker inspect <allowed-container> --format <fixed-template>
wsl -l -v
supabase --version
```

Allowed start commands:

```text
supabase start
docker start <allowed-supabase-container>
docker start supabase_edge_runtime_Extrusion_data
```

`supabase start` is allowed only after the runtime controller has verified that every required `supabase_*_Extrusion_data` container already exists. It is not a bootstrap command. If a required container is missing, the command runner must reject the start flow before command execution.

Allowed stop commands:

```text
docker stop <allowed-supabase-container>
```

Allowed containers:

```text
supabase_db_Extrusion_data
supabase_kong_Extrusion_data
supabase_auth_Extrusion_data
supabase_rest_Extrusion_data
supabase_realtime_Extrusion_data
supabase_storage_Extrusion_data
supabase_pg_meta_Extrusion_data
supabase_studio_Extrusion_data
supabase_inbucket_Extrusion_data
supabase_edge_runtime_Extrusion_data
supabase_analytics_Extrusion_data
supabase_vector_Extrusion_data
```

Required containers for the existence precheck are the full `supabase_*_Extrusion_data` allowlist above. The list is pinned to the current `Extrusion_data` local Supabase CLI container names. `supabase_imgproxy_Extrusion_data` is not required because image transformation is disabled in the reference `supabase/config.toml`. Grafana is intentionally excluded because Grafana remains status/link-only and is not controlled by this API. `docker start grafana_local` and `docker stop grafana_local` are forbidden in v1.

Explicitly forbidden:

```text
supabase db reset
supabase init
supabase stop
docker run
docker create
docker rm
docker rmi
docker volume
docker network rm
docker prune
docker system prune
docker compose up
docker compose down
docker compose rm
docker exec ... psql ... DROP/TRUNCATE/DELETE
shell metacharacters
user-supplied command strings
```

`supabase status` is not used as a primary source because it can print keys. If it is ever used for diagnostics, output must be parsed and redacted before persistence or UI display.

## Readiness Check Flow

Passive status check:

```text
1. Resolve settings and verify project path exists.
2. Read `supabase/config.toml` and confirm ports 54321, 25432, 54323.
3. Run WSL detection with `wsl -l -v`.
4. Run Docker detection with `docker version`.
5. List exact Supabase containers with `docker ps -a`.
6. Verify required containers already exist. Missing required containers produce `blocked|required_container_missing`.
7. Inspect required container state and health.
8. Probe TCP ports:
   - 127.0.0.1:25432 DB
   - 127.0.0.1:54321 API
   - 127.0.0.1:54323 Studio
9. Probe Edge route with `POST {}` without auth and a short timeout.
   - `401`, `Missing authorization header`, or a payload validation error means the route exists.
   - Connection refused, DNS error, or timeout means not ready.
10. Probe Grafana link only:
   - TCP/HTTP to configured URL or container state.
11. Compute operator-facing `overallStatus`, warnings, and errors.
```

Start operation:

```text
1. Insert runtime_operations queued.
2. Audit `runtime.supabase.start` requested.
3. Guard active upload/preview/runtime operation.
4. Mark operation running.
5. Run passive precheck.
6. If any required container is missing, mark blocked with `required_container_missing`; do not run `supabase start`.
7. If already ready, mark succeeded no-op.
8. If Docker unavailable, fail with operator message.
9. If Supabase CLI available and required containers exist, run `supabase start` in the fixed reference project path.
10. If CLI unavailable, start exact existing allowlisted containers only.
11. If Edge Runtime exists and stopped, `docker start supabase_edge_runtime_Extrusion_data`.
12. Poll readiness until timeout.
13. Mark succeeded, blocked, or failed; append runtime events and audit final result.
```

Stop operation:

```text
1. Insert runtime_operations queued.
2. Audit `runtime.supabase.stop` requested.
3. Guard active upload/preview/runtime operation.
4. Mark operation running.
5. If already stopped, mark succeeded no-op.
6. Stop allowlisted Supabase containers with exact `docker stop`.
7. Poll ports until DB/API/Studio are closed or timeout.
8. Mark succeeded or failed; append runtime events and audit final result.
```

Stop order:

```text
supabase_edge_runtime_Extrusion_data
supabase_studio_Extrusion_data
supabase_pg_meta_Extrusion_data
supabase_storage_Extrusion_data
supabase_realtime_Extrusion_data
supabase_rest_Extrusion_data
supabase_auth_Extrusion_data
supabase_inbucket_Extrusion_data
supabase_analytics_Extrusion_data
supabase_vector_Extrusion_data
supabase_kong_Extrusion_data
supabase_db_Extrusion_data
```

Grafana is not stopped by this API.

## Failure Modes

| Failure | API/UI status | Operator message | Audit |
| --- | --- | --- | --- |
| Project path missing | `blocked` | `Extrusion_data 경로를 찾을 수 없습니다.` | failure/block |
| `config.toml` port mismatch | `blocked` | `로컬 Supabase 포트 설정이 예상값과 다릅니다.` | failure/block |
| WSL CLI unavailable | `attention` or `blocked` | `WSL 상태를 확인할 수 없습니다.` | failure if command requested |
| Docker Desktop not running | `blocked` | `Docker Desktop을 먼저 실행해 주세요.` | failure |
| Docker daemon unreachable | `blocked` | `Docker daemon에 연결할 수 없습니다.` | failure |
| Supabase CLI missing | `attention` | `Supabase CLI가 없어 기존 컨테이너만 시작할 수 있습니다.` | warning event |
| Required container missing | `blocked|required_container_missing` | `필수 Supabase 컨테이너가 없습니다. 새 스택 생성은 v1에서 지원하지 않습니다.` | blocked/failure |
| Edge Runtime stopped | `attention` then start allowed | `Edge Runtime 컨테이너를 시작할 수 있습니다.` | success/failure |
| Port occupied by other process | `blocked` | `필수 포트가 다른 프로세스에 사용 중입니다.` | failure |
| DB port closed | `blocked` | `DB 포트 25432가 열려 있지 않습니다.` | failure |
| API port closed | `blocked` | `Supabase API 포트 54321이 열려 있지 않습니다.` | failure |
| Studio down only | `attention` | `Studio는 열리지 않지만 업로드 DB/API는 확인됩니다.` | status warning |
| Grafana down | `attention` | `Grafana는 별도 대시보드 링크만 제공됩니다.` | status warning |
| Active upload job | `blocked` | `업로드 작업 중에는 로컬 Supabase를 제어할 수 없습니다.` | blocked |
| Active preview run | `blocked` for stop | `Preview 실행 중에는 Supabase 종료를 막습니다.` | blocked |
| Command timeout | `failed` | `명령 시간이 초과되었습니다. Docker Desktop 상태를 확인해 주세요.` | failure |
| Redacted output detected | `attention` | `명령 출력 일부가 보안상 숨겨졌습니다.` | event only |

No failure path may be silent. It must appear in:

```text
runtime_operations
runtime_events
audit_log
Dashboard runtime panel
```

## Frontend Plan

### Dashboard Runtime Module

Replace mock-only runtime display with API-backed status when the backend is available.

Components:

```text
RuntimeStatusPanel
RuntimeServiceGrid
RuntimeActionBar
RuntimeOperationBanner
GrafanaLinkPanel
```

Panel content:

- Overall Local Supabase badge: `ready`, `running`, `attention`, `blocked`, `unknown`.
- Service rows: DB `25432`, API `54321`, Studio `54323`, Edge Runtime.
- Start/Stop buttons with disabled states and inline reasons.
- Last runtime operation summary.
- Grafana status and `Open Grafana` link only.

Action rules:

- Start disabled while upload job, preview run, or runtime operation is active.
- Stop disabled while upload job or preview run is active.
- Stop copy must be explicit: "로컬 Supabase 종료" / "Stop Local Supabase".
- No modal required for v1, but button text and audit log must make the action clear.

### Settings Integration

Add a Runtime section:

- Local Supabase project path.
- API/DB/Studio ports.
- Edge Runtime container name.
- Grafana URL.
- Source badge for each value: default, app config, env.

Do not add destructive maintenance controls.

### Visual Rules

Follow `docs/04_design_system.md`:

- Status always uses icon + label + color.
- Blocked/failed states must be visible within 3 seconds.
- Runtime table/list surfaces should be dense and bordered.
- Grafana remains link-only; no preview image, iframe, or dashboard cards.

## Interaction With Upload Preview And Upload Jobs

- Upload Preview still handles DB unreachable as `partial_failed` run and `risky/db_unreachable` items.
- Upload Start remains blocked when runtime status is `blocked`.
- Runtime Stop is blocked while an upload job is active.
- Runtime Stop is blocked while a preview run is active to avoid mid-reconciliation DB failure.
- Runtime Start is allowed when no upload/preview/runtime operation is active.
- Dashboard aggregate state uses runtime status:
  - `blocked` if DB/API unavailable.
  - `attention` if Grafana or Studio only is unavailable.
  - `running` if runtime start/stop is active.
  - `ready` when DB/API/Edge are ready and no upload blocker exists.

## Tests

Backend unit tests:

- Command allowlist permits only exact commands.
- Forbidden commands are rejected before execution.
- Command runner always uses `shell=False`.
- Command output redacts JWT-like tokens, anon keys, service keys, and long bearer strings.
- Runtime status maps Docker/port/container combinations to `ready`, `attention`, `blocked`, and `unknown`.
- `config.toml` port mismatch becomes `blocked`.
- Missing required container blocks start as `required_container_missing` and never calls `supabase start`.
- Command allowlist rejects `supabase start` when required container existence precheck failed.
- Edge Runtime stopped produces `attention` and start can call exact `docker start`.
- Start no-op when already ready.
- Start failure writes `runtime_events` and `audit_log`.
- Passive status polling success does not write `audit_log`.
- Stop no-op when already stopped.
- Stop is blocked by active upload job.
- Stop is blocked by active preview run.
- Edge route probe uses unauthenticated `POST {}` with short timeout and maps `401`, `Missing authorization header`, and validation errors to reachable.
- Runtime event seq is safe under concurrent append.

Backend API tests:

- `GET /api/runtime/local-supabase` returns expected DTO shape.
- `POST /api/runtime/local-supabase/start` returns `202` for accepted operation.
- start returns `409` and audit row for active upload conflict.
- start returns `409` and audit row for active preview conflict.
- start returns blocked/failure without command execution when required containers are missing.
- `POST /api/runtime/local-supabase/stop` returns `202` for accepted operation.
- stop returns `409` and audit row for active preview/upload conflict.
- `GET /api/runtime/operations/{id}` returns operation/events.

Frontend tests/checks:

- Dashboard renders runtime `ready`, `attention`, `blocked`, `running`.
- Start/Stop disabled reasons render in Korean and English.
- Grafana renders as link only.
- Small desktop width keeps runtime table readable.
- No v1-excluded management/delete controls appear.

Manual/browser QA:

- `GET /api/health`
- `GET /api/runtime/local-supabase`
- Dashboard ready/blocked runtime states.
- Start Local Supabase when stack is stopped.
- Stop Local Supabase when no upload/preview is active.
- Upload Preview regression with DB reachable and DB unreachable.
- Upload Job regression: active job blocks runtime stop.

Validation commands:

```powershell
.\.venv\Scripts\python -m pytest tests\backend
npm run typecheck
npm run build
git diff --check
```

## Implementation Order

1. Add settings defaults for local Supabase runtime and Grafana link.
2. Add runtime schemas and command runner with strict allowlist tests.
3. Add passive readiness probes for project path, config ports, WSL, Docker, containers, TCP ports, Edge route, and Grafana link.
4. Add runtime SQLite repository and audit logging for runtime operations.
5. Add `GET /api/runtime/local-supabase`.
6. Add required-container existence precheck and tests before wiring any start command.
7. Add `POST /api/runtime/local-supabase/start` with active preview/upload guards, no-op handling, command output redaction, and readiness polling.
8. Add `POST /api/runtime/local-supabase/stop` with active job/preview guards and exact `docker stop` allowlist.
9. Add operation detail endpoint.
10. Wire Dashboard runtime panel to API status and operation polling.
11. Add Settings Runtime section with source badges.
12. Run backend tests, frontend typecheck/build, and browser QA.
13. Update README with non-destructive runtime control behavior.

## Merge Readiness Criteria

- No command path can execute destructive Docker/Supabase operations.
- Runtime start/stop failures are visible in API response, Dashboard, runtime events, and audit log.
- Missing required containers block start before `supabase start` or `docker start`; v1 does not bootstrap/create a new stack.
- Passive status polling success does not create audit spam.
- Stop is blocked during active upload jobs and active preview runs.
- Start is blocked during active upload jobs and active preview runs.
- DB/API/Studio ports use `25432`, `54321`, and `54323`.
- Grafana is link/status only.
- Backend tests, frontend typecheck, frontend build, and `git diff --check` pass.
- Local operator-PC E2E confirms start/status/stop without data loss or container/volume deletion.

## Implementation Result

Implemented on branch `codex/local-supabase-control-impl`:

- Added `GET /api/runtime/local-supabase`, `POST /api/runtime/local-supabase/start`, `POST /api/runtime/local-supabase/stop`, and `GET /api/runtime/operations/{operationId}`.
- Added strict `AllowedCommandRunner` policy with `shell=False`, exact read/start/stop command allowlist, and forbidden destructive command coverage.
- Added required-container existence precheck. Missing required Supabase containers block start as `required_container_missing`; v1 still does not bootstrap or create a local stack.
- Added runtime operation/event SQLite persistence and startup interruption marking.
- Added audit rows for manual start/stop success/failure/blocked paths while leaving passive status polling success out of `audit_log`.
- Added readiness checks for Docker, WSL, Supabase CLI, required containers, API `54321`, DB `25432`, Studio `54323`, Edge Function unauthenticated `POST {}`, and Grafana status/link.
- Connected the Dashboard runtime panel to the runtime API in API mode with Start/Stop controls.
- Replaced the Settings placeholder with a runtime config/source editor connected to `GET /api/config` and `PUT /api/config`.
- Added Korean/English runtime and settings UI text.

Verification completed during implementation:

- `.\.venv\Scripts\python -m pytest tests\backend --basetemp C:\tmp\ewc-pytest`
- `npm run typecheck`
- `npm run build`

Remaining risks:

- Operator-PC E2E for actual Docker Desktop/WSL/local Supabase start-stop needs to be run before merge confidence is final.
- Runtime command output is captured only for operation events/audit summaries; future Logs/Audit pages should expose it with redaction.
- Settings save UI is implemented for config JSON writes. Env/process and repo `.env` overridden values remain visibly read-only and backend-blocked from save attempts; local Supabase runtime command policy remains unchanged.
