import { GestureType, HandLandmarks } from '../types/gesture';

const FINGER_TIPS_PIPS: [number, number][] = [
  [8, 6],   // INDEX
  [12, 10], // MIDDLE
  [16, 14], // RING
  [20, 18], // PINKY
];

const PALM_IDS = [0, 5, 9, 13, 17];
const THUMB_TIP = 4;
const INDEX_TIP = 8;
const MIDDLE_TIP = 12;
const INDEX = 0;
const MIDDLE = 1;
const RING = 2;
const PINKY = 3;

interface GestureConfig {
  pinchOnRatio: number;
  pinchOffRatio: number;
  minHandScalePx: number;
  gestureStableFrames: number;
  scrollDeadzonePx: number;
  volumeDeadzonePx: number;
  aiConfidenceMin: number;
}

const DEFAULT_CONFIG: GestureConfig = {
  pinchOnRatio: 0.38,
  pinchOffRatio: 0.55,
  minHandScalePx: 30.0,
  gestureStableFrames: 2,
  scrollDeadzonePx: 3.0,
  volumeDeadzonePx: 3.0,
  aiConfidenceMin: 0.6,
};

function dist(a: [number, number], b: [number, number]): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

export interface GestureResult {
  landmarks: HandLandmarks;
  event: string | null;
  value: number | null;
}

export class GestureEngine {
  private config: GestureConfig;
  private pinchIndexOn = false;
  private pinchMidOn = false;
  private candidate: GestureType = GestureType.NONE;
  private candidateCount = 0;
  private committed: GestureType = GestureType.NONE;
  private scrollPrevY: number | null = null;
  private scrollAccY = 0.0;
  private volPrevY: number | null = null;
  private volAccY = 0.0;

