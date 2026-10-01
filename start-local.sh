#!/usr/bin/env bash
set -euo pipefail
WEB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$WEB_DIR"

if [[ "${1:-}" == "--build" ]]; then
  (cd "$WEB_DIR/frontend" && npm ci --no-audit --no-fund && npm run build)
fi
if [[ ! -f "$WEB_DIR/frontend/dist/index.html" ]]; then
  echo "Frontend build missing. Run: Web/start-local.sh --build" >&2
  exit 1
fi
export MEMVAR_QUERY_BACKEND="${MEMVAR_QUERY_BACKEND:-${MEMVAR_DATABASE_URL:+postgresql}}"
export MEMVAR_QUERY_BACKEND="${MEMVAR_QUERY_BACKEND:-duckdb}"
if [[ "$MEMVAR_QUERY_BACKEND" == "postgresql" ]]; then
  if [[ ! -f "$WEB_DIR/data/.api.env" && -z "${MEMVAR_DATABASE_URL:-}" ]]; then
    echo "Configure a read-only PostgreSQL connection before starting the API." >&2
    exit 1
  fi
fi
exec python -m uvicorn src.api.main:app --host "${MEMVAR_HOST:-127.0.0.1}" --port "${MEMVAR_PORT:-8000}"
