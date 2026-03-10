#!/usr/bin/env python3
"""Deterministically validate ownership section tokens in active OpenSpec designs."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CHANGES = ROOT / "openspec" / "changes"
TOKENS = ("owner", "reviewer", "oncall")


def active_designs():
    for p in sorted(CHANGES.glob("*/design.md")):
        if p.parent.name == "archive" or p.parent.name.startswith("_"):
            continue
        yield p


def main() -> int:
    failed = False
    seen = 0
    for design in active_designs():
        seen += 1
        text = design.read_text(encoding="utf-8").lower()
        missing = [t for t in TOKENS if t not in text]
        if missing:
            failed = True
            rel = design.relative_to(ROOT)
            print(f"[error] {rel}: missing {', '.join(missing)}")
        else:
            print(f"[ok] {design.relative_to(ROOT)}")

    if seen == 0:
        print("No active OpenSpec designs found.")
        return 0

    if failed:
        print("\nownership policy check failed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
