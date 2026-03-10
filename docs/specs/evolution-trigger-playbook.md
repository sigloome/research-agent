# Evolution Trigger Playbook

## Purpose

Operational command guide for automatic evolution flow with deterministic-first policy.

## Standard Cycle

1. Run deterministic evolution cycle:
   - `scripts/run_evolution_cycle.sh`
   - The cycle auto-runs `scripts/run_live_benchmark.sh` after deterministic checks.
   - Live benchmark failures are recorded as soft warnings only (non-blocking).
2. On FAIL, trigger script auto-creates:
   - OpenSpec change scaffold (`openspec/changes/auto-evo-<timestamp>/`)
   - candidate task list (`tmp/runs/evolution/candidates/<timestamp>.md`)
3. Human reviews candidate list and approves one scoped task before code changes.

## Manual Trigger

- PASS:
  - `scripts/trigger_evolution.sh PASS <report-path> "<reason>"`
- FAIL:
  - `scripts/trigger_evolution.sh FAIL <report-path> "<reason>"`

## Candidate Planning (No Code Change)

- `scripts/generate_evolution_candidates.sh --report <report-path> --change-id <change-id>`

## Promotion Workflow (Non-Blocking Warnings)

- `scripts/promotion_workflow.sh`
- Warning thresholds:
  - `done_marker_rate < 0.98`
  - `tool_failure_rate > 0.02`
  - `latency_p95_ms > 30000`

## Benchmark Cadence Policy

1. Per-iteration live benchmark:
   - Enabled by default via `scripts/run_evolution_cycle.sh`.
   - Non-blocking; warning-only.
2. Periodic full live benchmark:
   - Not enabled for now.
   - Can be added later as an explicit opt-in workflow.

## Run-Log Sync

- `scripts/sync_runlogs_to_openspec.sh`

## Ownership Policy Check

- `python scripts/check_ownership_policy.py`

## Rollback Templates

1. Revert recent runtime-profile/trace changes.
2. Disable advanced profile route and use `baseline`.
3. Re-run:
   - `scripts/run_evolution_cycle.sh`
   - `scripts/run_live_benchmark.sh`
