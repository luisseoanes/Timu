"""La marca de TIMU en los PDF que genera la plataforma (docs/manual-de-marca.md).

Fuentes con todos los caracteres del espanol (las base del PDF son latin-1 y estropean las
tildes), el logo en vector y la paleta del manual. GeosansLight va en los titulos e Inter en el
resto, como en la interfaz. Los ficheros viven en `app/recursos/marca/`: el logo sale del vector
que entrego TIMU, GeosansLight es la tipografia complementaria del manual (licencia confirmada
por TIMU) e Inter va con su licencia OFL al lado.
"""

from pathlib import Path

from fpdf import FPDF

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
