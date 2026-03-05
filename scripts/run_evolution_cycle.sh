#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
REPORT_PATH="$RUNS_DIR/$TIMESTAMP.md"
INDEX_PATH="$RUNS_DIR/index.md"

mkdir -p "$RUNS_DIR"

status="PASS"
start_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  echo "# Evolution Cycle Report"
  echo
  echo "- Timestamp: $TIMESTAMP"
  echo "- Started (UTC): $start_iso"
  echo "- Workspace: $ROOT_DIR"
  echo
  echo "## Checks"
  echo
} >"$REPORT_PATH"

run_step() {
  local name="$1"
  local cmd="$2"
  echo "- [ ] $name" >>"$REPORT_PATH"
  echo "Running: $name"
  if bash -lc "$cmd" >>"$REPORT_PATH" 2>&1; then
    perl -0pi -e "s/- \\[ \\] \Q$name\E/- [x] $name/" "$REPORT_PATH"
    echo "  ok"
  else
    status="FAIL"
    echo "" >>"$REPORT_PATH"
    echo "### Failure: $name" >>"$REPORT_PATH"
    echo "- Command: \`$cmd\`" >>"$REPORT_PATH"
    echo "" >>"$REPORT_PATH"
    return 1
  fi
}

{
  run_step "OpenSpec proposal validation" "python $ROOT_DIR/scripts/check_openspec_proposals.py"
  run_step "OpenSpec tasks validation" "python $ROOT_DIR/scripts/check_openspec_tasks.py"
  run_step "OpenSpec design validation" "python $ROOT_DIR/scripts/check_openspec_design.py"
  run_step "OpenSpec retention validation" "python $ROOT_DIR/scripts/check_openspec_retention.py"
  run_step "Claude skill auto-load config validation" "python $ROOT_DIR/scripts/check_claude_skill_config.py"
  run_step "Deterministic eval suite (PR profile)" "python -m evals.runners.run_suite --suite pr --judge-rate 0.15 --k 1"
  run_step "Deterministic eval tests" "pytest -q evals/tests/test_retrieval_prompt_paths.py -q"
} || true

end_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  echo
  echo "## Summary"
  echo
  echo "- Result: **$status**"
  echo "- Finished (UTC): $end_iso"
  echo
} >>"$REPORT_PATH"

if [[ ! -f "$INDEX_PATH" ]]; then
  {
    echo "# Evolution Run Index"
    echo
    echo "| Timestamp | Result | Report |"
    echo "|---|---|---|"
  } >"$INDEX_PATH"
fi

echo "| $TIMESTAMP | $status | $REPORT_PATH |" >>"$INDEX_PATH"

echo "Evolution cycle complete: $status"
echo "Report: $REPORT_PATH"
echo "Index:  $INDEX_PATH"

if [[ "$status" != "PASS" ]]; then
  exit 1
fi
