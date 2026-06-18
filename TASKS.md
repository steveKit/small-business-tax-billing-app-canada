# Task Index — tax-billing

> **Milestone status:** `pending` (stub — not yet exploded) | `active` (exploded, in progress) | `deferred` (parked — body preserved) | `complete`
> **Task status (inside milestone files):** `pending` | `in_progress` | `blocked` | `complete`
> See [[PROJECT]] for architecture decisions and [[CLAUDE]] for conventions.

## How this works

- Each milestone has its own file under `tasks/` holding its tasks in full detail.
- Future milestones live here as **one-line stubs** until activated. Only the
  **planner** explodes a stub into its milestone file (never the director or
  other agents).
- Completed tasks stay in their milestone file. When a milestone closes, that
  frozen file is the milestone's permanent archive — there is no separate archive.
- Two cross-milestone logs: [[tasks/deferred]] and [[tasks/discovered]].

## Active Milestones

| Milestone | Status | Progress | File |
|-----------|--------|----------|------|
| Milestone 01: Stop the Bleeding | `active` | 8/11 tasks | [[tasks/milestone-01-stop-the-bleeding]] |
| Milestone 02: Quality Gates | `active` | 0/5 tasks (decomposed, not started) | [[tasks/milestone-02-quality-gates]] |

_The milestone file is the source of truth for per-task status. The Progress
column is a coarse rollup the director updates at task/milestone events — keep it
loose to avoid index drift._

## Planned Milestones (stubs)

| # | Milestone | Scope (one line) | Depends on |
|---|-----------|------------------|------------|
| 03 | Auth (L3 core) | Single-user JWT auth: login, `get_current_user` dep on all `/v1/*`, harden `POST /v1/backup/restore`, remove the 127.0.0.1 bind. Focused plenary at start. (planned tag `milestone-03-auth`) | M01, M02 |
| 04 | Migrations | Adopt Alembic; convert `schema.sql` to initial migration; drop the compose init-volume hack. (planned tag `milestone-04-migrations`) | M03 |
| 05 | Containerize Frontend | Make containerized Flet web canonical; rename `frontend`→`desktop`; finalize CORS. (planned tag `milestone-05-frontend-container`) | M02 |
| 06 | Dep Hygiene | Remove cargo-culted deps (`httpx`, `psycopg2-binary`) once auth locks in what stays. (planned tag `milestone-06-dep-hygiene`) | M03 |
| 07 | Network Exposure | Exposure model, HTTPS+HSTS, security headers, CORS finalize, login rate-limit, full L3 `/security-audit`. (planned tag `milestone-07-network-exposure`) | M03 |

_For an emergent/feature-driven project this table may be empty or hold a single
"next" stub; append milestones as features emerge (often promoted from
[[tasks/discovered]])._

## Deferred Milestones

_None._

## Completed Milestones

| Milestone | Completed | Tag | File |
|-----------|-----------|-----|------|
| Milestone 00: Workflow Scaffold | 2026-04-10 | `milestone-00-workflow-scaffold` | [[tasks/milestone-00-workflow-scaffold]] |

## Logs

- [[tasks/deferred]] — task-level deferred / descoped work, with disposition
  (whole-milestone deferral lives in § Deferred Milestones above)
- [[tasks/discovered]] — discovered-work log (feeds future milestone stubs)
