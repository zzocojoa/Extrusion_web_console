# Supabase Assets

This directory contains the repository-owned local Supabase assets for the independent `Extrusion_web_console` runtime.

Phase 1 includes only static assets:

- `config.toml` with independent project id and ports
- `functions/upload-metrics`
- `migrations/20260608000001_create_all_metrics_upload_contract.sql`

Do not store generated runtime state here. Raw `.env` files, local DB files, dumps, logs, operational CSV files, package output, zips, checksums, and Supabase `.temp` files must stay out of source control.

This phase does not run `supabase init`, `supabase start`, DB reset, migrations, Edge Function deploy, Upload Preview, or Start Upload. Runtime control and packaging integration are separate follow-up PRs.
