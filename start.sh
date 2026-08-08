#!/usr/bin/env bash
# Inicia backend e frontend do Arkium AI.
set -e
cd "$(dirname "$0")"

[ -d backend/venv ] || { echo "[ERRO] Execute ./install.sh primeiro."; exit 1; }

(cd backend && venv/bin/python run.py) &
API_PID=$!
echo "API iniciada (pid $API_PID) em http://localhost:8000 - Swagger em /docs"

if [ -d frontend/node_modules ]; then
  (cd frontend && npm run dev) &
  echo "Painel em http://localhost:5173"
fi

trap 'kill 0' INT TERM
wait
