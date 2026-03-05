#!/bin/sh
set -e

git config core.hooksPath .githooks
echo "Configured local git hooks path: .githooks"
echo "pre-commit hook is now active for this repository."
