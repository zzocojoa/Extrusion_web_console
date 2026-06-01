# Extrusion Web Console Design System

This document is the project-specific visual system for v1 Core Ops. It applies the root `DESIGN.md` direction to a local factory operations console.

`DESIGN.md` remains the broad visual reference. This file is the implementation reference for Extrusion Web Console screens.

## Product Context

- Product: local web operations console for extrusion data upload and local runtime operations.
- Users: factory operators, maintainers, and developers supporting the operator PC.
- Runtime: Windows operator PC, localhost web app, local Supabase under WSL/Docker, Grafana as a separate link.
- Goal: reduce mistakes and make upload/runtime state obvious.
- Non-goal: marketing, cinematic hero sections, product imagery, Apple branding, or decorative showcase layouts.

## Visual Concept

Direction: **Calm Industrial Console**.

The UI should feel precise, quiet, premium, and practical. Borrow from the Apple reference only where it helps: clear hierarchy, calm surfaces, crisp type, controlled spacing, and low visual noise. Do not borrow the photography-first layout, full-viewport hero tiles, brand-like blue-only interaction language, or oversized whitespace.

Design posture:

- Light-first.
- Dense but not cramped.
- Status-led.
- Tables and logs are first-class surfaces.
- Color has operational meaning.
- Motion is functional only.

## Theme Decision

V1 ships a single light theme.

Reasons:

- Factory operator PCs are likely shared, configured, and used in normal office/factory lighting.
- A single theme reduces QA surface before Core Ops replacement.
- The light theme can still avoid glare by using muted page canvas and restrained white surfaces.

Dark mode is out of scope for v1. Do not add theme toggles.

## Color Palette

Use cool neutral surfaces with semantic colors. Do not push the whole interface into one blue or purple family.

### Core Tokens

```css
:root {
  --color-bg: #f6f7f9;
  --color-bg-subtle: #eef1f4;
  --color-surface: #ffffff;
  --color-surface-raised: #fbfcfd;
  --color-surface-muted: #f1f4f7;
  --color-border: #d7dde5;
  --color-border-strong: #b9c2ce;

  --color-text: #17202a;
  --color-text-muted: #5d6978;
  --color-text-subtle: #7a8594;
  --color-text-inverse: #ffffff;

  --color-primary: #005ea8;
  --color-primary-hover: #004f8c;
  --color-primary-soft: #e8f2fb;
  --color-primary-border: #b7d6ef;

  --color-ready: #1f7a4d;
  --color-ready-soft: #e7f4ee;
  --color-running: #2563eb;
  --color-running-soft: #e9f0ff;
  --color-attention: #b7791f;
  --color-attention-soft: #fff4dc;
  --color-risk: #c05621;
  --color-risk-soft: #fff0e6;
  --color-danger: #c2413a;
  --color-danger-soft: #fdeceb;
  --color-blocked: #8b1e1e;
  --color-blocked-soft: #f7e7e7;
  --color-muted: #687386;
  --color-muted-soft: #edf0f3;

  --color-log-info: #2f6f8f;
  --color-log-warn: #b7791f;
  --color-log-error: #c2413a;
}
```

### Status Color Rules

Never rely on color alone. Every status uses icon + label + color.

| Status | Foreground | Background | Border | Icon | Use |
|--------|------------|------------|--------|------|-----|
| ready | `--color-ready` | `--color-ready-soft` | `#b9decf` | `check-circle` | safe to proceed |
| running | `--color-running` | `--color-running-soft` | `#c6d6ff` | `activity` | active upload/runtime |
| attention | `--color-attention` | `--color-attention-soft` | `#e4c37c` | `triangle-alert` | inspect soon |
| risk | `--color-risk` | `--color-risk-soft` | `#edbf9e` | `alert-triangle` | risky preview item |
| failed | `--color-danger` | `--color-danger-soft` | `#f0b6b2` | `circle-x` | operation failed |
| blocked | `--color-blocked` | `--color-blocked-soft` | `#d9aaa8` | `octagon-alert` | action unavailable |
| muted | `--color-muted` | `--color-muted-soft` | `--color-border` | `circle` | inactive/unknown |

