"""R3-PUB-04 Los datos de TIMU: una sola fila, que la migracion 0053 crea vacia."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.institucional.models import DatosTimu


def obtener(db: Session) -> DatosTimu:
    datos = db.scalar(select(DatosTimu))
    if datos is None:  # pragma: no cover - la migracion la crea; falla cerrado si falta
        raise RuntimeError("datos_timu sin su fila: falta aplicar la migracion 0053")
    return datos


def actualizar(db: Session, cambios: dict[str, Any]) -> DatosTimu:
    datos = obtener(db)
    for campo, valor in cambios.items():
        setattr(datos, campo, valor)
    db.flush()
    return datos


def whatsapp(db: Session) -> str | None:
    """El numero de contacto publico, o None si TIMU no lo ha escrito."""
    return obtener(db).whatsapp
