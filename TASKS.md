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

### TASK-007: Integration — Milestone 1 verification [`pending`] [`P0`] [`S`]
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-013, TASK-015, TASK-016
**Description:** End-to-end verification that Milestone 1 left the tool in a working state. Wiring audit per plenary checklist; ensures no orphaned new modules.
**Acceptance Criteria:**
- [ ] `docker compose down -v && docker compose up -d` rebuilds cleanly with new `.env`
- [ ] Backend `/health` returns 200 from `127.0.0.1`
- [ ] Frontend (host-mode `mise run desktop` for now) can load dashboard, create client, create invoice, record payment without crashing the auto-backup path
- [ ] Invoice status flow smoke-tested: direct PATCH to `PAID` rejected; payment-driven transition to `PAID` still works (TASK-013 regression check)
- [ ] Invoice numbering smoke-tested: new invoice for Adamson lands as `2026-Adamson-NNN`; new invoice for BEE lands as `2026-BEE-NNN`; existing 3 rows migrated (TASK-015 regression check)
- [ ] Payment creation smoke-tested: `POST /v1/payments` with a live `payment_method` value returns 201 (TASK-016 regression check)
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

### Milestone 1: Stop the Bleeding (partial — session 004)

**Completed:** 2026-04-13
**PRs:** #10 — `feat(invoices): TASK-013 — payments as source of truth for invoice status`; #12 — `feat(invoices): TASK-015 — per-client invoice numbering`; #14 — `fix(models): TASK-016 — PaymentMethod enum values_callable (P0 hotfix)`; #16 — `feat(frontend): TASK-014 — FilePicker save for PDF and backup downloads`
**Remaining in milestone:** TASK-003, TASK-006, TASK-007 (session 005+)

#### TASK-013: Make payments the source of truth for invoice status [`complete`] [`P1`] [`M`]
**Dependencies:** none
**Description:** Invoices could be marked `PAID` via `PATCH /v1/invoices/{id}/status` with no payment records existing, leaving them permanently stuck in an inconsistent state — the Flet UI blocked both adding a payment and reverting the status. Root cause: `update_invoice_status` performed an unconditional status assignment with no transition validation, and the Flet invoice view exposed a "Mark as Paid" button that drove that endpoint directly.

**Chosen approach:** Option A — payments are the source of truth. The only path to `PAID` is a payment (or sum of payments) that satisfies the invoice total. Manual PATCH is restricted to legal non-PAID transitions (DRAFT→PENDING, DRAFT→CANCELLED, PENDING→CANCELLED). The "Mark as Paid" button is removed from the Flet invoice view entirely.

**Files in scope (changed):**
- `backend/app/routers/invoices.py` — added `ALLOWED_STATUS_TRANSITIONS` whitelist; rewrote `update_invoice_status` with transition check; added handler docstring explaining the 422/400 error contract (post-review fixup)
- `backend/app/schemas/invoice.py` — constrained `InvoiceStatusUpdate.status` to `Literal[InvoiceStatus.PENDING, InvoiceStatus.CANCELLED]` (defense in depth)
- `frontend/views/invoices.py` — removed the "Mark as Paid" `IconButton`

**Acceptance Criteria:**
- [x] `PATCH /v1/invoices/{id}/status` rejects target=`PAID`: 422 from pydantic `Literal` rejection (request-boundary), with a PAID-specific 400 branch in the handler for programmatic bypass (`"Invoice status cannot be set to PAID manually — record a payment instead."`). Verified via curl.
- [x] `PATCH /v1/invoices/{id}/status` returns 400 for illegal transitions not in the whitelist — verified via curl on `PENDING → PENDING`.
- [ ] Valid `DRAFT → PENDING` transition still works end-to-end — **not live-tested** (would have mutated the real BEE draft). Static analysis + reviewer's full code trace confirm; live regression deferred to Milestone 2 pytest infra.
- [x] The Flet invoice view has no "Mark as Paid" button anywhere — verified via grep.
- [ ] Recording a payment that satisfies the invoice total still auto-transitions to `PAID` — **not live-tested** (would have required recording a real payment on a real invoice). `routers/payments.py` lines 117–120 unchanged; reviewer traced the path and confirmed no regressions. Live verification deferred to Milestone 2 and to the user's natural post-merge workflow (recording the real Adamson payments).
- [x] Data audit + reconciliation: the 2 stuck Adamson invoices (INV-2026-0001, INV-2026-0002) were reconciled from `paid` to `pending` via a transactional SQL UPDATE pre-dispatch, with `pg_dump` backups captured at `~/tax-billing-backup-20260413-111707.sql` (pre-reconcile) and `~/tax-billing-backup-20260413-115039.sql` (post-reconcile).
- [ ] Full manual QA walkthrough (create → send → PATCH rejection → record payment → auto-transition → tax summary) — **partial**. The curl rejection portion was verified. The payment-recording → auto-transition → tax summary portion is deferred to the user's natural post-merge workflow.
- [x] Regression test deferred to Milestone 2 with a note (same pattern as TASK-001).

