#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
REPORT_PATH="$RUNS_DIR/$TIMESTAMP.md"
INDEX_PATH="$RUNS_DIR/index.md"
LIVE_BENCH_CMD="$ROOT_DIR/scripts/run_live_benchmark.sh"

mkdir -p "$RUNS_DIR"

status="PASS"
soft_warn_count=0
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

run_soft_warning_step() {
  local name="$1"
  local cmd="$2"
  echo "- [ ] $name" >>"$REPORT_PATH"
  echo "Running (soft-warning): $name"
  if bash -lc "$cmd" >>"$REPORT_PATH" 2>&1; then
    perl -0pi -e "s/- \\[ \\] \Q$name\E/- [x] $name/" "$REPORT_PATH"
    echo "  ok"
  else
    perl -0pi -e "s/- \\[ \\] \Q$name\E/- [!] $name/" "$REPORT_PATH"
    soft_warn_count=$((soft_warn_count + 1))
    echo "" >>"$REPORT_PATH"
    echo "### Soft warning: $name" >>"$REPORT_PATH"
    echo "- Command: \`$cmd\`" >>"$REPORT_PATH"
    echo "- Note: non-blocking failure; deterministic result unchanged." >>"$REPORT_PATH"
    echo "" >>"$REPORT_PATH"
    echo "  warning (non-blocking)"
  fi
}

{
  run_step "OpenSpec proposal validation" "python $ROOT_DIR/scripts/check_openspec_proposals.py"
  run_step "OpenSpec tasks validation" "python $ROOT_DIR/scripts/check_openspec_tasks.py"
  run_step "OpenSpec design validation" "python $ROOT_DIR/scripts/check_openspec_design.py"
  run_step "OpenSpec retention validation" "python $ROOT_DIR/scripts/check_openspec_retention.py"
  run_step "Codex SDK config validation" "python $ROOT_DIR/scripts/check_codex_sdk_config.py"
  run_step "Runtime skill accessibility validation" "python $ROOT_DIR/scripts/check_skill_runtime_access.py"
  run_step "Deterministic eval suite (PR profile)" "python -m evals.runners.run_suite --suite pr --judge-rate 0.15 --k 1"
  run_step "Deterministic eval tests" "pytest -q evals/tests/test_retrieval_prompt_paths.py -q"
} || true

{
  echo
  echo "## Live Benchmark (Non-Blocking)"
  echo
} >>"$REPORT_PATH"

if [[ -x "$LIVE_BENCH_CMD" ]]; then
  run_soft_warning_step "Live benchmark run" "$LIVE_BENCH_CMD"
else
  soft_warn_count=$((soft_warn_count + 1))
  {
    echo "- [!] Live benchmark run"
    echo
    echo "### Soft warning: Live benchmark run"
    echo "- Command: \`$LIVE_BENCH_CMD\`"
    echo "- Note: script missing or not executable; non-blocking."
    echo
  } >>"$REPORT_PATH"
  echo "soft warning: live benchmark script missing/non-executable"
fi

end_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  echo
  echo "## Summary"
  echo
  echo "- Result: **$status**"
  echo "- Soft warnings (non-blocking): **$soft_warn_count**"
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

if [[ -x "$ROOT_DIR/scripts/trigger_evolution.sh" ]]; then
  "$ROOT_DIR/scripts/trigger_evolution.sh" "$status" "$REPORT_PATH" "run_evolution_cycle"
fi

if [[ -x "$ROOT_DIR/scripts/promotion_workflow.sh" ]]; then
  "$ROOT_DIR/scripts/promotion_workflow.sh" || true
fi

if [[ "$status" != "PASS" ]]; then
  exit 1
fi
