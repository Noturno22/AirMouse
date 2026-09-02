import math
import subprocess
import time

from core.gestures import Gesture, GestureEngine

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
                _magnifier_exit(self.kb)
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

        self.engines = {
            "Left": GestureEngine(cfg, gesture_ai),
            "Right": GestureEngine(cfg, gesture_ai),
        }
        self._seen = set()

    def _palm_center(self, hand):
        """Centro X (pulso + base dos dedos) de uma detecao, normalizado."""
        return (hand[0][0] + hand[9][0]) / 2.0 if len(hand) > 9 else hand[0][0]

    def update(self, hands, sides, width, height):
        # O MediaPipe por vezes devolve A MESMA mao real detetada 2x (labels
        # iguais, palma quase na mesma posicao) - isto NAO sao duas maos e nao
        # devia gerar uma segunda entidade (falso "2 maos" no Free, gestos de
        # 2 maos indevidos). Descarta a duplicata quando as palmas coincidem.
        kept = []
        for hand, side in zip(hands, sides):
            cx = self._palm_center(hand)
            if any(abs(kx - cx) < 0.18 for kx, _, _ in kept):
                continue
            kept.append((cx, side, hand))
        # Com 1 mao real mantemos o label original; com 2 maos reais distintas
        # opomos os labels (o MediaPipe desta camara marca ambas "Right").
        results = {}
        seen = set()
        for i, (cx, side, hand) in enumerate(kept):
            label = side if side in self.engines else "Right"
            if label in seen:
                label = "Left" if label == "Right" else "Right"
            seen.add(label)
            results[label] = self.engines[label].update(hand, width, height)
        for label in self.engines:
            if label not in seen:
                self.engines[label].reset()
        return results


class BrightnessCtl:
    """Controla luminosidade do ecra via gamma ramp (Windows).

    Cada chamada a decrease/increase ajusta o brilho por um passo
    percentual. Usa a API SetDeviceGammaRamp do gdi32 para resposta
    instantanea.
    """

    def __init__(self, step=10, initial=70):
        self.step = step
        self.level = initial
        try:
            import ctypes
            self._gdi32 = ctypes.windll.gdi32
            self._user32 = ctypes.windll.user32
            self._available = True
        except Exception:
            self._available = False

    def decrease(self):
        self.level = max(5, self.level - self.step)
        self._apply(self.level)
        return f"LUMINOSIDADE {self.level}%"

    def increase(self):
        self.level = min(100, self.level + self.step)
        self._apply(self.level)
        return f"LUMINOSIDADE {self.level}%"

    def _apply(self, level):
        if not self._available:
            return
        g = max(0.0, min(level / 100.0, 1.0))
        try:
            hdc = self._user32.GetDC(None)
            if not hdc:
                return
            ramp = (__import__("ctypes").c_ushort * 768)()
            for i in range(256):
                v = min(int(i * g * 257), 65535)
                ramp[i] = v
                ramp[256 + i] = v
                ramp[512 + i] = v
            self._gdi32.SetDeviceGammaRamp(hdc, __import__("ctypes").byref(ramp))
            self._user32.ReleaseDC(None, hdc)
        except Exception:
            pass


class FistCycleDetector:
    """Deteta ciclos de fechar/abrir punho para atalhos (ex: Ctrl+D).

    Conta transicoes FIST->OPEN dentro de uma janela temporal.
    Apos N ciclos completos, dispara a accao e reinicia.
    """

    def __init__(self, cycles_needed=2, window_s=2.5, cooldown_s=2.0):
        self.cycles_needed = cycles_needed
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self._in_fist = False
        self._cycle_count = 0
        self._first_t = None
        self._until = 0.0

    def update(self, gesture, now):
        if now < self._until:
            return False
        if gesture == Gesture.FIST:
            self._in_fist = True
        elif gesture == Gesture.OPEN:
            if self._in_fist:
                self._in_fist = False
                if self._first_t is None:
                    self._first_t = now
                self._cycle_count += 1
                if now - self._first_t > self.window_s:
                    self._cycle_count = 1
                    self._first_t = now
                elif self._cycle_count >= self.cycles_needed:
                    self._cycle_count = 0
                    self._first_t = None
                    self._until = now + self.cooldown_s
                    return True
        else:
            self._in_fist = False
        return False


