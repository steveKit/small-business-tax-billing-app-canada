# Handoff 007 — 2026-10-07

> Snapshot of session 007: statements below were true at write time.
> Current state lives in [[PROJECT]] and [[TASKS]] — this file is the bridge
> into the next session, not the store of record.

## Session Summary

This was an operational session, not a development one: the user ran the tool
for day-to-day business. There were no product-code commits and no PRs, and no
task was started. Two bookkeeping commits went direct to `main` and were
pushed: `f8ac09d` (the first version of this handoff) and `e62b8dd` (the
TASK-019 filing). Before this revision, `main` = `origin/main` at `e62b8dd`
with a clean tree. Milestone 2 is now 0/6, all `pending`
([[workflow/tasks/milestone-02-quality-gates]]).

- The stack was started with `docker compose up -d db backend` and
  `mise run web` (unsandboxed, in the background) at http://localhost:8080.
- The user updated the business address in the Flet **Settings** view. That
  is a data change to the `business_settings` row, not a code change. The PDF
  service reads that row on every render (`routers/invoices.py` queries it at
  request time), so new invoice PDFs and re-downloads of older ones carry the
  new address. The address is deliberately left out of this repo (see
  Blockers).
- The user created invoice `2026-CACEA-001` and marked it `pending`. The
  director confirmed both changes from inside the backend container. The books
  now hold 11 invoices.
- Shutdown: the Flet process was stopped by PID after matching its working
  directory, then `docker compose stop` ran. The data volume was not touched.
  The recipes are in [[workflow/memory/MEMORY]] § Operating the running stack
  from a director session.
- Pushing `f8ac09d` returned GitHub's Dependabot banner: 17 open alerts on
  `main`, all in `backend/requirements.txt` (1 critical, 5 high, 8 medium,
  3 low, across `python-jose`, `python-multipart`, `weasyprint`, `jinja2` and
  `pytest`). The director read them at source through the Dependabot alerts
  API. One weasyprint medium (GHSA-jhhc-3hcp-qhm5) has no patched version yet.
  The user chose to file this as a task at reduced priority, because the tool
  runs loopback-only for one user, so the blast radius is small. It became
  **TASK-019** `[P2]` in [[workflow/tasks/milestone-02-quality-gates]], with
  provenance row DW-026 in [[workflow/tasks/discovered]]
  (`promoted → TASK-019`).

## Files Changed

- `workflow/handoffs/handoff-007.md` — this handoff, first written at
  `f8ac09d` and revised in place to cover the TASK-019 tail
- `workflow/handoffs/INDEX.md` — handoff-007 row appended, then its summary
  refreshed for the TASK-019 tail
- `PROJECT.md` — § Status rewritten for this session, then its in-flight line
  moved to 0/6 with a TASK-019 mention
- `workflow/memory/MEMORY.md` — new section, Operating the running stack from
  a director session
- `CLAUDE.md` — Project Map "Latest handoff" pointer moved to handoff-007
- `workflow/tasks/milestone-02-quality-gates.md` — TASK-019 block added after
  TASK-012
- `workflow/tasks/discovered.md` — DW-026 row added (severity `next`,
  promoted to TASK-019)
- `TASKS.md` — Milestone 2 rollup moved from 0/5 to 0/6

This list is `git diff --name-status 9f53f95 e62b8dd` against the session
base. No product code changed: no `.py`, compose or template file. The
address update and the new invoice are data in the running database, not
files.

## Blockers & Open Questions

- **New: repo visibility vs. PII in committed workflow docs.** The GitHub repo
  is public (`gh repo view` reports PUBLIC). The handoff chain, task Notes and
  [[PROJECT]] already carry client names, invoice prefixes and revenue
  figures. This handoff deliberately leaves out the owner's address and the
  invoice amounts. Question for the user: should the repo go private, or
  should `workflow/**` and [[PROJECT]] adopt a redaction convention for client
  identifiers and figures?
- **Observation, not a blocker:** invoice `2026-BEE-004` (created 2026-09-22)
  is still `draft`. It was flagged this session and not acted on.
- **Carried from [[workflow/handoffs/handoff-006]]:**
  - Two user questions gate DW-010 and part of TASK-011. What does "current
    tax" mean on the dashboard? Should self-employed CPP be included in the
    holdback?
  - [[PROJECT]] § Runtime Data Flow is still a TODO stub.
  - All 12 ADR Consequences cells still read `—`. #6, #8, #9 and #12 are the
    ones worth enriching.
  - [[CLAUDE]] § Commands still has forward references to `mise run desktop`
    and `mise run up-all`, to be resolved in M5.
  - TASK-008 needs a dev-dependency proposal for `ruff` before anything is
    installed.
- **Resolved:** the tax-billing entry in `~/.claude/references/port-registry.yaml`
  is committed in the config repo (its `git status` was clean today), so it is
  dropped from the carried list.

## Next Steps

1. **Decide** the repo-visibility / PII question above, before more client
   data builds up in public history.
2. **Unblock** the dashboard work by answering its two questions. Then fold
   DW-008 and DW-011 into TASK-011's acceptance criteria and queue the DW-010
   dashboard task after it.
3. **Milestone 2, in order:** TASK-008 (dev-dep proposal first; fold in
   DW-003 `.gitattributes`, DW-004, and DW-022's tier block plus a home for
   the frontend linter), then TASK-009/010, then TASK-011 (TDD; read
   `backend/app/services/tax_calculator.py` first), then TASK-012, then
   TASK-019 (the Dependabot bumps). TASK-019 depends on TASK-008 because the
   pins land in the `backend/pyproject.toml` that TASK-008 creates. It is P2
   because the tool is loopback-only with one user. Separately, decide whether
   a CI task (the DW-019/014/015/018 cluster) joins M2.
4. **Optional, cheap:** correct the seven defaulted DW severities and enrich
   the four ADR Consequences cells.
5. **Later:** the Milestone 3 plenary draws § Runtime Data Flow and picks up
   TASK-003 (under ADR #12) and DW-001.

Reference [[TASKS]] for the full queue context.

## Files to Read on Resume

- [[PROJECT]] — § Status, the ADR table, and the § Runtime Data Flow stub
- [[TASKS]] — the milestone index
- [[workflow/tasks/milestone-02-quality-gates]] — the next work, starting
  with TASK-008
- [[workflow/tasks/discovered]] — read Severity and Disposition only; the log
  was fully triaged in session 006, so don't re-triage it.
  `docs/reports/gate-audit-2026-09-01.md` is the source for DW-014 through
  DW-025.
- [[workflow/memory/MEMORY]] — machine facts plus the recipes for running the
  stack
