"""F0-11 Subida validada de archivos.

El tipo se verifica por la firma de los primeros bytes, no por la extension ni por el
Content-Type que declara el cliente.
"""

import hashlib
import re
from datetime import date
from uuid import UUID, uuid4

from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.errores import ReglaNegocio
from app.integrations import storage
from app.modules.archivos.models import Archivo

_FIRMAS: dict[str, tuple[bytes, ...]] = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),  # + "WEBP" en el byte 8, se valida abajo
    "application/pdf": (b"%PDF-",),
}

_EXTENSIONES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}


class Politica(BaseModel):
    tipos: frozenset[str]
    max_mb: int


POLITICAS: dict[str, Politica] = {
    "foto_mascota": Politica(tipos=frozenset({"image/jpeg", "image/png", "image/webp"}), max_mb=5),
    "adjunto_clinico": Politica(
        tipos=frozenset({"image/jpeg", "image/png", "image/webp", "application/pdf"}), max_mb=10
    ),
    "documento": Politica(tipos=frozenset({"application/pdf"}), max_mb=10),
}


def nombre_seguro(nombre: str) -> str:
    """Sin rutas, comillas ni saltos de linea: el nombre viaja en Content-Disposition."""
    base = nombre.replace("\\", "/").rsplit("/", 1)[-1]
    limpio = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
    return (limpio or "archivo")[:120]


def detectar_tipo(contenido: bytes) -> str | None:
    for tipo, firmas in _FIRMAS.items():
        if any(contenido.startswith(f) for f in firmas):
            if tipo == "image/webp" and contenido[8:12] != b"WEBP":
                continue
            return tipo
    return None


def guardar_bytes(
    db: Session,
    *,
    contenido: bytes,
    nombre: str,
    proposito: str,
    usuario_id: UUID | None,
) -> Archivo:
    """Guarda contenido generado por el sistema (PDF de contrato, carnet) o ya validado."""
    tipo = detectar_tipo(contenido) or "application/octet-stream"
    hoy = date.today()
    clave = f"{proposito}/{hoy:%Y/%m}/{uuid4().hex}.{_EXTENSIONES.get(tipo, 'bin')}"
    storage.guardar_contenido(contenido, clave=clave, content_type=tipo)
    archivo = Archivo(
        clave=clave,
        proposito=proposito,
        nombre_original=nombre_seguro(nombre),
        content_type=tipo,
        tamano_bytes=len(contenido),
        sha256=hashlib.sha256(contenido).hexdigest(),
        subido_por_id=usuario_id,
    )
    db.add(archivo)
    db.flush()
    return archivo


async def leer(archivo: UploadFile, proposito: str) -> bytes:
    """Lee la carga en el endpoint (es E/S async) sin pasar del tope de la politica: un
    byte de mas basta para saber que se excede."""
    return await archivo.read(POLITICAS[proposito].max_mb * 1024 * 1024 + 1)


def subir(
    db: Session, contenido: bytes, *, nombre: str | None, proposito: str, usuario_id: UUID | None
) -> Archivo:
    politica = POLITICAS[proposito]
    limite = politica.max_mb * 1024 * 1024
    if len(contenido) > limite:
        raise ReglaNegocio(f"El archivo supera el maximo de {politica.max_mb} MB")
    if not contenido:
        raise ReglaNegocio("El archivo esta vacio")
    tipo = detectar_tipo(contenido)
    if tipo not in politica.tipos:
        permitidos = ", ".join(sorted(_EXTENSIONES[t] for t in politica.tipos))
        raise ReglaNegocio(f"Tipo de archivo no permitido. Se aceptan: {permitidos}")
    return guardar_bytes(
        db,
        contenido=contenido,
        nombre=nombre or f"archivo.{_EXTENSIONES[tipo]}",
        proposito=proposito,
        usuario_id=usuario_id,
    )


def url(archivo: Archivo) -> str:
    return storage.url_firmada(archivo.clave, nombre=archivo.nombre_original)