class WaveDetector:
    """Deteta gesto de "bye bye" (onda lateral) para atalhos (ex: Ctrl+E).

    Rastreia a posicao X da palma e conta inversoes de direcao.
    Apos M inversoes na janela temporal, dispara a accao.
    """

    def __init__(self, min_reversals=3, window_s=1.5,
                 min_amplitude_px=15.0, cooldown_s=2.0):
        self.min_reversals = min_reversals
        self.window_s = window_s
        self.min_amplitude_px = min_amplitude_px
        self.cooldown_s = cooldown_s
        self._points = []
        self._until = 0.0

    def update(self, palm_x, now):
        if now < self._until:
            return False
        self._points.append((palm_x, now))
        while self._points and now - self._points[0][1] > self.window_s:
            self._points.pop(0)
        if len(self._points) < 4:
            return False
        reversals = 0
        last_dir = 0
        prev_x = self._points[0][0]
        for i in range(1, len(self._points)):
            dx = self._points[i][0] - prev_x
            if abs(dx) < self.min_amplitude_px:
                continue
            cur_dir = 1 if dx > 0 else -1
            if last_dir != 0 and cur_dir != last_dir:
                reversals += 1
            last_dir = cur_dir
            prev_x = self._points[i][0]
        if reversals >= self.min_reversals:
            self._points.clear()
            self._until = now + self.cooldown_s
            return True
        return False


class MultiClapDetector:
    """Deteta N palmas rapidas para atalhos (ex: Alt+Tab).

    Funciona independentemente do ClapDetector de palma unica.
    Conta palmas dentro de uma janela temporal e dispara apos N.
    """

    def __init__(self, claps_needed=3, window_s=2.5, cooldown_s=2.5,
                 sep_factor=3.0, close_factor=1.35, speed_factor=2.0):
        self.claps_needed = claps_needed
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self.sep_factor = sep_factor
        self.close_factor = close_factor
        self.speed_factor = speed_factor
        self._prev_d = None
        self._prev_t = None
        self._separated = False
        self._fired_current = False
        self._count = 0
        self._window_start = None
        self._until = 0.0

    def update(self, palms, scales, now):
        if now < self._until:
            return False
        if len(palms) != 2 or len(scales) != 2:
            self._prev_d = None
            self._prev_t = None
            self._separated = False
            self._fired_current = False
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
            self._fired_current = False
        closing = v > self.speed_factor * ms
        near = d < self.close_factor * ms
        if closing and near and self._separated and not self._fired_current:
            self._fired_current = True
            if (self._window_start is None
                    or now - self._window_start > self.window_s):
                self._count = 1
                self._window_start = now
            else:
                self._count += 1
            if self._count >= self.claps_needed:
                self._count = 0
                self._window_start = None
                self._until = now + self.cooldown_s
                return True
        if not closing or not near:
            self._fired_current = False
        if (self._window_start is not None
                and now - self._window_start > self.window_s):
            self._count = 0
            self._window_start = None
        return False


class DualWaveDetector:
    """Deteta ondas rapidas com as duas maos para atalhos (ex: Alt+Tab).

    Rastreia o ponto medio X das duas maos e conta inversoes de direcao.
    Apos M inversoes na janela temporal, dispara a accao.
    """

    def __init__(self, min_reversals=2, window_s=1.5,
                 min_amplitude_px=20.0, cooldown_s=2.0):
        self.min_reversals = min_reversals
        self.window_s = window_s
        self.min_amplitude_px = min_amplitude_px
        self.cooldown_s = cooldown_s
        self._points = []
        self._until = 0.0

    def update(self, palms, now):
        if now < self._until:
            return False
        if len(palms) != 2:
            self._points.clear()
            return False
        mid_x = (palms[0][0] + palms[1][0]) / 2.0
        self._points.append((mid_x, now))
        while self._points and now - self._points[0][1] > self.window_s:
            self._points.pop(0)
        if len(self._points) < 4:
            return False
        reversals = 0
        last_dir = 0
        prev_x = self._points[0][0]
        for i in range(1, len(self._points)):
            dx = self._points[i][0] - prev_x
            if abs(dx) < self.min_amplitude_px:
                continue
            cur_dir = 1 if dx > 0 else -1
            if last_dir != 0 and cur_dir != last_dir:
                reversals += 1
            last_dir = cur_dir
            prev_x = self._points[i][0]
        if reversals >= self.min_reversals:
            self._points.clear()
            self._until = now + self.cooldown_s
            return True
        return False


