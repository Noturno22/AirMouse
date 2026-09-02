@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Corre setup.bat primeiro.
    exit /b 1
)

echo [1/5] A instalar PyInstaller ...
.venv\Scripts\python.exe -m pip install --upgrade -r requirements-build.txt -q
if errorlevel 1 exit /b 1

echo [2/5] A gerar icone (.ico) ...
.venv\Scripts\python.exe tools\generate_ico.py
if errorlevel 1 exit /b 1

echo [3/5] A gerar metadados de versao (version_info.txt) ...
.venv\Scripts\python.exe tools\gen_version_info.py
if errorlevel 1 exit /b 1

echo [4/5] A construir executavel (pode demorar varios minutos) ...
.venv\Scripts\python.exe -m PyInstaller airmouse.spec --noconfirm
if errorlevel 1 exit /b 1
xcopy /E /I /Y models "dist\AirMouse\models" >nul

echo [5/5] A gerar instalador 1-clique (Inno Setup) ...
set "ISCC=C:\Users\Luar Studio Angola\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo ATENCAO: Inno Setup nao encontrado em %ISCC%
    echo O instalador nao foi gerado, mas o AirMouse.exe esta em dist\AirMouse\
) else (
    rem Para assinar, adicione a este bat:
    rem   "%ISCC%" installer.iss /DPfxPath=C:\caminho\certificado.pfx /DPfxPass=SUA_PASSWORD
    "%ISCC%" installer.iss
    if errorlevel 1 exit /b 1
)

echo.
echo Build concluido:
echo   Executavel: dist\AirMouse\AirMouse.exe
echo   Instalador: dist\Maouse-Setup-1.0.0.exe
endlocal
