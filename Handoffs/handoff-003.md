# Handoff 003 — 2026-04-10

## Session Summary

Milestone 1 went 4-for-7 in one session. Started from clean `main` at
`3cb176c` (post-handoff-002 merge). Dispatched two parallel worktree
batches; both shipped after review:

- **PR #5** (`d30b558`) — `chore(security): TASK-002 + TASK-004` —
  extracted hardcoded credentials to `.env` refs and bound all compose
  services to `127.0.0.1` as a pre-auth mitigation. First-pass review
  approved with only minor nits (deferred).
- **PR #4** (`6f0b09b`) — `fix(backup): TASK-001 + TASK-005` —
  reconciled `BackupService` with its 7 call sites, wired the
  orphaned `backup_logs` table, and finished the `datetime.utcnow()`
  deprecation sweep. **Reviewer flagged 3 major issues on first pass**
  and required a fix cycle before approval — see Key Decisions below.

**Branch state:** clean on `main` at `6f0b09b`. Both feature branches
deleted locally + remote after squash-merge. Both worktrees
(`.claude/worktrees/agent-aa3f0738`, `.claude/worktrees/agent-ae4c2cc3`)
removed. This handoff itself is being shipped on `chore/handoff-003`
and will be fast-track merged before next session starts.

Three Milestone 1 tasks remain: **TASK-003** (strong secret generation,
user-gated **data-loss event**), **TASK-006** (stale backup file cleanup,
user-gated privilege-escalation command), and **TASK-007** (integration
verification + milestone tag). All three need direct user action before
the director can proceed — they cannot be dispatched to background
agents.

## Key Decisions

- **Service layer never owns the request transaction.** TASK-001's first
  implementation had `create_backup` calling `await self.db.commit()`
  mid-request, per the director's dispatch spec. Reviewer correctly
  pushed back: the FastAPI `get_db` dependency owns the request
  transaction, so services should `add() + flush()` and let the
  dependency commit. The fix commit (`1f24665`) dropped the mid-service
  commit and the `BackupLog` insert now rides on the enclosing
  transaction — atomic with the triggering client/payment mutation.
  **Director lesson:** when writing dispatch specs that touch DB work,
  specify `flush()` only and call out the dependency's commit ownership
  explicitly. Don't paper over the architecture by asking services to
  commit "for safety."
