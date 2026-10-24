"""F4-DAS-03 Reportes programados: el periodo anterior, en Excel, por correo."""

from datetime import date, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona, hoy
from app.integrations import correo
from app.modules.cartera.periodos import sumar_meses
from app.modules.dashboard import exportar, service
from app.modules.dashboard.models import ReporteProgramado

logger = structlog.get_logger(__name__)


def periodo_anterior(periodicidad: str, dia: date) -> tuple[date, date]:
    if periodicidad == "diaria":
        ayer = dia - timedelta(days=1)
        return ayer, ayer
    if periodicidad == "semanal":
        lunes = dia - timedelta(days=dia.weekday() + 7)
        return lunes, lunes + timedelta(days=6)
    primero = dia.replace(day=1)
    anterior = sumar_meses(primero, -1)
    return anterior, primero - timedelta(days=1)


def toca(reporte: ReporteProgramado, dia: date) -> bool:
    if (
        reporte.ultimo_envio
        and con_zona(reporte.ultimo_envio).astimezone(ZONA_NEGOCIO).date() == dia
    ):
        return False  # ya salio hoy
    if reporte.periodicidad == "semanal":
        return dia.weekday() == 0
    if reporte.periodicidad == "mensual":
        return dia.day == 1
    return True


def enviar_programados(db: Session, dia: date | None = None) -> dict[str, Any]:
    dia = dia or hoy()
    resumen: dict[str, Any] = {"enviados": 0, "fallidos": 0}
    for reporte in db.scalars(select(ReporteProgramado).where(ReporteProgramado.activo.is_(True))):
        if not toca(reporte, dia):
            continue
        desde, hasta = periodo_anterior(reporte.periodicidad, dia)
        try:
            resultado = service.calcular(
                db, desde, hasta, reporte.ciudad, reporte.indicadores or None
            )
            adjunto = (
                f"{reporte.nombre}-{desde}-{hasta}.xlsx",
                exportar.a_xlsx(resultado),
                exportar.XLSX,
            )
            for destino in reporte.destinatarios:
                correo.enviar(
                    destino,
                    f"TIMU - {reporte.nombre} ({desde:%d/%m/%Y} a {hasta:%d/%m/%Y})",
                    "Adjuntamos los indicadores del periodo. Las formulas estan en la hoja "
                    "Definiciones.",
                    [adjunto],
                )
        except Exception as e:  # noqa: BLE001  un reporte que falla no frena los demas
            logger.exception("Reporte %s fallido", reporte.nombre)
            reporte.ultimo_error = str(e)[:2000]
            resumen["fallidos"] += 1
            continue
        reporte.ultimo_envio = ahora()
        reporte.ultimo_error = None
        resumen["enviados"] += 1
    db.flush()
    return resumen
