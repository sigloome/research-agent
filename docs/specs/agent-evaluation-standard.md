# Agent Evaluation Standard (Deterministic-First, Flexible-Oracles)

## Overview

This document defines the required standard for all agent evaluations in this repository.
It is the canonical policy for:

1. Designing evals for customized agent/prompt paths.
2. Keeping evals flexible so valid alternative solutions can pass.
3. Minimizing runtime LLM judgment and cost.

This standard is mandatory for all new evals and all updates to existing evals.

## Scope

Customized-agent/custom-prompt paths currently in scope:

| Path ID | Path | Status in main chat flow |
|---|---|---|
| `A1` | `/Users/bytedance/code/anti-demo/backend/agent.py` main system prompt and tool policy | Active |
| `A2` | `/Users/bytedance/code/anti-demo/frontend/src/components/ChatInterface.tsx` local-first injected hint | Active |
| `A3` | `/Users/bytedance/code/anti-demo/skills/preference/sync.py` preference summary mini-agent | Active (background) |
| `A4` | `/Users/bytedance/code/anti-demo/skills/knowledge/summarizer/summarize.py` ingestion summarizer prompt (Codex-native adapter) | Active |
| `A5` | `/Users/bytedance/code/anti-demo/skills/knowledge/rag_critic/critic.py` critic prompt | Implemented, not in default `/api/chat` path |
| `A6` | `/Users/bytedance/code/anti-demo/skills/knowledge/bridge.py` and `/Users/bytedance/code/anti-demo/skills/knowledge/graph_rag/implementation.py` | Partially active |
| `A7` | `/Users/bytedance/code/anti-demo/backend/codex_sdk_runtime.py` and `/Users/bytedance/code/anti-demo/skills/knowledge/paper/core.py` codex-native tool routing + ingest contract | Active |
| `A8` | `/Users/bytedance/code/anti-demo/backend/app.py` skill-event ingest trigger (`knowledge.paper_ingest`) and fallback gate | Active |
| `A9` | `/Users/bytedance/code/anti-demo/backend/multi_agent_runtime.py` and `/Users/bytedance/code/anti-demo/evals/runners/run_suite.py` paper retrieval runtime context + frozen benchmark planning | Active |

Any new path that contains custom prompt behavior must be added to this table before merge.

## Non-Negotiable Requirements

1. Outcome-based grading only.
2. Evals must not require a single fixed tool sequence unless order is correctness-critical.
3. Every eval must support equivalent valid outputs through multi-oracle acceptance.
4. Deterministic checks are the default and must be sufficient for PR and nightly gating.
5. Runtime LLM judges are non-default and allowed only under strict exception rules.
6. Safety, privacy, and protocol invariants are hard gates and never delegated to LLM judges.

## Flexibility Standard (How valid alternatives pass)

Each eval must encode:

1. `required_invariants`: hard constraints that must always hold.
2. `accepted_outcomes`: OR-list of valid solution shapes.
3. `any_allowed_path`: set of tool paths that are all acceptable.
4. `tolerances`: numeric tolerance bands when relevant.

Rules:

1. Avoid exact-string checks except for strict identifiers (IDs, URLs, keys).
2. Prefer slot-based checks and regex/synonym equivalence sets.
3. Separate pass/fail invariants from quality scoring.
4. If deterministic result is borderline, run one additional deterministic trial before failing.
5. If still inconclusive, mark `needs_review` instead of hard-fail.

## Runtime LLM Minimization Policy

1. PR and nightly gates must use deterministic-only grading.
2. Weekly audit may use runtime LLM judges on sampled tasks only.
3. Weekly sample cap: at most 15% of tasks in that run.
4. LLM-judge failures cannot be the sole blocker for merge.
5. Every LLM-judge task must include a deterministic fallback check.
6. Judge model and rubric prompt versions must be pinned per run.

Allowed reasons for runtime LLM judgment:

1. Open-ended synthesis tasks without stable deterministic oracles.
2. Periodic calibration of rubric health on sampled tasks.

Disallowed reasons:

1. Convenience when a deterministic checker can be implemented.
2. Safety/privacy/protocol gating.
3. Tool-trace and DB-state correctness checks.

## Required Test Case Schema

All eval tasks must follow this schema shape:

```json
{
  "id": "RET-01",
  "suite": "retrieval_prompt_paths",
  "path_id": "A1",
  "mode": "single_turn",
  "input": "User prompt text",
  "setup": {
    "db_snapshot": "baseline_v1",
    "fixtures": ["paper_fixture_001"]
  },
  "expect": {
    "required_invariants": [
      "no_hidden_tag_leak",
      "no_private_path_leak"
    ],
    "accepted_outcomes": [
      {
        "tool_path_policy": "any_allowed_path",
        "allowed_first_tools": ["read_paper", "Skill:knowledge.paper.read"],
        "required_slots": {
          "citations_local_min": 1
        }
      }
    ],
    "forbidden_patterns": [
      "<thinking>",
      "<private>",
      "^/(Users|home|var|tmp)/"
    ]
  },
  "grading": {
    "deterministic_metrics": [
      "tool_trace",
      "citation_contract",
      "output_hygiene"
    ],
    "runtime_llm_judge": "off"
  }
}
```

