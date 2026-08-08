#!/usr/bin/env bash
# ===========================================================================
#  Arkium AI - instalacao completa (Linux / macOS).
# ===========================================================================
set -e
cd "$(dirname "$0")"

echo "======================================================"
echo "  Arkium AI - Instalacao"
echo "======================================================"

command -v python3 >/dev/null 2>&1 || { echo "[ERRO] Python 3.12+ nao encontrado."; exit 1; }
echo "[OK] $(python3 --version)"

mkdir -p backend/data backend/logs backups
echo "[OK] Pastas criadas"

[ -f .env ] || { cp .env.example .env; echo "[OK] .env criado"; }

[ -d backend/venv ] || python3 -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip >/dev/null
backend/venv/bin/python -m pip install -r backend/requirements.txt
echo "[OK] Dependencias Python instaladas"

(cd backend && venv/bin/python -m app.db.init_db)
echo "[OK] Banco inicializado"

if command -v npm >/dev/null 2>&1; then
  (cd frontend && npm install)
  echo "[OK] Painel instalado"
else
  echo "[AVISO] Node.js nao encontrado - painel nao instalado (https://nodejs.org)"
fi

if curl -s -o /dev/null http://localhost:11434/api/tags; then
  echo "[OK] Ollama respondendo"
else
  echo "[AVISO] Ollama offline. Instale: curl -fsSL https://ollama.com/install.sh | sh"
  echo "        Depois baixe um modelo: ollama pull llama3.2"
fi

echo "Instalacao concluida! Execute ./start.sh"
echo "Login padrao: admin@arkium.ai / admin123"
