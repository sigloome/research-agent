#!/usr/bin/env python3
"""Deterministic validation for single-provider codex-sdk runtime config."""

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
        r"self\.provider = \"codex_sdk\"",
        text,
        'backend/agent.py provider should be fixed to "codex_sdk"',
    )
    errors += require(
        r"async for chunk in self\._run_codex_sdk\(",
        text,
        "backend/agent.py must route requests through codex-sdk runtime",
    )
    # Ensure Claude runtime path is archived from active execution.
    if re.search(r"async def _run_claude\(", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not define _run_claude")
    if re.search(r"claude_agent_sdk", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not import claude_agent_sdk")
    if re.search(r"ANTHROPIC_", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not require Anthropic env vars")
    if re.search(r"LITELLM_", text, flags=re.MULTILINE | re.DOTALL):
        errors.append("backend/agent.py should not require LiteLLM-specific env vars")

    if errors:
        print("[error] codex-sdk runtime config validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[ok] codex-sdk single-provider config is present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
