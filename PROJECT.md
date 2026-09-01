# tax-billing — Project Overview

See [[CLAUDE]] for agent conventions and [[TASKS]] for the work queue.

## Status

**Phase:** Hardening — Milestone 1 closed, entering Milestone 2 (Quality Gates)
**Last Updated:** 2026-09-01

The project was built in Feb 2026 as a personal Canadian sole-proprietor
tax-holdback calculator + invoicing tool. It functioned but was unhardened:
no auth, no tests, no lint/type-check, hardcoded credentials in committed
files, a broken auto-backup code path, and an unauthenticated SQL restore
endpoint. A workflow plenary was held on 2026-04-10 and the project is
being hardened to L3 for eventual network exposure. Milestone 1 closed the
worst of that list — credentials extracted to `.env`, the auto-backup path
fixed, every published port bound to loopback — leaving no auth, no tests,
no lint/type-check, and the unauthenticated SQL restore endpoint as the
remaining unhardened surface (Milestones 2 and 3).

**Milestone 0 (Workflow Scaffold) is complete** as of 2026-04-10 —
tagged `milestone-00-workflow-scaffold`. Session 003 (2026-04-10) landed
the first four Milestone 1 tasks: TASK-001 (auto-backup fix), TASK-002
(credentials extracted to .env), TASK-004 (127.0.0.1 bind), TASK-005
(utcnow deprecations). Session 004 (2026-04-13) landed TASK-013
(invoice status bug — payments are source of truth; PR #10, `5a44a4e`),
TASK-015 (per-client invoice numbering; PR #12, `bd38aed`), TASK-016
(P0 hotfix — PaymentMethod enum serialization; latent bug surfaced on
first real payment attempt post-TASK-013; PR #14, `673e4d0`), and
**TASK-014 (resolved as reverted)** — FilePicker approach shipped in
PR #16 then reverted in PR #18 (`2f4ab90`) after web-mode testing
revealed `FilePicker.save_file()` is a no-op in Flet web. Web-mode PDF
and backup downloads work via the pre-existing `launch_url` approach;
native Flet desktop mode on WSLg remains broken (platform-level
`xdg_foreign` limitation — host-side `wslu` setup is the workaround,
now documented in CLAUDE.md § Gotchas). That session also unblocked
**payment creation** (TASK-016) and **web-mode PDF/backup downloads**
(TASK-014 revert), leaving TASK-003, TASK-006 and TASK-007 as the last
Milestone 1 work.

Session 005 (2026-06-10) shipped one ad-hoc fix outside the milestone
track: TASK-017 made the invoice PDF preserve user-entered line breaks
in the "Description of Work" field (one-line CSS `white-space: pre-wrap;`
in the WeasyPrint/Jinja2 template). Milestone 1 status is unchanged.

Session 006 (2026-09-01) was unblocking and bookkeeping only. TASK-018
reallocated the dev database host port 5434 → 5435 after a collision with
`adamson-next-2025`, the registered owner of 5434 in the global port
registry; tax-billing's port predated the registry and was unregistered,
so it was the party that moved — it is registered now, and the allocation
is mirrored below in § Provisioned Infrastructure (PR #25, `3918b41`).
The session also reconciled two things that had happened outside the
handoff chain. First, the task queue was migrated to the indexed
per-milestone layout on 2026-06-18 (PR #24, `01b1c1b`) with no handoff
written and no note here — [[TASKS]] is now an index over
`workflow/tasks/milestone-NN-*.md` plus [[workflow/tasks/deferred]] and
[[workflow/tasks/discovered]]. Second, **the real Adamson payments were recorded
out of band**: `2026-Adamson-001` and `-002` are both `paid`, which closes
the P0 reconciliation blocker carried since handoff-005. Newer invoices
exist (Adamson-003/004/005, BEE-002/003) and `backups/` holds `.sql`
auto-backups dated 2026-05-13. Milestone 1's three remaining tasks were
all user-gated at that point; they were resolved later the same day in the
close-out below.

**Milestone 1 — Stop the Bleeding — closed 2026-09-01**, annotated tag
`milestone-01-stop-the-bleeding` at `7d42dcb`. Final tally: 10 of 11 tasks
complete, with **TASK-003 (strong secrets) deferred to Milestone 3** by user
decision and re-scoped there to a non-destructive rotation (ADR #12;
[[workflow/tasks/deferred]] DEF-001) — the volume holds real financial records and the
original plan required `docker compose down -v`. The close-out ran TASK-006
(8 dead `.json` backups from the pre-TASK-001 format removed from the
root-owned `backups/` bind mount via `docker exec`, no host `sudo`) and
TASK-007, the integration verification. TASK-007 was deliberately built to
avoid destroying real data: the schema was rebuilt from `schema.sql` +
`seed_data.sql` inside a **throwaway** `postgres:16-alpine` container instead
of wiping `postgres_data` (9 tables, 2 views, 2025/2026 federal + Ontario
brackets, `tax_years` seeded), `/health` returned 200, the hardcoded-secrets
and `utcnow` greps came back clean, and the TASK-013/015/016 regressions were
confirmed from live production data plus a random-UUID PATCH probe rather
than a synthetic create/delete cycle that would have left test invoices in
real books. The wiring audit found nothing Milestone 1 introduced to be
orphaned; it did surface two **pre-existing** issues, logged as DW-012
(unreferenced pydantic schemas) and DW-013 (`backup_logs` rows outnumber
backup files on disk; `backup_retention_count` is never applied). Neither
task changed code, so there were no PRs in this close-out — bookkeeping went
direct to main (`1a4000e`, `7d42dcb`). The discovered-work log was triaged
with the user in full: every open item now carries a target milestone (see
[[workflow/tasks/discovered]]). **Next up: Milestone 02 — Quality Gates**, starting
with TASK-008 (pyproject + ruff). At M2 start the director folds DW-003,
DW-004, DW-008, DW-010 and DW-011 into the Milestone 2 task definitions.

That same session also brought the project's workflow machinery up to date:
`/migrate-workflow` ran staged from v0 to **v15**, relocating `Handoffs/`,
`tasks/` and `memory/` under `workflow/`, stamping `workflow-version: 15`,
`releasable: false` and `testing-paradigm: adaptive` in [[CLAUDE]], and adding
the Severity column to [[workflow/tasks/discovered]] plus the Consequences
column to the decisions table below (every row is still `—`, and § Runtime
Data Flow is likewise an undrawn stub — both are open work for the Milestone 3
plenary). The gate-auditor ran as part of the sync and found **11 expected
gates, 0 present** — by design, since Milestone 2 is their home; the report is
`docs/reports/gate-audit-2026-09-01.md` and its findings are queued as
DW-014 through DW-025, including DW-019 (no CI exists at all). The repository
itself was hardened on user confirmation: the `protect-main` ruleset now blocks
branch deletion and non-fast-forward pushes on `main`, and merges are
squash-only with the subject pinned to the PR title and the body to the PR
body — so a PR title is literally the commit subject that lands on `main`.
Require-PR and require-status-checks are deliberately off: the first would
block the bookkeeping-direct-to-main flow, and the second has no CI to check
yet.

## Architecture Decisions

| # | Decision | Choice | Rationale | Consequences | Date |
|---|----------|--------|-----------|--------------|------|
| 1 | Coding paradigm | Layered / service-oriented | Matches the existing `routers → services → models` shape; no refactor needed. FastAPI idiomatic. | — | 2026-04-10 |
| 2 | Testing paradigm | Adaptive | TDD for pure tax math (high-stakes, clear contracts); test-after for routers/views/wiring. | — | 2026-04-10 |
| 3 | Security profile | L3 | Handles PII + authoritative tax math + financial amounts; will eventually be network-exposed. "Harden this" is an explicit mandate from the user. | — | 2026-04-10 |
| 4 | Canonical frontend run mode | Containerized Flet web (port 8080) | One code path to secure, works on any host, suits network exposure target. | — | 2026-04-10 |
| 5 | Desktop-mode escape hatch | Kept as `mise run desktop` | Native window UX is pleasant for daily bookkeeping on WSL2/WSLg. Documented as non-canonical dev convenience. | — | 2026-04-10 |
| 6 | Auth mechanism | JWT (Bearer in `Authorization` header) | Stateless, scriptable via `curl`, keeps `python-jose` non-cargo-culted. CSRF-exempt because not cookie-based. Details finalized at Milestone 3 plenary. | — | 2026-04-10 |
| 7 | Tenancy model | Single-user (sole-prop) | The domain is one business owner. No multi-tenancy, no user registration, no role hierarchy. One admin user, one password. | — | 2026-04-10 |
| 8 | Migration tooling | Alembic (deferred to Milestone 4) | Current compose init-volume approach forces `down -v` data loss on any schema change. Unacceptable for a tool holding real financial records. | — | 2026-04-10 |
| 9 | Money handling | `Decimal` end to end | Floats are unacceptable for financial math. DB columns are `DECIMAL(12,2)`; Python quantizes to `Decimal("0.01")`. | — | 2026-04-10 (pre-existing, recorded) |
| 10 | Architect pass | Declined for now | Case-(b) trigger (structural problems code can't fix) hasn't fired; 2026-04-10 foundation audit still valid; remaining M1 is mechanical/user-gated, M2 is pure tooling, and the architecturally-significant milestones (3/4/5/7) each get a focused plenary at their start. Revisit at the Milestone 3 auth plenary boundary if JWT bolts on awkwardly, or if any fix cycle stalls past ~3 iterations. | — | 2026-06-10 |
| 11 | Dev DB host port | `127.0.0.1:5435` (registered) | Collided with `adamson-next-2025`, the registered owner of 5434 in the global port registry (`~/.claude/references/port-registry.yaml`). Per [[resource-naming]] § Ports Are Pinned Identities the unregistered party moves, and tax-billing's 5434 predated the registry. 5435 is the next free port in the postgres range 5433–5452; loopback-bound (`127.0.0.1:5435:5432`), and tax-billing now holds an `active` registry entry. Backend still reaches the DB at `db:5432` in-network, so only host-side connections moved. | — | 2026-09-01 |
| 12 | Secrets rotation procedure | Non-destructive: `ALTER USER … PASSWORD` inside the running `tax-billing-db` container + `.env` edit (`POSTGRES_PASSWORD`, `DATABASE_URL`) + `docker compose up -d` to recreate the backend — never `docker compose down -v` | The `postgres_data` volume holds real financial records, and the `POSTGRES_*` env vars only take effect at *first* initialization — so recreating the volume to change a password trades real data for a rotation `ALTER USER` performs in place. Adopted when TASK-003 was deferred to M3; the task's original AC 3 (`down -v` rebuild) is dropped on pickup. | — | 2026-09-01 |

_Add rows as decisions are made. Don't delete — this is the project's decision
history. A reversal is a new row; mark the old row's Choice `superseded by #N`,
never rewrite it. **Rationale** says why the choice won; **Consequences** says
what it makes easier and what it makes harder — the warning to the future
reader (`—` only when genuinely trivial). A decision with an expiry condition
records it in its Consequences cell as `Revisit when: <observable trigger>`;
the planner checks for fired triggers at every milestone explosion. A decision
**graduates** to a point-in-time doc under `docs/` (linked from the Rationale
cell — the row stays the index) when any criterion holds: real alternatives
were seriously weighed, the decision introduces a novel pattern, or it cuts
across features. The graduated doc follows Nygard's shape — Context, Decision,
Consequences, Alternatives considered, optional Revisit when._

_When descriptive architecture content outgrows this file (sections needing
subsections, agents needing repeated deep-dives), the documenter graduates the
descriptive bulk to `docs/architecture.md` from
`~/.claude/templates/architecture-md.md` and leaves a pointer here. This table
and § Runtime Data Flow never move — they are operational instruments._

## External Integrations

None currently. The backend is self-contained and does not call third-party APIs.

| Service | Purpose | Auth Method | Base URL / SDK | Rate Limits | Notes |
|---------|---------|-------------|----------------|-------------|-------|

A CRA / government tax-bracket API sync was scoped originally (the unused
backend `httpx` dependency hints at it) but is not on the roadmap.

## Provisioned Infrastructure

Stateful and long-lived resources this project owns. Pinned identities live in
committed config (`docker-compose.yml`); this table is the human-readable
registry and mirrors the global port registry
(`~/.claude/references/port-registry.yaml`). Update it whenever infrastructure
is added, swapped, or decommissioned. See [[resource-naming]].

| Resource | Identity | Host port | Daemon | Notes |
|----------|----------|-----------|--------|-------|
| `tax-billing-db` | `postgres:16-alpine`; compose service `db`, `container_name: tax-billing-db`; volume `postgres_data`; network `tax-billing-network` | `127.0.0.1:5435` → 5432 | Docker Desktop via WSL integration (context `default`) | `active`. Registry entry added 2026-09-01 (TASK-018); postgres range 5433–5452. Holds all real financial data — the volume survives `docker compose down`, but `down -v` wipes it (schema.sql re-runs). |
| `tax-billing-backend` | FastAPI/uvicorn; compose service `backend`, `container_name: tax-billing-backend` | `127.0.0.1:8000` → 8000 | same daemon | `active`. App dev server — exempt from the port registry. Loopback-bound until auth lands (Milestone 3, ADR #6). |
| `tax-billing-frontend` | Flet web; compose service `frontend`, `container_name: tax-billing-frontend` | `127.0.0.1:8080` → 8080 | same daemon | Declared in compose but not yet the working path. Containerized web is the canonical run mode (ADR #4) and gets wired into `mise run up-all` in Milestone 5. App dev server — registry-exempt. |

_One canonical Docker daemon serves all of the above: Docker Desktop via WSL
integration. A native systemd `dockerd` must stay inactive — two daemons can
each hold an identically-named container on the same published port while
backing divergent data ([[resource-naming]] § One Canonical Docker Daemon)._

**Open gap:** `docker-compose.yml` has no top-level `name:`, and neither the
`postgres_data` volume nor the `tax-billing-network` network is `name:`-pinned,
so their real identities are prefixed with the *directory basename* — which
differs inside every worktree and silently forks state. Logged as **DW-009** in
[[workflow/tasks/discovered]].

## Data Model

Single-tenant PostgreSQL schema. 9 tables, UUID primary keys, `DECIMAL(12,2)` money.

```
business_settings (singleton)
    └── province, hst_number, payment_terms, backup config

clients ──────────────┐
  (soft-deleted)      │
                      ▼
                   invoices ────────────┐
                     (status enum)      │
                     year_billed generated
                                        ▼
                                     payments
                                       (method enum)

tax_years ──┬── federal_tax_brackets    (by year)
            ├── provincial_tax_brackets (by province+year)
            └── sales_tax_rates         (by province+year)

backup_logs  (wired — TASK-001 shipped 2026-04-10, PR #4)

Views:
  v_tax_summary     (year → paid/pending revenue, taxes)
  v_client_summary  (client → invoice totals)
```

Full DDL in `database/schema.sql`. Seed data (CRA 2025/2026 federal +
Ontario provincial brackets) in `database/seed_data.sql`.

## Runtime Data Flow

_Source of truth for integration wiring: every domain component appears in
the flow with at least one arrow in and one arrow out. Update whenever the
pipeline gains, loses, or rewires a component._

```
TODO: draw the runtime flow. Stub added by /migrate-workflow (v01) on
2026-09-01 — drawing it is director/architect work, planned for the
Milestone 3 auth plenary. Unverified sketch to expand:

  Flet views -> api_client (httpx) -> FastAPI routers (/v1/*)
    -> services (tax_calculator | invoice_pdf | backup_service)
    -> SQLAlchemy models -> PostgreSQL (tax-billing-db)
  PDF:    invoice_pdf -> Jinja2 template -> WeasyPrint -> attachment download
  Backup: clients/payments routers -> backup_service -> pg_dump
            -> backups/ bind mount + backup_logs row
```

## Known Limitations

- **Single-tenant by design.** One business, one user. No multi-tenancy, ever. The tool is built for a sole proprietor, and adding tenancy would fundamentally change the data model.
- **Ontario-first, other provinces partial.** The seed data covers federal + Ontario brackets comprehensively; other provinces have sales tax rates only. Adding full provincial brackets for BC/QC/AB/etc. is feasible but not planned.
- **Not a payment processor.** Payments are recorded after the fact. The tool never touches a credit card, bank account, or payment gateway.
- **Manual backup restore is destructive.** `POST /v1/backup/restore` replaces the entire database. There is no partial restore and no undo. Milestone 3 hardens this endpoint with auth + validation; Milestone 1 cannot fully fix it without auth.
- **Schema changes require data wipe until Milestone 4.** The compose init-volume hack means every DDL change during Milestones 1-3 goes in by editing `schema.sql` + `docker compose down -v`. Plan schema work carefully.

## Milestones

| Milestone | Target | Status | Notes |
|-----------|--------|--------|-------|
| 0 — Workflow Scaffold | 2026-04-10 | `complete` | Tag: `milestone-00-workflow-scaffold` |
| 1 — Stop the Bleeding | 2026-09-01 | `complete` | Tag: `milestone-01-stop-the-bleeding` — 10/11 complete, TASK-003 deferred → M3; + ad-hoc TASK-017/018 |
| 2 — Quality Gates | — | `active` | Decomposed, not started (see [[workflow/tasks/milestone-02-quality-gates]]): pyproject, ruff, mypy, pytest; TDD on tax_calculator; vertical slice |
| 3 — Auth (L3) | — | `pending` | Single-user JWT auth, login, router decorator, harden restore endpoint |
| 4 — Migrations | — | `pending` | Adopt Alembic, convert schema.sql, drop init-volume hack |
| 5 — Containerize Frontend | — | `pending` | Canonical containerized Flet web; rename frontend task to desktop |
| 6 — Dep Hygiene | — | `pending` | Trim cargo-culted deps now that auth has locked in what stays |
| 7 — Network Exposure | — | `pending` | Exposure model, HTTPS, headers, CORS, `/security-audit` pass |
