from __future__ import annotations

from evals.metrics.paper_benchmark import (
    evaluate_benchmark_budget,
    evaluate_benchmark_signature,
    evaluate_cluster_coverage,
    evaluate_comparison_facet_coverage,
    evaluate_repeat_run_stability,
    evaluate_support_contradict_recall,
)


def test_benchmark_signature_completeness_and_missing_fields():
    complete = evaluate_benchmark_signature(
        {
            "dataset_version": "paper_bench_v1",
            "dataset_hash": "sha256:abc",
            "snapshot_id": "papers_snapshot_v1",
            "seed": 42,
            "params_signature": "baseline-v1",
            "git_commit": "deadbeef",
        }
    )
    assert complete["signature_completeness"] == 1.0
    assert complete["missing_fields"] == []

    incomplete = evaluate_benchmark_signature(
        {
            "dataset_version": "paper_bench_v1",
            "seed": 42,
        }
    )
    assert incomplete["signature_completeness"] < 1.0
    assert "dataset_hash" in incomplete["missing_fields"]
    assert "snapshot_id" in incomplete["missing_fields"]


def test_benchmark_budget_gate_blocking_and_warning_modes():
    blocking = evaluate_benchmark_budget(
        profile="core",
        observed={
            "sample_count": 30,
            "mean_total_tokens": 5200,
            "p95_latency_ms": 8100,
            "timeout_rate": 0.1,
        },
        budgets={
            "core": {
                "sample_count_max": 24,
                "mean_total_tokens_max": 5000,
                "p95_latency_ms_max": 8000,
                "timeout_rate_max": 0.0,
                "blocking": True,
            }
        },
    )
    assert blocking["over_budget"] is True
    assert blocking["should_fail"] is True
    assert set(blocking["violations"]) == {
        "sample_count",
        "mean_total_tokens",
        "p95_latency_ms",
        "timeout_rate",
    }

    warning = evaluate_benchmark_budget(
        profile="audit",
        observed={
            "sample_count": 30,
            "mean_total_tokens": 9000,
            "p95_latency_ms": 15000,
            "timeout_rate": 0.1,
        },
        budgets={
            "audit": {
                "sample_count_max": 24,
                "mean_total_tokens_max": 7000,
                "p95_latency_ms_max": 12000,
                "timeout_rate_max": 0.02,
                "blocking": False,
            }
        },
    )
    assert warning["over_budget"] is True
    assert warning["should_fail"] is False


def test_paper_recall_related_metrics():
    coverage = evaluate_cluster_coverage(
        observed_paper_ids=["p1", "p3", "p4"],
        required_clusters={
            "classic_baseline": ["p1"],
            "recent_followup": ["p2", "p3"],
            "same_method_family": ["p5"],
        },
    )
    assert coverage["cluster_coverage"] == 2 / 3

    facets = evaluate_comparison_facet_coverage(
        observed_facets=["method", "dataset", "metric"],
        required_facets=["method", "dataset", "metric", "limitation"],
    )
    assert facets["facet_coverage"] == 0.75

    recall = evaluate_support_contradict_recall(
        observed_paper_ids=["s1", "c2", "n1"],
        support_paper_ids=["s1", "s2"],
        contradict_paper_ids=["c1", "c2"],
    )
    assert recall["support_recall"] == 0.5
    assert recall["contradict_recall"] == 0.5
    assert recall["balanced_evidence"] is True


def test_repeat_run_stability_detects_variance_within_tolerance():
    stable = evaluate_repeat_run_stability(
        baseline={"paper_recall_at_10": 0.8, "comparison_facet_coverage": 0.75},
        repeated={"paper_recall_at_10": 0.83, "comparison_facet_coverage": 0.71},
        tolerance=0.05,
    )
    assert stable["within_tolerance"] is True

    unstable = evaluate_repeat_run_stability(
        baseline={"paper_recall_at_10": 0.8, "comparison_facet_coverage": 0.75},
        repeated={"paper_recall_at_10": 0.9, "comparison_facet_coverage": 0.6},
        tolerance=0.05,
    )
    assert unstable["within_tolerance"] is False
    assert "comparison_facet_coverage" in unstable["out_of_tolerance_metrics"]
