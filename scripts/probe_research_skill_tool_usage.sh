#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-18000}"
HOST="127.0.0.1"
LOG_FILE="/tmp/research-skill-probe-backend.log"
STREAM_FILE="/tmp/research-skill-probe-stream.out"
HEALTH_CODE_FILE="/tmp/research-skill-probe-health.code"
HEALTH_BODY_FILE="/tmp/research-skill-probe-health.out"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [[ -z "${ANTHROPIC_API_KEY:-}" && -z "${ANTHROPIC_AUTH_TOKEN:-}" ]]; then
  echo "[blocked] live probe requires ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN"
  exit 2
fi
if [[ -n "${ANTHROPIC_API_KEY:-}" && "${ANTHROPIC_API_KEY}" != sk-ant-* ]]; then
  echo "[blocked] ANTHROPIC_API_KEY is set but does not start with sk-ant-"
  exit 2
fi

cd "$ROOT_DIR"
source venv/bin/activate
python -m uvicorn backend.app:app --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
BACKEND_PID=$!

for _ in {1..40}; do
  sleep 0.5
  if curl -sS -o "$HEALTH_BODY_FILE" -w '%{http_code}' "http://$HOST:$PORT/api/health" >"$HEALTH_CODE_FILE" 2>/dev/null; then
    code="$(cat "$HEALTH_CODE_FILE")"
    if [[ "$code" == "200" ]]; then
      break
    fi
  fi
done

if [[ ! -f "$HEALTH_CODE_FILE" ]] || [[ "$(cat "$HEALTH_CODE_FILE" 2>/dev/null || true)" != "200" ]]; then
  echo "[error] backend health probe failed"
  tail -n 80 "$LOG_FILE" || true
  exit 1
fi

curl -sN -X POST "http://$HOST:$PORT/api/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"Use Skill tool to list available skills first, then use knowledge and preference skills to answer what you know about my profile and history.","session_id":"default"}' \
  --max-time 75 >"$STREAM_FILE"

auth_error=$(rg -n "Invalid bearer token|authentication_error|Failed to authenticate" "$STREAM_FILE" || true)
if [[ -n "$auth_error" ]]; then
  echo "[error] live probe failed due to authentication at runtime"
  sed -n '1,120p' "$STREAM_FILE"
  exit 1
fi

skill_events=$(rg -n '"type": "tool-input-available"|"type": "tool-input-start"' "$STREAM_FILE" || true)
skill_tool_hits=$(rg -n '"toolName": "Skill"|"toolName":"Skill"' "$STREAM_FILE" || true)

if [[ -z "$skill_events" ]]; then
  echo "[error] no tool-input events were emitted in /api/chat stream"
  sed -n '1,140p' "$STREAM_FILE"
  exit 1
fi

if [[ -z "$skill_tool_hits" ]]; then
  echo "[error] tool events exist but no Skill tool invocation was observed"
  sed -n '1,180p' "$STREAM_FILE"
  exit 1
fi

echo "[ok] live probe observed SDK tool usage and Skill invocations"
rg -n '"type": "tool-input-start"|"toolName": "Skill"|"finishReason"|\[DONE\]' "$STREAM_FILE" || true
exit 0
