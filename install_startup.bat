@echo off
setlocal
set "DIR=%~dp0"
set "PYW=%DIR%.venv\Scripts\pythonw.exe"
set "MAIN=%DIR%main.py"

if not exist "%PYW%" (
    echo ERRO: pythonw.exe nao encontrado em %PYW%
    echo Corre primeiro setup.bat
    pause
    exit /b 1
)

schtasks /Create /F /TN "AirMouse JARVIS" /SC ONLOGON /RL LIMITED /TR "\"%PYW%\" \"%MAIN%\" --tray"
if errorlevel 1 (
    echo Falhou a criacao da tarefa.
    pause
    exit /b 1
)
echo.
echo Mãouse arrancara automaticamente com o Windows (modo invisivel + bandeja).
echo Para remover: corre uninstall_startup.bat
pause
