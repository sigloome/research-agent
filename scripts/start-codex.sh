#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env.local ]; then
  echo "Missing .env.local"
  echo "Create .env.local (gitignored) with codex bridge settings:"
  echo "  AGENT_PROVIDER=codex_bridge"
  echo "  OPENAI_BASE_URL=..."
  echo "  OPENAI_MODEL=..."
  echo "  OPENAI_AUTH_HEADER_NAME=Byted-Authorization"
  echo "  OPENAI_AUTH_HEADER_VALUE=Bearer ..."
  exit 1
fi

./scripts/start.sh
