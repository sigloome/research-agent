#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACK_DIR="$ROOT_DIR/tmp/interview_pack"
BENCH_SCRIPT="$PACK_DIR/scripts/eval_e2e.sh"

if [[ ! -x "$BENCH_SCRIPT" ]]; then
  echo "live benchmark script not found or not executable: $BENCH_SCRIPT" >&2
  exit 1
fi

# Pass through environment variables and args.
"$BENCH_SCRIPT" "$@"
