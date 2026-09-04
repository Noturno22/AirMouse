import collections
import difflib
import json
import os
import queue
import re
import threading
import time
import unicodedata
import urllib.request
import zipfile

import numpy as np

from core.log import get_logger
from core.nlu import parse_local, parse_with_llm

log = get_logger("voice")

WAKE_ALIASES = ("jarvis", "jarbas", "assistente", "computador")

SIL_START_RMS = 550.0
SIL_END_RMS = 380.0
SILENCE_END_S = 1.0
MAX_UTT_S = 7.0
PREROLL_S = 0.45


def _strip_accents(text):
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def valid_model_dir(path):
    return os.path.isfile(os.path.join(path, "am", "final.mdl")) or os.path.isfile(
        os.path.join(path, "final.mdl")
    )


def _find_model_dir(base, preferred):
    candidates = [preferred]
    try:
        for name in os.listdir(base):
            full = os.path.join(base, name)
            if os.path.isdir(full) and name.startswith("vosk-model") and "pt" in name:
                candidates.append(full)
    except OSError as e:
        log.debug("Falha a listar %s \u00e0 procura de modelo Vosk: %s", base, e)
    for c in candidates:
        if valid_model_dir(c):
            return c
    return None


def ensure_vosk_model(cfg):
    base = os.path.dirname(cfg.vosk_model_path) or "."
    found = _find_model_dir(base, cfg.vosk_model_path)
    if found:
        return found

    zip_path = os.path.join(base, "vosk-pt.zip")
    print(f"A baixar modelo de voz (~49 MB) para {base} ...")
    os.makedirs(base, exist_ok=True)

    def _progress(blocks, bs, total):
        if total > 0:
            pct = min(blocks * bs * 100 // total, 100)
            print(f"\rA descarregar voz: {pct:3d}%   ", end="", flush=True)

    urllib.request.urlretrieve(cfg.vosk_model_url, zip_path, reporthook=_progress)
    print("\rA extrair modelo de voz...      ")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(base)
    os.remove(zip_path)
    found = _find_model_dir(base, cfg.vosk_model_path)
    if found:
        return found
    raise FileNotFoundError("Modelo Vosk nao encontrado apos extracao")


def _rms_i16(raw_bytes):
    n = len(raw_bytes) // 2
    if n == 0:
        return 0.0
    arr = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(arr * arr)))


