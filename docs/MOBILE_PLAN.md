# AirMouse Mobile - Plano Completo

## Visão Geral

**AirMouse Mobile** é um aplicativo React Native/Expo que permite controlar total do telemóvel usando gestos de mão detetados pela câmara frontal do dispositivo. Funcionalidades incluem: navegação, digitação, atalhos, controlo de voz, e muito mais - tudo hands-free.

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    AirMouse Mobile                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Camera    │  │  MediaPipe   │  │  Gesture Engine  │  │
│  │   Module    │──│  Hand        │──│  (One Euro +     │  │
│  │  (Front)    │  │  Landmarker  │  │   AccelCurve)    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Action Router                           │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │   │
│  │  │ Touch   │ │ Keyboard │ │ System   │ │ Voice  │  │   │
│  │  │ Control │ │ Control  │ │ Control  │ │ Engine │  │   │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Native Bridge                           │   │
│  │  • Android: AccessibilityService + MediaProjection   │   │
│  │  • iOS: Accessibility + AssistiveTouch               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Funcionalidades Planeadas

### 1. Controlo de Cursor (Touch Virtual)
| Gesto | Ação |
|-------|------|
| ✋ Mão aberta | Mover cursor (touchpad relativo) |
| 🤏 Pinça | Toque / Selecionar |
| 🤏🤞 Pinça+médio | Toque longo (long press) |
| ✊ Punho | Arrastar |
| 👆 Index | Swipe para navegar |

### 2. Digitação Virtual
| Gesto | Ação |
|-------|------|
| ☝️ Dedo indicador (curto) | Mover para tecla e digitar |
| 🤏 Pinça perto do teclado | Selecionar letra |
| ✌️ Dois dedos | Espaço / Enter |
| 👍 Polegar cima | Shift |

### 3. Atalhos de Sistema
| Gesto | Ação |
|-------|------|
| 🖐️ Mão aberta + deslizar cima | Notificações |
| ✊ Punho duplo | Volta / Início |
| 👋 Palma | Captura de ecrã |
| ☝️ + 👆 Dois dedos | Multitarefa |
| 🤙 Shaka | Controlos rápidos |

### 4. Controlo de Voz
| Comando | Ação |
|---------|------|
| "Hey AirMouse" | Wake word |
| "Clica" | Toque no cursor |
| "Sobe/Desce" | Scroll |
| "Volta" | Botão voltar |
| "Inicio" | Ecrã inicial |
| "Multitarefa" | Apps recentes |

### 5. Acessibilidade
| Gesto | Ação |
|-------|------|
| ✋ Mão aberta (sustido) | Modo acessibilidade |
| 👆 Index (sustido) | Selecionar elemento |
| 🤏 Pinça dupla | Duplo toque |
| 👋 Mão + deslizar | Navegar entre elementos |

---

## Estrutura do Projeto

