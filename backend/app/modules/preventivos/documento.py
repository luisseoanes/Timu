"""F2-PRE-06 Carnet preventivo en PDF con codigo de verificacion, con la marca de TIMU.

Se ordena como el carnet impreso de TIMU: los datos de la mascota, una tabla por tipo de
preventivo (vacunacion, desparasitacion interna y externa, esta con el peso de la mascota el dia
de la aplicacion, F2-PRE-07) y lo que esta pendiente. No lleva datos de la familia: el carnet se
comparte con terceros, que lo validan con el codigo del pie.
"""

from datetime import date
from typing import Any

from fpdf.fonts import FontFace

from app.core import marca_pdf as marca
from app.core.tiempo import hoy

SECCIONES: list[tuple[str, str, tuple[int, int, int]]] = [
    ("vacuna", "Vacunación", marca.AZUL),
    ("desparasitacion_interna", "Desparasitación interna", marca.VERDE),
    ("desparasitacion_externa", "Desparasitación externa", marca.NARANJA),
]
# «Aplicó» es el sello del carnet impreso: quien registro la aplicacion.
CABECERA_VACUNA = ("Vacuna", "Dosis", "Aplicada", "Producto", "Lote", "Próxima", "Aplicó")
CABECERA_DESPARASITACION = ("Aplicada", "Peso", "Producto", "Lote", "Próxima", "Aplicó")
CABECERA_PENDIENTES = ("Preventivo", "Programado para", "Estado")
VENCIDO = FontFace(family=marca.CUERPO, emphasis="BOLD", color=marca.ROJO)


def _fecha(iso: str | None) -> str:
    return f"{date.fromisoformat(iso):%d/%m/%Y}" if iso else "—"


def _peso(kg: float | None) -> str:
    """El peso como lo escribe una persona: «12,5 kg», sin decimales si no los tiene."""
    if kg is None:
        return "—"
    return f"{kg:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"


