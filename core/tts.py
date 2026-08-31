import os
import queue
import tempfile
import threading
import urllib.request
import wave

import numpy as np
import sounddevice as sd


def _download(url, path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + ".part"

    def _progress(blocks, bs, total):
        if total > 0:
            pct = min(blocks * bs * 100 // total, 100)
            print(f"\rA descarregar voz TTS: {pct:3d}%   ", end="", flush=True)

    print(f"A baixar voz neural para {path} ...")
    urllib.request.urlretrieve(url, tmp, reporthook=_progress)
    os.replace(tmp, path)
    print()


class Speaker:
    """Voz do Jarvis: Piper neural offline com fallback SAPI5 do Windows."""

    def __init__(self, enabled=True, model_dir="models/piper", voice_files=()):
        self.enabled = bool(enabled)
        self.model_dir = model_dir
        self.voice_files = tuple(voice_files)
        self.engine_name = "off"
        self._q = queue.Queue(maxsize=6)
        self._running = False
        self._thread = None
        self._pv = None
        self._sapi = None

    @property
    def status(self):
        return self.engine_name

    def start(self):
        if not self.enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="airmouse-tts", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        try:
            self._q.put_nowait(None)
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def say(self, text, interrupt=False):
        if not self.enabled or self.engine_name == "off":
            return
        text = (text or "").strip()
        if not text:
            return
        try:
            if interrupt:
                try:
                    while True:
                        self._q.get_nowait()
                except queue.Empty:
                    pass
            self._q.put_nowait(text)
        except queue.Full:
            try:
                self._q.get_nowait()
                self._q.put_nowait(text)
            except Exception:
                pass

    def _ensure_voice(self):
        for url, path in self.voice_files:
            if not os.path.isfile(path):
                _download(url, path)

    def _boot(self):
        onnx = None
        for _, path in self.voice_files:
            if path.endswith(".onnx"):
                onnx = path
                break
        try:
            self._ensure_voice()
            from piper import PiperVoice

            self._pv = PiperVoice.load(onnx)
            self.engine_name = "piper"
            return
        except Exception as exc:
            self._pv = None
            self._piper_err = str(exc)
        try:
            import pyttsx3

            self._sapi = pyttsx3.init()
            try:
                self._sapi.setProperty("rate", 185)
            except Exception:
                pass
            self.engine_name = "sapi5"
        except Exception:
            self.engine_name = "off"

    def _synth_piper(self, text):
        from piper import SynthesisConfig

        cfg = SynthesisConfig(length_scale=1.0)
        out = os.path.join(
            tempfile.gettempdir(), f"airmouse_tts_{os.getpid()}.wav"
        )
        try:
            self._pv.synthesize_wav(text, out, syn_config=cfg)
        except TypeError:
            self._pv.synthesize_wav(text, out)
        with wave.open(out, "rb") as wf:
            sr = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
        try:
            os.remove(out)
        except OSError:
            pass
        data = np.frombuffer(frames, dtype=np.int16)
        return data, sr

    def _loop(self):
        self._boot()
        print(f"TTS: {self.engine_name}")
        while self._running:
            try:
                text = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            if text is None:
                break
            if self.engine_name == "piper" and self._pv is not None:
                try:
                    data, sr = self._synth_piper(text)
                    sd.play(data, sr)
                    sd.wait()
                    continue
                except Exception:
                    self.engine_name = "sapi5-fallback"
                    try:
                        import pyttsx3

                        self._sapi = pyttsx3.init()
                    except Exception:
                        self.engine_name = "off"
            if self.engine_name.startswith("sapi5") and self._sapi is not None:
                try:
                    self._sapi.say(text)
                    self._sapi.runAndWait()
                except Exception:
                    pass
