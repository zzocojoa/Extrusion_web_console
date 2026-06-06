plan-eng-review 기준으로 기술 설계를 확정합니다. 기준 문서는 [AGENTS.md](/C:/Users/user/Documents/GitHub/Extrusion_web_console/AGENTS.md), [README.md](/C:/Users/user/Documents/GitHub/Extrusion_web_console/README.md), [docs/00_product_scope.md](/C:/Users/user/Documents/GitHub/Extrusion_web_console/docs/00_product_scope.md), [docs/01_development_roadmap.md](/C:/Users/user/Documents/GitHub/Extrusion_web_console/docs/01_development_roadmap.md)를 따릅니다.

**핵심 결정**
1. Backend: `FastAPI + Uvicorn + Pydantic + SQLite WAL`.
   이유: 기존 Python 업로드/변환 코드를 가장 적게 흔들고, SSE 스트리밍과 typed API를 깔끔하게 제공한다. Django는 과하고 Flask는 타입/스키마/비동기 운영 이벤트에 약하다.

2. Frontend: `React + Vite + TypeScript + TanStack Query + i18next`.
   이유: 운영 콘솔 UI에 필요한 상태 관리, SSE 구독, bilingual UI, 컴포넌트 분리가 안정적이다. Production은 FastAPI가 빌드된 static을 서빙한다.

3. Worker: 별도 큐 서버 없이 backend in-process `ThreadPoolExecutor`.
   단일 operator PC, localhost 전용이므로 Celery/RQ는 과하다. 단, 모든 job/event는 SQLite에 persist해서 재시작 복구한다.

**디렉터리 구조**
```text
backend/
  app/
    main.py
    api/
    core/              # copied/extracted transform/upload/files adapters
    services/          # upload, preview, runtime, grafana, audit, config
    db/                # sqlite schema + repositories
    schemas/           # pydantic DTOs
frontend/
  src/
    api/
    i18n/
    pages/             # Dashboard, Settings, Upload, Logs
    components/
launcher/
  start_web_console.ps1
  start_web_console.bat
supabase/
  functions/upload-metrics/
  migrations/
grafana/
  provisioning/
  dashboards/
tests/
  backend/
  frontend/
  integration/
docs/
```

**기존 자산 재사용**
- 재사용: [core/upload.py](/C:/Users/user/Documents/GitHub/Extrusion_data/core/upload.py:27)의 `UploadSession*`, `run_upload_session`; [core/transform.py](/C:/Users/user/Documents/GitHub/Extrusion_data/core/transform.py:28)의 PLC/temp 변환; [core/files.py](/C:/Users/user/Documents/GitHub/Extrusion_data/core/files.py:31)의 preflight 모델.
- 수정 필요: `core/files.py`는 legacy `load_processed()` 의존을 제거하고 새 state repository를 주입한다.
- 패턴 재사용: [core/state_db.py](/C:/Users/user/Documents/GitHub/Extrusion_data/core/state_db.py:449)의 upload run/file state SQLite 구조.
- 그대로 유지해야 할 안전장치: [upload-metrics/index.ts](/C:/Users/user/Documents/GitHub/Extrusion_data/supabase/functions/upload-metrics/index.ts:299)의 `onConflict: "timestamp,device_id"`와 [20260421000001_restore_all_metrics_device_scope.sql](/C:/Users/user/Documents/GitHub/Extrusion_data/supabase/migrations/20260421000001_restore_all_metrics_device_scope.sql:61)의 unique constraint.

**Backend API**
```text
GET  /api/health
GET  /api/config
PUT  /api/config                       audit: settings.save
GET  /api/runtime/supabase/status
POST /api/runtime/supabase/start       audit: supabase.start
POST /api/runtime/supabase/stop        audit: supabase.stop
GET  /api/runtime/grafana/status
POST /api/upload/preview               audit: upload.preview
GET  /api/upload/preview/latest
GET  /api/upload/preview/{preview_run_id}
POST /api/upload/preview/{preview_run_id}/cancel
POST /api/upload/jobs                  audit: upload.start
POST /api/upload/jobs/{id}/retry       audit: upload.retry
POST /api/upload/jobs/{id}/pause       audit: upload.pause
POST /api/upload/jobs/{id}/resume      audit: upload.resume
POST /api/upload/jobs/{id}/cancel      audit: upload.cancel
GET  /api/upload/jobs
GET  /api/upload/jobs/{id}
GET  /api/upload/jobs/{id}/events      SSE
GET  /api/audit
GET  /api/logs
```

