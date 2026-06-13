# Operator Stage 4 Source Access Proof

Date: 2026-06-13 Asia/Seoul

Branch: `codex/operator-stage-4-source-access-proof`

Scope: Stage 4 source candidate accessibility investigation and report-only QA

Verdict: `passed_with_caveats`

## Summary

The Stage 4 source candidate is accessible to a Python/backend-style process
when the source path is passed through the backend-style environment/config
path. The earlier Python `exists=false` result was reproduced only when the
path was embedded directly into an ad-hoc Python script.

No Upload Preview, Start Upload, Retry Failed, duplicate rerun, Edge
authenticated upload call, or full rollout was executed.

Root cause hypothesis:

```text
The source itself is reachable from the operator session. The failing Python
checks were caused by path string transfer/encoding differences in ad-hoc
script invocation, plus ambiguity between PowerShell drive visibility and the
path class a backend process actually receives. Backend-style environment
delivery resolves the source correctly.
```

## Sanitized Source Scope

| Item | Result |
| --- | --- |
| Sanitized source label | `stage4-full-candidate-a` |
| Intended source class | `full_operational_dataset_candidate` |
| Raw source locator recorded | no |
| Raw source filename recorded | no |
| Raw source content opened | no |
| File count | `1` |
| CSV count | `1` |
| Filename-date eligible CSV | `1` |
| `file_date_missing` | `0` |
| Pattern class | `integrated_stem_compact_date` |

This report proves accessibility and filename-date eligibility only. It does
not approve or execute Stage 4 Preview-only.

## Accessibility Matrix

| Probe | Path class | Result |
| --- | --- | --- |
| PowerShell provider check | `drive_letter_mapped` | accessible |
| PowerShell aggregate count | `drive_letter_mapped` | `1` CSV, `1` eligible, `0` missing date |
| Win32/.NET directory check | `drive_letter_mapped` | accessible |
| Win32/.NET directory check | `unc` | accessible |
| `cmd` directory check | `drive_letter_mapped` | accessible |
| `cmd` directory check | `unc` | accessible |
| Python direct literal check | `drive_letter_mapped` | inaccessible |
| Python direct literal check | `unc` | inaccessible |
| Python environment check | `drive_letter_mapped` | accessible |
| Python environment check | `unc` | accessible |
| Backend-style API process config | `drive_letter_mapped` | accepted from environment |
| Backend-style API process config | `unc` | accepted from environment |
| Backend-style Python environment count | `unc` | `1` CSV, `1` eligible, `0` missing date |

The direct literal Python check is not a valid backend-access proof for this
source because the same Python runtime succeeds when the path is supplied by
environment variable, which is the relevant backend configuration path.

## Backend Read-Only Smoke

| Item | Result |
| --- | --- |
| Backend process launched | yes, isolated QA port |
| Temporary QA state DB used | yes |
| Endpoint called | `/api/health`, `/api/config` only |
| Upload Preview called | no |
| Start Upload called | no |
| `plcDataDir` source | `env` |
| `plcDataDir` overridden | `true` |
| Source path value present | `true` |
| Recommended path class probe | `unc` |
| Backend-style source exists | `true` |
| Backend-style file count | `1` |
| Backend-style CSV count | `1` |
| Backend-style eligible CSV | `1` |
| Backend-style `file_date_missing` | `0` |

`/api/config` target-class status was not used as a Stage 4 runtime verdict in
this investigation because the smoke process was intentionally isolated for
source-path checking and was not configured to prove DB/Edge rollout readiness.

## Recommended `plcDataDir` Path Class

Recommended path class: `unc_from_environment_or_config`

Rationale:

- It avoids relying on an interactive drive-letter mapping being present in the
  backend process session.
- It was accessible to the same Python runtime when supplied through the
  backend-style environment path.
- It preserves aggregate source eligibility: `1` CSV, `1` eligible,
  `file_date_missing=0`.

Acceptable with caveats:

- `drive_letter_mapped_from_environment` also passed in the current operator
  session, but it is more fragile because it depends on the mapped drive being
  available to the backend process identity and launch context.

Not recommended:

- `python_direct_literal_probe` is not reliable evidence for this path because
  the direct literal form produced false inaccessible results.
- `local_temp_copied_source` should be treated as a separate operator-approved
  source scope, not as the default Stage 4 full candidate.

## Stage 4 Preview-Only Go/No-Go

Preview-only next step: `no_go_until_explicit_approval`

The source access proof passes with caveats, but the next Preview-only run still
requires separate explicit user approval. This document does not grant approval
to run Upload Preview.

Start Upload next step: `forbidden`

Start Upload remains forbidden until a future Stage 4 Preview-only run succeeds,
its counts are reviewed, and the user separately approves exactly one Start
Upload.

## Stop Conditions

| Stop condition | Result |
| --- | --- |
| Python/backend cannot access source path | not observed for environment/config path |
| `source_missing` likely for recommended path class | no |
| CSV count is `0` | no |
| `file_date_missing > 0` | no |
| Source scope unclear | partially, full-dataset approval still separate |
| User has not approved Preview-only rerun | yes |

For this source-access proof only, source accessibility is no longer the active
blocker for the recommended sanitized path class. Stage 4 Preview-only remains
blocked until separate explicit approval and all Stage 4 runtime gates pass
immediately before execution.

## Redaction Result

Manual review and marker scan requirements:

- no raw source full local path in this document;
- no raw source filename in this document;
- no raw source content in this document;
- no credential, connection, or auth header material;
- no package output, zip, or checksum material.

Allowed evidence retained:

- sanitized source label;
- path class;
- process/accessibility class;
- aggregate file and CSV counts;
- filename-date eligibility counts;
- go/no-go status.

## Next Safe Action

After this PR is reviewed, the safe next branch is:

```text
codex/operator-stage-4-preview-only-rerun
```

That branch must not run Stage 4 Preview-only unless the user separately
approves the sanitized source scope and recommended path class, and the
required runtime gates pass.
Start Upload remains forbidden until Preview-only succeeds and receives a
separate explicit approval.
