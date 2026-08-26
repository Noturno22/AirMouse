import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import {
  Camera,
  useCameraDevice,
  useFrameProcessor,
  useCameraPermission,
} from 'react-native-vision-camera';
import { Worklets } from 'react-native-worklets-core';
import { detectHandLandmarks } from 'expo-vision-camera-v4-mediapipe';
import { GestureEngine, GestureResult } from '../engine/gestures';
import { FilterPair2D, AccelCurve } from '../engine/filters';
import { useSettingsStore, useGestureStore } from '../store';
import { GestureType, HandLandmarks } from '../types/gesture';

interface UseHandDetectionOptions {
  onGesture?: (result: GestureResult) => void;
  onAction?: (event: string, value: number | null) => void;
  onFpsUpdate?: (fps: number) => void;
}

export function useHandDetection(options: UseHandDetectionOptions = {}) {
  const { onGesture, onAction, onFpsUpdate } = options;

  const device = useCameraDevice('front');
  const { hasPermission, requestPermission } = useCameraPermission();

  const engineRef = useRef<GestureEngine | null>(null);
  const filtersRef = useRef<FilterPair2D | null>(null);
  const curveRef = useRef<AccelCurve | null>(null);

  const lastFrameTime = useRef(performance.now());
  const frameCount = useRef(0);
  const prevPosRef = useRef<{ x: number; y: number } | null>(null);

  const {
    moveGain,
    filterMinCutoff,
    filterBeta,
    pinchOnRatio,
    pinchOffRatio,
  } = useSettingsStore();

  const { setGesture, incrementGestureCount, setFps, setHandCount } =
    useGestureStore();

  // Initialize engine
  useEffect(() => {
    engineRef.current = new GestureEngine({
      pinchOnRatio,
      pinchOffRatio,
    });
    filtersRef.current = new FilterPair2D(filterMinCutoff, filterBeta);
    curveRef.current = new AccelCurve(1.2, 3.0, 1400.0, 1.7);
  }, [pinchOnRatio, pinchOffRatio, filterMinCutoff, filterBeta]);

  // Process hand landmarks
  const processFrame = useCallback(
    (hands: any[], handedness: any[]) => {
      if (!engineRef.current || !filtersRef.current || !curveRef.current) {
        return;
      }

      const engine = engineRef.current;
      const filters = filtersRef.current;

      // Process each hand
      for (let i = 0; i < hands.length; i++) {
        const handLandmarks = hands[i];
        const side = handedness[i]?.[0]?.categoryName || 'Right';

        // Convert to our format
        const landmarks: [number, number, number][] = handLandmarks.map(
          (point: any) => [point.x, point.y, point.z]
        );

        // Get frame dimensions (normalized coordinates)
        const width = 1.0;
        const height = 1.0;

        // Process with gesture engine
        const result = engine.update(landmarks, width, height);

        // Apply filters for smooth movement
        const [fx, fy] = filters.filter(
          result.landmarks.palmCenter[0],
          result.landmarks.palmCenter[1]
        );

        // Update state
        setGesture(result.landmarks.gesture);
        incrementGestureCount();

        // Calculate delta movement
        const prev = prevPosRef.current;
        const dx = fx - (prev?.x ?? fx);
        const dy = fy - (prev?.y ?? fy);
        prevPosRef.current = { x: fx, y: fy };

        // Apply gain and acceleration
        const gain =
          moveGain * curveRef.current.apply(filters.vx, filters.vy);

        // Callbacks
        if (onGesture) {
          onGesture(result);
        }

        if (result.event && onAction) {
          onAction(result.event, result.value);
        }
      }

      setHandCount(hands.length);
    },
    [
      moveGain,
      setGesture,
      incrementGestureCount,
      setHandCount,
      onGesture,
      onAction,
    ]
  );

  // Frame processor for Vision Camera
  const frameProcessor = useFrameProcessor(
    (frame) => {
      'worklet';

      const result = detectHandLandmarks(frame);
      if (result?.hands && result.hands.length > 0) {
        // Bridge to JS thread
        const onResult = Worklets.createRunOnJS(
          (hands: any[], handedness: any[]) => {
            processFrame(hands, handedness);
          }
        );
        onResult(result.hands, result.handedness || []);
      }

      // Calculate FPS
      frameCount.current++;
      const now = performance.now();
      if (now - lastFrameTime.current >= 1000) {
        const fps = (frameCount.current * 1000) / (now - lastFrameTime.current);
        setFps(fps);
        if (onFpsUpdate) onFpsUpdate(fps);
        frameCount.current = 0;
        lastFrameTime.current = now;
      }
    },
    [processFrame, onFpsUpdate]
  );

  const reset = useCallback(() => {
    if (engineRef.current) {
      engineRef.current.reset();
    }
    if (filtersRef.current) {
      filtersRef.current.reset();
    }
  }, []);

  return {
    device,
    hasPermission,
    requestPermission,
    frameProcessor,
    reset,
  };
}
