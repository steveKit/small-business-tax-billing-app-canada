# Milestone 02: Quality Gates

> **Status:** active
> Index: [[TASKS]] · Architecture: [[PROJECT]] · Conventions: [[CLAUDE]]
> **Goal:** Introduces the tools that make every subsequent milestone safer: `pyproject.toml`, ruff, mypy, pytest. First real tests land here, starting TDD on `tax_calculator.py`. Vertical-slice smoke test lands here — it is the tool's first "boots and runs" check.
> **Priority:** `P0` (critical) | `P1` (high) | `P2` (medium) | `P3` (low) · **Size:** `S` (< 1 hr) | `M` (1–4 hrs) | `L` (4+ hrs)

## Active Tasks

### TASK-008: Introduce pyproject.toml and ruff [`pending`] [`P1`] [`M`]
**Description:** Migrate `backend/requirements.txt` to `pyproject.toml`. Configure ruff (lint + format). Frontend stays on `requirements.txt` until Milestone 6.
**Acceptance Criteria:**
- [ ] `backend/pyproject.toml` exists with dependencies matching current `requirements.txt` (pinned versions)
- [ ] `ruff` config in `pyproject.toml` under `[tool.ruff]`
- [ ] `ruff check backend/` passes (fix or ignore as needed, documenting ignores)
- [ ] `ruff format backend/` applied in a separate commit from the config commit
- [ ] `mise run lint` task added
- [ ] `.claude/settings.json` allow-list updated for `ruff` commands

### TASK-009: Introduce mypy (strict on services/) [`pending`] [`P1`] [`M`]
**Description:** Configure mypy with strict mode on `backend/app/services/` and lenient elsewhere. Fix any type errors that surface in the strict section.
**Acceptance Criteria:**
- [ ] `[tool.mypy]` config in `backend/pyproject.toml`
- [ ] `mypy backend/app/services/` passes clean
- [ ] `mypy backend/app/` (non-services) passes with documented ignore patterns
- [ ] `mise run typecheck` task added

### TASK-010: Introduce pytest + pytest-asyncio [`pending`] [`P1`] [`M`]
**Description:** Configure pytest + pytest-asyncio. Create `backend/tests/` directory with conftest.py. Do not write `tax_calculator` tests here — that is TDD work in TASK-011.
**Acceptance Criteria:**
- [ ] `[tool.pytest.ini_options]` in `backend/pyproject.toml`
- [ ] `backend/tests/` directory with `conftest.py` (async event loop fixture)
- [ ] `mise run test` task added
- [ ] `pytest` runs green on an empty test suite (placeholder test passes)

### TASK-011: TDD tax_calculator.py [`pending`] [`P0`] [`L`]
**Dependencies:** TASK-010
**Description:** Write comprehensive failing tests for `backend/app/services/tax_calculator.py` covering progressive bracket math, HST holdback, income tax holdback, YTD annualization, and edge cases (zero income, single-bracket income, income spanning all brackets, unknown province → ValueError). Then dispatch implementer in TDD mode to make tests pass with minimal changes. Purpose: lock in correct behavior before any subsequent refactor.
**Acceptance Criteria:**
- [ ] `backend/tests/services/test_tax_calculator.py` exists with ≥ 20 tests covering the above
- [ ] All tests pass against the current `tax_calculator.py` (or surface real bugs that become fix tasks)
- [ ] `tax_calculator.py` has no behavior change unless a test revealed a bug
- [ ] `pytest-cov` coverage of `tax_calculator.py` ≥ 90%
**Notes:**
- `pytest-cov` is a new dev dep; requires the standard dep proposal.
- Dispatch mode: TDD (tester-first). Interface spec = existing public methods on `TaxCalculatorService`.

### TASK-012: Vertical-slice smoke test [`pending`] [`P0`] [`M`]
**Dependencies:** TASK-010, TASK-001
**Description:** Implement the smoke test referenced in the plenary checklist. One input → one output, end-to-end, hitting every layer: `POST /v1/clients` → `POST /v1/invoices` → `POST /v1/payments` → `GET /v1/tax/summary`. Verify each step and that the tax summary reflects the payment.
**Acceptance Criteria:**
- [ ] `backend/tests/test_vertical_slice.py` runs the full flow against a live test DB (pytest-asyncio + httpx test client)
- [ ] Test uses a disposable SQLite-in-memory DB OR a dedicated test Postgres schema (decide during task)
- [ ] Smoke test command documented in `CLAUDE.md` Commands section
- [ ] `mise run smoke` task added
- [ ] Test passes from a freshly-seeded DB

### TASK-019: Bump vulnerable backend dependencies (Dependabot alerts) [`pending`] [`P2`] [`M`]
**Dependencies:** TASK-008
**Description:** GitHub reports 17 open Dependabot alerts on `main`, all in the backend dependency set (surfaced 2026-10-07 in the push response; verified at source via `gh api repos/{owner}/{repo}/dependabot/alerts?state=open`). Bump the pins in `backend/pyproject.toml` (post-TASK-008): `python-multipart` 0.0.9 → ≥ 0.0.31 (4 HIGH, 1 MED, 3 LOW); `python-jose` 3.3.0 → ≥ 3.4.0 (1 CRIT, 1 MED — declared but unused until M3); `weasyprint` 60.2 → ≥ 70.0 (1 HIGH, 2 MED; a major bump — `pydyf` 0.8.0 must move with it); `jinja2` 3.1.4 → ≥ 3.1.6 (3 MED); `pytest` 8.3.3 → ≥ 9.0.3 (1 MED; coordinate with TASK-010's `pytest-asyncio` pin). Blast radius is limited today — loopback-only, single user (user decision 2026-10-07) — hence P2; the L3 profile and TASK-008's re-pin make M2 the natural home. Version bumps of existing deps need no new-dep proposal, but the PR takes full review: the weasyprint major bump touches invoice PDF output.
**Acceptance Criteria:**
- [ ] `python-multipart` ≥ 0.0.31, `python-jose` ≥ 3.4.0, `jinja2` ≥ 3.1.6, `pytest` ≥ 9.0.3 pinned exactly in `backend/pyproject.toml`
- [ ] `weasyprint` ≥ 70.0 with a compatible `pydyf` pin; an existing invoice PDF renders without error and the TASK-017 `white-space: pre-wrap` behavior is preserved (visual check against a pre-bump render)
- [ ] Backend image rebuilds; `/health` returns 200; existing tests green
- [ ] `gh api …/dependabot/alerts?state=open` shows no alerts other than advisories with no patched version (GHSA-jhhc-3hcp-qhm5 at filing time)
- [ ] The pre/post-bump render check uses live data read-only — no synthetic invoices created in the real books
**Notes:**
- Origin: [[workflow/tasks/discovered]] DW-026, filed from session 007 ([[workflow/handoffs/handoff-007]]).

---

## Completed Tasks (this milestone)

_None yet._
