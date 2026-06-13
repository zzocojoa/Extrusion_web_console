# Operator Edge Runtime Restart Mount Hardening Plan

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-edge-runtime-restart-mount-hardening-plan`

Scope: docs-only hardening plan for Edge runtime restart stability and function
mount reproducibility

Verdict: `plan_ready_no_runtime_action`

Match Rate: `100%`

## Summary

Stage 4 upload and the later new-file retry upload are complete. No additional
upload is currently needed.

The next operational risk is not row ingestion. The risk is whether the local
Edge runtime keeps the recovered function mount state after a normal restart.

This plan defines the gates for a future approved restart/mount recheck. It
does not execute Upload Preview, Start Upload, Retry Failed, duplicate rerun,
authenticated Edge calls, full rollout, DB reset, Supabase reset, Docker volume
delete/prune, or operational source mutation.

## Non-Developer Explanation

The upload path now works because the Edge runtime was rebound to the current
function source and the upload function entrypoint was present.

The remaining question is simple: if the machine or local runtime restarts, will
it still look at the correct function files?

If it looks at an old temporary mount again, the operator could see another
Edge `503` failure even though the source data and DB are fine. The fix is not
to upload again. The fix is to verify the runtime wiring before allowing any
future upload or retry.

## Accepted Evidence Baseline

| Evidence | Accepted Result |
| --- | --- |
| Stage 4 final acceptance | completed |
| New-file retry upload | completed |
| Retry job final status | `succeeded` |
| Processed/uploaded/accepted rows | `15096 / 15096 / 15096` |
| DB row-count delta for retry | `15096` |
| Edge runtime function source class before retry | `current_repo_source` |
| Upload function entrypoint before retry | `present` |
| Edge no-auth `GET` before retry | `401_auth_class` |
| Edge no-auth `POST {}` before retry | `401_auth_class` |
| Additional upload currently needed | no |

The accepted evidence proves that the rebind state was healthy at the time of
the successful retry. It does not prove that the same mount state survives a
future restart.

## Match Rate Basis

| Required Plan Item | Covered |
| --- | --- |
| Define restart stability risk | yes |
| Define current function source class gate | yes |
| Define upload entrypoint presence gate | yes |
| Define no-auth Edge `401_auth_class` gate | yes |
| Define DB/volume/protected container preservation criteria | yes |
| Define stop conditions | yes |
| Define rollback/fallback direction | yes |
| Connect gate to future upload/retry approval | yes |
| Document forbidden operations not performed | yes |
| Keep protected untracked artifacts out of scope | yes |

Match Rate calculation: `10 / 10 = 100%`.

## Risk To Harden

The historical blocker was `edge_503` on the authenticated upload path. The
strongest evidence pointed to a stale temporary function mount and missing
runtime entrypoint, not bad source data, DB reconciliation, or upload target
count logic.

After Edge runtime rebind, the runtime saw the current repository function
source class, the upload function entrypoint was present, and the later retry
upload succeeded.

The remaining risk is restart reproducibility:

- an existing container restart may preserve a stale bind mount;
- a newly created runtime may bind the wrong source class if launched from the
  wrong working context;
- a no-auth `401_auth_class` only proves the auth boundary is reachable, not
  that the authenticated worker can boot;
- the upload function entrypoint must be verified inside the active runtime
  mount before a new upload/retry is approved.

## Future Restart/Mount Recheck Gates

Run these gates only after separate explicit approval for a restart/mount
recheck. Do not run upload actions during this recheck.

| Gate | Expected Result | Failure Meaning |
| --- | --- | --- |
| Active Edge container | `running` | Edge runtime unavailable |
| Function mount source class | `current_repo_source` | Runtime may be bound to stale or temporary source |
| Upload function entrypoint | `present` | Authenticated worker may fail to boot |
| Edge no-auth `GET` | `401_auth_class` | Gateway/auth boundary not healthy |
| Edge no-auth `POST {}` | `401_auth_class` | Gateway/auth boundary not healthy |
| Protected DB/data containers | unchanged identity class | Non-Edge runtime drift or data safety risk |
| DB volumes | unchanged identity class | Data preservation risk |
| Protected non-Edge services | running or known prior caveat class | Recovery affected more than Edge runtime |
| Backend target classes, if checked | passed | Backend/runtime target drift |

The entrypoint check must inspect the active runtime mount destination actually
used by the container. Do not rely on a single hardcoded container path.

## Protected State Criteria

Before any approved restart/mount recheck, capture sanitized identity classes
for protected runtime components.

Protected components:

- DB container identity class;
- gateway container identity class;
- REST container identity class;
- Studio container identity class;
- DB data/config volume identity class;
- active Edge container identity class.

After the recheck, DB/data containers and DB volumes must be unchanged. The Edge
container may change only if the approved recheck explicitly includes Edge-only
replacement/rebind. No DB volume deletion or prune is allowed.

## Stop Conditions

Stop the recheck and do not approve upload/retry if any of these are observed:

- function mount source class is stale, temporary, missing, or unknown;
- upload function entrypoint is missing;
- Edge no-auth `GET` or `POST {}` returns `503`;
- Edge no-auth probe does not reach `401_auth_class`;
- DB volume identity changes;
- protected DB/data container identity changes without explicit approval;
- backend target classes drift away from the expected independent target class;
- raw secret, credential-bearing header, signed token, DB locator, operational
  source locator, source filename, or source content appears in logs or docs;
- any Upload Preview, Start Upload, Retry Failed, duplicate rerun,
  authenticated Edge call, or full rollout is attempted during the recheck.

## Rollback And Fallback

If the restart/mount recheck fails, do not retry upload.

Fallback path:

1. keep upload/retry blocked;
2. preserve failed runtime evidence using sanitized classes only;
3. return to the approved Edge rebind/replacement plan pattern;
4. verify protected DB/data containers and DB volumes remain unchanged;
5. require a new explicit approval before any Edge runtime replacement/rebind;
6. after recovery, re-run the mount and no-auth gates before any upload action.

Rollback should restore runtime reachability only. It must not imply upload
readiness. Upload readiness still requires fresh source, Preview, target count,
runtime, and approval gates.

## Future Upload/Retry Gate Integration

Before any future Upload Preview, Start Upload, Retry Failed, duplicate rerun,
authenticated Edge call, or full rollout, the operator should treat this
restart/mount recheck as a prerequisite when the runtime has been restarted or
rebuilt since the last successful upload.

Minimum pre-upload chain:

1. Edge restart/mount recheck passes;
2. active backend/runtime target classes pass;
3. source eligibility and binding pass;
4. Preview-only gate runs only with separate approval;
5. target counts are reviewed;
6. upload or retry runs only with separate explicit approval.

## Explicitly Forbidden In This Task

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Docker volume delete or prune;
- Supabase reset;
- operational source mutation, deletion, or rename;
- protected untracked artifact commit or deletion.

## Redaction Result

This document records only sanitized runtime classes, repo-relative document
references, and aggregate operational decisions.

- no raw operational source locator;
- no raw operational source filename;
- no operational source row content;
- no full local operational source path;
- no raw DB URL;
- no token, credential-bearing header value, JWT, or secret;
- no raw Edge authenticated request payload;
- no destructive command output.

## Validation

| Check | Result |
| --- | --- |
| `git diff --check` | passed |
| New document marker scan | passed |
| PR file scope | docs/128 only |
| Protected untracked artifacts remain uncommitted | passed |

## Next QA

After this document is reviewed and merged, the next QA should be
restart/mount recheck only, on a separate branch and with separate explicit
approval.

That QA may verify Edge runtime restart stability and function mount
reproducibility. It must not run Upload Preview, Start Upload, Retry Failed,
duplicate rerun, authenticated Edge upload call, or full rollout.

## Next Safe Action

Open this docs-only hardening plan PR for review.
