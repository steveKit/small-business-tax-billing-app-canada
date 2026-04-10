# tax-billing — Project Overview

See [[CLAUDE]] for agent conventions and [[TASKS]] for the work queue.

## Status

**Phase:** Hardening
**Last Updated:** 2026-04-10

The project was built in Feb 2026 as a personal Canadian sole-proprietor
tax-holdback calculator + invoicing tool. It functions but is unhardened:
no auth, no tests, no lint/type-check, hardcoded credentials in committed
files, a broken auto-backup code path, and an unauthenticated SQL restore
endpoint. A workflow plenary was held on 2026-04-10 and the project is
now being hardened to L3 for eventual network exposure.

**Milestone 0 (Workflow Scaffold) is complete** as of 2026-04-10 —
tagged `milestone-00-workflow-scaffold`. No code was touched; only
documentation, configuration, and ignore rules. The next session will
pick up Milestone 1 (Stop the Bleeding) on user selection.

## Architecture Decisions

| # | Decision | Choice | Rationale | Date |
|---|----------|--------|-----------|------|
| 1 | Coding paradigm | Layered / service-oriented | Matches the existing `routers → services → models` shape; no refactor needed. FastAPI idiomatic. | 2026-04-10 |
| 2 | Testing paradigm | Adaptive | TDD for pure tax math (high-stakes, clear contracts); test-after for routers/views/wiring. | 2026-04-10 |
| 3 | Security profile | L3 | Handles PII + authoritative tax math + financial amounts; will eventually be network-exposed. "Harden this" is an explicit mandate from the user. | 2026-04-10 |
| 4 | Canonical frontend run mode | Containerized Flet web (port 8080) | One code path to secure, works on any host, suits network exposure target. | 2026-04-10 |
| 5 | Desktop-mode escape hatch | Kept as `mise run desktop` | Native window UX is pleasant for daily bookkeeping on WSL2/WSLg. Documented as non-canonical dev convenience. | 2026-04-10 |
| 6 | Auth mechanism | JWT (Bearer in `Authorization` header) | Stateless, scriptable via `curl`, keeps `python-jose` non-cargo-culted. CSRF-exempt because not cookie-based. Details finalized at Milestone 3 plenary. | 2026-04-10 |
| 7 | Tenancy model | Single-user (sole-prop) | The domain is one business owner. No multi-tenancy, no user registration, no role hierarchy. One admin user, one password. | 2026-04-10 |
| 8 | Migration tooling | Alembic (deferred to Milestone 4) | Current compose init-volume approach forces `down -v` data loss on any schema change. Unacceptable for a tool holding real financial records. | 2026-04-10 |
| 9 | Money handling | `Decimal` end to end | Floats are unacceptable for financial math. DB columns are `DECIMAL(12,2)`; Python quantizes to `Decimal("0.01")`. | 2026-04-10 (pre-existing, recorded) |

## External Integrations

None currently. The backend is self-contained and does not call third-party APIs.

| Service | Purpose | Auth Method | Base URL / SDK | Rate Limits | Notes |
|---------|---------|-------------|----------------|-------------|-------|

A CRA / government tax-bracket API sync was scoped originally (the unused
backend `httpx` dependency hints at it) but is not on the roadmap.

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

backup_logs  (orphaned — see TASK-001)

Views:
  v_tax_summary     (year → paid/pending revenue, taxes)
  v_client_summary  (client → invoice totals)
```

Full DDL in `database/schema.sql`. Seed data (CRA 2025/2026 federal +
Ontario provincial brackets) in `database/seed_data.sql`.

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
| 1 — Stop the Bleeding | — | `pending` | P0 fixes: broken auto-backup, hardcoded secrets, utcnow deprecations, localhost bind |
| 2 — Quality Gates | — | `pending` | pyproject, ruff, mypy, pytest; TDD on tax_calculator; vertical slice |
| 3 — Auth (L3) | — | `pending` | Single-user JWT auth, login, router decorator, harden restore endpoint |
| 4 — Migrations | — | `pending` | Adopt Alembic, convert schema.sql, drop init-volume hack |
| 5 — Containerize Frontend | — | `pending` | Canonical containerized Flet web; rename frontend task to desktop |
| 6 — Dep Hygiene | — | `pending` | Trim cargo-culted deps now that auth has locked in what stays |
| 7 — Network Exposure | — | `pending` | Exposure model, HTTPS, headers, CORS, `/security-audit` pass |