### Upload Preview Status Mapping

| Preview state | Visual token | Table behavior |
|---------------|--------------|----------------|
| `target` | ready | normal eligible row |
| `already_in_db` | muted with blue text accent | row remains visible, de-emphasized |
| `partial_overlap` | attention | sticky warning in summary, not selected by default |
| `risky` | risk | upload disabled for these rows |
| `excluded` | muted | row dimmed, reason required |

### Upload Job State Mapping

| Job state | Visual token |
|-----------|--------------|
| `queued` | muted |
| `running` | running |
| `succeeded` | ready |
| `partial_failed` | attention |
| `failed` | failed |
| `pausing` | attention |
| `paused` | attention |
| `cancelling` | attention |
| `cancelled` | muted |
| `interrupted` | blocked |

## Typography

Use self-hosted or bundled fonts when possible. Do not depend on external font CDNs at runtime.

Recommended stack:

```css
--font-sans: "Geist", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
--font-data: "Geist Mono", "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;
```

Rationale:

- `Geist` gives the calm, crisp, premium utility feel without copying Apple.
- `Segoe UI` is the practical Windows fallback.
- `Geist Mono` or `JetBrains Mono` keeps logs, counts, paths, and IDs aligned.

Typography rules:

- Letter spacing is `0`. Do not use negative tracking.
- Font size does not scale with viewport width.
- Use tabular numbers for metrics, counts, times, and row numbers.
- Buttons and badges use short labels. Long explanation moves to detail text.

### Type Scale

```css
--text-xs: 12px;
--text-sm: 13px;
--text-md: 14px;
--text-body: 15px;
--text-lg: 18px;
--text-xl: 22px;
--text-page: 26px;

--line-tight: 1.2;
--line-normal: 1.45;
--line-table: 1.25;

--weight-regular: 400;
--weight-medium: 500;
--weight-semibold: 600;
```

Use:

- Page title: 26px / 600 / 1.2.
- Section title: 18px / 600 / 1.2.
- Panel title: 15px / 600 / 1.25.
- Body: 15px / 400 / 1.45.
- Form label: 13px / 500 / 1.25.
- Table header: 12px / 600 / 1.25.
- Table cell: 13px / 400 / 1.25.
- Badge: 12px / 600 / 1.0.
- Log line: 13px / data font / 1.45.

## Spacing And Density

Use a 4px base with operational density.

```css
--space-0: 0;
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
```

Density rules:

- Page padding desktop: 20px.
- Page padding at 1024px: 16px.
- Panel padding: 16px.
- Compact panel padding: 12px.
- Table row height: 36px.
- Expanded table row min-height: 48px.
- Topbar height: 52px.
- Sidebar width: 220px.
- Icon button size: 32px.
- Minimum touch target on small screens: 40px.

Avoid `80px` marketing whitespace in this app. The Apple reference whitespace becomes controlled breathing room, not full-viewport spacing.

## Radius, Borders, Elevation

```css
--radius-none: 0;
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-pill: 999px;

--shadow-none: none;
--shadow-focus: 0 0 0 3px rgba(0, 94, 168, 0.18);
```

Rules:

- Panel/card radius max: 8px.
- Buttons: 6px radius. Pills only for status chips and compact badges.
- Tables: 8px outer radius, square internal cells.
- No decorative card shadows.
- Use borders and surface changes for hierarchy.
- Focus ring uses `--shadow-focus` plus visible outline when needed.

## Layout System

Approach: grid-disciplined.

Breakpoints:

```css
--bp-sm: 720px;
--bp-md: 900px;
--bp-lg: 1200px;
--bp-xl: 1440px;
```

Rules:

- Desktop app shell uses fixed sidebar + topbar + fluid content.
- Below 900px, sidebar collapses to icon rail.
- Below 720px, navigation becomes top tabs.
- Tables horizontally scroll below available width. Do not collapse critical columns into cards for v1.
- No nested UI cards.

