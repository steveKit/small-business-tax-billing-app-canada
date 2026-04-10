# Handoff 001 — 2026-04-10

## Session Summary

Plenary session for `tax-billing` project. Existing-project plenary — the codebase has been live since 2026-02-09 but had zero workflow scaffolding. Produced the full scaffold on branch `chore/workflow-scaffold`:

- `CLAUDE.md` — stack, commands, project map, conventions, gotchas
- `PROJECT.md` — status, 9 architecture decisions, data model, 8 milestones
- `TASKS.md` — Milestones 0-1 fully decomposed; Milestones 2-7 sketched
- `security-profile.yaml` — L3
- `.claude/settings.json` — initial allow-list for mise/ruff/mypy/pytest/pip
- `Handoffs/handoff-001.md` — this file
- `.gitignore` extended with `.claude/worktrees/` and tighter secrets patterns

Read-only plenary audit dispatched to an architect agent. Full report informs every decision below. No source code was touched.

## Key Decisions

Nine recorded in [[PROJECT]] § Architecture Decisions. Summary:

1. **Security profile: L3.** User mandate: "let's harden this."
2. **Coding paradigm: layered.** Matches existing shape.
3. **Testing paradigm: adaptive.** TDD for tax math, test-after elsewhere.
4. **Auth: JWT Bearer.** Milestone 3; details at Milestone 3 plenary.
5. **Single-user tenancy.** Sole-prop tool, one admin.
6. **Canonical frontend: containerized Flet web.** Milestone 5 makes it so.
7. **Desktop-mode kept** as `mise run desktop` — dev convenience.
8. **Alembic deferred to Milestone 4.** Current DDL hack is accepted debt until then.
9. **Decimal money.** Pre-existing; recorded for the historical record.

Full rationale and dates in [[PROJECT]].

## Files Changed

All new, no source code touched. See Session Summary for the list.

`.gitignore` is the only existing file edited:
- Added `.claude/worktrees/`
- Tightened secrets patterns: broader `.env.*` with `!.env.example` exception; explicit `*.pem`, `*.key`, `*.crt`, `credentials.json`, `secrets.*`

## Blockers & Open Questions

- **Stale root-owned backup files in `backups/`** — 8 `.json` files from an older backup implementation, un-deletable without sudo. Tracked as TASK-006.
- **TASK-003 is a data-loss event.** Regenerating `.env` credentials requires `docker compose down -v` which wipes the `postgres_data` volume. User should export current data first if they've been actively using the tool.
- **Milestone 3 needs a focused plenary** before work starts — token lifetime, refresh strategy, password reset flow, Flet login UX.

## Discovered Work

None yet — plenary session only. Every finding became a formal task.

## Next Steps

1. **P0** — User reviews the scaffold PR (`chore/workflow-scaffold`), merges.
2. **P0** — Start Milestone 1 with TASK-001 (fix broken auto-backup). TDD-eligible.
3. **P0** — TASK-002 + TASK-003 (extract hardcoded credentials, generate strong secrets) are data-loss events; user exports current data first.
4. **P1** — Milestone 2 (quality gates) after Milestone 1 closes cleanly.
5. **P2** — Schedule Milestone 3 plenary before starting auth work.

Reference [[TASKS]] for the full queue context and acceptance criteria.

## Files to Read on Resume

- [[CLAUDE]] — project conventions (just authored; must be the baseline)
- [[PROJECT]] — architecture decisions
- [[TASKS]] — Milestone 1 is next; TASK-001 first
- `backend/app/services/backup_service.py` — the broken auto-backup path
- `backend/app/routers/clients.py` — one of the TASK-001 call sites
- `docker-compose.yml` — the TASK-002 / TASK-004 target

## Library Candidates

_Skip — nothing extractable from a plenary session._