**State Store**
새 DB는 `%APPDATA%\ExtrusionWebConsole\web_console_state.db`. 기존 `uploader_state.db`는 기본 import하지 않는다.

필수 테이블:
```text
app_config(key, value_json, updated_at)
audit_log(audit_id, ts, actor, action, target_type, target_id,
          params_json_redacted, result, error_code, error_message,
          job_id, request_id)
upload_jobs(job_id, type, status, requested_at, started_at, finished_at,
            total_files, success_files, failed_files, warning_count,
            config_snapshot_json, error_message)
upload_job_files(job_file_id, job_id, file_key, folder, filename, path,
                 kind, status, resume_offset, row_count, inserted_count,
                 last_error, retry_count)
job_events(event_id, job_id, seq, ts, level, event_type, message, data_json)
file_state(file_key, legacy_key, folder, filename, state,
           resume_offset, last_error, retry_count, completed_at, failed_at)
preview_runs(...)
preview_items(...)
```

**Upload Job 상태**
```text
queued -> running -> succeeded
                 -> partial_failed
                 -> failed
                 -> pausing -> paused -> running
                 -> cancelling -> cancelled
                 -> interrupted
```
재시작 시 `running/pausing/cancelling` job은 `interrupted`로 닫고, 파일별 `resume_offset`과 `failed_retry_set`으로 복구 가능하게 한다.

**Preview 데이터 흐름**
```text
Local CSV dirs
  -> candidate scan/files preflight
  -> transform chunks to canonical rows
  -> build local keys: (timestamp, device_id)
  -> query local Supabase by exact key batches
  -> classify per file:
       already_in_db | upload_target | partial_overlap | risky | excluded
  -> persist preview_run + preview_items
  -> UI table with reasons
```
Preview는 “latest timestamp only”로 판단하지 않는다. 정확한 reconciliation은 `(timestamp, device_id)` key batch join/count로 한다. 최종 중복 방지는 DB unique/upsert가 계속 담당한다.

**Upload 데이터 흐름**
```text
UI start/retry
  -> FastAPI validates config + state health
  -> audit_log row: upload.start
  -> upload_jobs row queued/running
  -> worker calls extracted run_upload_session()
  -> per-file state + job_events persisted
  -> POST edge function upload-metrics
  -> Supabase upsert on (timestamp, device_id)
  -> SSE streams job_events to UI
  -> final audit success/failure
```

**Streaming**
SSE로 확정. `GET /api/upload/jobs/{id}/events?after_seq=N`를 지원하고 `Last-Event-ID` reconnect를 처리한다. 모든 progress/log는 `job_events`에 먼저 저장한 뒤 publish한다. UI가 닫혀도 로그가 사라지지 않는다.

**Config**
우선순위:
```text
built-in defaults
< %APPDATA%\ExtrusionWebConsole\config.json
< repo .env / launcher env
< process environment
```
UI 저장은 `config.json`만 갱신한다. env override가 있는 key는 UI에서 “overridden”으로 표시한다. secrets는 audit/log에서 redaction한다. 기존 `compute_edge_url`, `validate_config` 로직은 재사용한다.

Implementation status on PR #8:

- `GET /api/config` returns known config keys with source metadata and hides secret values.
- `PUT /api/config` saves allowed keys to config JSON and records `settings.save` audit rows for success, validation failure, malformed JSON/body failure, and env override blocked attempts.
- Settings load reads config JSON after built-in defaults and before repo `.env` / launcher env and process environment; env/process overrides still win.
- Audit params store safe metadata such as `savedSettings`, `rejectedSettings`, `validationReason`, and `configPathConfigured`, not raw config values.
- Secret/config raw values, DB URLs, tokens, anon keys, service role values, and malformed request bodies must not appear in responses, audit params, or logs.
- Config writes use a per-config-file in-process lock, unique temp filename, and atomic replace.
- Settings UI save integration is implemented. In API mode it loads `GET /api/config`, sends changed editable values through `PUT /api/config`, disables env/process and repo `.env` overridden fields, excludes empty/unchanged secret placeholder inputs from payloads, includes a secret key only when the operator types a replacement value, shows validation/save status, and refetches after save.

