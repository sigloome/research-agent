## Why

Current implementation is close to the target project description, but key gaps still block claiming a complete closed loop:

1. answer stage is not explicitly decoupled in runtime observability;
2. per-agent SSE trace namespace is missing;
3. promotion workflow automation (sandbox/shadow/canary + rollback templates) is still manual;
4. quality metric strictness and trend checks are not yet production-grade;
5. governance tail items (run-log sync, ownership checks, playbook) remain incomplete.

This change closes these gaps in one auditable package so external project claims can move to “fully landed” with evidence.

## What Changes

- Runtime:
  - add explicit answer-stage envelope in multi-agent runtime output;
  - emit per-agent `agent-trace` SSE events with `trace_id/role/stage/status/latency_ms`;
  - keep existing UI-message stream contract backward compatible.
- Governance/automation:
  - add promotion workflow automation script (`sandbox -> shadow -> canary`) with rollback command templates;
  - add non-blocking soft-threshold warning checks for rollout metrics.
- Evaluation:
  - add stricter parser-backed contract checks and claim/evidence proxy checks;
  - add trend export helper for weekly drift tracking.
- Governance tail:
  - add run-log sync helper from `tmp/runs/evolution` to tracked change artifacts;
  - add owner/reviewer/oncall policy check script;
  - add evolution trigger playbook documentation.
- Scope boundary:
  - no mandatory hard-blocking runtime judge; warnings remain non-blocking by policy.

## Expected Benefit

1. User impact: higher trust from clearer stage observability and more stable rollout path.
2. Engineering quality/stability: removes ambiguity between implemented vs planned architecture claims.
3. Operability: rollout warnings and rollback templates reduce incident recovery latency.

## Success Metrics

1. `agent_trace_coverage_rate >= 0.95` over benchmark cases (window: latest 2 runs).
2. `done_marker_rate >= 0.98` and `finish_stop_rate >= 0.98` (window: latest 2 runs).
3. `promotion_workflow_report_generated = true` for each run_evolution PASS cycle (window: daily).
4. `runlog_sync_completeness = 1.0` (each active change references latest evolution artifacts before merge).

## Risk Metrics

1. `latency_p95_ms` regression > 10% for 2 consecutive runs without quality gain -> emit canary warning and require manual rollback decision.
2. `tool_failure_rate > 0.02` or `done_marker_rate < 0.95` -> emit warning, pause promotion progression, run rollback template.

## Kill Criteria

1. If added observability scripts/events increase operational noise without improving remediation lead time for 3 consecutive weeks.
2. If rollout automation adds >20% execution time overhead while failing to reduce regressions.

## Capabilities

### New Capabilities

- `per-agent-trace-events`: non-blocking trace events in SSE stream.
- `promotion-workflow-automation`: scripted sandbox/shadow/canary checks with rollback guidance.
- `runlog-sync-helper`: promote local run evidence into tracked artifacts.
- `ownership-policy-check`: deterministic owner/reviewer/oncall policy verification.

### Modified Capabilities

- `multi-agent-runtime-answer-stage`: explicit answer envelope for runtime observability.
- `benchmark-alerting`: soft-threshold warnings added, still non-blocking.

## Impact

- Code paths:
  - `backend/multi_agent_runtime.py`
  - `backend/agent.py`
  - `evals/**`
  - `scripts/**`
- Specs/evals/tests:
  - `openspec/changes/close-remaining-agent-gap/**`
  - `tests/backend/test_multi_agent_runtime.py`
  - `tests/backend/test_bdd_chat_flow.py`
  - additional governance/eval tests introduced in this change
- Operational considerations:
  - warnings are non-blocking; rollout remains human-approved.

## Metadata

- Change ID: `close-remaining-agent-gap`
- Title: Close remaining agent gap for full-loop claim
- Created At (UTC): 2026-03-10T08:48:46Z

## Evolution Run Context

- Latest run index: `tmp/runs/evolution/index.md`
- Latest run report: `tmp/runs/evolution/<timestamp>.md`

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
