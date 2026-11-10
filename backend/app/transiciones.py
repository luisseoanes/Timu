"""Grafos de estados que la base hace cumplir (fase 2e de docs/plan-persistencia.md).

Cada servicio sigue validando sus transiciones antes, para devolver un mensaje claro; el
trigger `validar_transicion` rechaza en la base cualquier cambio de estado que no este
aqui, lo haga quien lo haga. Las migraciones escriben estas aristas en la tabla
`transiciones_estado`, y `test_persistencia` falla si la tabla y este modulo no coinciden.

Fuera a proposito: estados que cambian por informacion externa o por decision libre del
equipo (mensajes y pagos segun lo que reporten Meta y la pasarela, cuotas, estado de
afiliacion por reglas de cartera, etapa del embudo, aprobacion de plantillas de Meta).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDMixin
from app.modules.servicios.models import EstadoPendiente as P
from app.modules.servicios.state_machine import TRANSICIONES as _SERVICIOS

Grafo = dict[str, set[str]]


class TransicionEstado(Base, UUIDMixin):
    """Una arista permitida. Solo el dueno del esquema la escribe (migraciones); el trigger
    la lee con SECURITY DEFINER, asi que la aplicacion no puede ampliar sus propios grafos."""

    __tablename__ = "transiciones_estado"
    __unicos__ = {"arista": (["tabla", "columna", "desde", "hacia"], None)}

    tabla: Mapped[str] = mapped_column(String(64))
    columna: Mapped[str] = mapped_column(String(64))
    desde: Mapped[str] = mapped_column(String(40))
    hacia: Mapped[str] = mapped_column(String(40))


TRANSICIONES: dict[tuple[str, str], Grafo] = {
    ("servicios", "estado"): {d.value: {h.value for h in hs} for d, hs in _SERVICIOS.items()},
    ("pendientes", "estado"): {
        P.PENDIENTE_AUTORIZACION: {P.AUTORIZADO, P.RECHAZADO},
        P.AUTORIZADO: {P.EN_GESTION, P.RESUELTO},
        P.EN_GESTION: {P.RESUELTO},
    },
    ("tareas", "estado"): {"abierta": {"en_progreso", "cerrada"}, "en_progreso": {"cerrada"}},
    ("historias_clinicas", "estado"): {"borrador": {"firmada"}, "firmada": {"corregida"}},
    ("remisiones_aliadas", "estado"): {"emitida": {"utilizada", "anulada"}},
    ("rutas", "estado"): {
        # Planificada a finalizada: todas sus paradas omitidas antes de arrancar.
        "planificada": {"en_curso", "cancelada", "finalizada"},
        "en_curso": {"finalizada"},
    },
    ("paradas_ruta", "estado"): {
        "pendiente": {"en_camino", "en_sitio", "omitida"},
        "en_camino": {"en_sitio"},
        "en_sitio": {"completada"},
    },
    ("planificaciones_ruta", "estado"): {"pendiente": {"lista", "fallida"}},
    ("eventos_preventivos", "estado"): {"programado": {"aplicado", "cancelado"}},
    ("solicitudes_virtuales", "estado"): {
        "en_cola": {"en_atencion"},
        "en_atencion": {"respondida"},
        "respondida": {"cerrada"},
    },
    ("respuestas_virtuales", "estado"): {"borrador": {"aprobada"}},
    ("prompts_ia", "estado"): {
        "borrador": {"activo"},
        "activo": {"retirado"},
        "retirado": {"activo"},
    },
    ("encuestas", "estado"): {"pendiente": {"enviada", "omitida"}, "enviada": {"respondida"}},
    ("campanas", "estado"): {
        "borrador": {"programada", "en_envio", "cancelada"},
        "programada": {"en_envio", "cancelada"},
        "en_envio": {"programada", "finalizada", "cancelada"},
    },
    ("ejecuciones_campana", "estado"): {"en_envio": {"terminada", "cancelada"}},
    ("destinatarios_campana", "estado"): {"pendiente": {"encolado", "excluido"}},
    ("solicitudes_afiliacion", "estado"): {
        "pendiente_pago": {"pagada", "completada", "cancelada", "error"},
        # Registro en linea: el formulario la completa, o queda para el equipo.
        "pagada": {"completada", "error"},
        # Un pago que se aprueba despues de marcar el error completa la afiliacion.
        "error": {"completada"},
    },
}


def aristas() -> set[tuple[str, str, str, str]]:
    """(tabla, columna, desde, hacia) de todos los grafos."""
    return {
        (tabla, columna, str(desde), str(hacia))
        for (tabla, columna), grafo in TRANSICIONES.items()
        for desde, destinos in grafo.items()
        for hacia in destinos
    }
