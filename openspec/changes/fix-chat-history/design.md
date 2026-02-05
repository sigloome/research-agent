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
