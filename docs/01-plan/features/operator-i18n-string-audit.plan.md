# Operator I18n String Audit Plan

## Business Goal

한국어 운영자 UI에서 backend diagnostic English가 그대로 노출되지 않게 한다. 대표 사례는 Upload Preview table의 known reason code가 `File date is outside the preview range.` 같은 backend `reasonText` fallback으로 표시되는 문제다.

비개발자 설명: 화면은 한국어로 쓰고, backend가 보관하는 진단 문구는 내부 기록으로만 둔다. 미리보기 사유는 코드값을 기준으로 한국어 문구를 먼저 보여주고, 알 수 없는 사유만 제한적으로 진단 문구를 표시한다.

## Scope

- Upload Preview item reason display.
- Upload Preview run status banner error display.
- Korean and English i18n keys for known backend Preview reason codes.
- PDCA analysis report for the string audit and validation evidence.

## Out Of Scope

- Upload Preview execution.
- Start Upload, Retry Failed, duplicate rerun, authenticated Edge call, full rollout.
- DB, Supabase, Docker lifecycle or destructive operations.
- Backend API contract changes.
- Upload execution behavior changes.

## Investigation Targets

- `File date is outside the preview range.`
- `No matching rows were found in DB.`
- `All local keys already exist in DB.`
- `Some local keys already exist in DB.`
- `CSV schema is incomplete.`
- `Preview run exceeded the configured time limit.`
- `No valid timestamp/device_id keys were found.`
- Related `reasonCode` and `reasonText` rendering paths.

## Implementation Plan

1. Keep backend diagnostic `reasonText` unchanged.
2. In operator-facing Upload UI, prefer `upload.reason.<reasonCode>` when the key exists.
3. Add missing known reason keys for source, date, lock, timeout, cancel, DB, schema, and transform cases.
4. Allow backend fallback only for unknown reason codes and suppress fallback text when it resembles a path, URL, token, Authorization, JWT, or secret.
5. Validate mock and API mode builds without running Preview or Upload actions.

## Acceptance Criteria

- Known Preview reason codes render through i18n, not backend English fallback.
- Korean UI no longer shows `File date is outside the preview range.` for known `outside_date_range`.
- Unknown fallback remains available but is sanitized.
- No raw source path, source content, DB URL, token, Authorization header, JWT, or secret is introduced.
- PR contains only intended frontend and PDCA documentation files.

## Match Rate Target

- Target: `95%+`
- Risk: medium, because this affects operator-facing upload safety wording but does not mutate data or change upload behavior.
