#!/usr/bin/env python3
"""Backward-compatible wrapper for runtime agent config validation.

This script name is kept for compatibility with existing hooks/scripts,
but validation now targets codex-bridge runtime requirements.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    checks = [
        ["python3", str(REPO_ROOT / "scripts" / "check_codex_bridge_config.py")],
        ["python3", str(REPO_ROOT / "scripts" / "check_skill_runtime_access.py")],
    ]
    for cmd in checks:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if result.returncode != 0:
            return result.returncode

    print(
        "[ok] Legacy check alias passed using codex-bridge runtime validations."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
