"""Licenciamento — Gate Free/Pro + validação de chave + Paddle checkout.

Módulo autónomo (100% offline na validação) que implementa o modelo
``Mãouse Pro`` definido em ``BUSSINES/DECISOES.md`` (D1/D2) e
``BUSSINES/MODELO_DE_NEGOCIO.md`` §11:

* **Free**: mover cursor, cliques, 1 mão, watermark. Pro-locked: snap,
  voz, duas mãos, TTS, IA, auto-afinação, luz baixa.
* **Pro**: tudo (lifetime €39,90 / sub €4,99·€3,49 / família €59,90).

A validação de chave é **offline-first** (privacidade: a câmara/voz nunca
saem do dispositivo), usando um serial assinado com HMAC-SHA256. O checkout
Paddle (Merchant of Record, que trata IVA/VAT UE — decisão D2) é lançado no
browser default via *Pay Links* configuráveis; a ativação pode ser confirmada
offline por chave ou online por webhook assinado (Paddle Verifier).
"""
import hashlib
import hmac
import json
import os
import webbrowser
from enum import Enum

# Chave de assinatura das chaves Pro. Em produção vem de env/ficheiro secreto;
# aqui fica um default de desenvolvimento (overridable por secret explícito ou
# pela variável de ambiente AIRMOUSE_LICENSE_SECRET).
_DEFAULT_SECRET = "AIRMOUSE-DEV-INSECURE-SECRET-CHANGE-ME"

# Produtos Paddle (Pay Links). Preencher com os IDs reais dos preços quando a
# entidade UE (D5) e o catálogo Paddle existirem.
PADDLE_PRODUCT_URLS = {
    "lifetime": os.environ.get("AIRMOUSE_PADDLE_LIFETIME_URL", ""),
    "subscription": os.environ.get("AIRMOUSE_PADDLE_SUBSCRIPTION_URL", ""),
    "family": os.environ.get("AIRMOUSE_PADDLE_FAMILY_URL", ""),
    "access": os.environ.get("AIRMOUSE_PADDLE_ACCESS_URL", ""),
}

_PREFIX = "MAO-"
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


class Tier(Enum):
    FREE = "free"
    PRO = "pro"


# Funcionalidades que são Pro-locked no Free. "move"/"click" são sempre livres.
PRO_LOCKED = (
    "snap",
    "voice",
    "two_hands",
    "tts",
    "ai",
    "autotune",
    "low_light",
)


def entitlements(tier: Tier) -> dict[str, bool]:
    """Devolve o mapa de funcionalidades permitidas para um tier."""
    base = {
        "move": True,
        "click": True,
    }
    pro_on = tier == Tier.PRO
    for feature in PRO_LOCKED:
        base[feature] = pro_on
    return base


def is_pro_locked(tier: Tier, feature: str) -> bool:
    return feature in PRO_LOCKED and tier != Tier.PRO


