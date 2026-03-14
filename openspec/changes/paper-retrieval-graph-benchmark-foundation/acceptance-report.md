# Acceptance Report

Date: 2026-03-14
Change: `paper-retrieval-graph-benchmark-foundation`

## Scope Completed

This change delivered the paper retrieval foundation in four layers:

1. Active runtime profile wiring
- `backend/agent.py` now honors `runtime_profile` in the active `_run_codex_sdk` path.
- retrieval context is injected before answer synthesis rather than being ignored in the live path.
- runtime profile semantics now use:
  - `baseline`
  - `hybrid`
  - `graph_expand`
  - `graph_verify`
- legacy aliases (`graph`, `graph_critic`, related historical names) remain supported through parser compatibility.

2. Structured retrieval runtime output
- `backend/multi_agent_runtime.py` now emits structured retrieval payloads and serialized `[RetrievalContext]` output.
- retrieval payloads include:
  - `intent`
  - `candidate_papers`
  - `evidence_items`
  - `coverage_audit`
- baseline/comparison/cross-validation flows now expose evidence fields suitable for deterministic scoring.

3. Frozen paper benchmark governance and execution entrypoints
- `evals/datasets/paper_benchmark/` now contains curated frozen `core/full/audit` datasets.
- `evals/datasets/paper_benchmark/manifest_v1.json` now contains real dataset hashes and sample counts.
- `evals/fixtures/paper_benchmark/snapshots/papers_snapshot_v1.sqlite` is a real SQLite snapshot instead of a placeholder artifact.
- `evals/runners/run_suite.py` now supports:
  - `paper_core`
  - `paper_full`
  - `paper_audit`
- runner validates:
  - dataset existence
  - dataset hash
  - sample count
  - blocking snapshot precondition
  - snapshot contains referenced paper IDs
  - curated benchmark snapshot can be regenerated from source DB with `scripts/build_paper_benchmark_snapshot.py`
 - runner now also executes end-to-end paper benchmark suites against `MultiAgentRuntime` using the frozen snapshot as the retrieval source and emits case-level plus aggregate deterministic scores.

4. Repository policy sync and CI contract
- `docs/specs/agent-evaluation-standard.md` updated with paper benchmark path inventory, deterministic metrics, and tier policy.
- `docs/specs/auto-evolving-backend.md` updated with rollout and budget semantics.
- `.github/workflows/deterministic-agent-checks.yml` updated to validate paper benchmark planning on PR/push and scheduled runs.

5. Gold scoring and grounding enrichment
- `evals/metrics/paper_benchmark.py` now scores:
  - paper recall
  - cluster coverage
  - structured evidence facet coverage
  - support / contradict recall
  - repeat-run stability
  - span-level grounding recall over expected evidence references
  - semantic span equivalence for same-paper adjacent spans when structured evidence fields align

## Deterministic Verification Evidence

### Targeted foundation tests

Command:

```bash
python3 -m pytest -q \
  tests/backend/test_paper_retrieval_runtime.py \
  tests/backend/test_multi_agent_runtime.py \
  tests/backend/test_multi_agent_runtime_structured.py \
  tests/evals/test_paper_benchmark_contracts.py \
  tests/evals/test_paper_benchmark_runner.py \
  tests/evals/test_paper_benchmark_evidence.py \
  tests/evals/test_paper_benchmark_gold_scoring.py \
  tests/scripts/test_build_paper_benchmark_snapshot.py
```

Result:
- pass

### Existing retrieval deterministic suite

Command:

```bash
python3 -m pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py
```

Result:
- pass

### Runner CLI verification

Commands:

```bash
python3 -m evals.runners.run_suite --suite paper_core --params-signature graph_expand --git-commit testsha
python3 -m evals.runners.run_suite --suite paper_full --params-signature baseline --git-commit testsha
python3 -m evals.runners.run_suite --suite paper_audit --params-signature baseline --git-commit testsha
```

Result:
- all pass and emit aggregate deterministic scores from real runtime execution

## Delivered Files

### Runtime
- `/Users/bytedance/code/anti-demo/backend/agent.py`
- `/Users/bytedance/code/anti-demo/backend/multi_agent_runtime.py`

### Benchmark metrics / runner
- `/Users/bytedance/code/anti-demo/evals/metrics/paper_benchmark.py`
- `/Users/bytedance/code/anti-demo/evals/runners/run_suite.py`

### Frozen datasets / snapshot
- `/Users/bytedance/code/anti-demo/evals/datasets/paper_benchmark/core_v1.jsonl`
- `/Users/bytedance/code/anti-demo/evals/datasets/paper_benchmark/full_v1.jsonl`
- `/Users/bytedance/code/anti-demo/evals/datasets/paper_benchmark/audit_v1.jsonl`
- `/Users/bytedance/code/anti-demo/evals/datasets/paper_benchmark/manifest_v1.json`
- `/Users/bytedance/code/anti-demo/evals/fixtures/paper_benchmark/snapshots/papers_snapshot_v1.sqlite`
- `/Users/bytedance/code/anti-demo/scripts/build_paper_benchmark_snapshot.py`

### Tests
- `/Users/bytedance/code/anti-demo/tests/backend/test_paper_retrieval_runtime.py`
- `/Users/bytedance/code/anti-demo/tests/backend/test_multi_agent_runtime_structured.py`
- `/Users/bytedance/code/anti-demo/tests/evals/test_paper_benchmark_contracts.py`
- `/Users/bytedance/code/anti-demo/tests/evals/test_paper_benchmark_runner.py`
- `/Users/bytedance/code/anti-demo/tests/evals/test_paper_benchmark_evidence.py`
- `/Users/bytedance/code/anti-demo/tests/evals/test_paper_benchmark_gold_scoring.py`
- `/Users/bytedance/code/anti-demo/tests/scripts/test_build_paper_benchmark_snapshot.py`

### Policy / CI
- `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`
- `/Users/bytedance/code/anti-demo/docs/specs/auto-evolving-backend.md`
- `/Users/bytedance/code/anti-demo/.github/workflows/deterministic-agent-checks.yml`

## Remaining Limitations

1. The snapshot is curated for benchmark determinism and coverage; it is not yet automatically refreshed from the full production paper DB.
2. Graph-based retrieval itself is still a foundation implementation and not yet a fully tuned production retrieval system.

## Rollout Recommendation

- Keep `paper_core` as blocking planning/contract validation immediately.
- Keep `paper_core` blocking; `paper_full` and `paper_audit` can now run with real runtime benchmark execution over frozen snapshot outputs.
- Use the snapshot builder script to regenerate the frozen benchmark snapshot whenever curated paper benchmark datasets change.
