"""Validação de compras IAP (Google Play) via Android Publisher API.

Usa o purchaseToken do cliente para validar na Google Play Developer API.
A conta de serviço é fornecida por env (JSON) e usada para emitir um token
OAuth 2.0. A validação real só acontece se as credenciais estiverem
configuradas; caso contrário comporta-se em modo dev (aceita tokens de teste)
apenas se AIRMOUSE_MOBILE_DEV_ALLOW=1.

Ambiente:
  AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON  -> conteúdo JSON da conta de serviço
  AIRMOUSE_MOBILE_DEV_ALLOW              -> "1" para aceitar tokens de teste
"""
import json
import os

import requests

_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
_API = ("https://androidpublisher.googleapis.com/androidpublisher/v3/"
        "applications/{pkg}/purchases/products/{pid}/tokens/{tok}")


class PlayValidationError(Exception):
    """Erro de validação contra a Google Play (token inválido, expirado ou
    permissão em falta)."""


def _credentials_configured() -> bool:
    return bool(os.getenv("AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON", ""))


def _dev_allowed() -> bool:
    return os.getenv("AIRMOUSE_MOBILE_DEV_ALLOW", "") == "1"


def _service_credentials() -> dict:
    raw = os.getenv("AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON", "")
    try:
        return json.loads(raw)
    except ValueError:
        raise PlayValidationError("credenciais_invalidas") from None


def _access_token() -> str:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_info(
        _service_credentials(), scopes=[_SCOPE])
    creds.refresh(Request())
    return creds.token


def validate_purchase(package_name: str, product_id: str,
                      purchase_token: str) -> str:
    """Valida um purchaseToken na Google Play.

    Devolve "" se a compra for válida; levanta PlayValidationError com uma
    mensagem curta quando o token é rejeitado (ou o produto não é uma compra
    válida e consumível)."""
    if not _credentials_configured():
        if _dev_allowed():
            # Modo dev: aceita tokens de teste (nunca em produção real).
            if purchase_token.startswith("test_"):
                return ""
            raise PlayValidationError("token_invalido_dev")
        raise PlayValidationError("play_nao_configurado")
    url = _API.format(pkg=package_name, pid=product_id, tok=purchase_token)
    headers = {"Authorization": f"Bearer {_access_token()}"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        body = resp.json()
        state = body.get("purchaseState", 0)
        # 0 = comprado; 1 = cancelado; 2 = pendente
        if state == 0:
            return ""
        raise PlayValidationError("compra_nao_concluida")
    if resp.status_code == 404:
        raise PlayValidationError("token_invalido")
    if resp.status_code in (401, 403):
        raise PlayValidationError("permissao_play")
    raise PlayValidationError("play_api_erro")
