# Assinatura Digital do Windows (code-signing)

Para deixar de aparecer o "Publisher desconhecido / SmartScreen" e evitar AV a bloquear,
os executáveis (AirMouse.exe e o instalador) devem ser **assinados digitalmente**.

> **Estado:** o `.exe` e o instalador são gerados **sem assinatura** por defeito —
> funciona, mas mostra aviso. A assinatura é um passo de execução comercial que
> depende de um certificado comprado. Este guia explica como ativá-la quando tiveres.

## O que é um certificado code-signing

É um certificado digital (`.pfx` / `.p12`) que comprova "quem fez esta app" ao Windows.
Precisa de ser **comprado** a uma Autoridade de Certificação (CA) reconhecida.
Algumas opções populares:

- **DigiCert** (costuma ser o mais reconhecido)
- **Sectigo / Comodo**
- **Certum** (mais barato, código OV)
- **Microsoft Partner/Store** implica o certificado de Publisher da Store

> ⚠️ Sem um certificado válido emitido por uma CA, a assinatura **não** remove o
> SmartScreen em máquinas reais. Um certificado self-signed só serve para testes locais.

## O que precisas

1. Um ficheiro `.pfx` (ou `.p12`) com o certificado + chave privada.
2. A password desse ficheiro.
3. O `signtool.exe` (já tens: Windows Kits) — o `build.bat` já o usa.

## Passos

### 1. Comprar/generar o certificado
Seguir a CA escolhida. No final recebes um `.pfx` + password. Guarda-o num lugar seguro
(ex.: `C:\certs\maouse.pfx`). **Nunca** faças commit da password nem do `.pfx` para o git.

### 2. Ativar a assinatura no instalador
Edita `installer.iss` (ou passa os parâmetros no `build.bat`). O Inno Setup já está
configurado para assinar quando passas o certificado:

```bat
"C:\Users\Luar Studio Angola\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss /DPfxPath=C:\certs\maouse.pfx /DPfxPass=SUA_PASSWORD
```

Ou, para ficar tudo junto no `build.bat`, descomenta/edita a linha indicada lá dentro.

### 3. (Opcional) Assinar o AirMouse.exe em separado
O instalador quando assinado já assina o `AirMouse.exe` por dentro (via `SignTool` no Inno).
Para assinar só o exe manualmente:

```bat
"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe" sign /f C:\certs\maouse.pfx /p SUA_PASSWORD /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /d "Mãouse" "dist\AirMouse\AirMouse.exe"
```

### 4. Verificar a assinatura
```powershell
Get-AuthenticodeSignature "dist\AirMouse\AirMouse.exe"
Get-AuthenticodeSignature "dist\Maouse-Setup-1.0.0.exe"
```
Deve aparecer `Status: Valid` e o Publisher correto.

## Notas
- O timestamp (`/tr .../td SHA256`) é importante para a assinatura continuar válida
  depois de o certificado expirar.
- Guarda o `.pfx` e a password num cofre de passwords; se perderes a chave, a assinatura fica órfã.
- Para a **Microsoft Store** o processo é diferente (certificado de Publisher + MSIX), fora deste guia.
