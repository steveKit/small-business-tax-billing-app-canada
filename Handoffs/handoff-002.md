# Handoff 002 — 2026-04-10

## Session Summary

End-of-session handoff for the plenary session that bootstrapped the
`tax-billing` workflow. Supersedes `[[Handoffs/handoff-001]]`, which was
written mid-session before the PRs existed.

**Two PRs merged on `main` this session:**
- **PR #1** (`f2bed4b`) — `chore(workflow): plenary scaffold for tax-billing` — authored `CLAUDE.md`, `PROJECT.md`, `TASKS.md`, `security-profile.yaml`, `.claude/settings.json`, `Handoffs/handoff-001.md`, and extended `.gitignore`. Reviewer requested 7 changes (2 major, 5 minor), all addressed in fixup commit `b4f382d` before merge.
- **PR #2** (`6a7a15a`) — `docs(tasks): close Milestone 0` — ticked TASK-000, moved it to Completed Tasks, collapsed the Milestone 0 header to a stub, recorded the tag pointer.

**Milestone 0 tag:** `milestone-00-workflow-scaffold` (annotated, pushed)

**Branch state:** clean. Only `main` exists locally and remotely. Both feature branches (`chore/workflow-scaffold` and `chore/close-milestone-0`) deleted after squash-merge.

No source code was touched in this session. The architect agent conducted a read-only audit; everything it flagged became a task in Milestone 1 (`[[TASKS]]`).

## Key Decisions

All 9 architecture decisions recorded in `[[PROJECT]]` § Architecture Decisions. Summary: **L3 security profile** (hardening mandate), **layered paradigm**, **adaptive testing** (TDD for tax math, test-after elsewhere), **JWT Bearer auth** (Milestone 3), **single-user tenancy**, **containerized Flet web as canonical** with **`mise run desktop` kept as dev convenience**, **Alembic deferred to Milestone 4**, **Decimal money** (pre-existing, recorded).

Two process decisions worth remembering for future sessions:
- **Post-merge housekeeping uses a throwaway branch.** The pre-tool-safety hook blocks main commits even for the director. When closing a milestone, create `chore/close-milestone-NN`, push, open a fast-track PR, user approves, squash-merge. Adds one step but stays protocol-compliant.
- **Agents cannot write `.claude/settings.json`** — the hook refuses both agent Write/Edit and director Edit on that file. When settings need updating, present the exact JSON patch to the user and have them apply it. This is intentional and correct.

## Files Changed

All new files unless noted. See `git diff 81a3886..HEAD --name-status` for the full list.

- `CLAUDE.md` (new, ~188 lines) — stack, commands, project map, conventions, gotchas
- `PROJECT.md` (new, ~97 lines) — status, 9 architecture decisions, data model, 8 milestones
- `TASKS.md` (new, ~281 lines) — Milestone 0 closed; Milestone 1 fully decomposed; Milestones 2-7 sketched
- `security-profile.yaml` (new, 49 lines) — L3 profile
- `.claude/settings.json` (new, user-created per hook policy) — read-only mise tasks + ruff/mypy/pytest/pip-read + docker-compose-read + git-read
- `Handoffs/handoff-001.md` (new) — seed handoff, superseded by this file
- `Handoffs/handoff-002.md` (new) — this file
- `.gitignore` (edited, +17 lines) — tightened secrets patterns, `.claude/worktrees/`

## Blockers & Open Questions

Carried over from `[[Handoffs/handoff-001]]` — all still live for the next session:

- **TASK-003 is a data-loss event.** Regenerating `.env` credentials requires `docker compose down -v`, which wipes the `postgres_data` volume. **Export current data first** if the tool has real client records. The next session must flag this before starting TASK-002/003.
- **Stale root-owned files in `backups/`.** Eight `.json` files from a previous backup implementation, un-deletable without elevated privileges. Tracked as TASK-006. Director will provide the removal command; user runs it with root.
- **Milestone 3 needs a focused plenary** before auth work starts. Open questions: token lifetime, refresh strategy (or none), password reset flow (probably none — single user), Flet login view UX.
- **Broken auto-backup code path is still live.** TASK-001 fixes it, but until that task ships, any `POST /v1/clients` or `POST /v1/payments` will crash on the auto-backup call. Don't exercise the app against real data until TASK-001 lands.

## Next Steps

Prioritized recommendations for the next session, all referenced in `[[TASKS]]`:

1. **P0 — TASK-001** (Fix broken auto-backup crash path). S-sized, TDD-eligible, isolated, and blocks TASK-007. This is the cleanest first task: pure backend, clear contract, and proves the TDD-dispatch flow works on this project before larger tasks.
2. **P0 — TASK-002 + TASK-003** (Extract hardcoded credentials, generate strong secrets). Do these **in sequence** with a data export step between. Flag the data-loss warning before dispatching.
3. **P0 — TASK-004** (Bind backend to `127.0.0.1`). Safe quick win. Can run in parallel with TASK-001 if desired — no file overlap.
4. **P1 — TASK-005** (Fix `datetime.utcnow()`). Trivial safety net; can batch with TASK-001 since it touches `backup_service.py` too.
5. **P2 — TASK-006** (Clean up `backups/*.json`). User-gated (requires root), cosmetic, do whenever convenient.
6. **P0 — TASK-007** (Milestone 1 integration verification) after 001-006 land.
7. **Then** Milestone 2 (Quality Gates).

Recommended first dispatch: **TASK-001 in TDD mode**. Interface spec = the reconciled `BackupService` signature. Tester first, implementer second, tester-verify third.

## Files to Read on Resume

- `[[CLAUDE]]` — project conventions baseline
- `[[PROJECT]]` — architecture decisions, milestones
- `[[TASKS]]` — Milestone 1 is next
- `backend/app/services/backup_service.py` — TASK-001 primary target
- `backend/app/routers/clients.py` — TASK-001 call sites at lines 63, 112, 138
- `backend/app/routers/payments.py` — TASK-001 call sites at lines 125, 221
- `docker-compose.yml` — TASK-002, TASK-004 target
