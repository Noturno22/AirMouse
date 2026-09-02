import json
import os
from dataclasses import dataclass


@dataclass
class Config:
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    mirror: bool = True

    move_gain: float = 2.0
    deadzone_px: float = 1.0
    # Limiar de velocidade (px/s na câmara) abaixo do qual o cursor não mexe,
    # para eliminar tremor/deriva quando a mão está (quase) parada.
    still_velocity_px: float = 25.0

    filter_min_cutoff: float = 1.4
    filter_beta: float = 0.028

    accel_min_gain: float = 1.2
    accel_max_gain: float = 3.0
    accel_ref_speed: float = 1400.0
    accel_expo: float = 1.7

    # Antecipação do cursor (ms) na direção da mão. 0 = desativado.
    predict_ms: float = 0.0
    emitter_rate_hz: float = 180.0

    snap_enabled: bool = False
    snap_radius_px: float = 46.0
    snap_strength: float = 0.35
    snap_click_assist: bool = False
    snap_poll_hz: float = 4.0

    clap_enabled: bool = True
    magnifier_enabled: bool = True
    magnifier_step_frac: float = 0.85
    assistant_dir: str = ""
    assistant_url: str = "http://127.0.0.1:8794/stage.html"
    assistant_port: int = 8794
    assistant_title: str = "barehands"

    tts_enabled: bool = True
    piper_onnx_url: str = (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
    )
    piper_conf_url: str = (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
    )
    piper_model_dir: str = "models/piper"
    whisper_model: str = "small"
    low_light_boost: bool = False

    scroll_gain_factor: float = 0.06
    scroll_deadzone_px: float = 2.0
    volume_deadzone_px: float = 6.0
    volume_px_per_key: float = 16.0

    brightness_step: int = 10
    fist_cycle_count: int = 2
    fist_cycle_window_s: float = 2.5
    wave_min_reversals: int = 3
    wave_window_s: float = 1.5
    wave_min_amplitude_px: float = 15.0
    multi_clap_count: int = 3
    multi_clap_window_s: float = 2.5

    # Comandos especiais da MAO ESQUERDA (totalmente separada da direita)
    left_hand_commands: bool = True
    left_hand_swipe_min_px: float = 45.0
    left_hand_swipe_window_s: float = 0.5
    left_hand_cooldown_s: float = 1.1
    left_hand_scroll_deadzone_px: float = 18.0
    # Segurar a mao esquerda ABERTA durante este tempo (s) abre o alternador
    # de janelas (pick mode) em vez de apenas avancar uma janela de cada vez.
    left_hand_open_switch_s: float = 2.0

    click_freeze_ms: int = 100
    gesture_stable_frames: int = 2
    # Frames de confirmacao para a PINCA (clique). O Schmitt (on/off) ja filtra
    # ruido; reduzi-lo para 1 deixa o clique reagir na frame em que a pinça é
    # vista (menos latencia e taps rápidos que se perdiam).
    pinch_stable_frames: int = 1
    # Tempo maximo (s) para soltar o botao quando a mao some da câmara.
    click_release_grace_s: float = 0.12
    # Número de threads no tracker MediaPipe (CPU); -1 = auto.
    tracker_threads: int = -1
    warmup_frames: int = 10
    max_jump_frac: float = 0.35

    min_hand_scale_px: float = 55.0
    pinch_on_ratio: float = 0.42
    pinch_off_ratio: float = 0.58

    num_hands: int = 2
    hand_lock_radius_frac: float = 0.30
    hand_lost_grace_frames: int = 10

    model_path: str = "models/hand_landmarker.task"
    model_url: str = (
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/1/hand_landmarker.task"
    )

    ai_enabled: bool = True
    ai_confidence_min: float = 0.72
    ai_model_path: str = "models/gesture_mlp.npz"

    voice_enabled: bool = True
    voice_wake_word: str = "jarvis"
    voice_window_s: float = 8.0
    voice_always_on: bool = False
    vosk_model_url: str = (
        "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
    )
    vosk_model_path: str = "models/vosk-model-small-pt"

    llm_enabled: bool = True
    llm_model: str = "llama3.2:3b"
    llm_timeout_s: float = 2.5

    autotune_enabled: bool = True
    autotune_interval_s: float = 1.5
    filter_min_cutoff_min: float = 0.7
    filter_min_cutoff_max: float = 2.4
    filter_beta_min: float = 0.012
    filter_beta_max: float = 0.055
    gain_trim_frac: float = 0.2

    preview: bool = True
    gui_enabled: bool = True
    selftest_frames: int = 0

    # Licenciamento (preenchido em main.py; default = "free")
    license_tier: str = "free"


