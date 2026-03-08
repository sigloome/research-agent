#!/usr/bin/env python3
"""Deterministic validation for codex bridge-only runtime config."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_FILE = REPO_ROOT / "backend" / "agent.py"


def require(pattern: str, text: str, message: str) -> list[str]:
    if re.search(pattern, text, flags=re.MULTILINE | re.DOTALL):
        return []
    return [message]


def main() -> int:
    if not AGENT_FILE.exists():
        print(f"[error] missing file: {AGENT_FILE}")
        return 1

    text = AGENT_FILE.read_text(encoding="utf-8")
    errors: list[str] = []

    errors += require(
        r"self\.provider = os\.environ\.get\(\"AGENT_PROVIDER\", \"codex_bridge\"\)",
        text,
        'backend/agent.py default provider should remain "codex_bridge"',
    )
    errors += require(
        r"self\.codex_base_url = os\.environ\.get\(\"OPENAI_BASE_URL\", \"\"\)\.strip\(\)",
        text,
        "backend/agent.py must read OPENAI_BASE_URL directly",
    )
    errors += require(
        r"headers\[self\.codex_auth_header_name\] = self\.codex_auth_header_value",
        text,
        "backend/agent.py must forward OPENAI_AUTH_HEADER_* into bridge request headers",
    )
    errors += require(
        r"async for chunk in self\._run_codex_bridge\(",
        text,
        "backend/agent.py must route requests through bridge runtime",
    )
    errors += require(
        r"Missing bridge authentication: set OPENAI_AUTH_HEADER_\* or OPENAI_API_KEY",
        text,
        "backend/agent.py must include deterministic bridge auth diagnostic",
    )
    errors += require(
        r"async def _run_codex_bridge\(",
        text,
        "backend/agent.py must include codex bridge streaming runner",
    )
    # Ensure Claude runtime path is archived from active execution.
    if re.search(r"async def _run_claude\(", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not define _run_claude in bridge-only mode")
    if re.search(r"claude_agent_sdk", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not import claude_agent_sdk in bridge-only mode")
    if re.search(r"ANTHROPIC_", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not require Anthropic env vars in bridge-only mode")
    if re.search(r"LITELLM_", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not require LiteLLM-specific env vars in bridge-only mode")

    if errors:
        print("[error] Codex bridge config validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[ok] Codex bridge-only config is present and Claude runtime is archived.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
