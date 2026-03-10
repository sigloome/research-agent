#!/bin/sh
set -e

git config core.hooksPath .githooks
echo "Configured local git hooks path: .githooks"
echo "pre-commit and pre-push hooks are now active for this repository."
