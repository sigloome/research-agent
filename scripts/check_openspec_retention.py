#!/usr/bin/env python3
"""Validate OpenSpec change artifact retention and local run-log references."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = REPO_ROOT / "openspec" / "changes"
TRACKED_REQUIRED_FILES = ("proposal.md", "design.md", "tasks.md")
LOCAL_REFERENCE_TOKEN = "tmp/runs/evolution/"
CHANGE_INDEX_TOKEN = "tmp/runs/evolution/index.md"


def run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_changed_changes() -> List[Path]:
    """Return unique change directories touched in current git status."""
    out = run_git(["status", "--porcelain"])
    dirs: List[Path] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        rel = Path(path_text)
        if rel.match("openspec/changes/*/*"):
            change_name = rel.parts[2]
            if change_name == "archive" or change_name.startswith("_"):
                continue
            dirs.append(CHANGES_DIR / change_name)
    seen = set()
    unique = []
    for path in dirs:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def list_all_changes() -> List[Path]:
    if not CHANGES_DIR.exists():
        return []
    changes: List[Path] = []
    for entry in CHANGES_DIR.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == "archive" or entry.name.startswith("_"):
            continue
        changes.append(entry)
    return sorted(changes)


def _present_required_files(change_dir: Path) -> List[Path]:
    present: List[Path] = []
    for required in TRACKED_REQUIRED_FILES:
        path = change_dir / required
        if path.exists():
            present.append(path)
    return present


def validate_change(change_dir: Path, require_local_ref: bool) -> List[str]:
    errors: List[str] = []
    present = _present_required_files(change_dir)

    # Allow placeholder change dirs that have no tracked artifacts yet.
    if not present:
        return errors

    for required in TRACKED_REQUIRED_FILES:
        path = change_dir / required
        if not path.exists():
            errors.append(f"missing tracked artifact '{path.relative_to(REPO_ROOT)}'")

    if not require_local_ref:
        return errors

    has_local_ref = False
    for tracked in TRACKED_REQUIRED_FILES:
        path = change_dir / tracked
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if LOCAL_REFERENCE_TOKEN in text or CHANGE_INDEX_TOKEN in text:
            has_local_ref = True
            break

    if not has_local_ref:
        errors.append(
            "missing local-run-log reference; include "
            f"'{LOCAL_REFERENCE_TOKEN}' or '{CHANGE_INDEX_TOKEN}' in proposal/design/tasks"
        )

    return errors


def validate(changes: Iterable[Path], require_local_ref: bool) -> int:
    changes = list(changes)
    if not changes:
        print("No OpenSpec changes to validate for retention.")
        return 0

    has_error = False
    for change_dir in changes:
        errors = validate_change(change_dir, require_local_ref=require_local_ref)
        if not errors:
            print(f"[ok] {change_dir.relative_to(REPO_ROOT)}")
            continue
        has_error = True
        print(f"[error] {change_dir.relative_to(REPO_ROOT)}")
        for err in errors:
            print(f"  - {err}")

    if has_error:
        print(
            "\nOpenSpec retention validation failed. "
            "Ensure tracked artifacts are complete and local run-log references are present when required."
        )
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate OpenSpec change artifact retention requirements."
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Validate only changed OpenSpec change directories from git status.",
    )
    parser.add_argument(
        "--require-local-ref",
        action="store_true",
        help="Require tmp/runs/evolution references inside proposal/design/tasks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changes = list_changed_changes() if args.changed else list_all_changes()
    return validate(changes, require_local_ref=args.require_local_ref)


if __name__ == "__main__":
    sys.exit(main())
