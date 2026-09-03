# Assinatura Digital do Windows (code-signing)

Para deixar de aparecer o "Publisher desconhecido / SmartScreen" e evitar AV a bloquear,
os executáveis (AirMouse.exe e o instalador) devem ser **assinados digitalmente**.

> **Estado:** o `.exe` e o instalador são gerados **sem assinatura** por defeito —
> funciona, mas mostra aviso. A assinatura é um passo de execução comercial que
> depende de um certificado comprado. O `build.bat` **já assina automaticamente** quando
> existir o `.pfx` em `cert\maouse.pfx`. Este guia explica o que falta: **comprar o
> certificado (OV é suficiente desde 2026)** — atualizado 2026-09-03.

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

> **Posso fazer tudo sozinho se me deres apenas o `.pfx` + password (não via chat — coloca-os
> num local seguro no disco).** O `build.bat` **já assina automaticamente** quando encontra o
> certificado em `cert\maouse.pfx` (ou via argumentos/variáveis). Só falta o certificado.

## Passos

### 1. Comprar/gerar o certificado

Seguir a CA escolhida. No final recebes um `.pfx` + password.

> ⚠️ **O passo 1 é o único passo comercial/PKI que não consigo executar por ti**:
> requer a compra do certificado numa CA e a verificação da identidade da entidade
> (documentos da empresa + comprovativo de morada). O resto do processo (guardar o `.pfx`,
> correr o `build.bat`, verificar) já está automatizado.

### 2. Guardar o `.pfx` onde o build o encontra automaticamente

Coloca o certificado em `cert\maouse.pfx` na raiz do projeto (o `cert\` está no `.gitignore`
— `.pfx` **nunca** vai para o git). O `build.bat` deteta-o sozinho:

```
cert\maouse.pfx   ← raiz do projeto (o .gitignore já ignora *.pfx)
```

A password pode ser passada por:
- **Variável de ambiente** `PFX_PASS` (recomendado — não fica no histórico do shell);
- ou argumento: `build.bat cert\maouse.pfx <password>`.

### 3. Correr o build (assina tudo automaticamente)

```bat
build.bat
```

Com o certificado presente, o `build.bat`:
1. Assina `dist\AirMouse\AirMouse.exe` (SHA256 + timestamp) — passo `[5/6]`;
2. Assina também o instalador Inno Setup (passa o `.pfx` ao `installer.iss`) — passo `[6/6]`.

Sem certificado, o build continua mas fica **NÃO assinado** (SmartScreen/AV avisam) — é o estado atual.

### 4. Verificar a assinatura

```powershell
Get-AuthenticodeSignature "dist\AirMouse\AirMouse.exe"
Get-AuthenticodeSignature "dist\Maouse-Setup-1.0.0.exe"
```

Deve aparecer `Status: Valid` e o Publisher correto ("Luar Studio Angola").

---

## Escolha da CA (para a entidade PT/Angola)

> **Recomendação (atualizada 2026): começar por OV, não EV.** Desde as atualizações de 2026 a
> Microsoft trata os EV **da mesma forma** que os OV — o EV já não "salta" o SmartScreen
> automaticamente e também precisa de construir reputação. **OV é suficiente** para apps desktop
> normais e bastante mais barato. EV só é obrigatório para **drivers de kernel / componentes do
> sistema Windows**.
>
> Preços indicativos (sem IVA, confirmar na CA — mudam e há revendedores mais baratos):
> Validade máxima dos certificados CODE desde 2026: **460 dias (~15 meses)**.

| CA | Tipo | Preço/ano (aprox.) | Nota p/ a nossa entidade |
|----|------|---------------------|--------------------------|
| **Certum Cloud Code Signing (OV)** | OV (empresa) | ~€99 | A opção mais barata p/ a empresa; CA europeia |
| **Certum Individual Cloud Code** | OV (individual) | ~€97–117 | Só para criador individual, **não** para empresa; útil como *stopgap* enquanto a entidade UE não existe |
| **Sectigo Code Signing (OV)** | OV | ~€220–350 (ou ~€499 em revendedor PT) | Bom equilíbrio preço/reconhecimento |
| **DigiCert Code Signing (OV)** | OV | ~€440–579 | Mais reconhecido; pensado p/ empresas reguladas |
| **Sectigo / DigiCert EV** | EV | ~€300–750 | **Desnecessário** em 2026 p/ desktop (ver acima); só para drivers de kernel |

> **Dica de custo:** como a `Luar Studio Angola` é uma empresa, o certificado tem de ser **OV de
> empresa** (pede NIF/VAT + registo). Se a **entidade UE ainda não estiver constituída** (está em
> curso no `PLANO_DE_EXECUCAO_90_DIAS` §1.2), podes começar com um **Certum Individual** em teu
> nome enquanto a empresa formaliza — depois reemites para a empresa.

> **Não usar certificados self-signed** para distribuição pública — não removem o SmartScreen.

## Checklist de compra (fazer, não automatizável)

- [ ] Escolher CA e tipo (**recomendo OV** — suficiente e barato em 2026; EV não é necessário p/ desktop).
- [ ] Reunir documentos da entidade (certidão do registo, NIF/VAT, morada, representante legal). Se a entidade UE ainda não existir, considerar **Certum Individual** como stopgap (e reemitir depois p/ a empresa).
- [ ] Comprar o certificado (validade máx. **460 dias** desde 2026; renovar antes de expirar).
- [ ] Descarregar o `.pfx` + guardar a password num cofre de passwords.
- [ ] Colocar em `cert\maouse.pfx`.
- [ ] Correr `build.bat` e verificar com `Get-AuthenticodeSignature` → `Status: Valid` + Publisher "Luar Studio Angola".
- [ ] **Construir reputação SmartScreen** (ver Notas abaixo): mesmo assinado, um certificado novo pode ainda mostrar SmartScreen até ganhar reputação — isso acontece com downloads e instalações legítimas a partir de sites com tráfego.

> **Cuidado com a chave primária:** perde o `.pfx`/password → a assinatura fica órfã e as
> atualizações passam a mostrar SmartScreen de novo. Guarda cópia segura (offline + cofre).

## Notas
- O timestamp (`/tr .../td SHA256`) é importante para a assinatura continuar válida
  depois de o certificado expirar.
- Guarda o `.pfx` e a password num cofre de passwords; se perderes a chave, a assinatura fica órfã.
- **Reputação SmartScreen:** desde 2024/2026 a Microsoft já não confia automaticamente em nenhum
  certificado novo (nem EV). Um assinante sem reputação pode ainda mostrar SmartScreen nos
  primeiros downloads. Isso resolve-se com distribuição legítima e volume (site real com tráfego,
  downloads de vários utilizadores) — não é um bug da assinatura.
- Para a **Microsoft Store** o processo é diferente (certificado de Publisher + MSIX), fora deste guia.