```
airmouse-mobile/
├── app/                          # Expo Router
│   ├── _layout.tsx              # Root layout
│   ├── (tabs)/
│   │   ├── _layout.tsx          # Tab layout
│   │   ├── index.tsx            # Ecrã principal (controle)
│   │   ├── settings.tsx         # Configurações
│   │   ├── gestures.tsx         # Gestos disponíveis
│   │   └── about.tsx            # Sobre
│   ├── camera.tsx               # Ecrã da câmara
│   └── calibration.tsx          # Calibração
├── src/
│   ├── components/
│   │   ├── ui/                  # Componentes genéricos
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Slider.tsx
│   │   └── feature/
│   │       ├── CameraPreview.tsx    # Preview da câmara
│   │       ├── GestureOverlay.tsx   # Overlay de gestos
│   │       ├── CursorController.tsx # Controlador do cursor
│   │       └── VoiceControl.tsx     # Controlo de voz
│   ├── engine/
│   │   ├── camera.ts             # Gestão da câmara
│   │   ├── tracker.ts            # MediaPipe Hand Landmarker
│   │   ├── filters.ts            # One Euro Filter + AccelCurve
│   │   ├── gestures.ts           # Detetor de gestos
│   │   ├── motion.ts             # Suavização + predição
│   │   └── calibration.ts        # Calibração automática
│   ├── actions/
│   │   ├── touch.ts              # Controlo touch virtual
│   │   ├── keyboard.ts           # Controlo de teclado
│   │   ├── system.ts             # Ações de sistema
│   │   ├── accessibility.ts      # Acessibilidade
│   │   └── voice.ts              # Controlo de voz
│   ├── bridge/
│   │   ├── android.ts            # Native modules Android
│   │   ├── ios.ts                # Native modules iOS
│   │   └── types.ts              # Tipos partilhados
│   ├── store/
│   │   ├── settings.ts           # Zustand store
│   │   └── gestures.ts           # Estado dos gestos
│   ├── hooks/
│   │   ├── useCamera.ts          # Hook da câmara
│   │   ├── useGestures.ts        # Hook de gestos
│   │   ├── useAction.ts          # Hook de ações
│   │   └── useCalibration.ts     # Hook de calibração
│   ├── utils/
│   │   ├── math.ts               # Utilidades matemáticas
│   │   └── platform.ts           # Deteção de plataforma
│   ├── constants/
│   │   ├── colors.ts             # Cores
│   │   ├── gestures.ts           # Constantes de gestos
│   │   └── actions.ts            # Constantes de ações
│   └── types/
│       ├── gesture.ts            # Tipos de gestos
│       ├── camera.ts             # Tipos de câmara
│       └── actions.ts            # Tipos de ações
├── android/
│   └── app/
│       └── src/main/
│           └── java/.../
│               ├── AirMouseAccessibilityService.java
│               ├── TouchControllerModule.java
│               ├── KeyboardControllerModule.java
│               └── SystemControllerModule.java
├── ios/
│   └── AirMouse/
│       ├── TouchController.m
│       ├── KeyboardController.m
│       └── AccessibilityService.swift
├── assets/
│   ├── icons/
│   └── models/
│       └── hand_landmarker.task
├── app.json
├── package.json
├── tsconfig.json
└── README.md
```

---

## Stack Tecnológico

### Core
- **React Native** 0.74+ com **Expo** 51+
- **TypeScript** 5.4+
- **Expo Router** para navegação
- **Zustand** para state management

### ML/Computer Vision
- **@mediapipe/hands** (via expo ou bundled)
- **expo-camera** para acesso à câmara
- **react-native-fast-tflite** (opcional, para modelos custom)

### Native Bridge
- **expo-modules-api** para módulos nativos
- **react-native-accessibility-engine** (referência)

### UI/UX
- **Moti** + **Reanimated 3** para animações
- **expo-haptics** para feedback háptico
- **expo-blur** para efeitos visuais

### Voz
- **expo-speech** para TTS
- **@react-native-voice/voice** para STT

---

## Módulos Nativos (Android)

### 1. TouchControllerModule
```java
// Permite simular touch no ecrã
@ReactModule(name = "TouchController")
public class TouchControllerModule extends ReactContextBaseJavaModule {
    // Methods:
    // - tap(x: number, y: number)
    // - longPress(x: number, y: number, duration: number)
    // - swipe(x1: number, y1: number, x2: number, y2: number, duration: number)
    // - drag(x: number, y: number) - inicia arrasto
    // - moveTo(x: number, y: number) - move durante arrasto
    // - release() - solta arrasto
}
```

### 2. KeyboardControllerModule
```java
// Permite enviar input de teclado
@ReactModule(name = "KeyboardController")
public class KeyboardControllerModule extends ReactContextBaseJavaModule {
    // Methods:
    // - typeText(text: String)
    // - pressKey(keyCode: int)
    // - pressCombo(keys: int[]) // ex: Ctrl+C
    // - toggleKeyboard()
}
```

### 3. SystemControllerModule
```java
// Controlo de sistema
@ReactModule(name = "SystemController")
public class SystemControllerModule extends ReactContextBaseJavaModule {
    // Methods:
    // - goBack()
    // - goHome()
    // - openRecents()
    // - openNotifications()
    // - toggleQuickSettings()
    // - takeScreenshot()
    // - adjustVolume(direction: int)
    // - setBrightness(level: number)
}
```

### 4. AirMouseAccessibilityService
```java
// Serviço de acessibilidade para navegação
public class AirMouseAccessibilityService extends AccessibilityService {
    // Permite:
    // - Obter lista de elementos visíveis
    // - Clicar em elementos específicos
    // - Navegar por foco
    // - Ler conteúdo do ecrã
}
```

---

## Módulos Nativos (iOS)

### 1. TouchController
```swift
// Usa AssistiveTouch API
@objc(TouchController)
class TouchController: NSObject {
    // Simula touch via accessibility
    @objc func tap(_ x: Double, y: Double) { }
    @objc func longPress(_ x: Double, y: Double, duration: Double) { }
    @objc func swipe(_ x1: Double, y1: Double, x2: Double, y2: Double) { }
}
```