## Mandatory Eval Inventory By Path

### A1 and A2: Main prompt and local-first routing

Required evals:

1. `RET-01` local-first routing.
2. `RET-02` local citation contract (`/paper/{id}`).
3. `RET-03` no-web-overuse on local-only tasks.
4. `RET-04` missing-local fallback behavior.
5. `RET-05` hidden-tag/path leakage prevention.
6. `AGT-08` dynamic prompt wiring regression (`get_system_prompt` behavior).
7. `AGT-24` historical chat continuation behavior:
   - valid persisted provider thread resumes without transcript duplication in the visible answer body
   - invalid persisted provider thread falls back to transcript replay and still returns a continued answer
8. `AGT-25` process-output minimization:
   - final assistant text must not contain explicit process narration markers or hidden-tag leakage
   - tool/process visibility must remain available through structured stream parts

Required deterministic methods:

1. Streamed UI-message chunk parsing for tool traces (`tool-input-*`, `tool-output-*`).
2. Citation URL validation.
3. Output hygiene regex checks.
4. Runtime-state fixture replay for stored-thread resume and replay fallback behavior.

### A3: Preference sync mini-agent

Required evals:

1. `AGT-03` summary format and prefix contract.
2. `AGT-04` no sensitive-string echo.
3. `AGT-09` duplicate-summary suppression behavior.

Required deterministic methods:

1. Sentence-count and prefix contract checks.
2. Denylist checks for secrets/paths/tokens.
3. History dedup assertions.

### A4: Summarizer prompt in ingestion path

Required evals:

1. `RET-06` ingestion-to-retrieval integrity.
2. `AGT-05` strict JSON schema contract.
3. `AGT-06` planted fact-slot recall.
4. `AGT-10` malformed model-output fallback behavior.
5. `AGT-23` Codex summarizer adapter contract:
   - success path returns required keys
   - adapter failure returns deterministic fallback object.

Required deterministic methods:

1. JSON schema validator.
2. Slot extraction checks with synonym lists.
3. DB field presence and non-empty checks.

### A5: RAG critic prompt

Required evals:

1. `RET-08` JSON parse/fallback robustness (mocked LLM output variants).
2. `AGT-11` score-threshold filtering logic in retriever.
3. `AGT-12` deterministic pairwise ranking using a labeled fixture set.

Optional weekly audit:

1. `RET-07` live model polarity check on sampled query/chunk pairs.

Note:
`RET-07` is never a PR/nightly gate.

### A6: Bridge and GraphRAG LLM plumbing

Required evals:

1. `AGT-07` embedding fallback behavior when local model unavailable.
2. `AGT-13` completion error propagation and graceful handling.
3. `AGT-14` query-mode contract (`naive/local/global/hybrid`) and response-shape invariants.

Required deterministic methods:

1. Controlled exception injection.
2. Return-type and error-message contract checks.

### A7: Codex-native tool routing and paper ingest contract

Required evals:

1. `AGT-17` codex-native tool-event mapping contract:
   - `item.started|completed` for native tool/MCP calls must map to UI stream `tool-input-*` / `tool-output-*`.
2. `AGT-18` paper ingest durability contract:
   - success requires local persistence path + required key summary fields in DB.
3. `AGT-19` local retrieval integrity after ingest:
   - ingested paper discoverable through local retrieval path without external fallback.

Required deterministic methods:

1. Fixture replay for codex JSONL native tool events and parser assertions.
2. DB-state assertions for ingest success/failure envelopes.
3. Retrieval assertions on deterministic ingest fixtures.

### A8: Skill-triggered ingest gate in `/api/chat`

Required evals:

1. `AGT-20` skill-triggered ingest extraction:
   - `tool-input-available` with `knowledge.paper_ingest` must extract source and trigger ingest path.
2. `AGT-21` fallback gate default-off:
   - plain text mention of arXiv id must not trigger ingest when fallback env is unset.
3. `AGT-22` explicit fallback override:
   - fallback path only activates when `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true`.

Required deterministic methods:

1. BDD stream fixture tests over `/api/chat` with tool-event/text-only variants.
2. Helper-level unit tests for source extraction and fallback env parsing.

### Supplementary runtime guardrails (repository-required)

These are not custom prompt paths, but they are required for benchmark reliability in this repository.

Required evals:

