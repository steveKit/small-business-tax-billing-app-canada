# Milestone 01: Stop the Bleeding

> **Status:** active
> Index: [[TASKS]] · Architecture: [[PROJECT]] · Conventions: [[CLAUDE]]
> **Goal:** The P0 fixes that make the codebase safe to work on. Every task in this milestone addresses a latent bug, a security rule violation, or a footgun discovered in the plenary audit.
> **Priority:** `P0` (critical) | `P1` (high) | `P2` (medium) | `P3` (low) · **Size:** `S` (< 1 hr) | `M` (1–4 hrs) | `L` (4+ hrs)

## Active Tasks

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

## Completed Tasks (this milestone)

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
**Discovered during this task:** DW-001, DW-002
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
**Discovered during this task:** DW-003, DW-004, DW-005
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

### Milestone 1: Stop the Bleeding (partial — session 004)

**Completed:** 2026-04-13
**PRs:** #10 — `feat(invoices): TASK-013 — payments as source of truth for invoice status`; #12 — `feat(invoices): TASK-015 — per-client invoice numbering`; #14 — `fix(models): TASK-016 — PaymentMethod enum values_callable (P0 hotfix)`; #16 — `feat(frontend): TASK-014 — FilePicker save for PDF and backup downloads` + #18 — `hotfix(frontend): revert TASK-014 FilePicker approach — save_file is web-unsupported`
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

**Discovered during this task:** DW-006
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

**Discovered during this task:** DW-007, DW-008
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

#### TASK-014: Replace `launch_url` with `FilePicker.save_file` for PDF download [`complete`] [`P1`] [`M`]
**Status:** Attempted with FilePicker, reverted after web-mode testing revealed `FilePicker.save_file()` is a no-op in Flet web mode. Web-mode PDF/backup downloads work correctly via the original `page.launch_url()` approach, which was restored by the revert. Native Flet desktop on WSLg remains broken (original xdg_foreign limitation) and is deferred to host-side `wslu` setup — a platform limitation that cannot be fixed in Python code.

**Dependencies:** none
**Original description:** The user reported PDF download failing with `Gdk-WARNING: Server is missing xdg_foreign support` when running `mise run frontend` (native Flet desktop) on WSLg. TASK-014 was scoped to fix this by replacing `page.launch_url(pdf_url)` — which routes through GTK → Wayland portal → `xdg_foreign` — with `ft.FilePicker.save_file()` on the assumption that FilePicker would be platform-agnostic.

