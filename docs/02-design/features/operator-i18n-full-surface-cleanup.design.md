# operator-i18n-full-surface-cleanup - Design Document

> Version: 1.0.0 | Date: 2026-06-16 | Status: Draft
> Level: Dynamic

---

## 1. Design Summary

Operator-facing UI should prefer frontend i18n keys for known backend reason/status/message codes. Backend diagnostic English remains part of API payloads, but React components should translate known operational messages before rendering them in Korean mode.

## 2. Affected Surfaces

| Surface | Source text class | Display policy |
|---------|-------------------|----------------|
| Upload Preview table | `reasonCode`, `reasonText` | Use `upload.reason.<reasonCode>` first; sanitized `reasonText` only for unknown reasons. |
| Dashboard status matrix | backend `label`, `value`, `detail` | Map known item ids and known detail patterns to i18n keys. |
| Dashboard safety banner | backend `title`, `message` | Map known titles/messages to i18n keys; fallback to backend text. |
| Runtime panel | runtime statuses and `reasonText` | Translate status values and known reason codes; keep host/port identifiers as diagnostics. |
| Warning queue | backend `id`, `label`, `impact` | Map known row ids to i18n keys. |
| Recent jobs/current job | backend job-count message | Translate known count-message pattern. |
| Job event logs | backend `eventType`, `message` | Translate known event-type/message patterns; preserve event code and identifiers. |
| Settings | state context label/source labels | Map known context classes and source labels to i18n keys. |

## 3. API Contract

No backend API schema changes are required.

- Existing diagnostic fields remain available.
- Frontend components add display-only formatting helpers.
- Unknown text falls back to existing API payloads after local sanitization where applicable.

## 4. Security Design

- Do not introduce new display of raw source paths, filenames, DB URLs, tokens, Authorization headers, JWTs, or secrets.
- Do not document raw operational source values.
- Do not transform IDs or event codes that operators use for troubleshooting.
- Preserve existing secret placeholders in Settings.

## 5. Validation Design

- Static source scan for known English leakage patterns.
- i18n JSON parse check.
- `npm run typecheck`, `npm run build:api`, `npm run build`.
- Read-only browser smoke for Dashboard, Upload, Logs, Settings.
- No upload or runtime mutation actions during validation.
