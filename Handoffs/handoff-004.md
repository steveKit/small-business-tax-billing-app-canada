# Handoff 004 — 2026-04-13

## Session Summary

Milestone 1 went 4-for-7 again, closing out every queued M1 code task except
the three user-gated ones. Started from clean `main` at `aae5389`
(post-handoff-003 merge). Shipped **12 PRs merged** and **1 PR closed
without merge** over the session, plus two live data migrations against the
db and a full revert cycle for one of them.

**Branch state:** clean on `main` at `848ebf8`. All feature branches deleted
locally + remote after merges. This handoff itself is being shipped on
`chore/handoff-004` and will be fast-track merged before session 005.

**Milestone 1 resolved: 8 of 11.** Session 003 closed 4 (001/002/004/005);
session 004 closed 4 more (013/014/015/016). Only **TASK-003**,
**TASK-006**, and **TASK-007** remain — all user-gated, sequenced linearly,
unchanged from handoff-003's description of what's blocking them.

### PRs shipped this session

| PR | Commit | Title |
|---|---|---|
| #7 | `c6be094` | `chore(compose): move db host port 5433 → 5434` (early session unblock — port conflict on host) |
| #8 | `278adc8` | `docs(tasks): add TASK-013 — fix invoice status transition bug` |
| #9 | `7c2f944` | `docs(tasks): add TASK-015 — per-client invoice numbering` |
| #10 | `5a44a4e` | `feat(invoices): TASK-013 — payments as source of truth for invoice status` |
| #11 | `b42847b` | `docs(tasks): mark TASK-013 complete, log stale-gotcha in Discovered Work` |
| #12 | `bd38aed` | `feat(invoices): TASK-015 — per-client invoice numbering` |
| #13 | `db1bfbc` | `docs(tasks): TASK-015 complete; queue TASK-014 and P0 TASK-016` |
| #14 | `673e4d0` | `fix(models): TASK-016 — PaymentMethod enum values_callable (P0 hotfix)` |
| #15 | `1240570` | `docs(tasks): mark TASK-016 complete — payment enum hotfix shipped` |
| #16 | `379e6be` | `feat(frontend): TASK-014 — FilePicker save for PDF and backup downloads` (attempted — reverted in #18) |
| #18 | `2f4ab90` | `hotfix(frontend): revert TASK-014 FilePicker approach — save_file is web-unsupported` |
| #19 | `848ebf8` | `docs: TASK-014 honest bookkeeping (attempted, reverted) + CLAUDE.md gotchas` |

**Closed without merge:** PR #17 — `docs(tasks): mark TASK-014 complete; log
findings #3 and #4 as Discovered Work`. Became obsolete between writing and
user-review approval because the user then tested and confirmed TASK-014's
web-mode bug, so the bookkeeping narrative (claiming TASK-014 shipped
cleanly) was wrong.

### Tasks resolved in session 004

- **TASK-013 — Invoice status transition bug, Option A (payments are source
  of truth).** Bug: `PATCH /v1/invoices/{id}/status` accepted any target
  unconditionally; the Flet "Mark as Paid" button drove that endpoint, so
  users could mark invoices `paid` with zero payment records — and then
  could neither add a payment nor revert. Fix: added
  `ALLOWED_STATUS_TRANSITIONS` whitelist in `routers/invoices.py`,
  constrained `InvoiceStatusUpdate.status` to
  `Literal[PENDING, CANCELLED]` in the schema (defense in depth), and
  deleted the "Mark as Paid" IconButton from `frontend/views/invoices.py`.
  Pre-dispatch data reconciliation: the 2 stuck Adamson invoices were
  marked `pending` via a transactional SQL UPDATE against the live db with
  a pg_dump backup captured at
  `~/tax-billing-backup-20260413-111707.sql` pre-reconcile. Reviewer flagged
  3 minor findings; #1 (misleading error text) and #2 (undocumented 422/400
  error contract) fixed in fixup commit `a99a9b6`; #3 (refund workflow
  gap — no PAID→CANCELLED transition) intentionally left unfixed because
  Canadian sole-prop accounting practice uses credit notes / negative
  payments, not direct cancel of paid invoices.