1. `AGT-15` content-filter streaming edge cases:
   - nested hidden-tag handling
   - unclosed tag handling across chunk boundaries
   - no hidden content or partial-tag leakage in user-visible output
2. `AGT-16` app orchestration robustness:
   - concurrent/default session chat creation safety
   - standardized SSE UI-message stream parsing completeness (`data: { "type": ... }`)
   - persisted assistant response integrity

Required deterministic methods:

1. Deterministic stream-fixture replay with pass/fail invariants.
2. Deterministic DB-state assertions under concurrent request fixtures.

### A9: Paper retrieval runtime context and frozen benchmark planning

Required evals:

1. `PBR-01` active runtime profile honored:
   - active `_run_codex_sdk` path must inject structured retrieval context when `runtime_profile` is provided.
2. `PBR-02` structured retrieval context schema:
   - retrieval context must include `profile`, `intent`, `candidate_papers`, `evidence_items`, and `coverage_audit`.
3. `PBR-03` frozen benchmark signature completeness:
   - blocking paper benchmark tiers must emit `dataset_version`, `dataset_hash`, `snapshot_id`, `seed`, `params_signature`, and `git_commit`.
4. `PBR-04` tier budget gate behavior:
   - `core` and `full` over-budget runs fail; `audit` over-budget runs warn only.
5. `PBR-05` snapshot restore precondition:
   - blocking paper benchmark tiers fail before execution if the configured snapshot is missing.
6. `PBR-06` repeat-run stability calculation:
   - identical-signature runs must report variance for key retrieval metrics.

Required deterministic methods:

1. Runtime contract tests over the active `_run_codex_sdk` path.
2. Deterministic metric tests for paper recall, cluster coverage, comparison facet coverage, support/contradict recall, and repeat-run stability.
3. Runner contract tests for frozen manifest loading, snapshot precondition enforcement, signature construction, and budget policy.

## Required Metrics and Oracles

Each path suite must use deterministic metrics from this set:

1. `tool_trace`
2. `citation_contract`
3. `output_hygiene`
4. `schema_contract`
5. `db_state`
6. `differential_ab`
7. `latency_cost`
8. `content_filter_contract` (for `AGT-15`)
9. `orchestration_contract` (for `AGT-16`)
10. `paper_benchmark_signature`
11. `paper_benchmark_budget`
12. `paper_recall`
13. `cluster_coverage`
14. `comparison_facet_coverage`
15. `support_contradict_recall`
16. `repeat_run_stability`

If adding a new metric:

1. It must document deterministic behavior.
2. It must include at least 3 unit tests with fixture coverage.
3. It must define false-positive and false-negative mitigation notes.

## CI Gate Profiles

1. PR gate:
   - run deterministic only.
   - includes mandatory path tests except optional weekly-audit tests.
   - includes frozen `paper_core` benchmark planning/contract validation.
2. Nightly:
   - deterministic full path suite with `k=3` trials on flaky-prone tasks.
   - includes frozen `paper_full` benchmark planning/contract validation.
3. Weekly audit:
   - sampled runtime LLM judge tasks (<=15%) for open-ended quality monitoring.
   - includes frozen `paper_audit` benchmark planning/contract validation as non-blocking.

## Paper Benchmark Governance (Repository-Required)

Blocking paper benchmark tiers MUST follow these rules:

1. Use versioned frozen datasets only.
2. Restore a fixed snapshot before execution.
3. Emit complete signature metadata.
4. Stay within tier-specific sample/token/latency/timeout budgets.
5. Keep runtime LLM judgment off for PR and nightly blocking tiers.

Tier policy:

1. `paper_core`
   - PR blocking
   - small representative frozen dataset
2. `paper_full`
   - nightly blocking
   - broader frozen dataset
3. `paper_audit`
   - weekly non-blocking
   - high-difficulty frozen dataset with warning-only budget behavior

## Change Control Requirements For Coding Agents

When changing prompts, tool policies, or retrieval behavior, coding agents must:

1. Update this standard if path scope or contracts change.
2. Add or update deterministic evals for every impacted path.
3. Keep backward compatibility for existing accepted outcomes, unless intentionally deprecated.
4. Provide migration notes when an eval contract changes.

When introducing runtime LLM judgment, coding agents must:

1. Add explicit justification in the eval task metadata.
2. Add a deterministic fallback oracle.
3. Mark the task as non-blocking for PR and nightly.

## Compliance Checklist (Required Before Merge)

1. Does the change touch any path in the scope table?
2. Are required invariants encoded separately from quality scoring?
3. Do `accepted_outcomes` allow multiple valid solution forms?
4. Can PR and nightly pass/fail be computed without runtime LLM judgment?
5. Are optional LLM-judge checks capped and non-blocking?
6. Are safety/privacy/protocol checks deterministic and hard-gated?