**Notes:**
- **Discovered 2026-04-13** (session 004) while the user was verifying the tool post-backend-recovery. The "Mark as Paid" button lured the user into the broken state and the only escape was direct DB manipulation.
- **Reviewer findings (PR #10):**
  - #1 (minor — misleading "Use payment operations to change PAID state" text appended to every non-PAID rejection) — **fixed** in fixup commit `a99a9b6`: trailing sentence dropped from the generic-rejection branch.
  - #2 (minor — undocumented 422/400 error contract) — **fixed** in fixup commit `a99a9b6`: handler docstring added explaining the defense-in-depth split.
  - #3 (minor — whitelist narrowness: no PAID→CANCELLED refund path) — **intentionally not fixed**. Matches Canadian sole-prop accounting practice (credit notes / negative-payment refunds, never a direct cancel of a paid invoice). Current refund path: delete payments → auto-reverts `PAID→PENDING` via `routers/payments.py` → manual PATCH `PENDING→CANCELLED`. User confirmed acceptance.
- **Defense in depth** — the `Literal[PENDING, CANCELLED]` schema constraint and the handler `ALLOWED_STATUS_TRANSITIONS` check are genuinely layered, not redundant. Schema catches target=`PAID` at request parse time (422); handler catches source-state rules the schema cannot express (`PENDING→PENDING`, anything from `CANCELLED` or `PAID`, etc.) with 400. Split is documented in the handler docstring.
- **Pre-dispatch data reconciliation** — before dispatching the implementer, the director ran a transactional SQL `UPDATE` to mark the 2 bugged Adamson invoices as `pending`. User intends to record the real payments via the normal UI flow post-merge; those will re-transition the invoices to `PAID` via the existing `routers/payments.py` auto-transition logic.
- **Stale CLAUDE.md gotcha discovered** — TASK-013's implementer noticed the "Auto-backup code path is currently broken" bullet in CLAUDE.md § Gotchas is stale; TASK-001 fixed the code path but the doc was never updated. Logged in Discovered Work below for a separate docs PR.
- **PR #10** squash-merged as `5a44a4e` on main.

#### TASK-015: Per-client invoice numbering `{year}-{client_slug}-{seq}` [`complete`] [`P1`] [`M`]
**Dependencies:** none (preceded by a fresh `pg_dump` backup per spec)
**Description:** Switched invoice-number format from global-per-year (`INV-2026-0001`) to per-client-per-year (`{year}-{client_slug}-{seq:03d}`), and migrated the 3 existing rows in the live db to the new format in the same flow.

**Chosen approach:** Slug rule (a) — first whitespace-delimited word of `clients.name`, ASCII alphanumeric only, case preserved (e.g. `"Adamson Systems Engineering"` → `"Adamson"`, `"BEE"` → `"BEE"`). Rule (c) (explicit `clients.short_name` column) was rejected to avoid pre-Alembic DDL work.

**Files in scope (changed):**
- `backend/app/routers/invoices.py` — one file. Three edits: (1) added `_slug_client_name` helper with docstring, examples, and ASCII-alphanumeric filter; (2) rewrote `generate_invoice_number` signature to `(db, year, client_id, client_name)`, scoped count query on both `year_billed` and `client_id`, changed format string to `f"{year}-{slug}-{count + 1:03d}"`, added docstring documenting the race condition; (3) updated the call site in `create_invoice` to pass `client.id` and `client.name` from the already-loaded client local.

**Acceptance Criteria:**
- [x] `_slug_client_name` helper present with docstring, examples, and error handling (ValueError on empty/non-alphanumeric-only inputs)
- [x] `generate_invoice_number` rewritten with per-client-per-year scoping and new format string
- [x] Existing 3 invoices migrated via transactional SQL UPDATE against the live db:
  - `INV-2026-0001` → `2026-Adamson-001`
  - `INV-2026-0002` → `2026-Adamson-002`
  - `INV-2026-0003` → `2026-BEE-001`
- [x] Post-migration API response (`GET /v1/invoices`) shows new `invoice_number` values for all 3 rows — verified via curl
- [x] Manual QA: new Adamson invoice lands as `2026-Adamson-003` — verified live via `curl POST /v1/invoices` (test invoice subsequently deleted by user)
- [x] Manual QA: new BEE invoice lands as `2026-BEE-002` — verified live via `curl POST /v1/invoices` (test invoice subsequently deleted by user)
- [x] `grep -rn "INV-" backend/app/routers/` returns zero matches in the rewritten generator
- [ ] PDF filename format for migrated invoices — **not live-tested** (the PDF download button is broken on this session's WSLg config; see TASK-014). Static reasoning: the PDF filename format (`Invoice-{invoice_number}.pdf`) is unchanged and the reviewer traced its consumers (`services/invoice_pdf.py`, `templates/invoice.html`) and confirmed they treat `invoice_number` as opaque. Safe by construction.
- [x] Regression test deferred to Milestone 2 (same pattern as TASK-001, TASK-013)

**Notes:**
- **Discovered 2026-04-13** (session 004) after the user pulled the 3 existing PDFs via curl and decided the global-per-year scheme was harder to reference than a per-client sequence. First word "Adamson" / "BEE" suffices for the current client roster.
- **Reviewer findings (PR #12):**
  - Finding #1 (minor — slug collision across clients, e.g. "Adamson Systems" vs "Adamson Foundation") — **intentionally not fixed**. UNIQUE constraint on `invoice_number` surfaces any collision as a 500 rather than silent overwrite, so the failure mode is loud. Logged in Discovered Work for M4+ revisit if it surfaces in real data.
  - Finding #2 (minor — M2 test plan coverage) — added as a scope note here to carry into TASK-011 / TASK-012 decomposition.
  - Finding #3 (minor — migration audit trail in PR body) — addressed by updating PR #12 body with the post-migration `SELECT` output mid-review.
- **Race condition inherited** — `generate_invoice_number` uses count-then-insert with no row lock; the handler docstring explicitly names this and points at a Milestone 6 hardening task.
- **Pre-dispatch backup** — `~/tax-billing-backup-20260413-115039.sql` (27 KB, complete) captured before the data migration; restorable via `cat <file> | docker exec -i tax-billing-db psql -U postgres -d tax_billing`.
- **Test invoices cleanup** — the 2 verification test invoices (Adamson-003 and BEE-002 with $0.01 totals) were created live during the director's post-implementer verification, then deleted by the user via `docker exec psql` after the safety hook correctly blocked the director from running destructive SQL.
- **PR #12** squash-merged as `bd38aed` on main.
- **M2 test backlog note (from reviewer finding #2):** when pytest infra lands in TASK-010, the `_slug_client_name` helper wants unit-test coverage for: empty string, whitespace-only, punctuation-only first word, non-ASCII-only first word ("日本"), leading-whitespace input, case preservation, digit-containing slug ("BEE2 Corp"), and a full "O'Reilly & Sons" happy path. Add to TASK-011 or TASK-012 decomposition when M2 opens.

#### TASK-016: Fix PaymentMethod enum serialization (P0 hotfix) [`complete`] [`P0`] [`S`]
**Dependencies:** none (P0 blocker)
**Description:** Latent bug that had been in the codebase since project inception: SQLAlchemy was serializing `PaymentMethod.E_TRANSFER` as the member NAME (`'E_TRANSFER'`) instead of its VALUE (`'e_transfer'`) because the `Enum(...)` column on `Payment.payment_method` was missing `values_callable`. Postgres's `payment_method` enum only accepts the lowercase values, so every payment creation was returning 500 with `asyncpg.exceptions.InvalidTextRepresentationError`.

**Why latent until session 004:** Payments count had been 0 for the entire project's life — no payment had ever successfully inserted. The buggy "Mark as Paid" button (removed in TASK-013) bypassed payment creation by PATCHing invoice status directly. TASK-013 forcing payment-driven transitions surfaced the bug on the very first real payment attempt.

**Fix:** One-line port of the already-correct `Invoice.status` pattern (`backend/app/models/invoice.py` lines 50–59) to `Payment.payment_method`. Added `values_callable=lambda obj: [e.value for e in obj]` to the `Enum(...)` column.

**Files in scope (changed):**
- `backend/app/models/payment.py` — one file, +6/-1 lines. Multi-line reformatting of the `Enum(...)` call to match the `Invoice.status` style exactly.

**Acceptance Criteria:**
- [x] `Payment.payment_method` column has `values_callable=lambda obj: [e.value for e in obj]`, matching the `Invoice.status` pattern exactly
- [x] `POST /v1/payments` with `"payment_method": "e_transfer"` returns 201 — verified live via curl (response shows lowercase `"e_transfer"`)
- [x] Second enum value tested: `"payment_method": "bank_transfer"` also returns 201 — verified live via curl
- [x] Invoice auto-transition boundary verified: 2 × $0.01 payments on a $10,170 invoice correctly kept the invoice in `pending` (transition to `paid` fires only when sum ≥ total, as designed)
- [x] Grep audit of `backend/app/models/` completed: only two ORM Enum columns exist (`Invoice.status` already correct; `Payment.payment_method` fixed by this PR). No other latent enum serialization bugs in the models layer.
- [x] Regression test deferred to Milestone 2 (same pattern as TASK-001, TASK-013, TASK-015)

**Notes:**
- **Discovered 2026-04-13** (session 004) when the user tried to record the real Adamson payments to close TASK-013's reconciliation loop. The 500 error surfaced a bug that had been sitting latently since project inception. Fastest discovery-to-merge cycle of the session: diagnosis → dispatch → verification → PR → merge in under 30 minutes.
- **Full round-trip verification:** Director created 2 test payments (\$0.01 each, `e_transfer` and `bank_transfer`), verified 201 + correct response, DELETEd both via `/v1/payments/{id}`, verified 204, and re-queried the live db to confirm 0 payments + 2 pending invoices unchanged. No residual test data, no SQL cleanup needed.
- **Side effect observed:** Each successful payment creation triggered `BackupService.create_backup('auto')` per `routers/payments.py` lines 125–126, writing two `.sql` backup files to the bind-mounted `backups/` directory. Harmless (correct TASK-001 behavior) and left in place for user management; will be swept up by TASK-006's cleanup pass.
- **Fast-tracked** per the user's "A" response on review option. Rationale: one-line port of a known-good pattern, full live round-trip verification, P0 blocker, director's grep audit confirmed no sibling bugs. No independent reviewer dispatch.
- **Stale CLAUDE.md gotcha also applies to the PaymentMethod situation** — the current Gotchas list notes "Auto-backup code path is currently broken" (TASK-001 already fixed this). Separately, the PaymentMethod/values_callable trap is worth a new Gotcha line warning future developers. Flag for the stale-gotcha cleanup PR already logged in Discovered Work.
- **PR #14** squash-merged as `673e4d0` on main.

#### TASK-014: Replace `launch_url` with `FilePicker.save_file` for PDF and backup downloads [`complete`] [`P1`] [`M`]
**Dependencies:** none
**Description:** Replaced `page.launch_url(url)` with `ft.FilePicker.save_file()` in two Flet download buttons (invoice PDF + database backup). The original code routed through GTK's `gtk_show_uri` → Wayland desktop portal → `xdg_foreign` protocol for window parenting, which WSLg's Weston compositor does not implement — every click produced `Gdk-WARNING: Server is missing xdg_foreign support` and the launch was unreliable. The new code fetches bytes from the backend and uses the native `save_file` dialog, making "Download" match the button label and working identically on all platforms.

**Files in scope (changed):**
- `frontend/services/api_client.py` — added `get_backup_download() -> tuple[bytes, str]` method that fetches bytes and parses the `Content-Disposition` header to extract a suggested filename (falls back to `"backup.sql"` if header is missing). Cheap string parser; no cgi/email.message imports.
- `frontend/views/invoices.py` — added `pdf_file_picker = ft.FilePicker()` at top of `build()`, placed as first item in content Column; rewrote `download_pdf` to look up `invoice_number` from `self.invoices`, invoke `pdf_file_picker.save_file(...)` with a closure-based callback that fetches bytes via `api.get_invoice_pdf()` and writes them; added `from pathlib import Path`; token-sentinel guard via `pdf_file_picker.data` (fixup) to prevent rapid-double-click callback races; success toast uses `Path(e.path).name` (fixup) to show the filename the user actually picked.
- `frontend/views/settings.py` — added a second `backup_file_picker` (the existing restore `file_picker` left untouched); rewrote `download_backup` to fetch bytes once via `api.get_backup_download()`, then invoke `backup_file_picker.save_file(...)` with a closure-captured `sql_bytes`. Single-fetch pattern avoids double-invoking `pg_dump` on the backend.

**Acceptance Criteria:**
- [x] "Download PDF" button no longer calls `launch_url` (grep confirmed zero call sites)
- [x] Clicking the PDF button invokes `ft.FilePicker.save_file()` with a default filename derived from the invoice number (e.g. `Invoice-2026-Adamson-001.pdf`) — verified via AST + diff read
- [x] `get_backup_download` method added with `Content-Disposition` parsing and safe fallback
- [x] Settings view's backup-download button fixed the same way (second `FilePicker` instance; existing restore picker untouched)
- [x] Platform-agnostic — uses only `open()`, `httpx`, and `ft.FilePicker`; no Linux/WSLg-specific code
- [x] `docker compose restart frontend` succeeds with no new errors; imports for `APIClient`, `InvoicesView`, and `SettingsView` all load cleanly — verified live
- [ ] Manual QA: download a real invoice PDF via the button; verify the file opens in a PDF viewer — **deferred to user** (director cannot click buttons in Flet; acceptance criterion passes once user confirms post-merge)
- [ ] Same manual QA for backup download — **deferred to user**
- [x] Regression test deferred to Milestone 2 (same pattern as TASK-001, TASK-013, TASK-015, TASK-016)

**Notes:**
- **Discovered 2026-04-13** (session 004) when the user first tried to download PDFs and hit the xdg_foreign warning. Session workaround was curl directly against `http://127.0.0.1:8000/v1/invoices/{id}/pdf` → files saved at `/home/horse/tax-billing-invoices/`.
- **Reviewer findings (PR #16):**
  - #1 (minor — callback race on rapid double-click) — **fixed** in fixup commit `ba3f864`: added `my_token = object()` sentinel on `pdf_file_picker.data`, stale-check as first line of `on_save_result`. Not a realistic failure mode for a single-user tool but the fix is 4 lines and eliminates the class.
  - #2 (minor — `Content-Disposition` parser coupling anchor) — **fixed** in fixup commit: expanded comment above the parser to reference `backend/app/routers/backup.py:21` so a future backend change flags the frontend parser via grep.
  - #5 (minor — success toast showed suggested filename not actual) — **fixed** in fixup commit: added `from pathlib import Path`, changed toast to use `Path(e.path).name`.
  - #3 (minor — eager backup fetch orphans a `pg_dump` snapshot when user cancels) — **intentionally not fixed**. Requires backend changes to `backup_service.py` to stream without persisting via the HTTP endpoint; out of scope for a frontend-only PR. Logged in Discovered Work.
  - #4 (minor — FilePicker `page.overlay` migration) — **intentionally not fixed**. Would touch 3 FilePickers including the existing restore picker which works empirically; risk of regressing restore > benefit of canonical placement. Logged in Discovered Work as a follow-up consistency task.
- **Defense in depth on the callback race:** `download_backup` does NOT need the token guard because `sql_bytes` is captured in the closure BEFORE `save_file()` is invoked. Each backup callback owns its own bytes.
- **Not blocking TASK-007 integration verification.** User had a curl workaround all session. TASK-014 is P1 "fix the UX" not P0 "restore a broken flow".
- **Alternative considered and rejected:** `apt install wslu` + `export BROWSER=wslview` as a host-side workaround. Rejected because it only helps WSLg users, doesn't live in version control, and every new Windows dev environment would need the same incantation.
- **PR #16** squash-merged as `379e6be` on main.

---

## Discovered Work

_Tasks found during implementation that weren't in the original plan. User decides when/whether to promote these to Active Tasks._

- **`_get_db_params` fragile URL parsing** (session 003, PR #4 review) — `backend/app/services/backup_service.py::_get_db_params` splits `DATABASE_URL` by hand and crashes on passwords containing `:`, `@`, or `/`. Real passwords generated by `secrets.token_urlsafe(32)` are URL-safe, so this is latent, but TASK-003 introduces a new generated password so it could trip. Fix: use `urllib.parse.urlparse`. Proposed home: Milestone 6 (Dep Hygiene) or a new hardening task if TASK-003 surfaces a parse crash.
- **Backup file disk-leak on partial failure** (session 003, PR #4 review) — if pg_dump succeeds and the dump file is written but the `BackupLog` insert/flush fails, the `.sql` file stays on disk with no log row pointing at it. Soft leak. Fix: wrap in try/except and `unlink()` the file on log-insert failure. Proposed home: Milestone 6 hardening.
- **Line-ending drift / add `.gitattributes`** (session 003, PR #5) — repo has mixed CRLF/LF line endings. During TASK-002 edits, `docker-compose.yml` and `.env.example` flipped CRLF→LF, inflating diffs. Adding a `.gitattributes` with `* text=auto eol=lf` would normalize and prevent future churn. Small, cosmetic. Proposed home: Milestone 6 or a one-off chore before Milestone 2.
- **Unused `from typing import Optional` in `backend/app/config.py`** (session 003, PR #5 review) — will be caught by ruff in Milestone 2 (TASK-008); no action needed now.
- **Redundant `env_file: .env` on the `db` compose service** (session 003, PR #5 review, minor nit) — the `environment:` block already declares the `POSTGRES_*` vars via `${...}` substitution, so the `env_file:` line is redundant for its stated purpose. Also injects unrelated vars (JWT_SECRET_KEY, API_URL) into the postgres container environment, which is not a security hole but is slightly broader than necessary. Drop if revisiting compose in TASK-007 or later.
- **Stale CLAUDE.md gotcha re: auto-backup crash path** (session 004, TASK-013 implementer observation) — CLAUDE.md § Gotchas still contains the "Auto-backup code path is currently broken" bullet, but TASK-001 fixed that code path in session 003 (PR #4). The gotcha is misleading for any future agent or human reading the file. One-line deletion from `CLAUDE.md`. Not urgent; just misleading. Proposed home: next docs/chore window, or bundle with another M1 task's PR.
- **Slug collision across clients** (session 004, PR #12 reviewer finding #1) — `_slug_client_name` uses the first whitespace-delimited word of `clients.name`, which means two clients whose names start with the same word (e.g. "Adamson Systems" and "Adamson Foundation") would produce the same slug and collide on their first invoice of the year. The `UNIQUE` constraint on `invoice_number` surfaces the collision as a 500 error rather than silent overwrite, so the failure mode is loud but user-visible. Possible fixes: (a) add an explicit `clients.short_name` column (requires DDL — wait for Alembic in M4); (b) detect collision at client-create time and require disambiguation; (c) extend the slug helper to append a discriminator when a clash exists. Not urgent — current client roster has no collision. Revisit if a real client collision surfaces or alongside M4 Alembic adoption.
- **M2 test coverage for `_slug_client_name`** (session 004, PR #12 reviewer finding #2) — when pytest infra lands in TASK-010, add unit tests for the slug helper covering: empty string, whitespace-only, punctuation-only first word, non-ASCII-only first word, leading-whitespace input, case preservation, digit-containing slug ("BEE2 Corp"), happy path ("O'Reilly & Sons"). Add to TASK-011 or TASK-012 decomposition at M2 open.
- **Backend `pg_dump` orphan on save-dialog cancel** (session 004, PR #16 reviewer finding #3) — the frontend `download_backup` eagerly fetches `GET /v1/backup/download` before opening the save dialog (to get the suggested filename). Each call to that endpoint triggers `BackupService.create_backup('manual')`, which shells out to `pg_dump`, writes a `.sql` file to the bind-mounted `backups/` directory, and inserts a `backup_logs` row. If the user then cancels the save dialog, the dump exists on disk but was never handed to the user — orphaned work and a stray file. Fix options: (a) refactor `create_backup` to support a stream-only mode when called via the HTTP endpoint (don't persist unless requested); (b) add an in-memory-only variant `generate_backup_bytes()` distinct from the persistent `create_backup()`; (c) accept the status quo and document it. Proposed home: Milestone 6 hardening, or bundled with any future backend-streaming work.
- **FilePicker `page.overlay` migration** (session 004, PR #16 reviewer finding #4) — three FilePicker instances currently live in view content Columns instead of `page.overlay` as Flet docs recommend. The existing restore `file_picker` in `settings.py:49` already uses the in-content pattern and works empirically; both new save pickers (`pdf_file_picker` in invoices.py and `backup_file_picker` in settings.py) follow the same pattern for consistency. Migrating all three to `self.page.overlay.append(...)` would match Flet's canonical guidance and be consistent with how `clients.py:212` and `payments.py:224` handle dialogs. Risk: no test harness to catch a restore regression during the migration. Small, cosmetic, no functional improvement. Proposed home: next frontend consistency pass or Milestone 5 (Containerize Frontend) cleanup.
