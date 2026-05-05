#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

if [[ -n "${TAGR_PYTHON:-}" ]]; then
  PYTHON_BIN="$TAGR_PYTHON"
elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
elif [[ -x "$HOME/tagdrop-env/bin/python" ]]; then
  PYTHON_BIN="$HOME/tagdrop-env/bin/python"
else
  PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$PROJECT_ROOT/src/tagr.py" "$@"
