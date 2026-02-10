"""Helpers to map parsed stream events into eval-friendly traces."""

from __future__ import annotations

from typing import Iterable, List

from evals.adapters.stream_parser import StreamEvent


def map_tool_sequence(events: Iterable[StreamEvent]) -> List[str]:
    """Extract ordered tool names from normalized stream events."""

    tools: List[str] = []
    for event in events:
        if event.kind != "tool_usage":
            continue
        payload = event.payload
        if isinstance(payload, dict) and "tool" in payload:
            tools.append(str(payload["tool"]))
    return tools


def map_visible_text(events: Iterable[StreamEvent]) -> str:
    """Join user-visible text from parsed events."""

    parts: List[str] = []
    for event in events:
        if event.kind != "text":
            continue
        if isinstance(event.payload, str):
            parts.append(event.payload)
    return "".join(parts)


def map_data_events(events: Iterable[StreamEvent], event_type: str) -> List[dict]:
    """Collect data/meta events by `type` key if available."""

    out: List[dict] = []
    for event in events:
        if event.kind not in {"data", "meta", "tool_usage"}:
            continue
        payload = event.payload
        if isinstance(payload, dict) and payload.get("type") == event_type:
            out.append(payload)
    return out