**Local Supabase**
Backend가 고정 allowlist command만 실행한다.
- status: `wsl.exe ... supabase status`, Docker container health, Edge runtime probe, DB `pg_isready`
- start: WSL project dir에서 `supabase start`, DB ready wait, required migrations check
- stop: `supabase stop`
- fallback: Supabase CLI 없으면 `docker start/stop supabase_*_Extrusion_data` 패턴만 허용

임의 shell 입력은 받지 않는다.

**Grafana**
웹앱 안에 iframe embedding 없음. `GET /api/runtime/grafana/status`는 configured URL, 기본 `http://localhost:3001`, HTTP status와 Docker container 상태만 확인한다. UI는 “Open Grafana” 링크만 제공한다. 기존 provisioning/dashboard 파일은 복사한다.

**보안**
- Backend bind: `127.0.0.1` only.
- CORS: same-origin 또는 `127.0.0.1` dev port만.
- Launcher phase 1은 loopback enforcement와 backend-origin static serving을 제공한다.
- Launcher phase 2 is implemented: operator mode generates a per-run local token, passes it to the backend through process environment, injects a runtime bootstrap into the served frontend shell, and requires `X-EWC-Local-Token` for mutating `/api/*` routes.
- Protected mutating routes include Settings save, Upload Preview start/cancel, Upload Job start/retry/pause/resume/cancel, and Local Supabase start/stop. Read-only APIs, upload/job status reads, SSE events, `/api/health`, `/api/config`, and `/api/audit` remain token-free.
- Operator launcher mode disables `/api/docs`, `/api/openapi.json`, and ReDoc-style documentation routes by route configuration instead of token-gating them. Dev/test docs-enabled mode keeps Swagger/OpenAPI available with `EWC_API_DOCS_MODE=enabled`.
- Missing or invalid local tokens return `403 local_token_required` and write rate-limited blocked audit rows with safe metadata only. Token values must not appear in URL queries, storage, logs, audit params, screenshots, or generated artifacts.
- Vite development uses explicit `EWC_LOCAL_TOKEN_MODE=dev-disabled` when the backend is not serving the bootstrap token.
- Configured PLC/TEMP directory 밖 파일 접근 금지.
- Runtime commands는 allowlist.
- audit log append-only. UI delete 없음.

**오류 처리**
모든 background exception은 세 곳에 기록한다: `job_events`, `upload_jobs/upload_job_files`, `audit_log`. UI Dashboard는 latest failed job과 failed files를 반드시 표시한다. Supabase DB unreachable이면 upload start는 block, preview는 `risky/db_unreachable`로 표시한다.

**테스트 전략**
- Unit: config precedence, audit redaction, state transitions, SSE replay.
- Legacy regression copy: [test_smart_sync_regressions.py](/C:/Users/user/Documents/GitHub/Extrusion_data/tests/test_smart_sync_regressions.py), [test_upload_progress_core.py](/C:/Users/user/Documents/GitHub/Extrusion_data/tests/test_upload_progress_core.py).
- Contract: migration has `all_metrics_timestamp_device_id_key`; edge function uses `onConflict: timestamp,device_id`.
- Integration: local Supabase preview exact reconciliation, upload retry, DB down failure path.
- Frontend: Dashboard/Settings/Upload/Logs smoke, Korean/English toggle.
- Launcher: starts backend, opens browser, reuses port or reports clear error.

**구현 순서**
1. Scaffold backend/frontend/launcher and health page.
2. Add SQLite schema, config, audit services.
3. Extract transform/files/upload core with injected state callbacks.
4. Copy Supabase function/migrations and Grafana provisioning.
5. Implement Supabase/Grafana status/start/stop.
6. Implement upload preview reconciliation.
7. Implement upload jobs, retry, pause/resume/cancel, SSE.
8. Build frontend Core Ops screens.
9. Add double-click launcher.
10. Run regression, integration, frontend smoke tests.

