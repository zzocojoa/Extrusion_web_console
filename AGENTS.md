# AGENTS.md

## Project Identity

This project is the web-based replacement for the legacy `Extrusion_data` Tkinter GUI.

The product is a local web operations console for extrusion data upload and operations. It runs on the operator PC, connects to local Supabase running under WSL/Docker, and keeps Grafana as a separate internal-network dashboard.

## Source Of Truth

Before making architecture, implementation, or UI decisions, read:

- `DESIGN.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`
- `README.md`
- Existing reference project: `C:\Users\user\Documents\GitHub\Extrusion_data`

The product scope in `docs/00_product_scope.md` is the primary product decision record.

The visual design direction in `DESIGN.md` is the primary design system reference. When implementing UI, follow `DESIGN.md` unless a later approved design document explicitly supersedes it.

## Design Rules

When building or changing UI:

- Read `DESIGN.md` before editing frontend code.
- Treat `docs/03_ui_ux_plan.md` as the UX and information architecture source when it exists.
- Treat `DESIGN.md` as the visual style source.
- Do not create marketing-style hero sections, decorative landing pages, or image-led product pages.
- Build a dense, quiet, operator-focused console UI.
- Use the Apple-inspired reference only as a restrained visual influence: typography, hierarchy, spacing, and calm surfaces.
- Do not copy Apple branding, marketing layouts, cinematic imagery, or oversized whitespace that harms operational density.

## Scope Rules

Build v1 as Core Ops only:

- Dashboard
- Settings
- Upload Preview
- Start Upload
- Retry Failed
- Upload progress and logs
- Local Supabase status/start/stop
- Grafana status/link only
- Audit logs

Do not include in v1 unless explicitly requested:

- Data Mgmt archive/delete flows
- Supabase Mgmt delete UI
- Cycle Ops
- Training Dataset Builder
- Cloud Supabase migration
- Multi-user LAN access for the web app

## Architecture Defaults

Use a separated local web console architecture:

- Backend: Python API service
- Frontend: web UI
- Existing Python upload/transform logic should be reused where practical
- Supabase remains local
- Grafana remains separate and is not embedded in the app
- The web app itself is localhost-only

## Compatibility Rules

Do not import the legacy GUI upload state as the default migration path.

The new app should start with a new state store, but must provide Supabase-backed preview/reconciliation so operators can see which local CSV files are already represented in the database before upload.

The existing `all_metrics(timestamp, device_id)` upsert behavior is an important safety mechanism and must not be weakened.

## Safety Rules

Dangerous operations must be audit logged:

- Settings save
- Upload start
- Upload retry
- Upload cancel/pause/resume
- Local Supabase start
- Local Supabase stop
- Any failed operation

Avoid silent failures. Every background task failure must be visible in the UI and in logs.

## Reference Project Rules

Use the legacy project as reference, not as a dumping ground.

Prefer reusing or carefully extracting:

- `core/upload.py`
- `core/transform.py`
- `core/config.py`
- `core/files.py`
- `supabase/functions/upload-metrics`
- `supabase/migrations`
- `grafana/provisioning`
- `grafana/dashboards`
- upload and Smart Sync tests

Do not port `uploader_gui_tk.py` directly into the new project.
