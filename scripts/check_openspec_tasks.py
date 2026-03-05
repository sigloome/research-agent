#!/usr/bin/env python3
"""Validate OpenSpec tasks files include BDD/TDD evidence sections."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = REPO_ROOT / "openspec" / "changes"

REQUIRED_SECTIONS = (
    "## BDD Evidence",
    "## TDD Evidence",
)

BDD_MIN_TOKENS = ("given", "when", "then")
TDD_MIN_TOKENS = ("failing test", "implemented", "passing")


def run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_changed_tasks() -> List[Path]:
    out = run_git(["status", "--porcelain"])
    files: List[Path] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        rel = Path(path_text)
        if rel.match("openspec/changes/*/tasks.md"):
            files.append(REPO_ROOT / rel)
    seen = set()
    unique = []
    for file in files:
        if file not in seen:
            unique.append(file)
            seen.add(file)
    return unique


def list_all_tasks() -> List[Path]:
    if not CHANGES_DIR.exists():
        return []
    tasks: List[Path] = []
    for task_file in CHANGES_DIR.glob("*/tasks.md"):
        if task_file.parent.name == "archive":
            continue
        tasks.append(task_file)
    return sorted(tasks)


def validate_tasks(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"missing file: {path.relative_to(REPO_ROOT)}"]

    text = path.read_text(encoding="utf-8")
    lower = text.lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section '{section}'")

    if "## BDD Evidence" in text:
        for token in BDD_MIN_TOKENS:
            if token not in lower:
                errors.append(
                    f"BDD evidence must include Given/When/Then phrasing (missing '{token}')"
                )

    if "## TDD Evidence" in text:
        for token in TDD_MIN_TOKENS:
            if token not in lower:
                errors.append(
                    "TDD evidence must include failing->implemented->passing trace "
                    f"(missing '{token}')"
                )

    return errors


def validate(paths: Iterable[Path]) -> int:
    paths = list(paths)
    if not paths:
        print("No OpenSpec tasks files to validate.")
        return 0

    has_error = False
    for path in paths:
        errs = validate_tasks(path)
        if not errs:
            print(f"[ok] {path.relative_to(REPO_ROOT)}")
            continue
        has_error = True
        print(f"[error] {path.relative_to(REPO_ROOT)}")
        for err in errs:
            print(f"  - {err}")

    if has_error:
        print("\nOpenSpec tasks validation failed. Add BDD/TDD evidence sections to each tasks.md.")
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate required BDD/TDD evidence sections in OpenSpec tasks."
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Validate changed/untracked tasks files from git status only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = list_changed_tasks() if args.changed else list_all_tasks()
    return validate(targets)


if __name__ == "__main__":
    sys.exit(main())
