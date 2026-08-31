"""Application-level commands for the gesture engine.

Extraído de ``main.py``: ``apply_command`` traduz ações (gesto/voz/hotkey)
em efeitos no sistema (cliques, ganho, suavidade, snap, assistente, ...).
"""
import time
from typing import Any

from config import SMOOTH_PRESETS, save_settings


class AppCtl:
    """Contexto de serviços partilhado entre UIs e o motor de gestos."""

    def __init__(self):
        self.exit_requested = False
        self.speaker: Any = None
        self.snap: Any = None
        self.assistant: Any = None
        self.magnifier: Any = None


def _release_if_dragging(state, mouse):
    if state.get("button_down"):
        mouse.release_left()
        state["button_down"] = False


def _click_assist(ctx, state, mouse, cfg):
    if ctx.snap is None or not cfg.snap_click_assist or not ctx.snap.enabled:
        return
    try:
        cur = mouse.mouse.position
        target = ctx.snap.assist_point(cur, time.perf_counter())
        if target is not None:
            mouse.mouse.position = (int(target[0]), int(target[1]))
            state["assist_used"] = True
    except Exception:
        pass


def apply_command(action, value, cfg, mouse, state, ctx):
    now = time.monotonic()
    if action == "exit":
        ctx.exit_requested = True
        return "SAIR"
    if action == "pause":
        state["paused"] = True
        _release_if_dragging(state, mouse)
        state["emitter"].clear()
        return "PAUSA"
    if action == "resume":
        state["paused"] = False
        return "RETOMAR"
    if action == "pause_toggle":
        return apply_command(
            "resume" if state["paused"] else "pause",
            value, cfg, mouse, state, ctx,
        )
    if action == "help":
        state["show_help"] = not state["show_help"]
        return "AJUDA"
    if action == "save":
        save_settings(cfg, state["smooth_name"])
        return "GRAVAR"
    if action == "gain_up":
        cfg.move_gain = max(0.6, round(cfg.move_gain + 0.2, 2))
        state["tuner"].set_user_gain(cfg.move_gain)
        return f"GANHO {cfg.move_gain:.1f}"
    if action == "gain_down":
        cfg.move_gain = max(0.6, round(cfg.move_gain - 0.2, 2))
        state["tuner"].set_user_gain(cfg.move_gain)
        return f"GANHO {cfg.move_gain:.1f}"
    preset_map = {
        "smooth_suave": 0,
        "smooth_normal": 1,
        "smooth_reactivo": 2,
    }
    if action in preset_map:
        idx = preset_map[action]
        _, cut, beta = SMOOTH_PRESETS[idx]
        cfg.filter_min_cutoff = cut
        cfg.filter_beta = beta
        state["filters"].set_params(cut, beta)
        state["smooth_name"] = SMOOTH_PRESETS[idx][0]
        return SMOOTH_PRESETS[idx][0]
    if action == "assistant":
        if ctx.assistant is None:
            return "ASSISTENTE INDISPONIVEL"
        return ctx.assistant.toggle()
    if action == "assistant_close":
        if ctx.assistant is None:
            return "ASSISTENTE INDISPONIVEL"
        n = ctx.assistant.close()
        return "FECHAR ASSISTENTE" if n else "NAO ESTA ABERTO"
    if action == "magnify_on":
        if ctx.magnifier is None:
            return "LUPA INDISPONIVEL"
        return ctx.magnifier.force_on()
    if action == "magnify_off":
        if ctx.magnifier is None:
            return "LUPA INDISPONIVEL"
        return ctx.magnifier.force_off()
    if action == "snap_toggle":
        if ctx.snap is None or not ctx.snap.available:
            return "SNAP INDISPONIVEL"
        cfg.snap_enabled = ctx.snap.enabled
        return f"SNAP {ctx.snap.status}"
    if action == "left_click":
        if state["paused"] or state.get("button_down"):
            return None
        _click_assist(ctx, state, mouse, cfg)
        mouse.press_left()
        time.sleep(0.03)
        mouse.release_left()
        state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
        state["flash"] = 5
        return "CLIQUE ESQ"
    if action == "right_click":
        if state["paused"] or state.get("button_down"):
            return None
        _click_assist(ctx, state, mouse, cfg)
        mouse.right_click()
        state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
        state["flash"] = 5
        return "CLIQUE DIR"
    if action in ("scroll_up", "scroll_down"):
        if state["paused"]:
            return None
        amount = value if isinstance(value, (int, float)) and abs(value) >= 1 else 3
        mouse.scroll(amount if action == "scroll_up" else -amount)
        return "SCROLL +" if action == "scroll_up" else "SCROLL -"
    if action == "autotune_toggle":
        return state["tuner"].toggle()
    return None
