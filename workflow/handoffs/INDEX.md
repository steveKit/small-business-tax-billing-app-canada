# Handoff Index

status: append-only log — one row per handoff, appended at /handoff

| Handoff | Date | Summary |
|---|---|---|
| [[workflow/handoffs/handoff-001]] | 2026-04-10 | Existing-project plenary — scaffolded CLAUDE.md, PROJECT.md, TASKS.md, security-profile.yaml (L3) and 9 architecture decisions on branch `chore/workflow-scaffold`; read-only architect audit, no source code touched. |
| [[workflow/handoffs/handoff-002]] | 2026-04-10 | Plenary close-out superseding handoff-001 — PR #1 (scaffold) and PR #2 (close Milestone 0) merged, `milestone-00-workflow-scaffold` tagged, Milestone 1 queued and still unstarted. |
| [[workflow/handoffs/handoff-003]] | 2026-04-10 | Milestone 1 went 4-for-7 — PR #5 (TASK-002/004 credential extraction plus loopback binds) and PR #4 (TASK-001/005 BackupService reconciliation plus `datetime.utcnow()` sweep, one reviewer fix cycle) merged; TASK-003/006/007 remain user-gated. |
| [[workflow/handoffs/handoff-004]] | 2026-04-13 | 12 PRs merged and 1 closed — TASK-013 payments-as-source-of-truth status transitions, TASK-015 per-client invoice numbering, TASK-016 PaymentMethod enum hotfix, TASK-014 attempted then reverted (FilePicker is a web-mode no-op); db host port moved 5433 → 5434, two live data migrations run. |
| [[workflow/handoffs/handoff-005]] | 2026-06-10 | Short ad-hoc session — TASK-017 fixed collapsed newlines in the invoice PDF Description of Work with a `white-space: pre-wrap` CSS rule (PRs #21, #22); no Milestone 1 progress, TASK-003/006/007 still user-gated. |
| [[workflow/handoffs/handoff-006]] | 2026-09-01 | Milestone 1 closed at 10/11 (tag `milestone-01-stop-the-bleeding`, TASK-003 deferred to M3) and `/migrate-workflow` synced the project v0 → v15; sole PR #25 reallocated the dev DB host port 5434 → 5435 after a registry collision; discovered-work log fully triaged and the repo hardened with `protect-main` plus pinned squash settings. |
