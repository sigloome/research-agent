#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env.local ]; then
  echo "Missing .env.local"
  echo "Create .env.local (gitignored) with codex sdk runtime settings:"
  echo "  AGENT_PROVIDER=codex_sdk"
  echo "  OPENAI_MODEL=gpt-5.3-codex"
  echo "  # Optional: CODEX_SDK_MODEL=... (legacy CODEX_EXEC_MODEL also supported)"
  exit 1
fi

./scripts/start.sh
