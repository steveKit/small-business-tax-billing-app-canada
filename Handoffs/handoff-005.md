# Handoff 005 — 2026-06-10

## Session Summary

A short, focused session roughly two months after handoff-004 (sessions
are spaced). One ad-hoc user-requested fix shipped plus its bookkeeping.
No Milestone 1 progress — the three remaining M1 tasks (TASK-003/006/007)
are all user-gated and unchanged from handoff-004.

**TASK-017 (ad-hoc) — invoice PDF "Description of Work" collapsed
user-entered newlines.** Root cause was render-only: the Flet field is
`multiline=True` and the DB column is `Text`, so newlines were always
stored correctly; the `.description-text` div in
`backend/app/templates/invoice.html` had no `white-space` rule, so HTML
collapsed runs of whitespace including line breaks. Fix is a one-line
CSS rule `white-space: pre-wrap;` on `.description-text`. Injection-safe
— the template keeps Jinja2 `autoescape=True`, so the fix relies on CSS
rather than emitting raw `<br>` tags. `pre-wrap` was chosen over
`pre-line` to preserve pasted indentation/formatting, not just newlines.
No invoice recreation needed: re-rendering the PDF reflects the fix
because the backend bind-mounts the template and Jinja2 auto-reloads
(fallback: `docker restart tax-billing-backend`).

Fast-tracked: director self-review, no independent reviewer, 0 fix
cycles.

**Branch / PR status:** All work merged to `main`. Working tree clean at
`c7da78a`. Both session branches deleted. No open PRs.

| PR | Commit | Title |
|---|---|---|
| #21 | `b5a211a` | `fix(invoice-pdf): preserve line breaks in Description of Work` |
| #22 | `c7da78a` | `docs(bookkeeping): TASK-017 notes + invoice newline gotcha` |

## Key Decisions

- **Architect pass declined for now.** At session start the user asked
  whether an architect pass was warranted before continuing. Decision:
  **no.** The architect's case-(b) trigger (structural problems that code
  changes alone can't fix) had not fired; the foundation audit from the
  2026-04-10 plenary is still valid; remaining M1 work is mechanical and
  user-gated; M2 is pure tooling; and the architecturally-significant
  milestones (3 auth, 4 Alembic, 5 frontend container, 7 network) each
  already have a focused plenary scheduled at their start (planner work,
  not architect). **Revisit trigger:** reconsider an architect dispatch
  at the **Milestone 3 auth plenary boundary** if bolting JWT onto the
  current router structure proves awkward, or any time a fix cycle stalls
  past ~3 iterations.
- **`pre-wrap` over `pre-line` for invoice description rendering
  (TASK-017).** Preserves pasted indentation/formatting in addition to
  newlines. CSS-based fix keeps the template's `autoescape=True` intact
  rather than emitting raw `<br>` markup.

## Files Changed

- `backend/app/templates/invoice.html` — added `white-space: pre-wrap;`
  to the `.description-text` CSS rule (TASK-017 fix)
- `CLAUDE.md` — new § Gotcha on HTML/PDF newline collapse in the
  WeasyPrint/Jinja2 invoice template; latest-handoff pointer updated to
  005
- `TASKS.md` — TASK-017 recorded in Completed Tasks with Notes
- `PROJECT.md` — Last Updated → 2026-06-10; one-line session-005 note in
  Status
- `memory/MEMORY.md` — new file; records the bookkeeping-to-main hook
  workaround pattern
- `Handoffs/handoff-005.md` — this file

## Blockers & Open Questions

No new blockers introduced this session. The remaining Milestone 1 work
is unchanged from handoff-004 and carries forward:

- **Real Adamson payments still unrecorded.** Both Adamson invoices
  (`2026-Adamson-001` and `2026-Adamson-002`, $10,170 each) remain
  `pending` with 0 payment records. Recording them via the Flet UI
  auto-transitions them to `paid`. Take a fresh `pg_dump` first.
- **TASK-003 (strong secrets rotation) — user-gated.** Still has the
  pre-session-004 default credentials in `.env`; rotating them is a
  `docker compose down -v` data-loss event. Take a fresh `pg_dump`
  before starting; see handoff-004 for the exact command sequence.
- **TASK-006 (stale root-owned backup cleanup) — user-gated.** Requires
  `sudo`; agents cannot escalate privileges.
- **TASK-007 (integration verification + M1 tag).** Sequenced behind
  TASK-003 + TASK-006. First acceptance criterion is
  `docker compose down -v && docker compose up -d`, which needs TASK-003
  to have populated the new required vars.

The director-lesson items flagged in handoff-004 (acceptance criteria
that the inserted text violates; user-verify step for UI click-time
changes) remain uncodified in any agent config — still out of scope.

## Next Steps

Ordered, unchanged from handoff-004 plus this session's context. Session
005 made no M1 progress, so the M1 sequence stands as-is:

1. **P0 — Record real Adamson payments** via the Flet UI at
   `http://localhost:8080`. Take a fresh `pg_dump` first. Closes
   TASK-013's reconciliation loop. ~2 minutes of user work.
2. **P0 — TASK-003 (strong secrets; data-loss event; user-gated).**
   Fresh `pg_dump` → generate new secrets → `docker compose down -v` →
   bring up with new `.env` → restore from the fresh backup. See
   handoff-004 → handoff-003 for the canonical command sequence.
3. **P2 — TASK-006 (stale root-owned backup cleanup; user-gated sudo).**
   One cosmetic cleanup command.
4. **P0 — TASK-007 (integration verification + create
   `milestone-01-stop-the-bleeding` tag).** Includes TASK-013/015/016
   regression checks (see handoff-004 for the criteria list).
5. **Then Milestone 2 (Quality Gates):** TASK-008 → 009/010 → 011/012.

Reference [[TASKS]] for the full queue context.

## Files to Read on Resume

- [[PROJECT]] — status, milestones table (still 8/11 on Milestone 1 —
  TASK-017 is milestone-independent), Last Updated 2026-06-10
- [[TASKS]] — § Completed Tasks has the TASK-017 entry; § Milestone 1
  has the 3 remaining user-gated tasks
- [[Handoffs/handoff-004]] — still the canonical reference for the
  TASK-003 command sequence and the remaining-M1 detail
- `memory/MEMORY.md` — bookkeeping-to-main hook workaround (relevant on
  every handoff/bookkeeping cycle)
- The TASK-017 change in `backend/app/templates/invoice.html` is minor
  and self-contained; no deep read needed

## Library Candidates

_None._ The session touched one CSS line and two doc files.
