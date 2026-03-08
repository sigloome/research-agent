#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-18000}"
FRONTEND_PORT="${FRONTEND_PORT:-18001}"

count_listeners() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | tail -n +2 | wc -l | tr -d ' '
}

backend_count="$(count_listeners "$BACKEND_PORT")"
frontend_count="$(count_listeners "$FRONTEND_PORT")"

if [[ "$backend_count" -eq 0 ]]; then
  echo "[error] backend is not listening on :$BACKEND_PORT"
  exit 1
fi
if [[ "$frontend_count" -eq 0 ]]; then
  echo "[error] frontend is not listening on :$FRONTEND_PORT"
  exit 1
fi
if [[ "$backend_count" -gt 1 ]]; then
  echo "[error] multiple backend listeners detected on :$BACKEND_PORT (count=$backend_count)"
  lsof -nP -iTCP:"$BACKEND_PORT" -sTCP:LISTEN || true
  exit 1
fi
if [[ "$frontend_count" -gt 1 ]]; then
  echo "[error] multiple frontend listeners detected on :$FRONTEND_PORT (count=$frontend_count)"
  lsof -nP -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN || true
  exit 1
fi

echo "[ok] listener sanity passed (:${BACKEND_PORT}, :${FRONTEND_PORT})"
