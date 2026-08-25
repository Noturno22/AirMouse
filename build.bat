@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Corre setup.bat primeiro.
    exit /b 1
)
echo A instalar PyInstaller ...
.venv\Scripts\python.exe -m pip install --upgrade -r requirements-build.txt -q
if errorlevel 1 exit /b 1
echo A construir executavel (pode demorar varios minutos) ...
.venv\Scripts\python.exe -m PyInstaller airmouse.spec --noconfirm
if errorlevel 1 exit /b 1
xcopy /E /I /Y models "dist\AirMouse\models" >nul
echo.
echo Build concluido: dist\AirMouse\AirMouse.exe
endlocal
