# Prontidão Técnica para Venda — Mãouse (AirMouse)

> Estado real do produto face à primeira venda paga. Resultado de uma auditoria técnica
> profissional com agentes (revisão read-only, sem modificações de código).
> **Data:** 2026-09-01 · Autor: Luar Studio Angola.
> **Legenda:** ✅ Pronto · ⚠️ Parcial · 🔴 Bloqueador de receita.

---

## 0. Veredito rápido

O **motor de produto** (precisão, gestos, voz, snap, mobile engine) é real e testado —
qualidade genuína. Mas **nada protege nem captura a primeira venda**:

- 🔴 **Não há licenciamento nem pagamento** no desktop (zero código de licença/Paddle/Stripe).
- 🔴 **Não há gate Free/Pro** — 100% do produto corre de graça hoje.
- 🔴 **O `.exe` não está assinado, sem versão/ícone**, `console=True` → SmartScreen/AV + não passa Microsoft Store.
- 🔴 **As ações nativas do mobile não funcionam** — sem AccessibilityService/modulos; taps fazem no-op.
- 🔴 **Sem IAP no mobile** e o listing/posicionamento de acessibilidade está por fazer.

> **Conclusão:** o produto é **excelente como demo/freeware**, mas **não está pronto para ser
> vendido** por €39,90/€4,99. Os bloqueadores abaixo são todos de **execução comercial**, não
> de feature nova — devem entrar no `PLANO_DE_EXECUCAO_90_DIAS.md` antes de qualquer feature.

---

## 1. Desktop (Windows)

| Item | Estado | Detalhe verificado |
|---|---|---|
| Build `.exe` (PyInstaller) | ✅ | `dist\AirMouse\AirMouse.exe` (15,6 MB) existe; 709 MB com modelos; build smokes sem erros |
| **Code-signing** | 🔴 | `Get-AuthenticodeSignature` → **NotSigned**; nenhum cert/signtool; SmartScreen/AV garantido |
| Metadados do `.exe` (versão/empresa/ícone) | 🔴 | `console=True`, `icon=None`, sem VersionInfo → `FileVersion 0.0.0.0`, sem branding |
| Instalador (1-clique) | 🔴 | Só pasta zipada; sem NSIS/Inno/MSIX/AppX; sem packaging Microsoft Store |
| **Licenciamento/chave/ativação** | 🔴 | Zero código de licença/key/Paddle/Stripe em todo o Python |
| **Gate Free vs Pro** | 🔴 | Nenhum watermark/flags/entitlement; snap, voz, 2 mãos, TTS correm sempre de graça |
| Testes | ✅ | `tests/test_config.py` 7/7 · `tools/test_v3.py` 17/17 · `test_left_hand.py` 15/15 · `test_hand_lock.py` 13/13 (sem câmara) |
| Lint (ruff) | ⚠️ | 45 erros (E501 maioritário); um CI falharia hoje; sem CI configurado |

---

## 2. Mobile (Android / Play Store)

| Item | Estado | Detalhe verificado |
|---|---|---|
| App Expo SDK 57 + engine | ✅ | `mobile/src` real: gestures, filters (One Euro), hooks, store, App.tsx com frame-processor MediaPipe |
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
| Desktop — gateway (Paddle D2) | 🔴 Zero código |
| Desktop — validação de chave/serial | 🔴 Zero |
| Desktop — servidor de ativação/webhook | 🔴 Zero |
| Mobile — IAP | 🔴 Zero |
| Telemetria opt-in (D6) | ⚠️ Sem endpoint/implementação |

---

## 4. TOP 5 bloqueadores técnicos → 1ª venda paga

| # | Bloqueador | Página do plano |
|---|---|---|
| 1 | **Licenciamento + pagamento desktop** (Paddle D2, ativação) | S2 |
| 2 | **Gate Free/Pro + watermark + upgrade Pro** | S2 |
| 3 | **`.exe` polido**: assinatura EV, ícone, versão/empresa, `console=False`, instalador 1-clique | S2 |
| 4 | **Ações nativas Android** + `AccessibilityService` + remover permissões sem uso | S2 |
| 5 | **IAP mobile + store listing** posicionado acessibilidade + privacy policy + icons Mãouse | S2 |
| 6 | **LAB de compatibilidade** (mover o gargalo de hardware para `HARDWARE/`): matriz Validado/Aceite/Não-validado preenchida em ≥5 devices por categoria crítica — evita prometer universalidade e **previne reembolsos (D7)** | S1–S2 |

---

## 5. Decisão de roadmap (recomendada)

Pré-requisito de "vendável" e **entra antes de feature nova**:

1. **Licenciamento + gate Free/Pro + Paddle** (desktop) → fecha o modelo de receita D1/D2.
2. **Ferramenta de assinatura EV + pack MSIX**: distribuir via Microsoft Store (evita SmartScreen e o pior do AV). Alternativa imediata: `.exe` assinado + instalador Inno.
3. **Mobile:** implementar as 3 ações nativas Android + `AccessibilityService`, remover permissões mortas, adicionar IAP, submeter com posicionamento acessibilidade.
4. **Higiene de qualidade:** zerar os 45 erros de ruff, adicionar CI, trocar LICENSE desktop do template pelo do estúdio, reconciliar marca "Mãouse" vs "AirMouse" em todo o produto.
5. **LAB de hardware (área `HARDWARE/`):** preencher a `MATRIZ_DE_DISPOSITIVOS.md` com ≥5 devices por categoria crítica (desktop com GPU, desktop CPU fraco, mobile low-end) usando `HARDWARE/LAB.md` + `CHECKLIST_VALIDACAO.md`, e registar falhas em `HARDWARE/PROBLEMAS_KNOWN.md`. **Critério de "go":** ter pelo menos **1 ✅ Validado por categoria crítica** + este LAB a correr — é o que sustenta promessas honestas e reduz reembolsos (D7).

> **Nota de honestidade:** mesmo após estes bloqueadores, o produto estará *vendável* apenas no
> desktop consumer/mobile freeware; o pilar institucional (pacote compliance) **exige a auditoria
> WCAG independente + seguro RC + entidade UE** (ver `REVISAO_ESTRATEGICA.md`), antes de vender
> "conformidade" a hospitais. E, por causa do **gargalo de hardware**, o institucional exige ainda
> **≥5 ✅ por categoria crítica + 1 piloto real + o LAB a documentar** (ver `MATRIZ_DE_DISPOSITIVOS.md` §6.1).

---

*Auditoria técnica — Luar Studio Angola · 2026. Complementa PLANO_DE_EXECUCAO_90_DIAS.md e DECISOES.md.*
