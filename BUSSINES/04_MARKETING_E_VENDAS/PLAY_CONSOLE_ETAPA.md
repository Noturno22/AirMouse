# Play Console — Etapa de Lançamento Mobile (Mãouse)

> **Objetivo:** documentar o que é necessário para colocar a app Mãouse na Google Play Store,
> incluindo o custo da conta (Play Console) e o estado real do development mobile.
> **Data:** 2026-09-03 · Autor: Luar Studio Angola · Estado: **planeado / aguardando decisão de custo**

---

## ⚠️ Estado real do mobile (importante ler primeiro)

O código do **paywall Pro / IAP** (Play Billing) **já está implementado** e validado:
- Client: `mobile/airmouse-mobile/` — `expo-iap`, `ProGate`, `useProEntitlement`, `licenseApi`
- Server: `license-server/` — endpoint `/api/v1/mobile/entitle`, validação na Play Developer API (`playstore.py`)
- ✅ TypeScript typecheck passa · ✅ testes server + client passam

**MAS a app ainda NÃO está funcional** — o utilizador relatou que o mobile **não deteta nenhum
gesto ainda**. **Sem gestos a funcionar, não há produto para submeter à Play Store** — a Conta
Play Console é útil **só depois** de o reconhecimento de gestos estar a funcionar.

> **Conclusão:** a Play Console não é o próximo passo. O próximo passo é **fazer o mobile detetar
> gestos** (debug do frame processor e do modelo MediaPipe no dispositivo). Só depois de a app
> funcionar é que faz sentido pagar e criar a conta Play Console.

### ✔ Validação estática feita (2026-09-03) — o que encontrei e corrigi

Auditei o pipeline de deteção de gestos (nativo + JS). **O wiring nativo está correto**:
- `MainApplication.kt` regista o plugin `handLandmarker` via `FrameProcessorPluginRegistry`
  (nome bate certo com o `initFrameProcessorPlugin('handLandmarker')` do `App.tsx`).
- Asset `hand_landmarker.task` presente em `android/app/src/main/assets`.
- Versões compatíveis: `react-native-vision-camera@4.7.3` + `react-native-worklets-core@1.6.3`.

**Corrições aplicadas (code, $0):**
1. **Removido `src/hooks/useHandDetection.ts` (dead e partido)** — importava
   `detectHandLandmarks` de `expo-vision-camera-v4-mediapipe`, que **não exporta essa função**
   (é uma **global nativa** injetada, não um export — ver `index.js` do pacote). Se fosse usado,
   rebentava (`detectHandLandmarks is not a function`) e matava o frame processor.
2. **Removido `src/hooks/useGestures.ts` (dead)** e o import orfão em `App.tsx` — o caminho real
   usa o frame processor inline no `App.tsx`, que está correto.
3. **Removida dependência duplicada `react-native-worklets@0.10.1`** do `package.json` — coexistia
   com a correta `react-native-worklets-core@1.6.3`; dois pacotes worklets é uma causa conhecida
   de o frame processor não correr. (`npm install` reconciliado; typecheck ✅ EXIT 0.)

**⚠️ Ainda por confirmar (requer device/rebuild real, fora deste ambiente):** o motivo de "não
detetar gestos" pode ser puramente **build obsoleto no device** — as alterações nativas
(MediaPipe, plugin `handLandmarker`, expo-iap) foram adicionadas **depois** do último `prebuild`.
**Para validar:** re-correr `npx expo prebuild --clean` + rebuild/install no device Android e
re-testar. Isto NÃO é um custo ($0), é o bloqueio atual. Até lá, não criar a conta Play Console.

---

## 1. Custo da conta Play Console

| Item | Custo | Notas |
|---|---|---|
| **Registo de developer da Google Play (Play Console)** | **$25 USD** (pagamento único) | Taxa única de registo, pago 1 vez para sempre |
| Re-registo (se a conta for encerrada por inatividade/compliance) | $25 (de novo) | Evita-se mantendo a conta ativa |
| **Google Cloud** (conta de serviço p/ validar IAP) | **$0** | Free tier; só é preciso a API Play Developer ativada |
| Publicar apps | $0 | Publicação de apps é grátis depois do registo |

