#!/usr/bin/env python3
"""Validate OpenSpec proposal files include mandatory rationale/metrics sections."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = REPO_ROOT / "openspec" / "changes"

REQUIRED_SECTIONS = (
    "## Why",
    "## What Changes",
    "## Expected Benefit",
    "## Success Metrics",
    "## Risk Metrics",
    "## Kill Criteria",
)


def run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_changed_proposals() -> List[Path]:
    """Return unique changed/untracked proposal files under openspec/changes."""
    out = run_git(["status", "--porcelain"])
    files: List[Path] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_text = line[3:].strip()
        # Handle rename records like "old -> new".
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        rel = Path(path_text)
        if rel.match("openspec/changes/*/proposal.md"):
            files.append(REPO_ROOT / rel)
    # Stable de-dup while preserving order.
    seen = set()
    unique = []
    for file in files:
        if file not in seen:
            unique.append(file)
            seen.add(file)
    return unique


def list_all_proposals() -> List[Path]:
    if not CHANGES_DIR.exists():
        return []
    proposals: List[Path] = []
    for proposal in CHANGES_DIR.glob("*/proposal.md"):
        if proposal.parent.name == "archive":
            continue
        proposals.append(proposal)
    return sorted(proposals)


def validate_proposal(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"missing file: {path.relative_to(REPO_ROOT)}"]

    text = path.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section '{section}'")
    return errors


def validate(paths: Iterable[Path]) -> int:
    paths = list(paths)
    if not paths:
        print("No OpenSpec proposal files to validate.")
        return 0

    has_error = False
    for path in paths:
        errs = validate_proposal(path)
        if not errs:
            print(f"[ok] {path.relative_to(REPO_ROOT)}")
            continue
        has_error = True
        print(f"[error] {path.relative_to(REPO_ROOT)}")
        for err in errs:
            print(f"  - {err}")

    if has_error:
        print(
            "\nOpenSpec proposal validation failed. "
            "Use openspec/changes/_templates/proposal.md as baseline."
        )
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate required sections in OpenSpec proposals."
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Validate changed/untracked proposals from git status only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = list_changed_proposals() if args.changed else list_all_proposals()
    return validate(targets)


if __name__ == "__main__":
    sys.exit(main())
