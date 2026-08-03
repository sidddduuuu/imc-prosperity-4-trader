#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -d "$ROOT/backend/.venv" ]]; then
  python3 -m venv "$ROOT/backend/.venv"
  # shellcheck disable=SC1091
  source "$ROOT/backend/.venv/bin/activate"
  pip install -r "$ROOT/backend/requirements.txt"
else
  # shellcheck disable=SC1091
  source "$ROOT/backend/.venv/bin/activate"
fi

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi

echo "Starting Atlas backend on :8000 and frontend on :3000"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACK_PID=$!
(cd "$ROOT/frontend" && npm run dev -- --port 3000 --hostname 0.0.0.0) &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null || true' EXIT
wait