SMOOTH_PRESETS = (
    ("SUAVE", 0.9, 0.02),
    ("NORMAL", 1.4, 0.028),
    ("REACTIVO", 2.2, 0.05),
)
SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)


def load_settings(cfg):
    smooth_idx = 1
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        cfg.move_gain = max(float(data.get("move_gain", cfg.move_gain)), 0.6)
        cfg.snap_enabled = bool(data.get("snap_enabled", cfg.snap_enabled))
        if "mirror" in data:
            cfg.mirror = bool(data["mirror"])
        if "left_hand_commands" in data:
            cfg.left_hand_commands = bool(data["left_hand_commands"])
        if "low_light_boost" in data:
            cfg.low_light_boost = bool(data["low_light_boost"])
        if "deadzone_px" in data:
            cfg.deadzone_px = max(float(data["deadzone_px"]), 0.0)
        if "gesture_stable_frames" in data:
            cfg.gesture_stable_frames = max(int(data["gesture_stable_frames"]), 1)
        if "pinch_stable_frames" in data:
            cfg.pinch_stable_frames = max(int(data["pinch_stable_frames"]), 1)
        if "click_release_grace_s" in data:
            cfg.click_release_grace_s = max(float(data["click_release_grace_s"]), 0.03)
        if "tracker_threads" in data:
            cfg.tracker_threads = int(data["tracker_threads"])
        if "voice_enabled" in data:
            cfg.voice_enabled = bool(data["voice_enabled"])
        if "tts_enabled" in data:
            cfg.tts_enabled = bool(data["tts_enabled"])
        if "ai_enabled" in data:
            cfg.ai_enabled = bool(data["ai_enabled"])
        if "autotune_enabled" in data:
            cfg.autotune_enabled = bool(data["autotune_enabled"])
        name = str(data.get("suavidade", "")).upper()
        found = False
        for i, (pname, cut, beta) in enumerate(SMOOTH_PRESETS):
            if pname == name:
                cfg.filter_min_cutoff = cut
                cfg.filter_beta = beta
                smooth_idx = i
                found = True
        cut = data.get("filter_min_cutoff")
        beta = data.get("filter_beta")
        if isinstance(cut, (int, float)) and isinstance(beta, (int, float)):
            cfg.filter_min_cutoff = min(max(float(cut), 0.4), 3.0)
            cfg.filter_beta = min(max(float(beta), 0.008), 0.08)
            if not found:
                smooth_idx = -1
            else:
                _, pc, pb = SMOOTH_PRESETS[smooth_idx]
                if abs(pc - cfg.filter_min_cutoff) > 1e-6 or abs(pb - cfg.filter_beta) > 1e-6:
                    smooth_idx = -1
    except Exception:
        pass
    return smooth_idx


def save_settings(cfg, smooth_name):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "move_gain": round(cfg.move_gain, 2),
                    "suavidade": smooth_name,
                    "filter_min_cutoff": round(cfg.filter_min_cutoff, 3),
                    "filter_beta": round(cfg.filter_beta, 4),
                    "snap_enabled": bool(cfg.snap_enabled),
                    "mirror": bool(cfg.mirror),
                    "left_hand_commands": bool(cfg.left_hand_commands),
                    "low_light_boost": bool(cfg.low_light_boost),
                    "deadzone_px": round(cfg.deadzone_px, 1),
                    "gesture_stable_frames": int(cfg.gesture_stable_frames),
                    "pinch_stable_frames": max(int(cfg.pinch_stable_frames), 1),
                    "click_release_grace_s": round(float(cfg.click_release_grace_s), 3),
                    "tracker_threads": int(cfg.tracker_threads),
                    "voice_enabled": bool(cfg.voice_enabled),
                    "tts_enabled": bool(cfg.tts_enabled),
                    "ai_enabled": bool(cfg.ai_enabled),
                    "autotune_enabled": bool(cfg.autotune_enabled),
                },
                fh,
                indent=2,
            )
        print(f"Definicoes gravadas em {SETTINGS_FILE}")
    except Exception as exc:
        print(f"ERRO ao gravar definicoes: {exc}")
