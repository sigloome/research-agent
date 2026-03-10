## Context

The chat interface allows users to switch between multiple chat sessions. When switching, the frontend calls `GET /api/chats/{chatId}` to fetch the message history. However, users report that switching chats shows no messages.

**Root Cause Analysis:**
1. In `backend/app.py`, the `async_stream_generator()` function parses streaming chunks using `json.loads()`
2. The `json` module is **not imported** at the top of the file
3. This causes a `NameError` when parsing chunks, which is caught silently by the try/except
4. The `full_response` accumulator never gets populated
5. When the stream ends, `save_message()` is called with an empty string (or not at all)
6. No assistant messages are persisted to the database
7. When fetching chat history, only user messages exist (or nothing)

## Goals / Non-Goals

**Goals:**
- Fix the missing import so assistant messages are saved correctly
- Ensure chat history displays when switching between chats

**Non-Goals:**
- Recovering messages from chats that already ran (they were never saved)
- Changing the streaming protocol or message format
- Refactoring the chunk parsing logic

## Decisions

**Decision 1: Add `import json` to app.py**
- Rationale: This is the direct fix for the NameError
- Alternative considered: None - this is the only correct solution

**Decision 2: No additional error handling changes**
- Rationale: The existing try/except already logs errors via `logger.error()`. The DEBUG logs in place will help identify future parsing issues.

## Risks / Trade-offs

**[Risk] Existing chat sessions have no history** → Cannot be mitigated; those messages were never saved. Users will need to start new conversations to see history working.

**[Risk] Silent failures in chunk parsing** → The existing error logging (`logger.error`) captures these. The fix addresses the immediate issue, but the pattern of silently continuing on parse errors could hide future bugs.

## Rollback Plan

1. Trigger conditions for rollback:
   - New parsing/persistence regressions appear after applying the import fix.
   - Chat history visibility worsens compared to baseline.
2. Rollback steps:
   - Revert the `backend/app.py` import change commit.
   - Restore previous backend artifact state.
3. Validation after rollback:
   - Confirm stream endpoint still returns responses.
   - Confirm known pre-fix behavior is restored (for diagnosis only).
   - Re-run chat persistence checks to compare behavior.

## Ownership

1. Owner: Backend maintainer responsible for chat streaming parser path.
2. Reviewer: Backend reviewer for API chat persistence behavior.
3. Oncall: Backend oncall for rollback if regression occurs.

## Metrics Instrumentation

1. Metric: Assistant message persistence success rate.
   - Source: chat persistence integration checks and API tests.
   - Threshold: `>= 99.9%`.
   - Window: per PR run and 7-day rolling post-deploy.
2. Metric: Stream chunk parse exception rate.
   - Source: backend error logs in `async_stream_generator`.
   - Threshold: `<= baseline`, no sustained increase.
   - Window: daily and weekly rollups.

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
