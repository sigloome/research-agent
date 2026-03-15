- [x] 1. Add tracked and local planning artifacts for continuation + process-output hardening
- [x] 2. Add `chat_runtime_state` persistence and manager helpers
- [x] 3. Extend codex runtime adapter to resume by stored provider thread id and emit updated thread metadata
- [x] 4. Wire backend chat flow to:
  - [x] 4.1 read runtime state by `chat_id`
  - [x] 4.2 attempt resume first
  - [x] 4.3 fall back to transcript replay on invalid thread
  - [x] 4.4 persist new provider thread id and runtime status
- [x] 5. Tighten answer/process separation
  - [x] 5.1 update prompt instructions to suppress visible process narration
  - [x] 5.2 apply runtime content filtering before emitting text deltas
  - [x] 5.3 weaken completed process UI presentation by default
- [x] 6. Add deterministic tests for runtime state, parser behavior, and chat persistence
- [x] 7. Sync `docs/specs/agent-evaluation-standard.md` for the changed prompt/runtime path coverage

## BDD Evidence

1. Given an existing persisted chat, when the user reopens that chat and sends a follow-up question, then the browser-verified response continues the same conversation instead of starting an unrelated answer.
2. Given an in-flight assistant response, when the model is still streaming, then the browser-verified UI shows structured process feedback without requiring inline process narration in the final answer body.
3. Given a long history list, when the user enters filter text in the sidebar, then the browser-verified list narrows to matching chats while keeping the primary history actions accessible.

## TDD Evidence

1. Failing test: continuation/runtime coverage was added for stored thread resume, replay fallback, and content filtering in `tests/test_db_manager.py`, `tests/test_api_chats.py`, and `tests/backend/test_codex_sdk_runtime.py` before finalizing the runtime changes.
2. Implemented: backend runtime state persistence, adapter resume support, output filtering, and frontend structured progress rendering were added to satisfy the new deterministic cases.
3. Passing: `python3 -m pytest -q tests/test_db_manager.py tests/test_api_chats.py tests/backend/test_codex_sdk_runtime.py` and `PATH="/Users/bytedance/.nvm/versions/node/v22.14.0/bin:$PATH" npm --prefix frontend run build` completed successfully after implementation.

## Artifact Retention

1. Local diagnostics and follow-up verification notes for this change should be retained under `tmp/runs/evolution/` when additional runtime/browser investigation is needed beyond the tracked OpenSpec artifacts.
