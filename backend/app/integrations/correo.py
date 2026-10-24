"""Correo saliente por SMTP. Sin servidor configurado se registra en el log y no se envia."""

import smtplib
from email.message import EmailMessage

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ErrorCorreo(Exception):
    def __init__(self, mensaje: str, *, temporal: bool) -> None:
        super().__init__(mensaje)
        self.temporal = temporal


def configurado() -> bool:
    return bool(settings.SMTP_HOST)


def _enviar(destino: str, asunto: str, cuerpo: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except smtplib.SMTPRecipientsRefused as e:
        raise ErrorCorreo(f"Destinatario rechazado: {destino}", temporal=False) from e
    except (smtplib.SMTPException, OSError) as e:
        raise ErrorCorreo(str(e), temporal=True) from e


def enviar(destino: str, asunto: str, cuerpo: str) -> str:
    if not configurado():
        logger.warning("SMTP sin configurar; correo a %s no enviado: %s", destino, asunto)
        return "no_configurado"
    _enviar(destino, asunto, cuerpo)
    return "enviado"
