# Frontend Screenshot QA

Run this from `frontend/`:

```powershell
npm run qa:screenshots
```

The command starts Vite in mock mode, runs Chromium through Playwright, and writes screenshots plus redacted console/network artifacts under:

```text
../.gstack/screenshots/upload-job-browser-qa/<timestamp>/
```

The runner covers:

- Dashboard smoke
- Upload Preview
- Upload Job
- Job Logs
- Audit Logs
- Settings smoke
- Korean and English `acceptedRows` wording
- `1440x900`, `1366x768`, `1024x768`, and `720x900`

It must not perform a real upload and must not require local Supabase, Docker, DB URLs, auth keys, or operational CSV files.

The default QA Vite port is `5174` so it does not accidentally reuse a developer server on `5173` that may be running in API mode. Override with `EWC_SCREENSHOT_QA_PORT` only when needed.

Artifacts under `.gstack/` are ignored and must not be committed.