class LicenseManager:
    """Estado da licença + validação de chave offline + ação de checkout."""

    def __init__(self, secret: str = "", store_path: "str | None" = None,
                 agency: "LicenseAgency | None" = None):
        self._secret = secret or os.environ.get("AIRMOUSE_LICENSE_SECRET", _DEFAULT_SECRET)
        self._store_path = store_path or _default_store_path()
        self._agency = agency  # interface online opcional (Paddle)
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""

    # ── Persistência ──────────────────────────────────────────────────
    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
            with open(self._store_path, "w", encoding="utf-8") as fh:
                json.dump({
                    "tier": self.tier.value,
                    "key": self.key,
                    "email": self.email,
                    "sig": self._sign(f"{self.tier.value}:{self.key}:{self.email}"),
                }, fh, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        """Carrega o estado guardado. Recusa-se a honrar ficheiros adulterados:
        um store com sig inválido nunca concede Pro de graça."""
        try:
            with open(self._store_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return
        sig = data.get("sig", "")
        payload = f"{data.get('tier', '')}:{data.get('key', '')}:{data.get('email', '')}"
        if not hmac.compare_digest(sig, self._sign(payload)):
            return  # adulterado → mantém Free
        tier = Tier(data.get("tier", Tier.FREE.value))
        # Se for PRO, exige que a chave em si seja válida (não confiar no store).
        if tier == Tier.PRO:
            if not self.validate_key(data.get("key", "")):
                return
            self.tier = Tier.PRO
            self.key = data.get("key", "")
            self.email = data.get("email", "")
        else:
            self.tier = Tier.FREE
            self.key = ""
            self.email = ""

    # ── Assinatura HMAC ───────────────────────────────────────────────
    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret.encode(), payload.encode(),
                        hashlib.sha256).hexdigest()

    # ── Emissão / validação de chave (offline) ────────────────────────
    def issue_pro_key(self, email: str) -> str:
        """Emite uma chave Pro. Chamada apenas numa ferramenta de vendas, não
        pelo executável final. (Aqui para testes/ferramentas & demonstração.)
        O e-mail entra apenas como hash (sem caracteres especiais no corpo)."""
        email_hash = hmac.new(
            self._secret.encode(), email.lower().strip().encode(),
            hashlib.sha256,
        ).hexdigest()[:10].upper()
        nonce = os.urandom(6).hex().upper()
        doc = f"PRO{email_hash}{nonce}"
        sig = hmac.new(self._secret.encode(), doc.encode(),
                       hashlib.sha256).hexdigest()[:10].upper()
        return _format_key(doc + sig)

    def validate_key(self, key: str) -> bool:
        """Valida uma chave Offline (formato MAO-XXXX-...). Online opcional:
        se houver agency definido e o 'online' falhar na autenticidade, rejeita."""
        norm = _normalize_key(key)
        if not norm or not norm.startswith(_PREFIX.replace("-", "")):
            return False
        body = norm[3:].replace("-", "")
        if len(body) < 10:
            return False
        doc = body[:-10]
        sig = body[-10:]
        expected = hmac.new(self._secret.encode(), doc.encode(),
                            hashlib.sha256).hexdigest()[:10].upper()
        if not hmac.compare_digest(sig, expected):
            return False
        if not doc.startswith("PRO"):
            return False
        if self._agency is not None:
            if not self._agency.online_validate(doc):
                return False
        return True

    # ── Ativação ──────────────────────────────────────────────────────
    def activate(self, key: str) -> bool:
        if self.validate_key(key):
            self.tier = Tier.PRO
            self.key = _normalize_key(key)
            self.save()
            return True
        return False

    def deactivate(self) -> None:
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""
        if os.path.exists(self._store_path):
            try:
                os.remove(self._store_path)
            except OSError:
                pass

    @property
    def is_pro(self) -> bool:
        return self.tier == Tier.PRO

    def can(self, feature: str) -> bool:
        ent = entitlements(self.tier)
        return bool(ent.get(feature, True))

    # ── Paddle checkout (Merchant of Record decisão D2) ───────────────
    def checkout_urls(self, vendor_id: int) -> dict[str, str]:
        """Monta Pay Links a partir do catálogo configurado (ou fallback ao
        formato clássico de checkout quando ainda não há preço definido)."""
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


class LicenseAgency:
    """Interface opcional para validação ONLINE (ex. webhook Paddle assinado).

    Fornece a ponte para confirmar autenticidade servidor-a-servidor quando a
    ativação online estiver disponível; sem ela, a validação é offline-only.
    """

    def online_validate(self, license_doc: str) -> bool:
        """Implementar com o Paddle Verifier/webhook. Default: confiar em
        offline (sem agência → sem chamada de rede)."""
        return True


# ── Helpers ───────────────────────────────────────────────────────────
def _normalize_key(key: str) -> str:
    return "".join(ch.upper() for ch in (key or "") if ch.isalnum())


def _format_key(body: str) -> str:
    groups = [body[i:i + 5] for i in range(0, len(body), 5)]
    return _PREFIX + "-".join(groups)


def _default_store_path() -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "AirMouse", "license.json")


# Armazena o LicenseManager ativo, definido pelo main no arranque. Usado pelo
# runtime (UI, voz, snap) para bloquear toggles/ordens Pro-locked no tier Free.
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
