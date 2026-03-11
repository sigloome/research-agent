# Acceptance Report: add-codex-sdk-provider-sse-compat

## Scope Completed

1. Added single provider runtime path `AGENT_PROVIDER=codex_sdk`.
2. Implemented codex-sdk adapter runtime adapter:
   - local subprocess execution via Node script using `@openai/codex-sdk`
   - JSONL -> UI SSE event mapping
   - normalized error envelope for non-zero/non-JSON failure outputs
3. Preserved `/api/chat` SSE contract used by frontend `DefaultChatTransport`.

## Code Paths

- `/Users/bytedance/code/anti-demo/backend/agent.py`
- `/Users/bytedance/code/anti-demo/backend/codex_sdk_runtime.py`
- `/Users/bytedance/code/anti-demo/backend/codex_sdk_adapter/run_stream.mjs`
- `/Users/bytedance/code/anti-demo/backend/codex_sdk_adapter/package.json`
- `/Users/bytedance/code/anti-demo/tests/backend/test_codex_sdk_runtime.py`
- `/Users/bytedance/code/anti-demo/openspec/changes/add-codex-sdk-provider-sse-compat/specs/chat-interface/spec.md`

## Deterministic Verification

1. Red -> Green TDD
   - initial: `pytest -q tests/backend/test_codex_sdk_runtime.py` -> 2 failed
   - final: `pytest -q tests/backend/test_codex_sdk_runtime.py` -> 2 passed

2. Regression checks
   - `pytest -q tests/backend/test_bdd_chat_flow.py tests/evals/test_stream_parser_agent_trace.py tests/backend/test_multi_agent_runtime.py` -> 7 passed
   - `pytest -q tests/backend/test_codex_sdk_runtime.py tests/backend/test_bdd_chat_flow.py` -> 5 passed

3. Frontend build
   - `cd frontend && npm run build` -> success

## API + Frontend Live Validation

1. Backend live API check (provider=`codex_sdk`):
   - `POST /api/chat` returns stream with `start/start-step/text-start/text-delta/text-end/finish-step/data-metrics/finish/[DONE]`.
2. Frontend live rendering check:
   - with Vite dev server proxied to backend `18003`, sent a real chat message and confirmed assistant text rendered: `frontend-codex-sdk-ok`.

## Issues Found and Resolved During Validation

1. Duplicate `[DONE]` marker (agent + app both emitting) -> fixed by keeping `[DONE]` emission only at app layer.
2. Non-JSON codex diagnostics on failure could produce silent error finish -> fixed by fallback diagnostic extraction into structured `error` event.

## Rollback Readiness

- Immediate rollback switch: restore previous commit (bridge path no longer supported in runtime).
- No frontend protocol rollback required.
