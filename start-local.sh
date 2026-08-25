#!/usr/bin/env bash

set -Eeuo pipefail

website_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backend_dir="$website_dir/backend"
frontend_dir="$website_dir/frontend"
local_host="${MEMVAR_LOCAL_HOST:-127.0.0.1}"
api_port="${MEMVAR_API_PORT:-8000}"
web_port="${MEMVAR_WEB_PORT:-3000}"
backend_pid=""
frontend_pid=""

fail() {
  echo "memVar startup failed: $*" >&2
  exit 1
}

cleanup() {
  trap - EXIT
  for service_pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$service_pid" ]] && kill -0 "$service_pid" 2>/dev/null; then
      kill -TERM -- "-$service_pid" 2>/dev/null || true
    fi
  done
  for service_pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$service_pid" ]]; then
      wait "$service_pid" 2>/dev/null || true
    fi
  done
}

handle_signal() {
  exit 130
}

trap cleanup EXIT
trap handle_signal INT TERM HUP

for required_command in python npm setsid; do
  command -v "$required_command" >/dev/null 2>&1 \
    || fail "required command is not available: $required_command"
done

python - <<'PY' || fail "Python dependencies are missing; install fastapi, uvicorn, duckdb, numpy, pydantic, and PyYAML"
import duckdb  # noqa: F401
import fastapi  # noqa: F401
import numpy  # noqa: F401
import pydantic  # noqa: F401
import uvicorn  # noqa: F401
import yaml  # noqa: F401
PY

[[ -x "$frontend_dir/node_modules/.bin/next" ]] \
  || fail "frontend dependencies are missing; run: cd '$frontend_dir' && npm install"

[[ -n "${MEMVAR_DATA_ROOT:-}" ]] \
  || fail "MEMVAR_DATA_ROOT must name the exact serving release root"
[[ -n "${MEMVAR_DATA_UUID:-}" ]] \
  || fail "MEMVAR_DATA_UUID must name the data mount UUID"
PYTHONPATH="$backend_dir${PYTHONPATH:+:$PYTHONPATH}" python - <<'PY' \
  || fail "configured serving release is unavailable or incomplete"
from app.release_store import release_store

store = release_store()
if not store.core_database.is_file():
    raise RuntimeError(f"Core catalog is missing: {store.core_database}")
PY

[[ "$api_port" =~ ^[0-9]+$ ]] && (( api_port >= 1 && api_port <= 65535 )) \
  || fail "MEMVAR_API_PORT must be an integer from 1 to 65535"
[[ "$web_port" =~ ^[0-9]+$ ]] && (( web_port >= 1 && web_port <= 65535 )) \
  || fail "MEMVAR_WEB_PORT must be an integer from 1 to 65535"
[[ "$api_port" != "$web_port" ]] || fail "API and web ports must be different"

python - "$local_host" "$api_port" "$web_port" <<'PY' \
  || fail "one of the requested local ports is already in use"
import socket
import sys

host = sys.argv[1]
for raw_port in sys.argv[2:]:
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind((host, int(raw_port)))
PY

echo "Starting memVar API on http://$local_host:$api_port ..."
setsid python -m uvicorn app.main:app \
  --app-dir "$backend_dir" --host "$local_host" --port "$api_port" &
backend_pid=$!

api_ready_url="http://$local_host:$api_port/api/v1/search?q=P00533&limit=1"
api_ready="false"
for _ in {1..60}; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid" || true
    fail "API process stopped before becoming ready"
  fi
  if python - "$api_ready_url" <<'PY' 2>/dev/null
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=0.5) as response:
    if response.status != 200:
        raise SystemExit(1)
PY
  then
    api_ready="true"
    break
  fi
  sleep 0.25
done
[[ "$api_ready" == "true" ]] || fail "API did not become ready within 15 seconds"

echo "Starting memVar website on http://$local_host:$web_port ..."
setsid env \
  MEMVAR_API_INTERNAL_ORIGIN="http://$local_host:$api_port" \
  MEMVAR_API_INTERNAL_BASE="http://$local_host:$api_port/api/v1" \
  npm --prefix "$frontend_dir" run dev -- \
  --webpack --hostname "$local_host" --port "$web_port" &
frontend_pid=$!

web_ready_url="http://$local_host:$web_port"
web_ready="false"
for _ in {1..120}; do
  if ! kill -0 "$frontend_pid" 2>/dev/null; then
    wait "$frontend_pid" || true
    fail "website process stopped before becoming ready"
  fi
  if python - "$web_ready_url" <<'PY' 2>/dev/null
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=0.5) as response:
    if response.status >= 500:
        raise SystemExit(1)
PY
  then
    web_ready="true"
    break
  fi
  sleep 0.25
done
[[ "$web_ready" == "true" ]] || fail "website did not become ready within 30 seconds"

echo
echo "memVar is ready: http://$local_host:$web_port"
echo "EGFR example: http://$local_host:$web_port/protein/P00533"
echo "Press Ctrl+C once to stop both the website and API."
echo

set +e
wait -n "$backend_pid" "$frontend_pid"
service_status=$?
set -e
echo "A memVar service stopped; shutting down the other service."
exit "$service_status"
