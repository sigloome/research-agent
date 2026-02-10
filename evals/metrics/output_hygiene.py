"""Output hygiene and leakage checks."""

from __future__ import annotations

import re
from typing import Iterable

HIDDEN_TAG_RE = re.compile(r"</?(thinking|private|debug)\b", re.IGNORECASE)
ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s`])/(Users|home|var|tmp)/[^\s`<>]+", re.MULTILINE)


def evaluate_hygiene(text: str) -> dict:
    """RET-05 / AGT-01: hidden-tag and absolute-path leakage counts."""

    hidden_tag_leakage_count = len(HIDDEN_TAG_RE.findall(text))
    absolute_path_leakage_count = len(ABSOLUTE_PATH_RE.findall(text))
    return {
        "hidden_tag_leakage_count": hidden_tag_leakage_count,
        "absolute_path_leakage_count": absolute_path_leakage_count,
    }


def evaluate_sensitive_denylist(text: str, denylist: Iterable[str]) -> dict:
    """AGT-04: deterministic denylist-based sensitive leakage detection."""

    lowered = text.lower()
    leak_count = 0
    for token in denylist:
        if token.lower() in lowered:
            leak_count += 1
    return {"sensitive_leakage_count": leak_count}