class LeftHandDetector:
    """Comandos especiais da MAO ESQUERDA, totalmente separada da direita.

    A mao direita continua responsavel por mover o cursor/arrastar. A mao
    esquerda, por sua vez, funciona como uma "mao de comandos":

      * SWIPE horizontal (esq/dir) -> troca rapida de janela (solta logo);
      * Segurar a mao ABERTA ~2s  -> abre o alternador de janelas (pick mode);
        enquanto ativo, os swipes navegam sem soltar (confirmar = soltar a mao);
      * DESLIZAR para cima/baixo   -> scroll (movimento vertical continuo).

    Retorna um evento por chamada a update():
      ('alt_tab_forward', None)  swipe para a direita (troca rapida)
      ('alt_tab_back', None)  swipe para a esquerda (troca rapida)
      ('alt_switch_open', None)  mao aberta mantida Ns (abre alternador)
      ('scroll', value)  valor acumulado de scroll vertical
    """

    def __init__(self, cfg, allow_commands=True):
        self.cfg = cfg
        # No Free, o PEACE (paz) com a mao esquerda continua a funcionar para
        # mostrar/ocultar a interface, mas os comandos (swipe/alternador/scroll)
        # ficam desligados (sao recursos Pro).
        self.allow_commands = allow_commands
        self.reset()

    def reset(self):
        self._samples = []
        self._scroll_prev_y = None
        self._scroll_acc = 0.0
        self._swipe_until = 0.0
        # PEACE ("paz") com a mao esquerda mostra/oculta a interface (GUI).
        # _peace_on guarda o estado do gesto da frame anterior (rising edge) e
        # _toggle_until e o cooldown contra disparos repetidos ao manter o gesto.
        self._peace_on = False
        self._toggle_until = 0.0
        # "Pick mode" (escolher janela): mao esquerda aberta e mantida durante
        # alguns segundos abre o alternador de janelas. Enquanto o pick mode
        # estiver ativo, os swipes navegam sem soltar o Alt.
        self._open_since = None
        self._switcher_open = False

    def update(self, palm, now, gesture=None):
        """palm: (x, y) em px, ou None se a mao esquerda nao estiver visivel.
        gesture: opcional (Gesture) da mao esquerda, usado para o gesto de
        paz (PEACE) que mostra/oculta a interface."""
        cfg = self.cfg
        if palm is None:
            self.reset()
            return None, None
        px, py = palm
        self._samples.append((px, py, now))
        while self._samples and now - self._samples[0][2] > cfg.left_hand_swipe_window_s:
            self._samples.pop(0)

        ev = None
        val = None

        # PEACE ("paz") com a mao esquerda -> mostrar/ocultar a interface (GUI).
        # Dispara na transicao para PEACE (rising edge) e tem cooldown para nao
        # repetir enquanto a mao ficar parada no gesto.
        if gesture is not None:
            if gesture == Gesture.PEACE:
                if not self._peace_on and now >= self._toggle_until:
                    self._toggle_until = now + cfg.left_hand_cooldown_s
                    ev = "gui_toggle"
                    val = None
                    self._samples.clear()
                    self._scroll_acc = 0.0
                    self._scroll_prev_y = None
                self._peace_on = True
            else:
                self._peace_on = False

        # Pick mode: segurar a mao ABERTA durante N segundos abre o alternador.
        # Apos disparar, mantem-se ativo enquanto a mao continuar aberta; os
        # swipes seguintes navegam no alternador sem soltar (handled em main).
        # (Pro-locked: no Free, allow_commands=False desliga swipe/alternador/scroll.)
        if self.allow_commands and gesture == Gesture.OPEN:
            if self._open_since is None:
                self._open_since = now
            elif not self._switcher_open and now - self._open_since >= cfg.left_hand_open_switch_s:
                self._switcher_open = True
                self._swipe_until = now + cfg.left_hand_cooldown_s
                return "alt_switch_open", None
        else:
            self._open_since = None
            self._switcher_open = False

        # SWIPE horizontal + Scroll continuo (Pro-locked: no Free ficam desligados).
        if self.allow_commands:
            # SWIPE horizontal: deslocamento X dominante e rapido dentro da janela
            if now >= self._swipe_until and len(self._samples) >= 3:
                x0 = self._samples[0][0]
                dx = px - x0
                dy = py - self._samples[0][1]
                if abs(dx) >= cfg.left_hand_swipe_min_px and abs(dx) > abs(dy) * 1.5:
                    ev = "alt_tab_forward" if dx > 0 else "alt_tab_back"
                    val = None
                    self._swipe_until = now + cfg.left_hand_cooldown_s
                    self._samples.clear()
                    self._scroll_acc = 0.0
                    self._scroll_prev_y = None

            # Scroll vertical continuo (dominancia vertical, fora de cooldown de swipe)
            if ev is None:
                if self._scroll_prev_y is not None:
                    dy = py - self._scroll_prev_y
                    if abs(dy) >= cfg.left_hand_scroll_deadzone_px:
                        direction = 1 if dy < 0 else -1
                        self._scroll_acc += direction * abs(dy)
                    elif abs(py - self._samples[0][1]) > abs(px - self._samples[0][0]):
                        self._scroll_acc = 0.0
                self._scroll_prev_y = py
                if abs(self._scroll_acc) >= cfg.left_hand_scroll_deadzone_px:
                    ev = "scroll"
                    val = self._scroll_acc
                    self._scroll_acc = 0.0

        return ev, val
