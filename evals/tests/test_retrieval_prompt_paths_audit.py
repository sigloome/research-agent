"""Weekly audit-only tests: RET-07 plus sampled AGT-03 live-judge slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.metrics.retriever_contract import evaluate_ret07_ordering_agreement
from evals.runners.run_suite import build_weekly_audit_plan, run_suite
from evals.runners.task_loader import load_tasks

EVALS_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = EVALS_ROOT / "datasets" / "retrieval_prompt_paths.jsonl"
KNOWLEDGE_FIXTURES = EVALS_ROOT / "fixtures" / "knowledge"
LLM_MOCKS = EVALS_ROOT / "fixtures" / "llm_mocks"


def test_ret_07_weekly_threshold():
    rag_critic = json.loads((LLM_MOCKS / "rag_critic_outputs.json").read_text(encoding="utf-8"))
    result = evaluate_ret07_ordering_agreement(rag_critic["RET-07"]["labeled_pairs"])
    assert result["ordering_agreement"] >= 0.8


def test_agt_03_weekly_live_sample_target():
    fixture = json.loads((KNOWLEDGE_FIXTURES / "agt03_agt04_fixtures.json").read_text(encoding="utf-8"))
    scores = fixture["AGT-03"]["weekly_live_scores"]
    pass_rate = sum(1 for score in scores if float(score) >= 0.8) / len(scores)
    assert pass_rate >= 0.8


def test_weekly_runner_enforces_judge_rate_cap_and_sampling():
    tasks = load_tasks(DATASET_PATH)
    plan = build_weekly_audit_plan(tasks, judge_rate=0.15)

    assert set(plan["runtime_judge_task_ids"]) == {"RET-07", "AGT-03"}
    assert plan["observed_judge_rate"] <= 0.15

    summary = run_suite("weekly_audit", DATASET_PATH, judge_rate=0.15)
    assert summary["runtime_judge_task_count"] == 2


def test_weekly_runner_rejects_invalid_judge_rate():
    tasks = load_tasks(DATASET_PATH)
    with pytest.raises(ValueError, match="judge_rate"):
        build_weekly_audit_plan(tasks, judge_rate=0.16)
