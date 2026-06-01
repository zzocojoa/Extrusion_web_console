# Development Roadmap

## 1. Create The Project Baseline

- Keep this repository separate from `Extrusion_data`.
- Treat the legacy repository as the behavior reference and fallback.
- Store product scope in `docs/00_product_scope.md`.
- Store project rules in `AGENTS.md`.

## 2. Run Engineering Review Before Coding

Before implementation, ask Codex:

```text
docs/00_product_scope.md and AGENTS.md are the source of truth.
Use plan-eng-review to define the technical architecture, APIs, data flow, job execution model, audit log design, test strategy, and migration constraints for this new web project.
Use C:\Users\user\Documents\GitHub\Extrusion_data as the reference project.
```

The engineering review must decide:

- backend framework
- frontend framework
- project directory structure
- config storage
- upload job state model
- log streaming mechanism
- audit log storage
- local Supabase start/stop mechanism
- launcher/packaging strategy
- exact legacy code extraction strategy

## 3. Scaffold The Application

Create a runnable empty skeleton first:

```text
backend/
frontend/
launcher/
supabase/
grafana/
docs/
tests/
```

Do not port business logic until the skeleton can start and show a health page.

## 4. Build Backend Core Ops

Implement backend capabilities in this order:

1. config read/write
2. audit log append/query
3. local Supabase status
4. Grafana status/link
5. upload preview
6. upload start/retry
7. progress and log streaming
8. launcher integration

## 5. Build Frontend Core Ops

Implement frontend screens in this order:

1. Dashboard
2. Settings
3. Upload
4. Logs

The UI should be operational and dense, not marketing-oriented.

## 6. Validate Against Legacy Behavior

Compare the new app against the legacy GUI for:

- candidate file detection
- preview exclusion reasons
- upload batching
- Smart Sync filtering
- failure reporting
- local Supabase readiness
- settings precedence where retained

## 7. Package And Transition

Create a double-click launcher only after backend/frontend flows are stable.

Transition from the legacy GUI only after:

- Core Ops feature parity is verified
- audit logs are working
- duplicate risk preview is working
- upload behavior is tested with representative CSV files
- README run instructions are accurate
