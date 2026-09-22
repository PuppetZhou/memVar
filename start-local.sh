#!/usr/bin/env bash
set -euo pipefail
WEB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname -- "$WEB_DIR")"
cd "$PROJECT_DIR"

if [[ "${1:-}" == "--build" ]]; then
  (cd "$WEB_DIR/frontend" && npm ci --no-audit --no-fund && npm run build)
fi
if [[ ! -f "$WEB_DIR/frontend/dist/index.html" ]]; then
  echo "Frontend build missing. Run: Web/start-local.sh --build" >&2
  exit 1
fi
if [[ ! -f "$WEB_DIR/data/.api.env" && -z "${MEMVAR_DATABASE_URL:-}" ]]; then
  python -m Web.src.api.db --setup-reader
fi
exec python -m uvicorn Web.src.api.main:app --host "${MEMVAR_HOST:-127.0.0.1}" --port "${MEMVAR_PORT:-8000}"
