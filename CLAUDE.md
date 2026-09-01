# tax-billing

workflow-version: 13
releasable: false

Personal Canadian sole-proprietor tax-holdback calculator and invoicing
tool. Single-tenant (one business owner, one user). **L3 security profile**
— this tool holds authoritative tax math and real client PII.

## Stack
- **Language:** Python 3.12 (pinned in `.mise.toml`)
- **Backend:** FastAPI 0.115 + uvicorn 0.30 (async)
- **Frontend:** Flet 0.24 (Flutter-in-Python) — canonical mode is containerized web on port 8080
- **Database:** PostgreSQL 16-alpine via `asyncpg` 0.29
- **ORM:** SQLAlchemy 2.0 async
- **Validation:** pydantic 2.9 + pydantic-settings
- **PDF rendering:** WeasyPrint 60 + Jinja2 (invoice template)
- **Coding Paradigm:** Layered / service-oriented (`routers → services → models`). Pure tax math lives in `backend/app/services/tax_calculator.py` and avoids side effects.
- **Testing Paradigm:** Adaptive. TDD for pure logic (`services/tax_calculator.py`, validators, bracket math); test-after for routers, Flet views, and wiring.
- **Test Runner:** pytest + pytest-asyncio (configured in Milestone 2)
- **Linter/Formatter:** ruff (configured in Milestone 2)
- **Type Checker:** mypy — strict on `backend/app/services/`, lenient elsewhere (configured in Milestone 2)
- **Package Manager:** pip via `requirements.txt` (one per tier). `pyproject.toml` arrives in Milestone 2.
- **Runtime / Task Manager:** mise

## Project Map

Canonical [[wikilink]] targets for this project:
- [[CLAUDE]] — this file (agent conventions, stack, commands)
- [[PROJECT]] — status, architecture decisions, milestones
- [[TASKS]] — milestone index / dashboard
- [[workflow/tasks/milestone-02-quality-gates]] — active milestone (current work queue)
- [[workflow/tasks/milestone-01-stop-the-bleeding]] — completed milestone, frozen archive (tag `milestone-01-stop-the-bleeding`, closed 2026-09-01)
- [[workflow/tasks/deferred]] — task-level deferred / descoped log
- [[workflow/tasks/discovered]] — discovered-work log
- [[README]] — user-facing setup and usage
- [[workflow/handoffs/]] — session continuity directory (latest: [[workflow/handoffs/handoff-005]])
- [[workflow/memory/MEMORY]] — stable operational/workflow patterns for this machine
- `security-profile.yaml` — L3 profile for `/security-audit`

## Commands

All commands are declared in `.mise.toml` where possible. Run from project root.

```bash
# Install Python toolchain
mise install

# Start database + backend (Docker)
mise run up

# Start everything (db + backend + containerized Flet web frontend)
# Canonical run mode — opens http://localhost:8080 in a browser
# NOT YET CONFIGURED — arrives with Milestone 5
mise run up-all

# Run Flet frontend in native desktop mode (WSL2/WSLg or Linux host)
# Non-canonical dev convenience. Requires WSLg on Windows 11 or a native Linux desktop.
# Currently named `mise run frontend`; renames to `mise run desktop` in Milestone 5
mise run desktop

# Run Flet frontend in web mode (host-side, interim until Milestone 5)
# Current way to get a browser UI: runs pip install + FLET_WEB=1 python main.py
# on the HOST. Milestone 5 replaces this with the containerized frontend service
# wired into `mise run up-all`.
mise run web

# Stop services (keeps containers and data)
mise run stop

# Tear down containers (keeps data volume)
mise run down

# View logs
mise run logs

# Full data reset (WIPES ALL DATA — schema.sql re-runs)
docker compose down -v && docker compose up -d

# Run tests (NOT YET CONFIGURED — arrives with Milestone 2)
pytest

# Lint (NOT YET CONFIGURED — arrives with Milestone 2)
ruff check .

# Format (NOT YET CONFIGURED — arrives with Milestone 2)
ruff format .

# Type check (NOT YET CONFIGURED — arrives with Milestone 2)
mypy backend/app/services

# Smoke test (NOT YET DEFINED — lands with vertical slice in Milestone 2)
# Intended: create client → create invoice → record payment → fetch tax summary

# Database schema changes currently require:
docker compose down -v && docker compose up -d
# This wipes the data volume. Alembic migrations arrive in Milestone 4.
```

## Project Structure

