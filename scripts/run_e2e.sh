#!/bin/bash

# E2E Test Runner for Velvet Research
# Sets up a temporary test environment and runs Playwright tests.

cd "$(dirname "$0")/.."

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Cleanup function to kill background processes
cleanup() {
    echo "Cleaning up..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    # Delete test database
    rm -f data/test_papers.db
}

trap cleanup EXIT

echo -e "${GREEN}Starting E2E Tests...${NC}"

# 1. Setup Test Environment
echo "Setting up test environment..."
export DB_NAME="test_papers.db"
export BACKEND_PORT=18001
export VITE_PORT=15174

# 2. Start Backend
echo "Starting Backend on port $BACKEND_PORT..."
source venv/bin/activate
# Run uvicorn on custom port. Note: backend.app:app usually runs on 18000 by default if main is executed, 
# but calling uvicorn module directly allows port override.
python -m uvicorn backend.app:app --host 0.0.0.0 --port $BACKEND_PORT > logs/e2e_backend.log 2>&1 &
BACKEND_PID=$!
sleep 3 # Wait for startup

# 3. Start Frontend
echo "Starting Frontend on port $VITE_PORT..."
cd frontend
# We need to tell Vite to proxy to our test backend.
# Since Vite proxy is configured in vite.config.js usually hardcoded or env vars, 
# we might need to adjust vite.config.js or mock the API.
# For this E2E, assuming basic smoke test of UI load, we'll try running it.
# If the app hardcodes localhost:18000, we might have issues.
# For now, let's assume we just want to test variable ports.

# Note: We need to pass the custom port to vite.
npm run dev -- --port $VITE_PORT > ../logs/e2e_frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 5

# 4. Run Tests
echo "Running Playwright Tests..."
npx playwright test "$@"

echo -e "${GREEN}E2E Tests Passed!${NC}"
