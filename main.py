"""AirMouse — bootstrap/CLI.

Extraído para ``core/`` todo o motor (``core.engine``), hotkeys
(``core.hotkeys``), comandos (``core.commands``) e renderização do preview
(``core.overlay``). Este módulo fica responsável apenas por:
  * parsing de CLI e single-instance
  * abrir câmara/modelos/serviços (snap, voz, TTS, bandeja, assistente)
  * escolher o UI (janela nativa PySide6 vs preview OpenCV) e arrancar o loop

`main` continua a re-exportar ``process_frame``/``make_engine_ctx``/``AppCtl``
para scripts/ferramentas que os importam daqui, por retrocompatibilidade.
"""
import argparse
import ctypes
import logging
import os
import sys

import cv2

from config import SETTINGS_FILE, SMOOTH_PRESETS, Config, load_settings, save_settings
from core.assistant import Assistant3D
from core.autotune import AutoTuner
from core.camera import CameraStream
from core.commands import AppCtl, apply_command
from core.engine import run_loop
from core.gesture_ai import GestureAI, ensure_ai_model
from core.log import get_logger, setup_logging
from core.mouse_ctl import MouseCtl
from core.snap import SnapEngine
from core.tracker import HandTracker, ensure_model
from core.tray import TrayAppAdapter, TrayIcon
from core.tts import Speaker
from core.twohand import MagnifierCtl
from core.voice import VoiceEngine

log = get_logger("cli")


def parse_args():
    parser = argparse.ArgumentParser(description="AirMouse - controla o rato com a mao")
    parser.add_argument("--camera", type=int, default=None)
    parser.add_argument("--gain", type=float, default=None)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--preview", action="store_true", help="forca janela mesmo em modo bandeja")
    parser.add_argument("--gpu", action="store_true", help="tenta usar delegado GPU no tracker")
    parser.add_argument("--tray", action="store_true", help="modo bandeja: invisivel com icone na bandeja")
    parser.add_argument("--no-gui", action="store_true",
                        help="usa o preview OpenCV em vez da janela PySide6")
    parser.add_argument("--reset-config", action="store_true", help="apaga settings.json")
    parser.add_argument("--no-voice", action="store_true", help="desativa comandos de voz")
    parser.add_argument("--no-ai", action="store_true", help="desativa classificador IA de gestos")
    parser.add_argument("--no-autotune", action="store_true", help="desativa auto-afinacao")
    parser.add_argument("--pinch-debug", action="store_true", help="imprime racios de pinca no console")
    parser.add_argument("--voice-always", action="store_true", help="voz sempre ativa (sem wake word)")
    parser.add_argument("--no-tts", action="store_true", help="sem voz falada do Jarvis")
    parser.add_argument("--whisper-model", type=str, default=None,
                        help="modelo Whisper (tiny/base/small; default small)")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING"],
                        help="nivel de log (default: INFO)")
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="processa apenas N frames e sai (modo de teste)",
    )
    return parser.parse_args()


def acquire_single_instance():
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, False, "AirMouse_JARVIS_v3")
        err = ctypes.get_last_error()
        if not handle or err == 183:
            return None
        return handle
    except Exception:
        return object()


def open_camera(cfg):
    candidates = [cfg.camera_index] if cfg.camera_index is not None else [0, 1, 2]
    for index in candidates:
        cam = CameraStream(index)
        if cam.open(cfg.frame_width, cfg.frame_height, 30):
            log.info("Camera %d ativa.", index)
            return cam
        cam.release()
    return None


def resolve_assistant(cfg):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_dir = cfg.assistant_dir or base_dir
    if os.path.isfile(os.path.join(server_dir, "server.py")):
        return Assistant3D(
            server_dir,
            cfg.assistant_url,
            window_hint=cfg.assistant_title,
            port=cfg.assistant_port,
        )
    log.warning("barehands (server.py) nao encontrado; assistente 3D desativado.")
    return None


