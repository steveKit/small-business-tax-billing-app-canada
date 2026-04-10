# tax-billing

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
- [[TASKS]] — work queue with priorities and acceptance criteria
- [[README]] — user-facing setup and usage
- [[Handoffs/]] — session continuity directory (latest: [[Handoffs/handoff-001]])
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
└── Handoffs/
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

- **TDD (test-first):** `backend/app/services/tax_calculator.py` — pure math, clear contracts, the one place a silent bug costs the user real money. Interface is specified before implementation; tests drive the shape.
- **TDD (test-first):** pydantic validators and any future pure-logic helpers.
- **Test-after:** routers, database integration, `backup_service.py`, `invoice_pdf.py`, Flet views.
- **Skip (for now):** end-to-end browser tests of the Flet web UI. Revisit if the tool grows beyond personal use.
- **Coverage target:** not a metric we chase. Every bug fix adds a regression test; every new pure-logic function has tests before it's merged.

## Secrets & Environment

- **Secrets file format:** `.env` (dotenv), consumed by `pydantic-settings` in `backend/app/config.py` and by `docker-compose.yml` via `${VAR}` refs.
- **Example file:** `.env.example` — documents every required variable with a placeholder. Agents read ONLY this file, never the real `.env`.
- **Milestone 1 extracts** all currently-hardcoded credentials from `docker-compose.yml` and `config.py` defaults into `.env` refs. Do not fix these ad-hoc — follow the milestone tasks.
- **Never commit `.env`.** Gitignored at project root. Never has been committed (verified in plenary audit).

## Convention Overrides

None at plenary time. If the project diverges from global standards in the future, record the decision here with a rationale.

| Area | Global Standard | This Project | Rationale |
|------|----------------|--------------|-----------|

## Gotchas

- **Schema is applied via compose init-volume, not migrations.** `database/schema.sql` is mounted at `/docker-entrypoint-initdb.d/` and runs exactly once on first volume creation. Any schema change requires `docker compose down -v` and wipes all data. Alembic migrations arrive in Milestone 4 — do not add ad-hoc DDL before then.
- **Host port 5433 → container 5432.** Intentional, to avoid colliding with a host Postgres. Connect externally on 5433, but the backend inside the compose network still talks to `db:5432`.
- **`backups/` is bind-mounted and root-owned.** The container writes backup files as root onto the host volume, so `horse` cannot delete them without `sudo`. There are stale `.json` files from a previous backup implementation that TASK-006 will clean up.
- **Auto-backup code path is currently broken.** `BackupService(db)` is called with a `db` arg the constructor does not accept, and `create_backup(backup_type="auto")` does not match the current method signature. First client or payment create will crash. TASK-001 fixes this.
- **Cargo-culted dependencies.** `alembic`, `python-jose`, `passlib`, `httpx` (backend), and `psycopg2-binary` are declared in `backend/requirements.txt` but not yet used. `passlib` and `python-jose` become real in Milestone 3 (auth). The rest get trimmed in Milestone 6 after auth lands, so we know which stay.
- **Frontend name is a lie.** `frontend/` contains Python, not JavaScript. It is a Flet (Flutter) desktop/web client. Do not look for React or a build step.
- Use [[wikilinks]] when cross-referencing project docs — see Project Map above.
