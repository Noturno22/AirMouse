import threading
import time

import cv2


class CameraStream:
    def __init__(self, index):
        self.index = index
        self._cap = None
        self._lock = threading.Lock()
        self._frame = None
        self._seq = 0
        self._running = False
        self._thread = None

    def open(self, width=640, height=480, fps=30, timeout_s=2.0):
        cap = self._open_backend()
        if cap is None:
            return False
        self._cap = cap
        self._apply_config(cap, width, height, fps)
        if self._probe(cap, timeout_s):
            return self._start_thread()
        cap.release()
        self._cap = None
        cap = self._open_default()
        if cap is None:
            return False
        self._cap = cap
        if self._probe(cap, timeout_s):
            return self._start_thread()
        self.release()
        return False

    def _open_backend(self):
        if hasattr(cv2, "CAP_DSHOW"):
            cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            if cap.isOpened():
                return cap
            cap.release()
        return self._open_default()

    def _open_default(self):
        cap = cv2.VideoCapture(self.index)
        return cap if cap.isOpened() else None

    @staticmethod
    def _apply_config(cap, width, height, fps):
        try:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    def _probe(self, cap, timeout_s):
        deadline = time.perf_counter() + timeout_s
        while time.perf_counter() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None:
                with self._lock:
                    self._frame = frame
                    self._seq += 1
                return True
            time.sleep(0.02)
        return False

    def _start_thread(self):
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def _capture_loop(self):
        while self._running:
            cap = self._cap
            if cap is None:
                break
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.005)
                continue
            with self._lock:
                self._frame = frame
                self._seq += 1

    def read(self):
        with self._lock:
            return self._frame, self._seq

    def try_boost_exposure(self, value=-6.0):
        cap = self._cap
        if cap is None:
            return False
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            return bool(cap.set(cv2.CAP_PROP_EXPOSURE, float(value)))
        except Exception:
            return False

    def release(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        cap, self._cap = self._cap, None
        if cap is not None:
            cap.release()
