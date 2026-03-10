#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHANGES_DIR="$ROOT_DIR/openspec/changes"
TEMPLATE_DIR="$CHANGES_DIR/_templates"
RUN_INDEX="$ROOT_DIR/tmp/runs/evolution/index.md"

usage() {
  cat <<'EOF'
Usage:
  scripts/new_evolution_change.sh <change-id> [title]

Example:
  scripts/new_evolution_change.sh fix-stream-contract "Fix stream contract regressions"
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

CHANGE_ID="$1"
TITLE="${2:-$CHANGE_ID}"
CHANGE_DIR="$CHANGES_DIR/$CHANGE_ID"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "missing template dir: $TEMPLATE_DIR" >&2
  exit 1
fi

if [[ -e "$CHANGE_DIR" ]]; then
  echo "change already exists: $CHANGE_DIR" >&2
  exit 1
fi

mkdir -p "$CHANGE_DIR/specs"
cp "$TEMPLATE_DIR/proposal.md" "$CHANGE_DIR/proposal.md"
cp "$TEMPLATE_DIR/design.md" "$CHANGE_DIR/design.md"
cp "$TEMPLATE_DIR/tasks.md" "$CHANGE_DIR/tasks.md"

now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

append_if_missing() {
  local file="$1"
  local needle="$2"
  local block="$3"
  if ! grep -Fq "$needle" "$file"; then
    printf "\n%s\n" "$block" >>"$file"
  fi
}

append_if_missing "$CHANGE_DIR/proposal.md" "## Metadata" "## Metadata

- Change ID: \`$CHANGE_ID\`
- Title: $TITLE
- Created At (UTC): $now_utc"

append_if_missing "$CHANGE_DIR/proposal.md" "tmp/runs/evolution/index.md" "## Evolution Run Context

- Latest run index: \`tmp/runs/evolution/index.md\`
- Latest run report: \`tmp/runs/evolution/<timestamp>.md\`"

append_if_missing "$CHANGE_DIR/design.md" "## Evolution Run Context" "## Evolution Run Context

- Linked run index: \`tmp/runs/evolution/index.md\`
- Linked run report: \`tmp/runs/evolution/<timestamp>.md\`"

append_if_missing "$CHANGE_DIR/tasks.md" "## Evolution Run Context" "## Evolution Run Context

- Linked run index: \`tmp/runs/evolution/index.md\`
- Linked run report: \`tmp/runs/evolution/<timestamp>.md\`"

echo "created OpenSpec change scaffold:"
echo "  - $CHANGE_DIR/proposal.md"
echo "  - $CHANGE_DIR/design.md"
echo "  - $CHANGE_DIR/tasks.md"
echo "  - $CHANGE_DIR/specs/"
echo "note: update placeholders and replace <timestamp> with a real report path."
