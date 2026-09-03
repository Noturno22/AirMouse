"""Licenciamento AirMouse — trial 30min server-auth + ativacao online + lease ES256 + gate."""
import base64
import json
import os
import time
import webbrowser
from enum import Enum

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.fingerprint import machine_id
from core.license_client import LicenseClient, LicenseError

TRIAL_DEFAULT_SECONDS = 30 * 60
LEASE_DEFAULT_DAYS = 7

_PUBLIC_KEY_PEM = os.path.join(os.path.dirname(__file__), "licensing_public_key.pem")


class Tier(Enum):
    FREE = "free"
    PRO = "pro"


PRO_LOCKED = ("snap", "voice", "two_hands", "tts", "ai", "autotune", "low_light")

# Produtos Paddle (Pay Links). Preencher com os IDs reais dos preços quando a
# entidade UE e o catálogo Paddle existirem. Mantido por compat (checkout).
PADDLE_PRODUCT_URLS = {
    "lifetime": os.environ.get("AIRMOUSE_PADDLE_LIFETIME_URL", ""),
    "subscription": os.environ.get("AIRMOUSE_PADDLE_SUBSCRIPTION_URL", ""),
    "family": os.environ.get("AIRMOUSE_PADDLE_FAMILY_URL", ""),
    "access": os.environ.get("AIRMOUSE_PADDLE_ACCESS_URL", ""),
}


def entitlements(tier: Tier) -> dict:
    base = {"move": True, "click": True}
    pro_on = tier == Tier.PRO
    for f in PRO_LOCKED:
        base[f] = pro_on
    return base


def is_pro_locked(tier: Tier, feature: str) -> bool:
    return feature in PRO_LOCKED and tier != Tier.PRO


def _load_public_key():
    with open(_PUBLIC_KEY_PEM, "rb") as fh:
        return serialization.load_pem_public_key(fh.read())


