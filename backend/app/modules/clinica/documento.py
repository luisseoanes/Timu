"""6.14 Formula medica veterinaria en PDF, con la marca de TIMU (como el carnet)."""

from datetime import date
from typing import Any

from app.core import marca_pdf as marca


def _peso(kg: float | None) -> str:
    if kg is None:
        return "—"
    return f"{kg:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"


def generar_formula(
    *,
    fecha: date,
    mascota: dict[str, Any],
    titular: str,
    profesional: str,
    diagnostico: str | None,
    items: list[dict[str, Any]],
    indicaciones: str | None,
) -> bytes:
    pdf = marca.PdfMarca()
    pdf.set_title(f"Fórmula de {mascota['nombre']}")
    pdf.set_author("TIMU")
    pdf.add_page()
    marca.cabecera(pdf, "Fórmula médica veterinaria", f"Emitida el {fecha:%d/%m/%Y}")
    marca.datos(
        pdf,
        [
            ("Paciente", mascota["nombre"]),
            ("Especie", mascota.get("especie") or "—"),
            ("Peso", _peso(mascota.get("peso_kg"))),
            ("Responsable", titular),
        ],
    )
    marca.datos(pdf, [("Diagnóstico", diagnostico or "—")], columnas=1)
    marca.titulo_seccion(pdf, "Prescripción", marca.AZUL)
    marca.tabla(
        pdf,
        ("Medicamento", "Dosis", "Frecuencia", "Duración", "Indicaciones"),
        [
            (
                " · ".join(p for p in (i.get("medicamento"), i.get("presentacion")) if p),
                i.get("dosis") or "—",
                i.get("frecuencia") or "—",
                i.get("duracion") or "—",
                i.get("indicaciones") or "—",
            )
            for i in items
        ],
        (30, 13, 17, 13, 27),
    )
    if indicaciones:
        marca.titulo_seccion(pdf, "Indicaciones generales")
        marca.parrafo(pdf, indicaciones, tamano=10)
    if pdf.will_page_break(30):
        pdf.add_page()
    pdf.ln(14)
    pdf.set_draw_color(*marca.BORDE)
    pdf.set_line_width(0.3)
    pdf.line(marca.MARGEN, pdf.get_y(), marca.MARGEN + 70, pdf.get_y())
    pdf.ln(2)
    pdf.set_font(marca.CUERPO, "B", 10)
    pdf.set_text_color(*marca.MARINO)
    pdf.cell(0, 6, profesional, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(marca.CUERPO, "", 8)
    pdf.set_text_color(*marca.SUAVE)
    pdf.cell(0, 5, "Médico veterinario TIMU", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
