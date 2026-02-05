## Why

Chat history fails to display when switching between chats because assistant messages are not being saved to the database. The root cause is a missing `import json` in `backend/app.py`, which causes the streaming response parser to fail silently, preventing message accumulation and persistence.

## What Changes

- **Fix missing import**: Add `import json` to `backend/app.py` to enable chunk parsing in `async_stream_generator()`
- **Ensure message persistence**: With the import fixed, the `full_response` accumulator will work correctly, and assistant messages will be saved via `manager.save_message()`
- **Chat history loads correctly**: Once messages are persisted, `handleSelectChat()` in the frontend will retrieve and display them

## Capabilities

### New Capabilities
<!-- None - this is a bug fix -->

### Modified Capabilities
<!-- None - the existing behavior is correct, just broken due to a missing import -->

## Impact

- **Code**: `backend/app.py` - add missing import statement
- **Behavior**: Chat sessions will now properly persist both user and assistant messages, enabling chat history to be displayed when switching between conversations
- **Data**: New chats created after the fix will have proper history; existing chats remain unaffected (their messages were never saved)
