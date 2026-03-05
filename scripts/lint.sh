#!/bin/bash
set -e

echo "🔍 Linting Backend (Ruff)..."
ruff check .
ruff format --check .

echo "🔍 Validating OpenSpec proposal sections..."
python scripts/check_openspec_proposals.py

echo "🔍 Validating OpenSpec tasks BDD/TDD evidence..."
python scripts/check_openspec_tasks.py

echo "🔍 Linting Frontend (ESLint)..."
cd frontend
npm run lint

echo "🔍 Checking Frontend Formatting (Prettier)..."
npm run format:check

echo "✅ All checks passed!"
