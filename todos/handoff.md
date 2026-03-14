# Session Handoff

Date: 2026-03-14

## Completed in this session

1. Closed `paper-retrieval-graph-benchmark-foundation` implementation loop:
   - active `_run_codex_sdk` path honors `runtime_profile`
   - runtime profiles standardized to `baseline / hybrid / graph_expand / graph_verify`
   - `graph_expand` now adds classic baseline / recent follow-up coverage for related-work retrieval
2. Upgraded paper benchmark execution from plan-only to end-to-end deterministic runtime scoring:
   - `evals/runners/run_suite.py`
   - `paper_core / paper_full / paper_audit` now execute `MultiAgentRuntime` against frozen snapshot-backed retrieval
   - output includes case-level retrieval context and aggregate recall/coverage/grounding metrics
3. Upgraded span grounding beyond exact ref equality:
   - `evals/metrics/paper_benchmark.py`
   - now accepts same-paper semantic span equivalence when structured evidence fields overlap
4. Added deterministic tests for the new behavior:
   - `tests/backend/test_multi_agent_runtime_structured.py`
   - `tests/evals/test_paper_benchmark_gold_scoring.py`
   - `tests/evals/test_paper_benchmark_runner.py`
5. Synced tracked artifacts and local continuity files:
   - `openspec/changes/paper-retrieval-graph-benchmark-foundation/tasks.md`
   - `openspec/changes/paper-retrieval-graph-benchmark-foundation/acceptance-report.md`
   - `todos/active.md`
   - `todos/done.md`

## Current state

- The foundation change is implemented and verified.
- `paper_core` can now run as a real frozen end-to-end benchmark in the local minimal environment.
- Deterministic verification summary:
  - `58 passed` across runtime + benchmark + existing retrieval suites
  - `python3 -m evals.runners.run_suite --suite paper_core --params-signature graph_expand --git-commit testsha` passed
- New follow-up change scaffolded for the next phase:
  - `/Users/bytedance/code/anti-demo/openspec/changes/paper-retrieval-quality-upgrades/`
  - scope: real `hybrid`, cluster-aware `graph_expand`, evidence-item `graph_verify`, xval counter-evidence retrieval, benchmark profile parity
- First implementation pass for `paper-retrieval-quality-upgrades` is now complete:
  - contracts and deterministic tests pass
  - acceptance recorded in `/Users/bytedance/code/anti-demo/openspec/changes/paper-retrieval-quality-upgrades/acceptance-report.md`
  - quality targets are now met on frozen `paper_core`

## Immediate next task

1. Optional next loop:
   - verify the same uplifts on `paper_full` and a larger production-derived snapshot
   - tune token growth while preserving the new recall/coverage gains
   - make `graph_verify` produce measurable gains over `graph_expand`, not just parity

## Notes

- `openspec` CLI is not installed in this environment, so status/apply steps were validated through tracked artifacts directly rather than the CLI.
- The current paper benchmark snapshot is curated and deterministic; it is not auto-refreshed from the full paper DB unless `scripts/build_paper_benchmark_snapshot.py` is run.
