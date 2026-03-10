#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$ROOT_DIR/tmp/runs/evolution"
CHANGES_DIR="$ROOT_DIR/openspec/changes"

latest_report="$(find "$RUNS_DIR" -maxdepth 1 -type f -name "*.md" ! -name "index.md" | sort | tail -n 1 || true)"
if [[ -z "$latest_report" ]]; then
  echo "no run report found under $RUNS_DIR" >&2
  exit 1
fi

append_ref_if_missing() {
  local file="$1"
  local ref="$2"
  if [[ -f "$file" ]] && ! grep -Fq "$ref" "$file"; then
    {
      echo
      echo "## Run Log Sync"
      echo
      echo "- Synced evolution report: \`$ref\`"
    } >>"$file"
  fi
}

for d in "$CHANGES_DIR"/*; do
  [[ -d "$d" ]] || continue
  name="$(basename "$d")"
  [[ "$name" == "archive" || "$name" == _* ]] && continue
  append_ref_if_missing "$d/proposal.md" "$latest_report"
  append_ref_if_missing "$d/design.md" "$latest_report"
  append_ref_if_missing "$d/tasks.md" "$latest_report"
done

echo "run-log sync complete with report: $latest_report"
