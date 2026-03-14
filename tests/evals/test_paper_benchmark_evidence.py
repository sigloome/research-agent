from __future__ import annotations

from evals.metrics.paper_benchmark import (
    evaluate_evidence_item_coverage,
    extract_observed_facets_from_evidence,
)


def test_extract_observed_facets_from_evidence_items():
    evidence_items = [
        {
            "paper_id": "p1",
            "method": "graph retrieval",
            "dataset": "HotpotQA",
            "metric": "EM",
            "value": "48.2",
            "limitation": "different setup",
            "polarity": "support",
            "comparability_warning": "non-comparable",
            "source_ref": "/paper/p1",
        },
        {
            "paper_id": "p2",
            "polarity": "contradict",
            "source_ref": "/paper/p2",
        },
    ]
    observed = extract_observed_facets_from_evidence(evidence_items)
    assert set(observed) >= {
        "method",
        "dataset",
        "metric",
        "result",
        "limitation",
        "support",
        "contradict",
        "citation",
        "comparability_warning",
    }


def test_evaluate_evidence_item_coverage_uses_structured_fields():
    evidence_items = [
        {
            "paper_id": "p1",
            "method": "graph retrieval",
            "dataset": "HotpotQA",
            "metric": "EM",
            "value": "48.2",
            "limitation": "different setup",
            "polarity": "support",
            "source_ref": "/paper/p1",
        }
    ]
    result = evaluate_evidence_item_coverage(
        evidence_items=evidence_items,
        required_facets=["method", "dataset", "metric", "result", "limitation", "support"],
    )
    assert result["facet_coverage"] == 1.0
