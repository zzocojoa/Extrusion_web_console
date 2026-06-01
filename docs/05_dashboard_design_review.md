# Dashboard Design Review

This document records the design-system review for the Figma Dashboard variants.
It is a follow-up to `docs/03_ui_ux_plan.md` and `docs/04_design_system.md`.

## Review Target

- Figma file: [Extrusion Web Console Dashboard Design Shotgun](https://www.figma.com/design/xuI1kMSJs44UQGIO87pG7R)
- Screen: Dashboard variants A/B/C/D
- Primary design reference: `docs/04_design_system.md`
- Broad visual reference: `DESIGN.md`

## Compliance Score

**Design system compliance: 8.1 / 10**

The Dashboard variants mostly follow the Calm Industrial Console direction:

- Light-first theme.
- Dense operator-console layout.
- Semantic status colors.
- No marketing hero, product imagery, or decorative gradients.
- Sidebar, topbar, status panels, tables, and audit summaries are aligned with the v1 IA.

The remaining gaps are mostly implementation-level visual corrections around banner sizing, panel borders, icon treatment, button width, and data typography.

## Main Mismatches

- Variant B's safety banner is 112px tall, while `docs/04_design_system.md` expects the Dashboard safety banner to stay within 72-96px. The calmer layout is good, but the banner risks becoming hero-like.
- Variant C's `! 차단됨` headline is 30px and the state rail is 118px tall. The status emphasis is useful, but it exceeds the Dashboard banner sizing direction.
- Some large Variant B panels visually float without the required `1px #d7dde5` border. The design system requires bordered panels with calm surface hierarchy.
- Some button widths are too tight. Variant C's `Logs 보기` button at 48px is especially risky for Korean/English switching.
- Status icons use text symbols such as `●`, `!`, and `×`. This is acceptable for rough mockups, but implementation should use lucide-equivalent icons: `check-circle`, `activity`, `triangle-alert`, `octagon-alert`, and `circle-x`.
- Some numeric, time, and row-count values use Inter. The design system calls for a data font such as Geist Mono or JetBrains Mono for numbers, paths, IDs, logs, and tabular values.
- Not every variant explicitly includes the State Store status panel. Dashboard hierarchy should consistently include Upload, Supabase, Grafana, and State Store.

## Figma Edit Status

No Figma edits were applied during the review because the Figma MCP returned a Starter plan call-limit error:

```text
You've reached the Figma MCP tool call limit on the Starter plan
```

## Required Figma Corrections

Apply these corrections before using a Dashboard variant as the React implementation reference:

- Variant B: change safety banner height from `112px` to `96px`.
- Variant C: change state rail height from `118px` to `96px`.
- Variant C: change the `! 차단됨` headline from `30px` to `26px`.
- Variant B: add `1px #d7dde5` border to large main panels.
- Variant C: increase `Logs 보기` button width from `48px` to at least `96px`.
- All variants: add or clarify the State Store status panel.
- All variants: replace text-symbol status icons with lucide-equivalent icon treatment.
- All variants: use mono data typography for numeric/table values.

## Remaining Risks

- Variant B is the most visually calm, but its blocked/failure state is weaker than Variant C.
- Variant C gives the fastest 3-second blocked-state judgment, but it may feel too alarm-heavy during normal operation.
- Variant A and Variant D have strong operational density, but may feel dense for first-time operators.
- React implementation still needs screenshot QA at `1366x768`, `1024x768`, and `720px` widths to confirm Korean button, badge, and table text fit.

## Recommended Direction

Use **Variant C's status-first structure** as the Dashboard baseline, then borrow **Variant D's compact table/list pattern** for the lower Recent Jobs, Runtime, Warning, and Audit sections.

Reason:

- Dashboard's primary job is to answer whether upload, DB, and runtime state are safe right now.
- Variant C answers that fastest.
- Variant D scales best into Upload, Logs, and Settings because its table/list language matches the rest of the v1 Core Ops UI.

## Expansion Rules For Other Screens

### Upload

- Upload Preview table is the main surface.
- `risky`, `partial_overlap`, and `excluded` must be shown with badge, icon, and reason text.
- Do not rely on color alone.
- Keep partial overlap excluded by default unless explicitly enabled and audit logged.

### Logs

- Keep Job Logs and Audit Logs visually separate.
- Use the dark log viewer only for raw job stream output.
- Audit Logs stay as a light table for filtering and comparison.

### Settings

- Use sectioned forms, not decorative cards.
- Show env overrides as disabled fields with source badges.
- Keep validation inline and visible in section summaries.

### Runtime And Grafana

- Local Supabase status/start/stop stays visible and audit-relevant.
- Grafana remains status/link only.
- Do not add iframe embedding, dashboard previews, or Grafana management UI.

## Implementation QA Notes

Before accepting the Dashboard implementation:

- First viewport answers safe / attention / blocked / running within 3 seconds.
- Safety banner height remains within 72-96px.
- Topbar remains 52px.
- Sidebar remains 220px on desktop.
- Panel radius does not exceed 8px.
- Buttons remain 36px high with 6px radius.
- Status badges remain 22px high with icon + label + color.
- Tables preserve 36px row height unless expanded.
- No text uses negative letter spacing.
- No page reads as a SaaS landing page or marketing hero.
- Grafana is link/status only.
- No v1-excluded features appear in navigation or Dashboard content.
