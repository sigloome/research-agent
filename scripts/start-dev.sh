#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

BACKEND_PORT="${BACKEND_PORT:-18000}"
FRONTEND_PORT="${FRONTEND_PORT:-18001}"

cleanup_listeners() {
  local port="$1"
  # Clear stale listeners from previous runs to avoid duplicate/HMR nondeterminism.
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
  if [ -n "$pids" ]; then
    echo "Cleaning existing listeners on :$port -> $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

# Activate virtual environment if it exists.
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Load environment variables from .env and optional .env.local overrides.
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

if [ -f .env.local ]; then
  set -a
  source .env.local
  set +a
fi

# Load NVM for Node.js if present.
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

mkdir -p logs

# Ensure deterministic single-listener state before launching.
cleanup_listeners "$BACKEND_PORT"
cleanup_listeners "$FRONTEND_PORT"

echo "Starting backend (hot reload) on port ${BACKEND_PORT}..."
python -m uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port "$BACKEND_PORT" \
  --reload \
  --reload-dir backend \
  --reload-dir skills \
  > logs/backend.dev.log 2>&1 &
BACKEND_PID=$!

sleep 1

echo "Starting frontend (Vite HMR) on port ${FRONTEND_PORT}..."
cd frontend
export npm_config_cache="$(pwd)/../.npm-cache"
npm run dev -- --port "$FRONTEND_PORT" > ../logs/frontend.dev.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "Running listener sanity check..."
if ! BACKEND_PORT="$BACKEND_PORT" FRONTEND_PORT="$FRONTEND_PORT" scripts/check_dev_listener_sanity.sh; then
  echo "Listener sanity failed right after startup; stopping services."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  cleanup_listeners "$BACKEND_PORT"
  cleanup_listeners "$FRONTEND_PORT"
  exit 1
fi

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend:  http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Logs: logs/backend.dev.log, logs/frontend.dev.log"
echo ""
echo "Press Ctrl+C to stop both servers"

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  cleanup_listeners "$BACKEND_PORT"
  cleanup_listeners "$FRONTEND_PORT"
}

trap cleanup SIGINT SIGTERM EXIT
wait
