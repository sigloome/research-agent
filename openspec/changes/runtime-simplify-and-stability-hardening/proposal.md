## Why

Remaining P0 and P2 backlog items block long-term maintainability and reliability:

1. runtime bridge logic in `backend/agent.py` has accumulated control-flow complexity;
2. listener stability for local dev/start-restart should be deterministic and provable;
3. metric strictness is still heuristic and trend tracking is manual.

This change reduces runtime complexity while preserving behavior and adds deterministic hardening for listener lifecycle and metric quality tracking.

## What Changes

- Runtime simplification:
  - refactor bridge request/stream handling into smaller functions;
  - preserve current API response contract and tool routing behavior.
- Reliability hooks:
  - explicit auth preflight, timeout/retry wrapper, consistent error envelope path.
- Listener hardening:
  - tighten `start-dev` cleanup/start flow and post-start sanity checks.
- Metric strictness + trend:
  - add parser-backed metric validators and weekly trend export helper.
- Scope boundary:
  - no provider migration; remain codex bridge runtime.

## Expected Benefit

1. User impact: fewer transient runtime failures and more stable local/dev demo behavior.
2. Engineering impact: lower complexity in hot path and easier debugging/verification.
3. Operability: better trend visibility and earlier drift detection.

## Success Metrics

1. `bridge_runtime_errors_per_100_requests <= 1` in local benchmark window (2 consecutive runs).
2. `listener_sanity_pass_rate = 1.0` across 10 restart attempts.
3. weekly trend export generated at least once per week with quality/latency/cost fields present.

## Risk Metrics

1. `done_marker_rate < 0.95` after refactor -> rollback runtime simplification commit.
2. `latency_p95_ms` regression > 15% without quality gain -> pause rollout and restore previous flow.

## Kill Criteria

1. If simplification does not reduce maintenance complexity (no net code/readability improvement) after full implementation.
2. If stricter metric validators create excessive false positives and block normal iteration.

## Capabilities

### New Capabilities

- `bridge-runtime-simplified-control-flow`: smaller composable bridge runtime internals.
- `weekly-metrics-export`: trend export script with structured output.

### Modified Capabilities

- `start-dev-listener-stability`: deterministic cleanup/sanity behavior across restarts.
- `benchmark-metric-validation`: stricter parser-backed checks.

## Impact

- Code paths:
  - `backend/agent.py`
  - `scripts/start-dev.sh`
  - `scripts/check_dev_listener_sanity.sh`
  - `tmp/interview_pack/scripts/live_benchmark.py` (+ supporting helpers)
- Specs/evals/tests:
  - `openspec/changes/runtime-simplify-and-stability-hardening/**`
  - runtime/metrics/listener tests
- Operational considerations:
  - keep deterministic-first gate behavior;
  - warnings remain non-blocking.

## Metadata

- Change ID: `runtime-simplify-and-stability-hardening`
- Title: Runtime simplification and listener/metrics hardening
- Created At (UTC): 2026-03-10T09:07:03Z

## Evolution Run Context

- Latest run index: `tmp/runs/evolution/index.md`
- Latest run report: `tmp/runs/evolution/<timestamp>.md`
