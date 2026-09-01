# Handoff 006 — 2026-09-01

> Snapshot of session 006: statements below were true at write time.
> Current state lives in [[PROJECT]] and [[TASKS]] — this file is the bridge
> into the next session, not the store of record.

## Session Summary

One long session run entirely on `main`, from `01b1c1b` (post-handoff-005,
plus the never-recorded PR #24 task-layout migration) to `734ed63` — 14
commits, four phases. **Milestone 1 closed** and the project's workflow
config was brought from v0 to v15. Exactly one PR this session: **#25**
(`3918b41`, TASK-018, squash-merged); everything else was direct-to-main
bookkeeping, which the pre-tool-safety hook's bookkeeping gate now passes
prompt-free for workflow-state-only sets. **No open PRs, working tree
clean at `734ed63`.**

**Phase 1 — TASK-018 (ad-hoc P0): dev DB host port 5434 → 5435.**
`mise run up` failed at session start: `127.0.0.1:5434` was already held
by `adamson-next-2025-postgres-dev`, which is the *registered* owner of
5434 in the global port registry. tax-billing's 5434 predated the
registry and was unregistered, so per [[resource-naming]] § Ports Are
Pinned Identities tax-billing was the party that moved — to 5435, the
next free port in the postgres range 5433–5452, now registered. One-line
compose change, fast-tracked (director self-review), CI absent so the
local gate stood in: db healthy on 5435, `/health` 200, live data intact.
Recorded as ADR #11.

Two things that had happened outside the handoff chain were reconciled
here. The **real Adamson payments had been recorded out of band** —
`2026-Adamson-001` and `-002` are both `paid`, which closes the P0
blocker carried since handoff-005 — and **PR #24** (2026-06-18, the
monolithic-TASKS → indexed per-milestone migration) had never been noted
anywhere; it is now in [[PROJECT]] § Status. The frontend was launched
host-side (`mise run web`) for the user's own record keeping, then
stopped.

**Phase 2 — dashboard findings (user asked to "note for later").** Two
discovered-work items came out of reading the live dashboard against the
code. **DW-011 (tax math):** the revenue figures are `SUM(subtotal)`,
i.e. net of HST — $13,383.44 gross renders as $11,843.75 — and the
calculator has no basic personal amount, no self-employed CPP (the
largest single error), no Ontario surtax or health premium, an
annualization that uses today's calendar month regardless of which year
is being viewed, and a 1¢ bracket-edge gap. **DW-010 (dashboard):**
gross revenue exists in `v_tax_summary` but is never exposed or
rendered; projected tax exists in the API response
(`income_tax_calculation.total_income_tax`) but is never rendered; and
"current tax on collected revenue" does not exist at all — the holdback
is a proration, not a bracket computation on income to date. Routed: the
math goes into Milestone 2's TASK-011 acceptance criteria, the dashboard
work becomes a feature task queued *after* TASK-011. Both routings are
gated on two open user questions (see § Blockers).

