"""Unit tests para o núcleo de precisão: OneEuroFilter + AccelCurve (core/filters.py).

Estes filtros são o coração da qualidade do cursor (anti-tremor, resposta
em movimento, aceleração tipo rato). Estavam sem testes dedicados.
"""

from core.filters import AccelCurve, FilterPair2D, OneEuroFilter, _LowPass


def test_on_euro_first_call_returns_input():
    f = OneEuroFilter()
    assert f.filter(10.0, t=0.0) == 10.0
    assert f.filter(10.0, t=1 / 30) == 10.0


def test_on_euro_no_lag_on_constant_input():
    f = OneEuroFilter()
    t = 0.0
    for _ in range(30):
        f.filter(5.0, t=t)
        t += 1 / 30
    # Com entrada constante, a saída deve fixar-se no valor
    assert abs(f.filter(5.0, t=t) - 5.0) < 1e-6
    assert abs(f.filter(5.0, t=t + 1 / 30) - 5.0) < 1e-6


def test_on_euro_converges_to_step():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.05)
    t = 0.0
    out = 0.0
    for _ in range(200):
        out = f.filter(1.0, t=t)
        t += 1 / 60
    # Deve aproximar-se do degrau após muitos frames
    assert 0.95 <= out <= 1.0


def test_on_euro_velocity_tracks_movement():
    f = OneEuroFilter()
    t = 0.0
    for i in range(60):
        f.filter(float(i), t=t)  # rampa de 1 unidade/frame
        t += 1 / 60
    # Para uma rampa constante, a velocidade deve ser claramente > 0
    assert f.velocity > 1.0


def test_on_euro_reset_clears_state():
    f = OneEuroFilter()
    f.filter(3.0, t=0.0)
    f.filter(9.0, t=1 / 30)
    f.reset()
    assert f.velocity == 0.0
    # Após reset, o primeiro valor volta a passar praticamente direto
    out = f.filter(3.0, t=0.0)
    assert out == 3.0


def test_lowpass_applies_alpha():
    lp = _LowPass()
    assert lp.apply(5.0, 1.0) == 5.0
    # Com alpha=0.5 a partir de 5, depois 1.0
    val = lp.apply(1.0, 0.5)
    assert abs(val - 3.0) < 1e-9


def test_filter_pair_2d_magnitude_velocity():
    pair = FilterPair2D()
    t = 0.0
    # Filtra X e Y constantes, velocidade ~0
    for _ in range(30):
        pair.fx.filter(5.0, t=t)
        pair.fy.filter(3.0, t=t)
        t += 1 / 30
    assert pair.velocity < 1e-6


def test_accel_curve_bounds():
    if hasattr(AccelCurve, "apply"):
        curve = AccelCurve(min_gain=1.2, max_gain=3.0, ref_speed=1400.0, expo=1.7)
        # Devagar -> perto do ganho mínimo
        slow = curve.apply(10, 10)
        assert slow >= 1.2 and slow < 1.5
        # Muito rápido -> satura no ganho máximo
        fast = curve.apply(5000, 0)
        assert fast == 3.0
        # Monótono crescente em |v|
        prev = -1
        for v in range(0, 4000, 100):
            g = curve.apply(v, 0)
            assert g >= prev - 1e-9
            prev = g


def test_accel_curve_smoothstep_when_expo_zero():
    curve = AccelCurve(min_gain=1.0, max_gain=3.0, ref_speed=1000.0, expo=0.0)
    # No meio (t=0.5) → min + (max-min)*0.5 = 2.0 para smoothstep
    g = curve.apply(500, 0)
    assert abs(g - 2.0) < 1e-6
