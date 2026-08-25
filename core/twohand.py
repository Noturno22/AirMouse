import math
import subprocess
import time

from core.gestures import Gesture

CREATE_NO_WINDOW = 0x08000000


class ClapDetector:
    """Deteta palmas: duas maos abertas que se aproximam depressa.

    Exige que as maos estiveram separadas antes (evita falsos positivos
    quando as maos ja estao juntas) e tem cooldown apos disparar.
    """

    def __init__(self, sep_factor=3.0, close_factor=1.35, speed_factor=2.0,
                 stable_frames=2, cooldown_s=1.2):
        self.sep_factor = float(sep_factor)
        self.close_factor = float(close_factor)
        self.speed_factor = float(speed_factor)
        self.stable_frames = max(int(stable_frames), 1)
        self.cooldown_s = float(cooldown_s)
        self.reset()

    def reset(self):
        self._prev_d = None
        self._prev_t = None
        self._separated = False
        self._count = 0
        self._until = 0.0

    def update(self, palms, scales, now):
        if len(palms) != 2 or len(scales) != 2:
            self.reset()
            return False
        ms = (max(scales[0], 1e-3) + max(scales[1], 1e-3)) / 2.0
        d = math.hypot(palms[0][0] - palms[1][0], palms[0][1] - palms[1][1])
        v = 0.0
        if self._prev_d is not None and self._prev_t is not None:
            dt = max(now - self._prev_t, 1e-3)
            v = (self._prev_d - d) / dt
        self._prev_d = d
        self._prev_t = now

        if d > self.sep_factor * ms:
            self._separated = True
            self._count = 0
            return False
        if now < self._until or not self._separated:
            return False
        closing = v > self.speed_factor * ms
        near = d < self.close_factor * ms
        if closing and near:
            self._count += 1
        else:
            self._count = max(0, self._count - 1)
        if self._count >= self.stable_frames:
            self._until = now + self.cooldown_s
            self._separated = False
            self._count = 0
            return True
        return False


def _zoom_key(kb, up):
    from pynput.keyboard import Key

    kb.press(Key.cmd)
    kb.press("+" if up else "-")
    kb.release("+" if up else "-")
    kb.release(Key.cmd)


def _magnifier_exit(kb):
    from pynput.keyboard import Key

    kb.press(Key.cmd)
    kb.press(Key.esc)
    kb.release(Key.esc)
    kb.release(Key.cmd)


class MagnifierCtl:
    """Lupa do Windows controlada pela distancia entre as duas maos.

    Duas maos ABERTAS durante alguns frames entram no modo; afastar
    aproxima as maos aumenta/diminui o zoom por passos. Soltar uma mao
    ou deixar de ter as duas abertas sai do modo.
    """

    def __init__(self, step_frac=0.85, enter_frames=5, exit_s=0.35,
                 step_cooldown_s=0.14):
        from pynput.keyboard import Controller

        self.kb = Controller()
        self.step_frac = float(step_frac)
        self.enter_frames = max(int(enter_frames), 2)
        self.exit_s = float(exit_s)
        self.step_cooldown_s = float(step_cooldown_s)
        self.on = False
        self.last_action = ""
        self._streak = 0
        self._baseline = 0.0
        self._last_step_t = 0.0
        self._bad_since = None

    def _launch_magnifier(self):
        try:
            subprocess.Popen(["magnify.exe"], creationflags=CREATE_NO_WINDOW)
            time.sleep(0.4)
            return True
        except Exception:
            return False

    def update(self, entries, now):
        """entries: lista [(gesture, palm, scale)] das maos presentes."""
        both_open = len(entries) == 2 and all(e[0] == Gesture.OPEN for e in entries)
        if not self.on:
            if both_open:
                self._streak += 1
                if self._streak >= self.enter_frames:
                    self.on = True
                    self._baseline = math.hypot(
                        entries[0][1][0] - entries[1][1][0],
                        entries[0][1][1] - entries[1][1][1],
                    )
                    self._launch_magnifier()
                    self.last_action = "LUPA ON"
                    return self.last_action
            else:
                self._streak = 0
            return None

        good = both_open and len(entries) == 2
        if not good:
            if self._bad_since is None:
                self._bad_since = now
            elif now - self._bad_since >= self.exit_s:
                self.on = False
                self._streak = 0
                self._bad_since = None
                self.last_action = "LUPA OFF"
                return self.last_action
            return None
        self._bad_since = None

        d = math.hypot(
            entries[0][1][0] - entries[1][1][0],
            entries[0][1][1] - entries[1][1][1],
        )
        ms = (entries[0][2] + entries[1][2]) / 2.0
        step = max(self.step_frac * ms, 8.0)
        if now - self._last_step_t < self.step_cooldown_s:
            return None
        if d - self._baseline >= step:
            _zoom_key(self.kb, True)
            self._baseline += step
            self._last_step_t = now
            self.last_action = "ZOOM +"
        elif self._baseline - d >= step:
            _zoom_key(self.kb, False)
            self._baseline -= step
            self._last_step_t = now
            self.last_action = "ZOOM -"
        return None

    def force_off(self):
        if self.on:
            self.on = False
            self._streak = 0
        _magnifier_exit(self.kb)
        self.last_action = "LUPA OFF"
        return "LUPA OFF"

    def force_on(self):
        self._launch_magnifier()
        self.on = False
        self._streak = 0
        self.last_action = "LUPA ON"
        return "LUPA ON"


class HandPool:
    """Uma GestureEngine por mao (esquerda/direita), com reset individual."""

    def __init__(self, cfg, gesture_ai=None):
        from core.gestures import GestureEngine

        self.engines = {
            "Left": GestureEngine(cfg, gesture_ai),
            "Right": GestureEngine(cfg, gesture_ai),
        }
        self._seen = set()

    def update(self, hands, sides, width, height):
        results = {}
        seen = set()
        for hand, side in zip(hands, sides):
            label = side if side in self.engines else "Right"
            if label in results:
                continue
            seen.add(label)
            results[label] = self.engines[label].update(hand, width, height)
        for label in self.engines:
            if label not in seen:
                self.engines[label].reset()
        return results
