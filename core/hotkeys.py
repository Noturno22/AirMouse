"""Keyboard/media shortcuts emitted by the gesture engine.

Extraído de ``main.py``: toda a emissão de teclas (media keys, atalhos,
Alt+Tab com hold persistente) vive aqui. pynput é importado em lazy-load
para não travar o arranque quando não há teclas a enviar.
"""
import time

from core.log import get_logger

log = get_logger("hotkeys")

VOLUME_STEP_PX = 8.0
ALT_HOLD_TIMEOUT_S = 1.3

_kb_ctl = None
_alt_held = set()


def _media_tap(key, times=1):
    global _kb_ctl
    try:
        if _kb_ctl is None:
            from pynput.keyboard import Controller as _KC

            _kb_ctl = _KC()
        for _ in range(max(1, min(times, 8))):
            _kb_ctl.press(key)
            _kb_ctl.release(key)
    except Exception as e:
        log.debug("Falha ao emitir tecla de m\u00eddia %s: %s", key, e)


def _keyboard_shortcut(combo):
    global _kb_ctl
    try:
        if _kb_ctl is None:
            from pynput.keyboard import Controller as _KC
            _kb_ctl = _KC()
        from pynput.keyboard import Key
        key_map = {
            "ctrl": Key.ctrl_l, "alt": Key.alt_l, "shift": Key.shift_l,
            "cmd": Key.cmd, "tab": Key.tab, "win": Key.cmd,
            "down": Key.down, "up": Key.up, "left": Key.left, "right": Key.right,
            "enter": Key.enter, "space": Key.space, "esc": Key.esc, "delete": Key.delete,
            "home": Key.home, "end": Key.end, "pageup": Key.page_up, "pagedown": Key.page_down,
            "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
            "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
            "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
        }
        parts = combo.lower().split("+")
        keys = [key_map[p.strip()] if p.strip() in key_map else p.strip() for p in parts]
        modifiers = {Key.ctrl_l, Key.ctrl_r, Key.alt_l, Key.alt_r,
                     Key.shift, Key.shift_l, Key.shift_r, Key.cmd, Key.cmd_l, Key.cmd_r}
        # Pressiona primeiro TODOS os modificadores e mantem-nos premidos,
        # depois dispara as teclas normais. Isto e essencial para atalhos do
        # Windows como Alt+Tab, que so abrem o alternador se o Alt for
        # segurado enquanto o Tab e enviado(a) com um pequeno intervalo.
        mod_keys = [k for k in keys if k in modifiers]
        normal_keys = [k for k in keys if k not in modifiers]
        for k in mod_keys:
            _kb_ctl.press(k)
        time.sleep(0.05)
        for k in normal_keys:
            _kb_ctl.press(k)
            time.sleep(0.03)
            _kb_ctl.release(k)
            time.sleep(0.03)
        for k in reversed(mod_keys):
            _kb_ctl.release(k)
    except Exception as e:
        log.debug("Falha ao emitir atalho %s: %s", combo, e)


def _alt_ensure():
    global _kb_ctl
    if _kb_ctl is None:
        from pynput.keyboard import Controller as _KC
        _kb_ctl = _KC()
    from pynput.keyboard import Key
    return _kb_ctl, Key


def _alt_tab_navigate(back=False):
    """Segura Alt (e Shift se back) e envia um Tab, mantendo o hold ativo.

    Se o hold ja estiver ligado apenas reenvia o Tab (navega mais um),
    ajustando o Shift conforme a direcao pretendida."""
    _ALT, _Key = _alt_ensure()
    try:
        from pynput.keyboard import Key
        if Key.alt_l not in _alt_held:
            _ALT.press(Key.alt_l)
            _alt_held.add(Key.alt_l)
        if back and Key.shift_l not in _alt_held:
            _ALT.press(Key.shift_l)
            _alt_held.add(Key.shift_l)
        elif not back and Key.shift_l in _alt_held:
            _ALT.release(Key.shift_l)
            _alt_held.discard(Key.shift_l)
        time.sleep(0.05)
        _ALT.press(Key.tab)
        time.sleep(0.04)
        _ALT.release(Key.tab)
    except Exception:
        _alt_release_all()


def _alt_release_all():
    global _alt_held
    try:
        _ALT, _ = _alt_ensure()
        for k in _alt_held:
            _ALT.release(k)
    except Exception as e:
        log.debug("Falha ao libertar Alt (hold): %s", e)
    _alt_held.clear()


def _alt_tab_quick(back=False):
    """Avança/retrocede UMA janela de forma rápida (Alt+Tab solto).

    Premir Alt, enviar Tab, e soltar tudo de imediato: o Windows passa para a
    janela seguinte/anterior sem abrir o alternador persistente. É a ação do
    swipe simples — troca rápida, tal como o utilizador pediu.
    """
    _ALT, _Key = _alt_ensure()
    try:
        mods = [_Key.alt_l]
        if back:
            mods.append(_Key.shift_l)
        for k in mods:
            _ALT.press(k)
        time.sleep(0.04)
        _ALT.press(_Key.tab)
        time.sleep(0.03)
        _ALT.release(_Key.tab)
        time.sleep(0.02)
        for k in reversed(mods):
            _ALT.release(k)
    except Exception:
        _alt_release_all()


def _handle_media_event(event, value):
    if event == "volume":
        presses = int(abs(value) / VOLUME_STEP_PX)
        if presses >= 1:
            from pynput.keyboard import Key

            _media_tap(
                Key.media_volume_up if value > 0 else Key.media_volume_down,
                presses,
            )
            return "VOL " + ("+" * min(presses, 4) if value > 0 else "-" * min(presses, 4))
        return None
    if event == "play_pause":
        from pynput.keyboard import Key

        _media_tap(Key.media_play_pause, 1)
        return "PLAY/PAUSA"
    return None
