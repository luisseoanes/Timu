"""F2-PRE-06 Carnet preventivo en PDF con codigo de verificacion."""

from datetime import date
from typing import Any

from fpdf import FPDF


def _texto(valor: Any) -> str:
    # Las fuentes base del PDF son latin-1: se reemplazan caracteres fuera de ese rango.
    return str(valor if valor is not None else "-").encode("latin-1", "replace").decode("latin-1")


def _fecha(iso: str | None) -> str:
    return f"{date.fromisoformat(iso):%d/%m/%Y}" if iso else "-"


def _peso(kg: float | None) -> str:
    """El peso como lo escribe una persona: «12,5 kg», sin decimales si no los tiene."""
    if kg is None:
        return ""
    return f"{kg:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"


def linea_aplicada(fila: dict[str, Any]) -> str:
    """Una aplicacion del carnet: fecha, que, producto, lote, peso (si se anoto) y proxima."""
    peso = f"  peso {_peso(fila.get('peso_kg'))}" if fila.get("peso_kg") else ""
    return (
        f"{_fecha(fila['fecha_aplicacion'])}  {fila['nombre']} (dosis {fila['dosis']})  "
        f"{fila.get('producto') or ''} lote {fila.get('lote') or '-'}{peso}  "
        f"proxima: {_fecha(fila.get('proxima_fecha'))}"
    )


def generar_carnet(datos: dict[str, Any], *, codigo: str, url_verificacion: str) -> bytes:
    mascota = datos["mascota"]
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Carnet preventivo TIMU", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0,
        6,
        _texto(f"{mascota['nombre']}  -  {mascota['especie']}  -  {mascota.get('raza') or ''}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(
        0,
        6,
        _texto(f"Nacimiento: {_fecha(mascota.get('fecha_nacimiento'))}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    def tabla(titulo: str, filas: list[dict[str, Any]], aplicado: bool) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _texto(titulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        if not filas:
            pdf.cell(0, 6, "Sin registros", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            return
        for f in filas:
            if aplicado:
                linea = linea_aplicada(f)
            else:
                linea = f"{_fecha(f['fecha_programada'])}  {f['nombre']} (dosis {f['dosis']})"
            pdf.multi_cell(0, 5, _texto(linea), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    tabla("Aplicados", datos["aplicados"], aplicado=True)
    tabla("Vencidos", datos["vencidos"], aplicado=False)
    tabla("Proximos", datos["proximos"], aplicado=False)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _texto(f"Codigo de verificacion: {codigo}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0,
        5,
        _texto(
            f"Cualquier persona puede confirmar que este carnet es autentico en "
            f"{url_verificacion} sin necesidad de una cuenta."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    return bytes(pdf.output())
