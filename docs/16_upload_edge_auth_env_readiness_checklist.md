# Upload Edge Auth Environment Readiness Checklist

Status: engineering checklist for `codex/upload-edge-auth-env-checklist`

Purpose: prevent authenticated Upload Job smoke QA from stopping at `preconfigured_env_missing` or runtime unavailable.

## Scope

This checklist prepares the local operator environment for authenticated Upload Job smoke against the local Supabase Edge Function.

It is a runbook only. It does not change application code, test data, database rows, Docker containers, or Supabase schema.

## Non-Negotiable Safety Rules

- Do not print, paste, commit, or document secret values.
- Do not ask the operator to paste secret values into chat.
- Do not record DB URLs, auth keys, service role values, JWTs, tokens, Authorization headers, raw CSV paths, CSV filenames, CSV content, or row content in QA reports.
- Configure required values only through local `.env`, PowerShell environment variables, or app config.
- Record only `present` or `missing` for secret-bearing configuration.
- Do not run DB reset, delete, cleanup, truncate, prune, or migration repair commands.
- Do not delete Docker volumes or containers.
- Do not commit operational CSV fixtures.
- Do not upload the full operational fixture for smoke QA.

## Required Local Services

All services must be reachable before authenticated smoke starts.

| Item | Expected readiness |
| --- | --- |
| Docker Desktop | Running |
| Local Supabase API | `127.0.0.1:54321` reachable |
| Local Supabase Studio | `127.0.0.1:54323` reachable |
| Local Supabase DB TCP | `127.0.0.1:25432` reachable |
| Edge runtime | Running |
| Edge route | No-auth request returns `401` or a validation/auth-related error, not connection failure |

Presence-only runtime checks:

```powershell
$ports = @{
  SupabaseApi = 54321
  SupabaseStudio = 54323
  SupabaseDb = 25432
}

foreach ($item in $ports.GetEnumerator()) {
  $ok = Test-NetConnection 127.0.0.1 -Port $item.Value -InformationLevel Quiet
  "{0}={1}" -f $item.Key, $(if ($ok) { "reachable" } else { "unreachable" })
}

curl.exe -s -o NUL -w "edgeNoAuthStatus=%{http_code}" `
  http://127.0.0.1:54321/functions/v1/upload-metrics
```

Allowed interpretation:

- `401`: route reachable and auth required.
- `400` or `422`: route reachable and rejecting the unauthenticated/empty request shape.
- `000`: route unreachable; stop.
- Any status that requires printing response body to understand it: stop and inspect locally without putting the body into the report.

## Required Configuration Presence

The following settings must be present through approved local channels before smoke starts.

| Required setting | Accepted channels | Record in QA |
| --- | --- | --- |
| Supabase DB URL | local `.env`, PowerShell env var, app config | `present` or `missing` |
| Supabase Edge URL | local `.env`, PowerShell env var, app config | `present` or `missing` |
| Supabase anon/auth key | local `.env`, PowerShell env var, app config | `present` or `missing` |
| Source CSV/config path | local `.env`, PowerShell env var, app config | `present` or `missing` |
| State DB/config path | local `.env`, PowerShell env var, app config | `present` or `missing` |

Use key names only:

```text
EWC_SUPABASE_DB_URL
EWC_SUPABASE_EDGE_URL
EWC_SUPABASE_URL
EWC_SUPABASE_ANON_KEY
EWC_PLC_DATA_DIR
EWC_TEMPERATURE_DATA_DIR
EWC_STATE_DB_PATH
EWC_CONFIG_FILE_PATH
```

Presence-only process environment check:

```powershell
$keys = @(
  "EWC_SUPABASE_DB_URL",
  "EWC_SUPABASE_EDGE_URL",
  "EWC_SUPABASE_URL",
  "EWC_SUPABASE_ANON_KEY",
  "EWC_PLC_DATA_DIR",
  "EWC_TEMPERATURE_DATA_DIR",
  "EWC_STATE_DB_PATH",
  "EWC_CONFIG_FILE_PATH"
)

foreach ($key in $keys) {
  "{0}={1}" -f $key, $(if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) { "missing" } else { "present" })
}
```

Do not run commands that dump `.env`, Supabase status, Docker inspect, process environment, app config files, or request/response bodies with raw values into the QA transcript.

## App Config Readiness

When backend is running, `GET /api/config` may be used to verify source metadata and hidden secret values.

Safe expectations:

- Secret-bearing items have `secret=true`.
- Secret-bearing items with configured values return `value=null`.
- Source is visible as metadata such as `env`, `config`, or `default`.
- The response must not contain raw DB URLs, auth keys, JWTs, service role values, or tokens.

Allowed smoke:

```powershell
$config = Invoke-RestMethod http://127.0.0.1:8000/api/config
$config.items |
  Where-Object { $_.key -in @("supabaseDbUrl", "supabaseAnonKey", "supabaseEdgeUrl") } |
  Select-Object key, source, secret, @{ Name = "valueState"; Expression = { if ($null -eq $_.value) { "hidden_or_empty" } else { "visible" } } }
```

Stop if any configured secret-bearing key returns a visible raw value.

## Backend And Vite Readiness

The smoke must run against the intended branch or PR head.

Backend readiness:

```powershell
git rev-parse HEAD
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod "http://127.0.0.1:8000/api/audit?action=upload.start&limit=1"
```

Frontend readiness:

- Run Vite with API mode for real backend calls.
- Vite proxy must forward `/api` to `http://127.0.0.1:8000`.

