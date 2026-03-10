#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
INDEX_PATH="$RUNS_DIR/index.md"
HANDOFF_PATH="$ROOT_DIR/tmp/todos/handoff.md"
SCAFFOLD_SCRIPT="$ROOT_DIR/scripts/new_evolution_change.sh"
CANDIDATE_SCRIPT="$ROOT_DIR/scripts/generate_evolution_candidates.sh"

mkdir -p "$RUNS_DIR"
touch "$INDEX_PATH"

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/trigger_evolution.sh <PASS|FAIL> [report-path] [reason]" >&2
  exit 1
fi

RESULT="$(echo "$1" | tr '[:lower:]' '[:upper:]')"
REPORT_PATH="${2:-}"
REASON="${3:-auto-triggered from evolution cycle}"

if [[ "$RESULT" != "PASS" && "$RESULT" != "FAIL" ]]; then
  echo "first arg must be PASS or FAIL" >&2
  exit 1
fi

timestamp="$(date +"%Y%m%d-%H%M%S")"
change_id="auto-evo-${timestamp}"
change_created="false"
candidate_path=""

if [[ "$RESULT" == "FAIL" ]]; then
  if [[ -x "$SCAFFOLD_SCRIPT" ]]; then
    "$SCAFFOLD_SCRIPT" "$change_id" "Auto evolution follow-up: ${REASON}" >/dev/null
    change_created="true"
  else
    echo "warning: scaffold script not executable: $SCAFFOLD_SCRIPT" >&2
  fi

  if [[ -x "$CANDIDATE_SCRIPT" ]]; then
    if output="$("$CANDIDATE_SCRIPT" --report "${REPORT_PATH:-}" --change-id "$change_id" 2>&1)"; then
      candidate_path="$(echo "$output" | awk '/^candidate list generated: / {sub(/^candidate list generated: /, "", $0); print $0}' | tail -n 1)"
    else
      echo "warning: candidate generation failed" >&2
      echo "$output" >&2
    fi
  else
    echo "warning: candidate script not executable: $CANDIDATE_SCRIPT" >&2
  fi
fi

if [[ ! -f "$INDEX_PATH" ]]; then
  {
    echo "# Evolution Run Index"
    echo
    echo "| Timestamp | Result | Report |"
    echo "|---|---|---|"
  } >"$INDEX_PATH"
fi

summary_report="${REPORT_PATH:-$RUNS_DIR/${timestamp}.md}"
{
  echo
  echo "## Evolution Trigger Summary ($timestamp)"
  echo
  echo "- Result: \`$RESULT\`"
  echo "- Reason: $REASON"
  echo "- Report: \`$summary_report\`"
  if [[ "$change_created" == "true" ]]; then
    echo "- Auto-created change: \`openspec/changes/$change_id/\`"
  else
    echo "- Auto-created change: none"
  fi
  if [[ -n "$candidate_path" ]]; then
    echo "- Auto-generated candidate list: \`$candidate_path\`"
  else
    echo "- Auto-generated candidate list: none"
  fi
} >>"$INDEX_PATH"

if [[ -f "$HANDOFF_PATH" ]]; then
  {
    echo
    echo "## Evolution Trigger Update ($timestamp)"
    echo
    echo "- Result: \`$RESULT\`"
    echo "- Reason: $REASON"
    if [[ "$change_created" == "true" ]]; then
      echo "- New follow-up change scaffolded: \`openspec/changes/$change_id/\`"
      if [[ -n "$candidate_path" ]]; then
        echo "- Candidate task list generated: \`$candidate_path\`"
      fi
      echo "- Immediate next task: review candidate list, approve one scoped task, then implement under SDD->BDD->TDD order."
    else
      echo "- No new change scaffolded."
    fi
  } >>"$HANDOFF_PATH"
fi

if [[ "$RESULT" == "FAIL" ]]; then
  echo "triggered follow-up for failure: $change_id"
else
  echo "no trigger action required for PASS"
fi
