## Why

Persisted chat history currently supports retrieval and UI switching, but does not reliably preserve runtime continuity for follow-up questions. The backend stores transcript history in SQLite yet starts a fresh provider thread for every turn, so historical conversations are only visible, not actually continued. Separately, the assistant often emits process narration into the final response text, which makes completed answers noisy and weakens the distinction between answer content and execution state.

## What Changes

1. Add provider-thread runtime state persistence for each chat session and resume the same provider thread when possible.
2. Fall back to transcript replay when the stored provider thread cannot be resumed, keeping historical follow-up questions functional without resumable streams.
3. Separate answer text from process signaling more strictly:
   - keep tool/progress state in structured stream parts
   - reduce process narration leakage in assistant text
   - weaken completed process UI presentation by default
4. Extend deterministic tests and policy docs for continuation and output-hygiene behavior.

## Expected Benefit

1. Historical chats become materially usable for continued questioning after reloads and backend restarts.
2. Final answers become shorter, cleaner, and more user-facing without losing structured observability.
3. Stream/render behavior stays aligned with the Vercel UI message stream contract while improving UX quality.

## Success Metrics

1. Historical-chat continuation deterministic tests pass at `100%` for:
   - stored thread resume path
   - invalid-thread replay fallback path
2. Assistant output-hygiene deterministic checks prevent process-tag leakage at `100%` on covered fixtures.
3. Completed tool/process UI state defaults to collapsed/weak presentation in deterministic frontend coverage.

## Risk Metrics

1. Chat continuation regression: `0` failing deterministic cases on existing persisted-history coverage.
2. Stream contract regression: `0` violations of `x-vercel-ai-ui-message-stream: v1` flow tests.
3. Assistant persistence regression: `0` covered cases with missing final assistant transcript after stream completion.

## Kill Criteria

1. Resume/fallback logic causes duplicated or missing assistant turns in covered tests.
2. Stored runtime state causes provider failures that are not recovered by replay fallback.
3. Process minimization removes materially useful user-visible answer content in covered fixtures.

## Scope

- In scope:
  - backend runtime state persistence
  - codex adapter resume/fallback flow
  - prompt/output hygiene tightening
  - frontend process weak/default-collapse behavior
  - deterministic tests and eval policy sync
- Out of scope:
  - resumable stream endpoints
  - AI Elements adoption
  - visual redesign of the chat experience