- **TASK-015 — Per-client invoice numbering `{year}-{client_slug}-{seq}`
  (Option A slug rule).** Changed `generate_invoice_number` from
  `INV-{year}-{seq:04d}` global-per-year to `{year}-{slug}-{seq:03d}`
  per-client-per-year. Added `_slug_client_name` helper using first
  whitespace-delimited word stripped to ASCII alphanumeric
  (e.g. `"Adamson Systems Engineering"` → `"Adamson"`). Chose slug rule
  (a) over adding a `clients.short_name` column to avoid pre-Alembic DDL
  work. The 3 existing invoices migrated via transactional SQL UPDATE
  against the live db; `INV-2026-0001/2/3` became
  `2026-Adamson-001/002` and `2026-BEE-001`. Fresh pg_dump captured at
  `~/tax-billing-backup-20260413-115039.sql` before the migration ran.
  Manual verification: created test invoices for both Adamson and BEE
  via curl POST (produced `2026-Adamson-003` and `2026-BEE-002`), then
  user deleted them via `docker exec psql` after safety hook correctly
  blocked the director from running destructive SQL.
- **TASK-016 — P0 hotfix: `PaymentMethod` enum serialization.** **Latent
  bug since project inception.** The `Enum(...)` column on
  `Payment.payment_method` was missing `values_callable`, so SQLAlchemy
  serialized enum members as their uppercase NAME (e.g. `"E_TRANSFER"`)
  instead of their lowercase VALUE (`"e_transfer"`). Postgres's
  `payment_method` enum only accepts the lowercase values, so every
  payment INSERT returned 500. Latent because payments count was 0 for the
  project's life — nobody had ever successfully created a payment (the
  buggy "Mark as Paid" button from TASK-013 bypassed payment creation
  entirely). Surfaced when the user tried to record the real Adamson
  payments post-TASK-013. Fix was a one-line mechanical port of the
  already-correct `Invoice.status` pattern
  (`values_callable=lambda obj: [e.value for e in obj]`). Live-verified
  end-to-end with 2 test payments created + deleted via
  `POST /v1/payments` and `DELETE /v1/payments/{id}`, both returning
  201/204.
- **TASK-014 — Resolved as "attempted, reverted."** Originally scoped as
  "replace `page.launch_url()` with `ft.FilePicker.save_file()` to fix the
  xdg_foreign warning in native Flet desktop on WSLg." Implemented cleanly
  in PR #16 (3 files, 84 lines added) with reviewer sign-off. User tested
  post-merge: clicking Download PDF triggered button animation but nothing
  happened. **Root cause:** `FilePicker.save_file()` is a no-op in Flet
  web mode (Flutter-web compiled). The FilePicker class docstring
  explicitly describes it as using the "native file explorer" — web
  browsers have no native file explorer, so Flet web's client silently
  drops the save-dialog state change. PR #18 reverted all three files to
  pre-TASK-014 state. PR #17 (original TASK-014 bookkeeping claiming
  clean shipment) closed without merge as obsolete. PR #19 added honest
  post-mortem bookkeeping + two CLAUDE.md Gotchas documenting the
  FilePicker web-mode limitation and the `wslu` host-side workaround for
  native WSLg. **Net code impact on main:** approximately 6 lines (a
  clarifying comment in `download_pdf`). The web-mode PDF download works
  correctly via `launch_url` — the pre-existing behavior was never
  actually broken in the canonical run mode.

### Early-session unblocks (pre-task work)

