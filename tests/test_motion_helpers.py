"""Unit tests para helpers puros do núcleo: motion.lead_offset, snap e
mouse_ctl.build_mouse_input (construção da struct, sem enviar eventos)."""

from core.motion import lead_offset
from core.mouse_ctl import (
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    build_mouse_input,
)


def test_lead_offset_zero_when_no_prediction():
    assert lead_offset(10, 20, 0) == (0.0, 0.0)


def test_lead_offset_scales_with_velocity_and_time():
    vx, vy = lead_offset(100.0, 50.0, 50)  # 50 ms
    assert vx == 100.0 * 0.05
    assert vy == 50.0 * 0.05
    # Dobrar o tempo de previsão dobra o offset
    vx2, vy2 = lead_offset(100.0, 50.0, 100)
    assert vx2 == 2 * vx
    assert vy2 == 2 * vy


def test_mouse_input_builds_struct_fields():
    inp = build_mouse_input(MOUSEEVENTF_LEFTDOWN, data=0)
    assert inp.type == 0  # INPUT_MOUSE
    assert inp.union.mi.dwFlags == MOUSEEVENTF_LEFTDOWN
    assert inp.union.mi.mouseData == 0
    assert inp.union.mi.time == 0


def test_mouse_input_sets_wheel_data():
    inp = build_mouse_input(0x0800, data=120)  # MOUSEEVENTF_WHEEL
    assert inp.union.mi.mouseData == 120


def test_mouse_input_realistic_timing_fields():
    left_down = build_mouse_input(MOUSEEVENTF_LEFTDOWN)
    left_up = build_mouse_input(MOUSEEVENTF_LEFTUP)
    assert left_down.union.mi.dwFlags == MOUSEEVENTF_LEFTDOWN
    assert left_up.union.mi.dwFlags == MOUSEEVENTF_LEFTUP
    assert left_down.type == left_up.type == 0


def test_mouse_input_data_masked_to_32bit():
    inp = build_mouse_input(0x0800, data=0x1FFFFFFFF)  # além de 32 bits
    assert inp.union.mi.mouseData == 0xFFFFFFFF
