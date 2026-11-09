"""Ciclo de vida de la familia afiliada: los casos de uso que cruzan la ficha (familias) con
el contrato (cartera, planes), los preventivos y el embudo comercial.

`familias` es la ficha y no conoce a ningun dominio de arriba; estos casos de uso la
orquestan con el resto en la misma transaccion. Van sincronos a proposito, no por eventos
del outbox: validar el plan tiene que poder rechazar el alta en la misma peticion, y la baja
cancela el contrato en la misma transaccion que la marca (ver docs/deuda-ciclos-dominios.md).
"""

from sqlalchemy.orm import Session

from app.core.errores import Conflicto, ReglaNegocio
from app.core.tiempo import hoy
from app.modules.cartera import service as cartera
from app.modules.comercial import service as comercial
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import FormularioFamilia, MascotaCreate, ResultadoFormulario
from app.modules.planes import service as planes
from app.modules.preventivos import service as preventivos


def dar_de_baja(db: Session, familia: Familia, motivo: str) -> Familia:
    """F1-FAM-01 Baja de la familia: cancela antes su contrato vigente. Sin esto seguiria
    vigente: cuotas, avisos de mora y cobro a la tarjeta de una familia que ya se fue."""
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia ya esta dada de baja")
    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is not None:
        cartera.cancelar(db, contrato, f"Baja de la familia: {motivo}")
    return familias.dar_de_baja(db, familia, motivo)


def agregar_mascota(db: Session, familia: Familia, data: MascotaCreate) -> Mascota:
    """F1-FAM-02 Alta de mascota. Con contrato vigente, antes de guardarla debe caber en el
    plan (o pagar el adicional que defina la regla) y ser de una especie que cubre
    (F1-PLA-03); una vez dentro recibe su calendario preventivo (F1-AFI-03)."""
    mascota = familias.nueva_mascota(db, familia, data)
    afiliada = _validar_contra_plan(db, familia, mascota)
    familias.incorporar_mascota(db, familia, mascota)
    if afiliada:
        preventivos.calendario_inicial(db, mascota, hoy())
    return mascota


def _validar_contra_plan(db: Session, familia: Familia, mascota: Mascota) -> bool:
    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is None:
        return False
    plan = planes.obtener(db, contrato.plan_id)
    if plan.especies and mascota.especie not in plan.especies:
        raise ReglaNegocio(f"El plan {plan.nombre} no cubre la especie {mascota.especie}")
    planes.ajustar_por_mascotas(db, familia, "mascota_alta")
    return True


def dar_de_baja_mascota(db: Session, mascota: Mascota, motivo: str) -> Mascota:
    """Baja de mascota: el contrato vigente se recalcula sin ella desde la siguiente cuota."""
    familias.dar_de_baja_mascota(db, mascota, motivo)
    planes.ajustar_por_mascotas(db, familias.obtener(db, mascota.familia_id), "mascota_baja")
    return mascota


def anonimizar(db: Session, familia: Familia) -> Familia:
    """Habeas data (Ley 1581). La base tambien se niega con un contrato vigente, pero con el
    mismo error que para una familia ya anonimizada: aqui se distinguen para el mensaje."""
    if familia.anonimizada_en is not None:
        raise Conflicto("La familia ya esta anonimizada")
    if planes.contrato_vigente(db, familia.id) is not None:
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