**Phase 3 — Milestone 1 closed**, annotated tag
`milestone-01-stop-the-bleeding` at `7d42dcb`, final tally **10 of 11**.
TASK-006 removed the 8 dead pre-TASK-001 `.json` backups from the
root-owned `backups/` bind mount via `docker exec` running as root
inside the container — no host `sudo` needed, which is what had kept the
task user-gated for months. TASK-007 (integration verification) was
built to avoid destroying real data: the schema+seed init was proven in
a **throwaway** `postgres:16-alpine` container rather than
`docker compose down -v` on the real volume; `/health` 200; the
hardcoded-secrets and `utcnow` greps clean; the TASK-013/015/016
regressions confirmed against live production data plus a random-UUID
PATCH probe (422/404) instead of a synthetic create/delete cycle that
would have left test invoices in real books; LAN-IP reachability refused
on 8000, 5435 and 8080. The wiring audit found nothing Milestone 1
introduced to be orphaned, but surfaced two pre-existing issues (DW-012
unreferenced pydantic schemas, DW-013 `backup_logs` holding 21 rows
against 12 files on disk). **TASK-003 (strong secrets) was deferred to
Milestone 3** by user decision and re-scoped there to a non-destructive
rotation (ADR #12, [[workflow/tasks/deferred]] DEF-001). The full
discovered-work log was then triaged with the user item by item.

**Phase 4 — `/migrate-workflow`, v0 → v15, staged.** v01 stamped
`testing-paradigm: adaptive` and added the `## Runtime Data Flow` TODO
stub to [[PROJECT]]; v08 stamped `releasable: false`; v10 relocated
`Handoffs/`, `tasks/` and `memory/` under `workflow/` (4-check gate
green); v12 ran the gate-auditor — **11 gates expected, 0 present**,
which is by design since Milestone 2 is their home; the report is
`docs/reports/gate-audit-2026-09-01.md` and its findings are queued as
DW-014…DW-025, cross-referenced to TASK-008–012. v13 added the Severity
column to the discovered log, v14 added the workflow `.gitignore` block
(which cleared the sandbox phantom `??` entries), v15 added the
Consequences column to the ADR table. All 11 conformance items resolved:
tracked `.gitkeep`s under `.claude/{commands,hooks,skills}`, a genre
header on the gate-audit report, and `workflow/handoffs/INDEX.md`
backfilled. On the user's confirmation the **repo was hardened**: the
`protect-main` ruleset (block deletion, block non-fast-forward) is
active, and squash merges are pinned to `PR_TITLE` / `PR_BODY` with
merge and rebase merges disabled. CI is absent entirely → DW-019 (M2).
Stamped `workflow-version: 15`.

## Key Decisions

Lasting-impact only; the two formal ones are rows in [[PROJECT]]
§ Architecture Decisions.

- **ADR #11 — dev DB host port is `127.0.0.1:5435`, registered.** The
  registry is the arbiter of who moves; the unregistered party does. The
  backend still reaches the DB at `db:5432` in-network, so only host-side
  connection strings changed.
- **ADR #12 — secrets rotation is non-destructive.** `ALTER USER …
  PASSWORD` inside the running container plus a `.env` edit and a backend
  recreate — never `docker compose down -v`. The `POSTGRES_*` env vars
  only take effect at *first* initialization, so the original plan traded
  real financial records for something `ALTER USER` does in place.
- **TASK-003 deferred to Milestone 3** rather than dropped — it moves to
  where auth work already touches credentials, and lands with ADR #12's
  procedure replacing its original destructive AC 3.
- **Milestone 1 closed at 10/11** with the full discovered-work log
  triaged: every open DW item now carries a target milestone and a
  severity.
- **`releasable: false`.** This is a single-user internal tool; no
  CHANGELOG, no version tags, no GitHub Releases.
- **`testing-paradigm: adaptive`** stamped in [[CLAUDE]] — formalizes
  what ADR #2 already decided.
- **Repo hardening adopted.** `protect-main` (deletion +
  non_fast_forward blocked) and pinned squash settings, so main's history
  follows PR titles by construction rather than by discipline.

## Files Changed

Diff of `01b1c1b..HEAD`. No product code changed this session apart from
the one-line compose port.

- `docker-compose.yml` — dev DB published port `127.0.0.1:5434` → `:5435`
  (TASK-018, PR #25). The only source change of the session.
- `Handoffs/* → workflow/handoffs/*`, `tasks/* → workflow/tasks/*`,
  `memory/MEMORY.md → workflow/memory/MEMORY.md` — the v10 relocation, one
  logical move (`deferred.md`, `discovered.md` and `MEMORY.md` show as
  delete+add rather than renames only because they were edited past the
  similarity threshold in the same commit).
- `CLAUDE.md` — `workflow-version: 15`, `releasable: false`,
  `testing-paradigm: adaptive`; port gotcha updated to 5435; Project Map
  and structure tree re-pointed at `workflow/`; latest-handoff pointer
  → 006.
- `PROJECT.md` — session-006 and Milestone 1 close-out narrative in
  § Status; ADR #11 and #12 added; Consequences column added to the ADR
  table; `## Runtime Data Flow` stub added (still a TODO); Provisioned
  Infrastructure updated with the 5435 allocation.
- `TASKS.md` — Milestone 1 moved to Completed Milestones with its tag;
  Milestone 2 promoted to `active`; log links re-pointed at `workflow/`.
- `README.md` — doc-sync at milestone close: loopback-only note added to
  the access section, hardcoded `postgres`/`tax_billing` replaced with
  `.env` placeholders in the manual backup/restore commands.
- `.gitignore` — workflow-managed Claude Code block (v14); clears the
  sandbox path-mask phantoms from `git status`.
- `.claude/commands/.gitkeep`, `.claude/hooks/.gitkeep`,
  `.claude/skills/.gitkeep` — new tracked placeholders (conformance #1).
- `docs/reports/gate-audit-2026-09-01.md` — new; the gate-auditor's
  report, with a point-in-time genre header. This is the shopping list
  Milestone 2 works from.
- `workflow/handoffs/INDEX.md` — new; append-only handoff index,
  backfilled 001–005 and now carrying 006.
- `workflow/tasks/discovered.md` — DW-010…DW-025 logged; Severity column
  added; every open row triaged with a disposition.
- `workflow/tasks/deferred.md` — DEF-001 (TASK-003 → Milestone 3).
- `workflow/tasks/milestone-01-stop-the-bleeding.md` — frozen as the
  milestone's permanent archive; TASK-006/007/018 notes.
- `workflow/memory/MEMORY.md` — bookkeeping-gate supersession, canonical
  Docker daemon, dev DB port, the `mise run up` sandbox fact, and the
  repo merge settings.
- `workflow/handoffs/handoff-006.md` — this file.

## Discovered Work

Sixteen new items (DW-010…DW-025) were logged this session and the
**whole log was triaged with the user** — every open row carries a
severity and a target milestone, so none of it is awaiting first-pass
triage. Read [[workflow/tasks/discovered]] for the dispositions rather
than re-deriving them. Shape of the batch:

- **DW-010 / DW-011** — dashboard rendering gaps and tax-math gaps
  (found reading the live dashboard). DW-011 folds into TASK-011's
  acceptance criteria; DW-010 becomes a feature task after it.
- **DW-012 / DW-013** — pre-existing wiring findings from TASK-007's
  audit: unreferenced pydantic schemas; `backup_logs` rows outnumber
  files because `backup_retention_count` is never applied.
- **DW-014…DW-025** — the gate-auditor's findings, cross-referenced to
  TASK-008–012. DW-019 (no CI at all) is the big one. **DW-022** records
  two amendments TASK-008 must absorb: adopt the policy tier block, and
  pick a linter home for the Python *frontend*, which carries 17 blind
  `except Exception` handlers.
- Seven older items (DW-001…DW-008) received **defaulted** severities
  this session — 001 `next`, 002 `someday`, 003 `next`, 004 `next`,
  005 `next`, 007 `someday`, 008 `next`. The user may correct any of
  them cheaply. The auditor's own LOW items DW-024/DW-025 were recorded
  as `next` and are arguably `someday`.

## Blockers & Open Questions

- **Two user questions gate the DW-010 dashboard task and part of
  TASK-011's acceptance criteria.** Neither is answerable from the code:
  1. Does **"current tax"** mean bracket tax computed on YTD *paid*
     income as if the year ended today — a floor figure, displayed
     alongside the prorated holdback rather than replacing it?
  2. Should the **holdback include self-employed CPP** (both employee
     and employer halves)? This is the largest single number missing
     from the current math.
- **`## Runtime Data Flow` in [[PROJECT]] is a TODO stub.** v01 of the
  migration created it; nobody has drawn it. Draw it at the Milestone 3
  plenary, or via a one-off architect dispatch before then.
- **All 12 ADR Consequences cells are `—`.** v15 added the column but
  backfilling is a judgment call, not a mechanical one. Four rows are
  worth enriching from live knowledge: **#6** (JWT), **#8** (Alembic),
  **#9** (Decimal end-to-end), **#12** (non-destructive rotation).
- **The `~/.claude` config repo has an uncommitted change** — the
  tax-billing entry added to `references/port-registry.yaml` during
  TASK-018. That is the user's repo, not this one; it needs a commit
  there or the registration is local-only.
- **[[CLAUDE]] § Commands still lists `mise run desktop` and
  `mise run up-all` before they exist.** Both carry honest inline
  "NOT YET CONFIGURED / renames in Milestone 5" comments, so this is a
  known forward reference rather than stale documentation — it resolves
  in Milestone 5.
- **TASK-008 will need a dev-dependency proposal for `ruff`** before any
  install command runs. Present the lighter dev-dep template and get
  approval first; the hook prompts regardless.

## Next Steps

1. **Answer the two dashboard questions** (§ Blockers). Once answered,
   the director folds DW-008 and DW-011 into **TASK-011**'s acceptance
   criteria and queues the DW-010 dashboard feature task immediately
   after it. Cheap to answer, and it unblocks the shape of the milestone's
   biggest task.
2. **Milestone 2 — Quality Gates**, in order:
   **TASK-008** (pyproject + ruff — dev-dep proposal first; fold in DW-003
   `.gitattributes`, whose live symptom was this session's README CRLF→LF
   flip, plus DW-004 and DW-022's tier-block and frontend-linter-home
   amendments) → **TASK-009 / TASK-010** → **TASK-011** (TDD on
   `tax_calculator.py`, carrying the DW-011 math criteria) →
   **TASK-012**. Separately: **add a CI task to Milestone 2** covering the
   DW-019 / DW-014 / DW-015 / DW-018 cluster — the milestone was
   decomposed before the gate audit ran, so CI has no task today. User
   decides whether it goes in M2 or later.
3. **Optional cheap corrections, any time:** revise the seven defaulted
   DW severities; enrich the four ADR Consequences cells (#6, #8, #9,
   #12).
4. **Milestone 3 plenary, later:** draw § Runtime Data Flow; pick up
   TASK-003 with ADR #12's non-destructive procedure; DW-001.

Reference [[TASKS]] for the full queue context.

## Files to Read on Resume

- [[PROJECT]] — § Status carries the session-006 and Milestone 1
  close-out narrative; ADR #11/#12 are new; § Runtime Data Flow is the
  open stub
- [[TASKS]] — Milestone 1 is in Completed Milestones with its tag;
  Milestone 2 is `active`
- [[workflow/tasks/milestone-02-quality-gates]] — the next queue,
  TASK-008 first
- [[workflow/tasks/discovered]] — 25 rows, fully triaged; read the
  **Severity** and **Disposition** columns, don't re-triage
- `docs/reports/gate-audit-2026-09-01.md` — what Milestone 2 has to
  cover; 11 gates expected, 0 present
- [[workflow/memory/MEMORY]] — Docker daemon, dev DB port 5435, and the
  `mise run up` sandbox fact; relevant before touching containers
- `backend/app/services/tax_calculator.py` — the DW-011 math gaps live
  here; required reading before TASK-011

## Library Candidates

_None._ One line of YAML and a documentation cycle.
