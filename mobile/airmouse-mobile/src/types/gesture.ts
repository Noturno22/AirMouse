export enum GestureType {
  NONE = 'NONE',
  OPEN = 'OPEN',
  ONE = 'ONE',
  PINCH = 'PINCH',
  PINCH_MID = 'PINCH_MID',
  FIST = 'FIST',
  PEACE = 'PEACE',
  THREE = 'THREE',
  FOUR = 'FOUR',
  THUMB_UP = 'THUMB_UP',
  PINKY = 'PINKY',
  SHAKA = 'SHAKA',
}

export interface HandLandmarks {
  points: [number, number, number][]; // 21 points x [x, y, z]
  palmCenter: [number, number];
  palmCenterPx: [number, number];
  indexTip: [number, number];
  thumbTip: [number, number];
  pinchRatio: number;
  pinchMidRatio: number;
  gesture: GestureType;
  handScalePx: number;
  aiConfidence: number;
}

export interface HandFrame {
  landmarks: HandLandmarks;
  side: 'Left' | 'Right';
  timestamp: number;
}

export type ActionType =
  | 'tap'
  | 'longPress'
  | 'swipe'
  | 'drag'
  | 'scroll'
  | 'goBack'
  | 'goHome'
  | 'openRecents'
  | 'openNotifications'
  | 'typeText'
  | 'pressKey'
  | 'none';

export interface Action {
  type: ActionType;
  x?: number;
  y?: number;
  endX?: number;
  endY?: number;
  duration?: number;
  text?: string;
  keyCode?: number;
  direction?: 'up' | 'down' | 'left' | 'right';
}

export interface CalibrationData {
  offsetX: number;
  offsetY: number;
  scaleX: number;
  scaleY: number;
  rotation: number;
}
