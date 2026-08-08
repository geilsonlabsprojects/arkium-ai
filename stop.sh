#!/usr/bin/env bash
# Encerra os processos do Arkium AI.
pkill -f "app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
echo "Servicos encerrados."
