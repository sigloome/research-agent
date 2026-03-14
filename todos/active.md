# Active Backlog (Local)

Last updated: 2026-03-10

## P0 - Next Implementation Features

- [x] Evaluate direct OpenAI runtime simplification
  - Keep current API behavior while reducing unnecessary normalization/control-plane complexity.
  - Identify minimum required reliability hooks (auth preflight, timeout/retry, error envelope).
  - Draft one scoped refactor plan before code changes.

- [x] Stabilize `start-dev` single-listener behavior
  - Ensure backend hot-reload does not leave duplicate listeners on `:18000`.
  - Update start/restart workflow or helper script for deterministic cleanup.

- [x] Auto trigger engine (`scripts/trigger_evolution.sh`)
  - Detect failure signals from latest `tmp/runs/evolution/*.md` report.
  - On failure, scaffold a new change under `openspec/changes/<change-id>/` from templates.
  - Write trigger summary to `tmp/runs/evolution/index.md` and `todos/handoff.md`.

- [x] Change bootstrap automation (`scripts/new_evolution_change.sh`)
  - Generate `proposal.md`, `design.md`, `tasks.md` with mandatory sections pre-filled.
  - Include fields for expected benefit, success metrics, risk metrics, kill criteria.

- [x] Candidate generation pipeline (manual-assisted)
  - Script flow: validate artifacts -> run deterministic checks -> produce implementation task list.
  - Keep human approval mandatory before code-changing steps.

## P1 - Quality and Safety Hardening

- [x] Executable BDD gate
  - Introduce pytest-bdd/cucumber-style Given/When/Then checks.
  - Make failing BDD scenarios block merge locally.

- [x] Promotion workflow automation
  - Add explicit local stages: sandbox -> shadow -> canary simulation.
  - Define rollback commands and auto-trigger on risk metric breach.

- [x] Run-log sync helper
  - Summarize `tmp/runs/evolution` reports into tracked OpenSpec files before merge.

## P2 - Repo Governance Enhancements

- [x] Ownership approval automation (owner/reviewer/oncall policy check script).
- [x] Add "evolution trigger playbook" doc with exact commands and examples.

## P2 - Interview Readiness (Session-local)

- [x] Improve metric strictness for contract-quality proxies:
  - replace current heuristic checks with parser-backed contract validation and claim-level grounding checks.
- [x] Add long-window trend tracking:
  - weekly benchmark export and drift dashboard for quality/latency/cost trends.
