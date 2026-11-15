"""F3-POR-05 Comprobante de pago en PDF, con la marca de TIMU (como el carnet)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core import marca_pdf as marca
from app.core.tiempo import ZONA_NEGOCIO, con_zona
from app.modules.cartera.periodos import formato_cop, nombre_medio


def generar_comprobante(
    *,
    familia: dict[str, Any],
    pago: dict[str, Any],
    aplicaciones: list[tuple[str, Decimal]],
) -> bytes:
    """`aplicaciones`: cada cuota que cubrio el pago, ya nombrada por su mes, con su valor."""
    fecha: datetime = con_zona(pago["fecha"]).astimezone(ZONA_NEGOCIO)
    pdf = marca.PdfMarca()
    pdf.set_title(f"Comprobante de pago {pago['referencia']}")
    pdf.set_author("TIMU")
    pdf.add_page()
    hora = f"{fecha:%I:%M}".lstrip("0") + (" a. m." if fecha.hour < 12 else " p. m.")
    marca.cabecera(pdf, "Comprobante de pago", f"Pagado el {fecha:%d/%m/%Y} a las {hora}")
    marca.datos(
        pdf,
        [
            ("Titular", familia["titular"]),
            ("Documento", familia["documento"]),
            ("Medio", nombre_medio(pago["medio"])),
            ("Valor", formato_cop(pago["valor"])),
        ],
    )
    marca.datos(pdf, [("Referencia", pago["referencia"] or "—")], columnas=1)
    if aplicaciones:
        marca.titulo_seccion(pdf, "Lo que cubre", marca.VERDE)
        marca.tabla(
            pdf,
            ("Concepto", "Valor"),
            [(descripcion, formato_cop(valor)) for descripcion, valor in aplicaciones],
            (75, 25),
        )
    marca.parrafo(
        pdf,
        "Este comprobante lo genera la plataforma de TIMU cuando la pasarela o el equipo "
        "confirman el pago.",
        tamano=8,
        color=marca.SUAVE,
    )
    return bytes(pdf.output())
