## Context

Active runtime is fixed to `codex_sdk` in `/api/chat`, but skill/tool execution guarantees are currently split between:
- inactive bridge-only custom tool loop (`_run_codex_bridge`), and
- active codex-sdk path that does not emit complete tool timeline events.

Paper ingestion logic exists (`analyze_paper`) and DB schema already stores local path + summary fields, but there is no codex-native ingest contract that the agent can deterministically invoke for retrieval-oriented workflows.

Constraints:
- Keep single-provider strategy (`codex_sdk`) and avoid reintroducing multi-provider complexity.
- Preserve frontend stream compatibility (`x-vercel-ai-ui-message-stream: v1`).
- Follow deterministic-first gating and non-blocking runtime-LLM judgment policy.

Stakeholders:
- Runtime owners (backend/agent)
- Knowledge owners (skills/knowledge)
- Eval/governance owners (deterministic gates, OpenSpec policy docs)

## Goals / Non-Goals

**Goals:**
- Enforce codex-native skill routing in active runtime path.
- Map codex-native tool events to existing SSE tool timeline events.
- Provide a codex-native paper ingest contract that guarantees:
  - local persistence,
  - key-info extraction,
  - DB upsert for retrieval.
- Add deterministic tests/evals for routing, event contract, and ingest-retrieval integrity.
- Provide safe rollout with explicit rollback toggles and kill criteria.

**Non-Goals:**
- Re-enable legacy bridge provider as primary path.
- Redesign frontend chat UI or protocol shape.
- Replace existing GraphRAG implementation.
- Introduce broad schema migrations unrelated to ingest contract.

## Decisions

1. Decision: keep `codex_sdk` as the only runtime provider and remove bridge-only skill dependency from active path.
- Rationale: aligns with current single-provider architecture and reduces hidden divergence.
- Alternative considered: route skill-required prompts back to `_run_codex_bridge`.
- Rejected because it reintroduces dual-path behavior and inconsistent observability.

2. Decision: use codex-native tool/MCP events as the source of truth for skill execution telemetry.
- Rationale: matches SDK/CLI-native capabilities and avoids synthetic post-hoc tool traces.
- Alternative considered: infer tool execution from model text.
- Rejected because inference is brittle and not deterministic.

3. Decision: define explicit `knowledge.paper_ingest` contract instead of ad-hoc combinations (`fetch` then `analyze`).
- Rationale: single deterministic operation is easier to test, retry, and monitor.
- Alternative considered: keep current fragmented calls.
- Rejected because it cannot guarantee complete ingest state for retrieval.

4. Decision: retain existing `papers` table as canonical summary store, and add deterministic completeness checks rather than immediate broad DB refactor.
- Rationale: minimal migration risk and fastest path to enforceable contract.
- Alternative considered: large new normalized schema (`paper_chunks`, `paper_facts`, etc.) in same change.
- Rejected for scope and rollout risk; can follow in later change if needed.

5. Decision: gate with deterministic fixtures; runtime-LLM checks remain non-blocking.
- Rationale: required by repository evaluation standard and CI policy.

## Risks / Trade-offs

- [Risk] codex-native tool events differ across environments and may miss expected fields.
  - Mitigation: robust parser with fallback-safe envelopes and deterministic fixture coverage for variant event shapes.

- [Risk] ingest failures (network/parser) reduce retrieval quality.
  - Mitigation: explicit ingest status, retry policy, and failure telemetry; fail-fast when persistence or key field extraction is incomplete.

- [Risk] rollout increases error finishes in `/api/chat`.
  - Mitigation: feature flags, canary-style enablement, and immediate rollback thresholds.

- [Risk] legacy scripts/tests reference outdated modules.
  - Mitigation: fix stale paths and add deterministic smoke checks for batch ingest utilities.

## Migration Plan

1. Add feature flags:
- `ENABLE_CODEX_NATIVE_SKILL_ROUTING`
- `ENABLE_PAPER_INGEST_CONTRACT`

2. Implement runtime changes behind flags:
- codex-sdk event mapping for tool timeline
- codex-native skill invocation path

3. Implement ingest contract and deterministic validation:
- enforce local path + key fields presence before successful completion

4. Expand deterministic tests and eval fixtures:
- runtime stream contract
- skill routing contract
- ingest/retrieval integrity

5. Rollout sequence:
- sandbox -> shadow -> canary -> full
- monitor success/risk metrics per stage

6. Rollback strategy:
- disable feature flags,
- revert runtime mapping commit if stream contract breaks,
- rerun deterministic suite to confirm recovery.

## Open Questions

1. Should retrieval integrity in this change use SQL `LIKE` + deterministic fixtures only, or include FTS5 introduction now?
2. Is `knowledge.paper_ingest` exposed as one tool action with `mode` parameter, or split actions (`ingest`, `extract`, `upsert`) with orchestrated policy?
3. For withdrawn/failed papers, should contract return partial success or strict failure for deterministic gate purposes?