```
tax-billing/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI app instance, CORS, exception handler
│       ├── config.py            # pydantic-settings (reads .env)
│       ├── database.py          # async SQLAlchemy engine + session factory
│       ├── models/              # SQLAlchemy ORM models
│       ├── schemas/             # pydantic request/response schemas
│       ├── routers/             # FastAPI routers (one per domain)
│       ├── services/            # Business logic (tax_calculator, invoice_pdf, backup_service)
│       └── templates/           # Jinja2 templates (invoice.html for PDF rendering)
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # Flet entry point
│   ├── services/
│   │   └── api_client.py        # httpx wrapper around backend /v1/*
│   └── views/                   # One file per navigation destination
├── database/
│   ├── schema.sql               # Mounted to /docker-entrypoint-initdb.d/ on first run
│   └── seed_data.sql            # CRA federal + Ontario provincial brackets
├── docker-compose.yml
├── .mise.toml
├── .env / .env.example
├── security-profile.yaml        # L3
├── CLAUDE.md / PROJECT.md / TASKS.md / README.md
└── workflow/
    ├── handoffs/            # session continuity (handoff-NNN.md)
    ├── tasks/               # milestone files + deferred/discovered logs
    └── memory/              # MEMORY.md — machine/workflow patterns
```

## Conventions

### File Organization
- Backend: strict layering — a router imports services and schemas; services import models; models import nothing from routers. Do not reach across layers.
- One router per domain (`clients.py`, `invoices.py`, etc.). One service per cross-cutting concern.
- Frontend: one view per navigation destination; the `api_client` is the only thing that talks HTTP.
- Schemas (`backend/app/schemas/`) mirror models but are pydantic — never return ORM objects directly from a router.

### Naming
- snake_case for Python. PascalCase for ORM models and pydantic schemas.
- Enums live next to the model they annotate (`InvoiceStatus` in `models/invoice.py`).
- `v1` API prefix is fixed. Every router mounts under `/v1/<domain>`.

### Patterns
- **Money is `Decimal`, always.** Never `float`. DB columns are `DECIMAL(12,2)`, Python values are quantized to `Decimal("0.01")`. Any new money path must preserve this.
- **Async all the way down.** Routers are `async def`, service methods that touch the DB are `async def`, SQLAlchemy uses `AsyncSession`. No sync DB access.
- **Pure functions in `services/tax_calculator.py`.** Bracket math takes numbers in, returns numbers out, no I/O, no side effects. This is the TDD core.
- **Pydantic at the boundary.** Request bodies are pydantic models with `Field(...)` constraints. Responses are pydantic schemas, not ORM objects.

### Error Handling
- Validation errors: pydantic raises, FastAPI translates to 422. Don't catch these.
- Domain errors: raise `HTTPException` with a specific status code and a user-meaningful detail string. Never leak stack traces.
- DB errors: let SQLAlchemy raise; the global exception handler in `main.py` logs and returns 500.
- Tax math errors: `services/tax_calculator.py` raises `ValueError` for impossible inputs (negative income, unknown province). Routers translate to 400.

### Imports
- Absolute imports from `app.*` inside the backend. No relative imports.
- Frontend imports from `services.*` and `views.*` — no cross-view imports.

## Testing Strategy

Derived from the adaptive testing paradigm in [[PROJECT]].

testing-paradigm: adaptive

- **TDD (test-first):** `backend/app/services/tax_calculator.py` — pure math, clear contracts, the one place a silent bug costs the user real money. Interface is specified before implementation; tests drive the shape.
- **TDD (test-first):** pydantic validators and any future pure-logic helpers.
- **Test-after:** routers, database integration, `backup_service.py`, `invoice_pdf.py`, Flet views.
- **Skip (for now):** end-to-end browser tests of the Flet web UI. Revisit if the tool grows beyond personal use.
- **Coverage target:** not a metric we chase. Every bug fix adds a regression test; every new pure-logic function has tests before it's merged.

## Secrets & Environment

