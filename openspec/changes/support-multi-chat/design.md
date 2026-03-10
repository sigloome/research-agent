## Context
The current chat system is ephemeral. Messages are stored only in the frontend's React state and lost on refresh. The backend supports stateful `ClaudeSDKClient` sessions via `session_id`, but does not persist the conversation history text for retrieval. Users need to verify past conversations and manage multiple topics.

## Goals / Non-Goals
**Goals:**
- persist all chat messages to a local SQLite database.
- allow users to create, list, and switch between multiple named chat sessions.
- reload full chat history when opening a previous session.

**Non-Goals:**
- Real-time synchronization across multiple devices (local only).
- Advanced search within chat history (for now).

## Decisions

### 1. Database Schema
We will add two tables to `skills/knowledge/db/schema.sql` (or equivalent initialization in `manager.py`):
- `chats`: `id` (UUID), `title` (Text), `created_at` (Timestamp)
- `messages`: `id` (Auto-inc), `chat_id` (UUID), `role` (Text), `content` (Text), `created_at` (Timestamp)

Rationale: Simple relational structure fits our existing SQLite usage.

### 2. API Design
We will expose standard REST endpoints:
- `GET /api/chats`: List all chats (for sidebar).
- `POST /api/chats`: Create a new chat. Returns `chat_id`.
- `GET /api/chats/{chat_id}`: Get history for a chat.
- `DELETE /api/chats/{chat_id}`: Delete a chat.

The existing `POST /api/chat` will be modified to accept `session_id` (which maps to `chat_id`) and will be responsible for **saving messages** to the DB.

### 3. Session Management
We will map the DB `chat_id` directly to the `ClaudeSDKClient`'s `session_id`.
- When a user sends a message in chat `X`, we pass `session_id=X` to the SDK.
- The SDK manages the LLM context.
- We manage the persistent history record.

## Risks / Trade-offs
**Risk**: SDK Process Restart
- If the python backend restarts, the `ClaudeSDKClient` might lose its in-memory context (e.g. variables defined in a REPL).
- **Mitigation**: The *transcript* is safe in our DB. The user can see the history. If they continue the conversation, the Agent will see the *new* messages but might have lost "deep" state (variables). This is an acceptable trade-off for V1. We can potentially "replay" history to the SDK on reconnect in V2 if needed, but for now we treat the SDK session as a best-effort context container.

## Rollback Plan

1. Trigger conditions for rollback:
   - Chat persistence introduces data-integrity regressions (duplicate/missing messages above threshold).
   - API error rate increases beyond agreed risk metric after deployment.
2. Rollback steps:
   - Revert multi-chat API wiring to prior single-session flow.
   - Disable sidebar/session switching paths in frontend if needed.
   - Keep existing DB data untouched to avoid destructive migration risk.
3. Validation after rollback:
   - Verify `/api/chat` basic send/receive path works.
   - Verify no new 5xx regressions in chat endpoints.
   - Verify frontend can send and receive messages normally.

## Ownership

1. Owner: Backend chat/session maintainers for implementation and defect triage.
2. Reviewer: Full-stack maintainer covering backend+frontend chat flow.
3. Oncall: Backend service oncall responsible for rollback execution.

## Metrics Instrumentation

1. Metric: Chat message persistence correctness rate.
   - Source: DB-state integration checks and chat API tests.
   - Threshold: `>= 99.9%` correctness.
   - Window: per PR run and 14-day post-deploy window.
2. Metric: Chat API error rate (`/api/chat`, `/api/chats/*`).
   - Source: backend logs/monitoring counters.
   - Threshold: no increase above `+0.5%` absolute.
   - Window: 24-hour and 7-day rolling windows.

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
