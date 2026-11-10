"""Ciclo de vida de la familia afiliada: los casos de uso que cruzan la ficha (familias) con
el contrato (cartera, planes), los preventivos y el embudo comercial.

`familias` es la ficha y no conoce a ningun dominio de arriba; estos casos de uso la
orquestan con el resto en la misma transaccion. Van sincronos a proposito, no por eventos
del outbox: validar el plan tiene que poder rechazar el alta en la misma peticion, y la baja
cancela el contrato en la misma transaccion que la marca (ver docs/deuda-ciclos-dominios.md).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errores import Conflicto, ReglaNegocio
from app.core.tiempo import hoy
from app.modules.cartera import contratos
from app.modules.cartera import service as cartera
from app.modules.comercial import service as comercial
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import FormularioFamilia, MascotaCreate, ResultadoFormulario
from app.modules.preventivos import service as preventivos


def dar_de_baja(db: Session, familia: Familia, motivo: str) -> Familia:
    """F1-FAM-01 Baja de la familia: cancela antes su contrato vigente. Sin esto seguiria
    vigente: cuotas, avisos de mora y cobro a la tarjeta de una familia que ya se fue."""
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia ya esta dada de baja")
    contrato = contratos.contrato_vigente(db, familia.id)
    if contrato is not None:
        cartera.cancelar(db, contrato, f"Baja de la familia: {motivo}")
    return familias.dar_de_baja(db, familia, motivo)


def agregar_mascota(
    db: Session,
    familia: Familia,
    data: MascotaCreate,
    plan_id: UUID | None = None,
    usuario_id: UUID | None = None,
) -> Mascota:
    """F1-FAM-02 Alta de mascota. Con contrato vigente y `plan_id`, entra al contrato con su
    plan: antes de guardarla se valida que el plan se venda en la ciudad y cubra su especie,
    y despues todos pasan a la tarifa del nuevo numero de peludos desde la siguiente cuota
    (6.3). Recibe su calendario preventivo (F1-AFI-03).

    Sin `plan_id` (un formulario publico que completa la ficha) queda en la ficha sin
    afiliar: sin beneficios hasta que el equipo la afilie."""
    contrato = contratos.contrato_vigente(db, familia.id)
    afiliar = contrato is not None and plan_id is not None
    if afiliar:
        assert contrato is not None and plan_id is not None
        contratos.validar_alta(db, contrato, data.especie, plan_id)
    mascota = familias.nueva_mascota(db, familia, data)
    familias.incorporar_mascota(db, familia, mascota)
    if afiliar:
        assert contrato is not None and plan_id is not None
        contratos.agregar_mascota(db, contrato, mascota, plan_id, usuario_id)
        preventivos.calendario_inicial(db, mascota, hoy())
    return mascota


def alta_desde_panel(
    db: Session, familia: Familia, data: MascotaCreate, plan_id: UUID | None, usuario_id: UUID
) -> Mascota:
    """Desde el panel, con contrato vigente hay que elegir el plan de la mascota nueva: si no,
    quedaria fuera de la afiliacion sin que nadie lo decida."""
    if plan_id is None and contratos.contrato_vigente(db, familia.id) is not None:
        raise ReglaNegocio("Elige el plan de la mascota: la familia tiene una afiliacion vigente")
    return agregar_mascota(db, familia, data, plan_id, usuario_id)


def dar_de_baja_mascota(
    db: Session, mascota: Mascota, motivo: str, usuario_id: UUID | None = None
) -> Mascota:
    """Baja de mascota: sale del contrato vigente y los demas peludos pasan a la tarifa del
    nuevo numero desde la siguiente cuota. Si es el unico peludo, hay que cancelar el
    contrato."""
    contrato = contratos.contrato_vigente(db, mascota.familia_id)
    if contrato is not None:
        contratos.retirar_mascota(db, contrato, mascota.id, usuario_id)
    familias.dar_de_baja_mascota(db, mascota, motivo)
    return mascota


def anonimizar(db: Session, familia: Familia) -> Familia:
    """Habeas data (Ley 1581). La base tambien se niega con un contrato vigente, pero con el
    mismo error que para una familia ya anonimizada: aqui se distinguen para el mensaje."""
    if familia.anonimizada_en is not None:
        raise Conflicto("La familia ya esta anonimizada")
    if contratos.contrato_vigente(db, familia.id) is not None:
        raise ReglaNegocio("Cancele el contrato vigente antes de anonimizar la familia")
    return familias.anonimizar(db, familia)


def recibir_formulario(db: Session, data: FormularioFamilia) -> ResultadoFormulario:
    """F1-FAM-03 Crea o completa el perfil desde un formulario publico y deja al interesado
    en el embudo comercial (F3-COM-01)."""
    resultado = familias.desde_formulario(db, data, agregar_mascota=agregar_mascota)
    comercial.registrar(
        db,
        origen=data.origen[:24],
        telefono=data.telefono,
        email=str(data.email) if data.email else None,
        nombre=data.titular_nombre,
        ciudad=data.ciudad,
        familia_id=resultado.familia_id,
        datos={"mascotas": [m.especie for m in data.mascotas]},
    )
    return resultado
