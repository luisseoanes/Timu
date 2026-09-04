import pytest

from app.core.enums import EstadoServicio as E
from app.modules.servicios.state_machine import TransicionInvalida, transicionar


def test_flujo_normal():
    assert transicionar(E.SOLICITADO, E.AGENDADO) is E.AGENDADO
    assert transicionar(E.AGENDADO, E.EN_RUTA) is E.EN_RUTA
    assert transicionar(E.EN_ATENCION, E.COMPLETADO) is E.COMPLETADO


def test_transicion_invalida():
    with pytest.raises(TransicionInvalida):
        transicionar(E.COMPLETADO, E.AGENDADO)
