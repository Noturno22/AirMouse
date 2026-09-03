# Prontidão Técnica para Venda — Mãouse (AirMouse)

> Estado real do produto face à primeira venda paga. Resultado de uma auditoria técnica
> profissional com agentes (revisão read-only, sem modificações de código).
> **Data:** 2026-09-03 (atualizado) · Autor: Luar Studio Angola.
> **Legenda:** ✅ Pronto · ⚠️ Parcial · 🔴 Bloqueador de receita.

---

## 0. Veredito rápido

O **motor de produto** (precisão, gestos, voz, snap, mobile engine) é real e testado —
qualidade genuína. O **licenciamento desktop** está implementado (servidor FastAPI + SQLite
com trial server-authoritative, chaves MAO-, ativação por fingerprint, leases JWT ES256 e
gate no `process_frame`). O **pagamento automático Paddle está operacional** (webhook →
emissão de chave + email). Mas **faltam etapas de execução comercial** para capturar a primeira
venda paga:

- 🔴 **O `.exe` não está assinado** (o único que falta no #1: versão/ícone/console já estão ✅) → SmartScreen/AV.
- ✅ **Ações nativas Android funcionam** — `AccessibilityService` + Touch/Keyboard/System modules ligados no JS (2026-09-03).
- 🔴 **Sem IAP no mobile** e o listing/posicionamento de acessibilidade está por fazer.
- ✅ **Paddle checkout integrado** — webhook `transaction.completed` emite a chave `MAO-` e envia por email (2026-09-03).
- ✅ **Higiene de qualidade** — ruff 0 erros + CI GitHub Actions (feito em 2026-09-02).

> **Conclusão (atualizado 2026-09-03):** o produto tem licenciamento funcional (trial + chave + lease),
> **pagamento automático Paddle operacional** (webhook → emissão de chave + email), ações nativas
> Android a funcionar, instalador Inno Setup funcional e `.exe` com versão/ícone/`console=False`.
> Falta principalmente a **assinatura de código** (certificado EV/OV ×PFX — passo comercial/PKI) e o
> **IAP/listing mobile**. Os bloqueadores abaixo são de **execução comercial** — devem entrar no
> `PLANO_DE_EXECUCAO_90_DIAS.md` antes de qualquer feature nova.

---

## 1. Desktop (Windows)

| Item | Estado | Detalhe verificado |
|---|---|---|
| Build `.exe` (PyInstaller) | ✅ | `dist\AirMouse\AirMouse.exe` (18 MB) existe; build smokes sem erros |
| **Code-signing** | 🔴 | `Get-AuthenticodeSignature` → **NotSigned**; falta apenas o **certificado** ×PFX (signtool já existe; `build.bat` assina automaticamente quando o cert estiver presente) |
| Metadados do `.exe` (versão/empresa/ícone) | ✅ | `console=False`, `icon=maouse.ico`, VersionInfo via `version_info.txt` → `FileVersion 1.0.0`; `ProductName Mãouse`; `CompanyName Luar Studio Angola` (verificado no exe real) |
| Instalador (1-clique) | ✅ | Inno Setup `installer.iss` existe; `dist/Maouse-Setup-1.0.0.exe` (159 MB) gerado com sucesso; `VersionInfo*` + `SetupIconFile` + code-signing condicional via `/DPfxPath` |
| **Licenciamento/chave/ativação** | ✅ | `core/licensing.py` + `core/license_client.py` + `core/fingerprint.py` + `license-server/` completo (FastAPI+SQLite+ES256) — trial 30min server-authoritative, chaves MAO-, ativação por fingerprint, leases JWT |
| **Gate Free vs Pro** | ✅ | `core/engine.py:process_frame` bloqueia quando trial/lease expira; `ui/license_dlg.py` para upgrade/desativação |
| Paddle checkout (pagamento automático) | ✅ | Webhook `transaction.completed` verifica HMAC, dedup por `event_id`, emite chave `MAO-` e envia por email (`license-server/paddle.py` + `POST /webhooks/paddle`) |
| Testes | ✅ | 61 testes client (tests/) + **32 testes server** (license-server/tests/) — todos passam |
| Lint (ruff) | ✅ | 0 erros (resolvido 2026-09-02); CI GitHub Actions configurado (`.github/workflows/ci.yml`) |

---

## 2. Mobile (Android / Play Store)

| Item | Estado | Detalhe verificado |
|---|---|---|
| App Expo SDK 57 + engine | ✅ | `mobile/airmouse-mobile/src` real: gestures, filters (One Euro), hooks, store, App.tsx com frame-processor MediaPipe |
| EAS Build config | ✅ | `eas.json` (dev/preview/production) + `submit.production`; projectId configurado |
| **Ações nativas Android (Touch/Keyboard/System)** | ✅ | `AirMouseAccessibilityService` (tap/longPress/swipe/drag + back/home/recents/notif) declarado no Manifest; `TouchControllerModule`/`KeyboardControllerModule`/`SystemControllerModule` registados no `MainApplication` e ligados no JS (`App.tsx` → `handleAction`). Sem root. **2026-09-03** |
| iOS (modo remoto) | ⚠️ | `TouchController.swift`/`SystemController.swift` são **stubs de API privada** ("may cause App Store rejection"); não funcionais |
| **IAP / Play Billing** | 🔴 | Sem expo-iap/RevenueCat; sem product IDs/fluxo/restore |
| Store listing / posicionamento acessibilidade | 🔴 | Sem copy, sem privacy policy URL, sem vídeo de conformidade |
| Permissões sensíveis | ✅ | Removidas as permissões mortas `WRITE_SETTINGS` e `SYSTEM_ALERT_WINDOW` (e o `setBrightness` que dependia de `WRITE_SETTINGS`) de `app.json` + templates do plugin — sem risco de rejeição Play por permissões sem uso. **2026-09-03** |
| Marca/icons | ⚠️ | Icons "AirMouse"/template; `IDENTIDADE_VISUAL.md` marca como "precisa redesign p/ Mãouse"; LICENSE é o template MIT do Expo (não o do estúdio) |

---

## 3. Pagamento / Licenciamento

| Item | Estado |
|---|---|
| Desktop — gateway (Paddle D2) | ✅ Webhook de pagamento automático integrado (emite chave + envia por email) |
| Desktop — validação de chave/serial | ✅ Chaves MAO- com assinatura + fingerprint (core/licensing.py + license-server/) |
| Desktop — servidor de ativação/webhook | ✅ FastAPI + SQLite (license-server/) — health, keys, activate, trial, revalidate, revoke |
| Mobile — IAP | 🔴 Zero |
| Telemetria opt-in (D6) | ⚠️ Sem endpoint/implementação |

---

## 4. TOP bloqueadores técnicos → 1ª venda paga

| # | Bloqueador | Estado | Página do plano |
|---|---|---|---|
| 1 | **Assinatura digital do `.exe`** (certificado EV/OV ×PFX). Metadados/ícone/`console=False` e instalador já ✅; `build.bat` + signtool prontos a assinar automaticamente quando o cert existir | 🔴 Falta o certificado (passo comercial/PKI) | S2 |
| 2 | **IAP mobile + store listing** posicionado acessibilidade + privacy policy + icons Mãouse | 🔴 Falta | S2 |
| 3 | **LAB de compatibilidade** (mover o gargalo de hardware para `HARDWARE/`): matriz Validado/Aceite/Não-validado preenchida em ≥5 devices por categoria crítica — evita prometer universalidade e **previne reembolsos (D7)** | 🟡 Em recolha (diretriz: ≥ i3 4ª geração) | S1–S2 |

> **✅ Fechado em 2026-09-03:**
> - **Paddle checkout automático** (webhook de pagamento → emissão de chave `MAO-` + envio por email).
> - **Ações nativas Android** + `AccessibilityService` + remoção das permissões mortas.
> - **Metadados do `.exe`** (versão/empresa/ícone/`console=False`) + instalador + pipeline de assinatura automático no `build.bat`.

---

## 5. Decisão de roadmap (recomendada)

Pré-requisito de "vendável" e **entra antes de feature nova**:

1. **Assinatura digital do `.exe`**: adquirir certificado EV/OV de code-signing (×PFX) e correr `build.bat` — o pipeline já assina o `.exe` e o instalador automaticamente. (Metadados, ícone, `console=False` e instalador Inno Setup já estão ✅.)
2. **Mobile:** adicionar IAP + submeter com posicionamento de acessibilidade + privacy policy + icons Mãouse. (As ações nativas Android e a limpeza de permissões já estão feitas — 2026-09-03.)
3. **Higiene de qualidade:** ✅ ruff 0 erros + CI GitHub Actions + LICENSE do estúdio + marca "Mãouse" + Inno Setup installer funcional + **Paddle automático** — **feito em 2026-09-02/03**.
4. **LAB de hardware (área `HARDWARE/`):** preencher a `MATRIZ_DE_DISPOSITIVOS.md` com ≥5 devices por categoria crítica (desktop com GPU, desktop CPU fraco, mobile low-end) usando `HARDWARE/LAB.md` + `CHECKLIST_VALIDACAO.md`, e registar falhas em `HARDWARE/PROBLEMAS_KNOWN.md`. **Critério de "go":** ter pelo menos **1 ✅ Validado por categoria crítica** + este LAB a correr — é o que sustenta promessas honestas e reduz reembolsos (D7). **Dado recolhido (2026-09-03):** no desktop do estúdio (i3 4ª geração) funciona bem — a diretriz operacional é **"equivalente ou acima de um i3 de 4ª geração" como mínimo suportado**; abaixo disso o desempenho degrada.

> **Nota de honestidade:** mesmo após estes bloqueadores, o produto estará *vendável* apenas no
> desktop consumer/mobile freeware; o pilar institucional (pacote compliance) **exige a auditoria
> WCAG independente + seguro RC + entidade UE** (ver `REVISAO_ESTRATEGICA.md`), antes de vender
> "conformidade" a hospitais. E, por causa do **gargalo de hardware**, o institucional exige ainda
> **≥5 ✅ por categoria crítica + 1 piloto real + o LAB a documentar** (ver `MATRIZ_DE_DISPOSITIVOS.md` §6.1).

---

*Auditoria técnica — Luar Studio Angola · 2026. Complementa PLANO_DE_EXECUCAO_90_DIAS.md e DECISOES.md.*
