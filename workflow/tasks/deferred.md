# Deferred Work — tax-billing

> Index: [[TASKS]]
> **Disposition key:** `open` | `promoted → [[workflow/tasks/milestone-NN-slug]] TASK-NNN` | `dropped (reason)`

| ID | Description | Deferred from | Reason | Disposition |
|----|-------------|---------------|--------|-------------|
| DEF-001 | TASK-003 — generate strong secrets in `.env`: replace the placeholder `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` with `secrets.token_urlsafe(32)` values and document the generation command in `.env.example`. | [[workflow/tasks/milestone-01-stop-the-bleeding]] TASK-003 | User decision 2026-09-01 (session 006, milestone close): not urgent for a local-only tool — every published port is loopback-bound (TASK-004) and `JWT_SECRET_KEY` is unused until auth lands in M3, so rotation naturally belongs with the auth work. **Re-scope on pickup to the non-destructive procedure**: `ALTER USER … PASSWORD` inside the running `tax-billing-db` container + `.env` edit (`POSTGRES_PASSWORD`, `DATABASE_URL`) + `docker compose up -d` to recreate the backend — no `down -v`, no data loss. Drop the original AC 3 (`down -v` rebuild) accordingly; the volume holds real financial records. | `open (target M03)` |

> Don't delete rows when an item is promoted or dropped — update the
> disposition. The recorded disposition is what keeps a parked item from being
> silently lost.
