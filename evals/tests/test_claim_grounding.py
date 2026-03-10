from evals.metrics.claim_grounding import evaluate_claim_grounding


def test_claim_grounding_with_evidence_markers():
    text = """
Claim: The system always preserves stream completion markers.
Evidence: see <citation url="/paper/1706.03762">...</citation>
"""
    out = evaluate_claim_grounding(text)
    assert out["claim_count"] >= 1
    assert out["unsupported_claim_count"] == 0
    assert out["claim_grounded_ratio"] == 1.0
    assert out["evidence_marker_present"] == 1.0


def test_claim_grounding_detects_unsupported_claim():
    text = "The method is always correct and certainly optimal."
    out = evaluate_claim_grounding(text)
    assert out["claim_count"] >= 1
    assert out["unsupported_claim_count"] >= 1
    assert out["claim_grounded_ratio"] < 1.0
