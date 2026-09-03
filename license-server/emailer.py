"""Envio de email com a chave Pro por SMTP (stdlib). Desligável em dev."""
import os
import smtplib
from email.message import EmailMessage
from typing import NamedTuple


class Result(NamedTuple):
    fired: bool
    error: str


def _cfg():
    return {
        "enabled": os.getenv("AIRMOUSE_SMTP_ENABLED", "0") == "1",
        "host": os.getenv("AIRMOUSE_SMTP_HOST", ""),
        "port": int(os.getenv("AIRMOUSE_SMTP_PORT", "587")),
        "user": os.getenv("AIRMOUSE_SMTP_USER", ""),
        "password": os.getenv("AIRMOUSE_SMTP_PASSWORD", ""),
        "from": os.getenv("AIRMOUSE_SMTP_FROM", "sales@maouse.app"),
    }


def build_key_email(to_email: str, key: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "A tua chave Maouse PRO"
    msg["From"] = _cfg()["from"]
    msg["To"] = to_email
    body = (
        "Obrigado pela tua compra!\n\n"
        "A tua chave Maouse PRO:\n\n"
        f"{key}\n\n"
        "Como ativar:\n"
        "1. Abre o Maouse e vai a PRO / Ativar chave\n"
        "2. Cola a chave e ativa (precisa de internet uma vez)\n\n"
        "A chave fica ligada ao teu computador. Precisas de ajuda?"
        " Responde a este email.\n\nMaouse"
    )
    msg.set_content(body)
    return msg


def send_key_email(to_email: str, key: str) -> Result:
    cfg = _cfg()
    if not cfg["enabled"]:
        return Result(fired=False, error="")
    try:
        msg = build_key_email(to_email, key)
        with smtplib.SMTP(cfg["host"], cfg["port"]) as srv:
            srv.starttls()
            srv.login(cfg["user"], cfg["password"])
            srv.sendmail(cfg["from"], [to_email], msg.as_string())
        return Result(fired=True, error="")
    except Exception as exc:  # noqa: BLE001 - o webhook não deve falhar por email
        return Result(fired=False, error=str(exc))
