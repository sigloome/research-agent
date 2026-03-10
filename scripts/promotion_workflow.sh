#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
REPORT_DIR="$RUNS_DIR/promotion"
LATEST_BENCH="$ROOT_DIR/tmp/interview_pack/reports/live_benchmark_report.json"
OUT_PATH="$REPORT_DIR/$(date +"%Y%m%d-%H%M%S").md"

mkdir -p "$REPORT_DIR"

warn() {
  echo "[warning] $1"
}

extract_metric() {
  local key="$1"
  python - "$LATEST_BENCH" "$key" <<'PY'
import json,sys
path,key = sys.argv[1],sys.argv[2]
with open(path,'r',encoding='utf-8') as f:
    data=json.load(f)
profiles=data.get("profiles",[])
if not profiles:
    print("")
    raise SystemExit(0)
vals=[p.get(key) for p in profiles if isinstance(p.get(key),(int,float))]
if not vals:
    print("")
else:
    print(sum(vals)/len(vals))
PY
}

done_rate=""
tool_fail=""
lat_p95=""
if [[ -f "$LATEST_BENCH" ]]; then
  done_rate="$(extract_metric done_marker_rate || true)"
  tool_fail="$(extract_metric tool_failure_rate || true)"
  lat_p95="$(extract_metric latency_p95_ms || true)"
fi

warn_count=0
if [[ -n "$done_rate" ]]; then
  awk -v v="$done_rate" 'BEGIN{exit !(v<0.98)}' && { warn "done_marker_rate below 0.98: $done_rate"; warn_count=$((warn_count+1)); } || true
fi
if [[ -n "$tool_fail" ]]; then
  awk -v v="$tool_fail" 'BEGIN{exit !(v>0.02)}' && { warn "tool_failure_rate above 0.02: $tool_fail"; warn_count=$((warn_count+1)); } || true
fi
if [[ -n "$lat_p95" ]]; then
  awk -v v="$lat_p95" 'BEGIN{exit !(v>30000)}' && { warn "latency_p95_ms above 30000: $lat_p95"; warn_count=$((warn_count+1)); } || true
fi

{
  echo "# Promotion Workflow Report"
  echo
  echo "- Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Source benchmark: \`$LATEST_BENCH\`"
  echo
  echo "## Stage: sandbox"
  echo "- Command: \`scripts/run_evolution_cycle.sh\`"
  echo "- Expectation: deterministic gates pass."
  echo
  echo "## Stage: shadow"
  echo "- Command: \`scripts/run_live_benchmark.sh\`"
  echo "- Expectation: no protocol regressions; warnings allowed."
  echo
  echo "## Stage: canary"
  echo "- Command: manual small-traffic enable after human approval."
  echo "- Expectation: warning metrics reviewed by owner/reviewer/oncall."
  echo
  echo "## Soft Warning Summary (non-blocking)"
  echo "- done_marker_rate(avg): ${done_rate:-N/A} (warn if < 0.98)"
  echo "- tool_failure_rate(avg): ${tool_fail:-N/A} (warn if > 0.02)"
  echo "- latency_p95_ms(avg): ${lat_p95:-N/A} (warn if > 30000)"
  echo "- warnings: $warn_count"
  echo
  echo "## Rollback Templates"
  echo "1. Disable runtime profile routing:"
  echo "   - unset runtime_profile in caller and rerun baseline."
  echo "2. Disable trace extension quickly:"
  echo "   - rollback commit affecting \`agent-trace\` emission."
  echo "3. Re-validate:"
  echo "   - \`scripts/run_evolution_cycle.sh\`"
  echo
  echo "## Gate Decision"
  echo "- This report is non-blocking and requires explicit human approval for promotion."
} >"$OUT_PATH"

echo "promotion workflow report: $OUT_PATH"
echo "warnings=$warn_count"
