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
| `A4` | `/Users/bytedance/code/anti-demo/skills/knowledge/summarizer/summarize.py` ingestion summarizer prompt | Active |
| `A5` | `/Users/bytedance/code/anti-demo/skills/knowledge/rag_critic/critic.py` critic prompt | Implemented, not in default `/api/chat` path |
| `A6` | `/Users/bytedance/code/anti-demo/skills/knowledge/bridge.py` and `/Users/bytedance/code/anti-demo/skills/knowledge/graph_rag/implementation.py` | Partially active |

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

Required deterministic methods:

1. Stream `d:` tool-trace parsing.
2. Citation URL validation.
3. Output hygiene regex checks.

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

### Supplementary runtime guardrails (repository-required)

These are not custom prompt paths, but they are required for benchmark reliability in this repository.

Required evals:

1. `AGT-15` content-filter streaming edge cases:
   - nested hidden-tag handling
   - unclosed tag handling across chunk boundaries
   - no hidden content or partial-tag leakage in user-visible output
2. `AGT-16` app orchestration robustness:
   - concurrent/default session chat creation safety
   - mixed stream format parsing (`0:`, `data:`, `d:`) completeness
   - persisted assistant response integrity

Required deterministic methods:

1. Deterministic stream-fixture replay with pass/fail invariants.
2. Deterministic DB-state assertions under concurrent request fixtures.

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

If adding a new metric:

1. It must document deterministic behavior.
2. It must include at least 3 unit tests with fixture coverage.
3. It must define false-positive and false-negative mitigation notes.

## CI Gate Profiles

1. PR gate:
   - run deterministic only.
   - includes mandatory path tests except optional weekly-audit tests.
2. Nightly:
   - deterministic full path suite with `k=3` trials on flaky-prone tasks.
3. Weekly audit:
   - sampled runtime LLM judge tasks (<=15%) for open-ended quality monitoring.

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
