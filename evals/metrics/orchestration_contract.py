"""Deterministic orchestration contracts for mixed stream parsing."""

from __future__ import annotations

from typing import Iterable

from evals.adapters.stream_parser import parse_stream
from evals.adapters.trace_mapper import map_visible_text, map_tool_sequence


def evaluate_agt16_orchestration(stream_chunks: Iterable[str], persisted_assistant_response: str) -> dict:
    """AGT-16: parse mixed stream formats and verify persisted response completeness."""

    parsed = parse_stream(stream_chunks)
    visible_text = map_visible_text(parsed.events)
    tool_sequence = map_tool_sequence(parsed.events)

    expected_len = max(len(visible_text), 1)
    completeness_ratio = len(persisted_assistant_response) / expected_len

    return {
        "mixed_stream_parse_error_count": len(parsed.parse_errors),
        "persisted_response_completeness_ratio": completeness_ratio,
        "tool_sequence": tool_sequence,
        "visible_text": visible_text,
    }
