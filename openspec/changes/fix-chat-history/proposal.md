## Why

Chat history fails to display when switching between chats because assistant messages are not being saved to the database. The root cause is a missing `import json` in `backend/app.py`, which causes the streaming response parser to fail silently, preventing message accumulation and persistence.

## What Changes

- **Fix missing import**: Add `import json` to `backend/app.py` to enable chunk parsing in `async_stream_generator()`
- **Ensure message persistence**: With the import fixed, the `full_response` accumulator will work correctly, and assistant messages will be saved via `manager.save_message()`
- **Chat history loads correctly**: Once messages are persisted, `handleSelectChat()` in the frontend will retrieve and display them

## Expected Benefit

1. Restore core chat-history functionality for multi-session usage.
2. Eliminate silent assistant-message loss caused by chunk parse failures.
3. Reduce support/debug overhead caused by missing-history reports.

## Success Metrics

1. Assistant message persistence success in chat integration tests: `100%` for covered fixtures.
2. Chat-switch history load correctness: `100%` in deterministic orchestration fixtures.
3. Production/staging missing-history bug reports for this root cause: `0` over 30-day window.

## Risk Metrics

1. Any regression in SSE stream parsing contract tests triggers immediate rollback.
2. Assistant save failure rate above `0.1%` in monitored chat requests triggers rollback.
3. New parsing exceptions in chat stream path above baseline trigger rollback and hotfix.

## Kill Criteria

1. This fix is considered complete and retired if metrics remain stable for one release cycle with zero recurrences.
2. If a broader stream architecture change supersedes this path, this change is folded into the successor implementation.

## Capabilities

### New Capabilities
<!-- None - this is a bug fix -->

### Modified Capabilities
<!-- None - the existing behavior is correct, just broken due to a missing import -->

## Impact

- **Code**: `backend/app.py` - add missing import statement
- **Behavior**: Chat sessions will now properly persist both user and assistant messages, enabling chat history to be displayed when switching between conversations
- **Data**: New chats created after the fix will have proper history; existing chats remain unaffected (their messages were never saved)
