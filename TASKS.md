# Task Queue — tax-billing

> **Status key:** `pending` | `in_progress` | `blocked` | `complete`
> **Priority key:** `P0` (critical) | `P1` (high) | `P2` (medium) | `P3` (low)
> **Size key:** `S` (< 1 hour) | `M` (1-4 hours) | `L` (4+ hours)
> See [[PROJECT]] for architecture decisions and [[CLAUDE]] for conventions.

## Active Tasks

## Milestone 0: Workflow Scaffold [`in_progress`]

### TASK-000: Workflow scaffolding [`in_progress`] [`P0`] [`M`]
**Owner:** director + documenter
**Dependencies:** none
**Description:** Author the plenary artifacts: `CLAUDE.md`, `PROJECT.md`, `TASKS.md`, `security-profile.yaml`, `.claude/settings.json`, `Handoffs/handoff-001.md`, and extend `.gitignore` for `.claude/worktrees/` and tighter secrets patterns. Non-destructive — no source code touched.
**Acceptance Criteria:**
- [ ] `CLAUDE.md` present with stack, commands, project map, conventions, gotchas
- [ ] `PROJECT.md` present with status, 9 architecture decisions, data model, milestones table
- [ ] `TASKS.md` present with Milestones 0-1 fully decomposed; Milestones 2-7 sketched
- [ ] `security-profile.yaml` present with L3 level and correct scope flags
- [ ] `.claude/settings.json` present with allow-list for mise/ruff/mypy/pytest/pip/docker
- [ ] `Handoffs/handoff-001.md` present, seeded from this session
- [ ] `.gitignore` extended with `.claude/worktrees/` and tighter secrets patterns
- [ ] All files committed on `chore/workflow-scaffold`, PR opened, user merges after review

---

## Milestone 1: Stop the Bleeding [`pending`]

The P0 fixes that make the codebase safe to work on. Every task in this
milestone addresses a latent bug, a security rule violation, or a footgun
discovered in the plenary audit.

### TASK-001: Fix broken auto-backup crash path [`pending`] [`P0`] [`S`]
**Dependencies:** none
**Description:** `BackupService(db)` is called with a `db` arg the constructor does not accept, and `await backup_service.create_backup(backup_type="auto")` does not match the current sync, arg-less method. First client or payment create crashes in production. Reconcile the caller signature with the service (plenary preference — don't delete the feature).
**Files in scope:**
- `backend/app/routers/clients.py` (3 call sites: lines 63, 112, 138)
- `backend/app/routers/payments.py` (2 call sites: lines 125, 221)
- `backend/app/services/backup_service.py`
**Acceptance Criteria:**
- [ ] `BackupService` constructor accepts the arguments its callers pass (or callers updated to match)
- [ ] `create_backup` is async and accepts `backup_type: Literal["auto", "manual"]`
- [ ] `backup_logs` table is actually written to (currently orphaned per plenary audit)
- [ ] Regression test: creating a client triggers a successful auto-backup without exception
- [ ] Manual QA: POST a client via `curl`, verify no 500
**Notes:**
- TDD-eligible. Tester first — interface spec is the reconciled BackupService signature.

---

### TASK-002: Extract hardcoded credentials to .env [`pending`] [`P0`] [`M`]
**Dependencies:** none
**Description:** Every credential currently baked into `docker-compose.yml` and `backend/app/config.py` moves to `.env` refs. Violates `rules/security.md` § No Hardcoded Secrets. Not an auth task — just stop shipping credentials in committed files.
**Files in scope:**
- `docker-compose.yml` (lines 8, 9, 31, 32)
- `backend/app/config.py` (lines 23, 27)
- `.env.example` (add any new required vars)
- `.env` (user updates locally, not committed)
**Acceptance Criteria:**
- [ ] `docker-compose.yml` uses `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}`, `${DATABASE_URL}` — no literal values
- [ ] `backend/app/config.py` has no default values containing real-looking credentials
- [ ] `.env.example` documents every new variable with a comment and a placeholder
- [ ] README updated: "Copy `.env.example` to `.env` and generate real values" step is explicit
- [ ] `docker compose up` still works with a fresh `.env` file
**Notes:**
- `JWT_SECRET_KEY` stays a placeholder until Milestone 3 — but generate one now anyway; cheap future-proofing.

---

### TASK-003: Generate strong secrets in .env [`pending`] [`P0`] [`S`]
**Dependencies:** TASK-002
**Description:** Populate the local `.env` with strong random values for `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`. Document the generation command in `.env.example` comments. This is local-only work — director will not touch the user's `.env`; the user will follow a command the task provides.
**Acceptance Criteria:**
- [ ] `.env.example` contains a commented generation command: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] User is prompted (in the task dispatch) to run that command and update their local `.env`
- [ ] `docker compose down -v && docker compose up -d` rebuilds the DB container with the new password
**Notes:**
- **Data loss event.** Because this wipes the `postgres_data` volume, user should export current data first if they've been using the tool. Director flags this in the task dispatch.

