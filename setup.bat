@echo off
REM Configura o ambiente do Mãouse (executar apenas uma vez)
cd /d "%~dp0"

if not exist .venv (
    echo A criar ambiente virtual...
    python -m venv .venv || goto :erro
)

echo A instalar dependencias...
.venv\Scripts\pip.exe install --quiet --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt || goto :erro

echo.
echo Pronto! Executa start.bat para comecar.
pause
exit /b 0

:erro
echo ERRO: a instalacao falhou.
pause
exit /b 1
