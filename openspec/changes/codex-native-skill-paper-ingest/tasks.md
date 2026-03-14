## 1. SDD (Spec-Driven Definition)

- [x] 1.1 Validate proposal/design/spec deltas with `openspec` checks and resolve wording mismatches.
- [x] 1.2 Align capability boundaries with existing main specs (`chat-interface`, `skills-system`, `paper-management`) and confirm no missing delta capability.
- [x] 1.3 Update rollout metric definitions and kill criteria mapping in change artifacts if thresholds are ambiguous.

## 2. BDD (Behavior-Driven Scenarios)

- [x] 2.1 Add executable BDD scenarios for codex-native skill routing in active `/api/chat` flow.
- [x] 2.2 Add executable BDD scenarios for skill/tool event timeline contract (`tool-input-*`, `tool-output-*`, `finish`, `[DONE]`).
- [x] 2.3 Add executable BDD scenarios for paper ingest contract success/failure paths (durable local path + key-info DB upsert).

## 3. TDD (Deterministic Test First)

- [x] 3.1 Add failing deterministic unit tests for codex-sdk event mapping of native tool/MCP events.
- [x] 3.2 Add failing deterministic tests for `knowledge.paper_ingest` output schema and failure envelope.
- [x] 3.3 Add failing deterministic retrieval integrity tests (ingested paper retrievable by local query path).
- [x] 3.4 Add deterministic regression test for `scripts/process_all_papers.py` import/runtime path.

## 4. Implementation

- [x] 4.1 Implement codex-native skill routing in active runtime path in `backend/agent.py` (no bridge-only dependency for normal flow).
- [x] 4.2 Implement tool/MCP event -> UI stream mapping in `backend/codex_sdk_runtime.py`.
- [x] 4.3 Update Node adapter if required to preserve event fields needed for tool timeline mapping in `backend/codex_sdk_adapter/run_stream.mjs`.
- [x] 4.4 Implement `knowledge.paper_ingest` contract in `skills/knowledge/paper/core.py` and required DB manager support.
- [x] 4.5 Ensure ingest success is conditional on durable local path + key summary fields persisted in DB.
- [x] 4.6 Fix stale batch script import path and contract in `scripts/process_all_papers.py`.

## 5. Deterministic Verification and Governance Sync

- [x] 5.1 Run deterministic test suites for backend, evals, and skill/paper contracts; archive command outputs in run logs.
- [x] 5.2 Update `docs/specs/agent-evaluation-standard.md` path coverage and required eval inventory for codex-native skill routing path.
- [x] 5.3 Update `docs/specs/auto-evolving-backend.md` with this feature’s rationale, numeric success metrics, and rollback/kill criteria references.
- [x] 5.4 Execute rollout simulation steps (sandbox -> shadow -> canary) and document rollback evidence in acceptance report.
- [x] 5.5 Sync local notes/todos into tracked OpenSpec artifacts before merge.
