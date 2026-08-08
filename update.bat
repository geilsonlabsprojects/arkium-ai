@echo off
REM  Atualiza dependencias e o esquema do banco.
cd /d "%~dp0"
echo Atualizando Arkium AI...
call backend\venv\Scripts\python.exe -m pip install --upgrade pip
call backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt --upgrade
pushd backend
call venv\Scripts\python.exe -m app.db.init_db
popd
if exist "frontend\node_modules" ( pushd frontend & call npm install & popd )
echo Atualizacao concluida.
pause
