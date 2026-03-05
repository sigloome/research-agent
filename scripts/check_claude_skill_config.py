#!/usr/bin/env python3
"""Validate Claude Agent SDK skill auto-loading configuration."""

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
        r"setting_sources=\[\s*\"user\"\s*,\s*\"project\"\s*\]",
        text,
        'backend/agent.py must set setting_sources=["user", "project"] for SDK-native skills',
    )
    errors += require(
        r"allowed_tools=\[[^\]]*\"Skill\"[^\]]*\]",
        text,
        'backend/agent.py allowed_tools must include "Skill"',
    )
    errors += require(
        r"cwd=str\(self\.cwd\)",
        text,
        "backend/agent.py must set ClaudeAgentOptions cwd to project root (self.cwd)",
    )

    if errors:
        print("[error] Claude skill config validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[ok] Claude skill config is set for SDK-native automatic loading.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
