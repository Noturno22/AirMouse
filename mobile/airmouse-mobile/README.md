# AirMouse Mobile

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
├── App.tsx                    # Componente principal
├── src/
│   ├── engine/
│   │   ├── filters.ts         # One Euro Filter + AccelCurve
│   │   └── gestures.ts        # Deteção de gestos
│   ├── hooks/
│   │   └── useGestures.ts     # Hook de processamento
│   ├── store/
│   │   └── index.ts           # Zustand store
│   ├── types/
│   │   └── gesture.ts         # Tipos TypeScript
│   └── constants/
│       └── index.ts           # Constantes
└── app.json                   # Configuração Expo
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

## Licença

MIT
