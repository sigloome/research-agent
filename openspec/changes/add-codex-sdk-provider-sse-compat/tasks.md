## 1. Implementation Tasks

- [x] 1.1 Consolidate `backend/agent.py` runtime to single `codex_sdk` provider.
- [x] 1.2 Implement codex-sdk adapter stream runner helper (subprocess + JSONL parsing + SSE mapping + error normalization).
- [x] 1.3 Add deterministic backend tests for:
  - provider route selection,
  - success stream contract (`finish` + `[DONE]`),
  - failure stream normalized error envelope.
- [x] 1.4 Verify `/api/chat` API behavior and frontend rendering remain normal under new provider path.
- [x] 1.5 Update local TODO handoff and done logs with verification evidence.

## BDD Evidence

1. Given `AGENT_PROVIDER=codex_sdk` and a valid codex run.
2. When client posts to `/api/chat`.
3. Then stream includes ordered UI SSE events (`start`, `text-delta`, `finish`) and terminates with `[DONE]`.

1. Given `AGENT_PROVIDER=codex_sdk` and codex exits non-zero.
2. When client posts to `/api/chat`.
3. Then stream includes structured `error` payload and `finishReason=error` and terminates with `[DONE]`.

1. Given frontend `DefaultChatTransport` uses `/api/chat`.
2. When backend runs with codex_sdk provider only.
3. Then frontend still renders assistant content and stream completion status without protocol changes.

## TDD Evidence

1. Failing tests introduced:
   - new codex-sdk adapter stream tests in backend test suite (success/failure paths).
2. Implemented minimal code to satisfy the tests:
   - single-provider codex-sdk route + adapter runner helper.
3. Passing verification:
   - `pytest -q tests/backend/test_codex_sdk_runtime.py` (from 2 failed to 2 passed),
   - `pytest -q tests/backend/test_bdd_chat_flow.py tests/evals/test_stream_parser_agent_trace.py tests/backend/test_multi_agent_runtime.py` (7 passed),
   - `pytest -q tests/backend/test_codex_sdk_runtime.py tests/backend/test_bdd_chat_flow.py` (5 passed),
   - `cd frontend && npm run build` (success),
   - API stream curl checks under `AGENT_PROVIDER=codex_sdk`:
     - verified `start/text-delta/finish/[DONE]` contract,
     - fixed duplicate `[DONE]` regression and revalidated.

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/20260310-175312.md`
