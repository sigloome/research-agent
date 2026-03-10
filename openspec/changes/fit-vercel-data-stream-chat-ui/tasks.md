## 1. OpenSpec And Contract Alignment

- [x] 1.1 Update the evaluation policy wording in `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md` to reflect standardized SSE/UI stream expectations for AGT-16
- [x] 1.2 Update AGT-16 stream parser and fixtures for standardized SSE data-event parsing
- [x] 1.3 Update AGT-16 deterministic tests to validate the new stream fixture contract

## 2. Backend Stream Protocol Migration

- [x] 2.1 Refactor `/Users/bytedance/code/anti-demo/backend/agent.py` stream formatters to emit SSE UI message stream data events (remove legacy `0:`/`d:` formatting)
- [x] 2.2 Refactor `/Users/bytedance/code/anti-demo/backend/app.py` `/api/chat` response headers and media type to `text/event-stream` + `x-vercel-ai-ui-message-stream: v1`
- [x] 2.3 Update backend assistant-response accumulation to derive persisted text from standardized text parts only
- [x] 2.4 Ensure stream completion emits `[DONE]` and existing message persistence remains correct

## 3. Frontend `useChat` Migration And UX

- [x] 3.1 Replace manual fetch-reader parsing in `/Users/bytedance/code/anti-demo/frontend/src/components/ChatInterface.tsx` with `useChat`
- [x] 3.2 Map existing multi-chat session behavior into the `useChat` transport request shape (`message` + `session_id`)
- [x] 3.3 Implement tool-progress timeline rendering from structured streamed parts
- [x] 3.4 Add stop, retry/regenerate, and edit+resend controls bound to chat status
- [x] 3.5 Improve stream error states and reconnect messaging while preserving persisted chat loading
- [x] 3.6 Add accessible live transcript semantics for streaming responses
- [x] 3.7 Apply throttled streaming updates for smoother rendering

## 4. Verification

- [x] 4.1 Run targeted deterministic eval tests related to AGT-16 stream parsing/orchestration
- [x] 4.2 Run frontend build/lint checks for the chat UI migration
- [x] 4.3 Start app and validate end-to-end browser behavior (streaming, tool timeline, stop/retry/edit, chat persistence)

## BDD Evidence

1. Given chat streaming uses SSE UI message events with `x-vercel-ai-ui-message-stream: v1`.
2. When a user sends, retries, edits, or stops a chat response in the frontend.
3. Then streamed content/tool progress render correctly and persisted history remains consistent.

## TDD Evidence

1. Failing test introduced: AGT-16 stream/orchestration contract updates required before migration completion.
2. Implemented backend/frontend protocol and parser migration to satisfy the contract.
3. Passing verification: `4.1`, `4.2`, and `4.3` completed with deterministic and E2E validation.

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
