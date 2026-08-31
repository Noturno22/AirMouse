"""AirMouse real-time engine.

Extraído de ``main.py``: contém o cérebro da lógica de reconhecimento,
movimento, eventos e comandos. ``main.py`` ficou apenas bootstrap (CLI + IO),
e ``ui.main_window.py`` consume o mesmo motor para paridade total entre o
preview OpenCV e a janela PySide6.
"""
import math
import time
from types import SimpleNamespace

import cv2

from config import SMOOTH_PRESETS, save_settings
from core.commands import _click_assist, apply_command
from core.filters import AccelCurve, FilterPair2D
from core.gestures import Gesture
from core.hotkeys import (
    _alt_release_all,
    _alt_tab_navigate,
    _alt_tab_quick,
    _handle_media_event,
    _keyboard_shortcut,
)
from core.light import LightBoost
from core.log import get_logger
from core.motion import SmoothEmitter, lead_offset
from core.overlay import draw_overlay
from core.twohand import (
    BrightnessCtl,
    ClapDetector,
    FistCycleDetector,
    HandPool,
    LeftHandDetector,
    WaveDetector,
)

log = get_logger("engine")

MOVE_GESTURES = frozenset({Gesture.OPEN, Gesture.ONE, Gesture.PINCH})
ALT_HOLD_TIMEOUT_S = 1.3


def make_engine_ctx(cfg, smooth_idx, gesture_ai, tuner, ctx):
    """Constrói o contexto de motores/estado partilhado entre UIs.

    Toda a lógica de reconhecimento/movimento vive aqui (intacta). Tanto o
    preview OpenCV como a MainWindow PySide6 consomem o MESMO contexto, para
    garantir paridade total de comportamento.
    """
    pool = HandPool(cfg, gesture_ai)
    filters = FilterPair2D(cfg.filter_min_cutoff, cfg.filter_beta)
    curve = AccelCurve(cfg.accel_min_gain, cfg.accel_max_gain,
                       cfg.accel_ref_speed, cfg.accel_expo)
    emitter = None

    clap = ClapDetector() if cfg.clap_enabled else None
    magnifier = ctx.magnifier
    brightness = BrightnessCtl(step=cfg.brightness_step)
    fist_cycle = FistCycleDetector(
        cycles_needed=cfg.fist_cycle_count, window_s=cfg.fist_cycle_window_s,
    )
    wave = WaveDetector(
        min_reversals=cfg.wave_min_reversals, window_s=cfg.wave_window_s,
        min_amplitude_px=cfg.wave_min_amplitude_px,
    )
    left_hand = LeftHandDetector(cfg) if cfg.left_hand_commands else None
    light = LightBoost() if cfg.low_light_boost else None
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    ui = {
        "ai_on": gesture_ai is not None,
        "ai_conf": 0.0,
        "voice": "off",
        "toast": "",
        "toast_until": 0.0,
        "autotune": tuner.enabled,
        "magnify": "",
        "hands": 0,
        "light": False,
        "tts": "",
        "ui_show": False,
    }

    def toast(text):
        ui["toast"] = text
        ui["toast_until"] = time.monotonic() + 1.3

    return SimpleNamespace(
        pool=pool, filters=filters, curve=curve, emitter=emitter,
        clap=clap, magnifier=magnifier, brightness=brightness,
        fist_cycle=fist_cycle, wave=wave,
        left_hand=left_hand, light=light, clahe=clahe, ui=ui, toast=toast,
        smooth_name=(SMOOTH_PRESETS[smooth_idx][0] if smooth_idx >= 0 else "CUSTOM"),
        last_palm=None, prev_filtered=None, jump_streak=0, fast_until=0.0,
        alt_hold=False, alt_hold_until=0.0, alt_tab_until=0.0,
        switcher_pick=False,
        glitches=0, last_seq=-1, last_scroll=None, fps=0.0, infer_total=0.0,
        frames_done=0, warmup_left=max(cfg.warmup_frames, 0), started=None,
        window="AirMouse",
        # Com o ecrã espelhado (mirror=True), o lado esquerdo do ecrã corresponde
        # à mão "Right" do MediaPipe (e vice-versa). A mão de comandos é a que o
        # utilizador vê à ESQUERDA; a do cursor a que vê à DIREITA.
        command_side="Left" if not cfg.mirror else "Right",
        cursor_side="Right" if not cfg.mirror else "Left",
        active_side=("Right" if not cfg.mirror else "Left"),
        last_accept_t=None, last_hand_t=None, dt_ema=0.05,
        exposure_tried=False, gray_check=0,
        left_peace_prev=False, right_peace_prev=False, cmd_fist_prev=False,
    )


