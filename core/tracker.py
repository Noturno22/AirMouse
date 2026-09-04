import os
import urllib.request

import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

from core.log import get_logger

log = get_logger("tracker")

HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)


def ensure_model(path, url, timeout_s=15.0):
    if os.path.isfile(path):
        return path
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + ".part"
    print(f"A baixar modelo MediaPipe para {path} ...")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            with open(tmp, "wb") as fh:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError as e:
            log.debug("N\u00e3o foi poss\u00edvel limpar ficheiro tempor\u00e1rio %s: %s", tmp, e)
        raise
    print("Modelo pronto.")
    return path


class HandTracker:
    def __init__(self, model_path, num_hands=1, use_gpu=False, num_threads=-1):
        self._landmarker = None
        num_hands = max(1, min(int(num_hands), 2))
        if use_gpu:
            try:
                base = mp_tasks.BaseOptions(
                    model_asset_path=model_path,
                    delegate=mp_tasks.BaseOptions.Delegate.GPU,
                )
                self._landmarker = self._build(base, num_hands)
                print("Tracker: delegado GPU ativo.")
            except Exception as exc:
                print(f"Aviso: GPU indisponivel ({exc.__class__.__name__}); a usar CPU.")
        if self._landmarker is None:
            base = mp_tasks.BaseOptions(model_asset_path=model_path)
            self._landmarker = self._build(base, num_hands)

    @staticmethod
    def _build(base_options, num_hands):
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        return vision.HandLandmarker.create_from_options(options)

    def process(self, rgb_frame, timestamp_ms):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        hands = []
        sides = []
        for lm_list, handed in zip(
            result.hand_landmarks, result.handedness or (), strict=True
        ):
            hands.append([(lm.x, lm.y, lm.z) for lm in lm_list])
            label = "Right"
            if handed:
                label = handed[0].category_name if handed[0].category_name in (
                    "Left",
                    "Right",
                ) else "Right"
            sides.append(label)
        return hands, sides

    def close(self):
        self._landmarker.close()
