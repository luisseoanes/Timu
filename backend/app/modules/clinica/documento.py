"""F2-CLI-03 Formula medica veterinaria en PDF."""

from datetime import date
from typing import Any

from fpdf import FPDF


def _texto(valor: Any) -> str:
    # Las fuentes base del PDF son latin-1: se reemplazan caracteres fuera de ese rango.
    return str(valor if valor is not None else "").encode("latin-1", "replace").decode("latin-1")


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
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Formula medica veterinaria", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    peso = f"  -  {mascota['peso_kg']} kg" if mascota.get("peso_kg") else ""
    for linea in (
        f"Fecha: {fecha:%d/%m/%Y}",
        f"Paciente: {mascota['nombre']} ({mascota['especie']}){peso}",
        f"Responsable: {titular}",
        f"Diagnostico: {diagnostico or '-'}",
    ):
        pdf.cell(0, 6, _texto(linea), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Prescripcion", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for n, item in enumerate(items, start=1):
        partes = [
            item.get("medicamento"),
            item.get("presentacion"),
            f"dosis {item['dosis']}" if item.get("dosis") else None,
            item.get("frecuencia"),
            f"por {item['duracion']}" if item.get("duracion") else None,
        ]
        pdf.multi_cell(
            0,
            5,
            _texto(f"{n}. " + ", ".join(p for p in partes if p)),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        if item.get("indicaciones"):
            pdf.multi_cell(
                0, 5, _texto(f"   {item['indicaciones']}"), new_x="LMARGIN", new_y="NEXT"
            )
    if indicaciones:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Indicaciones generales", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _texto(indicaciones), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)
    pdf.cell(0, 6, _texto(profesional), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, "Medico veterinario TIMU", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
