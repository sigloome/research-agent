## Acceptance Report: codex-native-skill-paper-ingest

### Summary

Implemented codex-native skill/tool observability in active `codex_sdk` path, added paper ingest durability contract, fixed batch ingest script import path, and synced governance docs for deterministic-first evaluation and rollback policy.

### Verification Evidence

1. Targeted backend/skill/script/BDD tests:
- Command:
  - `pytest -q tests/backend/test_codex_sdk_runtime.py tests/skills/paper/test_ingest_contract.py tests/scripts/test_process_all_papers_script.py tests/backend/test_bdd_paper_ingest_flow.py tests/backend/test_bdd_chat_flow.py`
- Result:
  - `11 passed`

2. Deterministic eval suite:
- Command:
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`
- Result:
  - `31 passed`

3. OpenSpec change status:
- Command:
  - `openspec status --change codex-native-skill-paper-ingest`
- Result:
  - `4/4 artifacts complete`

4. OpenSpec validation:
- Command:
  - `openspec validate --changes codex-native-skill-paper-ingest`
- Result:
  - this change passes; repository has unrelated pre-existing failed changes (`_templates`, `runtime-simplify-and-stability-hardening`, `support-multi-chat`).

### Rollout Simulation / Rollback Evidence

1. Promotion workflow simulation:
- Command:
  - `scripts/promotion_workflow.sh`
- Output:
  - `tmp/runs/evolution/promotion/20260312-105525.md`
- Warning count:
  - `0`

2. Rollback templates documented in promotion report:
- disable runtime profile routing
- rollback trace/runtime mapping commit
- re-run deterministic cycle with `scripts/run_evolution_cycle.sh`

### Task Completion Notes

- Codex-native tool event mapping implemented in runtime parser.
- `knowledge.paper_ingest` contract added with strict success criteria (local path + key fields).
- Batch paper processing script import path corrected to current module structure.
- Governance docs updated:
  - `docs/specs/agent-evaluation-standard.md`
  - `docs/specs/auto-evolving-backend.md`

