"""6.1 Agregar un peludo desde el portal con el contrato vigente: se paga la parte del periodo
en curso y el peludo entra al contrato cuando la pasarela aprueba el pago."""

from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings
from app.core.enums import Rol
from app.core.security import hash_password
from app.core.tiempo import hoy
from app.modules.afiliaciones.models import AltaPeludo
from app.modules.auth.models import Usuario
from app.modules.cartera import contratos, pasarela
from app.modules.cartera import service as cartera
from app.modules.cartera.models import AfiliacionMascota, Contrato, Cuota, Pago
from app.modules.familias.models import Mascota
from app.modules.preventivos.models import EventoPreventivo
from app.modules.tareas.models import Tarea
from tests import fabricas
from tests.conftest import PASSWORD, login
from tests.test_cartera import _evento

pytestmark = pytest.mark.integration

API = "/api/v1/portal/peludos"


async def _familia_portal(db, plan, telefono: str, email: str):
    # A mitad de periodo: el alta paga los dias que quedan.
    familia, contrato = await fabricas.afiliada(
        db, hoy() - timedelta(days=10), plan, telefono=telefono
    )
    usuario = Usuario(
        email=email,
        telefono=telefono,
        nombre=familia.titular_nombre,
        rol=Rol.FAMILIA,
        hashed_password=hash_password(PASSWORD),
    )
    db.add(usuario)
    await db.flush()
    familia.usuario_portal_id = usuario.id
    await db.flush()
    return familia, contrato


@pytest.fixture
async def portal(client: AsyncClient, db, monkeypatch):
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "secreto-eventos")
    monkeypatch.setattr(settings, "WOMPI_INTEGRITY_SECRET", "secreto-integridad")
    # Un peludo paga 40.000; con dos, cada uno paga 35.000.
    plan = await db.run_sync(fabricas.plan, "amigo", tarifas=[40_000, 35_000, 30_000, 25_000])
    familia, contrato = await _familia_portal(db, plan, "+573001110001", "ana@correo.co")
    await _familia_portal(db, plan, "+573001110002", "beto@correo.co")
    ids = {"familia_id": familia.id, "contrato_id": contrato.id}
    await db.commit()
    return {
        **ids,
        "plan_id": str(plan.id),
        "headers": await login(client, "ana@correo.co"),
    }


def _peludo(portal, **cambios) -> dict:
    return {
        "nombre": "Kira",
        "especie": "canino",
        "raza": "Criolla",
        "sexo": "hembra",
        "fecha_nacimiento": "2023-01-10",
        "peso_kg": 8.5,
        "plan_id": portal["plan_id"],
        **cambios,
    }


async def _aprobar(db, referencia: str, valor: Decimal, estado: str = "APPROVED") -> None:
    evento, _ = await db.run_sync(
        pasarela.registrar_evento,
        _evento(referencia, int(valor * 100), estado, tx_id=f"tx-{referencia}-{estado}"),
    )
    await db.run_sync(pasarela.procesar_evento, evento.id)
    await db.commit()


async def test_cotiza_el_valor_nuevo_y_lo_que_queda_del_periodo(client: AsyncClient, db, portal):
    planes = (await client.get(f"{API}/planes", headers=portal["headers"])).json()
    assert portal["plan_id"] in [p["id"] for p in planes]

    resp = await client.post(
        f"{API}/cotizacion",
        json={"especie": "canino", "plan_id": portal["plan_id"]},
        headers=portal["headers"],
    )
    assert resp.status_code == 200, resp.text
    cot = resp.json()
    contrato = await db.get(Contrato, portal["contrato_id"])
    inicio, fin = contratos.ciclo_actual(contrato, hoy())
    # De 40.000 a 2 x 35.000: la diferencia, por los dias que quedan del periodo.
    esperado = (Decimal(30_000) * (fin - hoy()).days / (fin - inicio).days).quantize(
        Decimal("0.01")
    )
    assert (cot["valor_periodo_actual"], cot["valor_periodo_nuevo"]) == ("40000.00", "70000.00")
    assert Decimal(cot["valor_ajuste"]) == esperado
    assert cot["hasta"] == fin.isoformat()
    assert cot["cuotas_adelantadas"] == 0


async def test_si_la_proxima_cuota_ya_se_emitio_el_ajuste_cubre_su_diferencia(
    client: AsyncClient, db, portal
):
    """Las cuotas salen unos dias antes de vencer: un peludo que entra en esos dias no
    alcanzaria la siguiente, ya emitida con el valor anterior."""
    contrato = await db.get(Contrato, portal["contrato_id"])
    inicio, fin = contratos.ciclo_actual(contrato, hoy())
    await db.run_sync(cartera.generar_cuotas, fin)
    await db.commit()
    cot = (
        await client.post(
            f"{API}/cotizacion",
            json={"especie": "canino", "plan_id": portal["plan_id"]},
            headers=portal["headers"],
        )
    ).json()
    dias = (Decimal(30_000) * (fin - hoy()).days / (fin - inicio).days).quantize(Decimal("0.01"))
    assert cot["cuotas_adelantadas"] == 1
    assert Decimal(cot["valor_ajuste"]) == dias + Decimal(30_000)


