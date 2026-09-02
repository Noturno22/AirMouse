; Inno Setup script for AirMouse (Mãouse)
; Build input: dist\AirMouse\  (PyInstaller onedir)
; Compile:
;   "C:\Users\Luar Studio Angola\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
;
; Assinatura digital (opcional): compile com
;   ISCC.exe installer.iss /DPfxPath=C:\path\cert.pfx /DPfxPass=SECRET
; Sem PfxPath o build NÃO assina (seguro para testes).

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName "Mãouse"
#define MyAppExeName "AirMouse.exe"
#define MyAppPublisher "Luar Studio Angola"
#define MyAppURL "https://example.com"

[Setup]
AppId={{1C7E5048-FF54-4EA9-A454-BF3512E443A7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Maouse-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\brand\maouse.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Controla o rato do PC com a mão, via webcam
VersionInfoProductName={#MyAppName}
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── Assinatura condicional (só quando /DPfxPath é passado) ──────────────
#ifdef PfxPath
SignTool=signtool="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe" sign /f "{#PfxPath}" /p "{#PfxPass}" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /d "{#MyAppName}" $f
#endif

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\AirMouse\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
