## Why

Current `/api/chat` runtime is single-provider `codex_sdk`, but skill usage is still not enforced through Codex native tool capabilities in the active path. At the same time, paper ingestion and key-info persistence exist but are not exposed as a codex-native skill contract with deterministic retrieval guarantees.

We need one coherent path now: Codex built-in skill/tool invocation for knowledge workflows, plus mandatory paper ingest (local persistence + key info DB upsert) so later retrieval is reliable and observable.

## What Changes

- Introduce codex-native skill routing as a first-class runtime contract in active chat path.
- Extend codex SDK event mapping to emit tool timeline events (`tool-input-*`, `tool-output-*`) from codex-native tool/MCP call events.
- Add a codex-native `knowledge.paper_ingest` contract that performs:
  - remote/local paper acquisition,
  - local content persistence,
  - key information extraction,
  - database upsert for retrieval.
- Enforce deterministic-first verification for skill routing and ingest/retrieval integrity.
- Add rollout guardrails with explicit rollback/kill criteria.

Out of scope:

- No multi-provider runtime restoration.
- No UI redesign beyond existing SSE event contract compatibility.
- No replacement of existing GraphRAG architecture in this change.

## Expected Benefit

1. User impact:
   - Skill-dependent requests consistently execute through codex-native capabilities in active `/api/chat` flow.
   - Paper knowledge remains retrievable across sessions because local artifacts and structured DB records are guaranteed.
2. Engineering quality/stability impact:
   - Tool execution is observable in stream events and testable by deterministic fixtures.
   - Fewer hidden path divergences between prompt policy and actual runtime behavior.
3. Cost/performance/operability impact:
   - Less fallback to broad web search for tasks that should be solved by local/project knowledge.

## Success Metrics

1. `codex_native_skill_invocation_rate >= 95%`
   - Scope: prompts requiring skill routing in deterministic fixture suite + live smoke sample.
2. `paper_ingest_success_rate >= 98%`
   - Definition: ingest requests complete local persistence + key fields DB upsert.
3. `paper_key_info_schema_pass_rate >= 99%`
   - Definition: extracted key fields satisfy deterministic schema checks.
4. `local_retrieval_hit_at_5 >= 85%`
   - Scope: deterministic retrieval fixture set for ingested papers.

## Risk Metrics

1. `/api/chat` `tool_event_contract_error_rate > 1%` in validation window.
2. `paper_ingest_failure_rate > 2%` over last 100 ingest attempts.
3. `assistant_error_finish_rate` rises by `> 2%` versus baseline after rollout.

## Kill Criteria

1. If deterministic skill-routing contract tests fail in 2 consecutive runs, stop rollout and rollback.
2. If ingest failure rate exceeds 2% for 2 consecutive windows, disable `paper_ingest` path and revert to previous stable behavior.
3. If stream tool-event contract regression breaks frontend parsing, immediately rollback runtime mapping changes.

## Capabilities

### New Capabilities

- `codex-native-skill-routing`: Runtime-enforced codex-native skill/tool invocation contract with observable stream events.
- `paper-ingest-retrieval-contract`: Codex-native paper ingest contract requiring local persistence and structured key-info DB storage for retrieval.

### Modified Capabilities

- `chat-interface`: Stream contract updated to include codex-native skill/tool event visibility in active runtime.
- `skills-system`: Skill execution requirements updated to codex-native runtime integration expectations.
- `paper-management`: Paper processing requirements updated to require local persistence + key-info extraction contract for retrievability.

## Impact

- Affected code:
  - `backend/agent.py`
  - `backend/codex_sdk_runtime.py`
  - `backend/codex_sdk_adapter/run_stream.mjs`
  - `skills/knowledge/paper/core.py`
  - `skills/knowledge/db/manager.py`
  - `scripts/process_all_papers.py`
- Affected tests/evals:
  - deterministic retrieval/skill-routing suites under `evals/tests/`
  - backend runtime stream tests under `tests/backend/`
  - skill/paper contract tests under `tests/skills/`
- Operational dependencies:
  - codex runtime configuration (`~/.codex/config.toml`)
  - local database (`data/papers.db`)

## Metadata

- Change ID: `codex-native-skill-paper-ingest`
- Title: Codex-native skill routing with paper ingest and retrieval contract
- Created At (UTC): 2026-03-11T17:31:00Z

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/20260310-175312.md`
