"""Las plantillas de WhatsApp que envia la plataforma por su codigo (6.19).

Fuera de la ventana de 24 h, WhatsApp solo deja escribir con una plantilla registrada y aprobada en
Meta, y el codigo la cita por su nombre. Cada dominio declara aqui las que envia y para que, como
los eventos (`core/eventos.py`): asi Administracion puede decir cuales faltan en el catalogo y que
deja de enviarse sin ellas (`reglas.plantillas_faltantes`). Las que citan las reglas se leen de las
reglas; las de una campana las elige el equipo entre las aprobadas.
"""

from dataclasses import dataclass, field


@dataclass
class PlantillaDeclarada:
    codigo: str
    # Nombre para el equipo hasta que la plantilla se registre con el suyo (valor provisional).
    titulo: str
    # Lo que deja de enviarse por WhatsApp sin ella, en minuscula: «la bienvenida al afiliarse».
    usos: list[str] = field(default_factory=list)


_DECLARADAS: dict[str, PlantillaDeclarada] = {}


def declarar_plantilla(codigo: str, titulo: str, uso: str) -> str:
    """Declara una plantilla que el dominio envia y devuelve su codigo para usarlo como constante:
    `PLANTILLA_BIENVENIDA = declarar_plantilla("bienvenida", "Bienvenida", "la bienvenida")`."""
    declarada = _DECLARADAS.setdefault(codigo, PlantillaDeclarada(codigo, titulo))
    if uso not in declarada.usos:
        declarada.usos.append(uso)
    return codigo


def plantillas_declaradas() -> dict[str, PlantillaDeclarada]:
    return dict(_DECLARADAS)
