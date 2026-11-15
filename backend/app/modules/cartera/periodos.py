"""Aritmetica de periodos y dinero para cartera."""

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

CENTAVO = Decimal("0.01")


def dinero(valor: Any) -> Decimal:
    return Decimal(str(valor or 0)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def centavos(valor: Any) -> int:
    return int(dinero(valor) * 100)


def sumar_meses(dia: date, meses: int) -> date:
    mes = dia.month - 1 + meses
    anio = dia.year + mes // 12
    mes = mes % 12 + 1
    return date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def periodo(dia: date) -> str:
    return f"{dia:%Y-%m}"


def vencimiento(periodo_: str, dia_corte: int) -> date:
    anio, mes = (int(x) for x in periodo_.split("-"))
    return date(anio, mes, min(dia_corte, calendar.monthrange(anio, mes)[1]))


def siguiente_periodo(periodo_: str) -> str:
    anio, mes = (int(x) for x in periodo_.split("-"))
    return periodo(sumar_meses(date(anio, mes, 1), 1))


def dias_del_periodo(inicio_periodo: date) -> int:
    return (sumar_meses(inicio_periodo, 1) - inicio_periodo).days


def formato_cop(valor: Any) -> str:
    return "$" + f"{dinero(valor):,.0f}".replace(",", ".")


_MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def nombre_cuota(
    periodo: str, meses: int, tipo: str = "cuota", descripcion: str | None = None
) -> str:
    """La cuota por su mes, como la dice el portal: «Cuota de octubre de 2026», «Cuota de enero a
    marzo de 2027». En un documento el ano va siempre. Un ajuste conserva su descripcion."""
    if tipo != "cuota":
        return descripcion or "Ajuste de plan"
    anio, mes = (int(p) for p in periodo.split("-"))
    fin_total = mes - 1 + max(meses, 1) - 1
    anio_fin, mes_fin = anio + fin_total // 12, fin_total % 12
    if (anio, mes - 1) == (anio_fin, mes_fin):
        return f"Cuota de {_MESES[mes - 1]} de {anio}"
    desde = _MESES[mes - 1] + ("" if anio == anio_fin else f" de {anio}")
    return f"Cuota de {desde} a {_MESES[mes_fin]} de {anio_fin}"


# Como llega el medio de un pago: el que registra el equipo o el que dice la pasarela.
_MEDIOS = {
    "efectivo": "Efectivo",
    "transferencia": "Transferencia",
    "consignacion": "Consignación",
    "datafono": "Datáfono",
    "otro": "Otro medio",
    "CARD": "Tarjeta",
    "NEQUI": "Nequi",
    "PSE": "PSE",
    "BANCOLOMBIA_TRANSFER": "Transferencia Bancolombia",
    "BANCOLOMBIA_COLLECT": "Corresponsal Bancolombia",
    "DAVIPLATA": "Daviplata",
    "wompi": "Pago en línea",
}


def nombre_medio(medio: str | None) -> str:
    return _MEDIOS.get(medio or "", medio or "—")
