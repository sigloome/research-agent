# Evals

Deterministic-first eval scaffolding for retrieval/custom-prompt paths.

## Layout

- `datasets/retrieval_prompt_paths.jsonl`: required tasks (`RET-01..08`, `AGT-01..16`).
- `fixtures/knowledge/`: deterministic knowledge/state fixtures.
- `fixtures/llm_mocks/`: mocked LLM outputs for critic/summarizer/bridge contracts.
- `metrics/`: deterministic contract check modules.
- `adapters/`: stream parsing and trace mapping adapters.
- `runners/`: suite guardrails and run-profile selection.
- `tests/`: deterministic gate tests and weekly-audit tests.

## Run Commands

PR deterministic gate:

```bash
python -m evals.runners.run_suite --suite pr --judge-rate 0.15 --k 1
pytest -q evals/tests/test_retrieval_prompt_paths.py
```

Nightly deterministic gate:

```bash
python -m evals.runners.run_suite --suite nightly --judge-rate 0.15 --k 3
pytest -q evals/tests/test_retrieval_prompt_paths.py
```

Weekly audit slice:

```bash
python -m evals.runners.run_suite --suite weekly_audit --judge-rate 0.15 --k 1
pytest -q evals/tests/test_retrieval_prompt_paths_audit.py
```

## Deterministic vs Audit-Only

Deterministic gate set (PR/nightly):

- `RET-01..06`, `RET-08`
- `AGT-01..16` (`AGT-03` mocked deterministic)

Weekly audit-only runtime-judge slice:

- `RET-07`
- sampled `AGT-03` live-quality check

## Guardrails

- PR/nightly runners fail if any selected task has `runtime_llm_judge != "off"`.
- Weekly audit runner enforces `judge_rate <= 0.15` (configured and observed).
- `AGT-12` remains deterministic mocked-only.
