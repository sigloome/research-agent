#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT_DIR/.codex/skills/todo-orchestrator/SKILL.md"
CLAUDE_TARGET="$ROOT_DIR/.claude/skills/todo-orchestrator/SKILL.md"

if [[ ! -f "$CANONICAL" ]]; then
  echo "Canonical skill file missing: $CANONICAL"
  exit 1
fi

mkdir -p "$(dirname "$CLAUDE_TARGET")"
cp "$CANONICAL" "$CLAUDE_TARGET"

echo "Synced:"
echo "- $CANONICAL -> $CLAUDE_TARGET"