## Component Rules

### Sidebar

- Background: `--color-surface`.
- Border-right: 1px `--color-border`.
- Width: 220px.
- Nav item height: 36px.
- Active item: `--color-primary-soft` background, `--color-primary` left border 3px, text `--color-text`.
- Inactive item: transparent background, muted icon, text `--color-text-muted`.
- Bottom badges: localhost, language, version.

### Topbar

- Height: 52px.
- Background: `--color-surface-raised`.
- Border-bottom: 1px `--color-border`.
- Left: page title and short state.
- Right: status chips.
- No black global nav from the Apple reference. Black nav would read like a consumer brand page, not an operator console.

### Panels

- Background: `--color-surface`.
- Border: 1px `--color-border`.
- Radius: 8px.
- Padding: 16px.
- Header row: title left, actions right.
- Panels may sit side by side, but never inside other panels.

### Tables

Table surfaces carry the product. Make them precise.

- Header background: `--color-surface-muted`.
- Header text: `--color-text-muted`, 12px / 600.
- Row height: 36px.
- Cell padding: 8px 10px.
- Border-bottom: 1px `--color-border`.
- Hover: `#f8fafc`.
- Selected: `--color-primary-soft`.
- Sticky header.
- Sticky first important column on Preview table: Filename.
- Numeric columns use `--font-data`, tabular numbers, right aligned.
- Long path cells middle-truncate and include copy icon.
- Error rows use semantic left border, not full red background.

### Forms

- Labels above inputs, not left-aligned labels, for responsive stability.
- Label: 13px / 500 / muted text.
- Input height: 36px.
- Input background: `--color-surface`.
- Border: 1px `--color-border-strong`.
- Radius: 6px.
- Focus: primary border + focus ring.
- Disabled/env override: `--color-surface-muted`, muted text, `Overridden` badge.
- Secret fields masked by default.
- Validation appears under the field and in a section-level summary.

### Buttons

Primary:

- Background `--color-primary`.
- Hover `--color-primary-hover`.
- Text white.
- Height 36px.
- Radius 6px.
- Padding 0 14px.

Secondary:

- Background `--color-surface`.
- Border `--color-border-strong`.
- Text `--color-text`.
- Hover `--color-surface-muted`.

Danger:

- Background `--color-danger`.
- Hover `--color-blocked`.
- Text white.
- Used for Cancel Job and Stop Supabase only.

Ghost/icon:

- Transparent.
- 32px square.
- Hover `--color-surface-muted`.
- Always has tooltip.

Button text constraints:

- English command labels max 22 characters where possible.
- Korean command labels max 12 characters where possible.
- If the text needs explanation, keep button short and add detail nearby.

### Badges

- Height: 22px.
- Padding: 0 8px.
- Radius: pill.
- Icon size: 12px.
- Text: 12px / 600.
- Never use badge color without text.

### Progress

Progress track:

- Height: 8px for normal panels.
- Height: 12px for primary job progress.
- Radius: pill.
- Background: `--color-bg-subtle`.

Progress fill:

- Running: `--color-running`.
- Completed: `--color-ready`.
- Partial/paused: `--color-attention`.
- Failed/interrupted: `--color-danger`.

Indeterminate:

- Use subtle animated stripe or shimmer only inside the track.
- No full-page spinner for known table loading.

### Log Viewer

- Background: `#101820`.
- Text: `#e6edf3`.
- Font: `--font-data`.
- Size: 13px.
- Line height: 1.45.
- Padding: 12px.
- Radius: 8px.
- Border: 1px `#263241`.
- Timestamps: `#93a4b7`.
- Info: `#9ed0ea`.
- Warning: `#ffd27a`.
- Error: `#ff9b95`.
- Search highlight: `#6b5f21` background, `#fff6c7` text.

Audit logs do not use the dark log viewer by default. Audit is a table, because operators need comparison and filtering.

## Icon Principles

