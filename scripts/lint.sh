#!/bin/bash
set -e

echo "🔍 Linting Backend (Ruff)..."
ruff check .
ruff format --check .

echo "🔍 Validating OpenSpec proposal sections..."
python scripts/check_openspec_proposals.py

echo "🔍 Validating OpenSpec tasks BDD/TDD evidence..."
python scripts/check_openspec_tasks.py

echo "🔍 Validating OpenSpec design ownership/risk/metrics..."
python scripts/check_openspec_design.py

echo "🔍 Validating OpenSpec artifact retention..."
python scripts/check_openspec_retention.py

echo "🔍 Checking ownership policy..."
python scripts/check_ownership_policy.py

echo "🔍 Linting Frontend (ESLint)..."
cd frontend
npm run lint

echo "🔍 Checking Frontend Formatting (Prettier)..."
npm run format:check
cd ..

echo "🔍 Running executable BDD gate..."
pytest -q tests/backend/test_bdd_chat_flow.py

echo "✅ All checks passed!"