- **Port change 5433 → 5434** (PR #7). User's host had another process
  holding port 5433, so the existing db mapping conflicted. Moved the db
  host port to 5434. Docker-internal port stayed at 5432; no application
  config change needed. CLAUDE.md § Gotchas updated with history.
- **`.env` reconciliation.** User's local `.env` predated TASK-002 and was
  missing `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` variables that
  the new docker-compose.yml required. User added the old hardcoded
  credentials (`postgres`/`postgres`/`tax_billing`) to match the existing
  volume so `docker compose up` could start without wiping data. This is
  a pre-TASK-003 state — still has the pre-session-004 default secrets
  until the user runs TASK-003.
- **`DATABASE_URL` scheme fix.** User's `DATABASE_URL` was missing the
  `postgresql+asyncpg://` scheme prefix because of an ambiguous instruction
  in my previous session 004 explanation. Backend was crash-looping with
  `sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL` until
  user corrected it. Director lesson: when explaining connection strings,
  give the full literal including the scheme, not just the user/pass/host
  substring.

## Key Decisions

- **Payments are the source of truth for invoice status (Option A,
  TASK-013).** Only a payment that satisfies the invoice total can
  transition an invoice to `paid`. Manual PATCH is restricted to legal
  non-PAID transitions (DRAFT→PENDING, any→CANCELLED). The "Mark as Paid"
  button is gone from the Flet UI. Rejected: Option B (transition table
  with "Mark Unpaid" affordance) and Option C (auto-create synthetic
  payment on mark-paid). Rationale: matches Canadian sole-prop accounting
  practice and removes the "how did I get into this state" bug category.
- **First-word slug from client name for per-client invoice numbering
  (TASK-015 slug rule (a)).** Rejected: Option C (explicit
  `clients.short_name` column) to avoid pre-Alembic DDL work. Tradeoff:
  two clients whose names share the same first word would collide at
  invoice creation time — the `UNIQUE` constraint on `invoice_number`
  surfaces this as a 500, not a silent bug. Current client roster has no
  collision. Revisit in Milestone 4+ if it becomes a real problem.
  Logged in Discovered Work as "Slug collision across clients."
- **Flet `FilePicker.save_file()` is a no-op in web mode (hard lesson).**
  Documented in CLAUDE.md § Gotchas. The FilePicker class explicitly uses
  the "native file explorer" per its own docstring — web mode (browser-
  based Flutter-web) has no native file explorer, so `save_file()` sets
  Python state + calls `self.update()` and the Flet web client silently
  drops the dialog request. For downloads in web mode, use
  `page.launch_url()` with a backend endpoint returning
  `Content-Disposition: attachment` — the browser handles the download
  natively.
- **Native Flet desktop on WSLg needs host-side `wslu` install — this is
  NOT a code fix.** The `xdg_foreign` Wayland protocol isn't implemented
  by WSLg's Weston compositor. GTK's `gtk_show_uri` (used by
  `launch_url` in native Flet) depends on it. Host fix: install the
  `wslu` package via the distro package manager, then
  `export BROWSER=wslview`. Out of scope for any Python code change.
  Canonical run mode per ADR #4 is web, so the issue is a non-canonical-
  mode limitation.
- **"Revert as resolution" is a valid task outcome.** TASK-014 is marked
  `[complete]` in TASKS.md even though its code changes were fully
  reverted. Rationale: the task's user-visible goal (PDF download works)
  is achieved in the canonical web mode via the pre-existing
  `launch_url` approach. The revert proved the original scope was
  misdirected. The completion record in TASKS.md captures the full
  post-mortem so the next agent understands what was tried and why not to
  try it again. Milestone counts count tasks *resolved*, not code
  *shipped*.
- **Human-in-the-loop verification is mandatory for UI-visible changes.**
  TASK-014 shipped clean (AST parse, container restart, grep checks,
  reviewer approval) because the bug only manifested at button-click
  time, which the director can't reproduce without a user in the loop.
  Director should now include a "user manually verifies the UI
  interaction" step in the acceptance criteria for any frontend-touching
  dispatch that changes click-to-action flows. For Milestone 2+ dispatches
  that touch the Flet UI, bake the user-verify step into the task spec
  before presenting for merge.
- **Dispatch specs should not over-commit on satisfiable acceptance
  criteria.** TASK-013 fixup dispatch had a "grep returns zero matches
  for 5433" criterion but the replacement text I wrote for the Gotcha
  literally contained "5433" in a historical note. Implementer correctly
  paused and flagged the impossible criterion. Director lesson: when
  writing acceptance criteria, double-check that the exact text being
  inserted doesn't violate the criterion. This is a recurring failure
  mode worth adding to the director's pre-flight checklist.

## Files Changed

### Backend

- `backend/app/routers/invoices.py` — TASK-013 (added
  `ALLOWED_STATUS_TRANSITIONS` whitelist, rewrote `update_invoice_status`
  with transition checks + docstring) + TASK-015 (added
  `_slug_client_name` helper, rewrote `generate_invoice_number` with
  per-client-per-year scoping, updated call site to pass
  `client.id` + `client.name`)
- `backend/app/schemas/invoice.py` — TASK-013 (constrained
  `InvoiceStatusUpdate.status` to
  `Literal[InvoiceStatus.PENDING, InvoiceStatus.CANCELLED]`; added
  `Literal` to the `typing` import)
- `backend/app/models/payment.py` — TASK-016 (added
  `values_callable=lambda obj: [e.value for e in obj]` to the `Enum(...)`
  column on `Payment.payment_method`, matching `Invoice.status` pattern)

### Frontend

- `frontend/views/invoices.py` — TASK-013 (removed "Mark as Paid"
  IconButton, preserving "Mark as Pending" and `update_status` helper);
  TASK-014 attempted changes reverted, net result is one clarifying
  comment in `download_pdf` explaining the web/native trade-off
- `frontend/views/settings.py` — TASK-014 attempted changes reverted;
  file is byte-identical to pre-session-004
- `frontend/services/api_client.py` — TASK-014 attempted changes
  reverted; file is byte-identical to pre-session-004

### Infrastructure / config

- `docker-compose.yml` — host db port mapping 5433 → 5434 (PR #7
  unblock)
- `CLAUDE.md` — § Gotchas: port mapping gotcha updated with history note;
  two new Gotchas added (Flet `FilePicker.save_file()` web-mode
  limitation, native Flet desktop on WSLg needs `wslu`); latest handoff
  pointer updated to 004

### Project docs

- `TASKS.md` — extensive: 4 new completed task entries under session
  004 sub-block (TASK-013/014/015/016); TASK-013/014/015/016 removed
  from active Milestone 1; `Remaining in milestone` updated 3 times as
  work progressed; TASK-007 dependencies + acceptance criteria extended
  to cover TASK-013/015/016 regression checks; 3 new Discovered Work
  entries added (stale CLAUDE.md gotcha from TASK-001 era, slug
  collision across clients, M2 test backlog for `_slug_client_name`)
- `PROJECT.md` — status blurb updated several times as each task
  landed; milestones table M1 count moved 4/9 → 5/9 → 6/11 → 7/11 →
  8/11 (ended with 8/11 resolved); `Last Updated` moved from 2026-04-10
  to 2026-04-13
- `Handoffs/handoff-004.md` — this file

## Blockers & Open Questions

- **Real Adamson payments still need to be recorded manually.** Both
  Adamson invoices (`2026-Adamson-001` and `2026-Adamson-002`, $10,170
  each) are currently `pending` with 0 payment records. The pre-TASK-013
  data reconciliation reverted them from the buggy `paid`-with-no-
  payments state. The user committed to recording the real payment
  details (date, method, reference number) via the Flet UI after
  TASK-016 landed — which it now has. **Not done yet.** Session 005 (or
  the user out-of-band) should close this loop. The existing
  `routers/payments.py` auto-transition logic will flip the invoices to
  `paid` once the sums satisfy $10,170 each. This is *not* blocking
  TASK-003 or TASK-007 strictly, but leaving it open means
  TASK-007's smoke test runs against an inconsistent state.
- **TASK-003 still blocks on the user — data-loss event, same as
  handoff-003.** Nothing changed about this task: the user's `.env`
  still has the pre-session-004 default credentials
  (`postgres`/`postgres`/`tax_billing`), and rotating them requires
  `docker compose down -v` + fresh volume + restore from a pg_dump
  backup. Current backups: `~/tax-billing-backup-20260413-111707.sql`
  (pre-reconcile) and `~/tax-billing-backup-20260413-115039.sql`
  (post-reconcile, pre-TASK-015 migration). Neither captures the
  post-TASK-015 state because the migration ran against the live db and
  I didn't take another backup after. **Session 005 should take a fresh
  `pg_dump` before starting TASK-003.**
- **TASK-006 still blocks on elevated privileges.** 8 stale root-owned
  `.json` files in `backups/` plus some newer `.sql` files that were
  created by the TASK-016 verification payments triggering auto-backup
  (each successful `POST /v1/payments` runs `BackupService.create_backup`
  which writes to `backups/`). User runs the cleanup command; agents
  cannot escalate privileges.
- **TASK-007 still sequenced behind TASK-003 + TASK-006, same as
  handoff-003.** Its first acceptance criterion is
  `docker compose down -v && docker compose up -d` — can't run cleanly
  until TASK-003 has populated the new required vars.
- **Stale CLAUDE.md gotcha (auto-backup crash path) still there.** TASK-001
  fixed the code in session 003 but the Gotchas bullet was never deleted.
  Logged in Discovered Work. Small one-line deletion that would be
  trivial to bundle into any future docs PR. Not urgent; just misleading
  for any future agent reading CLAUDE.md.
- **Director lesson NOT captured in any agent config yet.** Session 004
  surfaced two director failure modes worth eventually codifying:
  (1) don't write acceptance criteria that the exact text being inserted
  violates; (2) for UI-visible click-time changes, require a user-
  verification step in the acceptance criteria before PR merge. Both
  were hard-learned via TASK-013 fixup and TASK-014 revert respectively.
  Adding these to `~/.claude/agents/director.md` or a director pre-flight
  checklist is out of scope for this session but should be a session 005
  consideration.

## Discovered Work

Three items added to TASKS.md § Discovered Work this session (two new,
one carried from session 003 still unfixed):

- [ ] **Stale CLAUDE.md gotcha — auto-backup crash path.** TASK-001
  fixed the code in session 003 but the "Auto-backup code path is
  currently broken" bullet in CLAUDE.md § Gotchas wasn't deleted. One-
  line fix. Proposed home: next docs/chore PR window. (Carried from
  session 003 as "discovered" during TASK-013 implementer's read.)
- [ ] **Slug collision across clients (TASK-015 reviewer finding #1).**
  `_slug_client_name` takes the first whitespace-delimited word of
  `clients.name`, so two clients whose names share the same first word
  (e.g. "Adamson Systems" and "Adamson Foundation") would produce the
  same slug and collide at invoice creation. The UNIQUE constraint on
  `invoice_number` surfaces this as a 500, not silent. Options: (a) add
  `clients.short_name` column (Alembic work), (b) detect collision at
  client-create time, (c) extend slug helper to suffix a discriminator.
  Not urgent; current roster has no collision. Revisit on next schema
  change or Milestone 4+.
- [ ] **M2 test coverage for `_slug_client_name` (TASK-015 reviewer
  finding #2).** When pytest infra lands in TASK-010, add unit tests
  for the slug helper covering: empty string, whitespace-only,
  punctuation-only first word, non-ASCII-only first word ("日本"),
  leading-whitespace input, case preservation, digit-containing slug
  ("BEE2 Corp"), happy path ("O'Reilly & Sons"). Add to TASK-011 or
  TASK-012 decomposition when M2 opens.

**Not logged** (moot after TASK-014 revert): reviewer findings #3
(backend pg_dump orphan on save-dialog cancel) and #4 (FilePicker
page.overlay migration). Both were about FilePicker code that no longer
exists on main.

## Next Steps

Session 005 must finish Milestone 1. The remaining sequence is unchanged
from handoff-003, with one addition (real payment recording):

1. **P0 — Record real Adamson payments** via the Flet UI at
   `http://localhost:8080`. Navigate to invoices, click an Adamson row,
   record a payment (date, method, reference number) for the real
   amount. The existing `routers/payments.py` logic will auto-transition
   the invoice to `paid` once the sum satisfies the $10,170 total.
   Repeat for the second Adamson invoice. Closes TASK-013's
   reconciliation loop. User action; director provides UI guidance if
   needed. ~2 minutes of user work in the canonical web mode.
2. **P0 — TASK-003 (data-loss event), same as handoff-003.** Before
   running, take a fresh `pg_dump` to capture the post-TASK-015 state:
   ```bash
   docker exec tax-billing-db pg_dump -U postgres -d tax_billing --clean --if-exists > ~/tax-billing-backup-$(date +%Y%m%d-%H%M%S).sql
   ```
   Then follow the TASK-003 procedure from handoff-003 (generate new
   secrets, `docker compose down -v`, bring up with new `.env`, restore
   from the fresh backup via `psql`). The restore is cleaner if the
   schema.sql init-volume init runs first and the dump's `--clean`
   directives drop+recreate on top of it — which is what happens by
   default with this backup format. Director provides the exact command
   sequence; user runs it.
3. **P2 — TASK-006 (elevated privileges).** Same as handoff-003. One
   command, cosmetic. Now also catches any stray `.sql` auto-backups
   from session 004's TASK-016 verification payments.
4. **P0 — TASK-007 (integration verification + M1 tag).** Same as
   handoff-003, with additions for TASK-013/015/016 regression checks:
   - PATCH → PAID must be rejected (422 from pydantic, 400 from
     handler whitelist)
   - New invoice for Adamson lands as `2026-Adamson-NNN`; new invoice
     for BEE lands as `2026-BEE-NNN`
   - `POST /v1/payments` with a real `payment_method` value returns 201
   - All existing acceptance criteria from handoff-003
   On pass: create and push annotated tag `milestone-01-stop-the-bleeding`,
   mark the Milestone 1 header `[complete]` with a stub, move
   TASK-003/006/007 to Completed Tasks (session 005 sub-block).
5. **Then Milestone 2 (Quality Gates)**, same decomposition as
   handoff-003 (TASK-008 → 009/010 → 011/012). Session 005 may start
   this if TASK-007 closes cleanly and there's runway.

## Files to Read on Resume

- [[CLAUDE]] — conventions, commands, § Gotchas (two new entries for
  Flet FilePicker and WSLg wslu)
- [[PROJECT]] — updated status blurb, milestones table, Last Updated
  2026-04-13
- [[TASKS]] § Milestone 1 — 3 remaining tasks (TASK-003/006/007) with
  acceptance criteria; § Completed Tasks has the session 004 sub-block
  with full post-mortems on TASK-013/014/015/016 including the
  TASK-014 revert cycle
- [[Handoffs/handoff-003]] — the handoff-003 TASK-003 command sequence
  is still the canonical reference; only addition is the pre-TASK-003
  fresh pg_dump note
- `backend/app/routers/invoices.py` — read `ALLOWED_STATUS_TRANSITIONS`
  (lines 32-35), the `update_invoice_status` handler (lines 148-171),
  `_slug_client_name` helper, and the new `generate_invoice_number`
  signature to understand the TASK-013/015 end state
- `backend/app/models/payment.py` — see the TASK-016 `values_callable`
  fix at lines 40-49; same pattern already in `invoice.py` lines 50-59
  is the canonical reference for any future ORM Enum column
- `frontend/views/invoices.py` — see the `download_pdf` comment
  explaining the web/native launch_url trade-off (TASK-014 post-mortem
  residue)

## Library Candidates

_None._ The code shipped this session is entirely project-specific
(invoice state machine, per-client numbering, Flet view tweaks, Postgres
enum serialization). The `_slug_client_name` helper is small and
domain-coupled to invoice numbering; the `ALLOWED_STATUS_TRANSITIONS`
pattern is idiomatic but a 3-line data structure isn't worth extracting.
Nothing qualifies.
