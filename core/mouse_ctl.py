import ctypes
import time

from pynput.mouse import Button, Controller


class MouseCtl:
    def __init__(self):
        self._enable_dpi_awareness()
        self.mouse = Controller()
        self.screen_w, self.screen_h = self._screen_size()
        self._scroll_acc = 0.0
        self._frac_x = 0.0
        self._frac_y = 0.0

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
        self.mouse.click(Button.left, 1)

    def right_click(self):
        self.mouse.press(Button.right)
        time.sleep(0.02)
        self.mouse.release(Button.right)

    def press_left(self):
        self.mouse.press(Button.left)

    def release_left(self):
        try:
            self.mouse.release(Button.left)
        except Exception:
            pass

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