- **Secrets file format:** `.env` (dotenv), consumed by `pydantic-settings` in `backend/app/config.py` and by `docker-compose.yml` via `${VAR}` refs.
- **Example file:** `.env.example` — documents every required variable with a placeholder. Agents read ONLY this file, never the real `.env`.
- **Milestone 1 extracted** every hardcoded credential from `docker-compose.yml` and `config.py` defaults into `.env` refs (TASK-002, PR #5). Any new credential follows the same pattern: `${VAR}` in compose, a `pydantic-settings` field in `config.py` with **no** default, and a documented placeholder in `.env.example`.
- **Rotating a credential never uses `docker compose down -v`.** The `POSTGRES_*` vars only take effect at first volume initialization, so a rebuild would destroy real financial data for nothing. Rotate in place: `ALTER USER … PASSWORD` inside the running `tax-billing-db` container, edit `.env` (`POSTGRES_PASSWORD`, `DATABASE_URL`), then `docker compose up -d` to recreate the backend ([[PROJECT]] ADR #12; lands with TASK-003 in Milestone 3).
- **Never commit `.env`.** Gitignored at project root. Never has been committed (verified in plenary audit).

## Convention Overrides

None at plenary time. If the project diverges from global standards in the future, record the decision here with a rationale.

| Area | Global Standard | This Project | Rationale |
|------|----------------|--------------|-----------|

## Gotchas

- **Schema is applied via compose init-volume, not migrations.** `database/schema.sql` is mounted at `/docker-entrypoint-initdb.d/` and runs exactly once on first volume creation. Any schema change requires `docker compose down -v` and wipes all data. Alembic migrations arrive in Milestone 4 — do not add ad-hoc DDL before then.
- **Host port 5435 → container 5432.** Deliberate, loopback-bound (`127.0.0.1:5435:5432`) and registered: tax-billing owns 5435 in the global port registry (`~/.claude/references/port-registry.yaml`, postgres range 5433–5452). **Connect externally on 5435**, but the backend inside the compose network still talks to `db:5432` — so application config and `.env.example` are unaffected by host-port changes; only `psql`/`pg_dump`/shell aliases are. History: 5433 originally → 5434 on 2026-04-13 after a host port conflict → 5435 on 2026-09-01 (TASK-018, PR #25) after a registry collision with `adamson-next-2025`, which is the registered owner of 5434. tax-billing's port predated the registry and was unregistered, so it was the party that moved; it is now registered.
- **`backups/` is bind-mounted and root-owned.** The container writes backup files as root onto the host volume, so `horse` cannot delete or overwrite them from the host without `sudo`. Don't reach for `sudo` — manage them from inside the container, which is already root and sees the same files at `/app/backups`: e.g. `docker exec tax-billing-backend sh -c 'rm -f /app/backups/*.json'`. That is how TASK-006 cleared the dead pre-TASK-001 `.json` dumps, and it is the pattern for anything else the backend wrote across that mount.
- **Cargo-culted dependencies.** `alembic`, `python-jose`, `passlib`, `httpx` (backend), and `psycopg2-binary` are declared in `backend/requirements.txt` but not yet used. `passlib` and `python-jose` become real in Milestone 3 (auth). The rest get trimmed in Milestone 6 after auth lands, so we know which stay.
- **Frontend name is a lie.** `frontend/` contains Python, not JavaScript. It is a Flet (Flutter) desktop/web client. Do not look for React or a build step.
- **Flet `FilePicker.save_file()` is a no-op in web mode.** The FilePicker class is documented as using the "native file explorer" — it works in Flet's native desktop client (Flutter-desktop) but silently does nothing in Flet's web mode (Flutter-web-compiled) because browsers cannot open native OS save dialogs from JavaScript. For file **downloads** in web mode (the canonical run mode per [[PROJECT]] ADR #4), use `page.launch_url(backend_url)` where the backend endpoint returns `Content-Disposition: attachment` — the browser handles the download via its normal mechanism. Learned the hard way in session 004 (TASK-014) when a FilePicker-based download approach was shipped, broke web mode, and had to be reverted (PR #18).
- **Native Flet desktop mode on WSLg needs `wslu`.** `mise run frontend` launches native Flet which uses GTK for `launch_url`. GTK's `gtk_show_uri` routes through the Wayland portal → `xdg_foreign` protocol, which WSLg's Weston compositor does not implement. Symptom: `Gdk-WARNING: Server is missing xdg_foreign support`, and URL launches (including download triggers) fail. **Host-side fix:** install the `wslu` package via the distro's package manager (provides `wslview`, a drop-in `xdg-open` replacement that routes to Windows browsers via WSL interop), then `export BROWSER=wslview` in `~/.bashrc` or equivalent. After that, `mise run frontend` downloads work via `wslview` → Windows default browser. This is a one-time host setup and is out of scope for the Python codebase. Canonical workaround: run in web mode at http://localhost:8080, which doesn't use GTK at all.
- **HTML/PDF render collapses newlines unless told not to.** WeasyPrint renders the Jinja2 invoice template as HTML, which collapses user-entered line breaks (and runs of whitespace) into single spaces by default. Any field in `backend/app/templates/invoice.html` that displays multi-line user text needs an explicit `white-space: pre-wrap;` CSS rule to preserve formatting. Use the CSS approach, not `<br>` injection — the template keeps `autoescape=True` and must stay injection-safe. Fixed for `.description-text` in session 005 (TASK-017, PR #21).
- **Window `docker logs` before reading it as "current".** These containers are long-lived — `tax-billing-backend` was *created* 2026-04-13 and merely *started* on later sessions, so a bare `docker logs` replays months of history and old, already-fixed tracebacks read as live failures. (TASK-007 hit exactly this: an April `invalid input value for enum payment_method: "E_TRANSFER"` error, fixed by TASK-016, surfacing in a September log dump.) Always pass `--since <date>` or `--tail` and say which window you looked at.
- Use [[wikilinks]] when cross-referencing project docs — see Project Map above.
