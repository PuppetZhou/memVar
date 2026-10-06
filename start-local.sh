#!/usr/bin/env bash
set -euo pipefail
WEB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$WEB_DIR"

if [[ -n "${MEMVAR_PYTHON:-}" ]]; then
  PYTHON="$MEMVAR_PYTHON"
elif [[ -x "$WEB_DIR/.venv/bin/python" ]]; then
  PYTHON="$WEB_DIR/.venv/bin/python"
else
  PYTHON=python3
fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python executable is unavailable: $PYTHON" >&2
  exit 1
fi

export MEMVAR_FRONTEND_DIST="${MEMVAR_FRONTEND_DIST:-$WEB_DIR/frontend/dist-portable}"
if [[ ! -f "$MEMVAR_FRONTEND_DIST/index.html" ]]; then
  echo "Frontend build missing: $MEMVAR_FRONTEND_DIST. Run prepare-local.sh first." >&2
  exit 1
fi

"$PYTHON" -m src.runtime check
exec "$PYTHON" -m uvicorn src.api.main:app --host "${MEMVAR_HOST:-127.0.0.1}" --port "${MEMVAR_PORT:-8000}"
