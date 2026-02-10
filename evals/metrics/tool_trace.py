"""Deterministic tool-trace metrics for retrieval-path evals."""

from __future__ import annotations

import re
from typing import Iterable, Sequence

LOCAL_RETRIEVAL_TOOLS = {
    "read_paper",
    "Skill:knowledge.paper.read",
    "Skill:paper.read",
    "Skill:knowledge.paper.search",
}
WEB_TOOLS = {"WebSearch", "WebFetch"}
FALLBACK_TOOLS = {"WebSearch", "WebFetch", "Skill:knowledge.paper.search"}

MISSING_LOCAL_PATTERNS = (
    re.compile(r"missing local", re.IGNORECASE),
    re.compile(r"could not find .*local", re.IGNORECASE),
    re.compile(r"not found .*library", re.IGNORECASE),
)


def _count_before_index(items: Sequence[str], matches: set[str], stop: int) -> int:
    return sum(1 for idx, name in enumerate(items) if idx < stop and name in matches)


def evaluate_ret_01(tool_sequence: Sequence[str]) -> dict:
    """RET-01: first retrieval must be local and web-before-local must be zero."""

    local_positions = [idx for idx, name in enumerate(tool_sequence) if name in LOCAL_RETRIEVAL_TOOLS]
    first_local_index = local_positions[0] if local_positions else None
    web_before_local = (
        _count_before_index(tool_sequence, WEB_TOOLS, first_local_index)
        if first_local_index is not None
        else sum(1 for name in tool_sequence if name in WEB_TOOLS)
    )
    first_retrieval_tool_local = first_local_index == 0

    return {
        "first_retrieval_tool_local": first_retrieval_tool_local,
        "web_tool_calls_before_first_local": web_before_local,
    }


def evaluate_ret_03(tool_sequence: Sequence[str]) -> dict:
    """RET-03: web calls <= 1 and local retrieval calls >= 1 on local-only tasks."""

    web_tool_calls = sum(1 for name in tool_sequence if name in WEB_TOOLS)
    local_retrieval_calls = sum(1 for name in tool_sequence if name in LOCAL_RETRIEVAL_TOOLS)
    return {
        "web_tool_calls": web_tool_calls,
        "local_retrieval_calls": local_retrieval_calls,
    }


def evaluate_ret_04(response_text: str, tool_sequence: Iterable[str]) -> dict:
    """RET-04: missing-local condition explicit and bounded fallback path."""

    sequence = list(tool_sequence)
    missing_local_stated = any(pattern.search(response_text) for pattern in MISSING_LOCAL_PATTERNS)
    fallback_tool_calls = sum(1 for name in sequence if name in FALLBACK_TOOLS)
    return {
        "missing_local_stated": missing_local_stated,
        "fallback_tool_calls": fallback_tool_calls,
    }
