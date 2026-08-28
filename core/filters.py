import math
import time


class _LowPass:
    def __init__(self):
        self.y = None

    def apply(self, x, alpha):
        self.y = x if self.y is None else alpha * x + (1.0 - alpha) * self.y
        return self.y


class OneEuroFilter:
    def __init__(self, min_cutoff=1.4, beta=0.028, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.velocity = 0.0
        self._x_lpf = _LowPass()
        self._dx_lpf = _LowPass()
        self._x_prev = None
        self._t_prev = None

    def reset(self):
        self._x_lpf.y = None
        self._dx_lpf.y = None
        self._x_prev = None
        self._t_prev = None
        self.velocity = 0.0

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x, t=None):
        now = time.perf_counter() if t is None else t
        if self._t_prev is None:
            dt = 1.0 / 30.0
        else:
            dt = max(now - self._t_prev, 1e-6)
        self._t_prev = now

        dx = 0.0 if self._x_prev is None else (x - self._x_prev) / dt
        self._x_prev = x
        edx = self._dx_lpf.apply(dx, self._alpha(self.d_cutoff, dt))
        self.velocity = edx
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self._x_lpf.apply(x, self._alpha(cutoff, dt))


class FilterPair2D:
    def __init__(self, min_cutoff=1.4, beta=0.028):
        self.fx = OneEuroFilter(min_cutoff=min_cutoff, beta=beta)
        self.fy = OneEuroFilter(min_cutoff=min_cutoff, beta=beta)
        self.vx = 0.0
        self.vy = 0.0

    @property
    def velocity(self):
        return math.hypot(self.vx, self.vy)

    def set_params(self, min_cutoff, beta):
        for f in (self.fx, self.fy):
            f.min_cutoff = min_cutoff
            f.beta = beta

    def reset(self):
        self.fx.reset()
        self.fy.reset()
        self.vx = 0.0
        self.vy = 0.0

    def filter(self, x, y):
        rx = self.fx.filter(x)
        ry = self.fy.filter(y)
        self.vx = self.fx.velocity
        self.vy = self.fy.velocity
        return rx, ry


class AccelCurve:
    """Curva de aceleracao tipo rato gaming.

    expo <= 0 mantem o smoothstep classico; expo > 0 usa curva de potencia
    (t**expo), que e mais precisa devagar e mais agressiva a varrer.
    """

    def __init__(self, min_gain=1.2, max_gain=3.0, ref_speed=1400.0, expo=1.7):
        self.min_gain = float(min_gain)
        self.max_gain = float(max_gain)
        self.ref_speed = max(float(ref_speed), 1e-6)
        self.expo = float(expo)

    def apply(self, vx, vy):
        t = min(math.hypot(vx, vy) / self.ref_speed, 1.0)
        if self.expo > 0.0:
            s = t ** self.expo
        else:
            s = t * t * (3.0 - 2.0 * t)
        return self.min_gain + (self.max_gain - self.min_gain) * s