- **Async all the way down is not a slogan — it's a concrete asyncio
  rule.** TASK-001 shipped `async def create_backup` that internally
  called blocking `subprocess.run(pg_dump, ...)`, stalling the entire
  event loop on every client/payment POST. Reviewer caught it. Fix:
  `await asyncio.to_thread(subprocess.run, ...)` around both pg_dump
  and psql calls. Next session should consider whether to make this
  explicit in CLAUDE.md conventions ("any `async def` that shells out
  must use `asyncio.to_thread` or `asyncio.create_subprocess_exec`").
- **Subprocess `env=` should inherit `os.environ`, not replace it.**
  The original `BackupService` passed `env={"PGPASSWORD": password}`
  which stripped `PATH`/`HOME`/`LANG`/etc. Child process only had
  `PGPASSWORD`. Reviewer flagged as L3-relevant and fragile. Fix:
  `env={**os.environ, "PGPASSWORD": password}`. Applied to both
  pg_dump and psql calls. Pre-existing bug predating the PR, but the
  reviewer's same-file rule meant fixing now was cheaper than tracking
  it into a follow-up.
- **Bundling related tasks into one PR is fine when file overlap is
  unavoidable.** TASK-001 and TASK-005 both touched `backup_service.py`;
  TASK-002 and TASK-004 both touched `docker-compose.yml`. Rather than
  sequential PRs with conflicts, combined them into two PRs (#4 and #5)
  with clearly labeled commit bodies. Future sessions should keep this
  pattern for file-overlapping task groups — it was cleaner than
  arbitration.
- **Line endings are inconsistent across the repo.** Two files
  (`docker-compose.yml`, `.env.example`) flipped CRLF→LF during TASK-002
  edits. No `.gitattributes` enforces normalization. Added to Discovered
  Work as a prospective task — decide whether to normalize before
  Milestone 2 or let ruff/format handle Python files and leave
  YAML/markdown drift alone.

## Files Changed

- `backend/app/services/backup_service.py` — rewritten for TASK-001 + TASK-005 + fix-cycle hardening (async subprocess, inherited env, flush-not-commit)
- `backend/app/routers/backup.py` — wired `db` dependency, awaits both service methods
- `backend/app/services/tax_calculator.py` — `datetime.utcnow()` → `datetime.now(timezone.utc)` in `get_tax_summary`
- `docker-compose.yml` — env refs on all credentials, `env_file: .env` on db + backend, 127.0.0.1 binds on all 3 services, TASK-004 comment
- `backend/app/config.py` — `database_url` and `jwt_secret_key` no longer have defaults (pydantic-settings fails fast)
- `.env.example` — added `POSTGRES_USER/PASSWORD/DB`, documented the compose variable-expansion gotcha, pointed at `secrets.token_urlsafe(32)`
- `README.md` — tightened setup step and Environment Variables table
- `TASKS.md` — 4 tasks moved to Completed Tasks with full acceptance-criteria ticking and notes; 5 new Discovered Work items added
- `PROJECT.md` — status paragraph reflects session 003 progress, Milestone 1 now `in_progress`, `backup_logs` table no longer labeled orphaned
- `CLAUDE.md` — Project Map latest-handoff pointer updated to 003
- `Handoffs/handoff-003.md` — this file

## Blockers & Open Questions

- **TASK-003 blocks on the user — data-loss event.** Because TASK-002 made
  `POSTGRES_USER`/`POSTGRES_PASSWORD` required env vars with no defaults,
  any value change will fail to match the existing `postgres_data`
  volume (initialized with `postgres:postgres` on first run). Bringing
  the new `.env` live requires `docker compose down -v`, which wipes
  all client/invoice/payment data. The user must decide whether to
  (a) export current data first, (b) accept the wipe (fresh dev), or
  (c) defer TASK-003 until after a data backup strategy is in place.
  Director CANNOT do this — `.env` is gitignored and secrets generation
  is local-only. **Next session must present this choice before
  starting any Milestone 1 work.**
- **TASK-006 blocks on elevated privileges.** 8 stale `root`-owned
  `.json` files in `backups/` from a pre-plenary backup implementation.
  Director provides the removal command; user runs it with elevated
  privileges. Agents cannot escalate privileges. Cosmetic — does not
  block TASK-007, but should be cleared for a clean Milestone 1 close.
- **TASK-007 cannot start until TASK-003 lands.** Its first acceptance
  criterion is `docker compose down -v && docker compose up -d`
  rebuilds cleanly with new `.env`. Without TASK-003 populating the
  new required vars, `docker compose up` will fail at startup
  (pydantic-settings will raise `ValidationError` for missing
  `DATABASE_URL`/`JWT_SECRET_KEY`). So TASK-003 → TASK-007 is a hard
  sequence.
- **Backup will write to a root-owned directory.** Per the CLAUDE.md
  Gotchas section and the TASK-001 implementer's flagged residual
  risk, the `backups/` bind mount is root-owned. After TASK-001 ships,
  `create_backup` will attempt to write a `.sql` file to that directory
  via `pathlib.Path.write_bytes`. If the backend container runs as root
  (check the Dockerfile), it will succeed. If it runs as a non-root
  user, the first auto-backup will crash the request. **TASK-007 should
  exercise this path** — POST a client, check the backup file landed,
  check the `BackupLog` row was inserted.
- **Director review spec caused the TASK-001 transaction bug.** Session
  003 showed that sloppy dispatch specs generate reviewer rework cycles.
  For Milestone 2+ dispatches, spec-writing should be tighter on
  transaction boundaries and async discipline. Possibly add a "DB work
  checklist" to the director agent definition — out of scope for this
  session.

## Discovered Work

Five items added to TASKS.md § Discovered Work this session:

- [ ] `_get_db_params` fragile URL parsing — backup_service will crash on passwords containing `:`, `@`, `/` (latent until TASK-003 generates a new password)
- [ ] Backup file disk-leak on partial failure — if `BackupLog` insert fails after pg_dump writes the file, the file stays on disk with no log row
- [ ] Line-ending drift / add `.gitattributes` — repo has mixed CRLF/LF; two files flipped during TASK-002
- [ ] Unused `from typing import Optional` in `backend/app/config.py` — ruff will catch in Milestone 2 (TASK-008)
- [ ] Redundant `env_file: .env` on the `db` compose service — minor cleanup in TASK-007 or later

## Next Steps

Next session must finish Milestone 1. **All three remaining tasks are
user-gated** and cannot run in parallel — they're a linear sequence:

1. **P0 — TASK-003 (data-loss event).** Director presents the choice:
   export data first, accept the wipe, or defer. If proceeding, the
   director provides the exact command sequence below and the user runs
   it. The director cannot edit `.env` — the hook forbids it and `.env`
   is gitignored.

   ```bash
   # Optional: export current data if there are real records
   docker compose up -d db
   docker exec tax-billing-db pg_dump -U postgres tax_billing \
     > backup-pre-task003-$(date +%Y%m%d).sql
   docker compose down

   # Generate new secrets
   python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

   # Edit .env (local file, gitignored) to contain:
   #   POSTGRES_USER=tax_billing_user
   #   POSTGRES_PASSWORD=<generated>
   #   POSTGRES_DB=tax_billing
   #   DATABASE_URL=postgresql+asyncpg://tax_billing_user:<generated>@db:5432/tax_billing
   #   JWT_SECRET_KEY=<generated>
   #   DEBUG=false
   #   API_URL=http://localhost:8000

   # Wipe volume and bring up with the new secrets
   docker compose down -v
   docker compose up -d
   ```

2. **P2 — TASK-006 (requires elevated privileges).** One command,
   cosmetic. Director provides the command, user runs it:

   ```bash
   sudo rm /home/horse/projects-linux/personal/tax-billing/backups/*.json
   ```

3. **P0 — TASK-007 (integration verification + Milestone 1 tag).**
   After TASK-003 and TASK-006 land, director dispatches the integration
   task (or runs it directly, since it's pure verification, not code).
   Acceptance criteria covered by TASK-007 in [[TASKS]]. On pass:
   create annotated tag `milestone-01-stop-the-bleeding` and push it,
   then mark Milestone 1 header `[complete]` with a stub and move
   TASK-003/006/007 to Completed Tasks. Per director protocol, the
   milestone auto-tag is mandatory and runs alongside the wiring audit.

4. **Then Milestone 2 (Quality Gates).** TASK-008 (pyproject + ruff),
   TASK-009 (mypy), TASK-010 (pytest + pytest-asyncio), TASK-011
   (TDD on `tax_calculator.py`), TASK-012 (vertical-slice smoke test).
   Ideally grouped: 008 → 009/010 in parallel → 011/012 in parallel
   (no file overlap once the infra is in).

## Files to Read on Resume

- [[CLAUDE]] — project conventions, commands, gotchas
- [[PROJECT]] — updated status section and milestones table
- [[TASKS]] § Milestone 1 — three remaining tasks with acceptance
  criteria; Completed Tasks section has the full postmortems of the
  four that shipped this session
- `backend/app/services/backup_service.py` — the final form after the
  fix cycle. Worth reading the `create_backup` flow end-to-end to
  understand the transaction ownership model before Milestone 2 tests
  are written against it
- `docker-compose.yml` — to see the final env_file + 127.0.0.1 wiring
- `.env.example` — the user's reference for TASK-003 secret population
- Next session should also read the `_get_db_params` function in
  `backup_service.py` — Discovered Work item flagged it as latent-fragile
  and TASK-003's new password could trip it
