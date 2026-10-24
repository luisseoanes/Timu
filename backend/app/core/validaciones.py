"""F1-FAM-04 Validaciones de datos colombianos, reutilizables como tipos de Pydantic.

- Telefono: se normaliza a E.164 (+57XXXXXXXXXX). Acepta espacios, guiones, parentesis y
  el indicativo con o sin '+'. Celulares (3XX) y fijos (60X) tienen 10 digitos.
- Documento: sin puntos, espacios ni guiones, en mayusculas. "1.020.304.050" y
  "1020304050" son el mismo documento y por tanto un duplicado.
"""

import re
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator

_NO_DIGITOS = re.compile(r"[\s\-().]")


class TipoDocumento(StrEnum):
    CC = "CC"  # cedula de ciudadania
    CE = "CE"  # cedula de extranjeria
    TI = "TI"  # tarjeta de identidad
    PA = "PA"  # pasaporte
    PPT = "PPT"  # permiso por proteccion temporal
    NIT = "NIT"


def normalizar_telefono(valor: str) -> str:
    limpio = _NO_DIGITOS.sub("", valor.strip())
    if limpio.startswith("+"):
        limpio = limpio[1:]
    if not limpio.isdigit():
        raise ValueError("El telefono solo puede contener digitos")
    if len(limpio) == 10:
        limpio = "57" + limpio
    if not (len(limpio) == 12 and limpio.startswith("57")):
        raise ValueError("Telefono colombiano invalido: se esperan 10 digitos (celular o fijo)")
    nacional = limpio[2:]
    if not (nacional.startswith("3") or nacional.startswith("60")):
        raise ValueError("El telefono debe ser un celular (3XX) o un fijo (60X)")
    return "+" + limpio


def normalizar_documento(valor: str) -> str:
    limpio = re.sub(r"[\s.\-]", "", valor).upper()
    if not re.fullmatch(r"[A-Z0-9]{4,20}", limpio):
        raise ValueError("Documento invalido: entre 4 y 20 letras o digitos")
    return limpio


def telefono_whatsapp(telefono_e164: str) -> str:
    """La API de Meta recibe el numero sin '+'."""
    return telefono_e164.lstrip("+")


TelefonoCO = Annotated[str, AfterValidator(normalizar_telefono)]
DocumentoCO = Annotated[str, AfterValidator(normalizar_documento)]
