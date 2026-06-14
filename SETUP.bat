@echo off
chcp 65001 >nul
title Assistente Desktop V2 - Setup

echo ============================================
echo   Assistente Desktop V2 - Setup
echo ============================================
echo.

REM Define caminho do venv local (adicionado ao .gitignore)
REM Caso seu projeto esteja em uma pasta sincronizada com OneDrive, 
REM você pode alterar para um caminho fora do OneDrive (ex: C:\venvs\assistente_v2) para melhor performance.
set VENV_PATH=%~dp0venv

REM Verifica se o Python está instalado
echo [1/5] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Comando 'python' não encontrado no PATH!
    echo Instale o Python 3.10+ e marque a opção "Add python.exe to PATH" no instalador.
    pause
    exit /b 1
)

REM Cria o ambiente virtual venv
echo [2/5] Criando ambiente virtual em %VENV_PATH%...
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    python -m venv "%VENV_PATH%"
)
if %errorlevel% neq 0 (
    echo ERRO: Falha ao criar ambiente virtual!
    pause
    exit /b 1
)

REM Ativa o ambiente virtual
call "%VENV_PATH%\Scripts\activate.bat"
python -m pip install --upgrade pip

REM PyTorch CUDA (ANTES do requirements.txt para garantir suporte à GPU)
echo [3/5] Instalando PyTorch com CUDA 12.1...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo AVISO: Falha ao instalar PyTorch CUDA, tentando versão CPU...
    pip install torch torchvision torchaudio
)

REM Instala demais dependências
echo [4/5] Instalando demais dependências...
pip install -r requirements.txt

REM Baixa o modelo do Whisper
echo [5/5] Baixando modelo Whisper...
python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8', download_root='models')" 2>nul
echo Modelo Whisper pronto.

REM Cria diretórios necessários
if not exist audio_output mkdir audio_output
if not exist models mkdir models

REM Verifica instalação do CUDA
echo.
echo Verificando instalação do PyTorch...
python -c "import torch; print('PyTorch ' + torch.__version__ + ' | CUDA Disponível: ' + str(torch.cuda.is_available()))"

echo.
echo ============================================
echo   Setup completo!
echo.
echo   1. Renomeie o arquivo .env.example para .env e configure suas chaves de API.
echo   2. Execute RUN.bat para iniciar o assistente.
echo ============================================
pause