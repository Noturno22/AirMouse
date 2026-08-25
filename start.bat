@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Ambiente nao configurado. Executa setup.bat primeiro.
    pause
    exit /b 1
)
.venv\Scripts\python.exe main.py %*
