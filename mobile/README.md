# AirMouse Mobile - Guia Completo

## Visão Geral

**AirMouse Mobile** é um aplicativo React Native/Expo que permite controlar o telemóvel total usando gestos de mão detetados pela câmara frontal do dispositivo.

---

## Funcionalidades

### Gestos de Mão
| Gesto | Ação |
|-------|------|
| ✋ Mão aberta | Mover cursor |
| 🤏 Pinça (polegar+index) | Tap / Selecionar |
| 🤏🤞 Pinça (polegar+médio) | Clique direito |
| ✊ Punho | Arrastar |
| ✌️ Dois dedos | Scroll |
| ☝️ Um dedo | Mover (1D) |
| 👍 Polegar cima | Play/Pausa |
| 🤙 Shaka | Colar |
| ✋✊ Palmas | Voltar / Multitarefa |

### Ações de Sistema
- **Tap** → Selecionar item
- **Long Press** → Clique direito
- **Swipe** → Navegar
- **Scroll** → Rolar página
- **Volta** → Botão voltar
- **Início** → Ecrã inicial
- **Multitarefa** → Apps recentes
- **Notificações** → Barra de notificações
- **Volume** → Ajustar volume
- **Brightness** → Ajustar brilho

---

## Estrutura do Projeto

```
mobile/airmouse-mobile/
├── App.tsx                          # Componente principal
├── src/
│   ├── engine/
│   │   ├── filters.ts               # One Euro Filter + AccelCurve
│   │   └── gestures.ts              # Deteção de 12+ gestos
│   ├── hooks/
│   │   ├── useGestures.ts           # Hook de processamento
│   │   └── useHandDetection.ts      # Hook MediaPipe
│   ├── store/
│   │   └── index.ts                 # Zustand store
│   ├── types/
│   │   └── gesture.ts               # Tipos TypeScript
│   └── constants/
│       └── index.ts                 # Cores, labels, presets
├── android/                         # Módulos nativos Android
│   ├── TouchControllerModule.java
│   ├── KeyboardControllerModule.java
│   ├── SystemControllerModule.java
│   └── AirMousePackage.java
├── ios/                             # Módulos nativos iOS
│   ├── TouchController.swift
│   └── SystemController.swift
├── app.json                         # Config Expo
├── eas.json                         # Config EAS Build
└── package.json                     # Dependências
```

---

## Pré-requisitos

- **Node.js** 18+
- **Expo CLI** (`npm install -g expo-cli`)
- **EAS CLI** (`npm install -g eas-cli`)
- **Conta Expo** (para build)
- **Telemóvel** com Android 7+ ou iOS 14+

---

## Instalação

### 1. Navegar até à pasta
```bash
cd mobile/airmouse-mobile
```

### 2. Instalar dependências
```bash
npm install --legacy-peer-deps
```

### 3. Baixar modelo MediaPipe
```bash
# Criar pasta assets se não existir
mkdir -p assets

# Descarregar modelo
curl -o assets/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

### 4. Verificar instalação
```bash
npx tsc --noEmit
```

---

## Configuração

### Variáveis de Ambiente (app.json)

O app já vem configurado com:
- **Câmara frontal** para deteção de gestos
- **MediaPipe** com 2 mãos
- **Confiança** 0.5 para deteção/tracking

### Parâmetros Ajustáveis (src/store/index.ts)

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `moveGain` | 2.0 | Velocidade do cursor |
| `filterMinCutoff` | 1.4 | Filtro One Euro (suavidade) |
| `filterBeta` | 0.028 | Aceleração do filtro |
| `pinchOnRatio` | 0.38 | Sensibilidade pinça |
| `pinchOffRatio` | 0.55 | Histerese pinça |
| `hapticEnabled` | true | Feedback háptico |

---

## Executar

### Opção 1: Expo Go (mais rápido, sem nativos)
```bash
npx expo start
```
Escaneia o QR code com o Expo Go.

### Opção 2: Expo Dev Client (com nativos)
```bash
# Login
eas login

# Build para Android
eas build --profile development --platform android

# Build para iOS
eas build --profile development --platform ios
```

### Opção 3: Local (com Android Studio/Xcode)
```bash
# Prebuild
npx expo prebuild --clean

