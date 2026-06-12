# Operator Stage 3 Bounded Start Upload Investigation

## Scope

- Investigation target: Stage 3 Profile A bounded Start Upload failure from PR #105.
- Source QA commit under investigation: `62e4c755061ed5036abd0a080394b368dbbdbf28`.
- Investigation branch: `codex/operator-stage-3-bounded-start-upload-investigation`.
- Investigation mode: read-only runtime/config/log inspection plus targeted tests.
- Start Upload executions during this investigation: `0`.
- Retry Failed executions during this investigation: `0`.
- Duplicate rerun executions during this investigation: `0`.
- Edge authenticated upload calls during this investigation: `0`.
- Full operational dataset rollout during this investigation: not performed.

## Start Upload Failure Summary

The Stage 3 Profile A Start Upload was executed exactly once in PR #105 and ended as `failed`.

Observed final job outcome:

| Field | Value |
| --- | ---: |
| Job final status | `failed` |
| Processed rows | `0` |
| Uploaded rows | `0` |
| Accepted rows | `0` |
| DB row-count delta | `0` |
| Start Upload executions | `1` |
| Retry Failed executions | `0` |
| Duplicate rerun executions | `0` |
| Full rollout | not performed |

The failure class is `connection_refused_before_upload_progress`. The upload job failed before any row processing or accepted-row mutation, so the no-mutation evidence remains intact.

## Root Cause Verdict

Root cause found: `qa_backend_stale_process_port_reuse`.

The most likely sequence is:

1. The first QA backend process served the QA API port with stale fallback configuration loaded from local config files.
2. The later attempt to restart the backend with corrected independent target overrides stopped the wrapper process but left the child `uvicorn` process serving the QA port.
3. The intended replacement backend failed to bind because the QA API port was already in use.
4. Subsequent API health/config/upload calls still reached the old backend process.
5. Start Upload therefore used the old backend process's upload execution target class and failed with connection refused before processing rows.

This explains why direct independent probes and readiness checks could look valid while the actual Start Upload execution still failed against a stale target class.

## Preview vs Start Upload Target Class Comparison

| Path | Evidence | Target class conclusion |
| --- | --- | --- |
| Preview path from the prior bounded QA | `dbStatus=reachable`, corrected bounded source, DB delta `0` | Independent DB target class was reachable for preview/reconciliation. |
| Direct DB probe during investigation | Read-only count returned successfully | Independent DB target class reachable. |
| Direct Edge no-auth probe during investigation | GET and POST `{}` returned auth-class responses without Authorization | Independent Edge runtime reachable and auth-protected. |
| Clean backend control run during investigation | API, DB, Studio, and Edge readiness all returned ready on an alternate QA API port | Backend can align to the independent target class when launched cleanly with explicit overrides. |
| Actual Start Upload job from PR #105 | Job failed before upload progress with connection refused class | Actual upload execution reached a stale/unreachable target class. |

The Preview and Start Upload source scope appear to reference the same corrected bounded source class. The observed mismatch is in backend process/config state, not in the source selection itself.

## Backend Config Class

The backend has three relevant target paths:

- Preview DB reconciliation uses the configured DB URL class.
- Runtime readiness checks use `local_runtime_edge_url`.
- Start Upload execution uses `upload_edge_url`.

Code inspection found an important distinction:

- Runtime readiness derives the local Edge readiness target from `local_runtime_edge_url`.
- Upload execution posts to `upload_edge_url`.
- The upload job config snapshot stores only configured/not-configured booleans for the Edge URL and anon key. It does not persist a sanitized upload target class.

Local config files contain Supabase-related keys with a stale loopback target class. No raw values were documented. Because the API intentionally hides secret config values, `/api/config` alone cannot prove that the hidden upload execution target class matches the runtime readiness class.

## Direct DB and Edge Probe Class

The independent target probes were read-only or unauthenticated:

| Probe | Result |
| --- | --- |
| Read-only DB count | reachable |
| Edge GET without Authorization | auth-class response |
| Edge POST `{}` without Authorization | auth-class response |
| Authorization header used | no |
| Edge authenticated upload call | not performed |

