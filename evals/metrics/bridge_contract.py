"""Bridge/GraphRAG deterministic contract metrics."""

from __future__ import annotations

from typing import Iterable, Mapping


def _pass_rate(cases: Iterable[Mapping[str, bool]], key: str) -> float:
    rows = list(cases)
    if not rows:
        return 0.0
    passed = sum(1 for row in rows if bool(row.get(key)))
    return passed / len(rows)


def evaluate_agt07(cases: Iterable[Mapping[str, bool]]) -> dict:
    """AGT-07 embedding/completion fallback behavior."""

    return {"fallback_contract_pass_rate": _pass_rate(cases, "fallback_ok")}


def evaluate_agt13(cases: Iterable[Mapping[str, bool]]) -> dict:
    """AGT-13 typed error-envelope and exception-leak checks."""

    rows = list(cases)
    if not rows:
        return {"error_envelope_pass_rate": 0.0, "uncaught_exception_leakage": 0}

    envelope_pass = sum(1 for row in rows if bool(row.get("envelope_valid")))
    uncaught = sum(1 for row in rows if bool(row.get("uncaught_exception")))
    return {
        "error_envelope_pass_rate": envelope_pass / len(rows),
        "uncaught_exception_leakage": uncaught,
    }


def evaluate_agt14(valid_mode_cases: Iterable[Mapping[str, bool]], invalid_mode_cases: Iterable[Mapping[str, bool]]) -> dict:
    """AGT-14 query-mode contract for valid/invalid modes."""

    return {
        "valid_mode_contract_pass_rate": _pass_rate(valid_mode_cases, "contract_ok"),
        "invalid_mode_contract_pass_rate": _pass_rate(invalid_mode_cases, "contract_ok"),
    }