### 2. SystemController
```swift
// Controlo de sistema via URL schemes
@objc(SystemController)
class SystemController: NSObject {
    @objc func goBack() { /* UIApplication.shared.sendAction */ }
    @objc func goHome() { /* UIApplication.shared.sendAction */ }
    @objc func openRecents() { /* UIApplication.shared.sendAction */ }
}
```

---

## Fluxo de Dados

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Camera  │────▶│ MediaPipe │────▶│ Gesture  │────▶│  Action  │
│  Frame   │     │  Hands   │     │  Engine  │     │  Router  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                │                  │
                      ▼                ▼                  ▼
                 ┌──────────┐    ┌──────────┐      ┌──────────┐
                 │Landmarks │    │ Filtrado │      │ Native   │
                 │  (21pts) │    │ + Suave  │      │ Bridge   │
                 └──────────┘    └──────────┘      └──────────┘
                                       │                  │
                                       ▼                  ▼
                                  ┌──────────┐      ┌──────────┐
                                  │  Curva   │      │ Touch /  │
                                  │ Accel    │      │ Keyboard │
                                  └──────────┘      └──────────┘
```

---

## Fases de Desenvolvimento

### Fase 1: MVP (4-6 semanas)
- [ ] Setup do projeto Expo
- [ ] Acesso à câmara frontal
- [ ] MediaPipe Hand Landmarker funcional
- [ ] Filtros One Euro (port do Python)
- [ ] Mover cursor com mão aberta
- [ ] Tap com pinça
- [ ] UI básica (overlay + controlos)

### Fase 2: Core Features (4-6 semanas)
- [ ] Swipe gestures
- [ ] Long press
- [ ] Drag and drop
- [ ] Scroll gestures
- [ ] Módulos nativos Android (Touch, Keyboard, System)
- [ ] Controlo de voz básico

### Fase 3: Advanced (4-6 semanas)
- [ ] Acessibilidade (AccessibilityService)
- [ ] Digitação por gestos
- [ ] Calibração automática
- [ ] Atalhos de sistema
- [ ] Modo desktop (remoto para PC)
- [ ] iOS nativo modules

### Fase 4: Polish (2-4 semanas)
- [ ] Animações e transições
- [ ] Feedback háptico
- [ ] Modo escuro/claro
- [ ] Tutorial interativo
- [ ] Performance optimization
- [ ] App Store / Play Store

---

## Calibração

O app inclui calibração automática que:
1. Mapeia a área visível da câmara para o ecrã
2. Ajusta sensibilidade ao tamanho da mão do utilizador
3. Adapta-se à iluminação ambiente
4. Aprende os limites de movimento do utilizador

---

## Performance Target

| Métrica | Target |
|---------|--------|
| Latência gesto→ação | < 50ms |
| FPS deteção | 30+ fps |
| RAM usage | < 150MB |
| Battery drain | < 15%/hora |
| Tamanho app | < 50MB |

---

## Segurança e Privacidade

- **Processamento 100% local** - nenhum dado sai do dispositivo
- **Câmara apenas quando ativo** - indicador visual sempre visível
- **Sem permissões desnecessárias** - apenas câmara + acessibilidade
- **Dados de calibração locais** - nunca enviados

---

## Comparação com AirMouse Desktop

| Feature | Desktop (Python) | Mobile (React Native) |
|---------|------------------|----------------------|
| Câmara | USB Webcam | Front Camera |
| Output | Mouse do PC | Touch nativo |
| Latência | ~30ms | ~50ms (target) |
| Gestos | 12+ | 15+ (mais acessibilidade) |
| Voz | Vosk + Whisper | nativo STT/TTS |
| Acessibilidade | Limitado | Completo |
| Distribuição | .exe manual | App Store |
| Multi-dispositivo | Não | Sim (pairing) |

---

## Conclusão

O AirMouse Mobile será significativamente mais poderoso que a versão desktop porque:
1. **Acessibilidade nativa** - controlo total do SO
2. **Portátil** - funciona em qualquer lugar
3. **Feedback háptico** - confirmação tátil das ações
4. **Distribuição fácil** - App Store / Play Store
5. **Calibração automática** - adapta-se ao utilizador
6. **Modo remoto** - pode controlar PC via WiFi

---

*Última atualização: 25/08/2026*
