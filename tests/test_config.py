import json

import config


def test_defaults_consistent():
    cfg = config.Config()
    assert cfg.num_hands == 2
    assert cfg.pinch_on_ratio < cfg.pinch_off_ratio
    assert 0.0 <= cfg.move_gain
    assert cfg.gesture_stable_frames >= 1
    assert cfg.pinch_stable_frames >= 1


def test_guard_against_duplicate_num_hands():
    """Regressão: num_hands aparecia duas vezes (config.py:34 e :98)."""
    fields = [f for f in config.Config.__dataclass_fields__]
    assert fields.count("num_hands") == 1


def test_presets_reference_real_fields():
    for _name, cut, beta in config.SMOOTH_PRESETS:
        assert 0.4 <= cut <= 3.0
        assert 0.008 <= beta <= 0.08


def test_load_settings_clamps_gain(monkeypatch, tmp_path):
    monkeypatch.setattr(
        config, "SETTINGS_FILE", str(tmp_path / "settings.json")
    )
    (tmp_path / "settings.json").write_text(
        json.dumps({"move_gain": 999.0}), encoding="utf-8"
    )
    cfg = config.Config()
    idx = config.load_settings(cfg)
    assert cfg.move_gain == 999.0
    assert idx == -1 or idx == 1


def test_load_settings_bad_file_keeps_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(
        config, "SETTINGS_FILE", str(tmp_path / "missing.json")
    )
    cfg = config.Config()
    assert config.load_settings(cfg) == 1
    assert cfg.move_gain == 2.0


def test_save_settings_roundtrip(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        config, "SETTINGS_FILE", str(tmp_path / "settings.json")
    )
    cfg = config.Config()
    cfg.move_gain = 3.7
    config.save_settings(cfg, "NORMAL")
    assert (tmp_path / "settings.json").exists()
    loaded = json.loads(
        (tmp_path / "settings.json").read_text(encoding="utf-8")
    )
    assert loaded["move_gain"] == 3.7
    assert loaded["suavidade"] == "NORMAL"
    assert loaded["pinch_stable_frames"] >= 1


def test_suave_preset_persists(monkeypatch, tmp_path):
    monkeypatch.setattr(
        config, "SETTINGS_FILE", str(tmp_path / "settings.json")
    )
    (tmp_path / "settings.json").write_text(
        json.dumps({"suavidade": "SUAVE", "move_gain": 2.0}), encoding="utf-8"
    )
    cfg = config.Config()
    idx = config.load_settings(cfg)
    assert idx == 0
    assert cfg.filter_min_cutoff == 0.9
    assert cfg.filter_beta == 0.02
