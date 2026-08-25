import math


def _palm_center(landmarks, width, height):
    ids = (0, 5, 9, 13, 17)
    xs = sum(landmarks[i][0] for i in ids) / len(ids)
    ys = sum(landmarks[i][1] for i in ids) / len(ids)
    return (xs * width, ys * height)


def _hand_scale(landmarks, width, height):
    wrist = landmarks[0]
    mid = landmarks[9]
    dx = (mid[0] - wrist[0]) * width
    dy = (mid[1] - wrist[1]) * height
    return math.hypot(dx, dy)


class HandLock:
    """Escolhe a mao do controlador quando ha mais maos em cena.

    Com uma so mao: essa mao controla sempre (comportamento anterior).
    Com varias: mantem a mao mais proxima do ultimo ponto controlado
    (continuidade de trajectoria); maos novas longe desse ponto nao
    roubam o controlo. Se a mao ativa desaparece, apos um periodo de
    graca qualquer mao pode adquirir o controlo.
    """

    def __init__(self, radius_frac=0.30, lost_grace_frames=10):
        self.radius_frac = float(radius_frac)
        self.lost_grace_frames = int(lost_grace_frames)
        self._last_palm = None
        self._lost = 0

    @property
    def locked(self):
        return self._last_palm is not None

    def reset(self):
        self._last_palm = None
        self._lost = 0

    def select(self, hands, width, height):
        """Devolve os landmarks da mao escolhida ou None.

        `hands` e a lista de maos do tracker (landmarks normalizados).
        """
        if not hands:
            self._lost += 1
            if self._lost > self.lost_grace_frames:
                self.reset()
            return None

        palms = [_palm_center(h, width, height) for h in hands]

        if self._last_palm is not None:
            best_i = None
            best_d = None
            for i, p in enumerate(palms):
                d = math.hypot(p[0] - self._last_palm[0], p[1] - self._last_palm[1])
                if d <= self.radius_frac * max(width, height) and (
                    best_d is None or d < best_d
                ):
                    best_i, best_d = i, d
            if best_i is not None:
                self._lost = 0
                self._last_palm = palms[best_i]
                return hands[best_i]
            # mao ativa desapareceu (outras estao fora do raio): nao trocar
            # de imediato; so apos a graca expirar e possivel readquirir.
            self._lost += 1
            if self._lost > self.lost_grace_frames:
                self.reset()
            else:
                return None

        # sem historico (ou graca expirada): adquire a maior mao
        # (mais proxima da camera); com uma so mao, essa mao.
        if len(hands) == 1:
            chosen = 0
        else:
            chosen = max(
                range(len(hands)), key=lambda i: _hand_scale(hands[i], width, height)
            )
        self._last_palm = palms[chosen]
        self._lost = 0
        return hands[chosen]
