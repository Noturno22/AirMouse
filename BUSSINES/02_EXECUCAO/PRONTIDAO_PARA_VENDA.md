# Prontidão Técnica para Venda — Mãouse (AirMouse)

> Estado real do produto face à primeira venda paga. Resultado de uma auditoria técnica
> profissional com agentes (revisão read-only, sem modificações de código).
> **Data:** 2026-09-02 (atualizado) · Autor: Luar Studio Angola.
> **Legenda:** ✅ Pronto · ⚠️ Parcial · 🔴 Bloqueador de receita.

---

## 0. Veredito rápido

O **motor de produto** (precisão, gestos, voz, snap, mobile engine) é real e testado —
qualidade genuína. O **licenciamento desktop** está implementado (servidor FastAPI + SQLite
com trial server-authoritative, chaves MAO-, ativação por fingerprint, leases JWT ES256 e
gate no `process_frame`). Mas **faltam etapas de execução comercial** para capturar a primeira
venda paga:

- 🔴 **O `.exe` não está assinado, sem versão/ícone**, `console=True` → SmartScreen/AV + não passa Microsoft Store.
- 🔴 **As ações nativas do mobile não funcionam** — sem AccessibilityService/módulos; taps fazem no-op.
- 🔴 **Sem IAP no mobile** e o listing/posicionamento de acessibilidade está por fazer.
- ⚠️ **Paddle checkout não está integrado** — o licenciamento aceita chaves manuais e trial
  server, mas falta o fluxo de pagamento automático (Paddle D2 webhooks).
- ⚠️ **Higiene de qualidade** (ruff 0 erros + CI GitHub Actions) — **resolvido em 2026-09-02**.

> **Conclusão (atualizado 2026-09-03):** o produto tem licenciamento funcional (trial + chave + lease),
> mas **faltam o pagamento automático (Paddle) e os/polir comercial** (assinatura EV, instalador,
> store). Os bloqueadores abaixo são de **execução comercial**, não de feature nova — devem entrar
> no `PLANO_DE_EXECUCAO_90_DIAS.md` antes de qualquer feature.

---

## 1. Desktop (Windows)

| Item | Estado | Detalhe verificado |
|---|---|---|
| Build `.exe` (PyInstaller) | ✅ | `dist\AirMouse\AirMouse.exe` (15,6 MB) existe; 709 MB com modelos; build smokes sem erros |
| **Code-signing** | 🔴 | `Get-AuthenticodeSignature` → **NotSigned**; nenhum cert/signtool; SmartScreen/AV garantido |
| Metadados do `.exe` (versão/empresa/ícone) | 🔴 | `console=True`, `icon=None`, sem VersionInfo → `FileVersion 0.0.0.0`, sem branding |
| Instalador (1-clique) | ✅ | Inno Setup `installer.iss` existe; `dist/Maouse-Setup-1.0.0.exe` (15,6 MB) gerado com sucesso |
| **Licenciamento/chave/ativação** | ✅ | `core/licensing.py` + `core/license_client.py` + `core/fingerprint.py` + `license-server/` completo (FastAPI+SQLite+ES256) — trial 30min server-authoritative, chaves MAO-, ativação por fingerprint, leases JWT |
| **Gate Free vs Pro** | ✅ | `core/engine.py:process_frame` bloqueia quando trial/lease expira; `ui/license_dlg.py` para upgrade/desativação |
| Paddle checkout (pagamento automático) | 🔴 | Fluxo de pagamento Paddle D2 não integrado — o cliente aceita chaves manuais mas não há webhooks/checkout automático |
| Testes | ✅ | 61 testes client (tests/) + 15 testes server (license-server/tests/) — todos passam |
| Lint (ruff) | ✅ | 0 erros (resolvido 2026-09-02); CI GitHub Actions configurado (`.github/workflows/ci.yml`) |

---

## 2. Mobile (Android / Play Store)