These probes support that the independent DB and Edge services were available. They do not prove that the stale QA backend process used the same target class during the failed Start Upload.

## Upload Execution Target Class

Start Upload execution follows this path:

1. `POST /api/upload/jobs`
2. `create_upload_job`
3. `UploadJobService`
4. `EdgeUploader`
5. HTTP POST to the configured upload Edge URL with the upload payload

The observed failure occurred before row processing. That matches an upload execution target that was unavailable at connection time, not a transform/data acceptance failure.

The clean-control backend run showed that upload/runtime target alignment is possible when the backend is launched without stale process reuse. Therefore the current evidence points to runtime launch/process state, not a confirmed product upload algorithm defect.

## Failure Class

Classification: `stale_backend_process_with_connection_refused_upload_target`.

Supported evidence:

- Backend log inspection found an address-in-use bind failure on the QA API port during the attempted restart.
- The failed replacement backend could not own the QA API port.
- Health/API calls could still succeed because an older backend process was already serving that port.
- The Start Upload job failed before processed/uploaded/accepted row counters advanced.
- The DB row-count delta remained `0`.
- A clean backend launched on an alternate QA API port with explicit independent overrides reported API, DB, Studio, and Edge readiness.

## Root Cause Candidates

| Candidate | Status | Rationale |
| --- | --- | --- |
| Stale QA backend process served the API port | confirmed | Address-in-use evidence and stale child-process behavior explain the mismatch. |
| Independent DB unavailable | disproven | Read-only DB probe succeeded. |
| Independent Edge runtime unavailable | disproven | No-auth Edge GET/POST returned auth-class responses. |
| Corrected bounded source mismatch | not supported | Source class evidence remained corrected/bounded; failure happened before row processing. |
| Product upload transform failure | not supported | No rows were processed before failure. |
| Launcher production defect | not proven | The launcher starts the Python process directly; the observed issue came from the QA wrapper process pattern. |
| Observability gap in upload target evidence | supported | Job config snapshot lacks a sanitized upload execution target class. |

## No-Retry Rationale

Start Upload must not be retried yet.

The failed job showed no DB mutation, but the investigation found that API readiness can be misleading when the QA port is owned by a stale backend process. Retrying without first fixing the process/config verification path could repeat the same failure or, worse, send upload traffic to a target class that was not the one validated by Preview.

Safe preconditions before any future Start Upload attempt:

1. Confirm no stale backend process owns the QA API port.
2. Launch the backend in a way that makes the intended independent target class effective.
3. Fail the procedure immediately on any address-in-use backend log.
4. Prove runtime readiness and upload execution target class alignment without exposing secrets.
5. Re-run Preview-only in a separate approved QA step if the source or runtime state changed.

## Next Safe Action

Recommended next action: separate recovery/fix work before any Start Upload retry.

Minimum safe follow-up:

- Add or document a preflight that proves the backend-owned upload execution target class using sanitized class labels only.
- Update the QA procedure to stop the actual backend child process before restart, not only the wrapper process.
- Treat backend bind failure as a hard stop.
- Keep Start Upload, Retry Failed, duplicate rerun, and full rollout blocked until that recovery path is reviewed.

If this becomes a code change, it should be a separate fix PR. A reasonable source-level improvement would be to expose a sanitized upload target class in a non-secret diagnostic response or the upload job config snapshot, without returning raw URLs or credentials.

## Redaction Result

No raw secrets, DB URLs, tokens, Authorization headers, JWTs, operational source paths, operational source filenames, raw CSV content, or full local paths are included in this report.

## Validation

Completed:

- Targeted backend package/runtime/upload preview/upload job tests: passed, `161 passed`.
- `npm run typecheck`: passed.
- `npm run build:api`: passed.
- `npm run build`: passed.
- `git diff --check`: passed.
- New document marker scan: passed.

Notes:

- Pytest emitted existing deprecation/cache warnings, with no test failures.
- Frontend build output was generated locally but is not part of the intended commit scope.
- PR file-scope check is required after push/PR creation.
