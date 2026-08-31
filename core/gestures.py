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
    ONE = "mover (1 dedo)"
    PINCH = "clique esquerdo"
    PINCH_MID = "clique direito"
    FIST = "arrastar"
    PEACE = "scroll"
    THREE = "volume"
    THUMB_UP = "play/pausa"
    THUMB_DOWN = "deslike"
    PINKY = "copiar"
    SHAKA = "colar"
    ROCK = "interface"


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
    LEFT_BUTTON_GESTURES = (Gesture.PINCH,)

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
        self._prev_curled = [False, False, False, False]

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
        self._prev_curled = [False, False, False, False]

    def update(self, landmarks, width, height):
        cfg = self.cfg
        pts = [(lm[0] * width, lm[1] * height) for lm in landmarks]
        wrist = pts[0]
        scale = max(_dist(wrist, pts[9]), 1e-6)
        # racio 2D: fiável de frente para a câmara (os dedos sobrepõem-se na projeção)
        pinch_ratio_2d = _dist(pts[THUMB_TIP], pts[INDEX_TIP]) / scale
        pinch_mid_ratio_2d = _dist(pts[THUMB_TIP], pts[MIDDLE_TIP]) / scale
        if len(landmarks[0]) > 2:
            # racio 3D: imune a inclinacao da mao (foreshortening)
            ky = height / width
            p3 = [(lm[0], lm[1] * ky, lm[2]) for lm in landmarks]

            def _d3(a, b):
                return math.sqrt(
                    (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
                )

            scale3 = max(_d3(p3[0], p3[9]), 1e-6)
            pinch_ratio_3d = _d3(p3[THUMB_TIP], p3[INDEX_TIP]) / scale3
            pinch_mid_ratio_3d = _d3(p3[THUMB_TIP], p3[MIDDLE_TIP]) / scale3
        else:
            pinch_ratio_3d = pinch_ratio_2d
            pinch_mid_ratio_3d = pinch_mid_ratio_2d
        # Pinça do INDICADOR (clique esq): mínimo(2D,3D) — robusto de frente para a
        # câmara, onde o z-noise do MediaPipe inflaciona o rácio 3D acima do limiar.
        pinch_ratio = min(pinch_ratio_2d, pinch_ratio_3d)
        # Pinça do MÉDIO (clique dir): só 3D — a projeção 2D colapsa quando o polegar
        # se curva sobre a palma (durante o agarrar) e daria cliques-direitos fantasmas.
        pinch_mid_ratio = pinch_mid_ratio_3d

        # Dedos "dobrados" com deadband (Schmitt trigger): um dedo a pairar no
        # limiar de dobrar/esticar (razão tip/pip ~ 1.0) não faz o gesto tremer
        # de frame para frame (ex.: ONE<->OPEN, PEACE<->THREE, FIST<->THUMB_UP).
        # Só muda de estado depois de cruzar uma folga confortável, usando o
        # estado da frame anterior como memória. Casos claros comportam-se como
        # antes (dobrado<=esticado), pelo que os valores de fluxo normal se mantêm.
        fold_on_margin = 1.06   # para sair de "dobrado" tem de esticar bastante
        fold_off_margin = 0.94  # para sair de "esticado" tem de dobrar bastante
        curled = []
        for i, (tip, pip) in enumerate(FINGER_TIPS_PIPS):
            d_tip = _dist(pts[tip], wrist)
            d_pip = max(_dist(pts[pip], wrist), 1e-6)
            ratio = d_tip / d_pip
            if self._prev_curled[i]:
                now_curled = ratio < fold_on_margin
            else:
                now_curled = ratio < fold_off_margin
            curled.append(now_curled)
        self._prev_curled = curled

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
        # ROCK / "chifre": indicador + mindinho em pé, medio e anelar dobrados.
        rock = (
            not curled[INDEX]
            and not curled[PINKY]
            and _clearly_curled(MIDDLE)
            and _clearly_curled(RING)
        )
        one_finger = (
            not curled[INDEX]
            and curled[MIDDLE]
            and curled[RING]
            and curled[PINKY]
            and not self._pinch_index_on
        )
        pinky_only = (
            curled[INDEX]
            and curled[MIDDLE]
            and curled[RING]
            and not curled[PINKY]
        )
        # SHAKA: thumb extended (not curled toward wrist) + pinky extended
        thumb_out = False
        if all_curled or pinky_only:
            tip_y = pts[THUMB_TIP][1]
            ip_y = pts[3][1]
            dx_thumb = abs(pts[THUMB_TIP][0] - pts[3][0])
            dy_thumb = abs(tip_y - ip_y)
            thumb_out = dx_thumb > 0.3 * scale or dy_thumb > 0.25 * scale
        thumb_pinky = (
            thumb_out
            and not curled[PINKY]
            and curled[INDEX]
            and curled[MIDDLE]
            and curled[RING]
        )
        thumb_up = False
        if all_curled:
            # polegar apontando claramente para cima, acima de todos os MCPs
            tip_y = pts[THUMB_TIP][1]
            ip_y = pts[3][1]
            mcp_y = min(pts[i][1] for i in (5, 9, 13, 17))
            dy_up = ip_y - tip_y
            seg = _dist(pts[THUMB_TIP], pts[3])
            thumb_up = (
                tip_y < mcp_y - 0.15 * scale
                and seg > 1e-6
                and dy_up > 0.55 * seg
            )
        # "Deslike": punho fechado com o polegar apontando claramente para baixo
        # (espelho do THUMB_UP). Usado como gate para mostrar/ocultar a interface.
        thumb_down = False
        if all_curled:
            tip_y = pts[THUMB_TIP][1]
            ip_y = pts[3][1]
            mcp_y = max(pts[i][1] for i in (5, 9, 13, 17))
            dy_down = tip_y - ip_y
            seg = _dist(pts[THUMB_TIP], pts[3])
            thumb_down = (
                tip_y > mcp_y + 0.15 * scale
                and seg > 1e-6
                and dy_down > 0.55 * seg
            )

        if too_far:
            geo = Gesture.NONE
        elif all_curled:
            if thumb_up:
                geo = Gesture.THUMB_UP
            elif thumb_down:
                geo = Gesture.THUMB_DOWN
            else:
                geo = Gesture.FIST
        elif self._pinch_mid_on:
            geo = Gesture.PINCH_MID
        elif self._pinch_index_on:
            geo = Gesture.PINCH
        elif three:
            geo = Gesture.THREE
        elif peace:
            geo = Gesture.PEACE
        elif rock:
            geo = Gesture.ROCK
        elif thumb_pinky:
            geo = Gesture.SHAKA
        elif pinky_only:
            geo = Gesture.PINKY
        elif one_finger:
            geo = Gesture.ONE
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
                    (ml_g == Gesture.OPEN and geo == Gesture.OPEN)
                    or (ml_g == Gesture.ONE and one_finger)
                    or (ml_g == Gesture.PINCH and self._pinch_index_on)
                    or (ml_g == Gesture.PINCH_MID and self._pinch_mid_on)
                    or (ml_g == Gesture.FIST and all_curled
                     and geo not in (Gesture.THUMB_UP, Gesture.THUMB_DOWN))
                    or (ml_g == Gesture.PEACE and peace)
                    or (ml_g == Gesture.THREE and three)
                    or (ml_g == Gesture.THUMB_UP and thumb_up)
                    or (ml_g == Gesture.PINKY and pinky_only)
                    or (ml_g == Gesture.SHAKA and thumb_pinky)
                )
                geo_click = geo in (Gesture.PINCH, Gesture.PINCH_MID)
                if ml_ok and not (geo_click and ml_g == Gesture.OPEN):
                    raw = ml_g
                    if raw == Gesture.PINCH and pinch_ratio < cfg.pinch_off_ratio:
                        self._pinch_index_on = True
                    if raw == Gesture.PINCH_MID and pinch_mid_ratio < cfg.pinch_off_ratio:
                        self._pinch_mid_on = True

        if raw == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = raw
            self._candidate_count = 1

        # A pinca (clique) tem uma confirmacao propria e mais curta: o Schmitt
        # on/off ja suporta o ruido, pelo que acelerar aqui nao custa robustez.
        need_frames = (
            max(1, int(cfg.pinch_stable_frames))
            if raw in (Gesture.PINCH, Gesture.PINCH_MID)
            else cfg.gesture_stable_frames
        )
        deep_click = (
            raw == Gesture.PINCH and pinch_ratio < cfg.pinch_on_ratio * 0.75
        ) or (
            raw == Gesture.PINCH_MID and pinch_mid_ratio < cfg.pinch_on_ratio * 0.75
        )
        if deep_click:
            need_frames = 1

        fast_release = (
            self._committed in (Gesture.PINCH, Gesture.PINCH_MID, Gesture.FIST)
            and raw == Gesture.OPEN
        )
        if fast_release:
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

        # Scroll: punho fechado (FIST) na mao de comandos; deslizar para cima/baixo
        # desloca o scroll na direcao oposta do movimento do punho.
        if self._committed == Gesture.FIST:
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
                # mesmo sinal do scroll: mover para baixo -> valor positivo
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
        if current == Gesture.PINKY:
            return "copy", None
        if current == Gesture.SHAKA:
            return "paste", None
        was_left = previous in cls.LEFT_BUTTON_GESTURES
        is_left = current in cls.LEFT_BUTTON_GESTURES
        if is_left and not was_left:
            return "left_down", None
        if was_left and not is_left:
            return "left_up", None
        return None, None
