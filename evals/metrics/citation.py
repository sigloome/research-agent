"""Deterministic citation contract checks."""

from __future__ import annotations

import re
from typing import List

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LOCAL_PAPER_URL_RE = re.compile(r"^/paper/[A-Za-z0-9._:-]+$")


def extract_citation_urls(text: str) -> List[str]:
    """Extract markdown citation URLs from output text."""

    return MARKDOWN_LINK_RE.findall(text)


def evaluate_ret_02(text: str) -> dict:
    """RET-02: local citation contract (/paper/{id}) with minimum local citation count."""

    urls = extract_citation_urls(text)
    local_citations = [url for url in urls if url.startswith("/paper/")]
    invalid_local_urls = [url for url in local_citations if not LOCAL_PAPER_URL_RE.match(url)]
    invalid_external_for_local = [url for url in urls if not url.startswith("/paper/")]

    return {
        "minimum_local_citations": len(local_citations),
        "invalid_citation_url_count": len(invalid_local_urls) + len(invalid_external_for_local),
        "all_citation_urls": urls,
    }