---

### TASK-004: Bind backend to 127.0.0.1 (temporary) [`pending`] [`P0`] [`S`]
**Dependencies:** none
**Description:** Until auth lands in Milestone 3, the unauthenticated API must not be reachable from the host network. Update `docker-compose.yml` to bind the backend and frontend ports to `127.0.0.1` only. Temporary mitigation — removed in Milestone 7 when HTTPS + auth land.
**Files in scope:**
- `docker-compose.yml` (ports sections for `backend` and `frontend`)
**Acceptance Criteria:**
- [ ] `backend` port mapping is `127.0.0.1:8000:8000`
- [ ] `frontend` port mapping is `127.0.0.1:8080:8080`
- [ ] `db` port mapping is `127.0.0.1:5433:5432` (already local-only — verify)
- [ ] Comment in compose file: `# Bound to 127.0.0.1 until auth lands (Milestone 3). See TASKS.md TASK-004.`
- [ ] `curl http://127.0.0.1:8000/health` works; `curl http://<LAN-IP>:8000/health` does not

---

### TASK-005: Fix datetime.utcnow() deprecations [`pending`] [`P1`] [`S`]
**Dependencies:** none
**Description:** Two remaining `datetime.utcnow()` calls survived the "deprecation fixes" commit. Replace with `datetime.now(timezone.utc)` per Python 3.12 guidance.
**Files in scope:**
- `backend/app/services/backup_service.py` (line 39)
- `backend/app/services/tax_calculator.py` (line 176)
**Acceptance Criteria:**
- [ ] No `datetime.utcnow()` usage anywhere in `backend/`
- [ ] `grep -rn "utcnow" backend/` returns no matches
- [ ] Tax summary and backup log both still produce correct timestamps

---

### TASK-006: Clean up stale root-owned backup files [`pending`] [`P2`] [`S`]
**Dependencies:** none
**Description:** The `backups/` directory contains 8 stale `.json` files owned by `root` from a previous backup implementation. Current code produces `.sql`, so these files are dead artifacts. Removing them requires `sudo` because they were written by the containerized backend's root user via bind mount.
**Files in scope:**
- `backups/*.json`
**Acceptance Criteria:**
- [ ] `backups/` is empty of stale artifacts
- [ ] A note in CLAUDE.md § Gotchas about the `root`-ownership footgun (already present — verify)
**Notes:**
- Director dispatches this as a user-prompted step: provides the `sudo rm` command, user runs it, task marked complete. Agents do not run sudo.

---

### TASK-007: Integration — Milestone 1 verification [`pending`] [`P0`] [`S`]
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006
**Description:** End-to-end verification that Milestone 1 left the tool in a working state. Wiring audit per plenary checklist; ensures no orphaned new modules.
**Acceptance Criteria:**
- [ ] `docker compose down -v && docker compose up -d` rebuilds cleanly with new `.env`
- [ ] Backend `/health` returns 200 from `127.0.0.1`
- [ ] Frontend (host-mode `mise run desktop` for now) can load dashboard, create client, create invoice, record payment without crashing the auto-backup path
- [ ] Grep for any remaining `postgres:postgres`, `change-this-secret`, `utcnow` — all zero
- [ ] Milestone 1 tag created: `milestone-01-stop-the-bleeding`

