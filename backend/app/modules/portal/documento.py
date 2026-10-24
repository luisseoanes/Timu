"""F3-POR-05 Comprobante de pago en PDF."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from fpdf import FPDF

from app.core.tiempo import ZONA_NEGOCIO, con_zona
from app.modules.cartera.periodos import formato_cop


def _texto(valor: Any) -> str:
    # Las fuentes base del PDF son latin-1: se reemplazan caracteres fuera de ese rango.
    return str(valor if valor is not None else "").encode("latin-1", "replace").decode("latin-1")


def generar_comprobante(
    *,
    familia: dict[str, Any],
    pago: dict[str, Any],
    aplicaciones: list[tuple[str, Decimal]],
) -> bytes:
    fecha: datetime = con_zona(pago["fecha"]).astimezone(ZONA_NEGOCIO)
    pdf = FPDF(format="Letter")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Comprobante de pago TIMU", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for linea in (
        f"Titular: {familia['titular']}  -  Documento: {familia['documento']}",
        f"Referencia: {pago['referencia']}",
        f"Fecha: {fecha:%d/%m/%Y %I:%M %p}",
        f"Medio: {pago['medio']}",
        f"Valor: {formato_cop(pago['valor'])}",
    ):
        pdf.cell(0, 6, _texto(linea), new_x="LMARGIN", new_y="NEXT")
    if aplicaciones:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Aplicado a", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for descripcion, valor in aplicaciones:
            pdf.cell(
                0, 6, _texto(f"{descripcion}: {formato_cop(valor)}"), new_x="LMARGIN", new_y="NEXT"
            )
    return bytes(pdf.output())
