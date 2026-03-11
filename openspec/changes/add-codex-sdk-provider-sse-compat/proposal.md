## Why

Current backend runtime is hard-wired to `codex_bridge` (Responses API-compatible endpoint).
For local/desktop-first workflows we need a second runtime path that can run Codex agent behavior via local `@openai/codex-sdk` while preserving:

1. existing orchestrator + workers architecture,
2. current `/api/chat` SSE contract used by frontend (`x-vercel-ai-ui-message-stream: v1`),
3. deterministic-first verification expectations.

Without this path, development and validation are blocked by bridge endpoint/network availability and cannot reliably validate local Codex profile/config behavior.

## What Changes

- Adopt a single runtime provider mode: `AGENT_PROVIDER=codex_sdk`.
- Implement a Codex SDK streaming adapter in backend that:
  - runs a local Node adapter backed by `@openai/codex-sdk` `runStreamed()` events,
  - maps codex JSONL events to existing UI SSE events (`start`, `text-delta`, `finish`, `[DONE]`),
  - emits normalized error envelopes on non-zero exits and non-JSON diagnostics.
- Remove runtime provider switching in chat execution path.
- Add deterministic tests for:
  - provider selection,
  - SSE stream contract and finish markers,
  - error normalization behavior.
- No frontend protocol changes; only compatibility verification.

Out of scope:

- No migration of tool execution ownership to codex native tool protocol in this change.
- No UI redesign/model switcher UX changes.

## Expected Benefit

1. User impact:
   - Local mode can run even when bridge endpoint is unavailable; chat UX remains unchanged.
2. Engineering quality/stability impact:
   - Runtime abstraction is explicit and testable; provider-specific failures are isolated.
3. Cost/performance/operability impact:
   - Enables local codex profile/config validation without forcing external bridge dependency in all test loops.

## Success Metrics

1. `codex_sdk_stream_contract_pass_rate = 100%` over deterministic test suite in CI/local runs.
2. `frontend_stream_render_regression = 0` on chat flow smoke checks (no missing finish or `[DONE]` markers) during verification run.
3. `error_envelope_presence_rate = 100%` for codex-sdk adapter non-zero exit test cases.

## Risk Metrics

1. `api_chat_error_rate` increases by `> 2%` vs baseline in local benchmark window -> rollback to previous runtime commit.
2. missing stream terminator (`finish` or `[DONE]`) in any deterministic stream test -> block release and rollback provider-specific commit.

## Kill Criteria

1. If codex-sdk adapter provider cannot keep SSE contract stable (two consecutive deterministic failures), stop rollout and rollback.
2. If local runtime introduces unacceptable latency/cost tradeoff, stop rollout and reassess runtime strategy.

## Capabilities

### New Capabilities

- `runtime-provider-codex-sdk`: Single local Codex SDK runtime with SSE contract compatibility.

### Modified Capabilities

- `api-chat-provider-routing`: `/api/chat` runtime uses only codex-sdk provider.

## Impact

- Code paths:
  - `backend/agent.py`
  - `backend/app.py` (verification compatibility only, no protocol change expected)
  - new backend runtime helper module for codex-sdk adapter path
- Specs/evals/tests:
  - `openspec/changes/add-codex-sdk-provider-sse-compat/specs/chat-interface/spec.md`
  - backend deterministic tests for stream and provider behavior
- Operational considerations:
  - Requires local `codex` binary and valid `~/.codex/config.toml` for `codex_sdk` mode.

## Metadata

- Change ID: `add-codex-sdk-provider-sse-compat`
- Title: Add Codex SDK provider with SSE compatibility
- Created At (UTC): 2026-03-11T13:34:55Z

## Evolution Run Context

- Latest run index: `tmp/runs/evolution/index.md`
- Latest run report: `tmp/runs/evolution/20260310-175312.md`