> A taxa de $25 é paga **uma vez** na criação da conta de developer. Google Cloud (para o
> `playstore.py` validar compras) é gratuito no free tier.

---

## 2. Passos da Play Console (quando o mobile estiver funcional)

### Pré-requisitos
- [ ] **Mobile funcional** — gestos detetados no dispositivo (bloqueio atual)
- [ ] Domínio próprio da marca (`maouse.app` / `maouse.pt`) para a privacy policy
- [ ] Privacy policy pública (obrigatória) — `maouse.app/privacy`
- [ ] Conta Google + método de pagamento (para os $25)

### 2.1 Criar conta de developer
1. Ir a https://play.google.com/console/
2. Pagar os $25 de registo (nome da empresa: **Luar Studio Angola**)
3. Preencher dados de developer (nome, email de contacto, website)
4. Verificação de identidade (pode pedir documento)

### 2.2 Criar o produto IAP "maouse_mobile_pro"
1. No Play Console: **Monetização → Produtos → Produtos no app**
2. Criar produto **compra única (one-time)** com ID `maouse_mobile_pro`
3. Definir preço regional (USD + EUR + R$ + Kz conforme roadmap)

### 2.3 Criar a conta de serviço (para o license-server validar compras)
1. **Google Cloud Console** → criar projeto
2. Ativar a **Android Publisher API** (Google Play Developer API)
3. Criar **conta de serviço** + chave JSON
4. Ligar a conta de serviço ao projeto no Play Console
   (Users & permissions → dar permissão "Ver dados financeiros" / "Ver compras")
5. Colocar o conteúdo do JSON em `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` no license server

### 2.4 Submeter a app
- Seguir o `LISTINGS_DE_LOJA.md` (listings PT-BR + EN, screenshots, ícones)
- Checklist de submissão completa (ver §8 do LISTINGS_DE_LOJA.md)
- Deploy do license server no Render (endpoint `/api/v1/mobile/entitle` acessível por HTTPS)

---

## 3. Ordem recomendada (evitar gastar cedo demais)

| Etapa | Custo | Quando |
|---|---|---|
| 1. Fazer o mobile detetar gestos | $0 | **Agora** (bloqueio atual) |
| 2. Polir UX mobile + testar em dispositivo | $0 | Depois de gestos OK |
| 3. Deploy license server (Render free tier) | $0 | Em paralelo |
| 4. Criar Play Console ($25) | $25 | **Só depois** de o mobile funcionar |
| 5. Criar produto IAP + conta serviço Google Cloud | $0 | Depois de pagar Play Console |
| 6. Submeter à Play Store | $0 | Último passo |

> **Princípio:** não pagar os $25 do Play Console até o mobile estar a **detetar gestos** e o
> produto estar mínimo-vável. Até lá, todo o work está em código (custo $0).

---

## 4. Custos relacionados (documentados em `CUSTOS_DE_LANCAMENTO.md`)

| Serviço | Custo | Estado |
|---|---|---|
| Google Play (Developer Console) | $25 pagamento único | **Não criada** — aguarda mobile funcional |
| Google Cloud (conta de serviço) | $0 | Não criada |
| Render (deploy license server) | $0 free tier | Código pronto; não deployado |
| Email transacional (SMTP) | $0 free tier | Não configurado |

---

## 5. Estado do código (o que já existe vs. o que falta)

**✅ Já existe (código, $0):**
- Paywall Pro (expo-iap) no mobile — `ProGate`, `useProEntitlement`, `licenseApi`
- Validação server-side de IAP — `playstore.py`, `/api/v1/mobile/entitle`
- Deploy config (Dockerfile + render.yaml)
- Keypair ES256 gerado

**❌ Falta (custos/operacional):**
- **Rebuild + teste em device** — re-correr `npx expo prebuild --clean` + re-instalar no Android e confirmar que os **gestos são detetados** (bloqueio central atual; dead-ware/duplicatas já corrigidas, mas preciso de device real)
- Conta Play Console ($25)
- Conta de serviço Google Cloud ($0)
- Deploy do license server no Render ($0)
- Produto IAP real na Play Console

---

*Documento operacional — Luar Studio Angola · Complementa `LISTINGS_DE_LOJA.md` e `CUSTOS_DE_LANCAMENTO.md`.*
