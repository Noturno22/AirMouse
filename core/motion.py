import threading
import time


class SmoothEmitter:
    """Distribui deslocamentos do cursor por micro-passos a alta frequencia.

    O loop principal calcula o deslocamento total por frame de camera
    (~20 fps). Esta classe reparte esse deslocamento ao longo do intervalo
    ate ao proximo frame, emitindo movimentos a ~180 Hz com acumulador
    fracionario. Resultado: movimento sedoso no ecra apesar da taxa baixa
    da camara, sem perder nem duplicar pixels.
    """

    def __init__(self, mouse, rate_hz=180.0):
        self._mouse = mouse
        self._period = 1.0 / max(float(rate_hz), 30.0)
        self._lock = threading.Lock()
        self._bx = 0.0
        self._by = 0.0
        self._accx = 0.0
        self._accy = 0.0
        self._span = 0.033
        self._last_push = 0.0
        self._running = False
        self._thread = None
        self.max_pending_px = 600.0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="airmouse-emitter", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def push(self, dxs, dys, seconds):
        with self._lock:
            self._bx += float(dxs)
            self._by += float(dys)
            mag = (self._bx * self._bx + self._by * self._by) ** 0.5
            if mag > self.max_pending_px and mag > 0:
                k = self.max_pending_px / mag
                self._bx *= k
                self._by *= k
            self._span = min(max(float(seconds), 0.006), 0.12)
            self._last_push = time.perf_counter()

    def clear(self):
        with self._lock:
            self._bx = 0.0
            self._by = 0.0

    @property
    def pending(self):
        with self._lock:
            return (self._bx * self._bx + self._by * self._by) ** 0.5

    def _loop(self):
        period = self._period
        next_tick = time.perf_counter()
        while self._running:
            # Espera o próximo instante de emissão sem deixar o temporizador
            # "recuperar o atraso" em rajadas. Se a iteração demorar mais do que
            # um período (ex.: um sleep/atraso do SO), ressincronizamos em vez de
            # disparar N emissões seguidas — que era a causa de micro-tropeções e
            # de movimento "aos solavancos" no cursor.
            now = time.perf_counter()
            if now < next_tick:
                time.sleep(next_tick - now)
                now = time.perf_counter()
            if now >= next_tick + period:
                next_tick = now
            next_tick += period

            ex = ey = 0.0
            with self._lock:
                now = time.perf_counter()
                idle = now - self._last_push > 2.5 * self._span
                frac = min(period / self._span, 1.0)
                ex = self._bx * frac
                ey = self._by * frac
                if idle:
                    ex += self._bx
                    ey += self._by
                    self._bx = 0.0
                    self._by = 0.0
                else:
                    self._bx -= ex
                    self._by -= ey
                self._accx += ex
                self._accy += ey
            ix = int(self._accx)
            iy = int(self._accy)
            if ix or iy:
                with self._lock:
                    self._accx -= ix
                    self._accy -= iy
                try:
                    self._mouse.move_by(ix, iy)
                except Exception:
                    pass


def lead_offset(vx, vy, predict_ms):
    """Antecipacao: deslocamento extra proporcional a velocidade filtrada."""
    t = max(predict_ms, 0.0) / 1000.0
    return vx * t, vy * t
