import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  Dimensions,
  Platform,
  StatusBar,
  NativeModules,
} from 'react-native';
import { Camera, useCameraDevice, useFrameProcessor, useCameraPermission } from 'react-native-vision-camera';
import { Worklets } from 'react-native-worklets-core';
import { useGestures } from './src/hooks/useGestures';
import { useSettingsStore, useGestureStore } from './src/store';
import { GESTURE_LABELS, GESTURE_COLORS, HAND_CONNECTIONS } from './src/constants';
import { GestureType, HandLandmarks } from './src/types/gesture';
import { GestureEngine, GestureResult } from './src/engine/gestures';
import { FilterPair2D, AccelCurve } from './src/engine/filters';

const { TouchController, KeyboardController, SystemController } = NativeModules;

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Hand detection via MediaPipe (will be replaced with real implementation)
let detectHandLandmarks: any = null;
try {
  detectHandLandmarks = require('expo-vision-camera-v4-mediapipe').detectHandLandmarks;
} catch (e) {
  console.log('MediaPipe not available, using simulated detection');
}

export default function App() {
  const [landmarks, setLandmarks] = useState<HandLandmarks | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  
  const device = useCameraDevice('front');
  const { hasPermission, requestPermission } = useCameraPermission();

  const {
    currentGesture,
    fps,
    isPaused,
    togglePaused,
    setGesture,
    incrementGestureCount,
    setFps,
  } = useGestureStore();

  const { moveGain, filterMinCutoff, filterBeta } = useSettingsStore();

  const engineRef = useRef<GestureEngine | null>(null);
  const filtersRef = useRef<FilterPair2D | null>(null);
  const curveRef = useRef<AccelCurve | null>(null);
  const lastFrameTime = useRef(performance.now());
  const frameCount = useRef(0);

  // Initialize gesture engine
  useEffect(() => {
    engineRef.current = new GestureEngine();
    filtersRef.current = new FilterPair2D(filterMinCutoff, filterBeta);
    curveRef.current = new AccelCurve(1.2, 3.0, 1400.0, 1.7);
  }, [filterMinCutoff, filterBeta]);

  // Process hand detection result
  const processHands = useCallback(
    (hands: any[], handedness: any[]) => {
      if (!engineRef.current || !filtersRef.current || !curveRef.current) return;

      const engine = engineRef.current;
      const filters = filtersRef.current;

      for (let i = 0; i < hands.length; i++) {
        const handLandmarks = hands[i];
        
        // Convert to our format
        const points: [number, number, number][] = handLandmarks.map(
          (point: any) => [point.x, point.y, point.z]
        );

        // Process with gesture engine (normalized coordinates)
        const result = engine.update(points, 1.0, 1.0);

        // Apply filters
        const [fx, fy] = filters.filter(
          result.landmarks.palmCenter[0],
          result.landmarks.palmCenter[1]
        );

        // Update state
        setGesture(result.landmarks.gesture);
        incrementGestureCount();
        setLandmarks(result.landmarks);

        // Handle actions via native modules
        if (result.event && TouchController && SystemController) {
          handleAction(result.event, result.value);
        }
      }
    },
    [setGesture, incrementGestureCount]
  );

  // Handle gesture actions
  const handleAction = useCallback(
    async (event: string, value: number | null) => {
      try {
        switch (event) {
          case 'tap':
            // Get palm position and tap there
            if (landmarks) {
              const x = landmarks.palmCenterPx[0];
              const y = landmarks.palmCenterPx[1];
              await TouchController?.tap(x, y);
            }
            break;
          case 'right_click':
            // Long press for right click
            if (landmarks) {
              const x = landmarks.palmCenterPx[0];
              const y = landmarks.palmCenterPx[1];
              await TouchController?.longPress(x, y, 0.5);
            }
            break;
          case 'drag':
            // Start drag
            if (landmarks) {
              const x = landmarks.palmCenterPx[0];
              const y = landmarks.palmCenterPx[1];
              await TouchController?.dragStart(x, y);
            }
            break;
          case 'scroll':
            // Handle scroll
            if (value !== null && TouchController) {
              await TouchController?.swipe(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2 - value * 10,
                0.1
              );
            }
            break;
          case 'goBack':
            await SystemController?.goBack();
            break;
          case 'goHome':
            await SystemController?.goHome();
            break;
          case 'openRecents':
            await SystemController?.openRecents();
            break;
          case 'openNotifications':
            await SystemController?.openNotifications();
            break;
          case 'minimize':
            await KeyboardController?.pressCombo([113, 40]); // Ctrl+D
            break;
          case 'copy':
            await KeyboardController?.pressCombo([113, 31]); // Ctrl+C
            break;
          case 'paste':
            await KeyboardController?.pressCombo([113, 50]); // Ctrl+V
            break;
          default:
            break;
        }
      } catch (error) {
        console.error('Action error:', error);
      }
    },
    [landmarks]
  );

  // Update FPS from the worklet via runOnJS (no React functions/refs are shared into the worklet)
  const updateFps = useRef(
    Worklets.createRunOnJS(() => {
      frameCount.current++;
      const now = Date.now();
      if (now - lastFrameTime.current >= 1000) {
        const fps = (frameCount.current * 1000) / (now - lastFrameTime.current);
        setFps(fps);
        frameCount.current = 0;
        lastFrameTime.current = now;
      }
    })
  );

  // Frame processor for real-time hand detection
  const frameProcessor = useFrameProcessor(
    (frame) => {
      'worklet';

      if (detectHandLandmarks) {
        const result = detectHandLandmarks(frame);
        if (result?.hands && result.hands.length > 0) {
          // Bridge to JS thread
          const onResult = Worklets.createRunOnJS(
            (hands: any[], handedness: any[]) => {
              processHands(hands, handedness);
            }
          );
          onResult(result.hands, result.handedness || []);
        }
      }

      // Update FPS on the JS thread
      updateFps.current();
    },
    [processHands]
  );

  // Render hand overlay
  const renderHandOverlay = () => {
    if (!landmarks) return null;

    const color = GESTURE_COLORS[landmarks.gesture] || '#969696';

    return (
      <View style={styles.overlay}>
        {/* Draw hand connections */}
        {HAND_CONNECTIONS.map(([a, b], index) => {
          const pa = landmarks.points[a];
          const pb = landmarks.points[b];
          if (!pa || !pb) return null;

          const x1 = pa[0] * SCREEN_WIDTH;
          const y1 = pa[1] * SCREEN_HEIGHT;
          const x2 = pb[0] * SCREEN_WIDTH;
          const y2 = pb[1] * SCREEN_HEIGHT;

          return (
            <View
              key={index}
              style={[
                styles.connectionLine,
                {
                  left: x1,
                  top: y1,
                  width: Math.hypot(x2 - x1, y2 - y1),
                  transform: [
                    {
                      rotate: `${Math.atan2(y2 - y1, x2 - x1)}rad`,
                    },
                  ],
                  backgroundColor: color,
                },
              ]}
            />
          );
        })}

        {/* Draw palm center */}
        <View
          style={[
            styles.palmCenter,
            {
              left: landmarks.palmCenterPx[0] - 15,
              top: landmarks.palmCenterPx[1] - 15,
              borderColor: color,
            },
          ]}
        />

        {/* Gesture badge */}
        <View style={[styles.gestureBadge, { backgroundColor: color + '80' }]}>
          <Text style={styles.gestureText}>
            {GESTURE_LABELS[landmarks.gesture]}
          </Text>
        </View>
      </View>
    );
  };

  if (!hasPermission) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          AirMouse precisa de acesso à câmara para detetar gestos de mão
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Permitir Câmara</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      {device && (
        <Camera
          style={StyleSheet.absoluteFill}
          device={device}
          isActive={true}
          frameProcessor={frameProcessor}
          pixelFormat="rgb"
        />
      )}

      {renderHandOverlay()}

      {/* Top bar */}
      <View style={styles.topBar}>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>
            {isPaused ? 'PAUSA' : GESTURE_LABELS[currentGesture]}
          </Text>
        </View>

        <View style={styles.statsContainer}>
          <Text style={styles.statsText}>{fps.toFixed(0)} fps</Text>
          <Text style={styles.statsText}>G: {moveGain.toFixed(1)}</Text>
        </View>
      </View>

      {/* Bottom controls */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={togglePaused}
        >
          <Text style={styles.controlButtonText}>
            {isPaused ? '▶' : '⏸'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setShowHelp(!showHelp)}
        >
          <Text style={styles.controlButtonText}>?</Text>
        </TouchableOpacity>
      </View>

      {/* Help overlay */}
      {showHelp && (
        <View style={styles.helpOverlay}>
          <View style={styles.helpContent}>
            <Text style={styles.helpTitle}>Gestos</Text>
            <Text style={styles.helpItem}>✋ Mão aberta = Mover cursor</Text>
            <Text style={styles.helpItem}>🤏 Pinça = Clique esquerdo</Text>
            <Text style={styles.helpItem}>🤏🤞 Pinça+médio = Clique direito</Text>
            <Text style={styles.helpItem}>✊ Punho = Arrastar</Text>
            <Text style={styles.helpItem}>✌️ Dois dedos = Scroll</Text>
            <Text style={styles.helpItem}>☝️ Um dedo = Mover (1D)</Text>
            <Text style={styles.helpItem}>👍 Polegar = Play/Pausa</Text>
            <Text style={styles.helpItem}>🤙 Shaka = Colar</Text>
            <TouchableOpacity
              style={styles.helpCloseButton}
              onPress={() => setShowHelp(false)}
            >
              <Text style={styles.helpCloseText}>Fechar</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  overlay: {
    ...StyleSheet.absoluteFill,
  },
  connectionLine: {
    position: 'absolute',
    height: 2,
    transformOrigin: 'left',
  },
  palmCenter: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 2,
  },
  gestureBadge: {
    position: 'absolute',
    top: 50,
    left: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  gestureText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  topBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 50,
  },
  statusBadge: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  statusText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  statsContainer: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  statsText: {
    color: '#FFF',
    fontSize: 14,
    marginLeft: 8,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButtonText: {
    color: '#FFF',
    fontSize: 24,
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 40,
  },
  permissionText: {
    color: '#FFF',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
  },
  permissionButton: {
    backgroundColor: '#50C8FF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  helpOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  helpContent: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 24,
    maxWidth: SCREEN_WIDTH * 0.9,
  },
  helpTitle: {
    color: '#FFF',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  helpItem: {
    color: '#DDD',
    fontSize: 16,
    marginBottom: 8,
  },
  helpCloseButton: {
    marginTop: 20,
    backgroundColor: '#50C8FF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  helpCloseText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