**Failure Modes**
```text
CSV transform fails        -> file failed, job partial_failed, UI visible, tested
SSE disconnect             -> reconnect by seq, no lost logs, test needed
Supabase DB down           -> upload blocked, audit failure, integration test
Edge function 500          -> retry then failed file, existing upload test base
Backend killed mid-upload  -> startup marks interrupted, resume available, test needed
Config env override hidden -> UI source_by_key, audit redacted, unit test
Grafana down               -> status degraded, link still shown, smoke test
```
Critical silent-failure gap: none allowed by design. The two “test needed” items must be implemented before v1 signoff.

**Launcher phase 1 implementation status**

- FastAPI serves built `frontend/dist` for operator mode after API routers are registered.
- `/api/*` routes keep precedence over SPA fallback; unknown `/api/*` returns API-style 404 rather than the frontend shell.
- `/`, `/upload`, `/logs`, and `/settings` are served from the built frontend when `frontend/dist/index.html` exists.
- Missing built frontend returns a clear `503`, and the launcher also blocks before backend start unless explicit `-BuildFrontend` is used.
- Windows launcher scripts exist at `launcher/start_web_console.ps1` and `launcher/start_web_console.bat`.
- The launcher binds Uvicorn to `127.0.0.1`, supports `-CheckOnly`, opens the browser to the backend origin, writes logs under `%APPDATA%\ExtrusionWebConsole\logs\launcher\`, and handles port conflicts without killing unknown processes.
- `npm run build` is not part of the double-click operator default path. It runs only through explicit `-BuildFrontend`, and that path fails clearly when the build exits non-zero or does not produce `frontend/dist/index.html`.
- Launcher phase 1 does not run local Supabase bootstrap, reset, cleanup, prune, create/delete, Docker volume operations, or arbitrary command input.
- QA passed for targeted launcher/static backend tests, full backend tests, frontend typecheck/build, screenshot QA, `-CheckOnly`, `-BuildFrontend -CheckOnly`, port conflict smoke, backend-origin HTTP smoke, and missing frontend `503` smoke.

**Launcher phase 2 implementation status**

- Per-run local token enforcement is implemented on branch `codex/launcher-local-token-impl`.
- The launcher sets `EWC_LOCAL_TOKEN_MODE=required` and passes `EWC_LOCAL_API_TOKEN` through process environment only; token values are not printed by `-CheckOnly`.
- The launcher sets `EWC_API_DOCS_MODE=disabled` in operator mode; `-CheckOnly` reports docs policy without printing token or secret values.
- FastAPI serves token bootstrap HTML with `Cache-Control: no-store` without mutating `frontend/dist/index.html`.
- Frontend mutating API calls add `X-EWC-Local-Token` only for same-origin `/api/*` requests.
- QA passed targeted token/static/launcher tests (`17 passed`), full backend tests from clean cwd (`151 passed`), frontend typecheck/build/`qa:screenshots`, token HTTP smoke, and unsafe marker scans (`0` matches).
- Repo cwd `.env` presence can change config override behavior during tests; clean-cwd backend test runs remain the authoritative full-suite validation for this branch.

**Parallelization**
```text
Lane A: backend state/config/audit -> upload job service
Lane B: frontend shell/i18n/pages using mocked API
Lane C: supabase/grafana asset copy + runtime status service
Lane D: launcher scripts

Merge A+C before real upload integration.
Merge A+B before SSE UI verification.
Launcher waits until backend port/token behavior is stable.
```

**NOT in scope**
- Data archive/delete UI: explicitly deferred.
- Supabase delete management UI: explicitly deferred.
- Cycle Ops: not Core Ops v1.
- Training Dataset Builder: separate product area.
- Cloud Supabase migration: local-only v1.
- Multi-user LAN web app: violates localhost-only constraint.
- Grafana iframe embedding: Grafana stays separate.
- Automatic legacy `uploader_state.db` import: forbidden for default migration path.
