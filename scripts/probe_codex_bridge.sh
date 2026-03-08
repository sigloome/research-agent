#!/usr/bin/env zsh
set -euo pipefail

# Use dedicated probe vars to avoid conflicts with generic shell HOST/PORT env vars.
HOST="${CODEX_PROBE_HOST:-127.0.0.1}"
PORT="${CODEX_PROBE_PORT:-18000}"
PAYLOAD_FILE="/tmp/codex-chat-payload.json"
STREAM_FILE="/tmp/codex-chat-stream.out"

cat >"$PAYLOAD_FILE" <<'JSON'
{"message":"Use Skill tool to list available skills first, then use knowledge and preference to answer what you know about my profile/history.","session_id":"default"}
JSON

curl -sS -o /tmp/codex-health.out -w '%{http_code}' "http://$HOST:$PORT/api/health" >/tmp/codex-health.code
code="$(cat /tmp/codex-health.code)"
if [[ "$code" != "200" ]]; then
  echo "[error] health check failed (code=$code)"
  cat /tmp/codex-health.out
  exit 1
fi

curl -sN -X POST "http://$HOST:$PORT/api/chat" \
  -H 'Content-Type: application/json' \
  --data-binary @"$PAYLOAD_FILE" \
  --max-time 120 >"$STREAM_FILE"

auth_err=$(rg -n 'authentication_error|Invalid bearer token|Missing bridge authentication|Codex bridge error 401' "$STREAM_FILE" || true)
if [[ -n "$auth_err" ]]; then
  echo "[error] live bridge probe auth failure"
  sed -n '1,160p' "$STREAM_FILE"
  exit 1
fi

tool_events=$(rg -n '"type": "tool-input-start"|"type": "tool-input-available"' "$STREAM_FILE" || true)
skill_events=$(rg -n '"toolName": "Skill"|"toolName":"Skill"' "$STREAM_FILE" || true)
knowledge_skill=$(rg -n '"skill": "knowledge"|"skill":"knowledge"' "$STREAM_FILE" || true)
preference_skill=$(rg -n '"skill": "preference"|"skill":"preference"' "$STREAM_FILE" || true)
if [[ -z "$tool_events" ]]; then
  echo "[fail] no tool-input events emitted"
  sed -n '1,220p' "$STREAM_FILE"
  exit 1
fi
if [[ -z "$skill_events" ]]; then
  echo "[fail] tool events found but no Skill invocation"
  sed -n '1,260p' "$STREAM_FILE"
  exit 1
fi
if [[ -z "$knowledge_skill" ]]; then
  echo "[fail] Skill invocation did not include knowledge"
  sed -n '1,280p' "$STREAM_FILE"
  exit 1
fi
if [[ -z "$preference_skill" ]]; then
  echo "[fail] Skill invocation did not include preference"
  sed -n '1,280p' "$STREAM_FILE"
  exit 1
fi

echo "[ok] live probe observed Skill tool events with knowledge+preference"
rg -n '"type": "tool-input-start"|"toolName": "Skill"|"skill": "knowledge"|"skill": "preference"|"finishReason"|\[DONE\]' "$STREAM_FILE" || true
