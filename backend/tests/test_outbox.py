"""Outbox y eventos de dominio."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EstadoServicio
from app.core.eventos import EventoDominio, al_ocurrir, manejadores
from app.core.outbox import EventoSaliente, publicar

pytestmark = pytest.mark.integration


async def test_publicar_deja_el_evento_en_la_misma_transaccion(db: AsyncSession):
    publicar(db, EventoDominio(nombre="servicio.completado", datos={"servicio_id": "abc"}))
    await db.flush()

    fila = await db.scalar(select(EventoSaliente))
    assert fila is not None
    assert fila.nombre == "servicio.completado"
    assert fila.datos == {"servicio_id": "abc"}
    assert fila.procesado_en is None
    assert fila.intentos == 0


async def test_el_evento_se_va_con_el_rollback(db: AsyncSession):
    """El punto entero del outbox: si la transaccion no cuaja, el efecto externo
    tampoco. Con `tarea.delay()` el mensaje ya habria salido."""
    savepoint = await db.begin_nested()
    publicar(db, EventoDominio(nombre="servicio.cancelado"))
    await db.flush()
    await savepoint.rollback()

    assert await db.scalar(select(EventoSaliente)) is None


@pytest.mark.unit
def test_la_maquina_de_estados_publica_al_transicionar():
    from app.modules.servicios.state_machine import aplicar

    class SesionFalsa:
        def __init__(self):
            self.agregados = []

        def add(self, obj):
            self.agregados.append(obj)

    class ServicioFalso:
        id = "s-1"
        estado = EstadoServicio.AGENDADO

    db, servicio = SesionFalsa(), ServicioFalso()
    evento = aplicar(db, servicio, EstadoServicio.EN_RUTA)

    assert servicio.estado is EstadoServicio.EN_RUTA
    assert evento.nombre == "servicio.en_ruta"
    assert evento.datos["estado_anterior"] == "agendado"
    assert len(db.agregados) == 1, "la transicion debe dejar el evento en el outbox"


@pytest.mark.unit
def test_transicion_invalida_no_publica_nada():
    from app.modules.servicios.state_machine import TransicionInvalida, aplicar

    class SesionFalsa:
        def __init__(self):
            self.agregados = []

        def add(self, obj):
            self.agregados.append(obj)

    class ServicioFalso:
        id = "s-1"
        estado = EstadoServicio.COMPLETADO

    db, servicio = SesionFalsa(), ServicioFalso()
    with pytest.raises(TransicionInvalida):
        aplicar(db, servicio, EstadoServicio.EN_RUTA)
    assert db.agregados == []
    assert servicio.estado is EstadoServicio.COMPLETADO


@pytest.mark.unit
def test_registro_de_manejadores():
    @al_ocurrir("prueba.ocurrida")
    def _manejador(evento: EventoDominio) -> None:
        pass

    assert _manejador in manejadores("prueba.ocurrida")
    assert manejadores("prueba.inexistente") == []
