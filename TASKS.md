# Task Queue — tax-billing

> **Status key:** `pending` | `in_progress` | `blocked` | `complete`
> **Priority key:** `P0` (critical) | `P1` (high) | `P2` (medium) | `P3` (low)
> **Size key:** `S` (< 1 hour) | `M` (1-4 hours) | `L` (4+ hours)
> See [[PROJECT]] for architecture decisions and [[CLAUDE]] for conventions.

## Active Tasks

## Milestone 0: Workflow Scaffold [`complete`]

_All tasks complete. Details in Completed Tasks section below._

**Tag:** milestone-00-workflow-scaffold

---

## Milestone 1: Stop the Bleeding [`pending`]

The P0 fixes that make the codebase safe to work on. Every task in this
milestone addresses a latent bug, a security rule violation, or a footgun
discovered in the plenary audit.

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

### TASK-013: Make payments the source of truth for invoice status [`pending`] [`P1`] [`M`]
**Dependencies:** none
**Description:** Invoices can currently be marked `PAID` via `PATCH /v1/invoices/{id}/status` with no payment records existing, after which the Flet UI blocks both adding a payment and reverting the status — the invoice becomes permanently stuck in an inconsistent state. Root cause: `update_invoice_status` (`backend/app/routers/invoices.py` lines 135–145) performs an unconditional status assignment with no transition validation, and the Flet invoice view exposes a "Mark as Paid" button that drives that endpoint directly.

**Chosen approach:** **Option A — Payments are the source of truth.** The only path to `PAID` is a payment (or sum of payments) that satisfies the invoice total. The manual PATCH endpoint is restricted to the legal non-PAID transitions: `DRAFT → PENDING` (send), any → `CANCELLED`. The "Mark as Paid" button is removed from the Flet invoice view entirely. Options B (transition table with "Mark Unpaid") and C (auto-create payment modal) were considered and rejected in favor of the simpler model that matches how a sole-prop actually thinks about invoices.

**Files in scope:**
- `backend/app/routers/invoices.py` — rewrite `update_invoice_status` with an allowed-transition whitelist; explicitly reject any request that sets status to `PAID`
- `backend/app/schemas/invoice.py` — constrain `InvoiceStatusUpdate.status` to the allowed subset (exclude `PAID`) so the rejection happens at the pydantic boundary, not in the handler
- `backend/app/routers/payments.py` — verify the existing auto-transition to `PAID` on payment creation (lines 117–120) still fires correctly; no behavior change intended
- `frontend/` — locate and remove the "Mark as Paid" button from wherever it lives in the Flet invoice view (likely `frontend/views/invoices.py` or `frontend/views/invoice_detail.py`)
- Data audit: reconcile any existing invoice currently in the buggy state (`status=PAID` with `sum(payments) < total`) before dispatch — the current db has 2 invoices, 0 payments, so at least one may be affected

**Acceptance Criteria:**
- [ ] `PATCH /v1/invoices/{id}/status` returns 400 (or 422 from pydantic) when the target status is `PAID`, with a detail message: "Invoice status cannot be set to PAID manually — record a payment instead."
- [ ] `PATCH /v1/invoices/{id}/status` returns 400 for any transition not in the whitelist: `DRAFT → PENDING`, `DRAFT → CANCELLED`, `PENDING → CANCELLED`
- [ ] A valid `DRAFT → PENDING` transition (send invoice) still works end-to-end
- [ ] The Flet invoice view has no "Mark as Paid" button anywhere; status display is read-only and driven by backend state
- [ ] Recording a payment that satisfies the invoice total still auto-transitions the invoice to `PAID` (no regression on existing `routers/payments.py` lines 117–120 logic)
- [ ] Data audit completed: any invoice currently in the buggy state is reconciled manually (either by adding the real payment records that support the `PAID` status, or by PATCHing back to `PENDING`)
- [ ] Manual QA walkthrough: create invoice → send → attempt `curl -X PATCH .../status -d '{"status":"paid"}'` returns 400 → record payment via Flet UI → invoice auto-transitions to `PAID` → tax summary reflects the payment
- [ ] Regression test deferred to Milestone 2 with a note (no pytest infra yet — same deferral pattern as TASK-001). Add a line to TASK-011 or TASK-012 scope noting this endpoint needs coverage once test infra lands.