class VoiceEngine:
    """Hibrido: VAD por energia para detetar atividade vocal; Whisper
    para transcrever e detetar a wake word e o comando num unico passo."""

    def __init__(self, cfg, cmd_queue):
        self.cfg = cfg
        self.cmd_queue = cmd_queue
        self.speaker = None
        self.chat = None
        self._chat_busy = False
        self.status = "off"
        self._running = False
        self._thread = None
        self._audio_q = queue.Queue()
        self._stream = None
        self._rec = None
        self._whisper = None

    def set_speaker(self, speaker):
        self.speaker = speaker

    def set_chat(self, chat):
        """Liga o cliente de conversa por IA (respostas livres faladas)."""
        self.chat = chat

    def start(self):
        if self._running:
            return True
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model, SetLogLevel
        except ImportError as exc:
            print(f"Aviso: voz desativada ({exc}). Instala com: pip install vosk sounddevice")
            return False

        try:
            sd.default.device = (sd.default.device[0], None)
            test = sd.query_devices(device=sd.default.device[0])
            print(f"Mic: {test['name']}")
        except Exception as exc:
            print(f"Aviso: nenhum microfone encontrado ({exc}); voz desativada.")
            return False

        try:
            model_dir = ensure_vosk_model(self.cfg)
            SetLogLevel(-3)
            model = Model(model_dir)
            self._rec = KaldiRecognizer(model, 16000)
            self._rec.SetWords(False)
        except Exception as exc:
            print(f"Aviso: nao foi possivel carregar o modelo de voz ({exc}).")
            return False

        def _callback(indata, frames, t, status_flag):
            self._audio_q.put(bytes(indata))

        try:
            self._stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=4000,
                dtype="int16",
                channels=1,
                callback=_callback,
            )
            self._stream.start()
        except Exception as exc:
            print(f"Aviso: falha ao abrir o microfone ({exc}); voz desativada.")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.status = "wake"
        wake = self.cfg.voice_wake_word
        mode = "sempre ativo" if self.cfg.voice_always_on else f'diga "{wake}"'
        print(f"Voz ativa ({mode}) + Whisper '{self.cfg.whisper_model}' para comandos.")
        print("  Exemplos: pausa | continua | clica | clique direito | scroll cima |")
        print("  mais rapido | suave | abre o assistente | ampliar | tirar a lupa | sai")
        return True

    def toggle(self):
        if self.status == "off":
            return self.start()
        self.status = "off"
        print("Voz em pausa (tecla v liga de novo).")
        return True

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                log.debug("Falha ao parar o stream de \u00e1udio: %s", e)
            self._stream = None

    def _beep(self):
        try:
            import sounddevice as sd

            sr = 16000
            t = np.linspace(0, 0.09, int(sr * 0.09), False)
            tone = (np.sin(2 * np.pi * 880 * t) * 12000).astype(np.int16)
            sd.play(tone, sr)
        except Exception as e:
            log.debug("Falha ao reproduzir beep de alerta: %s", e)

    def _get_whisper(self):
        if self._whisper is not None:
            return self._whisper
        name = getattr(self.cfg, "whisper_model", "small")
        print(f"A carregar Whisper '{name}' (a 1a vez descarrega o modelo)...")
        try:
            from faster_whisper import WhisperModel

            self._whisper = WhisperModel(
                name, device="cpu", compute_type="int8", cpu_threads=4
            )
            print("Whisper pronto.")
        except Exception as exc:
            print(f"Aviso: Whisper indisponivel ({exc}); comandos por voz limitados.")
            self._whisper = False
        return self._whisper

    def _transcribe(self, pcm_int16):
        model = self._get_whisper()
        if model is False or model is None:
            return ""
        audio = pcm_int16.astype(np.float32) / 32768.0
        try:
            segments, info = model.transcribe(
                audio, language="pt", beam_size=1, vad_filter=False
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return text
        except Exception as exc:
            print(f"(voz) erro Whisper: {exc}")
            return ""

    def _capture_utterance(self):
        chunks = collections.deque()
        chunk_durs = collections.deque()
        started = None
        last_voice_t = None
        deadline = time.monotonic() + MAX_UTT_S
        while time.monotonic() < deadline:
            try:
                data = self._audio_q.get(timeout=0.15)
            except queue.Empty:
                data = None
            now = time.monotonic()
            if data is not None:
                dur = len(data) / 32000.0
                rms = _rms_i16(data)
                chunks.append(data)
                chunk_durs.append(dur)
                while chunk_durs and sum(chunk_durs) > PREROLL_S:
                    chunk_durs.popleft()
                    chunks.popleft()
                if started is None:
                    if rms >= SIL_START_RMS:
                        started = now
                        last_voice_t = now
                elif rms >= SIL_END_RMS:
                    last_voice_t = now
            if started is not None:
                if last_voice_t is not None and now - last_voice_t >= SILENCE_END_S:
                    break
                if time.monotonic() - (started - PREROLL_S) > MAX_UTT_S:
                    break
        if started is None:
            return b""
        return b"".join(chunks)

    def _loop(self):
        while self._running:
            try:
                data = self._audio_q.get(timeout=0.25)
            except queue.Empty:
                continue
            if self.status == "off":
                continue
            try:
                if self._rec.AcceptWaveform(data):
                    text = json.loads(self._rec.Result()).get("text", "")
                    if text:
                        self._handle_vosk_result(text)
                else:
                    partial = json.loads(self._rec.PartialResult()).get("partial", "")
                    if partial:
                        self._handle_vosk_result(partial)
            except Exception:
                continue

    def _handle_vosk_result(self, text):
        t = _strip_accents(text.lower()).strip()
        if not t:
            return

        for alias in WAKE_ALIASES:
            if alias in t or difflib.get_close_matches(t, (alias,), n=1, cutoff=0.7):
                if self.cfg.voice_always_on:
                    rest = re.sub(
                        r"\b(" + "|".join(WAKE_ALIASES) + r")\b", "", t, flags=re.IGNORECASE
                    ).strip()
                    if rest:
                        self._dispatch(rest)
                    return
                self._listen_for_command()
                return

        words = t.split()
        for word in words:
            for alias in WAKE_ALIASES:
                if difflib.get_close_matches(word, (alias,), n=1, cutoff=0.55):
                    if self.cfg.voice_always_on:
                        rest = re.sub(
                            r"\b(" + "|".join(WAKE_ALIASES) + r")\b", "", t, flags=re.IGNORECASE
                        ).strip()
                        if rest:
                            self._dispatch(rest)
                        return
                    self._listen_for_command()
                    return

        if self.cfg.voice_always_on and len(t.split()) >= 2:
            self._dispatch(t)

    def _listen_for_command(self):
        self.status = "listening"
        self._beep()
        if self.speaker is not None:
            self.speaker.say("Sim?")
        pcm = self._capture_utterance()
        if self.status == "off":
            return
        if not pcm:
            self.status = "wake"
            return
        raw = np.frombuffer(pcm, dtype=np.int16)
        said = self._transcribe(raw)
        if not said:
            self.status = "wake"
            if self.speaker is not None:
                self.speaker.say("Nao ouvi nada.")
            return
        self._dispatch(_strip_accents(said.lower()))

    def _dispatch(self, text):
        # 1) Comando por regras locais (rapido, sem rede)
        action, value = parse_local(text)
        if action is not None:
            self.cmd_queue.put({"action": action, "value": value, "text": text})
            if self.status != "off":
                self.status = "wake"
            return

        # 2) Comando a desambiguar via IA
        if self.chat is not None:
            try:
                mode, action = self.chat.classify(text)
                if mode == "cmd":
                    if action is None:
                        action, value = parse_with_llm(text, self.cfg)
                    else:
                        value = None
                    if action is not None:
                        self.cmd_queue.put(
                            {"action": action, "value": value, "text": text}
                        )
                        if self.status != "off":
                            self.status = "wake"
                        return
                    # comando nao reconhecido pelo parser -> trata como conversa
                if mode == "chat":
                    self._reply_conversation(text)
                    return
            except Exception as e:
                log.debug("Erro ao processar comando de voz: %s", e)

        # 3) Fallback: conversa livre com a IA
        self._reply_conversation(text)

    def _reply_conversation(self, text):
        if self.chat is None or not getattr(self.cfg, "llm_enabled", True):
            print(f'(voz) nao entendi: "{text}"')
            if self.speaker is not None:
                self.speaker.say("Nao entendi.")
            return
        self._chat_busy = True
        self.status = "thinking"
        try:
            reply = self.chat.respond(text)
        except Exception as exc:
            print(f"(voz) erro de conversa: {exc}")
            reply = "Desculpa, tive um problema a pensar."
        finally:
            self._chat_busy = False
        if reply:
            print(f'[jarvis] {reply}')
            if self.speaker is not None:
                self.speaker.say(reply, interrupt=True)
        if self.status != "off":
            self.status = "wake"
