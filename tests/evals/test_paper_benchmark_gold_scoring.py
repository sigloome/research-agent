from __future__ import annotations

from evals.metrics.paper_benchmark import evaluate_case_against_retrieval_context


def test_evaluate_case_against_retrieval_context_scores_required_papers_and_facets():
    case = {
        "expect": {
            "required_paper_ids": ["p1", "p2"],
            "required_clusters": {
                "classic_baseline": ["p1"],
                "recent_followup": ["p3"],
            },
            "required_facets": ["method", "dataset", "metric", "result", "limitation"],
        }
    }
    retrieval_context = {
        "candidate_papers": [
            {"paper_id": "p1"},
            {"paper_id": "p3"},
        ],
        "evidence_items": [
            {
                "paper_id": "p1",
                "method": "graph retrieval",
                "dataset": "HotpotQA",
                "metric": "EM",
                "value": "48.2",
                "limitation": "different setup",
                "source_ref": "/paper/p1",
            }
        ],
    }
    result = evaluate_case_against_retrieval_context(
        case=case,
        retrieval_context=retrieval_context,
    )
    assert result["paper_recall"] == 0.5
    assert result["cluster_coverage"] == 1.0
    assert result["evidence_facet_coverage"] == 1.0


def test_evaluate_case_against_retrieval_context_scores_support_and_contradict_recall():
    case = {
        "expect": {
            "support_paper_ids": ["p-support"],
            "contradict_paper_ids": ["p-contradict"],
            "required_facets": ["support", "contradict"],
        }
    }
    retrieval_context = {
        "candidate_papers": [
            {"paper_id": "p-support"},
            {"paper_id": "p-contradict"},
        ],
        "evidence_items": [
            {"paper_id": "p-support", "polarity": "support", "source_ref": "/paper/p-support"},
            {
                "paper_id": "p-contradict",
                "polarity": "contradict",
                "source_ref": "/paper/p-contradict",
            },
        ],
    }
    result = evaluate_case_against_retrieval_context(
        case=case,
        retrieval_context=retrieval_context,
    )
    assert result["support_recall"] == 1.0
    assert result["contradict_recall"] == 1.0
    assert result["balanced_evidence"] is True
    assert result["evidence_facet_coverage"] == 1.0


def test_evaluate_case_against_retrieval_context_scores_span_grounding():
    case = {
        "expect": {
            "required_evidence_refs": ["/paper/p1#span1", "/paper/p2#span2"],
        }
    }
    retrieval_context = {
        "candidate_papers": [],
        "evidence_items": [
            {"paper_id": "p1", "source_ref": "/paper/p1#span1"},
            {"paper_id": "p2", "source_ref": "/paper/p2#spanX"},
        ],
    }
    result = evaluate_case_against_retrieval_context(case=case, retrieval_context=retrieval_context)
    assert result["span_grounding_recall"] == 0.5


def test_evaluate_case_against_retrieval_context_accepts_semantic_span_equivalence():
    case = {
        "expect": {
            "required_evidence_refs": ["/paper/p1#span1"],
            "required_evidence_items": [
                {
                    "source_ref": "/paper/p1#span1",
                    "paper_id": "p1",
                    "dataset": "HotpotQA",
                    "metric": "F1",
                    "value": "72.1",
                    "polarity": "support",
                }
            ],
        }
    }
    retrieval_context = {
        "candidate_papers": [{"paper_id": "p1"}],
        "evidence_items": [
            {
                "paper_id": "p1",
                "dataset": "HotpotQA",
                "metric": "F1",
                "value": "72.1",
                "polarity": "support",
                "source_ref": "/paper/p1#span2",
            }
        ],
    }
    result = evaluate_case_against_retrieval_context(case=case, retrieval_context=retrieval_context)
    assert result["span_grounding_recall"] == 1.0
