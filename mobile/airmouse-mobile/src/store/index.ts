import { create } from 'zustand';
import { GestureType } from '../types/gesture';

interface SettingsState {
  moveGain: number;
  filterMinCutoff: number;
  filterBeta: number;
  pinchOnRatio: number;
  pinchOffRatio: number;
  snapEnabled: boolean;
  voiceEnabled: boolean;
  hapticEnabled: boolean;
  darkMode: boolean;
  
  setMoveGain: (gain: number) => void;
  setFilterParams: (minCutoff: number, beta: number) => void;
  setPinchRatios: (on: number, off: number) => void;
  toggleSnap: () => void;
  toggleVoice: () => void;
  toggleHaptic: () => void;
  toggleDarkMode: () => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  moveGain: 2.0,
  filterMinCutoff: 1.4,
  filterBeta: 0.028,
  pinchOnRatio: 0.38,
  pinchOffRatio: 0.55,
  snapEnabled: true,
  voiceEnabled: false,
  hapticEnabled: true,
  darkMode: false,

  setMoveGain: (gain) => set({ moveGain: Math.max(0.6, gain) }),
  setFilterParams: (minCutoff, beta) =>
    set({ filterMinCutoff: minCutoff, filterBeta: beta }),
  setPinchRatios: (on, off) =>
    set({ pinchOnRatio: on, pinchOffRatio: off }),
  toggleSnap: () => set((s) => ({ snapEnabled: !s.snapEnabled })),
  toggleVoice: () => set((s) => ({ voiceEnabled: !s.voiceEnabled })),
  toggleHaptic: () => set((s) => ({ hapticEnabled: !s.hapticEnabled })),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
}));

interface GestureState {
  isTracking: boolean;
  currentGesture: GestureType;
  gestureCount: number;
  fps: number;
  handCount: number;
  isPaused: boolean;
  
  setTracking: (tracking: boolean) => void;
  setGesture: (gesture: GestureType) => void;
  incrementGestureCount: () => void;
  setFps: (fps: number) => void;
  setHandCount: (count: number) => void;
  togglePaused: () => void;
}

export const useGestureStore = create<GestureState>((set) => ({
  isTracking: false,
  currentGesture: GestureType.NONE,
  gestureCount: 0,
  fps: 0,
  handCount: 0,
  isPaused: false,

  setTracking: (tracking) => set({ isTracking: tracking }),
  setGesture: (gesture) => set({ currentGesture: gesture }),
  incrementGestureCount: () =>
    set((s) => ({ gestureCount: s.gestureCount + 1 })),
  setFps: (fps) => set({ fps }),
  setHandCount: (count) => set({ handCount: count }),
  togglePaused: () => set((s) => ({ isPaused: !s.isPaused })),
}));