def run_gui(cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice, tuner, speaker,
            snap, assistant, magnifier, ctx, state, tray_icon):
    """Arranca a janela nativa PySide6 (MainWindow) como interface principal.

    A MainWindow apresenta o feed com o esqueleto e overlays; a lógica de
    reconhecimento/movimento vive em ``process_frame`` (partilhada com o
    preview OpenCV), garantindo paridade total de comportamento.
    """
    try:
        from PySide6.QtWidgets import QApplication

        from ui.main_window import MainWindow
    except Exception as exc:
        log.warning("PySide6 indisponivel (%s); a usar preview OpenCV.", exc)
        cfg.gui_enabled = False
        return None

    app = QApplication.instance() or QApplication([])
    window = MainWindow(
        cfg, cam, tracker, mouse, gesture_ai=gesture_ai, voice=voice,
        tuner=tuner, speaker=speaker, snap=snap,
        assistant=assistant, magnifier=magnifier,
    )
    window.setWindowTitle("AirMouse")
    window.resize(900, 640)
    # Arranca OCULTA: a interface so aparece com o comando gui_toggle
    # (abrir/fechar a mao esquerda 3x). Serve apenas para configuracao.
    window.hide()

    # Ctrl+C na consola fecha a janela de forma limpa (sem interromper o
    # MediaPipe no meio do processamento nem deixar tracebacks repetidos).
    try:
        import signal as _sig

        from PySide6.QtCore import QTimer as _QTimer

        def _on_sigint(signum, frame):
            _QTimer.singleShot(0, window.close)

        _sig.signal(_sig.SIGINT, _on_sigint)
    except Exception:
        pass

    app.exec()
    window.close()
    return window


