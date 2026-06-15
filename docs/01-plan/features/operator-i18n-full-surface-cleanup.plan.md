# operator-i18n-full-surface-cleanup - Plan Document

> Version: 1.0.0 | Date: 2026-06-16 | Status: Draft
> Level: Dynamic

---

## 1. Overview

### 1.1 Purpose
Audit operator-facing UI strings that still render backend-generated English or development copy in Korean mode, then route known messages through frontend i18n without changing upload execution behavior.

### 1.2 Background
The Upload Preview table was fixed to prefer `reasonCode` i18n, but Dashboard, runtime status, Settings state context, and job logs still render some backend `label`, `detail`, `summary`, or `message` strings directly. Operators need Korean UI copy for operational decisions, while backend diagnostic English can remain available as an API/debug fallback.

## 2. Goals

### 2.1 Primary Goals
- [x] Keep Upload Preview known reason codes localized in Korean mode.
- [ ] Localize known Dashboard status, runtime, state-context, warning, and job-count messages.
- [ ] Localize known job event messages shown in Upload/Logs surfaces.
- [ ] Preserve neutral fallback behavior for unknown diagnostics without exposing secrets.

### 2.2 Non-Goals
- No Upload Preview, Start Upload, Retry Failed, duplicate rerun, Edge authenticated call, or rollout execution.
- No backend API schema change.
- No DB/Supabase/Docker lifecycle or destructive operation.
- No redesign of Dashboard, Upload, Logs, or Settings UI.

## 3. Scope

### 3.1 In Scope
- Frontend display helpers for known backend Dashboard/runtime/job-event text patterns.
- Locale keys for Korean and English.
- Settings state-context label display.
- Documentation of audit scope, caveats, and validation.

### 3.2 Out of Scope
- Upload execution behavior, backend guards, Retry Failed behavior.
- Raw operational source path/filename display policy, except avoiding new leakage in docs/output.
- Production deploy or GitHub Release/tag work.

## 4. Success Criteria

- [ ] Korean mode no longer shows known backend English reasons such as `File date is outside the preview range.` in operator-facing Preview reason cells.
- [ ] Dashboard no longer shows known backend English labels/details such as `Latest Upload`, `Latest upload succeeded`, or `Status ... processed ... rows.` in Korean mode.
- [ ] Logs/Upload job events localize known event message patterns.
- [ ] Unknown diagnostics remain visible only as sanitized fallback.
- [ ] Typecheck/build/diff check pass.
- [ ] Marker scan is clean for raw source content, DB URL, token, Authorization, JWT, and secret exposure.

## 5. Schedule

| Phase | Target Date | Status |
|-------|------------|--------|
| Plan | 2026-06-16 | In Progress |
| Design | 2026-06-16 | Pending |
| Implementation | 2026-06-16 | Pending |
| Review | 2026-06-16 | Pending |

## 6. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Over-localizing identifiers such as job IDs or event codes | Medium | Medium | Localize only human-readable labels/messages; keep IDs/codes visible. |
| Hiding useful diagnostic fallback | Medium | Low | Use i18n first for known patterns and retain sanitized fallback for unknown diagnostics. |
| Accidentally touching upload mutation paths | High | Low | Restrict changes to display helpers, locale files, docs, and read-only smoke. |

## 7. References

- `AGENTS.md`
- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/06_dashboard_implementation_spec.md`
- `docs/01-plan/features/operator-i18n-string-audit.plan.md`
- `docs/03-analysis/operator-i18n-string-audit.analysis.md`
