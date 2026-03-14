from __future__ import annotations

import re
from typing import Optional

_ARXIV_ID_WITH_OPTIONAL_VERSION_RE = re.compile(
    r"^(?P<id>\d{4}\.\d{4,5})(?:v(?P<version>\d+))?$",
    re.IGNORECASE,
)
_ARXIV_URL_RE = re.compile(
    r"arxiv\.org/(?:abs|pdf|html)/(?P<id>\d{4}\.\d{4,5})(?:v(?P<version>\d+))?(?:\.pdf)?$",
    re.IGNORECASE,
)


def canonicalize_arxiv_id(raw: str) -> Optional[str]:
    """Return canonical modern arXiv id (without version), or None if not matched."""
    value = str(raw or "").strip()
    if not value:
        return None

    direct = _ARXIV_ID_WITH_OPTIONAL_VERSION_RE.match(value)
    if direct:
        return direct.group("id")

    url = _ARXIV_URL_RE.search(value)
    if url:
        return url.group("id")
    return None


def resolve_paper_id(raw: str) -> str:
    """
    Resolve a paper identifier into canonical value for modern arXiv IDs.
    Non-arXiv local IDs are returned unchanged (trimmed).
    """
    value = str(raw or "").strip()
    canonical = canonicalize_arxiv_id(value)
    return canonical or value
