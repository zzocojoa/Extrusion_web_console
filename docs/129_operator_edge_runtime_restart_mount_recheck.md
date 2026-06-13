# Operator Edge Runtime Restart Mount Recheck

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-edge-runtime-restart-mount-recheck`

Scope: restart/mount recheck-only QA for Edge runtime function mount
reproducibility

Verdict: `passed_restart_mount_recheck`

Match Rate: `100%`

## Summary

The Edge runtime restart/mount recheck passed.

An Edge-only container restart was performed to verify the restart stability
risk described in `docs/128_operator_edge_runtime_restart_mount_hardening_plan.md`.
After restart, the active Edge runtime was still running, the upload function
mount source class still included `current_repo_source`, the active runtime
mount destination exposed the `upload-metrics` entrypoint, and no-auth Edge
`GET` and `POST {}` probes both returned `401_auth_class`.

No Upload Preview, Start Upload, Retry Failed, duplicate rerun, authenticated
Edge upload call, full rollout, DB reset, DB destructive operation, Docker
volume delete/prune, Supabase reset, or operational source mutation was
performed.

## Non-Developer Explanation

The previous upload problem happened because the local Edge runtime looked at
the wrong copy of the upload function files. Upload data and database matching
were not the real problem.

This QA restarted only the Edge runtime container and checked whether it still
looked at the correct function files afterward. It did.

What improved: future operators now have evidence that the active Edge runtime
can survive an Edge-only restart while still seeing the current upload function
entrypoint.

What still needs care: this does not approve another upload. Future uploads
still need a fresh Preview-only gate, reviewed target counts, and separate
explicit approval.

## Baseline

| Item | Result |
| --- | --- |
| Base document | `docs/128_operator_edge_runtime_restart_mount_hardening_plan.md` |
| Local main before branch | matched `origin/main` |
| QA type | restart/mount recheck only |
| Upload goal status | already complete |
| Additional upload needed now | no |

Protected untracked local artifacts were left uncommitted and undeleted.

## Action Performed

| Action | Result |
| --- | --- |
| Edge-only container restart | performed |
| Edge container identity after restart | preserved |
| Protected non-Edge container identities after restart | preserved |
| Destructive operation | not performed |

This was not a Supabase reset, not a DB reset, not a Docker prune, and not a
volume operation. It was limited to the active Edge runtime container.

## Gate Results

| Gate | Expected | Result |
| --- | --- | --- |
| Active Edge container status | `running` | `running` |
| Active Edge container health | non-blocking if not reported | `not_reported` |
| Function mount source class | includes `current_repo_source` | passed |
| Current repository function mount count | `>= 1` | `1` |
| Upload function entrypoint at active mount destination | `present` | `present` |
| Edge no-auth `GET` | `401_auth_class` | `401_auth_class` |
| Edge no-auth `POST {}` | `401_auth_class` | `401_auth_class` |
| Protected DB container identity | preserved | preserved |
| Protected gateway container identity | preserved | preserved |
| Protected REST container identity | preserved | preserved |
| Protected Studio container identity | preserved | preserved |
| DB data/config volume identity class | preserved | preserved |
| Backend `/api/config` target-class evidence | passed if available | passed |
| Runtime API | `ready` | `ready` |
| Runtime DB | `ready` | `ready` |
| Runtime Studio | `ready` | `ready` |
| Runtime Edge | `ready` | `ready` |
| Runtime Docker | `ready` | `ready` |

Runtime overall remained `attention` because of the already-known
`non_core_runtime_attention` class. The required API, DB, Studio, Edge, Docker,
mount, entrypoint, and no-auth Edge gates passed.

## Mount Class Caveat

The active Edge container still has multiple mount source classes, including
non-function helper/cache classes.

The relevant upload function mount is the one classified as
`current_repo_source`. That mount was present after restart, and the
`upload-metrics` entrypoint was present at the active runtime mount destination.

Because the function mount itself is `current_repo_source`, the historical
stale/temp function mount stop condition was not observed.

## Stop Conditions

| Stop Condition | Observed |
| --- | --- |
| Function mount source class stale/temp for upload function | no |
| Upload function entrypoint missing | no |
| Edge no-auth `503` | no |
| DB volume identity drift | no |
| Protected DB/data container drift | no |
| Backend target class drift | no |
| Secret/path marker exposure | no |
| Upload Preview attempted | no |
| Start Upload attempted | no |
| Retry Failed attempted | no |
| duplicate rerun attempted | no |
| authenticated Edge upload call attempted | no |
| full rollout attempted | no |

No stop condition was hit.

## Match Rate Basis

| Required Gate | Evidence |
| --- | --- |
| Active Edge container status | passed |
| Function mount source class is `current_repo_source` | passed |
| Upload function entrypoint present | passed |
| Edge no-auth `GET` returns `401_auth_class` | passed |
| Edge no-auth `POST {}` returns `401_auth_class` | passed |
| DB/protected container identities preserved | passed |
| DB volume identity class preserved | passed |
| Backend target classes checked if available | passed |
| Raw secret/source/DB marker scan clean | passed |
| Forbidden upload/runtime-destructive actions avoided | passed |

Match Rate calculation: `10 / 10 = 100%`.

## Decision

The restart/mount recheck is sufficient to remove the immediate uncertainty
documented in `docs/128`: the active Edge runtime can be restarted in an
Edge-only way and still see the current repository upload function entrypoint.

This does not authorize upload. It only hardens the runtime readiness gate that
must pass before any future Preview, Start Upload, Retry Failed, duplicate
rerun, authenticated Edge upload call, or full rollout is considered.

## Explicitly Not Performed

- Upload Preview;
- Start Upload;
- Retry Failed;
- duplicate rerun;
- authenticated Edge upload call;
- full rollout;
- DB reset, init, delete, truncate, drop, or prune;
- Docker volume delete or prune;
- Docker container delete or prune;
- Supabase reset;
- operational source mutation, deletion, or rename;
- protected untracked artifact commit or deletion.

## Redaction Result

This document records only sanitized runtime classes, repo-relative document
references, and aggregate operational evidence.

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
| PR file scope | docs/129 only |
| Protected untracked artifacts remain uncommitted | passed |

## Next Safe Action

Open this docs-only restart/mount recheck QA PR for review.

Future upload work still starts from a fresh Preview-only gate and separate
explicit approval. This QA does not approve upload/retry.
