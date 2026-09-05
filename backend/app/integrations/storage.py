"""F0-11 Almacenamiento de adjuntos clinicos (6.14), compatible S3.

El cliente todavia no entrego el bucket, y esperarlo seria construir un apano local
que luego habria que tirar. En su lugar hablamos S3 desde el primer dia contra MinIO
—que implementa el mismo protocolo— levantado en docker compose. El dia que llegue el
S3 real se cambian cuatro variables de entorno y no se toca una linea de codigo.

Nada se sirve publico: los adjuntos se entregan con URL firmada de vida corta
(STORAGE_URL_TTL_SEGUNDOS), como exige el criterio de aceptacion de F0-11.
"""

from __future__ import annotations

from functools import lru_cache
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


@lru_cache
def _cliente():
    return boto3.client(
        "s3",
        endpoint_url=settings.STORAGE_ENDPOINT_URL,  # None => AWS S3 real
        region_name=settings.STORAGE_REGION,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def asegurar_bucket() -> None:
    """Crea el bucket si no existe. Solo para desarrollo con MinIO; en produccion el
    bucket lo aprovisiona quien administra la cuenta."""
    cliente = _cliente()
    try:
        cliente.head_bucket(Bucket=settings.STORAGE_BUCKET)
    except ClientError:
        cliente.create_bucket(Bucket=settings.STORAGE_BUCKET)


def guardar(fichero: BinaryIO, *, nombre: str, content_type: str, prefijo: str = "adjuntos") -> str:
    """Sube el fichero y devuelve su clave. La clave lleva un uuid para que dos
    adjuntos con el mismo nombre no se pisen."""
    clave = f"{prefijo}/{uuid4()}/{nombre}"
    _cliente().upload_fileobj(
        fichero, settings.STORAGE_BUCKET, clave, ExtraArgs={"ContentType": content_type}
    )
    return clave


def url_firmada(clave: str, *, ttl: int | None = None) -> str:
    """URL temporal de lectura. Nunca se devuelve al cliente la clave desnuda."""
    return _cliente().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.STORAGE_BUCKET, "Key": clave},
        ExpiresIn=ttl or settings.STORAGE_URL_TTL_SEGUNDOS,
    )


def eliminar(clave: str) -> None:
    _cliente().delete_object(Bucket=settings.STORAGE_BUCKET, Key=clave)
