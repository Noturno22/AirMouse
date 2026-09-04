"""Unit tests para o parser local de intenções (core/nlu.py).

parse_local() traduz texto em PT para acções do motor, via regex + fuzzy
match, sem I/O. Cobre o vocabulário de comandos para evitar regressões.
"""

from core.nlu import ACTION_LABELS, parse_local


def test_empty_text_is_none():
    assert parse_local("") == (None, None)
    assert parse_local("   ") == (None, None)


def test_left_click_variants():
    assert parse_local("clica") == ("left_click", None)
    assert parse_local("clique") == ("left_click", None)
    assert parse_local("toca aí") == ("left_click", None)


def test_right_click_variants():
    assert parse_local("clique direito") == ("right_click", None)
    assert parse_local("botao direito") == ("right_click", None)


def test_scroll_up_down():
    assert parse_local("scroll para cima") == ("scroll_up", None)
    assert parse_local("scroll para baixo") == ("scroll_down", None)
    assert parse_local("sobe") == ("scroll_up", None)
    assert parse_local("desce") == ("scroll_down", None)


def test_pause_resume():
    assert parse_local("pausa") == ("pause", None)
    assert parse_local("congela") == ("pause", None)
    assert parse_local("para") == ("pause", None)
    assert parse_local("continua") == ("resume", None)
    assert parse_local("retoma") == ("resume", None)


def test_gain_up_down():
    assert parse_local("mais rapido") == ("gain_up", None)
    assert parse_local("acelera") == ("gain_up", None)
    assert parse_local("mais devagar") == ("gain_down", None)
    assert parse_local("mais lento") == ("gain_down", None)


def test_smooth_presets():
    assert parse_local("modo suave") == ("smooth_suave", None)
    assert parse_local("reactivo") == ("smooth_reactivo", None)
    assert parse_local("normal") == ("smooth_normal", None)


def test_other_commands():
    assert parse_local("guarda") == ("save", None)
    assert parse_local("ajuda") == ("help", None)
    assert parse_local("sair") == ("exit", None)
    assert parse_local("lupa") == ("magnify_on", None)
    assert parse_local("sem lupa") == ("magnify_off", None)
    assert parse_local("abre o assistente") == ("assistant", None)
    assert parse_local("fecha o assistente") == ("assistant_close", None)
    assert parse_local("snap") == ("snap_toggle", None)
    assert parse_local("auto-afinar") == ("autotune_toggle", None)


def test_unknown_text_is_none():
    assert parse_local("xpto sem sentido nenhum") == (None, None)


def test_case_insensitive():
    assert parse_local("PAUSA") == ("pause", None)
    assert parse_local("Clique Direito") == ("right_click", None)


def test_action_labels_cover_all_actions():
    # Todo o vocabulário reconhecível deve ter etiqueta de feedback
    for action, _ in [
        ("pause", None), ("resume", None), ("gain_up", None),
        ("gain_down", None), ("left_click", None), ("right_click", None),
        ("scroll_up", None), ("scroll_down", None), ("exit", None),
        ("help", None), ("save", None), ("smooth_suave", None),
        ("smooth_normal", None), ("smooth_reactivo", None),
        ("snap_toggle", None),
    ]:
        assert action in ACTION_LABELS, f"falta label: {action}"
