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
