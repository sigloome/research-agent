#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT_DIR/.codex/skills/todo-orchestrator/SKILL.md"
RUNTIME_TARGET="$ROOT_DIR/skills/todo-orchestrator/SKILL.md"

if [[ ! -f "$CANONICAL" ]]; then
  echo "Canonical skill file missing: $CANONICAL"
  exit 1
fi

mkdir -p "$(dirname "$RUNTIME_TARGET")"
cp "$CANONICAL" "$RUNTIME_TARGET"

echo "Synced:"
echo "- $CANONICAL -> $RUNTIME_TARGET"