Use `lucide-react`.

Required icons:

- Dashboard: `layout-dashboard`
- Upload: `upload-cloud`
- Logs: `scroll-text`
- Settings: `settings`
- Ready: `check-circle`
- Running: `activity`
- Attention: `triangle-alert`
- Risky: `alert-triangle`
- Failed: `circle-x`
- Blocked: `octagon-alert`
- Start: `play`
- Stop: `square`
- Pause: `pause`
- Resume: `play`
- Cancel: `ban`
- Retry: `rotate-ccw`
- Open Grafana/link: `external-link`
- Copy path: `copy`
- Search: `search`
- Filter: `list-filter`
- Save: `save`

Rules:

- Icon-only buttons need tooltips.
- Status icons are always paired with visible text.
- Do not draw custom SVG icons unless lucide has no matching symbol.

## Page Visual Guides

### Dashboard

Visual hierarchy:

1. Safety summary banner.
2. Four compact status panels: Upload, Supabase, Grafana, State Store.
3. Current job or latest failure panel.
4. Recent activity.

The safety banner gets the strongest color treatment. Other panels are calm and bordered.

Dashboard should fit the safety banner and status panels in the first viewport at 1366x768.

### Upload Preview

The preview table is the main visual object.

- Summary strip above table uses status counts with badges.
- Filters sit in one compact toolbar.
- `risky` and `partial_overlap` are visually louder than `target`.
- `excluded` rows are dimmed but readable.
- The Reason column is mandatory.
- Stale preview shows an attention banner above the table.

### Upload Job

- Overall progress at top.
- Job metrics in a compact four-column row: files, rows, failures, duration.
- Failed files stay pinned above successful files after completion.
- Live events are below file table, not mixed into the table.
- Cancel/Pause/Resume are grouped near progress, visually separate from Start/Retry.

### Job Logs

- Job logs use dark log viewer only when reading raw stream output.
- The default Job Logs tab uses a table with filters.
- A row expand can show raw JSON/details in dark mono block.
- Error level rows have red left border.

### Audit Logs

- Audit is a light table.
- Failed, blocked, cancelled results use semantic badges.
- Params are compact JSON chips with secret redaction.
- No delete, no edit, no inline mutation.

### Settings

- Sectioned forms.
- Runtime and source metadata are visible before editable fields.
- Env-overridden fields are visually disabled, not hidden.
- Sticky save bar at bottom.
- Save result appears inline in the bar and audit logs.

## Motion

Motion approach: minimal-functional.

```css
--duration-fast: 80ms;
--duration-short: 140ms;
--duration-medium: 220ms;
--ease-standard: cubic-bezier(0.2, 0, 0, 1);
```

Use motion only for:

- Button press feedback.
- Row expansion.
- SSE event arrival highlight.
- Progress transitions.
- Sidebar collapse.

Do not animate page entrance, dashboard panels, decorative backgrounds, or table sorting with large motion.

## CSS Token Starter

Implementation can start with this root block and extend it in `frontend/src/styles/tokens.css`.

