## Why

Users currently have a single ephemeral chat session. To support complex workflows and longer-term usage, users need to be able to create multiple distinct chat sessions, switch between them, and have their conversation history persisted indefinitely.

## What Changes

- **Database Schema**: Introduce `chats` and `messages` tables in the local SQLite database.
- **Backend API**:
    - Add endpoints to List (GET), Create (POST), and Delete (DELETE) chats.
    - Update Chat endpoint to save messages to the database and support a `chat_id` parameter.
- **Frontend UI**:
    - Add a Sidebar to the Chat Interface.
    - Implement "New Chat" functionality.
    - Display list of past chats and allow switching.
    - Load history from the backend when switching chats.

## Capabilities

### New Capabilities
- `chat-session-management`: Capability to create, list, and manage persistent chat sessions and their message history.

### Modified Capabilities
- `chat-interface`: Updating the UI to support the sidebar, session switching, and loading persisted history instead of maintaining local state only.
