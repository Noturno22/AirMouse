@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Corre setup.bat primeiro.
    exit /b 1
)

rem ── Certificado de assinatura digital (opcional) ──────────────────────
rem O build assina automaticamente quando existe um certificado .pfx.
rem A prioridade para detetar o certificado e:
rem   1. Argumento   : build.bat <pfx_path> <pfx_pass>
rem   2. Variaveis   : PFX_PATH e PFX_PASS
rem   3. Local fixo  : cert\maouse.pfx   (password = PFX_PASS ou vazia)
rem Sem certificado o build continua, mas o .exe/instalador ficam NAO assinados
rem (SmartScreen/AV vao avisar). Obter um cert EV e o passo comercial em falta.
set "PFX_PATH=%~1"
set "PFX_PASS=%~2"
if not defined PFX_PASS if defined PFX_PASS_ENV set "PFX_PASS=%PFX_PASS_ENV%"
if not defined PFX_PATH if exist "cert\maouse.pfx" set "PFX_PATH=%CD%\cert\maouse.pfx"
if defined PFX_PATH if not exist "%PFX_PATH%" (
    echo AVISO: PFX_PATH nao existe: %PFX_PATH%
    set "PFX_PATH="
)

rem Deteta o signtool (Windows SDK / Inno Setup).
set "SIGNTOOL="
for %%K in (
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe"
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x86\signtool.exe"
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
) do if not defined SIGNTOOL if exist "%%~K" set "SIGNTOOL=%%~K"

if defined PFX_PATH (
    echo [ASSINATURA] Certificado encontrado: %PFX_PATH%
) else (
    echo [ASSINATURA] Sem certificado - o .exe/instalador nao serao assinados.
)

echo [1/6] A instalar PyInstaller ...
.venv\Scripts\python.exe -m pip install --upgrade -r requirements-build.txt -q
if errorlevel 1 exit /b 1

echo [2/6] A gerar icone (.ico) ...
.venv\Scripts\python.exe tools\generate_ico.py
if errorlevel 1 exit /b 1

echo [3/6] A gerar metadados de versao (version_info.txt) ...
.venv\Scripts\python.exe tools\gen_version_info.py
if errorlevel 1 exit /b 1

echo [4/6] A construir executavel (pode demorar varios minutos) ...
.venv\Scripts\python.exe -m PyInstaller airmouse.spec --noconfirm
if errorlevel 1 exit /b 1
xcopy /E /I /Y models "dist\AirMouse\models" >nul

rem ── Assinar o AirMouse.exe (antes de o empacotar no instalador) ───────
if defined PFX_PATH if defined SIGNTOOL (
    echo [5/6] A assinar AirMouse.exe (SHA256 + timestamp) ...
    "%SIGNTOOL%" sign /f "%PFX_PATH%" /p "%PFX_PASS%" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /d "Maouse" "dist\AirMouse\AirMouse.exe"
    if errorlevel 1 echo AVISO: falhou a assinatura do AirMouse.exe (continuando sem ela).
) else (
    echo [5/6] Assinatura do AirMouse.exe ignorada.
)

echo [6/6] A gerar instalador 1-clique (Inno Setup) ...
set "ISCC=C:\Users\Luar Studio Angola\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo ATENCAO: Inno Setup nao encontrado em "%ISCC%"
    echo O instalador nao foi gerado, mas o AirMouse.exe esta em dist\AirMouse\
) else (
    if defined PFX_PATH (
        rem Assinar o instalador, reutilizando o mesmo certificado.
        "%ISCC%" installer.iss /DPfxPath="%PFX_PATH%" /DPfxPass="%PFX_PASS%"
    ) else (
        "%ISCC%" installer.iss
    )
    if errorlevel 1 exit /b 1
)

echo.
echo Build concluido:
echo   Executavel: dist\AirMouse\AirMouse.exe
echo   Instalador: dist\Maouse-Setup-1.0.0.exe
if defined PFX_PATH (
    echo   Assinado: SIM
) else (
    echo   Assinado: NAO  ^(obtem um certificado EV para remover o aviso SmartScreen^)
)
endlocal
