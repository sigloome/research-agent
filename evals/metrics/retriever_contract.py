"""Retriever and critic deterministic contracts."""

from __future__ import annotations

from typing import Iterable, Mapping


def evaluate_ret07_ordering_agreement(labeled_pairs: Iterable[Mapping[str, float]]) -> dict:
    """RET-07 weekly-only critic polarity agreement."""

    pairs = list(labeled_pairs)
    if not pairs:
        return {"ordering_agreement": 0.0}

    agreements = 0
    for pair in pairs:
        if float(pair["answer_score"]) > float(pair["distractor_score"]):
            agreements += 1

    return {"ordering_agreement": agreements / len(pairs)}


def evaluate_agt11(boundary_cases: Iterable[Mapping[str, float]], threshold: float = 0.5) -> dict:
    """AGT-11 threshold filtering accuracy over boundary fixtures."""

    cases = list(boundary_cases)
    if not cases:
        return {"boundary_accuracy": 0.0}

    correct = 0
    for case in cases:
        decision = float(case["score"]) >= threshold
        if decision == bool(case["expected_include"]):
            correct += 1

    return {"boundary_accuracy": correct / len(cases)}


def evaluate_agt12(pairwise_cases: Iterable[Mapping[str, float]]) -> dict:
    """AGT-12 deterministic pairwise ranking accuracy over frozen fixtures."""

    cases = list(pairwise_cases)
    if not cases:
        return {"pairwise_accuracy": 0.0}

    correct = 0
    for case in cases:
        if float(case["positive_score"]) > float(case["negative_score"]):
            correct += 1

    return {"pairwise_accuracy": correct / len(cases)}
