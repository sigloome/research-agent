## Why

The current chat stream mixes custom `0:`/`d:` lines with ad-hoc parsing in both backend and frontend, which blocks clean interoperability with Vercel Data Stream Protocol tooling (`useChat`) and causes brittle streaming/error handling behavior. We need a standards-aligned stream contract and a UI architecture that can reliably support tool progress, stop/retry/edit, persistence, and accessible live updates.

## What Changes

- **BREAKING**: Replace `/api/chat` response wire format with SSE (`text/event-stream`) using the Vercel UI message stream contract and response header `x-vercel-ai-ui-message-stream: v1`.
- Remove legacy mixed stream parsing paths (`0:`, `d:`, custom `data:` fallbacks) from backend accumulation and frontend rendering logic.
- Migrate chat UI from manual stream parsing to `useChat`, including:
  - status-driven controls (`stop`, retry/regenerate, edit+resend),
  - tool-progress timeline rendering from streamed parts,
  - improved error/reconnect states,
  - persisted chat loading continuity,
  - accessible live chat log behavior,
  - smoother throttled streaming updates.
- Update deterministic eval/spec contracts for orchestration and stream parsing so AGT-16 validates the standardized stream format.

## Expected Benefit

1. Improve interoperability with Vercel AI SDK message-stream tooling and reduce custom parser fragility.
2. Improve UX reliability for stop/retry/edit flows and tool-progress rendering.
3. Reduce long-term maintenance cost by aligning backend/frontend stream protocol to a standardized contract.

## Success Metrics

1. AGT-16 deterministic orchestration contract pass rate: `100%` in PR/nightly suites.
2. Streaming parse/runtime errors on `/api/chat`: reduce by `>= 80%` vs pre-change baseline over 14 days.
3. Retry/stop/edit interaction success rate in e2e chat tests: `>= 99%`.
4. UI stream rendering regressions from chunk-format mismatch: `0` in regression suite.

## Risk Metrics

1. Any contract mismatch with `x-vercel-ai-ui-message-stream: v1` in staging triggers rollback.
2. Chat response completion failure rate increase above `+0.5%` absolute triggers rollback.
3. Tool-progress rendering missing-event rate above `0.2%` in monitored sessions triggers rollback.

## Kill Criteria

1. If standards-aligned streaming does not reduce parsing fragility and error rates within one release cycle.
2. If the standardized protocol imposes unresolved compatibility constraints that materially degrade core chat workflows.

## Capabilities

### New Capabilities
- _None._

### Modified Capabilities
- `chat-interface`: Stream protocol contract, UI streaming behavior, tool progress rendering, and retry/stop/error accessibility behavior are updated to align with Vercel UI message stream expectations.

## Impact

- Backend: `/Users/bytedance/code/anti-demo/backend/app.py`, `/Users/bytedance/code/anti-demo/backend/agent.py`
- Frontend: `/Users/bytedance/code/anti-demo/frontend/src/components/ChatInterface.tsx` (and any small supporting component changes)
- Specs/evals policy: `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`
- Deterministic evals: `/Users/bytedance/code/anti-demo/evals/adapters/stream_parser.py`, `/Users/bytedance/code/anti-demo/evals/fixtures/knowledge/agt16_orchestration_fixture.json`, `/Users/bytedance/code/anti-demo/evals/tests/test_retrieval_prompt_paths.py`

## Local Run Logs

- Retention index: tmp/runs/evolution/index.md

## Run Log Sync

- Synced evolution report: `/Users/bytedance/code/anti-demo/tmp/runs/evolution/20260310-165800.md`