def filas_seccion(tipo: str, aplicados: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    """Las filas de la tabla de un tipo de preventivo. Las desparasitaciones llevan el peso."""
    filas: list[tuple[str, ...]] = []
    for a in (a for a in aplicados if a["tipo"] == tipo):
        comunes = (
            a.get("producto") or "—",
            a.get("lote") or "—",
            _fecha(a.get("proxima_fecha")),
            a.get("aplicado_por") or "—",
        )
        if tipo == "vacuna":
            dosis = f"{a['dosis']}{' (refuerzo)' if a.get('refuerzo') else ''}"
            filas.append((a["nombre"], dosis, _fecha(a["fecha_aplicacion"]), *comunes))
        else:
            filas.append((_fecha(a["fecha_aplicacion"]), _peso(a.get("peso_kg")), *comunes))
    return filas


def filas_pendientes(datos: dict[str, Any]) -> list[tuple[str, ...]]:
    """Lo vencido primero y luego lo proximo, cada uno con su fecha programada."""
    vencidos = [(f, "Vencido") for f in datos["vencidos"]]
    proximos = [(f, "Próximo") for f in datos["proximos"]]
    return [
        (f"{f['nombre']} · dosis {f['dosis']}", _fecha(f["fecha_programada"]), estado)
        for f, estado in vencidos + proximos
    ]


def generar_carnet(
    datos: dict[str, Any], *, codigo: str, url_verificacion: str, emitido: date | None = None
) -> bytes:
    mascota = datos["mascota"]
    pdf = marca.PdfMarca()
    pdf.set_title(f"Carnet preventivo de {mascota['nombre']}")
    pdf.set_author("TIMU")
    pdf.add_page()
    ancho = pdf.ancho_util

    # Cabecera: el logo a la izquierda, el titulo a la derecha y la linea verde de la marca.
    pdf.image(str(marca.LOGO), x=marca.MARGEN, y=13, w=44)
    pdf.set_xy(marca.MARGEN, 15)
    pdf.set_font(marca.TITULOS, "", 22)
    pdf.set_text_color(*marca.MARINO)
    pdf.cell(ancho, 10, "Carnet preventivo", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(marca.CUERPO, "", 9)
    pdf.set_text_color(*marca.SUAVE)
    pdf.cell(
        ancho,
        5,
        f"Vacunación y desparasitación · emitido el {emitido or hoy():%d/%m/%Y}",
        align="R",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_draw_color(*marca.VERDE)
    pdf.set_line_width(0.8)
    pdf.line(marca.MARGEN, 40, marca.MARGEN + ancho, 40)

    # La mascota: cuatro datos en una fila, con su etiqueta encima.
    pdf.set_y(45)
    datos_mascota = [
        ("Mascota", mascota["nombre"]),
        ("Especie", mascota.get("especie") or "—"),
        ("Raza", mascota.get("raza") or "—"),
        ("Nacimiento", _fecha(mascota.get("fecha_nacimiento"))),
    ]
    columna = ancho / len(datos_mascota)
    pdf.set_font(marca.CUERPO, "B", 7)
    pdf.set_text_color(*marca.SUAVE)
    pdf.set_char_spacing(0.4)
    for etiqueta, _ in datos_mascota:
        pdf.cell(columna, 5, etiqueta.upper())
    pdf.set_char_spacing(0)
    pdf.ln(5)
    pdf.set_font(marca.CUERPO, "B", 11)
    pdf.set_text_color(*marca.MARINO)
    for _, valor in datos_mascota:
        pdf.cell(columna, 7, valor)
    pdf.ln(12)

    def titulo(texto: str, color: tuple[int, int, int]) -> None:
        if pdf.will_page_break(24):
            pdf.add_page()
        y = pdf.get_y()
        pdf.set_fill_color(*color)
        pdf.rect(marca.MARGEN, y + 2.2, 3, 3, style="F")
        pdf.set_x(marca.MARGEN + 5)
        pdf.set_font(marca.TITULOS, "", 15)
        pdf.set_text_color(*marca.MARINO)
        pdf.cell(ancho - 5, 8, texto, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def tabla(
        cabecera: tuple[str, ...], filas: list[tuple[str, ...]], anchos: tuple[int, ...]
    ) -> None:
        pdf.set_font(marca.CUERPO, "", 9)
        pdf.set_text_color(*marca.TEXTO)
        pdf.set_draw_color(*marca.BORDE)
        pdf.set_line_width(0.2)
        # El relleno lo pone solo la cabecera: sin esto, las filas heredan el del titulo.
        pdf.set_fill_color(255, 255, 255)
        estilo = FontFace(
            family=marca.CUERPO, emphasis="BOLD", color=marca.MARINO, fill_color=marca.LIENZO
        )
        with pdf.table(
            width=int(ancho),
            col_widths=anchos,
            line_height=7,
            cell_fill_mode="NONE",
            headings_style=estilo,
            borders_layout="HORIZONTAL_LINES",
            text_align="LEFT",
        ) as t:
            fila = t.row()
            for celda in cabecera:
                fila.cell(celda)
            for valores in filas:
                fila = t.row()
                for celda in valores:
                    # Lo vencido se dice en rojo, ademas de con la palabra.
                    fila.cell(celda, style=VENCIDO if celda == "Vencido" else None)
        pdf.ln(6)

    for tipo, nombre, color in SECCIONES:
        titulo(nombre, color)
        filas = filas_seccion(tipo, datos["aplicados"])
        if not filas:
            pdf.set_font(marca.CUERPO, "", 9)
            pdf.set_text_color(*marca.SUAVE)
            pdf.cell(ancho, 6, "Sin aplicaciones registradas.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
        elif tipo == "vacuna":
            tabla(CABECERA_VACUNA, filas, (26, 10, 14, 19, 11, 14, 22))
        else:
            tabla(CABECERA_DESPARASITACION, filas, (14, 11, 26, 13, 14, 22))

    pendientes = filas_pendientes(datos)
    if pendientes:
        titulo("Pendiente", marca.MARINO)
        tabla(CABECERA_PENDIENTES, pendientes, (55, 25, 20))

    # Verificacion: el codigo y donde comprobarlo, sin cuenta.
    if pdf.will_page_break(26):
        pdf.add_page()
    y = pdf.get_y() + 2
    pdf.set_draw_color(*marca.BORDE)
    pdf.set_line_width(0.3)
    pdf.rect(marca.MARGEN, y, ancho, 20)
    pdf.set_xy(marca.MARGEN + 5, y + 3.5)
    pdf.set_font(marca.CUERPO, "B", 10)
    pdf.set_text_color(*marca.MARINO)
    pdf.cell(ancho - 10, 6, f"Código de verificación: {codigo}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(marca.MARGEN + 5)
    pdf.set_font(marca.CUERPO, "", 9)
    pdf.set_text_color(*marca.TEXTO)
    pdf.multi_cell(
        ancho - 10,
        4.5,
        f"Cualquier persona puede confirmar que este carnet es auténtico en {url_verificacion}, "
        "sin necesidad de una cuenta.",
        align="L",
    )
    return bytes(pdf.output())
