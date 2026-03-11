#!/usr/bin/env bash
set -euo pipefail

HOST="${CODEX_PROBE_HOST:-127.0.0.1}"
PORT="${CODEX_PROBE_PORT:-18000}"
BASE_URL="http://${HOST}:${PORT}"

step() {
  local label="$1"
  echo "[step] $label"
}

fail() {
  local msg="$1"
  echo "[error] $msg"
  exit 1
}

step "health check (${BASE_URL}/api/health)"
health_body="$(mktemp)"
health_code="$(curl -sS -o "$health_body" -w '%{http_code}' "${BASE_URL}/api/health" || true)"
if [[ "$health_code" != "200" ]]; then
  echo "[debug] health response body:"
  cat "$health_body" || true
  rm -f "$health_body"
  fail "backend health check failed (code=${health_code})"
fi
rm -f "$health_body"
echo "[ok] health"

step "codex bridge config check"
python3 scripts/check_codex_sdk_config.py || fail "codex sdk config check failed"
echo "[ok] codex bridge config"

step "runtime skill accessibility check"
python3 scripts/check_skill_runtime_access.py || fail "runtime skill accessibility check failed"
echo "[ok] runtime skill accessibility"

step "live skill probe"
./scripts/probe_codex_bridge.sh || fail "live probe failed"
echo "[ok] live skill probe"

echo "[ok] smoke_codex_bridge completed"
