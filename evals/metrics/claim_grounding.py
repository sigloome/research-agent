"""Parser-backed claim/evidence checks for stricter quality proxy validation."""

from __future__ import annotations

import re
from typing import Dict, List

CLAIM_PREFIX_RE = re.compile(r"^\s*(?:claim|assertion)\s*[:\-]\s*(.+)$", re.IGNORECASE)
GENERIC_CLAIM_RE = re.compile(r"\b(always|guaranteed|certainly|must)\b", re.IGNORECASE)
EVIDENCE_MARKERS = ("/paper/", "<citation", "<source", "reference", "evidence")


def extract_claims(text: str) -> List[str]:
    claims: List[str] = []
    for line in text.splitlines():
        m = CLAIM_PREFIX_RE.match(line)
        if m:
            claims.append(m.group(1).strip())
    if not claims:
        # Fallback: sentence-level strong claim heuristic.
        for sentence in re.split(r"[。.!?]\s*", text):
            if sentence and GENERIC_CLAIM_RE.search(sentence):
                claims.append(sentence.strip())
    return [c for c in claims if c]


def has_evidence(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in EVIDENCE_MARKERS)


def evaluate_claim_grounding(text: str) -> Dict[str, float]:
    claims = extract_claims(text)
    evidence = has_evidence(text)
    claim_count = len(claims)
    unsupported = claim_count if (claim_count > 0 and not evidence) else 0
    grounded_ratio = 1.0 if claim_count == 0 else max((claim_count - unsupported) / claim_count, 0.0)
    return {
        "claim_count": float(claim_count),
        "unsupported_claim_count": float(unsupported),
        "claim_grounded_ratio": grounded_ratio,
        "evidence_marker_present": 1.0 if evidence else 0.0,
    }