  constructor(config: Partial<GestureConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  reset(): void {
    this.pinchIndexOn = false;
    this.pinchMidOn = false;
    this.candidate = GestureType.NONE;
    this.candidateCount = 0;
    this.committed = GestureType.NONE;
    this.scrollPrevY = null;
    this.scrollAccY = 0.0;
    this.volPrevY = null;
    this.volAccY = 0.0;
  }

  update(
    rawLandmarks: [number, number, number][],
    width: number,
    height: number
  ): GestureResult {
    const cfg = this.config;

    // Convert normalized landmarks to pixels
    const pts: [number, number][] = rawLandmarks.map((lm) => [
      lm[0] * width,
      lm[1] * height,
    ]);

    const wrist = pts[0];
    const scale = Math.max(dist(wrist, pts[9]), 1e-6);

    // 3D ratios (immune to hand tilt/foreshortening)
    const ky = height / width;
    const p3: [number, number, number][] = rawLandmarks.map((lm) => [
      lm[0],
      lm[1] * ky,
      lm[2],
    ]);

    const d3 = (a: [number, number, number], b: [number, number, number]): number => {
      return Math.sqrt(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
      );
    };

    const scale3 = Math.max(d3(p3[0], p3[9]), 1e-6);
    const pinchRatio = d3(p3[THUMB_TIP], p3[INDEX_TIP]) / scale3;
    const pinchMidRatio = d3(p3[THUMB_TIP], p3[MIDDLE_TIP]) / scale3;

    // Check if fingers are curled
    const curled = FINGER_TIPS_PIPS.map(([tip, pip]) =>
      dist(pts[tip], wrist) <= dist(pts[pip], wrist)
    );

    // Pinch state machine with hysteresis
    if (this.pinchIndexOn) {
      if (pinchRatio > cfg.pinchOffRatio) {
        this.pinchIndexOn = false;
      }
    } else if (pinchRatio < cfg.pinchOnRatio) {
      this.pinchIndexOn = true;
    }

    if (this.pinchMidOn) {
      if (pinchMidRatio > cfg.pinchOffRatio) {
        this.pinchMidOn = false;
      }
    } else if (pinchMidRatio < cfg.pinchOnRatio) {
      this.pinchMidOn = true;
    }

    const tooFar = scale < cfg.minHandScalePx;
    const allCurled = curled.every(Boolean);

    const clearlyCurled = (idx: number): boolean => {
      const [tip, pip] = FINGER_TIPS_PIPS[idx];
      return dist(pts[tip], wrist) <= 0.92 * dist(pts[pip], wrist);
    };

    const peace =
      !curled[INDEX] &&
      !curled[MIDDLE] &&
      clearlyCurled(RING) &&
      clearlyCurled(PINKY);

    const three =
      !curled[INDEX] &&
      !curled[MIDDLE] &&
      !curled[RING] &&
      clearlyCurled(PINKY);

    const oneFinger =
      !curled[INDEX] &&
      curled[MIDDLE] &&
      curled[RING] &&
      curled[PINKY] &&
      !this.pinchIndexOn;

    const pinkyOnly =
      curled[INDEX] && curled[MIDDLE] && curled[RING] && !curled[PINKY];

    // Shaka: thumb extended + pinky extended
    let thumbOut = false;
    if (allCurled || pinkyOnly) {
      const tipY = pts[THUMB_TIP][1];
      const ipY = pts[3][1];
      const dxThumb = Math.abs(pts[THUMB_TIP][0] - pts[3][0]);
      const dyThumb = Math.abs(tipY - ipY);
      thumbOut = dxThumb > 0.3 * scale || dyThumb > 0.25 * scale;
    }

    const thumbPink =
      thumbOut &&
      !curled[PINKY] &&
      curled[INDEX] &&
      curled[MIDDLE] &&
      curled[RING];

    const thumbCurled =
      dist(pts[THUMB_TIP], wrist) < 0.7 * scale ||
      dist(pts[THUMB_TIP], pts[5]) < 0.5 * scale;

    const fourFingers =
      !curled[INDEX] &&
      !curled[MIDDLE] &&
      !curled[RING] &&
      !curled[PINKY] &&
      thumbCurled &&
      !this.pinchIndexOn &&
      !this.pinchMidOn;

    let thumbUp = false;
    if (allCurled) {
      const tipY = pts[THUMB_TIP][1];
      const ipY = pts[3][1];
      const mcpY = Math.min(pts[5][1], pts[9][1], pts[13][1], pts[17][1]);
      const seg = dist(pts[THUMB_TIP], pts[3]);
      const dyUp = ipY - tipY;
      thumbUp =
        tipY < mcpY - 0.15 * scale &&
        seg > 1e-6 &&
        dyUp > 0.55 * seg;
    }

    // Determine geometric gesture
    let geo: GestureType;
    if (tooFar) {
      geo = GestureType.NONE;
    } else if (allCurled) {
      geo = thumbUp ? GestureType.THUMB_UP : GestureType.FIST;
    } else if (this.pinchMidOn) {
      geo = GestureType.PINCH_MID;
    } else if (this.pinchIndexOn) {
      geo = GestureType.PINCH;
    } else if (three) {
      geo = GestureType.THREE;
    } else if (peace) {
      geo = GestureType.PEACE;
    } else if (thumbPink) {
      geo = GestureType.SHAKA;
    } else if (pinkyOnly) {
      geo = GestureType.PINKY;
    } else if (fourFingers) {
      geo = GestureType.FOUR;
    } else if (oneFinger) {
      geo = GestureType.ONE;
    } else {
      geo = GestureType.OPEN;
    }

    const raw = geo;

    // Stability check (confirmation frames)
    if (raw === this.candidate) {
      this.candidateCount++;
    } else {
      this.candidate = raw;
      this.candidateCount = 1;
    }

    let needFrames = cfg.gestureStableFrames;

    const deepClick =
      (raw === GestureType.PINCH && pinchRatio < cfg.pinchOnRatio * 0.75) ||
      (raw === GestureType.PINCH_MID && pinchMidRatio < cfg.pinchOnRatio * 0.75);
    if (deepClick) needFrames = 1;

    const fastRelease =
      [GestureType.PINCH, GestureType.PINCH_MID, GestureType.FIST].includes(this.committed) &&
      raw === GestureType.OPEN;
    if (fastRelease) needFrames = 1;

    let event: string | null = null;
    let value: number | null = null;

    if (this.candidateCount >= needFrames && raw !== this.committed) {
      const previous = this.committed;
      this.committed = raw;
      const transition = this.transition(previous, raw);
      event = transition.event;
      value = transition.value;
    }

    // Scroll tracking
    if (this.committed === GestureType.PEACE) {
      const midY = (pts[INDEX_TIP][1] + pts[MIDDLE_TIP][1]) / 2.0;
      if (this.scrollPrevY !== null) {
        const dy = midY - this.scrollPrevY;
        this.scrollAccY += dy;
        if (Math.abs(this.scrollAccY) >= cfg.scrollDeadzonePx) {
          event = 'scroll';
          value = this.scrollAccY;
          this.scrollAccY = 0.0;
        }
      }
      this.scrollPrevY = midY;
    } else {
      this.scrollPrevY = null;
      this.scrollAccY = 0.0;
    }

    // Volume tracking
    if (this.committed === GestureType.THREE) {
      const volY = (pts[8][1] + pts[12][1] + pts[16][1]) / 3.0;
      if (this.volPrevY !== null) {
        const dy = volY - this.volPrevY;
        this.volAccY -= dy;
        if (Math.abs(this.volAccY) >= cfg.volumeDeadzonePx) {
          event = 'volume';
          value = this.volAccY;
          this.volAccY = 0.0;
        }
      }
      this.volPrevY = volY;
    } else {
      this.volPrevY = null;
      this.volAccY = 0.0;
    }

    // Calculate palm center
    const palmCenter: [number, number] = [
      PALM_IDS.reduce((sum, i) => sum + pts[i][0], 0) / PALM_IDS.length,
      PALM_IDS.reduce((sum, i) => sum + pts[i][1], 0) / PALM_IDS.length,
    ];

    const palmCenterPx: [number, number] = [
      Math.round(palmCenter[0]),
      Math.round(palmCenter[1]),
    ];

    const landmarks: HandLandmarks = {
      points: rawLandmarks,
      palmCenter,
      palmCenterPx,
      indexTip: pts[INDEX_TIP],
      thumbTip: pts[THUMB_TIP],
      pinchRatio,
      pinchMidRatio,
      gesture: this.committed,
      handScalePx: scale,
      aiConfidence: 0.0,
    };

    return { landmarks, event, value };
  }

  private transition(
    previous: GestureType,
    current: GestureType
  ): { event: string | null; value: number | null } {
    const LEFT_BUTTON_GESTURES = [GestureType.PINCH, GestureType.FIST];

    if (current === GestureType.FOUR) {
      return { event: 'minimize', value: null };
    }
    if (current === GestureType.PINCH_MID) {
      return { event: 'right_click', value: null };
    }
    if (current === GestureType.THUMB_UP) {
      return { event: 'play_pause', value: null };
    }
    if (current === GestureType.PINKY) {
      return { event: 'copy', value: null };
    }
    if (current === GestureType.SHAKA) {
      return { event: 'paste', value: null };
    }

    const wasLeft = LEFT_BUTTON_GESTURES.includes(previous);
    const isLeft = LEFT_BUTTON_GESTURES.includes(current);

    if (isLeft && !wasLeft) {
      return { event: 'left_down', value: null };
    }
    if (wasLeft && !isLeft) {
      return { event: 'left_up', value: null };
    }

    return { event: null, value: null };
  }
}