**Notes:**
- **Discovered 2026-04-13** (session 004) while user was verifying the tool post-backend-recovery. The `mark paid` button lured them into the broken state and the only escape was direct DB manipulation.
- **Sequencing suggestion:** dispatch this BEFORE TASK-003. TASK-013 is non-destructive (code + frontend only), so fixing it first lets the user audit and reconcile the 2 existing invoices against the real data. TASK-003 wipes the volume afterward, so post-TASK-003 the "2 invoices" audit is moot, but pre-TASK-003 you at least know what real state you're trying to preserve in the backup.
- **Auth note for Milestone 3 plenary:** the PATCH endpoint has no auth (fine for M1 since all endpoints are unauthenticated until M3), but the blast radius of an open status-mutation endpoint is worth flagging during the M3 plenary.
- **Data audit query:**
  ```sql
  SELECT i.id, i.status, i.total, COALESCE(SUM(p.amount), 0) AS paid
  FROM invoices i
  LEFT JOIN payments p ON p.invoice_id = i.id
  GROUP BY i.id
  HAVING i.status = 'paid' AND COALESCE(SUM(p.amount), 0) < i.total;
  ```
- **Dispatch mode:** standard (test-after). Pure logic is minimal; most of the work is a validation table + frontend button removal.

---

### TASK-007: Integration — Milestone 1 verification [`pending`] [`P0`] [`S`]
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-013
**Description:** End-to-end verification that Milestone 1 left the tool in a working state. Wiring audit per plenary checklist; ensures no orphaned new modules.
**Acceptance Criteria:**
- [ ] `docker compose down -v && docker compose up -d` rebuilds cleanly with new `.env`
- [ ] Backend `/health` returns 200 from `127.0.0.1`
- [ ] Frontend (host-mode `mise run desktop` for now) can load dashboard, create client, create invoice, record payment without crashing the auto-backup path
- [ ] Invoice status flow smoke-tested: direct PATCH to `PAID` rejected; payment-driven transition to `PAID` still works (TASK-013 regression check)
- [ ] Grep for any remaining hardcoded secrets / deprecations — all zero matches (excluding `.env.example` and `.git/`): `grep -rn --exclude=.env.example --exclude-dir=.git -E "postgres:postgres|change-this-secret|your-secret-key|utcnow" .`
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

### Milestone 0: Workflow Scaffold [`complete`]

**Completed:** 2026-04-10
**Tag:** `milestone-00-workflow-scaffold`
**PR:** #1 — `chore(workflow): plenary scaffold for tax-billing`

