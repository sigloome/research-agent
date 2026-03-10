## 1. Implementation Tasks

- [x] 1.1 Runtime gap closure
- [x] 1.2 Emit per-agent trace events and preserve backward stream contract
- [x] 1.3 Add soft-threshold warning helper for benchmark/promotion workflow (non-blocking)
- [x] 1.4 Add promotion workflow automation script with rollback templates
- [x] 1.5 Add run-log sync helper and ownership policy checker
- [x] 1.6 Add/extend deterministic tests for runtime and governance scripts
- [x] 1.7 Produce acceptance report in tracked artifact path

## BDD Evidence

Document executable behavior scenarios.

1. Given runtime profile mode is enabled.
2. When `/api/chat` executes a request.
3. Then stream includes non-breaking `agent-trace` events for runtime stages and still ends with `finish` + `[DONE]`.

1. Given deterministic checks pass but warning thresholds are breached.
2. When promotion workflow script runs.
3. Then warning entries are generated and rollout remains non-blocking pending human approval.

## TDD Evidence

Document the red-green-refactor trace.

1. Failing test introduced:
   - runtime tests for answer envelope + trace event emission + parser compatibility.
   - script tests for promotion/run-log sync/ownership checks.
2. Implemented minimal code:
   - add answer envelope + trace event emitter;
   - add promotion/run-log/ownership scripts and soft warning helper.
3. Passing verification:
   - `pytest -q tests/backend/test_multi_agent_runtime.py tests/backend/test_bdd_chat_flow.py`
   - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`
   - `scripts/run_evolution_cycle.sh`

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/<timestamp>.md`

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
