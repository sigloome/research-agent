#!/bin/bash
cd "$(dirname "$0")/.."
# Start script for Velvet Research

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Load environment variables from .env
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Load NVM for Node.js
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Create logs directory if needed
mkdir -p logs

# Start backend in background (from project root, using backend module)
echo "Starting backend on port 18000..."
python -m uvicorn backend.app:app --host 0.0.0.0 --port 18000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
echo "Starting frontend on port 18001..."
cd frontend
export npm_config_cache=$(pwd)/../.npm-cache
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend: http://localhost:18000"
echo "Frontend: http://localhost:18001"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
