## Context

`backend/agent.py` originally routed chat execution through `_run_codex_bridge`.
Frontend consumes standardized UI SSE stream via `DefaultChatTransport` and expects stable event ordering and `[DONE]` termination.

We need a single-provider runtime that uses local `codex-sdk adapter` support without breaking existing stream contracts or chat persistence.

## Goals / Non-Goals

**Goals:**
- Remove provider routing and keep only `codex_sdk` runtime.
- Preserve frontend contract and backend chat persistence behavior.
- Add deterministic tests for success/failure stream paths.

**Non-Goals:**
- No change to frontend transport API shape.
- No tool-level timeline parity with bridge function-tool events in this iteration.
- No multi-provider runtime support in this change.

## Decisions

1. Decision: introduce a dedicated codex-sdk stream runner helper.
   - Rationale: isolate subprocess/event parsing complexity from chat API orchestration.
   - Alternative rejected: inline event parsing inside `MainAgent.run`, rejected due readability/testability risk.

2. Decision: keep stream event schema unchanged (UI message stream contract).
   - Rationale: avoid frontend changes and reduce regression surface.

3. Decision: normalize non-JSON codex diagnostics into `error` SSE payload on non-zero exit.
   - Rationale: codex may emit plain-text diagnostics; frontend needs structured error output.

## Risks / Trade-offs

- [Risk] codex CLI startup/network/config failures vary across environments.
  - Mitigation: deterministic error normalization tests and explicit preflight diagnostics.
- [Risk] provider consolidation may break legacy bridge assumptions in scripts/docs.
  - Mitigation: sync helper scripts and deterministic config checks in the same change.
- [Risk] codex-sdk adapter stream may lack tool granularity compared to historical bridge events.
  - Mitigation: accepted for this slice; keep UI contract stable and avoid tool-timeline coupling.

## Rollback Plan

1. Trigger conditions for rollback:
   - deterministic stream contract failures in codex_sdk mode,
   - increased `/api/chat` error rate above threshold during validation window.
2. Rollback steps:
   - revert to prior commit if rollback is required.
3. Validation after rollback:
   - rerun chat stream BDD tests and retrieval deterministic suite.

## Ownership

1. Owner: backend/runtime maintainer.
2. Reviewer: full-stack reviewer for stream protocol + frontend compatibility.
3. Oncall: backend oncall owner for runtime rollback.

## Metrics Instrumentation

1. Metric: `codex_sdk_stream_contract_pass_rate`
   - Source: backend deterministic tests (`tests/backend/*stream*`, BDD chat flow)
   - Threshold: 100%
   - Window: per PR and nightly deterministic runs

2. Metric: `error_envelope_presence_rate`
   - Source: codex_sdk failure-path tests
   - Threshold: 100%
   - Window: per PR run

3. Metric: `frontend_stream_render_regression`
   - Source: manual/API-front validation checklist
   - Threshold: 0 regressions (finish + `[DONE]` + visible assistant content)
   - Window: implementation verification session

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/20260310-175312.md`
