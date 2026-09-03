# Mãouse — Mobile

Controle total do telemóvel usando gestos de mão detetados pela câmara frontal.

## Funcionalidades

- **Mover cursor** - Mão aberta ou indicador levantado
- **Tap/Selecionar** - Pinça polegar+indicador
- **Clique direito** - Pinça polegar+médio
- **Arrastar** - Punho fechado
- **Scroll** - Dois dedos (peace sign)
- **Volta/Início** - Atalhos de sistema
- **Acessibilidade** - Navegação por foco

## Pré-requisitos

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Telemóvel com Expo Go ou Android Studio/iOS Simulator

## Instalação

```bash
cd mobile/airmouse-mobile
npm install
```

## Executar

```bash
# Development
npx expo start

# Android
npx expo start --android

# iOS
npx expo start --ios
```

## Estrutura do Projeto

```
airmouse-mobile/
├── App.tsx                    # Componente principal + gate de gestos Pro
├── src/
│   ├── engine/
│   │   ├── filters.ts         # One Euro Filter + AccelCurve
│   │   └── gestures.ts        # Deteção de gestos
│   ├── hooks/
│   │   ├── useGestures.ts     # Hook de processamento
│   │   └── useProEntitlement.ts  # IAP (expo-iap) + validação server-side + restore
│   ├── store/
│   │   ├── index.ts           # Zustand store
│   │   └── license.ts         # Zustand store de licença (tier free/mobile_pro)
│   ├── components/
│   │   └── ProGate.tsx        # Paywall Pro (comprar/restaurar/continuar gratis)
│   ├── services/
│   │   └── licenseApi.ts      # Cliente do license-server (/api/v1/mobile/entitle)
│   ├── utils/
│   │   └── deviceId.ts        # UUID persistente do dispositivo
│   ├── types/
│   │   └── gesture.ts         # Tipos TypeScript
│   └── constants/
│       └── index.ts           # Constantes
└── app.json                   # Configuração Expo (+ plugin expo-iap, extra license)
```

## Configuração

Parâmetros ajustáveis no `src/store/index.ts`:

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `moveGain` | 2.0 | Velocidade do cursor |
| `filterMinCutoff` | 1.4 | Filtro One Euro (suavidade) |
| `filterBeta` | 0.028 | Aceleração do filtro |
| `pinchOnRatio` | 0.38 | Sensibilidade pinça |
| `pinchOffRatio` | 0.55 | Histerese pinça |

## Próximos Passos

1. Integrar MediaPipe Hand Landmarker
2. Criar módulos nativos (Android/iOS)
3. Implementar ações de sistema
4. Adicionar controlo de voz
5. Calibração automática

## Compras Pro (IAP)

A versão gratuita navega/pré-visualiza; o controlo de gestos completo desbloqueia com a **compra
única** `maouse_mobile_pro` (Google Play), validada server-side.

- **Compra** → `useProEntitlement().purchasePro()` (produto IAP `maouse_mobile_pro`).
- **Validação** → `POST {licenseServerUrl}/api/v1/mobile/entitle` valida o `purchaseToken` na
  Google Play Billing API e emite um lease JWT (`tier=mobile_pro`). Sem validação do servidor,
  a transação **não** é finalizada (replay seguro).
- **Restore** → `restorePro()` (getAvailablePurchases + revalidação).
- **Gate** → `App.tsx` só envia gestos nativos se `proEntitlement.isPro`; caso contrário mostra `ProGate`.

### Configuração (app.json -> extra)

| Chave | Valor | Descrição |
|-------|-------|-----------|
| `licenseServerUrl` | `https://license.maouse.app` | Base URL do license-server |
| `mobileProductId` | `maouse_mobile_pro` | Product ID do Pro (pago único) no Play Console |
| `androidPackage` | `com.airmouse.mobile` | Package Android |

> **Builds nativos:** o `expo-iap` requer **custom dev client / prebuild**. Requer Android SDK:
> `npx expo prebuild --clean` antes de fazer build/upload para o Play Console.
> No license-server, define `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` (conta de serviço com permissão
> "Android Publisher") — sem isso a validação só corre em modo dev (`AIRMOUSE_MOBILE_DEV_ALLOW=1`, nunca em produção).

## Licença

MIT
