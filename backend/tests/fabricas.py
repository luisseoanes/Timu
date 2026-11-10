"""Constructores de datos de prueba para planes, familias, contratos y plantillas."""

from datetime import date
from itertools import count

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from app.modules.cartera import service as cartera
from app.modules.cartera.models import Contrato
from app.modules.catalogos.models import Ciudad
from app.modules.comunicaciones.models import PlantillaWhatsApp
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import (
    Beneficio,
    CiudadPlan,
    Plan,
    TarifaPeriodicidad,
    TarifaPlan,
)

_documentos = count(70_000_000)

# Plantillas que usan los procesos automaticos, con su numero de variables.
PLANTILLAS = {
    "cuota_vencida": 3,
    "aviso_mora": 3,
    "aviso_congelamiento": 3,
    "afiliacion_congelada": 1,
    "afiliacion_reactivada": 1,
    "bienvenida": 2,
    "activar_cuenta": 2,
    "recuperar_clave": 2,
    "completar_afiliacion": 2,
}


def plantillas_aprobadas(db: Session) -> None:
    for nombre, n in PLANTILLAS.items():
        cuerpo = " ".join(f"{{{{{i}}}}}" for i in range(1, n + 1))
        db.add(
            PlantillaWhatsApp(
                nombre=nombre,
                cuerpo=f"{nombre}: {cuerpo}",
                variables=[f"v{i}" for i in range(1, n + 1)],
                estado_aprobacion="aprobada",
                activa=True,
            )
        )
    db.flush()


def plan(
    db: Session,
    codigo: str = "individual",
    valor: int = 45_000,
    cupos: int = 1,
    ciudad: str | None = None,
    beneficios: list[dict] | None = None,
    tarifas: list[int] | None = None,
    largos: dict[str, int] | None = None,
) -> Plan:
    """Plan con el mismo valor para 1 a 4 peludos (`cupos` ya no limita: se conserva por
    las llamadas existentes). Sin `ciudad`, se vende en todas las del catalogo."""
    p = Plan(codigo=codigo, nombre=f"Plan {codigo}", especies=[])
    p.beneficios = [Beneficio(**b) for b in beneficios or []]
    db.add(p)
    db.flush()
    por_peludos = tarifas or [valor] * 4
    db.add_all(
        TarifaPlan(plan_id=p.id, peludos=n, valor=v) for n, v in enumerate(por_peludos, start=1)
    )
    db.add_all(
        TarifaPeriodicidad(plan_id=p.id, periodicidad=k, valor=v) for k, v in (largos or {}).items()
    )
    ciudades = [ciudad] if ciudad else list(db.scalars(select(Ciudad.nombre)))
    db.add_all(CiudadPlan(plan_id=p.id, ciudad=c) for c in ciudades)
    db.flush()
    db.refresh(p, ["tarifas", "tarifas_periodicidad", "ciudades"])
    return p


def familia(
    db: Session,
    mascotas: int = 1,
    ciudad: str = "Cali",
    telefono: str = "+573001112233",
    email: str | None = None,
) -> Familia:
    f = Familia(
        titular_nombre="Ana Ruiz",
        tipo_documento="CC",
        documento=str(next(_documentos)),
        telefono=telefono,
        email=email,
        ciudad=ciudad,
        barrio="El Poblado",
    )
    f.mascotas = [Mascota(nombre=f"Mascota{i}", especie="canino") for i in range(mascotas)]
    # Recien creada no tiene contactos; asi la relacion queda cargada, como al leerla de la base.
    set_committed_value(f, "contactos", [])
    db.add(f)
    db.flush()
    return f


async def afiliada(
    db: AsyncSession,
    inicio: date,
    p: Plan | None = None,
    periodicidad: str = "mensual",
    **kwargs,
) -> tuple[Familia, Contrato]:
    """Familia con contrato vigente: todos sus peludos en el plan `p`."""
    f = await db.run_sync(familia, **kwargs)
    p = p or await db.run_sync(plan, codigo=f"plan_{f.documento}")
    planes = {m.id: p.id for m in f.mascotas}
    contrato, _ = await db.run_sync(
        lambda s: cartera.crear_contrato(
            s, f, planes, periodicidad=periodicidad, fecha_inicio=inicio
        )
    )
    return f, contrato
