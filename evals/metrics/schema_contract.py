"""Schema and parser contract checks for summarizer/critic outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List

REQUIRED_SUMMARY_KEYS = [
    "tags",
    "summary_main_ideas",
    "summary_methods",
    "summary_results",
    "summary_limitations",
]

SUMMARY_PREFIXES = (
    "User has recently been exploring",
    "User is focused on",
)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_summary_schema(payload: Dict[str, Any]) -> bool:
    """Strict schema validator for AGT-05 summarizer output."""

    if not isinstance(payload, dict):
        return False
    for key in REQUIRED_SUMMARY_KEYS:
        if key not in payload:
            return False
    if not isinstance(payload.get("tags"), list):
        return False
    return all(
        _is_non_empty_string(payload[key])
        for key in ["summary_main_ideas", "summary_methods", "summary_results", "summary_limitations"]
    )


def evaluate_agt05(payloads: Iterable[Dict[str, Any]]) -> dict:
    """AGT-05: strict JSON schema pass rate."""

    data = list(payloads)
    if not data:
        return {"schema_validation_pass_rate": 0.0}
    passes = sum(1 for payload in data if validate_summary_schema(payload))
    return {"schema_validation_pass_rate": passes / len(data)}


def evaluate_agt10(fallback_objects: Iterable[Dict[str, Any]], crash_count: int) -> dict:
    """AGT-10: fallback contract success and crash count."""

    objects = list(fallback_objects)
    if not objects:
        return {"recovery_pass_rate": 0.0, "crash_count": crash_count}

    recoveries = 0
    for payload in objects:
        if not isinstance(payload, dict):
            continue
        tags = payload.get("tags")
        summary_main = payload.get("summary_main_ideas")
        if isinstance(tags, list) and len(tags) >= 1 and isinstance(summary_main, str):
            recoveries += 1

    return {
        "recovery_pass_rate": recoveries / len(objects),
        "crash_count": crash_count,
    }


def parse_critic_output_with_fallback(raw_output: str) -> dict:
    """Parse critic JSON with deterministic fallback contract."""

    fallback = {
        "score": 0.0,
        "reasoning": "Failed to parse LLM response",
        "fallback_used": True,
        "parsed_successfully": False,
    }

    text = (raw_output or "").strip()
    if not text:
        return fallback

    candidate = text
    if "{" in text and "}" in text:
        candidate = text[text.find("{") : text.rfind("}") + 1]

    try:
        payload = json.loads(candidate)
    except Exception:
        return fallback

    score = payload.get("score") if isinstance(payload, dict) else None
    reasoning = payload.get("reasoning") if isinstance(payload, dict) else None
    if not isinstance(score, (int, float)):
        return fallback
    if not isinstance(reasoning, str) or not reasoning.strip():
        return fallback

    return {
        "score": float(score),
        "reasoning": reasoning,
        "fallback_used": False,
        "parsed_successfully": True,
    }


def evaluate_ret08(valid_outputs: Iterable[str], malformed_outputs: Iterable[str]) -> dict:
    """RET-08: parse success on valid outputs + fallback contract on malformed outputs."""

    valid_list = list(valid_outputs)
    malformed_list = list(malformed_outputs)

    valid_parsed = [parse_critic_output_with_fallback(item) for item in valid_list]
    malformed_parsed = [parse_critic_output_with_fallback(item) for item in malformed_list]

    valid_success_count = sum(1 for item in valid_parsed if item["parsed_successfully"])
    malformed_fallback_success = sum(
        1
        for item in malformed_parsed
        if item["fallback_used"] and isinstance(item["score"], float) and isinstance(item["reasoning"], str)
    )

    valid_rate = (valid_success_count / len(valid_list)) if valid_list else 0.0
    malformed_rate = (malformed_fallback_success / len(malformed_list)) if malformed_list else 0.0

    return {
        "json_parse_success_rate": valid_rate,
        "fallback_contract_success_rate": malformed_rate,
    }


def evaluate_agt03_mock(summary: str) -> dict:
    """AGT-03 deterministic mocked format check."""

    text = summary.strip()
    sentence_split = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    sentence_count = len(sentence_split)
    has_required_prefix = any(text.startswith(prefix) for prefix in SUMMARY_PREFIXES)

    return {
        "sentence_count": sentence_count,
        "has_required_prefix": has_required_prefix,
        "mocked_format_pass": sentence_count == 1 and has_required_prefix,
    }
