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
- `DB에 있음` / `Already in DB` Upload Preview wording
- Absence of inserted-row wording: `Inserted`, `적재`, `삽입`, and `새로 삽입`
- Console errors, page errors, failed requests, and HTTP `>=400` responses
- `1440x900`, `1366x768`, `1024x768`, and `720x900`

The normal run captures 32 screenshots. It must not perform a real upload and must not require local Supabase, Docker, DB URLs, auth keys, or operational CSV files.

Text artifacts are scanned for generic timestamp-style CSV names, Windows absolute paths, credential-like markers, DB URLs, and token markers. Do not add operational CSV filename patterns, raw operational paths, CSV contents, DB URLs, or credentials to mock data or docs.

The default QA Vite port is `5174` so it does not accidentally reuse a developer server on `5173` that may be running in API mode. Override with `EWC_SCREENSHOT_QA_PORT` only when needed.

Artifacts under `.gstack/` are ignored and must not be committed.
