#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
INDEX_PATH="$RUNS_DIR/index.md"
OUT_DIR="$RUNS_DIR/candidates"
HANDOFF_PATH="$ROOT_DIR/todos/handoff.md"

mkdir -p "$RUNS_DIR" "$OUT_DIR"

usage() {
  cat <<'EOF'
Usage:
  scripts/generate_evolution_candidates.sh [--report <path>] [--change-id <id>] [--approve]

Behavior:
  1) Validate OpenSpec artifacts.
  2) Run deterministic checks.
  3) Generate implementation candidate task list in tmp/runs/evolution/candidates/.

Notes:
  - This script does NOT modify product code.
  - Human approval is mandatory before any code-changing follow-up steps.
EOF
}

REPORT_PATH=""
CHANGE_ID=""
APPROVED="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report)
      REPORT_PATH="${2:-}"
      shift 2
      ;;
    --change-id)
      CHANGE_ID="${2:-}"
      shift 2
      ;;
    --approve)
      APPROVED="true"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

latest_report() {
  find "$RUNS_DIR" -maxdepth 1 -type f -name "*.md" ! -name "index.md" | sort | tail -n 1
}

if [[ -z "$REPORT_PATH" ]]; then
  REPORT_PATH="$(latest_report || true)"
fi

if [[ -z "$REPORT_PATH" || ! -f "$REPORT_PATH" ]]; then
  echo "no evolution report found; pass --report <path>" >&2
  exit 1
fi

if [[ -z "$CHANGE_ID" ]]; then
  CHANGE_ID="$(find "$ROOT_DIR/openspec/changes" -maxdepth 1 -type d -name "auto-evo-*" | sort | tail -n 1 | xargs -I{} basename "{}" || true)"
fi

if [[ -z "$CHANGE_ID" ]]; then
  CHANGE_ID="(not-selected)"
fi

timestamp="$(date +"%Y%m%d-%H%M%S")"
OUT_PATH="$OUT_DIR/${timestamp}.md"

artifact_status="PASS"
det_status="PASS"

run_check() {
  local label="$1"
  local cmd="$2"
  if bash -lc "$cmd" >/tmp/evo-candidate-check.log 2>&1; then
    echo "- [x] $label"
  else
    echo "- [ ] $label"
    echo "  - failed command: \`$cmd\`"
    echo "  - tail:"
    tail -n 40 /tmp/evo-candidate-check.log | sed 's/^/    /'
    return 1
  fi
}

extract_failures() {
  awk '
    /^### Failure:/ {
      sub(/^### Failure: /, "", $0);
      print $0;
    }
  ' "$REPORT_PATH"
}

map_failure_to_task() {
  local failure="$1"
  case "$failure" in
    *proposal*)
      echo "Update OpenSpec proposal mandatory sections and numeric metrics for affected change."
      ;;
    *tasks*)
      echo "补齐 tasks.md 的 BDD/TDD 证据并映射到可执行测试命令。"
      ;;
    *design*)
      echo "Fill design ownership/risk/rollback/metrics instrumentation with concrete thresholds."
      ;;
    *retention*)
      echo "Promote behavior-impacting local notes into tracked OpenSpec artifacts before merge."
      ;;
    *Deterministic*|*eval*)
      echo "Fix deterministic contract regressions and make eval suite green locally."
      ;;
    *skill*|*bridge*)
      echo "Repair runtime skill/bridge contract path and re-verify stream/tool events."
      ;;
    *)
      echo "Triaged failure '$failure' and define a minimal reproducible fix task with test evidence."
      ;;
  esac
}

{
  echo "# Evolution Candidate Task List"
  echo
  echo "- Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Source report: \`$REPORT_PATH\`"
  echo "- Target change: \`$CHANGE_ID\`"
  echo "- Index: \`$INDEX_PATH\`"
  echo
  echo "## Stage 1: Artifact Validation"
  echo
} >"$OUT_PATH"

{
  if ! run_check "OpenSpec proposal validation" "python $ROOT_DIR/scripts/check_openspec_proposals.py"; then
    artifact_status="FAIL"
  fi
  if ! run_check "OpenSpec tasks validation" "python $ROOT_DIR/scripts/check_openspec_tasks.py"; then
    artifact_status="FAIL"
  fi
  if ! run_check "OpenSpec design validation" "python $ROOT_DIR/scripts/check_openspec_design.py"; then
    artifact_status="FAIL"
  fi
  if ! run_check "OpenSpec retention validation" "python $ROOT_DIR/scripts/check_openspec_retention.py"; then
    artifact_status="FAIL"
  fi
} >>"$OUT_PATH"

{
  echo
  echo "## Stage 2: Deterministic Verification"
  echo
} >>"$OUT_PATH"

{
  if ! run_check "Executable BDD gate" "pytest -q $ROOT_DIR/tests/backend/test_bdd_chat_flow.py"; then
    det_status="FAIL"
  fi
  if ! run_check "Deterministic eval suite" "pytest -q $ROOT_DIR/evals/tests/test_retrieval_prompt_paths.py $ROOT_DIR/evals/tests/test_retrieval_prompt_paths_audit.py"; then
    det_status="FAIL"
  fi
} >>"$OUT_PATH"

{
  echo
  echo "## Stage 3: Candidate Implementation Tasks (Manual-Assisted)"
  echo
  echo "Generated from failure markers in source report."
  echo
} >>"$OUT_PATH"

failures="$(extract_failures || true)"
task_count=0
if [[ -n "$failures" ]]; then
  while IFS= read -r item; do
    [[ -z "$item" ]] && continue
    task_count=$((task_count + 1))
    mapped="$(map_failure_to_task "$item")"
    {
      echo "$task_count. Failure: \`$item\`"
      echo "   - Candidate action: $mapped"
      echo "   - Verification: rerun \`scripts/run_evolution_cycle.sh\` and ensure no failure block remains."
    } >>"$OUT_PATH"
  done <<<"$failures"
fi

if [[ "$task_count" -eq 0 ]]; then
  {
    echo "1. No explicit failure blocks found in source report."
    echo "   - Candidate action: inspect drift/risk metrics and create one scoped hardening task."
    echo "   - Verification: deterministic gates remain green after change."
  } >>"$OUT_PATH"
fi

{
  echo
  echo "## Summary"
  echo
  echo "- Artifact status: **$artifact_status**"
  echo "- Deterministic status: **$det_status**"
  echo "- Human approval provided: \`$APPROVED\`"
  echo "- Code-changing actions executed by this script: **no**"
  echo
  echo "## Human Approval Gate (Mandatory)"
  echo
  echo "Before any code-changing implementation starts, a human must approve the candidate list above."
  echo "Suggested command after approval:"
  echo "\`scripts/new_evolution_change.sh <change-id> <title>\` (if change scaffold does not exist)."
} >>"$OUT_PATH"

if [[ -f "$HANDOFF_PATH" ]]; then
  {
    echo
    echo "## Candidate Generation Update ($timestamp)"
    echo
    echo "- Candidate list generated: \`$OUT_PATH\`"
    echo "- Source report: \`$REPORT_PATH\`"
    echo "- Artifact status: \`$artifact_status\`"
    echo "- Deterministic status: \`$det_status\`"
    if [[ "$APPROVED" == "true" ]]; then
      echo "- Human approval flag: provided."
    else
      echo "- Human approval flag: missing (expected for planning-only run)."
    fi
  } >>"$HANDOFF_PATH"
fi

echo "candidate list generated: $OUT_PATH"
if [[ "$APPROVED" != "true" ]]; then
  echo "note: planning-only run complete. human approval is still required before code changes."
fi
