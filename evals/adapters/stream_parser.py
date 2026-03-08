"""Parsers for UI-message SSE streams with legacy fallback support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class StreamEvent:
    """A normalized event emitted from a stream line."""

    kind: str
    payload: Any
    raw: str


@dataclass(frozen=True)
class ParsedStream:
    """Parsed stream output with accumulated errors."""

    events: List[StreamEvent]
    parse_errors: List[str]


def _parse_0_line(line: str) -> StreamEvent:
    raw_payload = line[2:].strip()
    payload = json.loads(raw_payload)
    if not isinstance(payload, str):
        raise ValueError("0: payload must decode to a string")
    return StreamEvent(kind="text", payload=payload, raw=line)


def _normalize_payload_event(payload: Any, raw_line: str) -> StreamEvent:
    if isinstance(payload, dict):
        chunk_type = payload.get("type")

        # Standard UI-message text streaming chunk.
        if chunk_type == "text-delta" and isinstance(payload.get("delta"), str):
            return StreamEvent(kind="text", payload=payload["delta"], raw=raw_line)

        # Legacy content payload fallback.
        if chunk_type == "content" and isinstance(payload.get("content"), str):
            return StreamEvent(kind="text", payload=payload["content"], raw=raw_line)

        # Legacy text payload fallback.
        if isinstance(payload.get("text"), str):
            return StreamEvent(kind="text", payload=payload["text"], raw=raw_line)

        # Tool invocation chunks in UI message streams.
        if chunk_type in {"tool-input-start", "tool-input-available"}:
            tool_name = payload.get("toolName")
            if isinstance(tool_name, str):
                return StreamEvent(
                    kind="tool_usage",
                    payload={"tool": tool_name, "type": chunk_type},
                    raw=raw_line,
                )

        # Legacy tool usage fallback.
        if chunk_type == "tool_usage" and isinstance(payload.get("tool"), str):
            return StreamEvent(kind="tool_usage", payload=payload, raw=raw_line)

        if chunk_type in {"finish", "meta"}:
            return StreamEvent(kind="meta", payload=payload, raw=raw_line)

    return StreamEvent(kind="data", payload=payload, raw=raw_line)


def _parse_data_line(line: str) -> StreamEvent:
    raw_payload = line[5:].strip()
    if raw_payload == "[DONE]":
        return StreamEvent(kind="done", payload="[DONE]", raw=line)

    payload = json.loads(raw_payload)
    return _normalize_payload_event(payload, line)


def _parse_d_line(line: str) -> StreamEvent:
    payload = json.loads(line[2:].strip())
    return _normalize_payload_event(payload, line)


def parse_stream(chunks: Iterable[str]) -> ParsedStream:
    """Parse SSE UI-message chunks (`data:`) with legacy `0:`/`d:` fallback."""

    events: List[StreamEvent] = []
    parse_errors: List[str] = []

    for chunk in chunks:
        for line in chunk.splitlines():
            normalized = line.strip()
            if not normalized:
                continue

            try:
                if normalized.startswith("0:"):
                    events.append(_parse_0_line(normalized))
                elif normalized.startswith("data:"):
                    events.append(_parse_data_line(normalized))
                elif normalized.startswith("d:"):
                    events.append(_parse_d_line(normalized))
                else:
                    events.append(StreamEvent(kind="unknown", payload=normalized, raw=normalized))
                    parse_errors.append(f"unsupported format: {normalized}")
            except Exception as exc:  # pragma: no cover - exercised in parser edge tests
                parse_errors.append(f"parse failure for line '{normalized}': {exc}")

    return ParsedStream(events=events, parse_errors=parse_errors)