| Item | Estado | Detalhe verificado |
|---|---|---|
| App Expo SDK 57 + engine | ✅ | `mobile/airmouse-mobile/src` real: gestures, filters (One Euro), hooks, store, App.tsx com frame-processor MediaPipe |
| EAS Build config | ✅ | `eas.json` (dev/preview/production) + `submit.production`; projectId configurado |
| **Ações nativas Android (Touch/Keyboard/System)** | 🔴 | **Não implementadas**; sem `AccessibilityService` no Manifest; `NativeModules.TouchController?.tap()` faz **no-op silencioso** em device real |
| iOS (modo remoto) | ⚠️ | `TouchController.swift`/`SystemController.swift` são **stubs de API privada** ("may cause App Store rejection"); não funcionais |
| **IAP / Play Billing** | 🔴 | Sem expo-iap/RevenueCat; sem product IDs/fluxo/restore |
| Store listing / posicionamento acessibilidade | 🔴 | Sem copy, sem privacy policy URL, sem vídeo de conformidade |
| Permissões sensíveis | ⚠️ | `WRITE_SETTINGS`/`SYSTEM_ALERT_WINDOW` declaradas **sem código que as use** → risco de rejeição Play |
| Marca/icons | ⚠️ | Icons "AirMouse"/template; `IDENTIDADE_VISUAL.md` marca como "precisa redesign p/ Mãouse"; LICENSE é o template MIT do Expo (não o do estúdio) |

---

## 3. Pagamento / Licenciamento

| Item | Estado |
|---|---|
| Desktop — gateway (Paddle D2) | 🔴 Sem integração de pagamento automático (chaves manuais e trial funcionam) |
| Desktop — validação de chave/serial | ✅ Chaves MAO- com assinatura + fingerprint (core/licensing.py + license-server/) |
| Desktop — servidor de ativação/webhook | ✅ FastAPI + SQLite (license-server/) — health, keys, activate, trial, revalidate, revoke |
| Mobile — IAP | 🔴 Zero |
| Telemetria opt-in (D6) | ⚠️ Sem endpoint/implementação |

---

## 4. TOP 5 bloqueadores técnicos → 1ª venda paga

| # | Bloqueador | Página do plano |
|---|---|---|
| 1 | **Paddle checkout automático** (webhook de pagamento → emissão de chave + envio por email) | S2 |
| 2 | **`.exe` polido**: assinatura EV, ícone, versão/empresa, `console=False`, instalador 1-clique | S2 |
| 3 | **Ações nativas Android** + `AccessibilityService` + remover permissões sem uso | S2 |
| 4 | **IAP mobile + store listing** posicionado acessibilidade + privacy policy + icons Mãouse | S2 |
| 5 | **LAB de compatibilidade** (mover o gargalo de hardware para `HARDWARE/`): matriz Validado/Aceite/Não-validado preenchida em ≥5 devices por categoria crítica — evita prometer universalidade e **previne reembolsos (D7)** | S1–S2 |

---

## 5. Decisão de roadmap (recomendada)

Pré-requisito de "vendável" e **entra antes de feature nova**:

1. **Paddle checkout** (webhook de pagamento → emissão automática de chave + envio por email) — fecha o modelo de receita D1/D2.
2. **`.exe` polido**: ferramenta de assinatura EV + pack MSIX/Inno (evita SmartScreen/AV). Alternativa imediata: `.exe` assinado + Inno.
3. **Mobile:** implementar as 3 ações nativas Android + `AccessibilityService`, remover permissões mortas, adicionar IAP, submeter com posicionamento acessibilidade.
4. **Higiene de qualidade:** ✅ ruff 0 erros + CI GitHub Actions + LICENSE do estúdio + marca "Mãouse" — **feito em 2026-09-02**.
5. **LAB de hardware (área `HARDWARE/`):** preencher a `MATRIZ_DE_DISPOSITIVOS.md` com ≥5 devices por categoria crítica (desktop com GPU, desktop CPU fraco, mobile low-end) usando `HARDWARE/LAB.md` + `CHECKLIST_VALIDACAO.md`, e registar falhas em `HARDWARE/PROBLEMAS_KNOWN.md`. **Critério de "go":** ter pelo menos **1 ✅ Validado por categoria crítica** + este LAB a correr — é o que sustenta promessas honestas e reduz reembolsos (D7).

> **Nota de honestidade:** mesmo após estes bloqueadores, o produto estará *vendável* apenas no
> desktop consumer/mobile freeware; o pilar institucional (pacote compliance) **exige a auditoria
> WCAG independente + seguro RC + entidade UE** (ver `REVISAO_ESTRATEGICA.md`), antes de vender
> "conformidade" a hospitais. E, por causa do **gargalo de hardware**, o institucional exige ainda
> **≥5 ✅ por categoria crítica + 1 piloto real + o LAB a documentar** (ver `MATRIZ_DE_DISPOSITIVOS.md` §6.1).

---

*Auditoria técnica — Luar Studio Angola · 2026. Complementa PLANO_DE_EXECUCAO_90_DIAS.md e DECISOES.md.*
