"""Differential contract checks for prompt-variant behavior."""

from __future__ import annotations

from typing import Iterable, Mapping


def evaluate_agt02(cases: Iterable[Mapping[str, bool]]) -> dict:
    """AGT-02: invariant compliance must be 100%, style regressions must be zero."""

    rows = list(cases)
    if not rows:
        return {"differential_invariant_compliance": 0.0, "forbidden_style_regressions": 0}

    compliant = sum(1 for row in rows if bool(row.get("invariant_compliant")))
    regressions = sum(1 for row in rows if bool(row.get("forbidden_style_regression")))

    return {
        "differential_invariant_compliance": compliant / len(rows),
        "forbidden_style_regressions": regressions,
    }


def evaluate_agt08(cases: Iterable[Mapping[str, bool]]) -> dict:
    """AGT-08: prompt-wiring differential signal must hold in every fixture case."""

    rows = list(cases)
    if not rows:
        return {"signal_direction_pass_rate": 0.0}

    passed = sum(1 for row in rows if bool(row.get("signal_direction_ok")))
    return {"signal_direction_pass_rate": passed / len(rows)}
