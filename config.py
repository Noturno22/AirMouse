from dataclasses import dataclass


@dataclass
class Config:
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    mirror: bool = True

    move_gain: float = 2.0
    deadzone_px: float = 1.0

    filter_min_cutoff: float = 1.4
    filter_beta: float = 0.028

    accel_min_gain: float = 1.2
    accel_max_gain: float = 3.0
    accel_ref_speed: float = 1400.0
    accel_expo: float = 1.7

    predict_ms: float = 0.0
    emitter_rate_hz: float = 180.0

    snap_enabled: bool = False
    snap_radius_px: float = 46.0
    snap_strength: float = 0.35
    snap_click_assist: bool = False
    snap_poll_hz: float = 4.0

    num_hands: int = 2
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

    click_freeze_ms: int = 100
    gesture_stable_frames: int = 2
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
    selftest_frames: int = 0
