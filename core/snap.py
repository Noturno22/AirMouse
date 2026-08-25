import ctypes
import ctypes.wintypes as wintypes
import math
import threading
import time

try:
    import uiautomation as auto

    _AUTO_OK = True
except Exception:
    auto = None
    _AUTO_OK = False

CLICKABLE_TYPES = frozenset(
    {
        "ButtonControl",
        "HyperlinkControl",
        "ListItemControl",
        "MenuItemControl",
        "TabItemControl",
        "CheckBoxControl",
        "RadioButtonControl",
        "SplitButtonControl",
        "ComboBoxControl",
    }
)


class SnapEngine:
    """Atracao magnetica do cursor para elementos clicaveis proximos.

    Uma thread em baixa frequencia pergunta ao Windows (UI Automation) qual
    o controlo sob o cursor e, se for clicavel, guarda o centro. O loop
    principal consulta pull() a cada frame e recebe uma pequena atracao na
    direcao desse centro quando o cursor passa perto devagar.
    """

    def __init__(self, radius_px=46.0, strength=0.35, poll_hz=4.0, enabled=True):
        self.radius_px = float(radius_px)
        self.strength = min(max(float(strength), 0.0), 1.0)
        self.poll_hz = max(float(poll_hz), 0.5)
        self.enabled = bool(enabled) and _AUTO_OK
        self.available = _AUTO_OK
        self._lock = threading.Lock()
        self._center = None
        self._ts = 0.0
        self._last_cursor = None
        self._speed = 0.0
        self._running = False
        self._thread = None

    @property
    def status(self):
        if not _AUTO_OK:
            return "indisponivel"
        return "ON" if self.enabled else "off"

    def start(self):
        if not self.available or self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="airmouse-snap", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def toggle(self):
        self.enabled = not self.enabled
        return self.status

    def _observe_cursor(self):
        try:
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            now = time.perf_counter()
            cur = (float(pt.x), float(pt.y))
        except Exception:
            return
        with self._lock:
            if self._last_cursor is not None:
                dt = max(now - getattr(self, "_obs_t", now), 1e-3)
                d = math.hypot(cur[0] - self._last_cursor[0], cur[1] - self._last_cursor[1])
                self._speed = self._speed * 0.6 + (d / dt) * 0.4
            self._last_cursor = cur
            self._obs_t = now

    def _poll_once(self):
        node = None
        try:
            ctrl = auto.ControlFromCursor()
            node = ctrl
            depth = 0
            while node is not None and depth < 5:
                if self._clickable(node):
                    break
                parent = node.GetParentControl()
                if parent is None:
                    break
                node = parent
                depth += 1
            else:
                node = None
            if node is None:
                with self._lock:
                    self._center = None
                return
            rect = node.BoundingRectangle
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w < 6 or h < 6 or rect.left < -90000 or rect.top < -90000:
                with self._lock:
                    self._center = None
                return
            center = ((rect.left + rect.right) / 2.0, (rect.top + rect.bottom) / 2.0)
            with self._lock:
                self._center = center
                self._ts = time.perf_counter()
        except Exception:
            with self._lock:
                self._center = None

    @staticmethod
    def _clickable(ctrl):
        try:
            name = ctrl.ControlTypeName
            if name in CLICKABLE_TYPES:
                return True
        except Exception:
            pass
        try:
            pat = ctrl.GetPattern(auto.PatternId.InvokePattern)
            return pat is not None
        except Exception:
            return False

    def fresh_center(self, now, max_age_s=0.45):
        with self._lock:
            if self._center is None or (now - self._ts) > max_age_s:
                return None
            return self._center

    def pull(self, cursor_xy, now):
        if not self.enabled:
            return 0.0, 0.0
        center = self.fresh_center(now)
        if center is None:
            return 0.0, 0.0
        dx = center[0] - cursor_xy[0]
        dy = center[1] - cursor_xy[1]
        d = math.hypot(dx, dy)
        with self._lock:
            speed = self._speed
        if d <= 0.5 or d > self.radius_px or speed > 1100.0:
            return 0.0, 0.0
        k = self.strength * (1.0 - d / self.radius_px)
        px = dx * k
        py = dy * k
        cap = 22.0
        mag = math.hypot(px, py)
        if mag > cap:
            px *= cap / mag
            py *= cap / mag
        return px, py

    def assist_point(self, cursor_xy, now, radius=None):
        if not self.enabled:
            return None
        center = self.fresh_center(now)
        if center is None:
            return None
        r = self.radius_px if radius is None else radius
        if math.hypot(center[0] - cursor_xy[0], center[1] - cursor_xy[1]) <= r:
            return center
        return None

    def _loop(self):
        interval = 1.0 / self.poll_hz
        next_tick = time.perf_counter()
        while self._running:
            self._observe_cursor()
            with self._lock:
                slow = self._speed < 1200.0
            if slow:
                self._poll_once()
            next_tick += interval
            rest = next_tick - time.perf_counter()
            if rest > 0:
                time.sleep(rest)
