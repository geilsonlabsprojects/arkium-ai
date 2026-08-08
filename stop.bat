@echo off
REM  Encerra os processos do Arkium AI (backend e frontend).
echo Encerrando Arkium AI...
taskkill /FI "WINDOWTITLE eq Arkium API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Arkium Painel*" /T /F >nul 2>&1
echo Servicos encerrados.
pause
