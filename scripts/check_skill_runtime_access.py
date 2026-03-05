#!/usr/bin/env python3
"""Deterministically verify runtime skill discovery/read path for required skills."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    try:
        core = importlib.import_module("skills.skill-management.core")
    except Exception as exc:
        print(f"[error] failed to import skills.skill-management.core: {exc}")
        return 1

    required = ["knowledge", "preference"]
    errors: list[str] = []

    skills = core.list_skills()
    if not isinstance(skills, list):
        print("[error] list_skills() did not return a list")
        return 1

    names = {str(s.get("name", "")) for s in skills if isinstance(s, dict)}
    print(f"[info] discovered skills: {len(skills)}")

    for name in required:
        if name not in names:
            errors.append(f"required skill not discoverable via list_skills(): {name}")

    read_targets = {
        "knowledge": ["knowledge", "skills/knowledge/SKILL.md"],
        "preference": ["preference", "skills/preference/SKILL.md"],
    }

    read_status: dict[str, dict[str, str]] = {}
    for skill_name, targets in read_targets.items():
        read_status[skill_name] = {}
        for target in targets:
            content = core.read_skill(target)
            ok = isinstance(content, str) and bool(content.strip()) and not content.startswith("Error:")
            read_status[skill_name][target] = "ok" if ok else "fail"
            if not ok:
                errors.append(f"read_skill('{target}') failed")

    print("[info] runtime read status:")
    print(json.dumps(read_status, indent=2, ensure_ascii=False))

    if errors:
        print("[error] runtime skill accessibility validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[ok] required runtime skills are discoverable and readable: knowledge, preference")
    return 0


if __name__ == "__main__":
    sys.exit(main())