def process_frame(cfg, cam, tracker, mouse, gesture_ai, voice, tuner, ctx, state, E):
    """Processa UMA iteracao de câmara/gestos e devolve um snapshot.

    Esta função contém TODO o cérebro da lógica (movimento, eventos,
    left_hand, punho, brilho, clap, wave, voz, autotune...). É partilhada
    pelo preview OpenCV e pela MainWindow PySide6 para paridade total.
    """
    loop_start = time.perf_counter()
    frame, seq = cam.read()
    if frame is None:
        return {"frame": None, "done": False, "to_render": False}

    if E.warmup_left > 0:
        E.warmup_left -= 1
        return {"frame": frame, "all_frames": {}, "active_side": E.active_side,
                "last_scroll": E.last_scroll, "fps": E.fps, "ui": E.ui,
                "done": False, "to_render": False}

    if seq == E.last_seq:
        return {"frame": None, "done": False, "to_render": False}
    E.last_seq = seq

    if cfg.mirror:
        frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    E.gray_check += 1
    if E.light is not None and E.gray_check % E.light.check_every == 0:
        gmean = float(cv2.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))[0])
        evt = E.light.feed(gmean)
        if evt == "on":
            E.toast("LUZ BAIXA: realce ativado")
            if not E.exposure_tried:
                E.exposure_tried = True
                cam.try_boost_exposure()
        elif evt == "off":
            E.toast("LUZ NORMAL")
    if E.light is not None and E.light.active:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lch, ach, bch = cv2.split(lab)
        lch = E.clahe.apply(lch)
        frame = cv2.cvtColor(cv2.merge((lch, ach, bch)), cv2.COLOR_LAB2BGR)

    ts_ms = time.monotonic_ns() // 1_000_000
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    t_infer = time.perf_counter()
    hands, sides = tracker.process(rgb, ts_ms)
    E.infer_total += (time.perf_counter() - t_infer) * 1000.0

    results = E.pool.update(hands, sides, w, h)
    now = time.perf_counter()

    event = None
    ev_value = None
    hand_frame = None

    if results:
        if E.active_side in results:
            hand_frame, event, ev_value = results[E.active_side]
        else:
            prev_active = E.active_side
            E.active_side = E.cursor_side if E.cursor_side in results else next(iter(results))
            hand_frame, event, ev_value = results[E.active_side]
            if prev_active is not None:
                E.filters.reset()
                E.last_palm = None
                E.prev_filtered = None
                E.jump_streak = 0
                E.fast_until = 0.0
                E.emitter.clear()

    all_frames = {s: r[0] for s, r in results.items()}
    E.ui["hands"] = len(results)

    # Liberta o Alt+Tab seguro por timeout (mesmo que a mao desapareca).
    if E.alt_hold and now > E.alt_hold_until:
        _alt_release_all()
        E.alt_hold = False
        E.switcher_pick = False
        E.toast("ALT+TAB")

    if E.clap is not None and len(results) == 2 and not state["paused"]:
        palms = [r[0].palm_center for r in results.values()]
        scales = [r[0].hand_scale_px for r in results.values()]
        if E.clap.update(palms, scales, now):
            note = ctx.assistant.toggle() if ctx.assistant else "ASSISTENTE OFF"
            E.toast(note)
            if ctx.speaker:
                ctx.speaker.say(note)

    # Comandos da mao esquerda:
    #   * SWIPE esq/dir   -> troca RÁPIDA: avança/retrocede uma janela e solta
    #     (Alt+Tab rápido) — o utilizador só deslizou, quer ir já para a seguinte.
    #   * Segurar a mão ABERTA ~2s -> abrir o alternador de janelas (pick mode);
    #     enquanto estiver aberto, os swipes navegam sem soltar o Alt e soltar a
    #     mão confirma a escolha.
    #   * Abrir/fechar 3x -> mostra/oculta a interface GUI.
    if E.left_hand is not None and not state["paused"]:
        lhf = results[E.command_side][0] if E.command_side in results else None
        lpalm = lhf.palm_center if lhf is not None else None
        lgesture = lhf.gesture if lhf is not None else None
        left_cmd, left_cmd_val = E.left_hand.update(lpalm, now, lgesture)

        # Pick mode: manter o Alt segurado enquanto a mao continua aberta;
        # quando deixar de estar aberta (ou desaparecer) confirma e solta.
        if E.switcher_pick:
            E.switcher_pick = lhf is not None and lgesture == Gesture.OPEN
            if not E.switcher_pick:
                _alt_release_all()
                E.alt_hold = False
                E.toast("ALTERNADOR FECHADO")
            else:
                E.alt_hold = True
                E.alt_hold_until = now + ALT_HOLD_TIMEOUT_S

        if left_cmd == "gui_toggle":
            E.ui["ui_show"] = not E.ui["ui_show"]
            E.toast("INTERFACE ON" if E.ui["ui_show"] else "INTERFACE OFF")
        elif left_cmd == "alt_switch_open":
            # Abre o alternador (Alt segurado) para o utilizador escolher.
            _alt_tab_navigate(back=False)
            E.switcher_pick = True
            E.alt_hold = True
            E.alt_hold_until = now + ALT_HOLD_TIMEOUT_S
            E.toast("ESCOLHER JANELA")
        elif left_cmd == "alt_tab_forward":
            if E.switcher_pick:
                _alt_tab_navigate(back=False)
                E.alt_hold_until = now + ALT_HOLD_TIMEOUT_S
            else:
                _alt_tab_quick(back=False)
            E.toast("ALT+TAB")
        elif left_cmd == "alt_tab_back":
            if E.switcher_pick:
                _alt_tab_navigate(back=True)
                E.alt_hold_until = now + ALT_HOLD_TIMEOUT_S
            else:
                _alt_tab_quick(back=True)
            E.toast("ALT+SHIFT+TAB")
        # Soltar a mao esquerda = confirma e liberta o Alt segurado.
        if lpalm is None and E.alt_hold:
            _alt_release_all()
            E.alt_hold = False
            E.switcher_pick = False

    # Fechar a mao de comandos (so ela presente) = fechar janela (Alt+F4)
    # O gesto de abrir/fechar a mao 3x (mostrar/ocultar interface) passa por
    # estados FIST transitorios; durante esse pump não deve fechar janelas,
    # caso contrário o Alt+F4 disparava no meio do gesto e fechava tudo.
    cmd_fist = (
        E.left_hand is not None
        and not state["paused"]
        and len(results) == 1
        and E.command_side in results
        and results[E.command_side][0].gesture == Gesture.FIST
        and now >= E.left_hand.pumping_until
    )
    if cmd_fist and not E.cmd_fist_prev:
        _keyboard_shortcut("alt+f4")
        E.toast("FECHAR JANELA (Alt+F4)")
    E.cmd_fist_prev = cmd_fist

    # Luminosidade com Dois Dedos (PEACE) na mao: esquerda diminui, direita aumenta.
    left_peace = False
    right_peace = False
    if len(results) == 2:
        if "Left" in results:
            left_peace = results["Left"][0].gesture == Gesture.PEACE
        if "Right" in results:
            right_peace = results["Right"][0].gesture == Gesture.PEACE
    if left_peace and not E.left_peace_prev:
        E.toast(E.brightness.decrease())
    if right_peace and not E.right_peace_prev:
        E.toast(E.brightness.increase())
    E.left_peace_prev = left_peace
    E.right_peace_prev = right_peace

    mag_note = None
    if E.magnifier is not None:
        if len(results) == 2:
            entries = [
                (r[0].gesture, r[0].palm_center, r[0].hand_scale_px)
                for r in results.values()
            ]
            mag_note = E.magnifier.update(entries, now)
        elif E.magnifier.on:
            mag_note = E.magnifier.update([], now)
    E.ui["magnify"] = E.magnifier.last_action if (E.magnifier and E.magnifier.on) else ""

    if mag_note:
        E.toast(mag_note)

    if hand_frame is not None and hand_frame.gesture != Gesture.NONE:
        palm = hand_frame.palm_center
        accept = True
        if E.last_palm is not None:
            d = math.hypot(palm[0] - E.last_palm[0], palm[1] - E.last_palm[1])
            limit = cfg.max_jump_frac * w
            if d <= limit:
                E.jump_streak = 0
                E.fast_until = 0.0
            elif now < E.fast_until:
                pass
            elif E.jump_streak < 2:
                E.jump_streak += 1
                E.glitches += 1
                accept = False
            else:
                E.jump_streak = 0
                E.fast_until = now + 0.5
        if accept:
            if E.last_accept_t is not None:
                inst_dt = now - E.last_accept_t
                E.dt_ema = E.dt_ema * 0.7 + min(max(inst_dt, 0.008), 0.2) * 0.3
            E.last_accept_t = now
            E.last_palm = palm
            E.last_hand_t = now
            fx, fy = E.filters.filter(*palm)
            if E.prev_filtered is None:
                E.prev_filtered = (fx, fy)
            dx = fx - E.prev_filtered[0]
            dy = fy - E.prev_filtered[1]
            E.prev_filtered = (fx, fy)

            gain = cfg.move_gain * E.curve.apply(E.filters.vx, E.filters.vy)
            sx = mouse.screen_w / w
            sy = mouse.screen_h / h
            mdx = dx * gain * sx
            mdy = dy * gain * sy
            movable = (
                not state["paused"]
                and now >= state["freeze_until"]
                and hand_frame.gesture in MOVE_GESTURES
                and not (E.magnifier is not None and E.magnifier.on)
                and not (
                    E.left_hand is not None
                    and E.active_side == E.command_side
                )
            )
            if movable and abs(mdx) < cfg.deadzone_px:
                mdx = 0.0
            if movable and abs(mdy) < cfg.deadzone_px:
                mdy = 0.0
            if movable:
                vspeed_cap = E.curve.ref_speed * 4.0 * cfg.move_gain
                vxs = mdx / E.dt_ema if E.dt_ema > 0 else 0.0
                vys = mdy / E.dt_ema if E.dt_ema > 0 else 0.0
                sp = math.hypot(vxs, vys)
                if sp > vspeed_cap and sp > 0:
                    k = vspeed_cap / sp
                    vxs *= k
                    vys *= k
                lx, ly = lead_offset(vxs, vys, cfg.predict_ms)
                try:
                    cx, cy = mouse.mouse.position
                    pxl, pyl = ctx.snap.pull((cx, cy), now) if ctx.snap else (0.0, 0.0)
                except Exception:
                    pxl = pyl = 0.0
                E.emitter.push(mdx + lx + pxl, mdy + ly + pyl, E.dt_ema)
            tuner.feed(True, E.filters, mdx, mdy)
    else:
        if hand_frame is None:
            E.active_side = None
        E.filters.reset()
        E.last_palm = None
        E.prev_filtered = None
        E.jump_streak = 0
        E.fast_until = 0.0
        E.last_accept_t = None
        E.emitter.clear()
        tuner.feed(False, E.filters, 0.0, 0.0)
        if state["button_down"] and (
            E.last_hand_t is None or now - E.last_hand_t > cfg.click_release_grace_s
        ):
            mouse.release_left()
            state["button_down"] = False
    if E.left_hand is not None and E.active_side == E.command_side:
        event = None

    if event and (not state["paused"] or event == "left_up"):
        if event == "left_down":
            _click_assist(ctx, state, mouse, cfg)
            mouse.press_left()
            state["button_down"] = True
            state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
            state["flash"] = 5
            E.emitter.clear()
        elif event == "left_up":
            mouse.release_left()
            state["button_down"] = False
            E.emitter.clear()
        elif event == "right_click":
            _click_assist(ctx, state, mouse, cfg)
            mouse.right_click()
            state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
            state["flash"] = 5
            E.emitter.clear()
        elif event == "copy":
            _keyboard_shortcut("ctrl+c")
            E.toast("COPIAR (Ctrl+C)")
            state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
            state["flash"] = 5
        elif event == "paste":
            _keyboard_shortcut("ctrl+v")
            E.toast("COLAR (Ctrl+V)")
            state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
            state["flash"] = 5
        elif event == "scroll" and ev_value is not None:
            mouse.scroll(ev_value * cfg.scroll_gain_factor)
        else:
            media_note = _handle_media_event(event, ev_value)
            if media_note:
                E.toast(media_note)

    if event == "scroll" and ev_value is not None:
        E.last_scroll = ev_value
    elif hand_frame is None or hand_frame.gesture != Gesture.FIST:
        E.last_scroll = None

    if (hand_frame is not None
            and hand_frame.gesture not in (Gesture.NONE, Gesture.PEACE, Gesture.THREE)
            and not state["paused"]):
        if E.fist_cycle.update(hand_frame.gesture, now):
            _keyboard_shortcut("win+d")
            E.toast("WIN+D")
        if hand_frame.gesture == Gesture.OPEN:
            if E.wave.update(hand_frame.palm_center[0], now):
                _keyboard_shortcut("win+down")
                E.toast("BYE BYE")

    tune_note = tuner.maybe_apply(time.monotonic(), E.filters, cfg)
    if tune_note:
        E.toast(tune_note)
        state["smooth_name"] = "AUTO"

    while True:
        try:
            cmd = voice.cmd_queue.get_nowait() if voice else None
        except Exception:
            cmd = None
        if cmd is None:
            break
        action = cmd.get("action")
        note = apply_command(action, cmd.get("value"), cfg, mouse, state, ctx)
        if note:
            log.info("voz %r -> %s", cmd.get("text", ""), note)
            E.toast(note)
            if ctx.speaker:
                ctx.speaker.say(note)
        if ctx.exit_requested:
            break

    dt = time.perf_counter() - loop_start
    inst = 1.0 / dt if dt > 0 else 0.0
    E.fps = inst if E.frames_done == 0 else E.fps * 0.9 + inst * 0.1
    if E.started is None:
        E.started = loop_start
    E.frames_done += 1

    E.ui["ai_conf"] = hand_frame.ai_conf if hand_frame is not None else 0.0
    if state.get("pinch_debug") and hand_frame is not None and now > state["dbg_until"]:
        state["dbg_until"] = now + 0.25
        log.info(
            "pincha idx=%.2f mid=%.2f lim=%.2f -> %s",
            hand_frame.pinch_ratio, hand_frame.pinch_mid_ratio,
            cfg.pinch_on_ratio, hand_frame.gesture.name,
        )
    if voice:
        st = voice.status
        E.ui["voice"] = {"off": "off", "wake": "wake",
                         "listening": "listening"}.get(st, st)
    else:
        E.ui["voice"] = "off"
    E.ui["autotune"] = tuner.enabled
    E.ui["light"] = E.light.active if E.light else False
    if ctx.speaker:
        E.ui["tts"] = ctx.speaker.status

    if state["flash"] > 0:
        state["flash"] -= 1

    if cfg.selftest_frames and E.frames_done >= cfg.selftest_frames:
        elapsed = time.perf_counter() - E.started
        avg_fps = E.frames_done / elapsed if elapsed > 0 else 0.0
        avg_infer = E.infer_total / E.frames_done if E.frames_done else 0.0
        tts_name = ctx.speaker.status if ctx.speaker else "-"
        snap_st = ctx.snap.status if ctx.snap else "-"
        log.info(
            "selftest %d frames | %.1f fps | inferencia %.1f ms | glitches %d"
            " | tts=%s | snap=%s",
            E.frames_done, avg_fps, avg_infer, E.glitches, tts_name, snap_st,
        )
        return {"frame": frame, "all_frames": all_frames, "active_side": E.active_side,
                "last_scroll": E.last_scroll, "fps": E.fps, "ui": E.ui,
                "done": True, "to_render": True}

    return {"frame": frame, "all_frames": all_frames, "active_side": E.active_side,
            "last_scroll": E.last_scroll, "fps": E.fps, "ui": E.ui, "flash": state["flash"],
            "done": False, "to_render": True}


