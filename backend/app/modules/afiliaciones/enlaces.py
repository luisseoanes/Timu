"""6.1 Enlace al formulario posterior al pago del registro en linea.

Cada enlace nuevo sustituye al anterior (el token del navegador que pago sigue valiendo).
El token solo se guarda como SHA-256.
"""

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import ReglaNegocio
from app.core.security import generar_token_opaco, hash_token
from app.modules.afiliaciones.models import SolicitudAfiliacion
from app.modules.comunicaciones import service as comunicaciones

logger = structlog.get_logger(__name__)

PLANTILLA = "completar_afiliacion"


def url_formulario(token: str) -> str:
    return f"{settings.FRONTEND_URL}/afiliacion/completar?token={token}"


def enviar(db: Session, solicitud: SolicitudAfiliacion) -> str:
    """Emite un enlace nuevo y lo envia al contacto por correo y por WhatsApp."""
    token = generar_token_opaco()
    solicitud.token_enlace_hash = hash_token(token)
    enlace = url_formulario(token)
    nombre = solicitud.contacto_nombre or "familia TIMU"
    if solicitud.contacto_email:
        comunicaciones.encolar_correo(
            db,
            email=solicitud.contacto_email,
            asunto="Completa la afiliacion de tus peludos",
            cuerpo=(
                f"Hola {nombre},\n\nRecibimos tu pago. Para activar la afiliacion, completa los "
                f"datos de tu familia y de tus peludos en este enlace:\n{enlace}\n\nEquipo TIMU"
            ),
        )
    if solicitud.contacto_telefono:
        try:
            comunicaciones.encolar_plantilla(
                db,
                telefono=solicitud.contacto_telefono,
                plantilla=PLANTILLA,
                variables=[nombre, enlace],
            )
        except ReglaNegocio as e:
            logger.error("Enlace de registro sin WhatsApp para %s: %s", solicitud.id, e)
    db.flush()
    return token
