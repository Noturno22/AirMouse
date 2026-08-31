import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
import { Camera, useCameraDevice, useFrameProcessor, useCameraPermission, VisionCameraProxy } from 'react-native-vision-camera';
import { Worklets } from 'react-native-worklets-core';
import type { HandDetectionResult } from 'expo-vision-camera-v4-mediapipe';
import { useGestures } from './src/hooks/useGestures';
import { useSettingsStore, useGestureStore } from './src/store';
import { GESTURE_LABELS, GESTURE_COLORS, HAND_CONNECTIONS } from './src/constants';
import { GestureType, HandLandmarks } from './src/types/gesture';
import { GestureEngine, GestureResult } from './src/engine/gestures';
import { FilterPair2D, AccelCurve } from './src/engine/filters';

const { TouchController, KeyboardController, SystemController } = NativeModules;

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

export default function App() {
const [landmarks, setLandmarks] = useState<HandLandmarks | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [frameDims, setFrameDims] = useState<{ w: number; h: number } | null>(null);
  const [debugInfo, setDebugInfo] = useState<{
    plugin: boolean;
    hands: number;
    error?: string | null;
  } | null>(null);

  const device = useCameraDevice('front');
  const { hasPermission, requestPermission } = useCameraPermission();
  const [cameraError, setCameraError] = useState<string | null>(null);

  const detectHandLandmarks = useMemo(
    () => VisionCameraProxy.initFrameProcessorPlugin('handLandmarker', {}),
    []
  );
  const hasPlugin = detectHandLandmarks != null;

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
    (hands: any[], handedness: any[], imgW: number, imgH: number) => {
      if (!engineRef.current || !filtersRef.current || !curveRef.current) return;
      if (imgW <= 0 || imgH <= 0) return;

      try {
        const engine = engineRef.current;
        const filters = filtersRef.current;

        for (let i = 0; i < hands.length; i++) {
          const handLandmarks = hands[i];

          // Convert to our format
          const points: [number, number, number][] = handLandmarks.map(
            (point: any) => [point.x, point.y, point.z]
          );

          // Process with gesture engine in image pixels so scale thresholds apply
          const result = engine.update(points, imgW, imgH);

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
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setDebugInfo((prev) =>
          prev && prev.error === msg ? prev : { plugin: true, hands: 0, error: `JS: ${msg}` }
        );
        console.error('processHands error:', e);
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

  const emptyFrames = useRef(0);
  const clearAfterEmptyFrames = 6;

  const handleFramePayload = useCallback(
    (payload: {
      hands?: any[];
      handedness?: any[];
      imgW: number;
      imgH: number;
      handsCount: number;
    }) => {
      if (payload.handsCount > 0 && payload.hands && payload.hands.length > 0) {
        emptyFrames.current = 0;
        setFrameDims((prev) =>
          prev && prev.w === payload.imgW && prev.h === payload.imgH
            ? prev
            : { w: payload.imgW, h: payload.imgH }
        );
        processHands(payload.hands, payload.handedness || [], payload.imgW, payload.imgH);
      } else {
        emptyFrames.current += 1;
        if (emptyFrames.current >= clearAfterEmptyFrames) {
          setLandmarks(null);
        }
      }
    },
    [processHands]
  );

  const framePayloadRef = useRef(handleFramePayload);
  useEffect(() => {
    framePayloadRef.current = handleFramePayload;
  }, [handleFramePayload]);

  const bridgeFrame = useRef(
    Worklets.createRunOnJS(
      (payload: {
        hands?: any[];
        handedness?: any[];
        imgW: number;
        imgH: number;
        handsCount: number;
      }) => {
        framePayloadRef.current(payload);
      }
    )
  );

  const updateDebug = useRef(
    Worklets.createRunOnJS(
      (info: { plugin: boolean; hands: number; error?: string | null }) => {
        setDebugInfo((prev) => {
          if (
            prev &&
            prev.plugin === info.plugin &&
            prev.hands === info.hands &&
            prev.error === info.error
          ) {
            return prev;
          }
          return info;
        });
      }
    )
  );

  // Frame processor for real-time hand detection
  const frameProcessor = useFrameProcessor(
    (frame) => {
      'worklet';

      // Read frame dimensions BEFORE the slow MediaPipe call, while the frame is
      // guaranteed valid. Accessing frame props after heavy native work can throw
      // FrameInvalidError, and reading them first is the documented safe pattern.
      const imgW = frame.width;
      const imgH = frame.height;

      let hands: any[] | undefined;
      let handedness: any[] | undefined;
      let handsCount = 0;
      let errorMsg: string | null = null;

      try {
        const result = detectHandLandmarks?.call(frame) as HandDetectionResult | undefined;
        hands = result?.hands;
        handedness = result?.handedness;
        handsCount = result?.hands?.length ?? 0;
        errorMsg = result?.error ?? null;
      } catch (e: any) {
        errorMsg = e?.message ? String(e.message) : 'Frame processor error';
      }

      bridgeFrame.current({
        hands,
        handedness,
        imgW,
        imgH,
        handsCount,
      });

      updateDebug.current({ plugin: hasPlugin, hands: handsCount, error: errorMsg });

      // Update FPS on the JS thread
      updateFps.current();
    },
    [detectHandLandmarks, hasPlugin]
  );

  const viewMapping = useMemo(() => {
    if (!frameDims) return null;
    const scale = Math.max(SCREEN_WIDTH / frameDims.w, SCREEN_HEIGHT / frameDims.h);
    const dispW = frameDims.w * scale;
    const dispH = frameDims.h * scale;
    return {
      ox: (SCREEN_WIDTH - dispW) / 2,
      oy: (SCREEN_HEIGHT - dispH) / 2,
      dispW,
      dispH,
    };
  }, [frameDims]);

  // Render hand overlay
  const renderHandOverlay = () => {
    if (!landmarks) return null;

    const color = GESTURE_COLORS[landmarks.gesture] || '#969696';

    const mapX = (nx: number) =>
      viewMapping ? viewMapping.ox + (1 - nx) * viewMapping.dispW : nx * SCREEN_WIDTH;
    const mapY = (ny: number) =>
      viewMapping ? viewMapping.oy + ny * viewMapping.dispH : ny * SCREEN_HEIGHT;
    const toScreenX = (ix: number) =>
      viewMapping && frameDims
        ? viewMapping.ox + viewMapping.dispW - (viewMapping.dispW / frameDims.w) * ix
        : ix;
    const toScreenY = (iy: number) =>
      viewMapping && frameDims
        ? viewMapping.oy + (viewMapping.dispH / frameDims.h) * iy
        : iy;

    return (
      <View style={styles.overlay}>
        {/* Draw hand connections */}
        {HAND_CONNECTIONS.map(([a, b], index) => {
          const pa = landmarks.points[a];
          const pb = landmarks.points[b];
          if (!pa || !pb) return null;

          const x1 = mapX(pa[0]);
          const y1 = mapY(pa[1]);
          const x2 = mapX(pb[0]);
          const y2 = mapY(pb[1]);

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
              left: toScreenX(landmarks.palmCenterPx[0]) - 15,
              top: toScreenY(landmarks.palmCenterPx[1]) - 15,
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

  if (cameraError) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>Câmara indisponível</Text>
        <Text style={[styles.permissionText, { fontSize: 14 }]}>{cameraError}</Text>
        <Text style={[styles.permissionText, { fontSize: 14 }]}>
          A câmara está restrita pelo sistema (política de dispositivo ou
          restrição parental). Ative-a em Definições e reinicie a app.
        </Text>
      </View>
    );
  }

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
          isActive={!cameraError}
          frameProcessor={frameProcessor}
          onError={(error) => {
            console.error('Camera error:', error.message);
            setCameraError(error.message);
          }}
        />
      )}

      {renderHandOverlay()}

      {/* Debug overlay */}
      {debugInfo && (
        <View style={styles.debugOverlay}>
          <Text style={styles.debugText}>
            plugin:{debugInfo.plugin ? 'Y' : 'N'} hands:{debugInfo.hands}
            {debugInfo.error ? ` err:${debugInfo.error}` : ''}
          </Text>
        </View>
      )}

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
  debugOverlay: {
    position: 'absolute',
    bottom: 110,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  debugText: {
    color: '#FFE066',
    fontSize: 13,
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
