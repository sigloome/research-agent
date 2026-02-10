"""Deterministic contracts for streaming content filter behavior."""

from __future__ import annotations

import re
from typing import Iterable

from backend.content_filter import StreamingContentFilter

HIDDEN_TAG_RE = re.compile(r"</?(thinking|private|debug)\b", re.IGNORECASE)
RAW_PARTIAL_TAG_RE = re.compile(r"<(/)?(think|priv|deb)[^>]*$|<(/)?(think|priv|deb)", re.IGNORECASE)


def evaluate_agt15(chunks: Iterable[str]) -> dict:
    """AGT-15: no hidden-tag leakage, including nested/unclosed chunk boundaries."""

    content_filter = StreamingContentFilter()
    rendered_parts = []

    for chunk in chunks:
        filtered = content_filter.filter_chunk(chunk)
        if filtered:
            rendered_parts.append(filtered)

    tail = content_filter.flush()
    if tail:
        rendered_parts.append(tail)

    visible_text = "".join(rendered_parts)
    hidden_tag_leakage_count = len(HIDDEN_TAG_RE.findall(visible_text))
    raw_partial_tag_leakage_count = len(RAW_PARTIAL_TAG_RE.findall(visible_text))

    return {
        "visible_text": visible_text,
        "hidden_tag_leakage_count": hidden_tag_leakage_count,
        "raw_partial_tag_leakage_count": raw_partial_tag_leakage_count,
    }
