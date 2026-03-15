## Context

The current chat stack already persists transcript history per `chat_id`, but runtime continuity is incomplete because the provider thread identifier is not stored and reused. Every turn effectively starts from a fresh provider runtime. The system compensates by replaying transcript text into the query, but this should be fallback behavior rather than the default continuation path.

The stream/UI layer also leaks too much process content into final assistant messages. Tool and progress signals already have structured stream-part support, yet the agent prompt and frontend rendering still allow process narration to show up in the main answer body.

## Goals / Non-Goals

**Goals**

1. Preserve chat continuation for historical sessions without resumable streams.
2. Store and resume a stable provider thread per persisted chat when valid.
3. Automatically recover with transcript replay if the stored provider thread is invalid or unavailable.
4. Keep process state observable but weaker than the final answer once a turn completes.
5. Maintain compatibility with the Vercel UI message stream contract.

**Non-Goals**

1. Browser refresh reconnection of an active unfinished stream.
2. Provider abstraction for multiple runtime backends.
3. Large UI redesign or framework migration.

## Decisions

### 1) Add database-backed runtime state per chat

Create a `chat_runtime_state` table keyed by `chat_id` with:

- `provider_thread_id`
- `last_mode` (`resume` or `replay`)
- `last_error`
- `updated_at`

Rationale: transcript persistence and runtime continuity are distinct concerns and should not be conflated in the `messages` table.

### 2) Prefer provider thread resume, but always keep transcript replay available

Chat execution uses this order:

1. Load persisted `provider_thread_id` for the chat.
2. Attempt provider resume with the new user message only.
3. If resume fails, rerun the turn without `provider_thread_id` using transcript replay (`summary/recent-history` equivalent through the existing history query builder).
4. Persist the fresh provider thread id observed from the new turn.

Rationale: this preserves strong continuation when possible while keeping the system robust to thread invalidation and backend restarts.

### 3) Make process output structured-first, text-last

The assistant prompt will explicitly forbid user-visible process narration such as "I'll search..." or "Now I will read..." in final answer text. Tool/progress states remain visible through structured stream parts only.

Additional enforcement:

1. Streaming content filter is applied to runtime text deltas before they become UI `text-delta` parts.
2. Frontend presentation auto-collapses completed process/tool sections and downgrades them to secondary status once the answer finishes.

Rationale: prompt-only enforcement is not sufficient; we need prompt + runtime filter + UI hierarchy.

### 4) No `resume streams` in this change

We will not implement active-stream reconnection endpoints. Historical follow-up questions are handled by persisted transcript + provider-thread resume/fallback.

Rationale: active stream resumption solves a different problem and conflicts with existing stop behavior.

## Risks / Trade-offs

1. Resume may silently fail for provider-specific reasons.
   - Mitigation: detect failed resume attempt and automatically retry with replay.
2. Replay fallback can increase prompt size for long chats.
   - Mitigation: reuse the current history truncation logic and keep it bounded.
3. Prompt tightening may over-suppress useful short context.
   - Mitigation: keep tool timeline and optional collapsed process notes instead of removing all execution visibility.

## Rollback Plan

1. Trigger conditions:
   - deterministic continuation tests fail
   - persisted runtime state causes assistant-turn loss
   - process suppression hides essential answer content in covered tests
2. Rollback steps:
   - disable runtime-state lookup and resume path
   - revert to transcript-only continuation
   - restore current process rendering behavior
3. Validation:
   - persisted chat history still loads
   - assistant/user turn persistence remains intact
   - stream protocol tests remain green

## Ownership

1. Owner: chat/runtime maintainer
2. Reviewer: full-stack maintainer for backend + chat UI behavior
3. Oncall: backend maintainer coordinating rollback of runtime-state behavior

## Metrics Instrumentation

1. Continuation mode metric:
   - source: persisted `chat_runtime_state.last_mode` plus API/runtime deterministic tests
   - threshold: resume and replay paths must both remain covered at `100%` in deterministic verification
   - window: every change touching `/api/chat` continuation behavior
2. Runtime fallback health metric:
   - source: persisted `chat_runtime_state.last_error` and runtime fallback test fixtures
   - threshold: `0` unrecovered invalid-thread failures in covered deterministic cases
   - window: every change touching provider-thread resume logic
3. Output hygiene metric:
   - source: `tests/backend/test_codex_sdk_runtime.py` plus browser verification artifacts
   - threshold: `0` covered cases where final assistant text leaks process narration after filtering
   - window: every change touching prompt, runtime text mapping, or chat rendering
4. Process visibility metric:
   - source: browser verification of the chat UI process strip during active streaming
   - threshold: at least one verified in-flight state shows lightweight progress feedback while final-answer rendering remains primary
   - window: every change touching chat process presentation

## Deterministic Verification

1. Database tests for runtime-state CRUD.
2. Runtime parser tests for:
   - thread id metadata extraction
   - filtered text-delta output
   - resume-failure replay fallback
3. API tests for assistant/user persistence plus runtime-state update.
4. Eval policy sync for prompt/output-hygiene and continuation coverage.