---

## Milestone 2: Quality Gates [`pending`]

Introduces the tools that make every subsequent milestone safer: `pyproject.toml`, ruff, mypy, pytest. First real tests land here, starting TDD on `tax_calculator.py`. Vertical-slice smoke test lands here — it is the tool's first "boots and runs" check.

### TASK-008: Introduce pyproject.toml and ruff [`pending`] [`P1`] [`M`]
**Description:** Migrate `backend/requirements.txt` to `pyproject.toml`. Configure ruff (lint + format). Frontend stays on `requirements.txt` until Milestone 6.
**Acceptance Criteria:**
- [ ] `backend/pyproject.toml` exists with dependencies matching current `requirements.txt` (pinned versions)
- [ ] `ruff` config in `pyproject.toml` under `[tool.ruff]`
- [ ] `ruff check backend/` passes (fix or ignore as needed, documenting ignores)
- [ ] `ruff format backend/` applied in a separate commit from the config commit
- [ ] `mise run lint` task added
- [ ] `.claude/settings.json` allow-list updated for `ruff` commands

### TASK-009: Introduce mypy (strict on services/) [`pending`] [`P1`] [`M`]
**Description:** Configure mypy with strict mode on `backend/app/services/` and lenient elsewhere. Fix any type errors that surface in the strict section.
**Acceptance Criteria:**
- [ ] `[tool.mypy]` config in `backend/pyproject.toml`
- [ ] `mypy backend/app/services/` passes clean
- [ ] `mypy backend/app/` (non-services) passes with documented ignore patterns
- [ ] `mise run typecheck` task added

### TASK-010: Introduce pytest + pytest-asyncio [`pending`] [`P1`] [`M`]
**Description:** Configure pytest + pytest-asyncio. Create `backend/tests/` directory with conftest.py. Do not write `tax_calculator` tests here — that is TDD work in TASK-011.
**Acceptance Criteria:**
- [ ] `[tool.pytest.ini_options]` in `backend/pyproject.toml`
- [ ] `backend/tests/` directory with `conftest.py` (async event loop fixture)
- [ ] `mise run test` task added
- [ ] `pytest` runs green on an empty test suite (placeholder test passes)

### TASK-011: TDD tax_calculator.py [`pending`] [`P0`] [`L`]
**Dependencies:** TASK-010
**Description:** Write comprehensive failing tests for `backend/app/services/tax_calculator.py` covering progressive bracket math, HST holdback, income tax holdback, YTD annualization, and edge cases (zero income, single-bracket income, income spanning all brackets, unknown province → ValueError). Then dispatch implementer in TDD mode to make tests pass with minimal changes. Purpose: lock in correct behavior before any subsequent refactor.
**Acceptance Criteria:**
- [ ] `backend/tests/services/test_tax_calculator.py` exists with ≥ 20 tests covering the above
- [ ] All tests pass against the current `tax_calculator.py` (or surface real bugs that become fix tasks)
- [ ] `tax_calculator.py` has no behavior change unless a test revealed a bug
- [ ] `pytest-cov` coverage of `tax_calculator.py` ≥ 90%
**Notes:**
- `pytest-cov` is a new dev dep; requires the standard dep proposal.
- Dispatch mode: TDD (tester-first). Interface spec = existing public methods on `TaxCalculatorService`.

### TASK-012: Vertical-slice smoke test [`pending`] [`P0`] [`M`]
**Dependencies:** TASK-010, TASK-001
**Description:** Implement the smoke test referenced in the plenary checklist. One input → one output, end-to-end, hitting every layer: `POST /v1/clients` → `POST /v1/invoices` → `POST /v1/payments` → `GET /v1/tax/summary`. Verify each step and that the tax summary reflects the payment.
**Acceptance Criteria:**
- [ ] `backend/tests/test_vertical_slice.py` runs the full flow against a live test DB (pytest-asyncio + httpx test client)
- [ ] Test uses a disposable SQLite-in-memory DB OR a dedicated test Postgres schema (decide during task)
- [ ] Smoke test command documented in `CLAUDE.md` Commands section
- [ ] `mise run smoke` task added
- [ ] Test passes from a freshly-seeded DB