async def test_el_peludo_entra_al_contrato_cuando_se_aprueba_el_pago(
    client: AsyncClient, db, portal
):
    resp = await client.post(API, json=_peludo(portal), headers=portal["headers"])
    assert resp.status_code == 201, resp.text
    inicio = resp.json()
    enlace = parse_qs(urlparse(inicio["enlace_pago"]).query)
    assert enlace["amount-in-cents"] == [str(int(Decimal(inicio["valor"]) * 100))]
    assert "expiration-time" in enlace
    familia_id = portal["familia_id"]
    # Antes del pago, la ficha espera: el peludo aun no esta en la familia ni en el contrato.
    nombres = set(await db.scalars(select(Mascota.nombre).where(Mascota.familia_id == familia_id)))
    assert "Kira" not in nombres
    altas = (await client.get(f"{API}/altas", headers=portal["headers"])).json()
    assert [(a["nombre"], a["estado"], a["estado_pago"]) for a in altas] == [
        ("Kira", "pendiente_pago", "pendiente")
    ]

    alta = await db.get(AltaPeludo, inicio["alta_id"])
    await _aprobar(db, alta.referencia_pago, Decimal(inicio["valor"]))
    await db.refresh(alta)
    assert alta.estado == "completada"
    mascota = await db.get(Mascota, alta.mascota_id)
    assert (mascota.nombre, mascota.raza, mascota.peso_kg) == ("Kira", "Criolla", 8.5)
    linea = await db.scalar(
        select(AfiliacionMascota).where(AfiliacionMascota.mascota_id == mascota.id)
    )
    assert str(linea.plan_id) == portal["plan_id"]
    contrato = await db.get(Contrato, portal["contrato_id"])
    await db.refresh(contrato)
    assert contrato.valor_periodo == Decimal("70000.00")
    # Lo pagado es su propia cuota de ajuste, ya pagada; no abona otra deuda.
    cuota = await db.scalar(select(Cuota).where(Cuota.descripcion == "Alta de Kira"))
    assert (cuota.valor, cuota.estado) == (Decimal(inicio["valor"]), "pagada")
    pago = await db.get(Pago, alta.pago_id)
    assert pago.aplicado and pago.cuota_id == cuota.id
    preventivos = await db.scalar(
        select(EventoPreventivo.id).where(EventoPreventivo.mascota_id == mascota.id).limit(1)
    )
    assert preventivos is not None
    # Un evento repetido no lo agrega dos veces.
    await _aprobar(db, alta.referencia_pago, Decimal(inicio["valor"]))
    kiras = await db.scalars(
        select(Mascota.id).where(Mascota.familia_id == familia_id, Mascota.nombre == "Kira")
    )
    assert len(list(kiras)) == 1


async def test_en_mora_o_con_un_nombre_repetido_no_se_agrega(client: AsyncClient, db, portal):
    repetido = await db.scalar(
        select(Mascota.nombre).where(Mascota.familia_id == portal["familia_id"]).limit(1)
    )
    resp = await client.post(API, json=_peludo(portal, nombre=repetido), headers=portal["headers"])
    assert resp.status_code == 422 and "Ya tienes un peludo llamado" in resp.text

    await db.execute(
        text("UPDATE contratos SET estado = 'en_mora' WHERE id = :id"),
        {"id": portal["contrato_id"]},
    )
    await db.commit()
    resp = await client.post(
        f"{API}/cotizacion",
        json={"especie": "canino", "plan_id": portal["plan_id"]},
        headers=portal["headers"],
    )
    assert resp.status_code == 422 and "ponte al dia" in resp.text


async def test_un_pago_en_curso_impide_otro_y_uno_rechazado_se_reemplaza(
    client: AsyncClient, db, portal
):
    primero = (await client.post(API, json=_peludo(portal), headers=portal["headers"])).json()
    otro = await client.post(API, json=_peludo(portal, nombre="Toby"), headers=portal["headers"])
    assert otro.status_code == 422 and "pago en curso" in otro.text

    alta = await db.get(AltaPeludo, primero["alta_id"])
    await _aprobar(db, alta.referencia_pago, Decimal(primero["valor"]), "DECLINED")
    otro = await client.post(API, json=_peludo(portal, nombre="Toby"), headers=portal["headers"])
    assert otro.status_code == 201, otro.text
    await db.refresh(alta)
    assert alta.estado == "cancelada"


async def test_a_las_48_horas_sin_pago_se_cierra_y_un_pago_tardio_va_al_equipo(
    client: AsyncClient, db, portal, en_worker
):
    from app.workers.tasks.afiliaciones import cerrar_registros_sin_pago

    inicio = (await client.post(API, json=_peludo(portal), headers=portal["headers"])).json()
    alta = await db.get(AltaPeludo, inicio["alta_id"])
    assert (await en_worker(cerrar_registros_sin_pago))["altas_canceladas"] == 0
    await db.execute(
        text("UPDATE altas_peludo SET created_at = now() - interval '49 hours' WHERE id = :id"),
        {"id": alta.id},
    )
    await db.commit()
    assert (await en_worker(cerrar_registros_sin_pago))["altas_canceladas"] == 1
    await db.refresh(alta)
    pago = await db.get(Pago, alta.pago_id)
    await db.refresh(pago)
    assert (alta.estado, pago.estado) == ("cancelada", "anulado")

    await _aprobar(db, alta.referencia_pago, Decimal(inicio["valor"]))
    tarea = await db.scalar(select(Tarea).where(Tarea.clave == f"alta_peludo_revision:{alta.id}"))
    assert tarea is not None and tarea.prioridad == "alta"
    kira = await db.scalar(select(Mascota.id).where(Mascota.nombre == "Kira"))
    assert kira is None


async def test_cada_familia_ve_solo_sus_altas(client: AsyncClient, db, portal):
    await client.post(API, json=_peludo(portal), headers=portal["headers"])
    ajena = await login(client, "beto@correo.co")
    assert (await client.get(f"{API}/altas", headers=ajena)).json() == []
