#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

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

echo "Starting backend (hot reload) on port 18000..."
python -m uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 18000 \
  --reload \
  --reload-dir backend \
  --reload-dir skills \
  > logs/backend.dev.log 2>&1 &
BACKEND_PID=$!

sleep 1

echo "Starting frontend (Vite HMR) on port 18001..."
cd frontend
export npm_config_cache="$(pwd)/../.npm-cache"
npm run dev > ../logs/frontend.dev.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend:  http://localhost:18000"
echo "Frontend: http://localhost:18001"
echo "Logs: logs/backend.dev.log, logs/frontend.dev.log"
echo ""
echo "Press Ctrl+C to stop both servers"

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM EXIT
wait
