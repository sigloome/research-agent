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

## Expected Benefit

1. Improve continuity for research workflows by making chat context persistent across sessions.
2. Reduce repeated user work caused by losing prior assistant context.
3. Increase reliability of chat state management by moving from ephemeral frontend state to database-backed sessions.

## Success Metrics

1. Chat-history retrieval success rate for existing sessions: `>= 99.5%` over 14-day window.
2. Message persistence correctness (user+assistant saved in DB): `>= 99.9%` in integration tests and staging probes.
3. Session-switch latency (P95 loading existing chat): `<= 500ms` in local/staging profile.

## Risk Metrics

1. Chat endpoint error rate increase above `+0.5%` absolute after rollout triggers rollback.
2. Message duplication or ordering defect rate above `0.1%` in regression/eval fixtures triggers rollback.
3. DB lock/contention failures above baseline by `> 10%` triggers rollback and schema/index review.

## Kill Criteria

1. If persistent multi-chat does not measurably improve successful session reuse after two release cycles.
2. If operational complexity and defect rate remain above acceptable thresholds after remediation.

## Capabilities

### New Capabilities
- `chat-session-management`: Capability to create, list, and manage persistent chat sessions and their message history.

### Modified Capabilities
- `chat-interface`: Updating the UI to support the sidebar, session switching, and loading persisted history instead of maintaining local state only.