def run_loop(cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice, tuner, ctx, state):
    E = make_engine_ctx(cfg, smooth_idx, gesture_ai, tuner, ctx)
    E.emitter = SmoothEmitter(mouse, cfg.emitter_rate_hz)
    E.emitter.start()
    state["smooth_name"] = E.smooth_name
    state.setdefault("paused", False)
    state.setdefault("show_help", False)
    state.setdefault("flash", 0)
    state.setdefault("freeze_until", 0.0)
    state.setdefault("button_down", False)
    state["filters"] = E.filters
    state["tuner"] = tuner
    state["emitter"] = E.emitter

    try:
        if cfg.preview:
            cv2.namedWindow(E.window, cv2.WINDOW_NORMAL)

        while True:
            snap = process_frame(cfg, cam, tracker, mouse, gesture_ai, voice, tuner, ctx, state, E)
            if snap["done"]:
                break
            if not snap["to_render"] or snap["frame"] is None:
                if ctx.exit_requested:
                    break
                continue
            frame = snap["frame"]
            all_frames = snap["all_frames"]
            active_side = snap["active_side"]
            fps = snap["fps"]
            ui = snap["ui"]

            if cfg.preview:
                draw_overlay(
                    frame, all_frames, active_side, E.last_scroll, fps, cfg,
                    state["smooth_name"], state["paused"], state["show_help"],
                    state["flash"], ui,
                )
                cv2.imshow(E.window, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord(" "):
                    note = apply_command("pause_toggle", None, cfg, mouse, state, ctx)
                    if note:
                        E.toast(note)
                elif key == ord("["):
                    cfg.move_gain = max(0.6, round(cfg.move_gain - 0.2, 2))
                    tuner.set_user_gain(cfg.move_gain)
                elif key == ord("]"):
                    cfg.move_gain = max(0.6, round(cfg.move_gain + 0.2, 2))
                    tuner.set_user_gain(cfg.move_gain)
                elif key in (ord(","), ord(".")):
                    step = -1 if key == ord(",") else 1
                    cur = next(
                        (i for i, p in enumerate(SMOOTH_PRESETS) if p[0] == state["smooth_name"]),
                        1,
                    )
                    idx = (cur + step) % len(SMOOTH_PRESETS)
                    _, cut, beta = SMOOTH_PRESETS[idx]
                    cfg.filter_min_cutoff = cut
                    cfg.filter_beta = beta
                    E.filters.set_params(cut, beta)
                    state["smooth_name"] = SMOOTH_PRESETS[idx][0]
                elif key == ord("s"):
                    save_settings(cfg, state["smooth_name"])
                elif key == ord("h"):
                    state["show_help"] = not state["show_help"]
                elif key == ord("v"):
                    if voice is not None:
                        voice.toggle()
                elif key == ord("a"):
                    E.toast(tuner.toggle())
                elif key == ord("m"):
                    if ctx.snap is not None and ctx.snap.available:
                        cfg.snap_enabled = ctx.snap.enabled
                        note = apply_command("snap_toggle", None, cfg, mouse, state, ctx)
                        E.toast(str(note))
                elif key == ord("b"):
                    note = apply_command("assistant", None, cfg, mouse, state, ctx)
                    E.toast(str(note))
                    if ctx.speaker:
                        ctx.speaker.say(str(note))

            if ctx.exit_requested:
                break
    finally:
        E.emitter.stop()
        if state["button_down"]:
            mouse.release_left()
            state["button_down"] = False

    return state
