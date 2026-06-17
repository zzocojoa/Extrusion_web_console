# Runtime Core Non-Core Readiness Policy Analysis

Date: 2026-06-17 Asia/Seoul

## Summary

Match Rate: `95%`

This change closes the investigated policy gap between Core Ops blockers and
non-core runtime caveats.

Core runtime services are:

- API;
- DB;
- Studio;
- Edge.

Non-core caveat services are:

- Grafana, represented in the runtime API and Dashboard UI;
- Vector, documented as an observability caveat but not yet represented as a
  runtime API/UI row.

## Gap

Before this change, the runtime readiness API could classify Studio or Edge
failure under `non_core_runtime_attention`, the same bucket used for Grafana.
That was too broad. A broken Studio or Edge gate can affect operator evidence
or upload execution readiness, so it must be a Core Ops blocker.

Dashboard summary logic also treated API/DB readiness separately from Edge and
did not include Studio in the Core runtime summary.

## Implemented Alignment

The backend runtime policy now blocks when any of API, DB, Studio, or Edge is
not ready.

Grafana unreachable remains `non_core_runtime_attention` only when all core
runtime services are ready.

Dashboard summary and warning rows now use the same Core runtime definition, so
Edge or Studio failure is visible as a blocker instead of being lowered to
attention.

## Vector Decision

Vector remains a document-only non-core caveat in this PR.

Reason: the current runtime API/schema does not expose a dedicated Vector row,
and Core Ops evidence is already covered by API, DB, Studio, Edge, Dashboard,
Upload, Logs/Audit, token guard, and state context. Adding Vector to the API
would require a schema/UI expansion that is separate from this policy fix.

If Vector instability hides local logs/audit evidence, destabilizes Edge/API, or
prevents runtime evidence collection, it must be promoted to a blocker by the
runbook.

## Validation Plan

- Runtime unit tests must prove API/DB/Studio/Edge failures are blockers.
- Runtime unit tests must prove Grafana-only failure remains non-core
  attention.
- Dashboard tests must prove Core runtime failure appears as a blocked runtime
  gate.
- Dashboard tests must prove Grafana-only failure leaves the Core runtime gate
  ready while Grafana is shown separately.
- Frontend typecheck and builds must pass.
- Read-only runtime API checks must continue to show current Grafana-only
  attention without running Preview, Start Upload, Retry Failed, or any
  destructive runtime action.

## Remaining Caveat

The UI still labels an unreachable Grafana row with the generic blocked status
badge because that badge reflects the service probe state. The operating
distinction is preserved by the Core runtime gate: Core runtime stays ready
while Grafana is shown as a separate service problem.
