## Context

The current chat streaming pipeline is split across custom framing (`0:` and `d:`), mixed parsing logic in backend persistence, and manual frontend stream decoding. This creates protocol drift from Vercel UI message stream expectations, increases parse fragility, and makes advanced controls (stop/retry/edit/reconnect) harder to implement consistently.

This change crosses backend streaming, frontend chat state architecture, and deterministic eval fixtures. It must preserve local persistence and multi-chat behavior while replacing the wire protocol and rendering model.

## Goals / Non-Goals

**Goals:**
- Standardize `/api/chat` streaming as SSE with `text/event-stream` and `x-vercel-ai-ui-message-stream: v1`.
- Emit/consume Vercel-style UI message stream parts in a deterministic order (start/text/tool/finish/[DONE]).
- Replace manual stream parsing UI with `useChat` and status-driven actions (`stop`, retry/regenerate, edit+resend).
- Improve tool progress timeline and failure/recovery states without regressing existing persisted-chat workflows.
- Update deterministic AGT-16 fixtures/parsers to enforce the new stream contract.

**Non-Goals:**
- Full transport-level resume API (`prepareReconnectToStreamRequest`) in this iteration.
- Cross-device sync or cloud persistence.
- Reworking non-chat pages/components.

## Decisions

### 1) Backend stream contract becomes canonical SSE UI stream
- `/api/chat` will return `StreamingResponse` with `media_type="text/event-stream"` and header `x-vercel-ai-ui-message-stream: v1`.
- Output will use `data: <json>\n\n` SSE frames and terminate with `data: [DONE]\n\n`.
- Text and metadata frames are represented as standard UI-message parts rather than transport-specific `0:`/`d:` prefixes.

Rationale: this aligns backend behavior with Vercel AI SDK transports and removes parsing ambiguities.

Alternative considered: keep dual compatibility by emitting legacy `0:/d:` alongside SSE data payloads. Rejected because it prolongs complexity and makes parser correctness harder to assert.

### 2) Frontend chat state moves to `useChat`
- `ChatInterface` uses `useChat` + transport hooks for send/retry/stop/state transitions.
- Rendering uses message `parts` first, with markdown rendering for assistant text segments and structured rendering for tool timeline events.
- Request body remains compatible with backend (`message`, `session_id`) through transport request preparation.

Rationale: `useChat` provides robust streaming lifecycle and reduces custom stream parser maintenance.

Alternative considered: keep existing custom `fetch` reader and only adjust line format. Rejected because it still duplicates transport responsibilities and complicates controls.

### 3) Persistence behavior remains backend-authoritative
- Backend continues saving user messages on request receipt and assistant message once streaming completes.
- Assistant text accumulation will be derived from standard text parts rather than legacy chunk prefixes.

Rationale: this keeps storage semantics stable and reduces migration risk for existing chat history endpoints.

### 4) Deterministic eval updates are required with protocol migration
- AGT-16 parser and fixture data will be updated to the standardized SSE data events.
- `docs/specs/agent-evaluation-standard.md` path/contracts will reflect that mixed legacy parsing is no longer the expected default contract.

Rationale: repo policy requires deterministic-first eval alignment when prompt/tool/stream behavior changes.

## Risks / Trade-offs

- [Risk] Existing custom parser assumptions still referenced in edge code paths → Mitigation: remove dead parsing branches and run targeted grep/tests for `0:`/`d:` readers.
- [Risk] `useChat` migration may regress sidebar/multi-chat interactions → Mitigation: preserve explicit session selection/load flow and validate via browser e2e.
- [Risk] Tool events emitted by backend may not map 1:1 to timeline UI expectations → Mitigation: normalize backend tool payload shape and render defensively.
- [Risk] Breaking stream wire format for any old client → Mitigation: scope this change to current frontend; document break in proposal and specs.

## Rollback Plan

1. Trigger conditions for rollback:
   - SSE contract mismatch causes client breakage or high chat failure rates.
   - Deterministic AGT-16 contract violations appear in staging/production runs.
2. Rollback steps:
   - Revert backend/frontend stream migration commit set.
   - Restore prior parser paths and transport wiring.
   - Revert updated fixtures/parsers if needed to keep tests coherent with restored runtime.
3. Validation after rollback:
   - Confirm legacy chat flow functions end-to-end.
   - Confirm stream endpoint returns parseable responses for current client.
   - Confirm chat persistence remains intact.

## Ownership

1. Owner: Chat platform maintainer for backend/frontend stream contract.
2. Reviewer: Full-stack reviewer for transport protocol and UI behavior.
3. Oncall: Backend oncall coordinating rollback for chat streaming incidents.

## Metrics Instrumentation

1. Metric: AGT-16 deterministic orchestration contract pass rate.
   - Source: eval suite `evals/tests/test_retrieval_prompt_paths.py`.
   - Threshold: `100%` in PR/nightly deterministic profiles.
   - Window: every PR and nightly runs.
2. Metric: `/api/chat` stream parse/runtime error rate.
   - Source: backend logs and stream parsing exception counters.
   - Threshold: reduce by `>= 80%` from pre-migration baseline; no post-deploy regression > `+0.5%`.
   - Window: 14-day post-deploy plus daily rollups.

## Migration Plan

1. Update OpenSpec artifacts (proposal/design/specs/tasks).
2. Implement backend SSE message stream format and headers.
3. Implement frontend `useChat` migration with tool timeline and controls.
4. Update deterministic eval parser fixtures and policy docs.
5. Run unit/eval tests and browser verification on local app.
6. Rollback plan: revert this change set to previous custom parser behavior if blocking issues appear.

## Open Questions

- Should a follow-up change add resumable stream endpoints (`GET /api/chat/{id}/stream`) for full reconnect semantics?
- Should we hard-stop exposing raw internal tool event payloads and enforce a strict frontend-safe schema?
