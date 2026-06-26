@echo off
chcp 65001 >nul 2>&1
title Sistema de Diagnostico Medico - Redes Bayesianas

echo.
echo  ============================================
echo   Sistema de Diagnostico Medico
echo   Redes Bayesianas - Doencas Respiratorias
echo  ============================================
echo.

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao encontrado!
    echo  Instale em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo  [1/2] Instalando dependencias...
echo.
pip install flask pgmpy matplotlib networkx tabulate --quiet
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo  [2/2] Iniciando servidor...
echo.
echo  Acesse no navegador: http://localhost:5000
echo  Para encerrar, feche esta janela ou pressione Ctrl+C
echo.

set PYTHONIOENCODING=utf-8
python app.py
pause
