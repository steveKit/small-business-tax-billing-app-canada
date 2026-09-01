# Gate Audit Report

**Project**: tax-billing (`steveKit/small-business-tax-billing-app-canada`, public)
**Surfaces**: Python (`backend/` — FastAPI), Python (`frontend/` — Flet; "frontend" is Python, not JS)
**Shape**: code repo w/ PR flow (PRs #4–#25 on main; squash-merged)
**Security level**: L3 (`security-profile.yaml`)
**Date**: 2026-09-01 (invoked by `/migrate-workflow` v12; `workflow-version: 10`, `releasable: false`)

## Summary
- Gates expected: 11 | present: 0 | partial: 2 (`gate:linter-tier` settings-allow surface only; `gate:vulns` async layer only) | missing: 11 | n/a (recorded here): 6 | deviating: 0 (documented: 0, undocumented: 0)
- Repo settings: squash pins **drift** (`squash_merge_commit_title=COMMIT_OR_PR_TITLE`, `squash_merge_commit_message=COMMIT_MESSAGES`, `allow_merge_commit=true`, `allow_rebase_merge=true`) · `protect-main` ruleset **absent** (`rulesets` → `[]`; classic branch protection → 404)
- Proving status: proofs **absent** (no gate exists to prove) · job-set check: **n/a** — zero workflow runs; the only remote workflow is GitHub's `dynamic/dependabot/update-graph` (run 31711852670, 2026-08-13)
- Dependabot: alerts **enabled** (`GET /vulnerability-alerts` → 204); dependency graph active for `pip` in `/backend` and `/frontend`; automated security fixes disabled (not required)
- Tree state: clean (`main` == `origin/main` at `21c0ba7`); the `??` entries in `git status` are sandbox path-mask phantoms, not real files

The absence is **by design, not drift** — Milestone 02 "Quality Gates" is the planned home for ruff/mypy/pytest, and the plenary pre-seeded `.claude/settings.json` for them. This audit's value is the delta M2 does **not** cover: every CI workflow, repo merge settings, the branch ruleset, secrets/CVE scanning, commit-msg/pr-title/slop, dead-code (deptry), layering (import-linter), the frontend surface's tier, and the shape gates.

## Expected Set (derived from policy + docs before reading any config)

Inputs: `deterministic-gates.md` § Selecting, `gates/python.md`, CLAUDE.md, PROJECT.md (ADR #1 layered `routers → services → models`), `security-profile.yaml` (L3), `releasable: false`.

1. **Shape**: code repo with PR flow → gate tier applies.
2. **Agnostic core**: `hygiene.yml` (secrets, commit-msg, pr-title, slop), `ci.yml` heavy (per-surface lint/typecheck/test + duplication, `paths-ignore` docs/workflow), `vulns.yml`; squash settings pinned; `protect-main` ruleset; `gate:deps-currency` n/a (pending CI).
3. **Per-stack tier × 2 surfaces**: `backend/` and `frontend/` are both Python → `gates/python.md` applies to each (module exists — no authoring finding). Per-surface `paths:` filters on heavy jobs (polyglot-scoping obligation applies to two same-language surfaces too).
4. **Layering contracts, transcribed**: backend is layered (ADR #1; CLAUDE.md "a router imports services and schemas; services import models; models import nothing from routers"). Frontend: "one view per destination; `api_client` is the only thing that talks HTTP; no cross-view imports." Expected outcome is **contracts**, not `no contracts (flat)`.
5. **Shape gates**: `gate:containers` (two Dockerfiles), `gate:actions` (once workflows exist). `gate:shell`, `gate:iac`, `gate:docs` n/a. `gate:db-migrations` n/a until Alembic (M4).
6. **L3 depth**: `gate:vulns` blocking on `requirements*.txt` PRs **and** an async layer.
7. `releasable: false` → no version/changelog conformance checks.

Code cross-check of step 4 (import edges, `grep '^from app\.'`): the backend is consistently layered with **no upward imports** — `main → routers → services → schemas → models`, with `database` and `config` as the floor (`routers → database`; `services → config`; `database → config`; `models` import only `models`). One edge the docs don't state: `services/tax_calculator.py:12` imports `app.schemas.tax`, which places `schemas` **below** `services` in the transcription. Frontend: every view imports only `services.api_client`; `httpx` appears only in `frontend/services/api_client.py:3`; no cross-view imports. **Docs and code agree — no architecture escalation.**

## Per-Gate Verdicts
| Gate | Verdict | Detail |
|---|---|---|
| `gate:linter-tier` (backend) | **missing** (partial: surface 3 present) | No `pyproject.toml`/`ruff.toml` anywhere. `.claude/settings.json` already allows `ruff check *`, `ruff format *`, `mypy *`, `pytest*`, `mise run lint/typecheck/test/smoke` (pre-seeded). CLAUDE.md Commands lists `ruff check .` as NOT YET CONFIGURED. **Covered by TASK-008** — but its AC says only "`ruff` config under `[tool.ruff]`"; it must adopt the module's tier block (`C901`, `PLR0912/0913/0915`, `T20`, `BLE`, `RUF100`; complexity 10 / statements 50 / branches 12 / args 5; tests exempt from size caps). Adoption impact: 2 `print()` in backend, 3 blind `except Exception` in backend, 17 in frontend, 0 existing `# noqa`. |
| `gate:linter-tier` (frontend) | **missing** | TASK-008 scopes config to `backend/pyproject.toml` and leaves `frontend/` on `requirements.txt` until M6 — the frontend surface has **no config home** and no task. The 17 blind excepts live here. |
| `gate:dead-code` | **missing** | `F401` arrives with ruff defaults (TASK-008; DW-004 is one instance). **deptry** is in no task: `backend/requirements.txt` declares `alembic`, `psycopg2-binary`, `python-jose`, `passlib`, `httpx` unused (CLAUDE.md § Gotchas) plus `pytest`/`pytest-asyncio` in the runtime manifest — DEP002/DEP004 go red by construction; the sanctioned pattern is a `per_rule_ignores` ledger with WHY + expiry (M3 consumes `passlib`/`python-jose`; M6 trims the rest), never a wholesale disable. Note: neither F401 nor deptry catches unreferenced *classes* — DW-012's dead schemas stay a manual M6 sweep. |
| `gate:layering` | **missing** | No import-linter. Contracts to transcribe (from § Expected Set): backend `layers` contract, `root_packages=["app"]`, `exhaustive=true`, `layers = ["main", "routers", "services", "schemas", "models", "database", "config"]` + a `forbidden` contract pinning `app.models` ↛ `app.routers | app.services`; frontend `independence` contract over `views.*` submodules + `forbidden` `views.*` ↛ `httpx`. The code already satisfies all of them. |
| `gate:secrets` | **missing** | No workflow, no `.gitleaks.toml`. History contains the pre-TASK-002 hardcoded credentials (`0871743` Initial commit … removed in `d30b558`, PR #5) — a full-history scan **will** flag them on first run. Remedy is path/rule-scoped allowlist **plus rotation**; rotation is already TASK-003 (deferred → M3, ADR #12). On an L3 project this is the highest-value absent gate. |
| `gate:vulns` | **missing** (partial: async layer present) | Dependabot alerts enabled (204) and dependency graph active for both `pip` directories — the async layer L3 requires exists. The **blocking** layer (`vulns.yml`, osv-scanner or `pip-audit`, on `**/requirements*.txt` PRs) is absent; L3 requires both (§ Selecting step 6). |
| `gate:deps-currency` | **n/a (pending CI)** | Correctly not adopted — no heavy tier exists. Once `ci.yml` lands: `.github/dependabot.yml`, `pip` × `/backend` and `/frontend`, monthly, grouped (FastAPI/pydantic/SQLAlchemy families). |
| `gate:commit-msg` | **missing** | No check. Last 40 subjects on main: 3 non-conforming — `hotfix(frontend): …` (#18, post-plenary), `Add MIT License`, `Initial commit`. |
| `gate:pr-title` | **missing** + repo settings drift | No title check. `squash_merge_commit_title=COMMIT_OR_PR_TITLE`, `squash_merge_commit_message=COMMIT_MESSAGES`, merge and rebase merges enabled. The `hotfix(frontend)` subject on main (#18) is exactly the nondeterminism the pin prevents; `/billing-summary` reads these subjects. Public repo → `PR_TITLE` must cross via `env:`, never interpolated. |
| `gate:slop` | **missing** | No `.ci/slop-patterns.txt`. Dry run of the canonical pattern set over `backend/ frontend/ database/ *.md` with `/usr/bin/grep`: exit 1 (clean). Sunset tripwire 2027-02-01 applies. |
| `gate:duplication` | **missing** | No jscpd. Belongs in `ci.yml`, `continue-on-error: true`, scope `backend/ frontend/` (policy example uses `src/`). |
| `gate:actions` | **missing** | Expected as soon as hand-written workflows exist. actionlint, provenance-verified at adoption. |
| `gate:containers` | **missing** | `backend/Dockerfile` (38 lines), `frontend/Dockerfile` (25 lines); no hadolint. |
| `gate:shell` | n/a | No `*.sh` in tree; `.mise.toml` tasks are one-line compose/pip invocations. |
| `gate:iac` | n/a | No Terraform/IaC. |
| `gate:docs` | n/a | No docs site. |
| `gate:db-migrations` | n/a (revisit M4) | `database/schema.sql`/`seed_data.sql` are init-volume DDL, not a migration set. Alembic (ADR #8, M4) emits Python; record a squawk decision then. |
| releasable checks | n/a | `releasable: false`. |

Repo settings / branch ruleset: see `gate:pr-title` row and Findings.

## Findings
- [ ] [HIGH] `gate:secrets` absent → `.github/workflows/hygiene.yml` + `.gitleaks.toml` → expected: gitleaks CLI v8.30.1 checksum-pinned, `fetch-depth: 0`, HEAD + shallow guards, full-history scan; actual: nothing. Fix: adopt the policy's canonical block verbatim; on first run, allowlist the `0871743..d30b558` credential sites path/rule-scoped and confirm TASK-003 (rotation) stays queued — allowlisting is not the remedy. Prove: fake-AWS-key canary + drop `fetch-depth: 0` → red.
- [ ] [HIGH] `gate:vulns` blocking layer absent (L3) → `.github/workflows/vulns.yml` → expected: PR-blocking scan on `**/requirements*.txt` changes; actual: only the Dependabot-alerts async layer. Fix: `vulns.yml` per policy (osv-scanner pinned + sha256, or `pip-audit -r` as the stack-native substitute), `permissions: contents: read`, `timeout-minutes: 5`; the weekly `schedule:` can be omitted since alerts cover the async layer — record that choice in the workflow comment.
- [ ] [MEDIUM] `gate:pr-title` absent and squash-title source unpinned → repo settings + `hygiene.yml` → expected `PR_TITLE`/`PR_BODY`, merge+rebase disabled; actual GitHub defaults (`COMMIT_OR_PR_TITLE`/`COMMIT_MESSAGES`, both enabled). Fix (user/director runs — never the auditor): `gh api repos/steveKit/small-business-tax-billing-app-canada -X PATCH -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY -F allow_merge_commit=false -F allow_rebase_merge=false`; add the pr-title step with `types: [opened, edited, synchronize, reopened]`.
- [ ] [MEDIUM] `protect-main` ruleset absent → repo rulesets → expected `deletion` + `non_fast_forward` on `refs/heads/main`; actual `[]`. Fix: the `gh api …/rulesets -X POST` block from [[git]] § Remote Branch Protection.
- [ ] [MEDIUM] `gate:commit-msg` and `gate:slop` absent → `hygiene.yml` + `.ci/slop-patterns.txt` → expected: PR-only commit-msg walk with base-ref guard and three-state `case`; slop scan with `[ -s ]` guard, `--include='*.md' --include='*.py'`, plus `--exclude-dir=backups --exclude-dir=.flet --exclude-dir=build`; actual: nothing. Public repo: the single-consolidated-job rule is a private-repo cost rule — split or consolidate is a free choice here; `timeout-minutes` + `concurrency: cancel-in-progress` remain mandatory. Prove: `wip stuff` subject canary; rename and separately zero-byte the pattern file → red.
- [ ] [MEDIUM] Heavy tier (`ci.yml`) absent → `.github/workflows/ci.yml` → expected: per-surface `ruff check` / `mypy` / `pytest` jobs with `paths:` scoped to `backend/**` and `frontend/**`, `paths-ignore: ['**/*.md', 'docs/**', 'workflow/**']` under each event, `gate:duplication` (`npx jscpd@5.0.12 --min-tokens 70 --reporters consoleFull backend/ frontend/`, `continue-on-error: true`), `timeout-minutes`, `concurrency`; actual: nothing. **Depends on TASK-008/009/010** (the tools must exist before CI runs them) — sequence after them, not in parallel. Note `pytest` DB-dependent tests (TASK-012) need a service container or a SQLite decision in the job.
- [ ] [MEDIUM] `gate:dead-code` (deptry) absent → `backend/pyproject.toml` `[tool.deptry]` + `frontend/` scan + CI step + `Bash(deptry *)` allow + Commands entry → expected per module; actual: not in TASK-008 or any task. Dev-dep proposal required (deptry, MIT). Ledger the known cargo-culted deps with WHY + expiry rather than disabling DEP002.
- [ ] [MEDIUM] `gate:layering` (import-linter) absent → `backend/pyproject.toml` `[tool.importlinter]` + a frontend config + CI `lint-imports` + `Bash(lint-imports*)` allow + Commands → contracts as transcribed in § Expected Set (code already conforms — adoption should be green on day one, then prove with a canary import). Dev-dep proposal required (import-linter, BSD-2). Also sync CLAUDE.md § File Organization to state `services → schemas` is permitted (it is, in `tax_calculator.py`).
- [ ] [MEDIUM] Frontend surface has no linter-tier home → TASK-008 scopes ruff to `backend/pyproject.toml`; `frontend/` stays on `requirements.txt` until M6 → expected: both surfaces carry the tier now. Fix options: a root-level `ruff.toml` covering both (simplest; `extend` from backend), or `frontend/ruff.toml`; either way `ruff check frontend` in CI/Commands/settings. Decision for the director at TASK-008 pickup.
- [ ] [MEDIUM] Shape gates `gate:actions` (actionlint) and `gate:containers` (hadolint) absent → `hygiene.yml` or `ci.yml` steps → expected once workflows and the two Dockerfiles are gated; actual: none. Both tools pass § Tool Provenance at adoption (pin version + sha256).
- [ ] [LOW] `gate:deps-currency` — record `n/a (pending CI)` in PROJECT.md now; queue `.github/dependabot.yml` (`pip` × `/backend`, `/frontend`, monthly, grouped) to land immediately after `ci.yml`.
- [ ] [LOW] `.claude/settings.json` allows `Bash(docker compose config)` — a full-config renderer that prints every `env_file` value ([[security]] § Secrets: "content renderers leak like dumpers"; the hook prompts on it). Not a gate, but it sits on the agent self-validation surface this audit inventories. Replace with `docker compose config --services` / `--volumes`.
- [ ] [LOW] CLAUDE.md Commands drift at TASK-008: the entry says `ruff check .` — `gates/python.md` § Delivery quad requires source-root-scoped local forms (`ruff check backend frontend`), never `.`, because the sandbox's phantom path-masks abort a root walk. TASK-008's AC already uses `ruff check backend/`; align the Commands entry when it lands. Also add `Bash(ruff check *)`-style rules for deptry/lint-imports as those gates land, and update `security-profile.yaml` `existing_security_tooling` once ruff/gitleaks/osv are live.
- [ ] [LOW] `gates/python.md` states its quad in `uv run …` forms; this project is pip/`requirements.txt` (TASK-008 introduces `pyproject.toml` but not uv). Adapt forms to bare `ruff`/`deptry`/`lint-imports` — the pre-seeded settings rules already take this shape. Upstream note for the core-architect: the module could state the pip-native forms as an alternative.

## Covered by Milestone 02 (no duplicate queued)
- `gate:linter-tier` backend config, `mise run lint`, settings allow rule → **TASK-008** (settings rules are already present — that AC is pre-satisfied). Amend TASK-008's AC to adopt the module's tier block, not a bare `[tool.ruff]`.
- `F401` (part of `gate:dead-code`) → **TASK-008** (DW-004).
- `.gitattributes` line-ending normalization → **TASK-008** (DW-003).
- mypy strict-on-services → **TASK-009**; pytest/pytest-asyncio + `mise run test` → **TASK-010**; TDD tax_calculator → **TASK-011**; smoke → **TASK-012**. These are the heavy tier's *contents*; the `ci.yml` that runs them is not in M2 (finding above).

## Documented Deviations (preserved)
- None. CLAUDE.md § Convention Overrides is empty; no gate config exists to carry inline justifications.

## Recorded n/a
- `gate:deps-currency` — n/a (pending CI); adopt after `ci.yml`.
- `gate:shell` — no shell scripts in tree.
- `gate:iac` — no IaC.
- `gate:docs` — no docs site.
- `gate:db-migrations` — no migration set until Alembic (M4, ADR #8); revisit then.
- Releasable conformance checks — `releasable: false`.
- `gate:layering` is **not** n/a: the architecture is layered (ADR #1) and the code conforms — contracts are expected.

## Method Notes
- Expected set was written to scratch before any config was opened (`expected-set.md`); the inventory then found no gate config, no `.github/`, no `.ci/`, no `pyproject.toml`.
- Repo facts from `gh api repos/{owner}/{repo}`, `/rulesets`, `/branches/main/protection`, `/vulnerability-alerts`, `/actions/workflows`, `gh run list`, `gh pr list --state merged`.
- No tools were installed or run against the repo beyond `git` and GNU `grep` (`/usr/bin/grep`, per policy § Proving's local-reproduction rule). Historical credential values were located by commit (`git log -S`) without printing content.
