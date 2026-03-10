## Context

Current backend already has explicit retrieval/preference/verifier envelopes, but answer stage remains implicit in `backend/agent.py` prompt assembly. Stream events are unified and do not expose per-agent trace namespace. Governance scripts now cover trigger/bootstrap/candidate, yet promotion staging, run-log sync, and ownership policy checks are missing.

## Goals / Non-Goals

**Goals:**
- Add explicit answer-stage envelope to runtime result.
- Emit per-agent trace SSE events without breaking existing frontend parser.
- Add non-blocking soft-threshold warning capability for rollout metrics.
- Add scripted promotion workflow (sandbox/shadow/canary) + rollback command templates.
- Add run-log sync helper and ownership policy check scripts.
- Produce complete auditable artifact package (OpenSpec + tests + acceptance report).

**Non-Goals:**
- No change to public API request schema for `/api/chat`.
- No mandatory blocking runtime LLM judge in PR/nightly.
- No full replacement of existing benchmark pipeline; extend current path.

## Decisions

1. Keep compatibility-first stream design: add new `agent-trace` event type while retaining legacy event types.
2. Introduce answer-stage envelope in runtime context; avoid heavy architectural rewrite.
3. Enforce soft threshold warnings (non-blocking) for rollout policy in scripts and reports.
4. Make governance additions deterministic and script-based to fit existing eval policy.

## Risks / Trade-offs

- [Risk] Additional stream events may confuse old parsers -> Mitigation: append-only event type; legacy parser ignores unknown types.
- [Risk] Promotion automation may create false confidence -> Mitigation: keep explicit human approval gate and non-blocking warnings.
- [Risk] Stricter metrics may introduce noise -> Mitigation: keep warning thresholds configurable and trend-based.

## Rollback Plan

1. Trigger conditions:
   - agent-trace events cause stream regressions (`done_marker_rate < 0.95`);
   - p95 latency regression > 10% for two runs without quality gain.
2. Rollback steps:
   - disable trace emission via env flag;
   - revert promotion automation invocation from cycle script;
   - restore prior benchmark metric set.
3. Validation after rollback:
   - rerun `scripts/run_evolution_cycle.sh`;
   - verify deterministic tests and stream contract tests pass.

## Ownership

1. Owner: backend/runtime maintainer.
2. Reviewer: agent-eval governance maintainer.
3. Oncall: repository oncall owner for evolution workflow.

## Metrics Instrumentation

1. Metric: `agent_trace_coverage_rate`
   - Source: live benchmark parser + SSE event logs.
   - Threshold: warning if `< 0.95`.
   - Window: latest 2 benchmark runs.

2. Metric: `promotion_warning_count`
   - Source: promotion workflow report.
   - Threshold: warning if `> 0` (non-blocking).
   - Window: per run.

3. Metric: `runlog_sync_completeness`
   - Source: run-log sync script output.
   - Threshold: warning if `< 1.0`.
   - Window: pre-merge.

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/<timestamp>.md`

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
