import time


class LightBoost:
    """Deteta ambiente escuro e ativa realce (histerese on<low, off>high)."""

    def __init__(self, low=40.0, high=60.0, frames=8, check_every=15):
        self.low = float(low)
        self.high = float(high)
        self.frames = max(int(frames), 1)
        self.check_every = max(int(check_every), 1)
        self.active = False
        self._streak = 0
        self._bright_streak = 0
        self._since_check = 0

    def feed(self, gray_mean):
        self._since_check += 1
        if self._since_check < self.check_every:
            return None
        self._since_check = 0
        if not self.active:
            if gray_mean < self.low:
                self._streak += 1
                if self._streak >= self.frames:
                    self.active = True
                    self._streak = 0
                    return "on"
            else:
                self._streak = 0
        else:
            if gray_mean > self.high:
                self._bright_streak += 1
                if self._bright_streak >= self.frames:
                    self.active = False
                    self._bright_streak = 0
                    return "off"
            else:
                self._bright_streak = 0
        return None
