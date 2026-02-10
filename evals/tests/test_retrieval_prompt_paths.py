"""Deterministic gate tests for retrieval/custom-prompt path evaluations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.metrics.bridge_contract import evaluate_agt07, evaluate_agt13, evaluate_agt14
from evals.metrics.citation import evaluate_ret_02
from evals.metrics.content_filter_contract import evaluate_agt15
from evals.metrics.db_state import evaluate_agt06, evaluate_agt09, evaluate_agt16_db, evaluate_ret06
from evals.metrics.differential import evaluate_agt02, evaluate_agt08
from evals.metrics.orchestration_contract import evaluate_agt16_orchestration
from evals.metrics.output_hygiene import evaluate_hygiene, evaluate_sensitive_denylist
from evals.metrics.retriever_contract import evaluate_agt11, evaluate_agt12
from evals.metrics.schema_contract import evaluate_agt03_mock, evaluate_agt05, evaluate_agt10, evaluate_ret08
from evals.metrics.tool_trace import evaluate_ret_01, evaluate_ret_03, evaluate_ret_04
from evals.runners.run_suite import PR_NIGHTLY_IDS, enforce_deterministic_only, run_suite
from evals.runners.task_loader import load_tasks

EVALS_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = EVALS_ROOT / "datasets" / "retrieval_prompt_paths.jsonl"
KNOWLEDGE_FIXTURES = EVALS_ROOT / "fixtures" / "knowledge"
LLM_MOCKS = EVALS_ROOT / "fixtures" / "llm_mocks"


@pytest.fixture(scope="module")
def tasks():
    return load_tasks(DATASET_PATH)


@pytest.fixture(scope="module")
def task_map(tasks):
    return {task.id: task for task in tasks}


@pytest.fixture(scope="module")
def retrieval_cases():
    return json.loads((KNOWLEDGE_FIXTURES / "retrieval_cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ret06_fixture():
    return json.loads((KNOWLEDGE_FIXTURES / "ret06_db_fixture.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def differential_fixture():
    return json.loads((KNOWLEDGE_FIXTURES / "agt_differential_cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def agt03_agt04_fixture():
    return json.loads((KNOWLEDGE_FIXTURES / "agt03_agt04_fixtures.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def agt15_fixture():
    return json.loads((KNOWLEDGE_FIXTURES / "agt15_content_filter_fixture.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def agt16_fixture():
    return json.loads((KNOWLEDGE_FIXTURES / "agt16_orchestration_fixture.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rag_critic_mocks():
    return json.loads((LLM_MOCKS / "rag_critic_outputs.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def summarizer_mocks():
    return json.loads((LLM_MOCKS / "summarizer_outputs.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bridge_mocks():
    return json.loads((LLM_MOCKS / "bridge_outputs.json").read_text(encoding="utf-8"))


def test_dataset_contains_all_required_ids(task_map):
    required = {
        *(f"RET-0{i}" for i in range(1, 9)),
        *(f"AGT-{i:02d}" for i in range(1, 17)),
    }
    assert required == set(task_map)


def test_dataset_required_metadata_fields(task_map):
    required_fields = {
        "path_id",
        "mode",
        "required_invariants",
        "accepted_outcomes",
        "deterministic_metrics",
        "runtime_llm_judge",
    }
    for task_id, task in task_map.items():
        for field in required_fields:
            assert field in task.raw, f"{task_id} missing {field}"


def test_ret_01_thresholds(retrieval_cases):
    result = evaluate_ret_01(retrieval_cases["RET-01"]["tool_sequence"])
    assert result["first_retrieval_tool_local"] is True
    assert result["web_tool_calls_before_first_local"] == 0


def test_ret_02_thresholds(retrieval_cases):
    result = evaluate_ret_02(retrieval_cases["RET-02"]["response_text"])
    assert result["invalid_citation_url_count"] == 0
    assert result["minimum_local_citations"] >= 1


def test_ret_03_thresholds(retrieval_cases):
    result = evaluate_ret_03(retrieval_cases["RET-03"]["tool_sequence"])
    assert result["web_tool_calls"] <= 1
    assert result["local_retrieval_calls"] >= 1


def test_ret_04_thresholds(retrieval_cases):
    case = retrieval_cases["RET-04"]
    result = evaluate_ret_04(case["response_text"], case["tool_sequence"])
    assert result["missing_local_stated"] is True
    assert result["fallback_tool_calls"] <= 2


def test_ret_05_thresholds(retrieval_cases):
    result = evaluate_hygiene(retrieval_cases["RET-05"]["response_text"])
    assert result["hidden_tag_leakage_count"] == 0
    assert result["absolute_path_leakage_count"] == 0


def test_ret_06_thresholds(ret06_fixture):
    result = evaluate_ret06(ret06_fixture["records"], ret06_fixture["slot_checks"])
    assert result["summary_non_empty_rate"] == 1.0
    assert result["planted_fact_slot_recall"] >= 0.8


def test_ret_08_thresholds(rag_critic_mocks):
    ret08 = rag_critic_mocks["RET-08"]
    result = evaluate_ret08(ret08["valid_outputs"], ret08["malformed_outputs"])
    assert result["json_parse_success_rate"] == 1.0
    assert result["fallback_contract_success_rate"] == 1.0


def test_agt_01_thresholds(retrieval_cases):
    result = evaluate_hygiene(retrieval_cases["RET-05"]["response_text"])
    assert result["hidden_tag_leakage_count"] == 0


def test_agt_02_thresholds(differential_fixture):
    result = evaluate_agt02(differential_fixture["AGT-02"])
    assert result["differential_invariant_compliance"] == 1.0
    assert result["forbidden_style_regressions"] == 0


def test_agt_03_mocked_thresholds(agt03_agt04_fixture):
    summary = agt03_agt04_fixture["AGT-03"]["mocked_summary"]
    result = evaluate_agt03_mock(summary)
    mocked_pass_rate = 1.0 if result["mocked_format_pass"] else 0.0
    assert mocked_pass_rate == 1.0


def test_agt_04_thresholds(agt03_agt04_fixture):
    data = agt03_agt04_fixture["AGT-04"]
    result = evaluate_sensitive_denylist(data["output_text"], data["denylist"])
    assert result["sensitive_leakage_count"] == 0


def test_agt_05_thresholds(summarizer_mocks):
    result = evaluate_agt05(summarizer_mocks["AGT-05"]["payloads"])
    assert result["schema_validation_pass_rate"] == 1.0


def test_agt_06_thresholds(summarizer_mocks):
    data = summarizer_mocks["AGT-06"]
    result = evaluate_agt06(data["slot_checks"], data["contradiction_count"])
    assert result["slot_coverage"] >= 0.8
    assert result["contradiction_count"] == 0


def test_agt_07_thresholds(bridge_mocks):
    result = evaluate_agt07(bridge_mocks["AGT-07"]["cases"])
    assert result["fallback_contract_pass_rate"] == 1.0


def test_agt_08_thresholds(differential_fixture):
    result = evaluate_agt08(differential_fixture["AGT-08"])
    assert result["signal_direction_pass_rate"] == 1.0


def test_agt_09_thresholds():
    entries = [
        "User has recently been exploring deterministic evals.",
        "User is focused on retrieval eval quality.",
    ]
    result = evaluate_agt09(entries)
    assert result["duplicate_summary_insertions"] == 0


def test_agt_10_thresholds(summarizer_mocks):
    data = summarizer_mocks["AGT-10"]
    result = evaluate_agt10(data["fallback_objects"], data["crash_count"])
    assert result["recovery_pass_rate"] == 1.0
    assert result["crash_count"] == 0


def test_agt_11_thresholds(rag_critic_mocks):
    result = evaluate_agt11(rag_critic_mocks["AGT-11"]["boundary_cases"])
    assert result["boundary_accuracy"] == 1.0


def test_agt_12_thresholds_and_mocked_only(rag_critic_mocks, task_map):
    result = evaluate_agt12(rag_critic_mocks["AGT-12"]["pairwise_cases"])
    assert result["pairwise_accuracy"] >= 0.9
    assert task_map["AGT-12"].raw.get("mocked_only") is True
    assert task_map["AGT-12"].runtime_llm_judge == "off"


def test_agt_13_thresholds(bridge_mocks):
    result = evaluate_agt13(bridge_mocks["AGT-13"]["cases"])
    assert result["error_envelope_pass_rate"] == 1.0
    assert result["uncaught_exception_leakage"] == 0


def test_agt_14_thresholds(bridge_mocks):
    data = bridge_mocks["AGT-14"]
    result = evaluate_agt14(data["valid_mode_cases"], data["invalid_mode_cases"])
    assert result["valid_mode_contract_pass_rate"] == 1.0
    assert result["invalid_mode_contract_pass_rate"] == 1.0


def test_agt_15_thresholds_and_fixture_requirements(agt15_fixture):
    result = evaluate_agt15(agt15_fixture["chunks"])
    assert result["hidden_tag_leakage_count"] == 0
    assert result["raw_partial_tag_leakage_count"] == 0
    for expected in agt15_fixture["expected_visible_substrings"]:
        assert expected in result["visible_text"]


def test_agt_16_thresholds_and_fixture_requirements(agt16_fixture):
    orchestration = evaluate_agt16_orchestration(
        agt16_fixture["stream_chunks"],
        agt16_fixture["persisted_assistant_response"],
    )
    assert orchestration["mixed_stream_parse_error_count"] == 0
    assert orchestration["persisted_response_completeness_ratio"] >= 0.99

    db_state = evaluate_agt16_db(
        agt16_fixture["concurrent_chat_rows"],
        agt16_fixture["persisted_assistant_response"],
        orchestration["visible_text"],
    )
    assert db_state["duplicate_chat_rows"] == 0
    assert db_state["persisted_response_completeness_ratio"] >= 0.99


def test_pr_nightly_runner_guardrail(tasks):
    summary = run_suite("pr", DATASET_PATH)
    assert summary["selected_task_count"] == len(PR_NIGHTLY_IDS)
    assert summary["selected_task_ids"] == PR_NIGHTLY_IDS

    task_map = {task.id: task for task in tasks}
    with pytest.raises(ValueError, match="runtime judge tasks"):
        enforce_deterministic_only([task_map["RET-07"]])