class LicenseManager:
    def __init__(self, secret: str = "", store_path=None,
                 agency: "LicenseAgency | None" = None,
                 endpoints=None, trial_seconds=TRIAL_DEFAULT_SECONDS,
                 public_key=None):
        self._store_path = store_path or _default_store_path()
        self._agency = agency
        self._endpoints = endpoints or _default_endpoints()
        self._client = LicenseClient(self._endpoints)
        self._trial_seconds = trial_seconds
        self._public_key = public_key or _load_public_key()
        self._machine = machine_id()
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""
        self.lease = ""
        self._trial_used = 0
        self._last_nonce = 0
        self._last_use_seq = 0
        self._blocked = False
        self._block_reason = ""
        self.load()

    # ── Trial (server-authoritative + best-effort offline) ──
    def trial_used_seconds(self) -> int:
        return self._trial_used

    def trial_remaining_seconds(self) -> int:
        return max(0, self._trial_seconds - self._trial_used)

    def report_usage(self, seconds: int) -> None:
        self._trial_used = min(self._trial_seconds, self._trial_used + max(0, seconds))
        if self._trial_used >= self._trial_seconds:
            self._blocked = True
            self._block_reason = "trial_esgotado"
        self.save()

    def reconcile_trial(self) -> None:
        """Quando há rede, o servidor é a fonte de verdade: adota o MAIOR uso
        entre local e servidor, e reporta o uso local para o servidor persistir.

        Regra anti-reset: se não há registo local do trial (ex.: ficheiro apagado)
        e o servidor não está alcançável, este aparece como "primeira vez" sem prova
        — bloqueia com pedido de ligação em vez de conceder 30 min novos.
        """
        if self.is_pro:
            return
        had_local = self._trial_used > 0 or _store_exists(self._store_path)
        try:
            status = self._client.trial_status(self._machine)
            server_used = max(0, self._trial_seconds - status["remaining_seconds"])
        except LicenseError:
            if not had_local:
                # sem registo local E sem servidor -> não pode provar 1ª vez
                self._blocked = True
                self._block_reason = "trial_requer_ligacao"
            return
        try:
            self._client.trial_report(self._machine, self._trial_used)
        except LicenseError:
            pass
        self._trial_used = max(self._trial_used, server_used)
        if self._trial_used >= self._trial_seconds:
            self._blocked = True
            self._block_reason = "trial_esgotado"
        self.save()

    def tier_pending(self) -> str:
        if self.is_pro:
            return "pro"
        if self.is_blocked():
            return "trial_esgotado"
        return "trial"

    # ── Persistência ──
    def save(self) -> None:
        if self._store_path == ":memory:":
            return
        try:
            os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
            with open(self._store_path, "w", encoding="utf-8") as fh:
                json.dump({
                    "lease": self.lease,
                    "email": self.email,
                    "machine_id": self._machine,
                    "trial_used": self._trial_used,
                    "last_nonce": self._last_nonce,
                    "last_use_seq": self._last_use_seq,
                }, fh, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        if self._store_path == ":memory:":
            return
        data = self._read_store()
        if data is None:
            return
        if data.get("machine_id") != self._machine:
            return  # ficheiro de outra máquina -> não honrar
        self._trial_used = int(data.get("trial_used", 0))
        self._last_nonce = int(data.get("last_nonce", 0))
        self._last_use_seq = int(data.get("last_use_seq", 0))
        if data.get("lease") and self._validate_local_lease(data["lease"]):
            self.lease = data["lease"]
            self.email = data.get("email", "")
            self.tier = Tier.PRO

    def _read_store(self):
        try:
            with open(self._store_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    # ── Validação local do lease (ES256, anti-forgery) ──
    def _verify_es256_with(self, pub_key, signing_input: bytes, raw_sig: bytes) -> bool:
        """Verifica a assinatura ES256 (raw r||s -> DER) com a chave pública."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
        try:
            r = int.from_bytes(raw_sig[:32], "big")
            s = int.from_bytes(raw_sig[32:], "big")
            der_sig = encode_dss_signature(r, s)
            pub_key.verify(der_sig, signing_input, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def _validate_local_lease(self, lease: str) -> bool:
        try:
            header_b64, payload_b64, sig_b64 = lease.split(".")
        except ValueError:
            return False
        try:
            header = json.loads(_b64d(header_b64))
            payload = json.loads(_b64d(payload_b64))
            raw_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
        except Exception:
            return False
        if header.get("alg") != "ES256":
            return False  # rejeita alg:none e outras
        if not self._verify_es256_with(self._public_key,
                                       f"{header_b64}.{payload_b64}".encode(), raw_sig):
            return False
        if payload.get("sub") != f"machine:{self._machine}":
            return False
        if int(time.time()) > int(payload.get("exp", 0)):
            return False
        # Anti-replay: rejeita apenas leases ESTRITAMENTE mais antigos do que o
        # último já visto. O lease atual (use_seq/revocation_nonce iguais aos
        # últimos vistos) tem de continuar válido ao revalidar/reabrir (senão um
        # lease gravado nunca carregaria e `is_blocked()` bloquearia um PRO bom).
        if int(payload.get("revocation_nonce", -1)) < self._last_nonce:
            return False
        if int(payload.get("use_seq", -1)) < self._last_use_seq:
            return False
        # Avança monotonicamente os contadores (nunca regredem).
        self._last_nonce = max(self._last_nonce, int(payload.get("revocation_nonce", 0)))
        self._last_use_seq = max(self._last_use_seq, int(payload.get("use_seq", 0)))
        return True

    def is_pro_offline_valid(self) -> bool:
        return bool(self.lease and self._validate_local_lease(self.lease))

    # ── Ativação online ──
    def activate(self, key: str) -> bool:
        try:
            result = self._client.activate(key.strip(), self._machine)
        except LicenseError as exc:
            self._blocked = True
            self._block_reason = f"ativacao_falhou: {exc}"
            return False
        self.lease = result["lease"]
        self.key = key.strip()
        self.tier = Tier.PRO
        self.save()
        return True

    def revalidate(self) -> bool:
        if not self.lease:
            return False
        try:
            result = self._client.revalidate(self._machine, self.lease)
        except LicenseError:
            return False
        self.lease = result["lease"]
        self.save()
        return True

    def maybe_revalidate(self) -> None:
        if not self.is_pro:
            return
        if self._needs_revalidation():
            self.revalidate()

    def _needs_revalidation(self) -> bool:
        try:
            payload = self._decode_payload(self.lease)
            issued = int(payload.get("iat", 0))
        except Exception:
            return True
        return (time.time() - issued) >= 7 * 24 * 3600 - 3600  # ~1h antes de expirar 7d

    def _decode_payload(self, lease: str) -> dict:
        payload_b64 = lease.split(".")[1]
        return json.loads(_b64d(payload_b64))

    # ── Bloqueio / gate ──
    def is_blocked(self) -> bool:
        if self.tier == Tier.PRO:
            if not self._validate_local_lease(self.lease):
                self._blocked = True
                self._block_reason = "lease_invalido_ou_expirado"
                return True
            return False
        if self._blocked:
            return True
        if self._trial_used >= self._trial_seconds:
            return True
        return False

    def block_reason(self) -> str:
        if self._block_reason:
            return self._block_reason
        return "trial_esgotado" if self.is_blocked() else ""

    # ── Compat com UI / CLI / tools (API preservada) ──
    @property
    def is_pro(self) -> bool:
        return self.tier == Tier.PRO

    def can(self, feature: str) -> bool:
        return bool(entitlements(self.tier).get(feature, True))

    def deactivate(self) -> None:
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""
        self.lease = ""
        self._blocked = False
        self._block_reason = ""
        if os.path.exists(self._store_path):
            try:
                os.remove(self._store_path)
            except OSError:
                pass

    def checkout_urls(self, vendor_id: int) -> dict[str, str]:
        url = PADDLE_PRODUCT_URLS.get("lifetime")
        payment = PADDLE_PRODUCT_URLS.get("subscription")
        family = PADDLE_PRODUCT_URLS.get("family")
        access = PADDLE_PRODUCT_URLS.get("access")
        return {
            "lifetime": url or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-lifetime",
            "subscription": payment or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-subscription",
            "family": family or f"https://checkout.paddle.com/{vendor_id}?product=maouse-family",
            "access": access or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-access",
        }

    def open_checkout(self, product: str, vendor_id: int) -> bool:
        urls = self.checkout_urls(vendor_id)
        url = urls.get(product)
        if not url:
            return False
        try:
            return bool(webbrowser.open(url, new=2))
        except webbrowser.Error:
            return False

    # issue_pro_key / validate_key: mantidos NA API pública mas já NÃO usados
    # no caminho de produção (o servidor emite; o cliente só ativa online).
    def issue_pro_key(self, email: str) -> str:
        raise NotImplementedError(
            "Emissão de chaves é feita pelo servidor (license-server). "
            "Use tools/issue_pro_key.py remoto.")


class LicenseAgency:
    """Interface opcional para validação ONLINE (compat mit UI).

    Mantida da API anterior; o caminho de produção é a ativação online
    (LicenseManager.activate / lease ES256), não a validação offline.
    """

    def online_validate(self, license_doc: str) -> bool:
        return True


# ── Helpers ─────────────────────────────────────────────────────────────────
def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _default_store_path() -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "AirMouse", "license.json")


def _store_exists(store_path: str) -> bool:
    return store_path != ":memory:" and os.path.exists(store_path)


def _default_endpoints():
    raw = os.getenv("AIRMOUSE_LICENSE_URLS", "")
    return [u.strip() for u in raw.split(",") if u.strip()] or [
        "https://licenses.maouse.example.com"
    ]


_ACTIVE: "LicenseManager | None" = None


def set_active_license(manager: "LicenseManager") -> None:
    global _ACTIVE
    _ACTIVE = manager


def active_license() -> "LicenseManager":
    return _ACTIVE or LicenseManager()


def active_tier() -> Tier:
    return active_license().tier


__all__ = [
    "Tier", "PRO_LOCKED", "entitlements", "is_pro_locked",
    "LicenseManager", "LicenseAgency",
    "set_active_license", "active_license", "active_tier",
]
