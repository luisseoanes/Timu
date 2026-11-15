"""La marca de TIMU en los PDF que genera la plataforma (docs/manual-de-marca.md).

Fuentes con todos los caracteres del espanol (las base del PDF son latin-1 y estropean las
tildes), el logo en vector y la paleta del manual. GeosansLight va en los titulos e Inter en el
resto, como en la interfaz. Los ficheros viven en `app/recursos/marca/`: el logo sale del vector
que entrego TIMU, GeosansLight es la tipografia complementaria del manual (licencia confirmada
por TIMU) e Inter va con su licencia OFL al lado.
"""

from collections.abc import Callable
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

RECURSOS = Path(__file__).resolve().parents[1] / "recursos" / "marca"
LOGO = RECURSOS / "timu-color.svg"

# Paleta del manual (seccion 2) y roles de la interfaz (seccion 10), en RGB.
MARINO = (17, 21, 55)  # marino-900: titulos
TEXTO = (65, 68, 95)  # marino-700: texto
SUAVE = (95, 98, 117)  # marino-600: etiquetas y notas
BORDE = (226, 227, 231)  # marino-100: separadores
LIENZO = (245, 246, 241)  # fondo de las cabeceras de tabla
VERDE = (152, 184, 51)  # verde-500: color de marca
NARANJA = (212, 130, 0)  # naranja-500
AZUL = (71, 112, 149)  # azul-500
ROJO = (169, 33, 21)  # rojo-700: lo vencido

TITULOS = "GeosansLight"
CUERPO = "Inter"
MARGEN = 16  # mm
PIE = "TIMU · Medicina veterinaria prepagada · www.timu.com.co"


class PdfMarca(FPDF):
    """Carta, con las fuentes de la marca y un pie con la marca y el numero de pagina."""

    def __init__(self) -> None:
        super().__init__(format="Letter")
        self.add_font(TITULOS, "", str(RECURSOS / "GeosansLight.ttf"))
        self.add_font(CUERPO, "", str(RECURSOS / "Inter-Regular.ttf"))
        self.add_font(CUERPO, "B", str(RECURSOS / "Inter-SemiBold.ttf"))
        self.set_margins(MARGEN, MARGEN, MARGEN)
        self.set_auto_page_break(auto=True, margin=22)
        self.set_text_color(*TEXTO)

    @property
    def ancho_util(self) -> float:
        return self.w - 2 * MARGEN

    def footer(self) -> None:
        self.set_y(-14)
        self.set_draw_color(*BORDE)
        self.set_line_width(0.2)
        self.line(MARGEN, self.get_y(), self.w - MARGEN, self.get_y())
        self.set_y(-12)
        self.set_font(CUERPO, "", 8)
        self.set_text_color(*SUAVE)
        self.cell(self.ancho_util / 2, 5, PIE)
        self.cell(self.ancho_util / 2, 5, f"Página {self.page_no()} de {{nb}}", align="R")


# --- Piezas comunes de los documentos (el carnet es la referencia) ----------------------------

# Color de cada plan del catalogo (`ColorPlan`): su titulo lleva el cuadrado del color.
COLOR_PLAN = {"verde": VERDE, "naranja": NARANJA, "azul": AZUL}


def cabecera(pdf: PdfMarca, titulo: str, subtitulo: str) -> None:
    """El logo a la izquierda, el titulo y su linea a la derecha, y la linea verde de la marca.
    Deja el cursor debajo, donde empieza el documento."""
    ancho = pdf.ancho_util
    pdf.image(str(LOGO), x=MARGEN, y=13, w=44)
    pdf.set_xy(MARGEN, 15)
    pdf.set_font(TITULOS, "", 22)
    pdf.set_text_color(*MARINO)
    pdf.cell(ancho, 10, titulo, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(CUERPO, "", 9)
    pdf.set_text_color(*SUAVE)
    pdf.cell(ancho, 5, subtitulo, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*VERDE)
    pdf.set_line_width(0.8)
    pdf.line(MARGEN, 40, MARGEN + ancho, 40)
    pdf.set_y(45)


def datos(pdf: PdfMarca, pares: list[tuple[str, str]], columnas: int = 4) -> None:
    """Pares etiqueta y valor en filas de `columnas`: la etiqueta en mayusculas encima, como
    en la interfaz. Un valor largo baja de linea dentro de su columna."""
    ancho = pdf.ancho_util / columnas
    for inicio in range(0, len(pares), columnas):
        fila = pares[inicio : inicio + columnas]
        pdf.set_font(CUERPO, "B", 7)
        pdf.set_text_color(*SUAVE)
        pdf.set_char_spacing(0.4)
        for etiqueta, _ in fila:
            pdf.cell(ancho, 5, etiqueta.upper())
        pdf.set_char_spacing(0)
        pdf.ln(5)
        arriba = pdf.get_y()
        abajo = arriba
        pdf.set_font(CUERPO, "B", 11)
        pdf.set_text_color(*MARINO)
        for i, (_, valor) in enumerate(fila):
            pdf.set_xy(MARGEN + i * ancho, arriba)
            pdf.multi_cell(ancho - 3, 7, valor or "—", new_x="LMARGIN", new_y="NEXT")
            abajo = max(abajo, pdf.get_y())
        pdf.set_y(abajo + 3)
    pdf.ln(2)


def titulo_seccion(pdf: PdfMarca, texto: str, color: tuple[int, int, int] = MARINO) -> None:
    """Titulo de un bloque en GeosansLight, con el cuadrado de su color delante."""
    if pdf.will_page_break(24):
        pdf.add_page()
    y = pdf.get_y()
    pdf.set_fill_color(*color)
    pdf.rect(MARGEN, y + 2.2, 3, 3, style="F")
    pdf.set_x(MARGEN + 5)
    pdf.set_font(TITULOS, "", 15)
    pdf.set_text_color(*MARINO)
    pdf.cell(pdf.ancho_util - 5, 8, texto, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def tabla(
    pdf: PdfMarca,
    cabecera_tabla: tuple[str, ...],
    filas: list[tuple[str, ...]],
    anchos: tuple[int, ...],
    estilo: Callable[[str], FontFace | None] = lambda _: None,
) -> None:
    """Tabla con hilos entre filas y la cabecera sobre el lienzo. `estilo` da el de una celda
    por su texto (el carnet pinta «Vencido» en rojo)."""
    pdf.set_font(CUERPO, "", 9)
    pdf.set_text_color(*TEXTO)
    pdf.set_draw_color(*BORDE)
    pdf.set_line_width(0.2)
    # El relleno lo pone solo la cabecera: sin esto, las filas heredan el del titulo.
    pdf.set_fill_color(255, 255, 255)
    cabeza = FontFace(family=CUERPO, emphasis="BOLD", color=MARINO, fill_color=LIENZO)
    with pdf.table(
        width=int(pdf.ancho_util),
        col_widths=anchos,
        line_height=7,
        cell_fill_mode="NONE",
        headings_style=cabeza,
        borders_layout="HORIZONTAL_LINES",
        text_align="LEFT",
    ) as t:
        fila = t.row()
        for celda in cabecera_tabla:
            fila.cell(celda)
        for valores in filas:
            fila = t.row()
            for celda in valores:
                fila.cell(celda, style=estilo(celda))
    pdf.ln(6)


def parrafo(
    pdf: PdfMarca, texto: str, *, tamano: float = 9, color: tuple[int, int, int] = TEXTO
) -> None:
    pdf.set_font(CUERPO, "", tamano)
    pdf.set_text_color(*color)
    pdf.multi_cell(pdf.ancho_util, tamano * 0.5, texto, align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)
