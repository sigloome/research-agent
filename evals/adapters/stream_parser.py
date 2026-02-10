"""Parsers for mixed stream formats used by chat/orchestration eval fixtures."""

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


def _parse_data_line(line: str) -> StreamEvent:
    raw_payload = line[5:].strip()
    if raw_payload == "[DONE]":
        return StreamEvent(kind="done", payload="[DONE]", raw=line)

    payload = json.loads(raw_payload)
    if isinstance(payload, dict):
        if payload.get("type") == "content" and "content" in payload:
            return StreamEvent(kind="text", payload=payload["content"], raw=line)
        if "text" in payload:
            return StreamEvent(kind="text", payload=payload["text"], raw=line)
    return StreamEvent(kind="data", payload=payload, raw=line)


def _parse_d_line(line: str) -> StreamEvent:
    payload = json.loads(line[2:].strip())
    if isinstance(payload, dict) and payload.get("type") == "tool_usage":
        return StreamEvent(kind="tool_usage", payload=payload, raw=line)
    if isinstance(payload, dict) and payload.get("type") == "meta":
        return StreamEvent(kind="meta", payload=payload, raw=line)
    return StreamEvent(kind="data", payload=payload, raw=line)


def parse_stream(chunks: Iterable[str]) -> ParsedStream:
    """Parse mixed stream chunks (`0:`, `data:`, `d:`) into normalized events."""

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
