# Extrusion Web Console

Local web operations console for extrusion data upload and local Supabase operations.

This project replaces the legacy Tkinter GUI in `C:\Users\user\Documents\GitHub\Extrusion_data`.

## Current Status

Planning baseline created. Implementation should not start until `plan-eng-review` defines the technical architecture.

## Source Documents

- `AGENTS.md`
- `docs/00_product_scope.md`
- `docs/01_development_roadmap.md`

## Reference Project

Legacy project:

```text
C:\Users\user\Documents\GitHub\Extrusion_data
```

Use the legacy project as a behavior reference and extraction source. Do not directly port `uploader_gui_tk.py`.

## V1 Target

Core Ops only:

- Dashboard
- Settings
- Upload Preview
- Start Upload
- Retry Failed
- Upload progress and logs
- Local Supabase status/start/stop
- Grafana status/link only
- Audit logs
