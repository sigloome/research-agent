# Acceptance Report

Date: 2026-03-14
Change: `paper-retrieval-quality-upgrades`

## Scope Implemented

This pass implemented the planned quality-upgrade contracts:

1. `hybrid` profile parity
- `hybrid` is now benchmark-addressable in `manifest_v1.json`.
- `hybrid` retrieval now executes a separate semantic recall path and fuses candidates with lexical recall.

2. cluster-aware `graph_expand`
- `graph_expand` now merges cluster-bearing related-work candidates and preserves cluster-oriented `match_reasons`.
- candidate merge now preserves combined reasons instead of discarding graph expansion reasons on duplicate papers.

3. evidence-item `graph_verify`
- `graph_verify` now feeds structured evidence items into critic/rerank flow rather than relying only on free-form chunk text.
- reranked evidence items are preserved as structured `evidence_items` in retrieval context.

4. xval counter-evidence retrieval
- cross-validation retrieval now adds a counter-evidence probe path.
- coverage audit distinguishes whether counter-evidence search was checked.

## Deterministic Verification

### Test suites

Command:

```bash
python3 -m pytest -q \
  tests/backend/test_multi_agent_runtime.py \
  tests/backend/test_paper_retrieval_runtime.py \
  tests/backend/test_codex_sdk_runtime.py \
  tests/backend/test_multi_agent_runtime_structured.py \
  tests/evals/test_paper_benchmark_contracts.py \
  tests/evals/test_paper_benchmark_evidence.py \
  tests/evals/test_paper_benchmark_gold_scoring.py \
  tests/evals/test_paper_benchmark_runner.py \
  evals/tests/test_retrieval_prompt_paths.py \
  evals/tests/test_retrieval_prompt_paths_audit.py
```

Result:
- `64 passed`

### Paper core profile comparison

Command:

```bash
python3 -m evals.runners.run_suite --suite paper_core --params-signature baseline --git-commit testsha
python3 -m evals.runners.run_suite --suite paper_core --params-signature hybrid --git-commit testsha
python3 -m evals.runners.run_suite --suite paper_core --params-signature graph_expand --git-commit testsha
python3 -m evals.runners.run_suite --suite paper_core --params-signature graph_verify --git-commit testsha
```

Observed aggregate results:

- `baseline`
  - `paper_recall = 0.75`
  - `cluster_coverage = 0.75`
  - `support_recall = 0.1667`
  - `contradict_recall = 0.0`
  - `balanced_evidence_rate = 0.0`
- `hybrid`
  - `paper_recall = 0.8333`
  - `cluster_coverage = 1.0`
  - `support_recall = 1.0`
  - `contradict_recall = 1.0`
  - `balanced_evidence_rate = 1.0`
- `graph_expand`
  - `paper_recall = 0.8333`
  - `cluster_coverage = 1.0`
  - `support_recall = 1.0`
  - `contradict_recall = 1.0`
  - `balanced_evidence_rate = 1.0`
- `graph_verify`
  - `paper_recall = 0.8333`
  - `cluster_coverage = 1.0`
  - `support_recall = 1.0`
  - `contradict_recall = 1.0`
  - `balanced_evidence_rate = 1.0`

## Outcome Assessment

Implementation contracts are complete and the proposed success metrics are now met on the frozen `paper_core` benchmark.

Met:
- `hybrid.paper_recall > baseline.paper_recall`
- `graph_expand.cluster_coverage >= 0.60`
- `graph_verify.support_recall >= 0.50`
- `graph_verify.contradict_recall >= 0.50`
- `graph_verify.balanced_evidence_rate >= 0.50`
- runtime and benchmark parity contracts are implemented
- deterministic verification remains green
- `graph_verify` token growth remains within the intended budget envelope relative to `graph_expand`

## Rollout Recommendation

- `hybrid` is now a meaningful quality upgrade over `baseline` for the frozen benchmark and can be treated as the new default benchmark comparison point.
- `graph_expand` and `graph_verify` now satisfy the frozen benchmark thresholds for completeness-sensitive paper tasks.
- Continue to keep rollout conservative for live traffic until the same behavior is verified on a larger non-curated slice.

## Recommended Next Optimization Loop

1. verify the same quality deltas on `paper_full` and a larger production-derived snapshot
2. make `graph_verify` produce a measurable gain over `graph_expand`, not only parity
3. tune token growth for `hybrid` and `graph_expand` while preserving recall
4. consider citation-neighbor retrieval as the next higher-leverage quality upgrade
