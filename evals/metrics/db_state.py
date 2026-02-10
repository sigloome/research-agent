"""Deterministic DB/state contracts for eval tasks."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping, Sequence

REQUIRED_SUMMARY_FIELDS = (
    "summary_main_ideas",
    "summary_methods",
    "summary_results",
    "summary_limitations",
)


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def required_field_non_empty_rate(records: Sequence[Mapping[str, object]]) -> float:
    """Compute per-record all-required-fields non-empty rate."""

    if not records:
        return 0.0

    passed = 0
    for row in records:
        if all(_non_empty(row.get(field)) for field in REQUIRED_SUMMARY_FIELDS):
            passed += 1
    return passed / len(records)


def planted_fact_slot_recall(slot_checks: Iterable[Mapping[str, Sequence[str]]]) -> float:
    """Compute aggregate recall from expected/matched slot fixtures."""

    expected_total = 0
    matched_total = 0

    for check in slot_checks:
        expected = list(check.get("expected", []))
        matched = list(check.get("matched", []))
        expected_total += len(expected)
        matched_total += len([slot for slot in matched if slot in expected])

    if expected_total == 0:
        return 0.0
    return matched_total / expected_total


def evaluate_ret06(records: Sequence[Mapping[str, object]], slot_checks: Iterable[Mapping[str, Sequence[str]]]) -> dict:
    """RET-06 ingestion-to-retrieval integrity."""

    return {
        "summary_non_empty_rate": required_field_non_empty_rate(records),
        "planted_fact_slot_recall": planted_fact_slot_recall(slot_checks),
    }


def evaluate_agt06(slot_checks: Iterable[Mapping[str, Sequence[str]]], contradiction_count: int) -> dict:
    """AGT-06 slot coverage and contradiction checks."""

    return {
        "slot_coverage": planted_fact_slot_recall(slot_checks),
        "contradiction_count": contradiction_count,
    }


def evaluate_agt09(summary_entries: Sequence[str]) -> dict:
    """AGT-09 duplicate summary insertion checks."""

    normalized = [entry.strip().lower() for entry in summary_entries if entry.strip()]
    counts = Counter(normalized)
    duplicate_insertions = sum(count - 1 for count in counts.values() if count > 1)
    return {"duplicate_summary_insertions": duplicate_insertions}


def evaluate_agt16_db(chat_rows: Sequence[Mapping[str, str]], persisted_assistant_response: str, expected_response: str) -> dict:
    """AGT-16 DB-facing assertions for duplicate rows and persisted completeness."""

    chat_ids = [row.get("chat_id", "") for row in chat_rows]
    counts = Counter(chat_ids)
    duplicate_rows = sum(count - 1 for count in counts.values() if count > 1 and count > 0)

    expected_len = max(len(expected_response), 1)
    persisted_len = len(persisted_assistant_response)
    completeness_ratio = persisted_len / expected_len

    return {
        "duplicate_chat_rows": duplicate_rows,
        "persisted_response_completeness_ratio": completeness_ratio,
    }
