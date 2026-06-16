# Dev Source Binding Hardening Analysis

## Summary

Match Rate: 97%

This change hardens the developer API-mode source binding path without running Upload Preview, Start Upload, Retry Failed, or any DB/Supabase/Docker lifecycle operation.

The main issue was configuration drift: when the developer launcher started the backend with stale or non-canonical source binding, the active PLC source could point at a fixture, stale UNC, or other wrong source. At the same time, the frontend mock Settings fallback showed a sample-looking source value that could be mistaken for an operator setting. That combination made it too easy to read the wrong source state.

## Scope

In scope:

- Developer launcher canonical PLC source guard and process-only fallback.
- Frontend mock Settings fallback copy.
- API-mode execution guidance for `/api/config`.
- Regression coverage for config API source classification.

Out of scope:

- Operator package source pinning.
- AppData config mutation.
- Settings save.
- Upload Preview, Start Upload, Retry Failed, duplicate rerun, authenticated Edge calls, full rollout.
- DB/Supabase/Docker lifecycle or destructive operations.

## Evidence

| Item | Result |
| --- | --- |
| Backend Settings default | empty unless explicit env/config or launcher process fallback supplies a value |
| Developer launcher fallback | process-only mapped-drive class only when no env/dotenv/config provides `plcDataDir` |
| Non-canonical source handling | default launcher start blocked, `-AllowNonCanonicalSource` required for diagnostics |
| Explicit source precedence | preserved for env and config JSON |
| API-mode source of truth | backend `/api/config` items and targetClasses |
| Frontend mock fallback | neutral development sample value |
| Settings save path | unchanged |
| Upload execution behavior | unchanged |
| Active console preflight | `/api/config` reachable, active process source accessible, CSV count 9 |
| Branch backend preflight | `/api/config` reachable, source accessible, CSV count 9 |

## Gap Analysis

| Requirement | Status | Evidence |
| --- | --- | --- |
| Keep developer source binding stable | matched | launcher blocks non-canonical PLC source binding before backend start |
| Preserve explicit env/config source | matched | backend Settings no longer rewrites explicit source bindings; launcher surfaces drift instead of silently changing it |
| Avoid mock fallback looking like operator config | matched | Settings mock fallback no longer uses source-like slash labels |
| Clarify API-mode source evidence | matched | README states API-mode uses `/api/config` as source evidence |
| Do not mutate AppData config | matched | no Settings save or config file write performed |
| Do not run Preview/Upload/Retry | matched | no mutation endpoints were executed |
| Operator package source pinning | deferred | explicitly left as separate decision |

## Risk Review

Risk level: medium.

The launcher guard still depends on the user's Windows session mapping for the canonical mapped-drive class. If that mapping is unavailable to the launcher-owned backend process, default startup is blocked and Preview must remain blocked until an explicit canonical, accessible source binding is supplied. The intended mitigation is read-only `/api/config` plus backend-side source existence confirmation before Preview.

Rollback is a normal PR revert. No DB migration, config file migration, package output, or runtime state mutation is involved.

## Nondeveloper Explanation

The web console has two different modes.

In real API mode, the backend tells the UI which process-data folder is active. That answer comes from `/api/config`.

In mock development mode, the UI only shows sample text so developers can inspect the screen. That sample text must not look like a real operator folder. This change makes that distinction clearer and makes the developer launcher stop when the configured source is not the approved mapped-drive class.

## Validation Plan

- `git status --short --branch`: branch `codex/dev-source-binding-hardening`, protected untracked items left uncommitted.
- read-only `/api/config`: active console reachable, source accessible, CSV count 9, targetClasses passed.
- branch backend-process source accessibility class/count preflight: temporary backend reachable, source accessible, CSV count 9.
- targeted config tests: 18 passed, 2 warnings unrelated to this change.
- upload preview API contract / DTO tests: 24 passed, 2 warnings unrelated to this change.
- PowerShell launcher parser check: passed.
- `launcher/start_web_console.ps1 -CheckOnly`: blocked current non-canonical repo/config source classes as expected; no backend process started.
- `launcher/start_web_console.ps1 -CheckOnly -AllowNonCanonicalSource`: passed with warning; no backend process started.
- `npm run typecheck`: passed.
- i18n JSON parse: passed.
- `npm run build:api`: passed.
- `npm run build`: passed after rerunning sequentially; an earlier parallel build invocation collided on the shared `frontend/dist` output directory.
- `git diff --check`: passed with Windows CRLF warnings only.
- marker scan: old mock source markers removed from changed frontend/source bundle paths; secret/source scans produced only existing redaction documentation/test fixtures or non-raw generic wording.