# Android
npx expo run:android

# iOS
npx expo run:ios
```

---

## Módulos Nativos

### Android (Java)

#### TouchControllerModule
```javascript
// Tap no ecrã
TouchController.tap(x, y);

// Long press
TouchController.longPress(x, y, duration);

// Swipe
TouchController.swipe(x1, y1, x2, y2, duration);

// Drag
TouchController.dragStart(x, y);
TouchController.dragMove(x, y);
TouchController.dragEnd();
```

#### KeyboardControllerModule
```javascript
// Digitar texto
KeyboardController.typeText("Hello");

// Pressionar tecla
KeyboardController.pressKey(66); // Enter

// Combinação de teclas
KeyboardController.pressCombo([113, 31]); // Ctrl+C

// Toggle teclado
KeyboardController.toggleKeyboard();
```

#### SystemControllerModule
```javascript
// Voltar
SystemController.goBack();

// Ecrã inicial
SystemController.goHome();

// Apps recentes
SystemController.openRecents();

// Notificações
SystemController.openNotifications();

// Volume
SystemController.adjustVolume(1); // +1 = subir
SystemController.adjustVolume(-1); // -1 = descer

// Brilho
SystemController.setBrightness(128); // 0-255

// Screenshot
SystemController.takeScreenshot();
```

### iOS (Swift)

#### TouchController
```swift
// Tap
TouchController.tap(x, y)

// Long press
TouchController.longPress(x, y, duration)

// Swipe
TouchController.swipe(x1, y1, x2, y2, duration)

// Drag
TouchController.dragStart(x, y)
TouchController.dragMove(x, y)
TouchController.dragEnd()
```

#### SystemController
```swift
// Voltar
SystemController.goBack()

// Ecrã inicial
SystemController.goHome()

// Apps recentes
SystemController.openRecents()

// Volume
SystemController.adjustVolume(1)

// Brilho
SystemController.setBrightness(128)
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Camera (Vision Camera)                │
│                         │                                │
│                         ▼                                │
│              ┌─────────────────────┐                    │
│              │   MediaPipe Hands   │                    │
│              │  (Kotlin/Swift nativo)│                    │
│              └──────────┬──────────┘                    │
│                         │ 21 landmarks                  │
│                         ▼                                │
│              ┌─────────────────────┐                    │
│              │   Gesture Engine    │                    │
│              │  (One Euro Filter)  │                    │
│              └──────────┬──────────┘                    │
│                         │ Gesture + Event               │
│                         ▼                                │
│              ┌─────────────────────┐                    │
│              │   Action Router     │                    │
│              └──────────┬──────────┘                    │
│                         │                                │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│   │  Touch   │   │ Keyboard │   │ System   │          │
│   │Controller│   │Controller│   │Controller│          │
│   └──────────┘   └──────────┘   └──────────┘          │
│         │               │               │               │
│         └───────────────┼───────────────┘               │
│                         ▼                                │
│              ┌─────────────────────┐                    │
│              │   Android / iOS     │                    │
│              │   (Ação no SO)      │                    │
│              └─────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

---

## Performance

| Métrica | Target |
|---------|--------|
| Latência gesto→ação | < 50ms |
| FPS deteção | 30+ fps |
| RAM usage | < 150MB |
| Battery drain | < 15%/hora |

---

## Troubleshooting

### Erro: "Cannot find module"
```bash
rm -rf node_modules
npm install --legacy-peer-deps
```

### Erro: "Camera permission denied"
Verificar `app.json` → `expo.plugins` → `expo-camera`

### Erro: "MediaPipe not found"
Verificar se `hand_landmarker.task` está em `assets/`

### Erro: "Native module not found"
```bash
npx expo prebuild --clean
```

### Build falha no EAS
```bash
# Limpar cache
eas build:configure
eas build --profile development --platform android --clear-cache
```

---

## Próximos Passos

- [ ] Testar em dispositivo real
- [ ] Otimizar performance em devices low-end
- [ ] Adicionar controlo de voz (Whisper/Vosk)
- [ ] Implementar calibração automática
- [ ] Adicionar modo desktop (remoto para PC)
- [ ] Publicar na Play Store / App Store

---

## Licença

MIT
