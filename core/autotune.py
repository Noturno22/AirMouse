import math
import time


class AutoTuner:
    def __init__(self, cfg):
        self.cfg = cfg
        self.enabled = bool(getattr(cfg, "autotune_enabled", True))
        self.user_base_gain = cfg.move_gain
        self._reset_stats()

    def _reset_stats(self):
        self._prev_vx = None
        self._prev_vy = None
        self._v_ema = 0.0
        self._jitter_ema = 0.0
        self._reversals = 0
        self._last_sign = 0
        self._samples = 0
        self._high_flip_windows = 0
        self._next_tick = time.monotonic() + self.cfg.autotune_interval_s

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.cfg.move_gain = self.user_base_gain
            self._reset_stats()
            return "auto-afinacao ON"
        return "auto-afinacao OFF"

    def set_user_gain(self, value):
        self.user_base_gain = value

    def notify_params_changed(self):
        self.cfg.move_gain = self.cfg.move_gain

    def feed(self, active, filters, cursor_dx, cursor_dy):
        if not self.enabled:
            return
        if not active:
            self._prev_vx = None
            self._prev_vy = None
            return
        vx, vy = filters.vx, filters.vy
        if self._prev_vx is None:
            self._prev_vx, self._prev_vy = vx, vy
            return
        dvx, dvy = abs(vx - self._prev_vx), abs(vy - self._prev_vy)
        self._prev_vx, self._prev_vy = vx, vy
        speed = math.hypot(vx, vy)
        a = 0.06
        self._v_ema += a * (speed - self._v_ema)
        self._jitter_ema += a * (math.hypot(dvx, dvy) - self._jitter_ema)
        self._samples += 1

        if cursor_dx or cursor_dy:
            dom_x = abs(cursor_dx) >= abs(cursor_dy)
            s = 1 if (cursor_dx if dom_x else cursor_dy) > 0 else 2
            if self._last_sign and s != self._last_sign:
                self._reversals += 1
            self._last_sign = s

    def maybe_apply(self, now, filters, cfg):
        if not self.enabled or now < self._next_tick:
            return None
        interval = cfg.autotune_interval_s
        self._next_tick = now + interval
        note = None

        if self._samples >= int(20 * interval * 0.5):
            if self._v_ema < 60.0 and self._jitter_ema > 90.0:
                new_cut = max(
                    cfg.filter_min_cutoff_min, cfg.filter_min_cutoff * 0.9
                )
                new_beta = max(cfg.filter_beta_min, cfg.filter_beta * 0.94)
                if new_cut != cfg.filter_min_cutoff:
                    note = f"tremor detetado -> corte {new_cut:.2f}"
                cfg.filter_min_cutoff = new_cut
                cfg.filter_beta = new_beta
                filters.set_params(new_cut, new_beta)
            elif self._v_ema > 650.0 and self._jitter_ema < 0.22 * self._v_ema:
                new_cut = min(
                    cfg.filter_min_cutoff_max,
                    max(cfg.filter_min_cutoff * 1.05, cfg.filter_min_cutoff + 0.04),
                )
                if new_cut != cfg.filter_min_cutoff:
                    cfg.filter_min_cutoff = new_cut
                    filters.set_params(new_cut, cfg.filter_beta)
                    note = f"resposta melhorada -> corte {new_cut:.2f}"

            window_s = interval
            flips_per_s = self._reversals / max(window_s, 1e-6)
            lo = self.user_base_gain * (1.0 - cfg.gain_trim_frac)
            hi = self.user_base_gain * (1.0 + cfg.gain_trim_frac)
            if flips_per_s > 3.0:
                self._high_flip_windows += 1
            else:
                self._high_flip_windows = 0
            if self._high_flip_windows >= 2 and self._v_ema > 120.0:
                ng = max(lo, cfg.move_gain * 0.96)
                if ng != cfg.move_gain:
                    cfg.move_gain = round(ng, 2)
                    note = f"ganho {cfg.move_gain:.1f} (twitch)"
                self._high_flip_windows = 0
            elif flips_per_s < 0.7 and self._v_ema > 420.0:
                ng = min(hi, cfg.move_gain * 1.03)
                if ng != cfg.move_gain:
                    cfg.move_gain = round(ng, 2)
                    note = f"ganho {cfg.move_gain:.1f} (alcance)"

        self._reversals = 0
        self._samples = 0
        return note