#### TASK-000: Workflow scaffolding [`complete`] [`P0`] [`M`]
**Owner:** director + documenter
**Dependencies:** none
**Description:** Author the plenary artifacts: `CLAUDE.md`, `PROJECT.md`, `TASKS.md`, `security-profile.yaml`, `.claude/settings.json`, `Handoffs/handoff-001.md`, and extend `.gitignore` for `.claude/worktrees/` and tighter secrets patterns. Non-destructive — no source code touched.
**Acceptance Criteria:**
- [x] `CLAUDE.md` present with stack, commands, project map, conventions, gotchas
- [x] `PROJECT.md` present with status, 9 architecture decisions, data model, milestones table
- [x] `TASKS.md` present with Milestones 0-1 fully decomposed; Milestones 2-7 sketched
- [x] `security-profile.yaml` present with L3 level and correct scope flags
- [x] `.claude/settings.json` present with allow-list for mise/ruff/mypy/pytest/pip/docker
- [x] `Handoffs/handoff-001.md` present, seeded from this session
- [x] `.gitignore` extended with `.claude/worktrees/` and tighter secrets patterns
- [x] All files committed on `chore/workflow-scaffold`, PR opened, user merges after review
**Notes:**
- Plenary audit (read-only) conducted by architect agent first; all findings converted into Milestone 1 tasks (TASK-001 through TASK-007).
- Reviewer (PR #1) requested 7 changes — 2 major, 5 minor — all addressed in fixup commit `b4f382d` before merge.
- Scaffold PR squash-merged as commit `f2bed4b` on main.

---

### Milestone 1: Stop the Bleeding (partial — session 003)

**Completed:** 2026-04-10
**PRs:** #4 — `fix(backup): TASK-001 + TASK-005`; #5 — `chore(security): TASK-002 + TASK-004`
**Remaining in milestone:** TASK-003, TASK-006, TASK-007 (next session)

#### TASK-001: Fix broken auto-backup crash path [`complete`] [`P0`] [`S`]
**Dependencies:** none
**Description:** `BackupService(db)` was called with a `db` arg the constructor did not accept, and `await backup_service.create_backup(backup_type="auto")` did not match the sync, arg-less method. First client or payment create would crash. Reconciled the caller signature with the service.
**Files in scope:**
- `backend/app/routers/clients.py` (3 call sites: lines 63, 112, 138)
- `backend/app/routers/payments.py` (2 call sites: lines 125, 221)
- `backend/app/routers/backup.py` (manual backup endpoint — db dep added)
- `backend/app/services/backup_service.py`
**Acceptance Criteria:**
- [x] `BackupService` constructor accepts `db: AsyncSession` — all 5 auto call sites and 2 manual call sites now consistent
- [x] `create_backup` is async and accepts `backup_type: Literal["auto", "manual"]`
- [x] `backup_logs` table is actually written to (was orphaned — ORM model existed but nothing wrote to it)
- [ ] Regression test: creating a client triggers a successful auto-backup without exception — **deferred to Milestone 2** (no test infra yet; TASK-007 integration covers manual verification)
- [ ] Manual QA: POST a client via `curl`, verify no 500 — **deferred to TASK-007**
**Notes:**
- Dispatched in standard mode (not TDD) because the fix was a refactor-to-match-callers, not behavior-spec-first.
- Reviewer flagged 3 major issues on first pass: (1) mid-request `db.commit()` breaking transaction ownership, (2) sync `subprocess.run` blocking the event loop inside `async def`, (3) stripped `os.environ` on subprocess env. All three fixed in commit `1f24665` before merge. The transaction-boundary issue was director-caused (the dispatch spec explicitly said `flush() + commit()`; reviewer correctly pushed back). Lesson: `get_db` owns the request transaction — services that live under it should `add() + flush()`, never commit.
- PR #4 squash-merged as `6f0b09b` on main.

#### TASK-002: Extract hardcoded credentials to .env [`complete`] [`P0`] [`M`]
**Dependencies:** none
**Description:** Every credential baked into `docker-compose.yml` and `backend/app/config.py` moved to `.env` refs. Fixed an L3 `rules/security.md` § No Hardcoded Secrets violation that had been live since the project's inception.
**Files in scope:**
- `docker-compose.yml` (env refs, env_file wiring, healthcheck parameterization)
- `backend/app/config.py` (removed defaults on `database_url` and `jwt_secret_key`)
- `.env.example` (added `POSTGRES_USER/PASSWORD/DB`; documented the compose variable-expansion gotcha)
- `README.md` (setup step + Environment Variables table tightened)
**Acceptance Criteria:**
- [x] `docker-compose.yml` uses `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}`, `${DATABASE_URL}`, `${JWT_SECRET_KEY}` — no literal values, no dangerous `:-...` fallback on secrets
- [x] `backend/app/config.py` has no default values containing real-looking credentials; pydantic-settings now fails fast at startup if `DATABASE_URL` or `JWT_SECRET_KEY` missing
- [x] `.env.example` documents every new variable with a comment and a placeholder; includes prominent pointer to `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [x] README updated: "Copy `.env.example` to `.env` and generate real values" step is explicit
- [ ] `docker compose up` still works with a fresh `.env` file — **deferred to TASK-007**
**Notes:**
- Healthcheck updated to `pg_isready -U ${POSTGRES_USER}` so it tracks whatever user the operator configures.
- `DEBUG` kept its `${DEBUG:-false}` fallback (not a secret, has matching default in `config.py`).
- Line endings on `docker-compose.yml` and `.env.example` flipped CRLF→LF during the edit. Repo has mixed line endings (no `.gitattributes`); LF is correct for a Linux/Docker project. Flag for a `.gitattributes` task if the drift becomes noisy.
- `config.py` has an unused `from typing import Optional` import — caught by reviewer, deferred to Milestone 2 ruff pass.
- PR #5 squash-merged as `d30b558` on main.

#### TASK-004: Bind backend to 127.0.0.1 (temporary) [`complete`] [`P0`] [`S`]
**Dependencies:** none
**Description:** Until auth lands in Milestone 3, the unauthenticated API must not be reachable from LAN. Bound all three services to 127.0.0.1. Temporary mitigation — removed in Milestone 7 when HTTPS + auth land.
**Files in scope:**
- `docker-compose.yml` (ports sections for `db`, `backend`, `frontend`)
**Acceptance Criteria:**
- [x] `backend` port mapping is `127.0.0.1:8000:8000`
- [x] `frontend` port mapping is `127.0.0.1:8080:8080`
- [x] `db` port mapping is `127.0.0.1:5433:5432`
- [x] Comment in compose file: `# Bound to 127.0.0.1 until auth lands (Milestone 3). See TASKS.md TASK-004.`
- [ ] `curl http://127.0.0.1:8000/health` works; `curl http://<LAN-IP>:8000/health` does not — **deferred to TASK-007**
**Notes:**
- Bundled into PR #5 with TASK-002 because both touched `docker-compose.yml`.

#### TASK-005: Fix datetime.utcnow() deprecations [`complete`] [`P1`] [`S`]
**Dependencies:** none
**Description:** Two `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)` per Python 3.12 guidance.
**Files in scope:**
- `backend/app/services/backup_service.py` (replaced during the TASK-001 rewrite of `create_backup`)
- `backend/app/services/tax_calculator.py` (line 176 — `get_tax_summary` timestamp)
**Acceptance Criteria:**
- [x] No `datetime.utcnow()` usage anywhere in `backend/`
- [x] `grep -rn "utcnow" backend/` returns no matches
- [x] Tax summary and backup log both still produce correct timestamps (same wall-clock semantics)
**Notes:**
- Bundled into PR #4 with TASK-001 because both touched `backup_service.py`.

---

## Discovered Work

_Tasks found during implementation that weren't in the original plan. User decides when/whether to promote these to Active Tasks._

- **`_get_db_params` fragile URL parsing** (session 003, PR #4 review) — `backend/app/services/backup_service.py::_get_db_params` splits `DATABASE_URL` by hand and crashes on passwords containing `:`, `@`, or `/`. Real passwords generated by `secrets.token_urlsafe(32)` are URL-safe, so this is latent, but TASK-003 introduces a new generated password so it could trip. Fix: use `urllib.parse.urlparse`. Proposed home: Milestone 6 (Dep Hygiene) or a new hardening task if TASK-003 surfaces a parse crash.
- **Backup file disk-leak on partial failure** (session 003, PR #4 review) — if pg_dump succeeds and the dump file is written but the `BackupLog` insert/flush fails, the `.sql` file stays on disk with no log row pointing at it. Soft leak. Fix: wrap in try/except and `unlink()` the file on log-insert failure. Proposed home: Milestone 6 hardening.
- **Line-ending drift / add `.gitattributes`** (session 003, PR #5) — repo has mixed CRLF/LF line endings. During TASK-002 edits, `docker-compose.yml` and `.env.example` flipped CRLF→LF, inflating diffs. Adding a `.gitattributes` with `* text=auto eol=lf` would normalize and prevent future churn. Small, cosmetic. Proposed home: Milestone 6 or a one-off chore before Milestone 2.
- **Unused `from typing import Optional` in `backend/app/config.py`** (session 003, PR #5 review) — will be caught by ruff in Milestone 2 (TASK-008); no action needed now.
- **Redundant `env_file: .env` on the `db` compose service** (session 003, PR #5 review, minor nit) — the `environment:` block already declares the `POSTGRES_*` vars via `${...}` substitution, so the `env_file:` line is redundant for its stated purpose. Also injects unrelated vars (JWT_SECRET_KEY, API_URL) into the postgres container environment, which is not a security hole but is slightly broader than necessary. Drop if revisiting compose in TASK-007 or later.
