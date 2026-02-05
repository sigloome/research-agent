#!/bin/bash
set -e

echo "🔍 Linting Backend (Ruff)..."
ruff check .
ruff format --check .

echo "🔍 Linting Frontend (ESLint)..."
cd frontend
npm run lint

echo "🔍 Checking Frontend Formatting (Prettier)..."
npm run format:check

echo "✅ All checks passed!"