def main():
    args = parse_args()
    setup_logging(level=getattr(logging, args.log_level, logging.INFO))
    cfg = Config()
    cfg.selftest_frames = args.frames

    mutex = acquire_single_instance()
    if mutex is None:
        log.info("AirMouse ja esta em execucao.")
        return 1

    if args.reset_config:
        try:
            if os.path.isfile(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
                log.info("Definicoes apagadas.")
        except Exception:
            pass
    smooth_idx = load_settings(cfg)

    if args.camera is not None:
        cfg.camera_index = args.camera
    if args.gain is not None:
        cfg.move_gain = args.gain
    if args.tray:
        cfg.preview = bool(args.preview) and not args.no_preview
    else:
        if args.no_preview:
            cfg.preview = False
    if args.no_voice:
        cfg.voice_enabled = False
    if args.no_autotune:
        cfg.autotune_enabled = False
    if args.voice_always:
        cfg.voice_always_on = True
    if args.no_tts:
        cfg.tts_enabled = False
    if args.whisper_model:
        cfg.whisper_model = args.whisper_model

    gesture_ai = None
    if cfg.ai_enabled and not args.no_ai:
        try:
            ai_path = ensure_ai_model(cfg.ai_model_path)
            gesture_ai = GestureAI(ai_path)
            log.info("IA de gestos ativa (confianca min %.2f).", cfg.ai_confidence_min)
        except FileNotFoundError as exc:
            log.warning("IA de gestos indisponivel (%s); a usar regras geometricas.", exc)

    model_path = ensure_model(cfg.model_path, cfg.model_url)

    cam = open_camera(cfg)
    if cam is None:
        log.error("ERRO: nenhuma camera encontrada.")
        return 1

    tracker = HandTracker(
        model_path, num_hands=cfg.num_hands,
        use_gpu=args.gpu, num_threads=cfg.tracker_threads,
    )
    mouse = MouseCtl()
    tuner = AutoTuner(cfg)

    speaker = None
    if cfg.tts_enabled:
        voice_files = (
            (cfg.piper_onnx_url, os.path.join(cfg.piper_model_dir, "pt_BR-faber-medium.onnx")),
            (cfg.piper_conf_url, os.path.join(cfg.piper_model_dir, "pt_BR-faber-medium.onnx.json")),
        )
        speaker = Speaker(enabled=True, model_dir=cfg.piper_model_dir,
                          voice_files=voice_files)
        speaker.start()

    snap = SnapEngine(radius_px=cfg.snap_radius_px, strength=cfg.snap_strength,
                      poll_hz=cfg.snap_poll_hz, enabled=cfg.snap_enabled)
    snap.start()

    assistant = resolve_assistant(cfg)
    magnifier = MagnifierCtl(cfg.magnifier_step_frac) if cfg.magnifier_enabled else None

    voice = None
    if cfg.voice_enabled:
        import queue as _queue

        voice = VoiceEngine(cfg, _queue.Queue())
        if speaker is not None:
            voice.set_speaker(speaker)
        voice.start()

    ctx = AppCtl()
    state = {
        "paused": False,
        "show_help": False,
        "flash": 0,
        "freeze_until": 0.0,
        "button_down": False,
        "pinch_debug": bool(getattr(args, "pinch_debug", False)),
        "dbg_until": 0.0,
    }
    tray_icon = None
    tray_adapter = None

    def tray_apply(action, value):
        note = apply_command(action, value, cfg, mouse, state, ctx)
        if note and not cfg.preview:
            if tray_icon:
                tray_icon.notify("AirMouse", note)
            log.info("[bandeja] %s", note)

    if args.tray:
        tray_adapter = TrayAppAdapter(state, cfg, voice, snap, tuner,
                                      assistant, tray_apply)
        tray_icon = TrayIcon(tray_adapter)
        if tray_icon.start():
            log.info("Icone na bandeja ativo.")

    ctx.speaker = speaker
    ctx.snap = snap
    ctx.assistant = assistant
    ctx.magnifier = magnifier

    smooth_label = SMOOTH_PRESETS[smooth_idx][0] if smooth_idx >= 0 else "CUSTOM"
    log.info("Ecra: %dx%d | ganho: %.1f | suavidade: %s",
             mouse.screen_w, mouse.screen_h, cfg.move_gain, smooth_label)
    log.info(
        "Gestos: mao aberta/1 dedo=mover | pinca index=clique/arrastar |"
        " punho=cima/baixo=scroll | pinca medio=clique dir |"
        " 3 dedos=cima/baixo=volume | polegar=play/pausa"
    )
    log.info(
        "Novo: mindinho=copy | polegar+mindinho=paste |"
        " dois dedos esq/dir (2 maos)=brilho | fechar/abrir punho x2=Ctrl+D |"
        " bye bye=Ctrl+E | 3 palmas=Alt+Tab | lupa | snap"
    )
    log.info(
        "Teclas: [ ] ganho | , . suavidade | a auto-afinacao | v voz |"
        " s gravar | h ajuda | espaco pausa | Q sair"
    )

    exit_code = 0
    initial_params = (cfg.move_gain, cfg.filter_min_cutoff, cfg.filter_beta)
    use_gui = (not args.no_gui) and not (cfg.selftest_frames or args.frames)
    cfg.gui_enabled = use_gui
    try:
        if use_gui:
            run_gui(
                cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice,
                tuner, speaker, snap, assistant, magnifier, ctx, state,
                tray_icon,
            )
            if (
                (cfg.move_gain, cfg.filter_min_cutoff, cfg.filter_beta) != initial_params
            ) and tuner.enabled:
                save_settings(cfg, state.get("smooth_name", "NORMAL"))
        else:
            end_state = run_loop(
                cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice, tuner, ctx,
                state,
            )
            if (
                (cfg.move_gain, cfg.filter_min_cutoff, cfg.filter_beta) != initial_params
                or end_state.get("touched_settings")
            ) and tuner.enabled:
                save_settings(cfg, end_state["smooth_name"])
    except KeyboardInterrupt:
        log.info("Ate ja!")
    except Exception as exc:
        log.error("ERRO fatal: %s", exc)
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        if tray_icon is not None:
            tray_icon.stop()
        if voice is not None:
            voice.stop()
        if speaker is not None:
            speaker.stop()
        snap.stop()
        tracker.close()
        cam.release()
        cv2.destroyAllWindows()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
