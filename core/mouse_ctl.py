import ctypes
import os
import time
from ctypes import wintypes

from pynput.mouse import Button, Controller

# ── Win32 SendInput (botões do rato) ─────────────────────────────────
# O despacho de cliques via SendInput é determinístico e sub-ms, sem o
# overhead do pynput. Em plataformas sem user32 o código cai no pynput.
_IS_WINDOWS = os.name == "nt"

INPUT_MOUSE = 0

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

ULONG_PTR = (
    ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong
)


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


def build_mouse_input(flags, data=0):
    """Constrói uma struct INPUT para um evento de rato (puro, sem enviar)."""
    inp = _INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi = _MOUSEINPUT(0, 0, int(data) & 0xFFFFFFFF, flags, 0, 0)
    return inp


def send_mouse_input(inp):
    """Envia uma struct INPUT via SendInput. Apenas Windows."""
    sent = ctypes.windll.user32.SendInput(
        1, ctypes.byref(inp), ctypes.sizeof(_INPUT)
    )
    return sent == 1


def sendinput_available():
    if not _IS_WINDOWS:
        return False
    try:
        return callable(ctypes.windll.user32.SendInput)
    except Exception:
        return False


class MouseCtl:
    def __init__(self):
        self._enable_dpi_awareness()
        self.mouse = Controller()
        self.screen_w, self.screen_h = self._screen_size()
        self._scroll_acc = 0.0
        self._frac_x = 0.0
        self._frac_y = 0.0
        self._sendinput = sendinput_available()

    @staticmethod
    def _enable_dpi_awareness():
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    @staticmethod
    def _screen_size():
        try:
            user32 = ctypes.windll.user32
            return (
                int(user32.GetSystemMetrics(0)),
                int(user32.GetSystemMetrics(1)),
            )
        except Exception:
            return (1920, 1080)

    def _send_down(self, flags):
        if self._sendinput:
            send_mouse_input(build_mouse_input(flags))
        else:
            self.mouse.press(Button.left)

    def _send_up(self, flags):
        if self._sendinput:
            send_mouse_input(build_mouse_input(flags))
        else:
            try:
                self.mouse.release(Button.left)
            except Exception:
                pass

    def move_by(self, dx, dy):
        self._frac_x += dx
        self._frac_y += dy
        ix = int(self._frac_x)
        iy = int(self._frac_y)
        if not ix and not iy:
            return
        self._frac_x -= ix
        self._frac_y -= iy
        x, y = self.mouse.position
        nx = min(max(x + ix, 0), self.screen_w - 1)
        ny = min(max(y + iy, 0), self.screen_h - 1)
        self.mouse.position = (int(nx), int(ny))

    def left_click(self):
        self.press_left()
        self.release_left()

    def right_click(self):
        if self._sendinput:
            send_mouse_input(build_mouse_input(MOUSEEVENTF_RIGHTDOWN))
            send_mouse_input(build_mouse_input(MOUSEEVENTF_RIGHTUP))
        else:
            self.mouse.press(Button.right)
            time.sleep(0.02)
            self.mouse.release(Button.right)

    def press_left(self):
        self._send_down(MOUSEEVENTF_LEFTDOWN)

    def release_left(self):
        self._send_up(MOUSEEVENTF_LEFTUP)

    def scroll(self, dy):
        self._scroll_acc += dy
        ticks = int(self._scroll_acc)
        if ticks != 0:
            self.mouse.scroll(0, ticks)
            self._scroll_acc -= ticks

    def drag_start(self):
        self.press_left()

    def drag_end(self):
        self.release_left()
