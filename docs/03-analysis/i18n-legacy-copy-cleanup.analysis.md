# I18n Legacy Copy Cleanup Analysis

## Match Rate

`98%`

## Summary

Repeated i18n JSON edits did not remove the stale operator-facing text because
some visible strings were not coming from i18n files. They were embedded in
development-only frontend fixtures and imported into pages at module load time.

The cleanup keeps API-mode behavior unchanged, preserves frontend development
scenarios, and removes confusing development fixture markers from source and
API-mode build output.

## Non-Developer Explanation

The app had two kinds of text:

- normal translated UI text;
- development scenario text used for screenshots and local testing.

Changing only the translation files fixed the first kind. It did not fix the
second kind because those labels lived directly inside development data files.
The app was carrying those strings in the built frontend bundle, even when the
operator was using API mode.

The fix separates the API-mode bundle from those development fixtures and
renames the remaining development-only labels so they no longer look like real
operator jobs or real source locations.

## Root Cause

Root cause classification: `static_development_fixture_leakage`.

Evidence:

- Dashboard development data had a fake running job id and fake progress counts
  that could be mistaken for a real operator job.
- Upload development preview/job data had file and source labels that looked
  too close to operational CSV evidence.
- Settings development data used URI-like placeholder values that looked like
  active source binding.
- API-mode build used static imports for some development fixture modules, so
  the safest fix was to move those imports behind API-mode conditionals and
  verify the built assets.

## Changes

- Dashboard query now loads development dashboard data only when frontend mock
  mode is active.
- Upload page now loads development preview/job fixtures only when frontend
  mock mode is active.
- Development Dashboard job ids and progress copy now use neutral development
  labels.
- Development Upload fixture filenames and source labels now use neutral
  training labels instead of operational-looking names.
- Development Settings fallback values now use neutral labels instead of
  URI-like mock placeholders.
- Development-only Settings and Logs text now uses development wording rather
  than the older mock wording.

## Safety Boundary

No upload execution behavior changed.

Not performed:

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB, Supabase, or Docker lifecycle/destructive operation;
- operational CSV mutation.

## Validation

- `npm run typecheck`: passed.
- i18n JSON parse: passed.
- `npm run build`: passed.
- `npm run build:api`: passed and left `frontend/dist` in API mode.
- Source marker scan: no old operational-looking development markers in
  frontend source.
- API-mode dist marker scan: no old operational-looking development markers in
  built assets.
- Backend-served JS marker scan: no old operational-looking development markers
  in the served API-mode asset.
- Browser smoke at the backend-served app:
  - Dashboard loaded;
  - Upload loaded;
  - Logs loaded;
  - Settings loaded;
  - marker findings: `0`;
  - console errors: `0`;
  - failed browser requests: `0`.

## Caveats

Settings intentionally shows read-only configuration fields in the application
itself. This report does not record raw setting values, source paths, DB URLs,
tokens, Authorization headers, JWTs, or secrets.

The development fixture modules still exist for local screenshot and demo
states. They now use neutral development/training labels. The old confusing
markers are absent from the API-mode build output and the modules are only
loaded by frontend mock-mode branches.

## Next Action

Review and merge this cleanup PR. After merge, rebuild or refresh the operator
frontend package in API mode before asking an operator to re-check the screen.
