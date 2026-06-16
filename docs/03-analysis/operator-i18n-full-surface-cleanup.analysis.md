# operator-i18n-full-surface-cleanup - Analysis

> Date: 2026-06-16
> Verdict: implementation_ready_for_review
> Match Rate: 96%

## Summary

The original issue was an English Preview reason, `File date is outside the preview range.`, appearing in Korean UI. The first fix localized known Preview `reasonCode` values. This follow-up expands the same display policy to Dashboard, runtime, Settings, and job event surfaces where backend `label`, `detail`, `summary`, or `message` fields were rendered directly.

For non-developers: the backend can still keep English diagnostic text for logs and debugging, but the operator screen now translates known operational reasons and statuses before showing them. Unknown diagnostics remain visible as fallback so errors are not hidden.

## Investigated Surfaces

| Surface | Finding | Action |
|---------|---------|--------|
| Upload Preview table | Known `reasonCode` values could fall back to backend English `reasonText`. | Keep i18n-first reason display with sanitized fallback. |
| Dashboard top bar/status matrix | Backend labels and details such as latest upload state were rendered directly. | Add display helper for known item ids and message patterns. |
| Dashboard safety banner | Backend titles/messages were rendered directly. | Add title/message mapping for known Dashboard states. |
| Runtime panel | Runtime status details and reason text were shown directly. | Translate known reason/status classes while preserving diagnostic host/port identifiers. |
| Warning queue | Backend warning labels/impact text were shown directly. | Map known warning ids to locale keys. |
| Recent jobs/current job | Backend job count message was shown directly. | Translate known job-count pattern. |
| Logs and Upload job events | Known event messages were shown directly. | Translate known job event patterns without changing event codes. |
| Audit log error messages | Known backend diagnostic `errorMessage` values could be rendered directly. | Translate known audit diagnostics at render time; keep unknown fallback visible. |
| Settings | State-context label and env override wording could remain English. | Map known state context classes and Korean env override wording. |

## Design Decision

The implementation keeps backend API payloads unchanged. Frontend helpers translate known patterns at render time:

- Known code/id/pattern: render i18n text.
- Unknown diagnostic: render existing sanitized fallback.
- Operational identifiers such as job IDs, event types, service names, env var names, and product names remain visible.

This avoids a backend schema migration and keeps operator diagnostics available.

## Safety Controls

- Upload Preview was not executed.
- Start Upload was not executed.
- Retry Failed, duplicate rerun, authenticated Edge call, and full rollout were not executed.
- DB/Supabase/Docker lifecycle or destructive operations were not executed.
- Operational CSV files were not modified.
- No raw operational source path, source content, DB URL, token value, Authorization header, JWT, or secret is documented here.

## Validation Plan

- `npm run typecheck`
- `npm run build:api`
- `npm run build`
- i18n JSON parse
- `git diff --check`
- Marker scan for known English leakage and sensitive markers
- Read-only browser smoke for Dashboard, Upload, Logs, Settings

## Caveats

- English locale intentionally still contains English strings.
- Some backend diagnostic fallback strings remain in source so unknown errors are not hidden.
- Existing UI may still display operational source locator columns in Upload table; this cleanup does not change source locator display policy.
- Product/runtime terms such as Supabase, Grafana, Docker, WSL, API, DB, Edge, and event codes remain untranslated by design.

## Gap Analysis

Match Rate: 96%

Implemented:

- Upload Preview known reason codes use i18n-first display.
- Dashboard status matrix, safety banner, top bar, warning queue, recent jobs, and audit summary now localize known backend text classes.
- Runtime panel localizes known runtime reason/status classes.
- Upload and Logs job event views localize known event message patterns.
- Audit log error messages localize known backend diagnostics such as Preview timeout, source missing, and local token required.
- Settings state-context and Korean env override wording are localized.

Remaining gaps:

- Unknown backend diagnostics intentionally remain visible as fallback.
- Raw source locator display policy is not changed by this i18n cleanup.
- Product/runtime identifiers and event codes remain untranslated for operator troubleshooting.

## Next Action

Review the draft PR. If approved, merge the i18n display cleanup, then use read-only smoke to confirm the operator UI remains localized in API mode.
