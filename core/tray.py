import threading

from PIL import Image, ImageDraw
import pystray


def _build_icon_image(active=True):
    size = 64
    img = Image.new("RGBA", (size, size), (16, 16, 20, 255))
    d = ImageDraw.Draw(img)
    color = (90, 220, 120, 255) if active else (150, 150, 150, 255)
    d.ellipse((8, 8, 56, 56), outline=color, width=4)
    d.line((32, 18, 32, 40), fill=color, width=5)
    d.line((32, 40, 22, 50), fill=color, width=5)
    d.line((32, 40, 42, 50), fill=color, width=5)
    return img


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: "Retomar" if self.app.is_paused() else "Pausar",
                lambda: self.app.toggle_pause(),
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: f"Ganho: {self.app.gain_label()}",
                None,
                enabled=False,
            ),
            pystray.MenuItem("Ganho -", lambda: self.app.gain_step(-1)),
            pystray.MenuItem("Ganho +", lambda: self.app.gain_step(+1)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: f"Voz: {self.app.voice_status()}",
                lambda: self.app.toggle_voice(),
            ),
            pystray.MenuItem(
                lambda item: f"Snap: {self.app.snap_status()}",
                lambda: self.app.toggle_snap(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Assistente 3D", lambda: self.app.open_assistant()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", lambda: self.app.quit()),
        )

    def start(self):
        try:
            self.icon = pystray.Icon(
                "AirMouse",
                icon=_build_icon_image(True),
                title="AirMouse JARVIS",
                menu=self._menu(),
            )
            t = threading.Thread(target=self.icon.run, daemon=True)
            t.start()
            return True
        except Exception as exc:
            print(f"Aviso: bandeja indisponivel ({exc}).")
            return False

    def notify(self, title, message):
        if self.icon is not None:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def stop(self):
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None


class TrayAppAdapter:
    """Liga o menu da bandeja aos controlos do loop principal."""

    def __init__(self, state, cfg, voice, snap, tuner, assistant, apply_fn):
        self.state = state
        self.cfg = cfg
        self.voice = voice
        self.snap = snap
        self.tuner = tuner
        self.assistant = assistant
        self.apply = apply_fn

    def is_paused(self):
        return bool(self.state.get("paused"))

    def toggle_pause(self):
        self.apply("pause_toggle", None)

    def gain_label(self):
        return f"{self.cfg.move_gain:.1f}"

    def gain_step(self, direction):
        self.apply("gain_up" if direction > 0 else "gain_down", None)

    def voice_status(self):
        if self.voice is None:
            return "off"
        st = getattr(self.voice, "status", "off")
        return {"off": "off", "wake": "jarvis", "listening": "a ouvir"}.get(st, st)

    def toggle_voice(self):
        if self.voice is not None:
            self.voice.toggle()

    def snap_status(self):
        return self.snap.status if self.snap else "off"

    def toggle_snap(self):
        if self.snap:
            self.apply("snap_toggle", None)

    def open_assistant(self):
        self.apply("assistant", None)

    def quit(self):
        self.apply("exit", None)
