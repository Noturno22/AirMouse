import { useCallback, useRef, useState } from 'react';
import { GestureEngine, GestureResult } from '../engine/gestures';
import { FilterPair2D, AccelCurve } from '../engine/filters';
import { useSettingsStore, useGestureStore } from '../store';
import { GestureType } from '../types/gesture';

interface UseGesturesOptions {
  onGesture?: (result: GestureResult) => void;
  onAction?: (event: string, value: number | null) => void;
}

export function useGestures(options: UseGesturesOptions = {}) {
  const { onGesture, onAction } = options;
  
  const engineRef = useRef<GestureEngine | null>(null);
  const filtersRef = useRef<FilterPair2D | null>(null);
  const curveRef = useRef<AccelCurve | null>(null);
  
  const {
    moveGain,
    filterMinCutoff,
    filterBeta,
    pinchOnRatio,
    pinchOffRatio,
  } = useSettingsStore();

  const { setGesture, incrementGestureCount } = useGestureStore();

  const initEngine = useCallback(() => {
    engineRef.current = new GestureEngine({
      pinchOnRatio,
      pinchOffRatio,
    });
    filtersRef.current = new FilterPair2D(filterMinCutoff, filterBeta);
    curveRef.current = new AccelCurve(1.2, 3.0, 1400.0, 1.7);
  }, [pinchOnRatio, pinchOffRatio, filterMinCutoff, filterBeta]);

  const processFrame = useCallback(
    (
      landmarks: [number, number, number][],
      width: number,
      height: number
    ): GestureResult | null => {
      if (!engineRef.current || !filtersRef.current || !curveRef.current) {
        initEngine();
      }

      const engine = engineRef.current!;
      const filters = filtersRef.current!;
      const curve = curveRef.current!;

      const result = engine.update(landmarks, width, height);

      // Apply filters for smooth cursor movement
      const [fx, fy] = filters.filter(
        result.landmarks.palmCenter[0],
        result.landmarks.palmCenter[1]
      );

      // Update gesture state
      setGesture(result.landmarks.gesture);
      incrementGestureCount();

      // Call callbacks
      if (onGesture) {
        onGesture(result);
      }

      if (result.event && onAction) {
        onAction(result.event, result.value);
      }

      return result;
    },
    [initEngine, setGesture, incrementGestureCount, onGesture, onAction]
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
    processFrame,
    reset,
    initEngine,
  };
}