```css
:root {
  color-scheme: light;

  --font-sans: "Geist", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-data: "Geist Mono", "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;

  --color-bg: #f6f7f9;
  --color-bg-subtle: #eef1f4;
  --color-surface: #ffffff;
  --color-surface-raised: #fbfcfd;
  --color-surface-muted: #f1f4f7;
  --color-border: #d7dde5;
  --color-border-strong: #b9c2ce;
  --color-text: #17202a;
  --color-text-muted: #5d6978;
  --color-text-subtle: #7a8594;
  --color-text-inverse: #ffffff;

  --color-primary: #005ea8;
  --color-primary-hover: #004f8c;
  --color-primary-soft: #e8f2fb;
  --color-primary-border: #b7d6ef;

  --color-ready: #1f7a4d;
  --color-ready-soft: #e7f4ee;
  --color-running: #2563eb;
  --color-running-soft: #e9f0ff;
  --color-attention: #b7791f;
  --color-attention-soft: #fff4dc;
  --color-risk: #c05621;
  --color-risk-soft: #fff0e6;
  --color-danger: #c2413a;
  --color-danger-soft: #fdeceb;
  --color-blocked: #8b1e1e;
  --color-blocked-soft: #f7e7e7;
  --color-muted: #687386;
  --color-muted-soft: #edf0f3;

  --text-xs: 12px;
  --text-sm: 13px;
  --text-md: 14px;
  --text-body: 15px;
  --text-lg: 18px;
  --text-xl: 22px;
  --text-page: 26px;
  --line-tight: 1.2;
  --line-normal: 1.45;
  --line-table: 1.25;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-pill: 999px;

  --topbar-height: 52px;
  --sidebar-width: 220px;
  --table-row-height: 36px;
  --control-height: 36px;
  --icon-button-size: 32px;

  --shadow-focus: 0 0 0 3px rgba(0, 94, 168, 0.18);
  --duration-fast: 80ms;
  --duration-short: 140ms;
  --duration-medium: 220ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
}
```

## Tailwind Mapping

If Tailwind is used, map tokens rather than hardcoding hex in components.

```js
theme: {
  extend: {
    fontFamily: {
      sans: ["Geist", "Segoe UI", "system-ui", "sans-serif"],
      data: ["Geist Mono", "JetBrains Mono", "Consolas", "monospace"],
    },
    colors: {
      bg: "var(--color-bg)",
      surface: "var(--color-surface)",
      border: "var(--color-border)",
      text: "var(--color-text)",
      muted: "var(--color-text-muted)",
      primary: "var(--color-primary)",
      ready: "var(--color-ready)",
      running: "var(--color-running)",
      attention: "var(--color-attention)",
      risk: "var(--color-risk)",
      danger: "var(--color-danger)",
      blocked: "var(--color-blocked)",
    },
    borderRadius: {
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
      lg: "var(--radius-lg)",
    },
  },
}
```

## Design QA Checklist

### Before Implementation

- `docs/03_ui_ux_plan.md` and this file agree on IA and component purpose.
- No v1-excluded page appears in navigation.
- The chosen visual direction does not require product photography or marketing hero assets.
- All status states have a token and icon.
- Long Korean labels have a planned wrapping/truncation behavior.

### After React Implementation

Capture screenshots at:

- 1366x768
- 1920x1080
- 1024x768
- 720x900
- 375x812

Check:

- Dashboard first viewport shows safety summary and runtime/upload state without scrolling at 1366x768.
- No text overlaps in Korean or English.
- Buttons keep stable dimensions across language switch.
- Preview table supports 200+ rows with sticky header and no layout shift.
- Status badges remain readable in all states.
- Risky/partial/excluded rows are distinguishable without reading only color.
- Job progress updates do not resize panels.
- Log viewer preserves monospace alignment and readable contrast.
- Audit table redacts secrets.
- Settings env override fields are visibly read-only.
- Focus ring is visible on buttons, tabs, table rows, and form controls.
- Page does not read as a SaaS landing page, marketing hero, or decorative card grid.

### Pixel Checks

- Topbar height remains 52px.
- Sidebar width remains 220px on desktop.
- Table row height remains 36px unless row is expanded.
- Panel radius does not exceed 8px.
- No nested panel/card backgrounds.
- No negative letter-spacing.
- No viewport-based font scaling.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-01 | Use Calm Industrial Console direction | Fits operator console, avoids marketing layout, preserves premium clarity from `DESIGN.md`. |
| 2026-06-01 | Ship light-only v1 | Reduces implementation/QA scope and suits shared Windows operator PCs. |
| 2026-06-01 | Use semantic multi-color state system | Upload/runtime safety cannot depend on one blue accent. |
| 2026-06-01 | Use Geist + Segoe UI fallback | Gives crisp utility feel while staying practical on Windows. |
| 2026-06-01 | Use bordered panels, no decorative shadows | Keeps hierarchy calm and dense without card-heavy marketing feel. |
