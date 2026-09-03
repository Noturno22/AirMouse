# Validação Mobile em Device — Mãouse (Android)

> Checklist operacional para confirmar que o **reconhecimento de gestos** funciona no device
> após `npx expo prebuild --clean` + rebuild. É o bloqueio atual antes da Play Console
> (ver `BUSSINES/04_MARKETING_E_VENDAS/PLAY_CONSOLE_ETAPA.md`).
> **Data:** 2026-09-03 · Autor: Luar Studio Angola · Estado: **por executar (requer device Android).**

---

## 0. Pré-requisitos

- [ ] Correr `npx expo prebuild --clean` (na pasta `mobile/airmouse-mobile`).
- [ ] Correr `npm install` (reconciliar dependências).
- [ ] Build/install num **telemóvel Android real** (não emulador): `npx expo run:android` ou
      EAS dev build.
- [ ] Confirmar no overlay debug que aparece **`plugin:Y`** (se aparecer `plugin:N`, o plugin
      nativo `handLandmarker` não foi registado — ver §3).

> O `android/` e `ios/` são regenerados pelo prebuild e gitignored — nenhuma alteração nativa
> atual se perde (tudo é re-injetado por plugins: `with-airmouse-native` + `expo-vision-camera-v4-mediapipe`).

## 1. Verificar no overlay debug (primeiro sinal)

Ao abrir a app com a câmara ativa, o overlay amarelo no fundo mostra:

```
plugin:Y hands:N err:...
```

| Campo | Esperado | Se não |
|---|---|---|
| `plugin` | **Y** | `N` → plugin nativo não registado (ver §3) |
| `hands` | **≥1 quando a mão está à frente da câmara** | 0 → problema de deteção (ver §3) |
| `err` | vazio | Mostra o erro retornado pelo plugin |

## 2. Volta completa de gestos (devagar, boa luz)

Posicionar a mão a ~30–50 cm da câmara frontal, palmada aberta. Percorrer pela ordem:

- [ ] **Mão aberta** → mover cursor (badge muda para o gesto, FPS atualiza)
- [ ] **Pinça (polegar+indicador)** → clique esquerdo
- [ ] **Pinça médio** → clique direito
- [ ] **Punho** → arrastar; **soltar** → largar
- [ ] **Dois dedos (paz)** → scroll
- [ ] **Três dedos** → volume
- [ ] **Um dedo** → mover 1D
- [ ] **Polegar pra cima** → play/pause
- [ ] **Shaka** → colar
- [ ] Afastar a mão → gesto `NONE` (palm center some após ~6 frames vazios)

> Se marcares gestos a funcionar mas com FPS baixo, ver `HARDWARE/` + `MATRIZ` (alvo ≥15 fps mobile baixo).

## 3. Se NÃO detetar gestos (debug)

Já foi feita limpeza/auditoria estática (2026-09-03): removidos `useHandDetection.ts`
(import inválido) e `useGestures.ts` (dead) e a dependência duplicada
`react-native-worklets@0.10.1` (conflito conhecido que trava o frame processor). O caminho
ativo está no `App.tsx` e usa a API correta de VisionCamera v4.

Ordem de diagnóstico se ainda falhar:

1. **`plugin:N`** → o `handLandmarker` não está registado. Confirmar no `MainApplication.kt`
   gerado que existe `FrameProcessorPluginRegistry.addFrameProcessorPlugin("handLandmarker")`.
   Se não existir, o prebuild não aplicou o plugin `expo-vision-camera-v4-mediapipe` — ver
   `app.json` (está no array de plugins) e re-correr `npx expo prebuild --clean`.
2. **`plugin:Y` mas `hands:0` sempre** → problema na deteção. Abrir o logcat:
   `adb logcat | grep -i handlandmarker` — procurar `=== ERROR INITIALIZING landmarkers ===`
   (modelo não encontrado em assets) ou `ERROR in detection callback` (exceção por frame).
3. **`hands:0` e FPS muito baixo / sem FPS** → o frame processor pode não estar a correr.
   Confirmar que **não** há dois pacotes worklets no `package-lock.json`
   (`react-native-worklets` E `react-native-worklets-core` juntos = bug). Deve ficar só o
   `react-native-worklets-core`.
4. Meter o erro do overlay na `HARDWARE/PROBLEMAS_KNOWN.md` §2 (não em conversa), para não re-testar.

## 4. Afinar gestos ao vivo (sem rebuild)

Os parâmetros são controlados pelo `useSettingsStore` (`src/store/index.ts`). Para afinar sem
recompilar, altera os defaults e grava (Metro HMR recarrega):

| Knob | Default | Quando ajustar | Faixa típica |
|---|---|---|---|
| `pinchOnRatio` | 0.38 | Clique não deteta (aumentar) / cliques fantasma (diminuir) | 0.30–0.45 |
| `pinchOffRatio` | 0.55 | Soltar trava (aumentar) / solta cedo de mais (diminuir) | 0.50–0.65 |
| `moveGain` | 2.0 | Cursor lento (aumentar) / rápido (diminuir) | 1.2–3.0 |
| `filterMinCutoff` | 1.4 | Tremor (diminuir) / lag (aumentar) | 1.0–2.0 |
| `filterBeta` | 0.028 | Resposta (aumentar) / suavidade (diminuir) | 0.015–0.05 |

> Regra: muda **um** parâmetro de cada vez, anota o resultado. Só persiste num PR depois de
> 2 devices confirmarem o mesmo comportamento.

## 5. Teste Pro (free → paywall) no mesmo device

- [ ] Com a conta **free**, fazer um gesto de ação (ex.: pinça) → deve abrir o **ProGate**
      paywall e **não** enviar o comando nativo.
- [ ] Fechar o ProGate e confirmar que a pré-visualização de gestos continua (badge muda).
- [ ] (Quando o produto `maouse_mobile_pro` existir no Play Console) comprar/restaurar →
      validar em `{licenseServerUrl}/api/v1/mobile/entitle` e desbloquear gestos nativos.
      Sem produto no Play Console, usar `AIRMOUSE_MOBILE_DEV_ALLOW=1` no license-server para
      tokens `test_` (nunca em produção).

> **Go/No-go:** só se marca o bloqueio "gestos" como fechado quando a §2 passar na totalidade
> num device real. Depois disso sim, criar a conta Play Console ($25).

---

*Validação operacional — Luar Studio Angola · 2026. Complementa `HARDWARE/` e `PLAY_CONSOLE_ETAPA.md`.*
