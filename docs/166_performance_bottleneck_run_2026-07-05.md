# Performance Bottleneck Run 2026-07-05

## Summary

This run investigated operator-package startup and packaging performance for the local web console.

No runtime code patch was retained. A launcher health-polling experiment was tested against an installed operator package, but the installed-app A/B result did not show a reliable improvement. The source tree and packaged app were rolled back to the baseline behavior.

## Scope

- Runtime: Windows operator package path, PowerShell launcher, FastAPI backend, React/Vite frontend.
- Risk level: medium, because launcher changes affect operator startup and support diagnostics.
- Safety boundary: no upload, delete, Supabase lifecycle, Docker, or operational CSV flow was exercised.

## Baseline Measurements

Measured on a prepared local workspace with a fresh Python virtual environment and frontend dependencies installed.

| Area | Result |
| --- | ---: |
| API-mode frontend build | 6.667 s |
| Operator package assembly | 8.382 s |
| Installed package launcher to external `/api/health` | 6974 ms |
| Source direct uvicorn to `/api/health` | 1249 ms |
| Installed package direct uvicorn to `/api/health` | 1254 ms |

Installed package route samples after startup:

| Route | Average |
| --- | ---: |
| `/` | 25.6 ms |
| `/upload` | 14.7 ms |
| `/logs` | 13.1 ms |
| `/settings` | 13.0 ms |
| `/api/config` | 20.9 ms |
| `/api/audit?limit=1` | 23.0 ms |

## Experiment Tested And Rolled Back

Candidate patch:

- Change launcher `Get-Health` from `Invoke-RestMethod -TimeoutSec 2` to `-TimeoutSec 1`.
- Change `Wait-ForHealth` polling sleep from `500 ms` to `100 ms`.

Reason for testing:

- A closed localhost port call with `Invoke-RestMethod -TimeoutSec 2` took about 2 seconds per failed probe.
- The launcher uses health polling before opening the browser, so failed probes looked like a plausible startup delay source.

Installed-package readiness log A/B:

| Variant | Trial 1 | Trial 2 | Trial 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 2195 ms | 2233 ms | 3944 ms | 2233 ms |
| Patched | 4422 ms | 2479 ms | 2264 ms | 2479 ms |

Decision:

- The patch did not produce a reliable improvement and regressed the median by about 246 ms in this sample.
- The code change was reverted before commit.

## Current Bottleneck Read

Direct uvicorn startup from both source and the installed package was about 1.25 seconds, while full launcher startup was materially higher and variable. The launcher path still appears to be the best next investigation target, but the next change should begin with phase-level millisecond instrumentation before changing behavior.

Packaging assembly is also a valid next candidate. The baseline assembly took about 8.4 seconds and pruned more than 1600 runtime cache entries from `.venv`, so the copy/prune path may have measurable overhead.

## Recommended Next Run

1. Add temporary or permanent millisecond phase timing for launcher startup:
   - repo resolution
   - log path setup
   - Supabase default resolution
   - PLC source guard
   - port check
   - backend process spawn
   - first successful health probe
2. Re-run installed-package cold start with at least five trials.
3. Only patch the slowest confirmed phase.
4. If launcher phase timing does not isolate a clear delay, test package assembly copy/prune optimization next.

## Validation

- `python -m venv .venv`
- `npm ci`
- `.venv\Scripts\python -m pip install -r backend\requirements.txt`
- `npm run build:api`
- `packaging\assemble_operator_package.ps1 -FrontendMode api`
- Installed-package launcher cold-start smoke with `/`, `/upload`, `/logs`, `/settings`, `/api/config`, and `/api/audit?limit=1`
- Targeted launcher tests during the reverted experiment: `29 passed`

## Known Gaps

- Browser Core Web Vitals were not collected because the gstack browse daemon was not available in this workspace.
- The first installed-app baseline included cold OS and process-cache effects; repeated A/B used warmed local cache.
- No code patch remains from this run, so there is no production rollback action beyond discarding the failed experiment output.