**What actually happened (in order):**
1. **PR #16 shipped the FilePicker approach** (2026-04-13). Three files changed: `invoices.py`, `settings.py`, `api_client.py`. Added `pdf_file_picker` and `backup_file_picker` in content Columns, rewrote `download_pdf` and `download_backup` to use `save_file()` with closure-based callbacks, added `get_backup_download()` to api_client. Reviewer (PR #16) approved with 5 minor findings. Fixup commit `a99a9b6` addressed findings #1, #2, #5. Findings #3 and #4 logged as Discovered Work.
2. **Director's pre-merge verification was incomplete.** AST parsed, container restarted cleanly, `grep launch_url` showed zero residue. BUT no live button-click verification happened because the director can't click buttons in Flet without a human in the loop.
3. **PR #16 merged.** User tested and reported: button click animation triggers but nothing happens — no dialog, no file, no error. Same behavior in both Flet web mode (localhost:8080) and native Flet desktop.
4. **First recovery attempt — overlay hotfix.** Director initially diagnosed the bug as FilePicker placement (reviewer finding #4 revisited). Prepared a branch moving `pdf_file_picker` to `page.overlay`. Before applying it, went to verify against Flet source: found the FilePicker docstring explicitly describes it as using the "native file explorer", and `save_file()` in Flet 0.24 is just a state-setter on the Python side that calls `self.update()` — the actual dialog is rendered by the Flet CLIENT, which in web mode is Flutter-web-compiled and has NO implementation for native save dialogs (browsers cannot open native OS dialogs from JavaScript).
5. **Correct diagnosis arrived.** `FilePicker.save_file()` is web-unsupported. The reviewer's finding #4 (about overlay placement) was irrelevant — the issue wasn't placement, it was that Flet web mode fundamentally does not support this API.
6. **Second recovery — the actual fix.** Director reverted the two download handlers to `page.launch_url(url)`. Web mode works because the browser handles the `Content-Disposition: attachment` header and auto-downloads the file. Native Flet desktop on WSLg remains broken with the same xdg_foreign warning as before TASK-014 — nothing in the revert touches that platform limitation.
7. **PR #18 shipped the revert** (`2f4ab90`). User confirmed web-mode PDF download works. PR #17 (the original TASK-014 bookkeeping, which claimed TASK-014 had shipped successfully) was closed without merging because its narrative was wrong.

**Files changed on main (net result, post PR #16 + PR #18):**
- `frontend/views/invoices.py` — one comment change to `download_pdf` documenting the web/native trade-off and pointing at PROJECT.md ADR #4 (web is canonical). Otherwise byte-identical to pre-TASK-014.
- `frontend/views/settings.py` — byte-identical to pre-TASK-014.
- `frontend/services/api_client.py` — byte-identical to pre-TASK-014.

Net code change from TASK-014's exploration: **approximately 6 lines** (the clarifying comment). The 84-line FilePicker implementation was entirely transient.

**Acceptance Criteria (final assessment):**
- [x] PDF download works in the canonical web-mode run (http://localhost:8080) — user verified live
- [ ] Native Flet desktop mode PDF download — **NOT fixed**. Original WSLg `xdg_foreign` limitation persists. Not a code bug; fix is host-side `wslu` setup (see CLAUDE.md follow-up Gotcha/Setup note).
- [x] Backup download works in web mode (expected — same `launch_url` mechanism, not live-tested but infrastructure is identical)
- [x] No regression in the canonical run mode
- [x] Reviewer findings #1, #2, #5 (token guard, coupling anchor, filename accuracy) — all reverted along with the code they were fixing; no longer applicable.
- [ ] Regression test — **not applicable**. The code that would have been tested no longer exists. If native-mode support is ever re-scoped (TASK-014b), add tests there.

**Notes (post-mortem):**
- **Discovered 2026-04-13** (session 004) when user first tried to download PDFs via native Flet desktop on WSLg. Workaround used during the session: curl directly against `http://127.0.0.1:8000/v1/invoices/{id}/pdf` from the host — works fine, files saved at `/home/horse/tax-billing-invoices/`.
- **Lesson for the director:** when a task touches UI-visible behavior that only manifests at click time, **require a human-in-the-loop verification step in the acceptance criteria** before presenting the PR for merge. Static analysis, AST parse, and container restart caught nothing because the bug was Flet-web-runtime-specific. A 30-second "click the button and tell me what you see" check during TASK-014's dispatch would have surfaced the bug before PR #16 merged and prevented the revert cycle.
- **Lesson for Flet web users:** `FilePicker.save_file()` is a no-op in Flet web mode. The FilePicker class description says "native file explorer" — take that literally. For file *downloads* in web mode, use `page.launch_url()` with a backend endpoint that returns `Content-Disposition: attachment`. Added as a Gotcha in CLAUDE.md by this PR.
- **Native WSLg workaround:** install `wslu` on the host and export `BROWSER=wslview`, then `launch_url` in native Flet mode routes through `wslview` → Windows browser → download works. Added as a Setup/Gotcha note in CLAUDE.md by this PR. This is a one-time host setup and is explicitly out of scope for any Python code change.
- **Reviewer findings #3 and #4 (logged as Discovered Work in PR #17):** both were about FilePicker code that no longer exists. Finding #3 (backend `pg_dump` orphan on save-dialog cancel) is moot because the eager-fetch pattern is gone. Finding #4 (FilePicker overlay migration) is moot because only the restore picker remains and it uses `pick_files()` (different dispatch). **Not migrating these to Discovered Work in this PR** — they're artifacts of the reverted code.
- **PR #16** squash-merged as `379e6be` on main.
- **PR #18** (the revert) squash-merged as `2f4ab90` on main.
- **PR #17** (stale bookkeeping claiming TASK-014 shipped) closed without merging.

---

## Out-of-milestone / ad-hoc completed work

_Ad-hoc fix landed during the M1 window (session 005); never part of M1 scope — excluded from the 8/11 milestone count._

### Ad-hoc fix — session 005

**Completed:** 2026-06-10
**PR:** #21 — `fix(invoice-pdf): preserve line breaks in Description of Work`

#### TASK-017: Preserve line breaks in invoice PDF "Description of Work" [`complete`] [`P2`] [`S`]
**Dependencies:** none (ad-hoc user-requested fix; never queued under a milestone)
**Description:** User-entered newlines in an invoice's Description of Work were collapsed into single spaces in the rendered PDF. The fix preserves them with a one-line CSS addition (`white-space: pre-wrap;`) on the `.description-text` rule in the Jinja2 invoice template.

**Files in scope (changed):**
- `backend/app/templates/invoice.html` — added `white-space: pre-wrap;` to the `.description-text` CSS rule (one line).

**Acceptance Criteria:**
- [x] `.description-text` rule in `backend/app/templates/invoice.html` carries `white-space: pre-wrap;`
- [x] Re-rendered invoice PDFs preserve user-entered line breaks in Description of Work
- [x] No template injection risk introduced (Jinja2 `autoescape=True` retained; CSS approach, no `<br>` injection)
- [x] No invoice recreation required — stored data was already correct; only PDF render output changed

**Notes:**
- **Root cause was render-only.** The input/storage side was already correct: the Flet field is `multiline=True` and the DB column is `Text`, so newlines were always stored. The `.description-text` CSS rule simply had no `white-space` property, so HTML collapsed the stored line breaks into single spaces at PDF render time.
- **Injection-safe by design.** The Jinja2 template keeps `autoescape=True`, so a CSS-based fix was chosen over injecting `<br>` tags (which would have required either disabling autoescaping or a manual `nl2br`-style filter — both higher-risk for a template rendering client-supplied text).
- **`pre-wrap` over `pre-line`.** `pre-wrap` preserves both newlines *and* runs of whitespace/indentation faithfully, which suits a pasted line-by-line work list where indentation may be meaningful. `pre-line` would have collapsed multiple spaces.
- **No data migration / invoice recreation needed.** Because newlines were always stored, re-rendering the PDF reflects the fix. The backend bind-mounts the template (`./backend:/app`) and Jinja2 auto-reloads, so only a PDF re-download — or at most a `docker restart tax-billing-backend` — is required to pick up the change.
- **Fast-tracked** (director self-review, no independent reviewer dispatch). Rationale: single-line CSS change, no API/schema/behavior change, no injection surface, 0 fix cycles.
- **PR #21** squash-merged as `b5a211a` on main.
