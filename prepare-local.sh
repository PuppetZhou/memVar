#!/usr/bin/env bash
set -euo pipefail

WEB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$WEB_DIR"

PYTHON_BOOTSTRAP="${MEMVAR_PYTHON_BOOTSTRAP:-python3.12}"
INSTALL_FRONTEND=1
BUILD_FRONTEND=1
PLAN_DATA=0
DATA_OUTPUT=''
while (($#)); do
  case "$1" in
    --python) PYTHON_BOOTSTRAP="$2"; shift 2 ;;
    --skip-npm-install) INSTALL_FRONTEND=0; shift ;;
    --skip-frontend) BUILD_FRONTEND=0; INSTALL_FRONTEND=0; shift ;;
    --plan-data) PLAN_DATA=1; shift ;;
    --data-output) DATA_OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -x "$WEB_DIR/.venv/bin/python" ]]; then
  "$PYTHON_BOOTSTRAP" -m venv "$WEB_DIR/.venv"
fi
PYTHON="$WEB_DIR/.venv/bin/python"
"$PYTHON" -m pip install -r "$WEB_DIR/requirements-web.txt"

if (( INSTALL_FRONTEND )); then
  (cd "$WEB_DIR/frontend" && npm ci --no-audit --no-fund)
fi
if (( BUILD_FRONTEND )); then
  (cd "$WEB_DIR/frontend" && npm run build -- --outDir dist-portable)
fi

if (( PLAN_DATA )); then
  "$PYTHON" -m src.database.portable plan
fi
if [[ -n "$DATA_OUTPUT" ]]; then
  if [[ "$DATA_OUTPUT" != /* ]]; then
    echo '--data-output requires an absolute, new directory path.' >&2
    exit 2
  fi
  "$PYTHON" -m src.database.portable build --output "$DATA_OUTPUT"
fi

echo 'Environment prepared. Point MEMVAR_DATA_ROOT or config/duckdb.yaml at a validated package, then run start-local.sh.'
