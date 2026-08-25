import math
from dataclasses import dataclass
from enum import Enum

FINGER_TIPS_PIPS = ((8, 6), (12, 10), (16, 14), (20, 18))
PALM_IDS = (0, 5, 9, 13, 17)
INDEX, MIDDLE, RING, PINKY = 0, 1, 2, 3
THUMB_TIP, INDEX_TIP, MIDDLE_TIP = 4, 8, 12


class Gesture(Enum):
    NONE = "sem mao"
    OPEN = "mover"
    PINCH = "clique esquerdo"
    PINCH_MID = "clique direito"
    FIST = "arrastar"
    PEACE = "scroll"
    THREE = "volume"
    THUMB_UP = "play/pausa"


@dataclass
class HandFrame:
    points_px: list
    hand_scale_px: float
    pinch_ratio: float
    pinch_mid_ratio: float
    raw_gesture: "Gesture"
    gesture: "Gesture"
    index_tip: tuple
    palm_center: tuple
    ai_conf: float = 0.0


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class GestureEngine:
    LEFT_BUTTON_GESTURES = (Gesture.PINCH, Gesture.FIST)

    def __init__(self, cfg, gesture_ai=None):
        self.cfg = cfg
        self.ai = gesture_ai
        self.ai_conf = 0.0
        self._pinch_index_on = False
        self._pinch_mid_on = False
        self._candidate = Gesture.NONE
        self._candidate_count = 0
        self._committed = Gesture.NONE
        self._scroll_prev_y = None
        self._scroll_acc_y = 0.0
        self._vol_prev_y = None
        self._vol_acc_y = 0.0

    def reset(self):
        self._pinch_index_on = False
        self._pinch_mid_on = False
        self._candidate = Gesture.NONE
        self._candidate_count = 0
        self._committed = Gesture.NONE
        self._scroll_prev_y = None
        self._scroll_acc_y = 0.0
        self._vol_prev_y = None
        self._vol_acc_y = 0.0

    def update(self, landmarks, width, height):
        cfg = self.cfg
        pts = [(lm[0] * width, lm[1] * height) for lm in landmarks]
        wrist = pts[0]
        scale = max(_dist(wrist, pts[9]), 1e-6)
        if len(landmarks[0]) > 2:
            # racio 3D: imune a inclinacao da mao (foreshortening)
            ky = height / width
            p3 = [(lm[0], lm[1] * ky, lm[2]) for lm in landmarks]

            def _d3(a, b):
                return math.sqrt(
                    (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
                )

            scale3 = max(_d3(p3[0], p3[9]), 1e-6)
            pinch_ratio = _d3(p3[THUMB_TIP], p3[INDEX_TIP]) / scale3
            pinch_mid_ratio = _d3(p3[THUMB_TIP], p3[MIDDLE_TIP]) / scale3
        else:
            pinch_ratio = _dist(pts[THUMB_TIP], pts[INDEX_TIP]) / scale
            pinch_mid_ratio = _dist(pts[THUMB_TIP], pts[MIDDLE_TIP]) / scale

        curled = [
            _dist(pts[tip], wrist) <= _dist(pts[pip], wrist)
            for tip, pip in FINGER_TIPS_PIPS
        ]

        if self._pinch_index_on:
            if pinch_ratio > cfg.pinch_off_ratio:
                self._pinch_index_on = False
        elif pinch_ratio < cfg.pinch_on_ratio:
            self._pinch_index_on = True

        if self._pinch_mid_on:
            if pinch_mid_ratio > cfg.pinch_off_ratio:
                self._pinch_mid_on = False
        elif pinch_mid_ratio < cfg.pinch_on_ratio:
            self._pinch_mid_on = True

        too_far = scale < cfg.min_hand_scale_px
        all_curled = all(curled)

        def _clearly_curled(idx):
            tip, pip = FINGER_TIPS_PIPS[idx]
            return _dist(pts[tip], wrist) <= 0.92 * _dist(pts[pip], wrist)

        peace = (
            not curled[INDEX]
            and not curled[MIDDLE]
            and _clearly_curled(RING)
            and _clearly_curled(PINKY)
        )
        three = (
            not curled[INDEX]
            and not curled[MIDDLE]
            and not curled[RING]
            and _clearly_curled(PINKY)
        )
        thumb_up = False
        if all_curled:
            # polegar apontando claramente para cima, acima de todos os MCPs
            tip_y = pts[THUMB_TIP][1]
            ip_y = pts[3][1]
            mcp_y = min(pts[i][1] for i in (5, 9, 13, 17))
            dx = pts[THUMB_TIP][0] - pts[3][0]
            dy_up = ip_y - tip_y
            seg = _dist(pts[THUMB_TIP], pts[3])
            thumb_up = (
                tip_y < mcp_y - 0.15 * scale
                and seg > 1e-6
                and dy_up > 0.55 * seg
            )

        if too_far:
            geo = Gesture.NONE
        elif all_curled:
            geo = Gesture.THUMB_UP if thumb_up else Gesture.FIST
        elif self._pinch_mid_on:
            geo = Gesture.PINCH_MID
        elif self._pinch_index_on:
            geo = Gesture.PINCH
        elif three:
            geo = Gesture.THREE
        elif peace:
            geo = Gesture.PEACE
        else:
            geo = Gesture.OPEN

        raw = geo
        self.ai_conf = 0.0
        if self.ai is not None and not too_far:
            ml_g, conf = self.ai.classify(pts)
            self.ai_conf = conf
            if ml_g is not None and conf >= cfg.ai_confidence_min:
                # a IA so pode confirmar o que a geometria tambem ve;
                # nunca inventa modos (THREE/PEACE/FIST) nem mata um clique ativo
                ml_ok = (
                    ml_g == Gesture.OPEN
                    or (ml_g == Gesture.PINCH and self._pinch_index_on)
                    or (ml_g == Gesture.PINCH_MID and self._pinch_mid_on)
                    or (ml_g == Gesture.FIST and all_curled)
                    or (ml_g == Gesture.PEACE and peace)
                    or (ml_g == Gesture.THREE and three)
                    or (ml_g == Gesture.THUMB_UP and thumb_up)
                )
                geo_click = geo in (Gesture.PINCH, Gesture.PINCH_MID)
                if ml_ok and not (geo_click and ml_g == Gesture.OPEN):
                    raw = ml_g
                    if raw == Gesture.PINCH and pinch_ratio < cfg.pinch_off_ratio:
                        self._pinch_index_on = True
                    if raw == Gesture.PINCH_MID and pinch_mid_ratio < cfg.pinch_off_ratio:
                        self._pinch_mid_on = True

        ext_count = sum(1 for c in curled if not c)
        if not too_far and ext_count >= 4 and raw != Gesture.OPEN:
            raw = Gesture.OPEN

        if raw == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = raw
            self._candidate_count = 1

        need_frames = cfg.gesture_stable_frames
        deep_click = (
            raw == Gesture.PINCH and pinch_ratio < cfg.pinch_on_ratio * 0.75
        ) or (
            raw == Gesture.PINCH_MID and pinch_mid_ratio < cfg.pinch_on_ratio * 0.75
        )
        if deep_click:
            need_frames = 1

        event = None
        value = None
        if (
            self._candidate_count >= need_frames
            and raw != self._committed
        ):
            previous = self._committed
            self._committed = raw
            event, value = self._transition(previous, raw)

        if self._committed == Gesture.PEACE:
            mid_y = (pts[INDEX_TIP][1] + pts[MIDDLE_TIP][1]) / 2.0
            if self._scroll_prev_y is not None:
                dy = mid_y - self._scroll_prev_y
                self._scroll_acc_y += dy
                if abs(self._scroll_acc_y) >= cfg.scroll_deadzone_px:
                    event, value = "scroll", self._scroll_acc_y
                    self._scroll_acc_y = 0.0
            self._scroll_prev_y = mid_y
        else:
            self._scroll_prev_y = None
            self._scroll_acc_y = 0.0

        if self._committed == Gesture.THREE:
            vol_y = (pts[8][1] + pts[12][1] + pts[16][1]) / 3.0
            if self._vol_prev_y is not None:
                dy = vol_y - self._vol_prev_y
                self._vol_acc_y += dy
                if abs(self._vol_acc_y) >= cfg.volume_deadzone_px:
                    event, value = "volume", self._vol_acc_y
                    self._vol_acc_y = 0.0
            self._vol_prev_y = vol_y
        else:
            self._vol_prev_y = None
            self._vol_acc_y = 0.0

        palm_center = (
            sum(pts[i][0] for i in PALM_IDS) / len(PALM_IDS),
            sum(pts[i][1] for i in PALM_IDS) / len(PALM_IDS),
        )
        frame = HandFrame(
            points_px=pts,
            hand_scale_px=scale,
            pinch_ratio=pinch_ratio,
            pinch_mid_ratio=pinch_mid_ratio,
            raw_gesture=raw,
            gesture=self._committed,
            index_tip=pts[INDEX_TIP],
            palm_center=palm_center,
            ai_conf=self.ai_conf,
        )
        return frame, event, value

    @classmethod
    def _transition(cls, previous, current):
        if current == Gesture.PINCH_MID:
            return "right_click", None
        if current == Gesture.THUMB_UP:
            return "play_pause", None
        was_left = previous in cls.LEFT_BUTTON_GESTURES
        is_left = current in cls.LEFT_BUTTON_GESTURES
        if is_left and not was_left:
            return "left_down", None
        if was_left and not is_left:
            return "left_up", None
        return None, None
