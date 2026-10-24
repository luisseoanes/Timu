"""Constructores de datos de prueba para planes, familias, contratos y plantillas."""

from datetime import date
from itertools import count

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.cartera import service as cartera
from app.modules.cartera.models import Contrato
from app.modules.comunicaciones.models import PlantillaWhatsApp
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Beneficio, Plan

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
) -> Plan:
    p = Plan(
        codigo=codigo,
        nombre=f"Plan {codigo}",
        valor_mensual=valor,
        cupos_mascotas=cupos,
        ciudad=ciudad,
        especies=[],
    )
    p.beneficios = [Beneficio(**b) for b in beneficios or []]
    db.add(p)
    db.flush()
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
    )
    f.mascotas = [Mascota(nombre=f"Mascota{i}", especie="canino") for i in range(mascotas)]
    db.add(f)
    db.flush()
    return f


async def afiliada(
    db: AsyncSession, inicio: date, p: Plan | None = None, **kwargs
) -> tuple[Familia, Contrato]:
    f = await db.run_sync(familia, **kwargs)
    p = p or await db.run_sync(plan, codigo=f"plan_{f.documento}")
    contrato, _ = await db.run_sync(cartera.crear_contrato, f, p, fecha_inicio=inicio)
    return f, contrato
