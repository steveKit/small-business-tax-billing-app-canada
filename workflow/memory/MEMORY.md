# Project Memory — tax-billing

Stable operational patterns specific to this machine/project. Conventions,
stack, and gotchas about the *code* live in [[CLAUDE]]; this file is for
recurring *workflow* friction that isn't covered by the rules.

## Bookkeeping commits — direct-to-main is fine for workflow-state-only changes

valid_from: 2026-09-01
(supersedes the earlier blanket rule "bookkeeping commits must route
through a short-lived branch, never direct-to-main" — ended: 2026-09-01;
that rule survives only as the fallback below)

The global pre-tool-safety hook gained a **bookkeeping gate** (user decision
2026-07-29): a `git commit` + `git push origin main` from a session already on
`main` passes **prompt-free** when the real staged set — and the outgoing
commits — touch nothing but `TASKS.md`, `PROJECT.md`, `CLAUDE.md`, and the
workflow state directories. Verified on this project 2026-09-01: a
`tasks/`-only bookkeeping commit landed as `aa10605` with no prompt and no
branch.

**Fallback — still needed for anything the gate prompts on** (a product file
in the staged set, an `-a`-form commit, a refspec push from another branch):
1. Create a short-lived branch as its **own** Bash call:
   `git checkout -b chore/handoff-NNN` (or `docs/...`).
2. Commit and push on that branch.
3. Merge with `gh pr merge --squash --delete-branch`.

**Why step 1 must be separate:** the hook evaluates statically, so a combined
`git checkout -b foo && git commit ...` in a single command still trips the
main-branch check — the branch switch has not "happened" from the hook's point
of view when it inspects the compound command. Always make the branch switch a
prior, standalone call.

**Layout note:** until 2026-09-01 this project sat on the pre-v10 root-level
layout (`tasks`, `Handoffs`, `memory` folders at the repo root), which the
gate's `workflow/**` allowlist did not cover — a handoffs-only commit could
prompt where a tasks-only one did not. `/migrate-workflow` v10 relocated all
three under `workflow/` that day, so every workflow-state commit now matches
the allowlist; the branch fallback is only for sets that include product files.

## Local environment facts

valid_from: 2026-09-01

- **Canonical Docker daemon:** Docker Desktop via WSL integration (`docker
  context ls` → `default`, server 29.7.2). The native systemd daemon must stay
  inactive (`systemctl is-active docker` → `inactive`); two live daemons can
  each hold an identically-named container on the same published port while
  backing divergent data.
- **Dev DB host port:** `127.0.0.1:5435` → container 5432 (reallocated from
  5434 on 2026-09-01, TASK-018; registered in
  `~/.claude/references/port-registry.yaml`). In-network the backend still uses
  `db:5432`.
- **`mise run up` is NOT covered by the sandbox's docker exclusion.** The
  exclusion applies to the `docker` command itself; wrapped through `mise run`,
  the compose call runs sandboxed and fails with a docker-socket permission
  error. It must be run **unsandboxed** — which the director can do in an
  attended session, but a dispatched agent cannot (it cannot self-approve the
  escape-hatch prompt). Agents needing containers up should report the
  limitation rather than retrying; or invoke `docker compose ...` directly.

## GitHub repo settings — protected `main`, squash-only, PR-title subjects

valid_from: 2026-09-01

Applied on user confirmation during the `/migrate-workflow` sync; these are
server-side facts, so they hold for terminals outside Claude Code too.

- **`protect-main` ruleset is active** on `refs/heads/main`: branch deletion
  and non-fast-forward (force) pushes are blocked. Require-PR is deliberately
  NOT enabled — it would break the direct-to-main bookkeeping flow this
  project relies on. Require-status-checks is likewise off; there is no CI yet
  (DW-019).
- **Squash is the only merge method.** Merge commits and rebase merges are
  disabled, and squash subjects are pinned to `PR_TITLE` with `PR_BODY` as the
  body. Consequence: a PR title is literally the commit subject that lands on
  `main`, so it must carry the conventional-commit format and the TASK ID —
  the branch's own commit subject is no longer used, not even for
  single-commit PRs.
