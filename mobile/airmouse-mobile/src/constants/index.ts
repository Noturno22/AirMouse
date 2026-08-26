import { GestureType } from '../types/gesture';

export const GESTURE_LABELS: Record<GestureType, string> = {
  [GestureType.NONE]: 'SEM MÃO',
  [GestureType.OPEN]: 'MOVER',
  [GestureType.ONE]: 'MOVER 1D',
  [GestureType.PINCH]: 'CLIQUE ESQ',
  [GestureType.PINCH_MID]: 'CLIQUE DIR',
  [GestureType.FIST]: 'ARRASTAR',
  [GestureType.PEACE]: 'SCROLL',
  [GestureType.THREE]: 'VOLUME',
  [GestureType.THUMB_UP]: 'PLAY/PAUSA',
  [GestureType.FOUR]: 'MINIMIZAR',
  [GestureType.PINKY]: 'COPIAR',
  [GestureType.SHAKA]: 'COLAR',
};

export const GESTURE_COLORS: Record<GestureType, string> = {
  [GestureType.NONE]: '#969696',
  [GestureType.OPEN]: '#50C8FF',
  [GestureType.ONE]: '#50C8FF',
  [GestureType.PINCH]: '#5ADC5A',
  [GestureType.PINCH_MID]: '#3C3CEB',
  [GestureType.FIST]: '#4682FF',
  [GestureType.PEACE]: '#FF50C8',
  [GestureType.THREE]: '#FFAA3C',
  [GestureType.THUMB_UP]: '#8CE1E1',
  [GestureType.FOUR]: '#FFC832',
  [GestureType.PINKY]: '#B478FF',
  [GestureType.SHAKA]: '#78C8B4',
};

export const SMOOTH_PRESETS = [
  { name: 'SUAVE', minCutoff: 0.9, beta: 0.02 },
  { name: 'NORMAL', minCutoff: 1.4, beta: 0.028 },
  { name: 'REACTIVO', minCutoff: 2.2, beta: 0.05 },
] as const;

export const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];
