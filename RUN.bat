@echo off
chcp 65001 >nul
title Assistente Desktop V2

echo ============================================
echo   Assistente Desktop V2
echo ============================================
echo.

REM Define caminho do venv local
set VENV_PATH=%~dp0venv

REM Verifica se o ambiente virtual existe
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual não encontrado em %VENV_PATH%!
    echo Execute SETUP.bat primeiro para instalar todas as dependências.
    pause
    exit /b 1
)

REM Ativa o ambiente virtual e inicia o assistente
call "%VENV_PATH%\Scripts\activate.bat"
echo [INFO] Iniciando Assistente Desktop V2...
python main.py

REM Pausa em caso de erro
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O programa encerrou com erro %errorlevel%.
    pause
)
