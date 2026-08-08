@echo off
REM ===========================================================================
REM  Arkium AI - inicia backend (API + Swagger) e frontend (painel).
REM ===========================================================================
cd /d "%~dp0"
echo Iniciando Arkium AI...

if not exist "backend\venv" (
  echo [ERRO] Ambiente nao instalado. Execute install.bat primeiro.
  pause & exit /b 1
)

start "Arkium API" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe run.py"
timeout /t 3 /nobreak >nul

if exist "frontend\node_modules" (
  start "Arkium Painel" cmd /k "cd /d %~dp0frontend && npm run dev"
  timeout /t 4 /nobreak >nul
  start http://localhost:5173
) else (
  start http://localhost:8000/docs
)

echo.
echo  API .......... http://localhost:8000
echo  Swagger ...... http://localhost:8000/docs
echo  Painel ....... http://localhost:5173
echo.