---

## Milestone 3: Auth (L3 core work) [`pending`]

Single-user JWT auth. One admin, passlib/bcrypt, python-jose, Bearer tokens. Harden `POST /v1/backup/restore`. Remove the 127.0.0.1 bind from Milestone 1. **A focused plenary happens at the start of this milestone** to nail down: token lifetime, refresh strategy (or none), password reset (probably none), Flet login view UX.

_Tasks sketched; final decomposition at Milestone 3 plenary._

- Create `admin_users` table (final DDL change before Alembic — plan carefully)
- Hash password via `passlib[bcrypt]` at bootstrap time
- `/v1/auth/login` endpoint, returns JWT
- `get_current_user` dependency, applied to every `/v1/*` router except `/health`, `/v1/auth/login`
- Flet login view + token storage in the API client
- Harden `POST /v1/backup/restore`: file size limit, content-type check, SQL pre-flight validation, auth-required
- Remove `127.0.0.1` bind from `docker-compose.yml` (TASK-004 inverse)
- Milestone 3 tag: `milestone-03-auth`

---

## Milestone 4: Migrations [`pending`]

Adopt Alembic. Convert `database/schema.sql` into an initial migration. Drop the compose init-volume approach. Document the migration workflow.

_Tasks sketched; final decomposition at Milestone 4 plenary._

- `alembic init backend/migrations`
- Initial migration = the current schema (autogenerate from ORM models OR translate `schema.sql` directly — decide at plenary)
- Backfill seed data as a data migration OR keep as a separate script
- Remove `database/schema.sql` mount from `docker-compose.yml`
- Backend container runs `alembic upgrade head` on startup
- `mise run migrate` task
- Milestone 4 tag: `milestone-04-migrations`

---

## Milestone 5: Containerize Frontend (canonical path) [`pending`]

Make containerized Flet web the canonical run mode. Keep desktop mode as `mise run desktop` for dev convenience.

_Tasks sketched; final decomposition at Milestone 5 plenary._

- `frontend/Dockerfile` reviewed for Flet web mode
- `docker-compose.yml` frontend service wired into a new `mise run up-all` task
- Rename `mise run frontend` → `mise run desktop`; update README
- CORS allowlist updated in backend (`http://localhost:8080` stays; remove aspirational `localhost:3000`)
- Flet web reachable at `http://localhost:8080`
- Milestone 5 tag: `milestone-05-frontend-container`

---

## Milestone 6: Dependency Hygiene [`pending`]

With auth landed and quality gates enforced, remove the cargo-culted deps we now know we don't need. This is ONLY removals — always welcome per `rules/dependencies.md`.

_Tasks sketched; final decomposition at Milestone 6 plenary._

- Remove `httpx` from backend deps (backend makes no outbound HTTP)
- Remove `psycopg2-binary` (we use asyncpg)
- Keep `alembic` (Milestone 4), `python-jose` + `passlib` (Milestone 3)
- `mise run lint` still passes; no imports broken
- Frontend tier audited separately
- Milestone 6 tag: `milestone-06-dep-hygiene`

---

## Milestone 7: Network Exposure [`pending`]

Pick an exposure model and ship it. Final hardening before the tool can be used off a trusted machine.

_Tasks sketched; final decomposition at Milestone 7 plenary._

- Decide: tailnet vs. LAN-only + self-signed vs. reverse-proxy (Caddy/Traefik) + Let's Encrypt
- Add reverse proxy container if applicable
- HTTPS enforced (HSTS header)
- Security headers: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- CORS allowlist finalized to the real frontend origin
- Rate limiting on `/v1/auth/login` (brute-force protection)
- `/security-audit` full pass against L3 checklist — zero high-severity findings
- Milestone 7 tag: `milestone-07-network-exposure`

---

## Completed Tasks

_Empty. First milestone tag arrives when Milestone 0 closes._

---

## Discovered Work

_Tasks found during implementation that weren't in the original plan. User decides when/whether to promote these to Active Tasks._

- None yet.
