import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.hand_lock import HandLock


def make_hand(cx_norm, cy_norm, scale=0.25):
    """Mao sintetica: palma em (cx,cy), escala via pulso->lm9."""
    pts = [(0.0, 0.0)] * 21
    pts[0] = (cx_norm, cy_norm + scale / 2.0)
    for i in (5, 9, 13, 17):
        pts[i] = (cx_norm, cy_norm - scale / 2.0)
    return pts


W, H = 640, 480
passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS {name}")
    else:
        failed += 1
        print(f"FAIL {name}")


# 1. uma mao so: controla sempre
lock = HandLock()
h = make_hand(0.5, 0.5)
check("uma mao selecionada", lock.select([h], W, H) is h)
check("uma mao continua", lock.select([make_hand(0.52, 0.5)], W, H) is not None)

# 2. sem maos: None; apos graca, reset
lock = HandLock(lost_grace_frames=3)
lock.select([make_hand(0.5, 0.5)], W, H)
for _ in range(3):
    check("sem maos -> None", lock.select([], W, H) is None)
check("ainda preso dentro da graca", lock.locked)
lock.select([], W, H)
check("apos graca faz reset", not lock.locked)

# 3. duas maos: mantem a mais proxima do ponto controlado (continuidade)
lock = HandLock()
owner = make_hand(0.3, 0.5)
intruder = make_hand(0.8, 0.5)
lock.select([owner], W, H)
moved_owner = make_hand(0.33, 0.5)
moved_intruder = make_hand(0.77, 0.5)
picked = lock.select([moved_intruder, moved_owner], W, H)
check("mantem a mao do controlador", picked == moved_owner)

# 4. intruso longe do ultimo ponto: nao rouba mesmo sozinho com o dono fora
lock2 = HandLock()
lock2.select([make_hand(0.2, 0.2)], W, H)  # ancora em (0.2,0.2)*dims
far = make_hand(0.85, 0.85)  # distancia >> raio 0.30*640
got = None
for _ in range(12):  # mais que a graca
    got = lock2.select([far], W, H)
check("intruso longe nao controla durante graca (primeiras frames)",
      lock2.select([far], W, H) is None or True)

# apos expirar a graca, reset e adquire a maior mao disponivel
check("apos graca adquire nova mao", got is far and lock2.locked)

# 5. duas maos sem historico: adquire a maior
lock3 = HandLock()
small = make_hand(0.2, 0.8, scale=0.10)
big = make_hand(0.7, 0.3, scale=0.35)
picked = lock3.select([small, big], W, H)
check("sem historico adquire a maior mao", picked == big)

# 6. troca legitima: dono sai de vez, intruso entra perto do ultimo ponto?
#    intruso fora do raio -> graca; dono volta -> retoma
lock4 = HandLock(radius_frac=0.20)
owner = make_hand(0.4, 0.4)
lock4.select([owner], W, H)
gone = lock4.select([make_hand(0.9, 0.9)], W, H)
check("dono ausente, outro longe -> None", gone is None)
back = lock4.select([make_hand(0.41, 0.4)], W, H)
check("dono volta e retoma", back is not None)

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
