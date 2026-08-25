import ctypes

VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_MEDIA_PLAY_PAUSE = 0xB3

_KEYEVENTF_KEYUP = 0x0002


class MediaCtl:
    """Teclas multimidia globais via keybd_event (sem dependencias novas).

    dry_run=True nao envia teclas (para testes).
    """

    def __init__(self, dry_run=False):
        self.dry_run = bool(dry_run)
        self.sent = []

    def _press(self, vk):
        if self.dry_run:
            self.sent.append(vk)
            return
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP, 0)

    def volume(self, steps):
        steps = max(-20, min(20, int(steps)))
        vk = VK_VOLUME_UP if steps > 0 else VK_VOLUME_DOWN
        for _ in range(abs(steps)):
            self._press(vk)
        return steps

    def play_pause(self):
        self._press(VK_MEDIA_PLAY_PAUSE)
