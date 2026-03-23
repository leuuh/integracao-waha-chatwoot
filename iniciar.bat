@echo off
title WAHA Chatwoot - Painel de Integração
echo.
echo  ================================================
echo   WAHA ^<-^> Chatwoot  Painel de Integração
echo  ================================================
echo.

:: Caminho do Python 3.12 instalado
set PYTHON=C:\Users\Leonardo\AppData\Local\Programs\Python\Python312\python.exe

:: Verificar se Python existe no caminho padrão
if not exist "%PYTHON%" (
    echo  [!] Python nao encontrado em %PYTHON%
    echo  [!] Tentando instalar via winget...
    winget install Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    echo  [!] Reinicie este script apos a instalacao.
    pause
    exit /b 1
)

:: Instalar dependências
echo  [*] Verificando dependencias Python...
"%PYTHON%" -m pip install -r requirements.txt -q 2>nul

:: Iniciar o servidor
echo  [*] Iniciando servidor em http://localhost:5000
echo.
start "" "http://localhost:5000"
"%PYTHON%" "%~dp0server.py"
pause
