#!/usr/bin/env python3
"""Validate OpenSpec design files include metrics/risk/rollback/ownership sections."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = REPO_ROOT / "openspec" / "changes"

REQUIRED_SECTIONS = (
    "## Risks / Trade-offs",
    "## Rollback Plan",
    "## Ownership",
    "## Metrics Instrumentation",
)

OWNERSHIP_TOKENS = ("owner", "reviewer", "oncall")
METRIC_TOKENS = ("metric", "source", "threshold", "window")


def run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_changed_designs() -> List[Path]:
    out = run_git(["status", "--porcelain"])
    files: List[Path] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        rel = Path(path_text)
        if rel.match("openspec/changes/*/design.md"):
            files.append(REPO_ROOT / rel)
    seen = set()
    unique = []
    for file in files:
        if file not in seen:
            unique.append(file)
            seen.add(file)
    return unique


def list_all_designs() -> List[Path]:
    if not CHANGES_DIR.exists():
        return []
    designs: List[Path] = []
    for design in CHANGES_DIR.glob("*/design.md"):
        if design.parent.name == "archive":
            continue
        designs.append(design)
    return sorted(designs)


def validate_design(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"missing file: {path.relative_to(REPO_ROOT)}"]

    text = path.read_text(encoding="utf-8")
    lower = text.lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section '{section}'")

    if "## Ownership" in text:
        for token in OWNERSHIP_TOKENS:
            if token not in lower:
                errors.append(f"ownership section missing '{token}'")

    if "## Metrics Instrumentation" in text:
        for token in METRIC_TOKENS:
            if token not in lower:
                errors.append(f"metrics section missing '{token}'")

    return errors


def validate(paths: Iterable[Path]) -> int:
    paths = list(paths)
    if not paths:
        print("No OpenSpec design files to validate.")
        return 0

    has_error = False
    for path in paths:
        errs = validate_design(path)
        if not errs:
            print(f"[ok] {path.relative_to(REPO_ROOT)}")
            continue
        has_error = True
        print(f"[error] {path.relative_to(REPO_ROOT)}")
        for err in errs:
            print(f"  - {err}")

    if has_error:
        print(
            "\nOpenSpec design validation failed. "
            "Add required risk/rollback/ownership/metrics sections."
        )
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate required sections in OpenSpec design files."
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Validate changed/untracked design files from git status only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = list_changed_designs() if args.changed else list_all_designs()
    return validate(targets)


if __name__ == "__main__":
    sys.exit(main())
