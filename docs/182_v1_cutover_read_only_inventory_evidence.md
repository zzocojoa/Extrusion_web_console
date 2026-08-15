# V1 Cutover Read-Only Inventory Evidence

## Status

```text
read_only_inventory_human_confirmed_preview_not_approved_no_data_mutation
```

## Summary

- Evidence date: 2026-08-15 Asia/Seoul
- Inventory record id: `inv_20260815T031829Z_0d41338f`
- Inventory observation: `completed`
- Human reviewer class: `human_operator`
- Human review status: `confirmed`
- Preview approval: `not_approved`
- Upload Preview executions: `0`
- Operational DB queries or mutations: `0`
- Source mutations: `0`
- Final decision: `blocked`

This is a filled, sanitized read-only inventory evidence record for the V1
cutover gate. It is not an approval template and does not authorize Upload
Preview, Start Upload, Retry Failed, Delete, Settings save, runtime lifecycle,
Supabase or Docker lifecycle, LAN, deployment, migration, reset, cleanup, or
any source or database mutation.

## Package Binding

| Field | Recorded value |
| --- | --- |
| `packageSourceCommit` | `d16b822d4a461fc7705c5aca9cebd40cb19fe918` |
| `packageLabel` | `ExtrusionWebConsole-d16b822-20260815-030206-082` |
| `zipSha256` | `1e5416072511daeb884e4be7be3f257e7b00377fb9614df53c8c6df67129a83c` |
| Runtime mode | `operator-ready` |
| Frontend mode | `api` |
| Package installation or execution | not performed by this record |

The package label, source commit, and ZIP hash identify the artifact to which
this inventory is bound. They do not prove that this artifact is installed or
currently executing on the operator PC.

## Inventory Result

| Field | Recorded value |
| --- | --- |
| `inventoryEvidenceRecordId` | `inv_20260815T031829Z_0d41338f` |
| `inventoryObservedAtUtc` | `2026-08-15T03:18:29.4209312Z` |
| `sourceKind` | `plc` |
| `sourceScope` | `folder_all` |
| `sourceOriginClass` | `operator_config` |
| `sourceClass` | `drive_letter` |
| `sourceFingerprint` | `8823e8a110b1eae4` |
| `inventoryObservedFiles` | `12` |
| `inventoryObservedPhysicalDataLines` | `3451430` |
| `inventoryApprovedPhysicalRowsCeiling` | `3451430` |
| Stable files | `12` |
| Unstable files | `0` |
| Non-CSV files in the direct scope | `0` |
| Read errors | `0` |
| Files changed during read | `0` |
| Scope changed during inventory | `false` |
| `inventoryEvidenceHash` | `e0f051d2a2b158a076d50b4d617dce41ecf0dac9a328e35682e04048c28b790c` |

The physical data-line count is the sum of physical file lines after removing
one header line from each non-empty CSV. It is not a transformed exact-key
count, Preview target-row count, database match count, or database row count.

## Human Confirmation

The human operator confirmed the following bounded values after the read-only
observation:

```text
inventoryObservedFiles = 12
inventoryApprovedPhysicalRowsCeiling = 3451430
Preview execution is not approved.
```

The reviewer is recorded as the sanitized role class `human_operator`; no
personal identifier is stored in this repository record.

## Required Evidence Fields

| Field | Current value |
| --- | --- |
| `previewApprovalId` | `not_approved` |
| `previewRunId` | `not_run` |
| `previewStatus` | `not_run` |
| `previewTargetRows` | `not_observed` |
| `previewPartialOverlapRows` | `not_observed` |
| `previewRiskyCount` | `not_observed` |
| `dbStatusClass` | `not_queried` |
| `targetClassStatus` | `not_observed` |
| `runtimeReadinessClass` | `not_observed` |
| `edgeAuthClass` | `not_observed` |
| `startUploadApprovalId` | `not_approved` |
| `approvedTargetRows` | `not_applicable` |
| `uploadJobId` | `not_created` |
| `acceptedRowsClass` | `not_applicable` |
| `retryApprovalId` | `not_approved` |
| `remainingPhysicalRows` | `not_applicable` |
| `auditEvidence` | `not_created` |
| `dbDeltaEvidence` | `not_queried` |
| `rowAttributionEvidence` | `not_queried` |
| `finalDecision` | `blocked` |

## Read-Only Method

The inventory used the operator-configured PLC source directly and considered
only direct child files with the `.csv` extension. It:

1. read the configured source using UTF-8;
2. classified the source without recording its raw path;
3. captured file size and modification metadata before reading;
4. streamed file bytes only to count physical newline boundaries;
5. removed one header line from each non-empty CSV;
6. compared size, modification time, and scope before and after the scan; and
7. emitted only sanitized classes, counts, ids, fingerprints, and hashes.

It did not call the Upload Preview API, start a backend, query Supabase, call an
Edge function, write audit or local application state, or modify a source file.

## Redaction And Safety Validation

| Check | Result |
| --- | --- |
| Raw operational source path recorded | no |
| Raw source filename recorded | no |
| CSV content or row content recorded | no |
| Raw timestamp/device key recorded | no |
| DB URL, token, Authorization value, JWT, or credential recorded | no |
| Preview run or local Preview state created | no |
| Operational DB query or mutation performed | no |
| Source file mutation performed | no |

## Staleness And Stop Conditions

This record is valid only for the recorded package identity, source class,
source fingerprint, file count, and physical-row ceiling. Before any separate
Preview approval is used, stop and repeat inventory if:

- the configured source class or fingerprint differs;
- observed CSV files are not exactly `12`;
- physical data lines exceed `3451430`;
- any file is unstable, unreadable, or changes during inventory;
- the source scope changes;
- the package label, source commit, or ZIP hash differs; or
- Preview approval wording does not name this exact inventory record.

## Next Gate

No next execution gate is approved by this document. A future Preview-only
request must be separate, name this inventory record and package source commit,
use `sourceClass=drive_letter`, `expectedFiles=12`, and
`expectedPhysicalRows<=3451430`, and repeat inventory first if any staleness
condition is present.
