"""Trial de 30 min no cliente: conta uso real, is_blocked quando esgota,
e NÃO concede trial novo offline sem registo local (anti-reset)."""
import core.licensing as lic
from core.license_client import LicenseError


def test_default_state_is_free():
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=30 * 60)
    assert lm.tier is lic.Tier.FREE
    assert not lm.is_blocked()


def test_trial_uses_30_minutes(tmp_path):
    store = tmp_path / "lic.json"
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    lm.report_usage(30 * 60)
    assert lm.trial_used_seconds() == 30 * 60
    assert lm.trial_remaining_seconds() == 0
    assert lm.is_blocked()
    assert lm.block_reason() == "trial_esgotado"


def test_trial_offline_without_local_record_blocks(monkeypatch, tmp_path):
    """Apagou-se license.json e está offline -> NÃO recebe 30 min novos."""
    store = tmp_path / "lic.json"  # não existe -> ficheiro novo (apagado)
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    # força falha de rede no cliente
    def _boom(*a, **k):
        raise LicenseError("sem_servidor_reachavel")
    monkeypatch.setattr(lm._client, "trial_status", _boom)
    lm.reconcile_trial()
    assert lm.is_blocked()
    assert lm.block_reason() == "trial_requer_ligacao"
