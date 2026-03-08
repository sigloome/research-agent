#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
TODOS_DIR="$ROOT_DIR/tmp/todos"
IDEAS_DIR="$ROOT_DIR/tmp/proposals/ideas"
ACTIVE_FILE="$TODOS_DIR/active.md"
HANDOFF_FILE="$TODOS_DIR/handoff.md"

TITLE=""
PRIORITY="P1"
IDEA=""
BENEFIT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE="$2"; shift 2 ;;
    --priority) PRIORITY="$2"; shift 2 ;;
    --idea) IDEA="$2"; shift 2 ;;
    --benefit) BENEFIT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$TITLE" || -z "$IDEA" ]]; then
  echo "Usage: $0 --title <title> [--priority P0|P1|P2] --idea <idea text> [--benefit <benefit>]"
  exit 1
fi

mkdir -p "$TODOS_DIR" "$IDEAS_DIR"

TS="$(date +"%Y%m%d-%H%M%S")"
SLUG="$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
IDEA_FILE="$IDEAS_DIR/$TS-$SLUG.md"

cat > "$IDEA_FILE" <<EON
# Idea Survey & Design Note

- Title: $TITLE
- Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- Priority: $PRIORITY

## Idea

$IDEA

## Why

(Describe problem/pain this idea addresses.)

## Expected Benefit

${BENEFIT:-"(Add measurable project benefit.)"}

## Candidate Metrics

1. Success metric:
2. Risk metric:
3. Rollback trigger:

## Design Notes

(Implementation sketch, dependencies, risks.)
EON

if [[ ! -f "$ACTIVE_FILE" ]]; then
  cat > "$ACTIVE_FILE" <<EON
# Active Backlog (Local)

Last updated: $(date +"%Y-%m-%d")

## P0 - Next Implementation Features

## P1 - Quality and Safety Hardening

## P2 - Repo Governance Enhancements
EON
fi

ENTRY="- [ ] $TITLE  \\
  - Idea note: $IDEA_FILE  \\
  - Reason: $IDEA  \\
  - Expected benefit: ${BENEFIT:-TBD}"

awk -v prio="## $PRIORITY" -v entry="$ENTRY" '
  BEGIN { inserted=0 }
  {
    print $0
    if (!inserted && index($0, prio)==1) {
      print ""
      print entry
      inserted=1
    }
  }
  END {
    if (!inserted) {
      print ""
      print "## " prio
      print ""
      print entry
    }
  }
' "$ACTIVE_FILE" > "$ACTIVE_FILE.tmp" && mv "$ACTIVE_FILE.tmp" "$ACTIVE_FILE"

if [[ -f "$HANDOFF_FILE" ]]; then
  {
    echo ""
    echo "## New Idea Added"
    echo "- $TITLE ($PRIORITY)"
    echo "- Note: $IDEA_FILE"
  } >> "$HANDOFF_FILE"
fi

echo "Added idea: $TITLE"
echo "Idea note: $IDEA_FILE"
echo "Backlog updated: $ACTIVE_FILE"