```powershell
$env:VITE_API_MODE="api"
npm run dev -- --host 127.0.0.1 --port 5173

curl.exe -s -o NUL -w "viteRoot=%{http_code}" http://127.0.0.1:5173/
curl.exe -s -o NUL -w "viteProxyAudit=%{http_code}" "http://127.0.0.1:5173/api/audit?action=upload.start&limit=1"
```

Stop if Vite is serving mock mode when the smoke requires real API mode.

## Git Hygiene

Before creating any QA report or PR:

```powershell
git status --short --branch
```

Expected:

- Report document changes are tracked.
- Operational CSV fixture remains untracked if present.
- No operational CSV fixture, temp sample, local state DB, secret file, `.env`, log file, screenshot containing secrets, or raw CSV content is staged.

Before commit:

```powershell
git diff --cached --name-status
```

Stop if anything other than the intended report/checklist document is staged.

## Exact Sample Strategy

Use the sanitized data label `integrated_plc_operational_fixture` in reports.

Rules:

- Original fixture is read-only.
- Original full fixture is never uploaded for smoke QA.
- Create a minimal temporary sample only when needed.
- The temporary sample path, original path, raw filename, and CSV content are not documented.
- If a safe minimal sample cannot be prepared without exposing sensitive path/content or risking unintended large upload, stop with `sample_unsafe`.

The smoke should prefer a duplicate-safe minimal sample whose exact keys are already known to exist in `all_metrics`. If that is not possible, document the limitation before any upload attempt.

## Preview And Upload Start Strategy

Readiness gate before `POST /api/upload/jobs`:

- Backend is running at the intended PR head.
- Vite is in API mode if browser/API proxy smoke is part of the run.
- Local Supabase DB is reachable.
- Edge route is reachable.
- Required env/app settings are `present`.
- A Preview run has terminal status `succeeded`.
- Preview DB status is `reachable`.
- Upload target setup uses only the safe minimal sample strategy.
- No active preview or upload job is running.

Stop if Preview returns `partial_failed`, `risky/db_unreachable`, `no_upload_targets` for the intended sample, or if active job/preview conflicts are present.

## Duplicate-Safe Verification Strategy

Do not clean, delete, or reset DB rows.

For the minimal sample:

1. Count exact `(timestamp, device_id)` keys before upload.
2. Start Upload from safe Preview target rows.
3. Wait for terminal Upload Job status.
4. Count the same exact keys after upload.
5. Run the duplicate-safe rerun.
6. Count the same exact keys again.

Expected:

- First upload reaches terminal `succeeded` or a clearly documented failure state.
- Duplicate rerun does not increase exact-key row count.
- Existing `all_metrics(timestamp, device_id)` upsert safety remains the protection boundary.

Only record counts, status names, job IDs, preview IDs, and redaction results. Do not record raw keys, row contents, file paths, DB URLs, or auth headers.

## Audit Verification

Required audit checks:

```text
GET /api/audit?action=upload.start
```

Verify:

- `upload.start` row exists for the smoke attempt.
- success/failure/blocked result matches the actual operation.
- `jobId` or target id links the audit row to the Upload Job.
- Params contain safe metadata only.
- Params do not contain raw source path, raw filename, DB URL, auth key, service role, JWT, token, Authorization header, CSV content, or row content.

If an audit row contains raw sensitive data, stop and mark the smoke as a security blocker.

## SSE Verification

Required SSE checks:

- Full replay from the beginning of the job event stream.
- `afterSeq` replay from a known event sequence.
- No duplicate events across replay.
- Terminal job event is present.

Allowed evidence:

- event count
- first and last sequence numbers
- terminal event type
- status code
- replay range

Forbidden evidence:

- raw CSV content
- source paths
- auth headers
- DB URLs
- token-like values
- raw request or response bodies that may include secrets

## Stop Conditions

Stop immediately and record the listed reason when any condition is true.

| Stop reason | Condition |
| --- | --- |
| `preconfigured_env_missing` | Any required DB URL, Edge URL/auth key, source path, or state/config path is missing |
| `runtime_unavailable` | Docker, local Supabase API, Studio, DB TCP, or Edge route is unreachable |
| `edge_auth_unavailable` | Edge route cannot be authenticated with approved preconfigured values |
| `backend_head_mismatch` | Backend is not running the intended PR head |
| `vite_proxy_mismatch` | Vite proxy does not reach the intended backend |
| `sample_unsafe` | Minimal sample cannot be prepared without unsafe path/content exposure or large upload risk |
| `active_operation_conflict` | Active preview/upload job makes the smoke ambiguous |
| `audit_secret_exposure` | Audit or logs expose raw secret/path/token content |

## Ready-To-Run Decision

Authenticated Upload Job smoke may start only when all are true:

- Docker Desktop is running.
- Local Supabase API, Studio, DB TCP, and Edge route are reachable.
- No-auth Edge route proves the route is alive.
- Required env/app settings are present.
- `GET /api/config` hides configured secret values.
- Backend is the intended PR head.
- Vite API proxy reaches the intended backend when UI smoke is included.
- Operational fixture remains untracked.
- Minimal sample strategy is safe.
- Duplicate-safe verification will use exact key counts without DB cleanup.
- Audit and SSE verification plans are ready.

If any item is false, do not run authenticated upload. Record the stop reason and create a report-only QA artifact.
