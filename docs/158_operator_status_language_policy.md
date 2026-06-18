# Operator Status Language Policy

Date: 2026-06-19 Asia/Seoul

Status: `active_language_policy`

## Purpose

This document defines how project status, infographics, release notes, handoff
notes, and non-developer summaries must describe remaining work, approval
boundaries, and caveats.

The goal is to prevent a non-developer from reading a safety restriction as an
unfinished task.

## Core Rule

Do not group all non-completed-looking items under `미완료`, `미작업`, or
`미승인`.

Those words imply one of these meanings:

- someone has not done required work yet;
- the project is incomplete;
- the next correct action is to complete or approve the item.

Most remaining items in this project are not unfinished development work. They
are operating controls, explicit approval boundaries, intentionally deferred
scope, or conditional monitoring caveats.

## Required Categories

Use these categories for future status reports and infographics.

| Category | Korean label | Meaning | Example |
| --- | --- | --- | --- |
| Completed evidence | `완료 / 승인 / 증거` | Implemented, validated, accepted, or executed with evidence. | Core Ops UI/API, approved Start Upload, recorded delete execution. |
| Operating restriction | `운영 제한 / 별도 승인 필요` | Must not be run automatically; requires fresh evidence and explicit approval. | Additional Preview, Start Upload, Retry Failed, hard delete, full rollout. |
| Intentional out of scope | `의도적 제외 / v1 범위 아님` | Not planned for v1 unless separately re-scoped. | Data Mgmt, Cycle Ops, Training Dataset Builder, Cloud/LAN, Grafana iframe. |
| Conditional caveat | `조건부 주의` | Not blocking now, but becomes a blocker if it affects Core Ops evidence or safety. | Grafana/Vector caveat, independent DB delta not measured. |
| Review gate | `검토 대기 / PR 게이트` | Work exists but must not be treated as broadly available until review gates pass. | PR #182 Draft, fixture-only destructive smoke, date-scoped delete maintainer-only path. |
| Forbidden without approval | `별도 승인 전 금지` | Action must not be performed without a separate approved plan. | DB reset, truncate, Docker/Supabase destructive cleanup, legacy project deletion. |

## Disallowed Heading Patterns

Avoid these as section headings for current project status:

- `미완료`
- `미작업`
- `미승인`
- `미완료 / 미승인`
- `미작업 / 미승인 / Caveat`

These may appear only inside a precise sentence that explains the category, for
example:

```text
추가 Start Upload는 현재 필요한 미완료 작업이 아니라, fresh Preview와 별도 승인 없이는 금지되는 운영 제한 항목이다.
```

## Required Framing

For non-developer summaries, use this framing:

```text
현재 남은 항목은 완료되지 않은 개발 작업 목록이 아니다. 대부분은 완료된 시스템에서
함부로 실행하면 안 되는 운영 제한, 별도 승인 항목, 의도적 v1 제외 범위, 또는 조건부
주의 항목이다.
```

For infographics, use these panel headings:

```text
완료 / 승인 / 증거
운영 제한 / 별도 승인 필요
검토 대기 / 조건부 주의
의도적 제외 / v1 범위 아님
```

If only three columns are available, use:

```text
개발 구성
완료 / 승인 / 증거
제한 / 검토 대기 / 조건부 주의
```

## Current Project Classification

### Completed / Evidence

- Core Ops UI/API.
- Dashboard real-state and state context.
- Upload Preview DB reconciliation and audit.
- Start Upload, Retry Failed, SSE, typed count contracts.
- Settings save and secret redaction.
- Local Supabase status/start/stop.
- Audit Logs append-only query and redaction.
- Launcher local token and API docs hardening.
- API-mode package/runtime state context.
- Legacy GUI hard retirement from normal operator path, with rollback knowledge retained.
- Approved Start Upload evidence for `369383` rows.
- Already-in-DB hard delete contract and selected execution evidence, only within its recorded scope.

### Operating Restrictions / Separate Approval Required

- Any future Upload Preview, Start Upload, Retry Failed, or hard delete.
- Full rollout.
- Release, tag, package zip, and checksum creation.
- Settings save when tied to operational changes.
- DB, Supabase, Docker, or source mutation.

### Review Gates / Conditional Caveats

- PR #182 delete work must stay gated until its merge-readiness checklist is satisfied.
- Destructive smoke must use a disposable fixture DB unless separately approved.
- Date-scoped delete is maintainer-only until frontend controls, copy, i18n, and runbook approval are separately completed.
- Grafana/Vector remain non-core caveats unless they affect Core Ops evidence.
- Independent DB before/after delta and row-level attribution items are audit-strengthening investigations, not current feature blockers unless a specific incident or audit requirement makes them mandatory.

### Intentional Out Of Scope

- Data Mgmt archive/delete flows.
- Supabase Management delete UI.
- Cycle Ops.
- Training Dataset Builder.
- Cloud Supabase migration.
- Multi-user LAN web access.
- Grafana iframe embedding.
- Default legacy upload state import.

## Governance

When producing any future project status artifact:

1. Read this document before choosing status labels.
2. Classify each item into one of the required categories.
3. Do not imply that an item should be executed just because it is not in the
   completed column.
4. For destructive or mutating actions, state the approval boundary before the
   action name.
5. Keep raw paths, filenames, DB URLs, credentials, tokens, Authorization values,
   JWTs, exact keys, and source row contents out of status artifacts.