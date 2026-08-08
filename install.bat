@echo off
title Arkium AI - Instalacao
color 0A
setlocal EnableDelayedExpansion

REM ===========================================================================
REM Arkium AI - Instalacao Completa
REM ===========================================================================

cd /d "%~dp0"

echo.
echo ======================================================
echo            Arkium AI - Instalacao
echo ======================================================
echo.

REM ===========================================================================
REM Detectar Python
REM ===========================================================================

set PYTHON=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
)

if "%PYTHON%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=py
    )
)

if "%PYTHON%"=="" (
    echo.
    echo [ERRO] Python nao encontrado.
    echo.
    echo Baixe em:
    echo https://www.python.org/downloads/
    echo.
    echo Durante a instalacao marque:
    echo [x] Add Python to PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado.

%PYTHON% --version

echo.

REM ===========================================================================
REM Verificar pip
REM ===========================================================================

%PYTHON% -m pip --version >nul 2>&1

if errorlevel 1 (
    echo [ERRO] Pip nao encontrado.
    echo Execute:
    echo %PYTHON% -m ensurepip --upgrade
    pause
    exit /b 1
)

echo [OK] Pip encontrado.
echo.

REM ===========================================================================
REM Criar pastas
REM ===========================================================================

if not exist backend\data mkdir backend\data
if not exist backend\logs mkdir backend\logs
if not exist backups mkdir backups

echo [OK] Estrutura criada.
echo.

REM ===========================================================================
REM Criar .env
REM ===========================================================================

if not exist .env (
    copy .env.example .env >nul
    echo [OK] Arquivo .env criado.
) else (
    echo [OK] Arquivo .env existente.
)

echo.

REM ===========================================================================
REM Criar Ambiente Virtual
REM ===========================================================================

if not exist backend\venv (

    echo Criando ambiente virtual...

    %PYTHON% -m venv backend\venv

    if errorlevel 1 (
        echo.
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )

)

echo [OK] Ambiente virtual pronto.
echo.

REM ===========================================================================
REM Atualizar Pip
REM ===========================================================================

call backend\venv\Scripts\python.exe -m pip install --upgrade pip

echo.

REM ===========================================================================
REM Instalar Dependencias
REM ===========================================================================

echo Instalando dependencias...

call backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

if errorlevel 1 (

    echo.
    echo [ERRO] Erro ao instalar dependencias.
    pause
    exit /b 1

)

echo.
echo [OK] Dependencias instaladas.
echo.

REM ===========================================================================
REM Inicializar Banco
REM ===========================================================================

echo Criando banco de dados...

pushd backend

call venv\Scripts\python.exe -m app.db.init_db

if errorlevel 1 (

    popd

    echo.
    echo [ERRO] Falha ao criar banco.
    pause
    exit /b 1

)

popd

echo [OK] Banco criado.
echo.

REM ===========================================================================
REM Verificar Node.js
REM ===========================================================================

where node >nul 2>&1

if errorlevel 1 (

    echo [AVISO] Node.js nao encontrado.
    echo.
    echo O frontend nao sera instalado.
    echo.
    echo Baixe:
    echo https://nodejs.org
    echo.

) else (

    echo Instalando frontend...

    pushd frontend

    call npm install

    popd

    echo [OK] Frontend instalado.

)

echo.

REM ===========================================================================
REM Verificar Ollama
REM ===========================================================================

curl http://localhost:11434/api/tags >nul 2>&1

if errorlevel 1 (

    echo.
    echo [AVISO] Ollama nao encontrado.
    echo.
    echo Baixe:
    echo https://ollama.com/download
    echo.
    echo Depois execute:
    echo.
    echo ollama pull llama3.2
    echo.
    echo Ou:
    echo.
    echo ollama pull qwen3:4b
    echo.

) else (

    echo [OK] Ollama encontrado.

)

echo.
echo ======================================================
echo             INSTALACAO CONCLUIDA
echo ======================================================
echo.
echo Login:
echo.
echo admin@arkium.ai
echo Senha:
echo admin123
echo.
echo Execute agora:
echo.
echo start.bat
echo.
echo ======================================================

pause