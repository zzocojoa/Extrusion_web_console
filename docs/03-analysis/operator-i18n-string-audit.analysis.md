# Operator I18n String Audit Analysis

## Match Rate

`96%`

## Summary

The audit found that the backend already emits stable Preview `reasonCode` values with diagnostic English `reasonText`. The frontend attempted to translate `upload.reason.<reasonCode>`, but used backend `reasonText` as the i18next `defaultValue`. When a known backend reason code was missing from the locale files, the Korean operator UI displayed the English diagnostic text directly.

비개발자 설명: 미리보기 결과에는 "사유 코드"와 "영어 진단 문장"이 같이 들어옵니다. 기존 화면은 한국어 사유가 없으면 영어 진단 문장을 그대로 보여줬습니다. 이제 알려진 사유 코드는 한국어 문구를 먼저 쓰고, 알 수 없는 새 사유만 제한적으로 표시합니다.

## Root Cause

`known_reason_code_missing_i18n_fallback_leakage`

- Backend source: `backend/app/services/upload_preview.py`
- Frontend rendering path: `frontend/src/pages/UploadPage.tsx`
- Existing behavior: `t("upload.reason.<code>", { defaultValue: item.reasonText })`
- Failure mode: missing locale key allowed backend English fallback into Korean UI.

## Confirmed Known Reason Codes

- `db_no_match`
- `db_full_match`
- `db_partial_match`
- `source_not_configured`
- `source_missing`
- `file_missing`
- `file_date_missing`
- `outside_date_range`
- `file_locked`
- `schema_mismatch`
- `file_unstable`
- `db_unreachable`
- `timeout`
- `cancelled`
- `transform_error`
- `no_valid_keys`

## Changes Made

- Upload Preview table now uses i18n-first reason formatting.
- Upload Preview run error banner now uses the same reason-code formatter when `errorCode` is present.
- Backend diagnostic fallback is used only when the reason code is unknown.
- Fallback text is suppressed if it resembles a path, URL, token, Authorization/JWT/secret, or similar sensitive diagnostic.
- Korean and English locale files now cover the known Preview reason code set.

## Safety Review

- Upload Preview was not executed.
- Start Upload was not executed.
- Retry Failed was not executed.
- duplicate rerun was not executed.
- authenticated Edge upload call was not executed.
- full rollout was not executed.
- DB/Supabase/Docker lifecycle or destructive operations were not executed.
- Operational CSV files were not modified.

## Remaining Caveats

- Job and audit logs may intentionally display backend event or error text. Those are diagnostic log surfaces, not the Preview reason table. They should be reviewed separately if the product requires full error-code localization across all logs.
- English strings remain in `en.json` by design.
- The backend `reasonText` contract remains unchanged for API diagnostics and tests.

## Next Safe Action

Review and merge the docs/code PR. After merge, browser smoke can confirm the latest Preview table in Korean without running a new Preview, Start Upload, or Retry.
