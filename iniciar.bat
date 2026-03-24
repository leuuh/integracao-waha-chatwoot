@echo off
title WAHA Chatwoot - Painel de Integração
echo.
echo  ================================================
echo   WAHA ^<-^> Chatwoot  Painel de Integração
echo  ================================================
echo.

:: Verificar se Python existe no PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON=py
    ) else (
        echo  [!] Python nao encontrado no PATH da maquina.
        echo  [!] Tentando instalar via winget...
        winget install Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
        echo  [!] Reinicie este script apos a instalacao. Se o problema persistir, instale o Python manualmente e adicione-o ao PATH.
        pause
        exit /b 1
    )
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
