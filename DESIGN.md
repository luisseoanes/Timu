---
name: TIMU
description: Panel de trabajo de una medicina veterinaria prepagada, dibujado como la señalética de un metro.
colors:
  superficie-marca: "#111537"
  superficie-marca-hover: "#282E53"
  superficie-sobre-marca: "rgb(255 255 255 / 8%)"
  borde-sobre-marca: "rgb(255 255 255 / 22%)"
  texto-sobre-marca: "#FFFFFF"
  texto-sobre-marca-suave: "#C4C4CD"
  indicador-sobre-marca: "#98B833"
  accion-fondo: "#98B833"
  accion-fondo-hover: "#769116"
  accion-texto: "#111537"
  accion-suave-fondo: "#F3F6E7"
  accion-suave-fondo-hover: "#E5EDCC"
  accion-suave-texto: "#415800"
  indicador-seleccion: "#769116"
  superficie-seleccion: "#F3F6E7"
  seleccion-texto: "#D6E3AD"
  foco: "#477095"
  texto-enlace: "#477095"
  texto-enlace-hover: "#274F73"
  superficie-lienzo: "#F5F6F1"
  superficie: "#FFFFFF"
  texto-titulo: "#111537"
  texto: "#41445F"
  texto-suave: "#5F6275"
  texto-deshabilitado: "#A0A1AF"
  borde: "#E2E3E7"
  borde-control: "#85889D"
  borde-control-hover: "#707387"
  velo: "rgb(17 21 55 / 50%)"
  estado-ok-fondo: "#F3F6E7"
  estado-ok-texto: "#415800"
  estado-alerta-fondo: "#FAF0E0"
  estado-alerta-texto: "#813E00"
  estado-info-fondo: "#E9EEF2"
  estado-info-texto: "#274F73"
  estado-peligro-fondo: "#FFF2EF"
  estado-peligro-texto: "#892319"
  estado-neutro-fondo: "#E2E3E7"
  estado-neutro-texto: "#41445F"
  peligro-accion-fondo: "#C0392B"
  peligro-accion-fondo-hover: "#A92115"
  peligro-accion-texto: "#FFFFFF"
  texto-error: "#A92115"
  plan-verde: "#98B833"
  plan-naranja: "#D48200"
  plan-azul: "#477095"
  plan-ninguno: "#A0A1AF"
  ruta-recorrida: "#111537"
  ruta-pendiente: "#85889D"
  serie-1: "#769116"
  serie-2: "#BE7700"
  serie-3: "#477095"
  serie-4: "#111537"
typography:
  display:
    fontFamily: "GeosansLight, Inter Variable, Inter, system-ui, sans-serif"
    fontSize: "2.125rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  cifra:
    fontFamily: "Inter Variable, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    fontFeature: "tnum"
  headline:
    fontFamily: "GeosansLight, Inter Variable, Inter, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.2
  title:
    fontFamily: "Inter Variable, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "Inter Variable, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
  body-menor:
    fontFamily: "Inter Variable, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Inter Variable, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.55
    letterSpacing: "0.09em"
rounded:
  campo: "6px"
  tarjeta: "8px"
  panel: "12px"
  pastilla: "999px"
spacing:
  e1: "4px"
  e2: "8px"
  e3: "12px"
  e4: "16px"
  e5: "20px"
  e6: "24px"
  e7: "32px"
  e8: "40px"
components:
  btn-primario:
    backgroundColor: "{colors.accion-fondo}"
    textColor: "{colors.accion-texto}"
    typography: "{typography.body}"
    rounded: "{rounded.campo}"
    padding: "0 20px"
    height: "40px"
  btn-primario-hover:
    backgroundColor: "{colors.accion-fondo-hover}"
    textColor: "{colors.accion-texto}"
  btn-secundario:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.texto-titulo}"
    rounded: "{rounded.campo}"
    padding: "0 20px"
    height: "40px"
  btn-suave:
    backgroundColor: "{colors.accion-suave-fondo}"
    textColor: "{colors.accion-suave-texto}"
    rounded: "{rounded.campo}"
    padding: "0 20px"
    height: "40px"
  btn-suave-hover:
    backgroundColor: "{colors.accion-suave-fondo-hover}"
    textColor: "{colors.accion-suave-texto}"
  btn-plano:
    textColor: "{colors.texto-suave}"
    rounded: "{rounded.campo}"
    padding: "0 20px"
    height: "40px"
  btn-icono:
    rounded: "{rounded.campo}"
    padding: "0"
    width: "40px"
    height: "40px"
  btn-peligro:
    backgroundColor: "{colors.peligro-accion-fondo}"
    textColor: "{colors.peligro-accion-texto}"
    rounded: "{rounded.campo}"
    padding: "0 20px"
    height: "40px"
  btn-deshabilitado:
    backgroundColor: "{colors.estado-neutro-fondo}"
    textColor: "{colors.texto-suave}"
  input:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.texto}"
    rounded: "{rounded.campo}"
    padding: "8px 12px"
    height: "40px"
  distintivo-ok:
    backgroundColor: "{colors.estado-ok-fondo}"
    textColor: "{colors.estado-ok-texto}"
    typography: "{typography.label}"
    rounded: "{rounded.pastilla}"
    padding: "3px 10px"
  distintivo-alerta:
    backgroundColor: "{colors.estado-alerta-fondo}"
    textColor: "{colors.estado-alerta-texto}"
    rounded: "{rounded.pastilla}"
    padding: "3px 10px"
  distintivo-info:
    backgroundColor: "{colors.estado-info-fondo}"
    textColor: "{colors.estado-info-texto}"
    rounded: "{rounded.pastilla}"
    padding: "3px 10px"
  distintivo-peligro:
    backgroundColor: "{colors.estado-peligro-fondo}"
    textColor: "{colors.estado-peligro-texto}"
    rounded: "{rounded.pastilla}"
    padding: "3px 10px"
  distintivo-neutro:
    backgroundColor: "{colors.estado-neutro-fondo}"
    textColor: "{colors.estado-neutro-texto}"
    rounded: "{rounded.pastilla}"
    padding: "3px 10px"
  panel:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.panel}"
    padding: "24px"
  barra-marca:
    backgroundColor: "{colors.superficie-marca}"
    textColor: "{colors.texto-sobre-marca-suave}"
    height: "64px"
    padding: "0 24px"
  barra-marca-modulo-activo:
    textColor: "{colors.texto-sobre-marca}"
  barra-inferior:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.texto-suave}"
    height: "56px"
  pestana:
    textColor: "{colors.texto-suave}"
    typography: "{typography.body-menor}"
    padding: "8px 16px"
  pestana-activa:
    textColor: "{colors.texto-titulo}"
  modal:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.panel}"
    padding: "20px"
    width: "560px"
  parada-punto:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.pastilla}"
    size: "24px"
  parada-vencida:
    backgroundColor: "{colors.peligro-accion-fondo}"
    textColor: "{colors.peligro-accion-texto}"
    rounded: "{rounded.pastilla}"
    size: "24px"
---

# Design System: TIMU

Este fichero describe lo construido, no lo planeado. La primera superficie del sistema es la
estructura del panel del equipo (`AppLayout`) y Familias (listado, detalle, pestañas y
ventanas); después, Rutas (la ruta del día del médico y su coordinación) y Clínica (la historia de
cada mascota y la consulta guiada). El resto de módulos del panel, el portal y las páginas públicas todavía usan la
maqueta anterior y adoptan este sistema en sus unidades de
[`docs/hoja-de-ruta-rediseno.md`](docs/hoja-de-ruta-rediseno.md): lo que se ve hoy en ellos no
es el sistema. El color, la tipografía, el logo y la voz los fija el
[manual de marca](docs/manual-de-marca.md); aquí se dice cómo se aplican en la interfaz y se
remite al manual donde él es la autoridad.

## Overview

**Creative North Star: "La línea de metro"**

Cada familia es una línea de metro. Su plan se dibuja como una línea del color del plan cuyas
estaciones son cuotas, preventivos y servicios: hechas, próxima o vencidas. El mundo visual es
la señalética del Metro de Medellín con la paleta de TIMU: una barra superior marina con los
módulos y el activo subrayado en verde, superficies blancas planas sobre un lienzo cálido, y
símbolos geométricos simples (líneas, círculos, cuadrados) que se leen de un vistazo. La
interfaz es de trabajo: densa, sin decoración, pensada para quien la usa ocho horas al día en
escritorio y para el médico en ruta con el celular.

La densidad viene de la información, no del adorno. No hay sombras en lo que está quieto, ni
bordes de adorno, ni degradados; la jerarquía la dan el tamaño del tipo, el peso, el marino del
título frente al marino suave del texto, y el único verde lleno de la acción principal. La
geometría de la línea (8 px, esquinas de pastilla, estaciones de 24 px) es el elemento que
identifica el producto y el que más se reutiliza: aparece entera en la ficha y en miniatura en
cada fila del listado.

Solo hay tema claro, por decisión de producto (`color-scheme: light`). El logo es el SVG del
vector de TIMU (`MarcaTimu`): completo con su lema, o compacto donde el lema no se leería.
Los títulos de 20 px o más van en GeosansLight y todo lo demás en Inter.

**Key Characteristics:**
- Barra de marca marina de 64 px; módulo activo con un subrayado verde de 4 px.
- Superficies blancas planas sobre lienzo `superficie-lienzo`; sombra solo en lo que flota.
- La línea de la familia: 8 px del color del plan, estaciones circulares con estado por forma.
- Inter con escala fija en rem, cifras tabulares, etiquetas de 12 px en mayúsculas espaciadas.
- Un solo verde lleno por vista; el resto de acciones son suaves, secundarias o planas.
- El estado nunca se lee solo por el color: siempre lleva texto e icono.

## Colors

Marino para el texto y la marca, verde para la acción y la selección, azul para el foco y los
enlaces, naranja y rojo solo para avisar; todo lo demás es blanco y lienzo.

Los valores de la paleta (`--verde-50` a `--marino-900`) solo se nombran en
`frontend/src/styles/tokens.css`. Fuera de ese fichero se usan roles (sección 10 del manual), y
el frontmatter de este documento lista los roles con su valor resuelto. Cada par de texto o
control con su fondo está declarado en el bloque `@pares` de `tokens.css` con su mínimo (4.5
texto, 3 controles e indicadores, 7 para los distintivos de estado).

### Primary
- **Verde TIMU** (`accion-fondo`): el fondo de la acción principal de la vista, la línea de un
  plan verde y el subrayado del módulo activo sobre la barra marina. Su texto encima es marino
  (`accion-texto`), nunca blanco. Como texto sobre claro se usa su paso oscuro
  (`accion-suave-texto`), regla 1 de la sección 11 del manual.
- **Verde hondo** (`accion-fondo-hover`, `indicador-seleccion`): hover del principal y todo
  indicador de selección sobre claro: pestaña activa, borde de la fila seleccionada, casillas.
- **Verde tenue** (`accion-suave-fondo`, `superficie-seleccion`): fondo de las acciones suaves y
  de la fila o el elemento seleccionado; también el halo de la estación próxima.

### Secondary
- **Azul TIMU** (`foco`, `texto-enlace`): anillo de foco y enlaces. Es el color de la
  navegación y la información, no de la acción.

### Tertiary
- **Naranja TIMU** (`plan-naranja`, `estado-alerta-*`): la línea de un plan naranja y los
  avisos. Como los colores de plan coinciden con los de estado, se distinguen por la forma
  (regla 4 del manual, ver Named Rules).
- **Rojo auxiliar** (`peligro-accion-fondo`, `texto-error`, `estado-peligro-*`): solo peligro,
  error y lo destructivo. En la línea, la estación vencida.

### Neutral
- **Marino noche** (`superficie-marca`, `texto-titulo`): la barra de marca y todo título, nombre
  o cifra que manda.
- **Marino texto** (`texto`) y **marino suave** (`texto-suave`): cuerpo y metadatos; el suave
  también para etiquetas en mayúsculas.
- **Lienzo** (`superficie-lienzo`): fondo de la aplicación y zonas hundidas
  (`superficie-hundida`, mismo valor), como la fila en hover.
- **Blanco** (`superficie`): paneles, campos, barra inferior, ventanas.
- **Hilo** (`borde`): separadores decorativos entre filas y bloques. **Borde de control**
  (`borde-control`) para todo lo que se toca: campos, botón secundario, casillas.
- **Velo marino** (`velo`): detrás de una ventana; las sombras y el velo salen del marino, no
  del negro (regla 8 del manual).

### Named Rules
**La regla de los roles.** Fuera de `tokens.css` no se escribe un color ni se nombra un paso de
la paleta: solo roles. Un rol nuevo llega con su par en `@pares`. Lo hace cumplir
`frontend/src/test/tokens.test.ts` (sin `#hex`, `rgb()`, `oklch()` ni nombres de color en
`src`, también en `style={{}}` y atributos SVG; ninguna `var(--…)` sin definir; cada par llega a
su mínimo).

**La regla del verde único.** Un solo botón principal (verde lleno) por vista; el resto son
suaves, secundarias o planas (regla 2 de la sección 11 del manual). En la ficha de una familia,
el principal es la acción de la próxima estación y nombra lo que hace.

**La regla de plan contra estado.** El plan es identidad: un cuadrado de 12 px del color del
plan (`marcador-plan`) y el nombre al lado en texto, o la línea de la familia. El estado es una
pastilla tintada con texto oscuro e icono. El color del plan sale del campo `color` del
catálogo (`data-color`), nunca del nombre del plan.

**La regla de la señal doble.** El estado nunca se comunica solo con color (WCAG 1.4.1): el
distintivo lleva icono por tono (`check`, `alerta`, `info`, `cerrar`, `menos`), la estación
vencida lleva el icono de alerta, y la fila del listado dice «N vencidas» en texto junto a la
miniatura.

## Typography

**Display Font:** GeosansLight (`--fuente-titulos`, con Inter de respaldo), solo en títulos de
20 px o más
**Body Font:** Inter Variable (con Inter, system-ui, -apple-system, Segoe UI)

**Character:** Dos familias servidas desde el proyecto: GeosansLight, la complementaria del
manual, en los títulos de 20 px o más (`h1` y `h2`), en su único peso, fino, sin negrita
sintetizada; e Inter (`@fontsource-variable/inter`) en todo lo demás, con la jerarquía hecha
de tamaño y peso 600/700. Un `h1` o `h2` que se reduce por debajo de 20 px vuelve a Inter.
Las cifras siguen en Inter por sus números tabulares (sección 12 del manual).

### Hierarchy
- **Display** (GeosansLight 400, `--t-display` 2.125rem / 34 px, 1.2, −0.01em en la ficha): el
  nombre de la familia abierta, el saludo y el ingreso. Uno por pantalla.
- **Cifra** (600, `--t-cifra` 1.5rem / 24 px): cifras destacadas de indicadores.
- **Headline** (GeosansLight 400, `--t-titulo` 1.25rem / 20 px, 1.2): título de página
  (`cabecera-pagina`).
- **Title** (600, `--t-seccion` 1rem / 16 px, 1.2): encabezado de bloque, título de ventana,
  cabecera del listado.
- **Body** (400, `--t-cuerpo` 0.875rem / 14 px, 1.55): texto de la interfaz, botones, celdas.
- **Menor** (400–600, `--t-menor` 0.8125rem / 13 px): metadatos, pestañas, módulos de la barra,
  rótulos de estación.
- **Label** (700, `--t-etiqueta` 0.75rem / 12 px, 0.09em, mayúsculas, `texto-suave`): cabeceras
  de columna, `dt` de una ficha de datos, la etiqueta de cada valor en la tabla apilada, los
  encabezados de los bloques Mascotas y Cartera del resumen, y «Hoy» en la línea. Nada baja de
  12 px.

### Named Rules
**La regla de la escala fija.** El tipo se mide en rem con los siete pasos de `tokens.css`; una
interfaz de trabajo no escala el tipo con la ventana (nada de `clamp()` ni `vw` en tamaños de
letra). En pantallas táctiles o de 900 px o menos, campos y buscadores suben a 1rem para que
iOS no amplíe la página al enfocar.

**La regla de las cifras tabulares.** Importes, fechas, totales y contadores llevan `.numero`
(`font-variant-numeric: tabular-nums`) donde se comparan en columna o se actualizan.

**La regla de la etiqueta que nombra.** La etiqueta en mayúsculas nombra un dato o un bloque de
datos; es el título de lo que tiene debajo, nunca una línea decorativa encima de otro título.

## Layout

**Estructura.** `.shell` es una rejilla de dos filas: la barra de marca fija arriba (64 px,
`--capa-barra`) y `.contenido` debajo, centrado con un máximo de 1440 px y relleno de 24 px
(16 px en el celular). Cada hijo de una rejilla lleva `min-width: 0` para que una tabla ancha
se desplace dentro de su `.scroll-x` en vez de estirar la página.

**Navegación según el ancho.** `AppLayout` decide cuántos módulos caben en la barra y manda el
resto a «Más»: 8 desde 1360 px, 6 desde 1180, 3 desde 900. Por debajo de 1360 px se ocultan el
lema de la marca y el buscador encoge a 220 px. Por debajo de 900 px la navegación pasa a una
barra inferior fija (56 px, al alcance del pulgar) con los cuatro módulos que más usa cada
perfil y «Más» con el resto; el contenido reserva su alto más el área segura.

**Listado y ficha (`.con-ficha`: Familias, Rutas, Clínica).** Dos columnas: listado de 320–420 px
(`.listado`) y el registro abierto en el resto (`.ficha-abierta`), separadas 20 px. Por debajo
de 900 px se ve uno u otro: el listado sin registro abierto, la ficha (con botón de volver) con
él.

**La ruta propia (Rutas).** Quien solo sale a campo no ve listado: su ruta del día ocupa una
columna de hasta 760 px, que se lee igual en el escritorio que en el celular. Encima, una línea
con el avance («1 de 3 paradas · 22,3 km · hasta las 1:15 p. m.») y el día, un botón compacto
que dice «Hoy» con el campo de fecha nativo superpuesto; fuera de hoy, el día y «Volver a hoy»
bajan a su fila.

**Ritmo.** Escala de 4 px (`--e1` a `--e8`). Entre bloques de página 16 px; entre columnas 20
px; dentro de un panel 20–24 px; entre filas de un listado 12 px de relleno con un hilo
(`borde`) entre ellas. Los pares etiqueta/valor se separan 2 px; las fichas de datos van en
`repeat(auto-fill, minmax(180px, 1fr))`.

**Zonas táctiles.** Botones, campos, buscadores y botones de icono miden 40 px y suben a 44 px
en pantallas de 900 px o menos o con puntero grueso.

### Named Rules
**La regla del contenedor.** Lo que cambia de forma según el sitio que tiene lo decide su
contenedor, no la ventana: junto al listado, la ficha es estrecha en un escritorio ancho. La
`tabla-apilable` se apila con una container query por debajo de 640 px de su `.scroll-x`, y la
línea de la familia pasa a vertical cuando mide que sus paradas no caben con su rótulo (y
siempre por debajo de 600 px de ventana).

**La regla de sin desborde.** Ninguna ruta desborda en horizontal a 375, 768 ni 1280 px, ni
tiene texto con contraste insuficiente según axe-core; las rutas con pestañas se comprueban
pestaña por pestaña. Lo vigila `frontend/e2e-stack/responsive.spec.ts`, cuya lista
`PENDIENTES` (deuda de los módulos sin rediseñar) solo puede encoger.

## Elevation & Depth

El sistema es plano. Las superficies quietas (paneles, tarjetas, barras) no llevan sombra: la
profundidad la dan el blanco sobre el lienzo, el hilo entre filas y la barra marina. `--sombra-1`
y `--sombra-2` valen `none` a propósito. Solo lo que flota sobre la pantalla —menús
desplegables, ventanas y la lista de opciones de un selector— lleva sombra, difusa y teñida de
marino. El apilamiento sale entero de la escala `--capa-*`: `elevada` (1, una estación sobre su
línea), `barra` (10), `velo` (30), `ventana` (31) y `menu` (40), para que lo que se abre desde
una ventana quede por encima de ella.

### Shadow Vocabulary
- **Flotante** (`--sombra-3`: `box-shadow: 0 12px 32px rgb(17 21 55 / 16%)`): menús, ventanas,
  lista de opciones.
- **Anillo de foco de campo** (`box-shadow: 0 0 0 1px var(--foco)`): campo o buscador enfocado,
  sumado a su borde azul; en rojo (`texto-error`) si el campo es inválido.
- **Subrayado de módulo** (`box-shadow: inset 0 -4px 0 var(--indicador-sobre-marca)`): módulo
  activo en la barra marina; en la barra inferior, `inset 0 3px 0 var(--indicador-seleccion)`
  arriba.
- **Halo de la próxima** (`box-shadow: 0 0 0 3px var(--indicador-seleccion)`): la estación
  próxima de la línea.

### Named Rules
**La regla de lo que flota.** Sombra solo para lo que tapa a otra cosa y desaparece al cerrarse.
Un panel, una tarjeta o una barra nunca la llevan.

**La regla de las capas.** Todo `z-index` sale de `--capa-*`; lo comprueba `tokens.test.ts`, y
`frontend/e2e-stack/recorridos.spec.ts` comprueba que menús y ventanas abiertas quedan por
encima de las barras fijas.

## Shapes

Esquinas contenidas, como la señalética del metro, y la pastilla reservada para lo que es señal.
Campos, botones, botones de icono e iconos de fila llevan esquina de campo (6 px); tarjetas
interiores, menús e indicadores, de tarjeta (8 px); paneles del listado y la ficha, ventanas y
la espera de sesión, de panel (12 px; la hoja del celular solo arriba). La pastilla (999 px) es
para distintivos de estado, la línea, sus estaciones, el botón del tramo plegado y el avatar de
la cuenta. El marcador de plan es un cuadrado: el plan es identidad, no estado. Los bordes son
de 1 px; los controles usan `borde-control` y los separadores `borde`. La iconografía es un solo
juego (`Icono`): trazo de 1.6, extremos y uniones redondeados, 20 px por defecto, siempre
`currentColor`.

## Components

### Buttons
Firmes y planos; el color dice la jerarquía, no la forma.
- **Shape:** esquina de campo (6 px), 40 px de alto (44 en táctil), 0 20 px de relleno, 600 a
  14 px, icono y texto separados 8 px.
- **Primario:** verde TIMU con texto marino; hover a verde hondo. Uno por vista.
- **Suave:** verde tenue con texto verde oscuro; para las acciones que acompañan al principal
  («Habilitar portal», «Gestionar afiliación», «Editar»).
- **Secundario:** blanco con borde de control y texto marino; hover con borde más oscuro y
  fondo de lienzo.
- **Plano:** sin fondo, texto suave; hover a marino sobre lienzo. **Plano peligro** para lo
  destructivo dentro de una fila.
- **Peligro:** rojo lleno con texto blanco, solo en la confirmación de algo que no se deshace.
- **De icono** (`btn-icono`, junto a la variante): cuadrado de 40 px (44 en táctil) con solo un
  icono y su `aria-label`, como llamar o «Más acciones» en una parada.
- **Hover / Focus / Active:** transición de 160 ms con la curva del sistema; foco con contorno
  azul de 2 px separado 2 px; al pulsar baja 1 px.
- **Deshabilitado:** el mismo gris neutro para todas las variantes, para que no parezca otra.

### Chips (distintivos de estado)
- **Style:** pastilla de fondo tintado y texto oscuro del mismo tono (contraste ≥ 7), 12 px en
  700, 3 × 10 px de relleno, icono de 12 px delante.
- **State:** cinco tonos (`ok`, `alerta`, `info`, `peligro`, `neutro`), cada uno con su icono.
  El tono y el texto salen del mapeo único de `lib/estados.ts` a través de `Distintivo`;
  `Insignia` es la pastilla sin dominio.

### Cards / Containers
- **Corner Style:** panel (12 px) para las columnas del listado y la ficha; tarjeta (8 px) para
  métricas, indicadores y avisos.
- **Background:** blanco sobre el lienzo.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** ninguno en los paneles; el hilo `borde` separa filas y bloques dentro de ellos.
- **Internal Padding:** 16 px en el listado, 24 px en la ficha (16 px por debajo de 900 px).
- **Bloque:** un apartado dentro de un panel (título de 14 px y su tabla o lista), separado
  24 px del anterior.

### Inputs / Fields
- **Style:** blanco, borde de control de 1 px, esquina de campo, 40 px de alto, 8 × 12 px de
  relleno. La etiqueta va encima en 13 px y 600, marino; la ayuda debajo en 12 px suave y
  enlazada con `aria-describedby`. El buscador es el mismo control con icono, para que junto a
  un `select` sean un solo tipo de control.
- **Focus:** borde azul y anillo de 1 px azul, sin contorno extra.
- **Error / Disabled:** `aria-invalid` pone el borde (y el anillo al enfocar) en rojo de error;
  deshabilitado, fondo de lienzo y texto suave.
- **Formulario:** rejilla de dos columnas con 16 px; una a 900 px o menos. Casillas y radios de
  18 px con `accent-color` verde hondo.

### Navigation
- **Barra de marca:** marino noche, 64 px, fija. Marca en texto blanco a la izquierda; módulos
  en 13 px y 600, marino claro (`texto-sobre-marca-suave`); hover a blanco sobre marino de
  hover; activo en blanco con subrayado verde de 4 px. Buscador blanco a la derecha y avatar
  circular con iniciales en una pastilla translúcida. Foco en verde sobre la marca.
- **«Más»:** los módulos que no caben, en un menú (Radix DropdownMenu) blanco con esquina de
  tarjeta y sombra flotante; el elemento resaltado en verde tenue. Arriba lleva una flecha;
  en la barra inferior, tres puntos (nunca «+», que se lee como crear).
- **Barra inferior (celular):** blanca con hilo arriba, 56 px por elemento, icono de 22 px y
  rótulo de 12 px; activo en marino con una marca verde de 3 px en el borde superior.

### Tabs
- Sobre Radix Tabs (`Pestanas`): 13 px en 700, texto suave, subrayado de 3 px verde hondo en la
  activa y hilo bajo la lista. Por debajo de 600 px no se reparten en varias filas: se desplazan
  en la suya.

### Ventanas (Modal)
- Sobre Radix Dialog: blanca, esquina de panel, sombra flotante, 560 px de ancho como máximo y
  20 px de relleno, sobre el velo marino. Cabecera (título de 16 px, descripción de 13 px suave y
  cierre con botón de icono) y pie fijos; solo el cuerpo se desplaza, así la acción principal
  del pie se ve siempre. El pie va alineado a la derecha sobre un hilo.
- Por debajo de 600 px es una hoja que sube desde abajo: todo el ancho, hasta el 92 % del alto,
  esquinas de panel solo arriba y relleno para el área segura. `recorridos.spec.ts` comprueba
  que el pie queda a la vista.

### Tabla apilable
- **Escritorio:** cabeceras en etiqueta (12 px, mayúsculas espaciadas, texto suave), celdas con
  12 px de relleno e hilo entre filas, fila en hover sobre lienzo, acciones a la derecha.
- **Contenedor de menos de 640 px:** cada fila es un bloque. La primera celda es su título en
  marino y 700; el resto, pares etiqueta y valor con la etiqueta (de `data-etiqueta`, que repite
  la cabecera) en la misma voz que la cabecera de columna. Las acciones bajan a una fila propia.
  La cabecera sigue en el DOM para los lectores de pantalla.
- Hoy la usan las pestañas de Familias; las tablas de los demás módulos la adoptan en su unidad
  de la hoja de ruta.

### Historial
- Lista de cambios con la fecha (suave, tabular) en una columna de hasta 11 rem a la izquierda y
  qué cambió a la derecha (título de 14 px y detalle suave); hilo entre entradas. Por debajo de
  600 px la fecha va encima.

### Espera de sesión
- Mientras se comprueba la sesión (`ProtectedRoute`): la marca y un esqueleto centrados en el
  lienzo. Si falla, un aviso blanco con esquina de panel, icono de error, título de 16 px y el
  botón para reintentar. El esqueleto es una barra del color de pista que respira
  (opacidad 1 → 0.45, 1.2 s).

### La línea de la familia (componente propio)
El elemento que identifica el producto. `LineaFamilia` dibuja el año de la familia como un plano
de metro: espaciado esquemático, no proporcional al tiempo.
- **Línea:** 8 px, pastilla, del color del plan (`data-color` del catálogo) o gris
  (`plan-ninguno`) sin plan.
- **Estaciones:** botones circulares de 24 px con borde de 4 px. Hecha: llena del color de la
  línea. Próxima: anillo marino con halo verde hondo de 3 px (3:1 sobre blanco). Vencida: roja con el icono de
  alerta en blanco. Programada: contorno del color de la línea sobre blanco. Los eventos del
  mismo día comparten estación.
- **Rótulos:** título en 13 px (rojo de error si está vencida) y fecha en 12 px suave. Siempre
  rotuladas la próxima y las vencidas; las demás muestran el rótulo al pasar el cursor o al
  enfocarlas (transición de opacidad de 160 ms). El nombre accesible del botón lo dice todo.
- **Hoy:** marca vertical marina de 4 × 24 px con «Hoy» en etiqueta.
- **Tramo plegado:** las hechas antiguas se pliegan en una pastilla «N hechas» con borde de
  control que se despliega al activarla.
- **Vertical:** cuando las paradas no caben con su rótulo, y siempre en el celular, la línea
  baja en vertical con todo rotulado.
- **Activar:** una estación abre donde se atiende (el registro de pago desde una cuota, la ficha
  de un servicio). Desde un preventivo hoy solo lleva a la pestaña de mascotas; agendarlo desde
  la estación llega en `R2-PAN-08`.
- **Miniatura (`LineaMini`):** en cada fila del listado, línea de 2 px con puntos de 10 px y la
  marca de hoy de 2 × 12 px; es dibujo (`role="img"`) con el resumen en `aria-label`, y la fila
  repite las vencidas en texto.

### La línea de la ruta (componente propio)
`LineaRuta` dibuja la ruta del día con la misma gramática que la línea de la familia, en
vertical siempre: es una lista que se recorre de arriba abajo.
- **Línea:** 8 px marina, nunca del color de un plan (una ruta no es un plan). Recorrida en
  `ruta-recorrida` hasta la parada que toca; por recorrer, en `ruta-pendiente`.
- **Estaciones:** 24 px con borde de 4 px. Hecha: llena de marino. La que toca: anillo marino con
  halo verde hondo de 3 px. Pendiente: contorno gris.
- **Estados:** los del camino normal (en curso, en camino, en sitio, próxima) van en tono
  informativo; la alerta queda para lo que la merece, como lo que falta por rutear.
- **La que toca, abierta:** hora (o «Llegó …») y franja acordada, estado, la dirección en Inter
  600 de 24 px (es casi toda cifras y se lee a pleno sol), complemento y barrio, familia (enlace
  a su ficha) y mascota con especie, edad y peso, el servicio y sus observaciones, y sus
  acciones: la de estado («Iniciar ruta», «Voy en camino», «Llegué», «Terminar visita» o, si al
  servicio le faltan pasos obligatorios, «Registrar la atención»), «Cómo llegar», llamar y un
  menú con WhatsApp, el servicio, la historia clínica y omitir. En un contenedor de 440 px o
  menos la acción de estado ocupa su fila, de 48 px.
- **Pendientes:** hora, franja, a quién y qué; el resumen es un botón que la abre en su sitio.
- **Hechas:** mientras falte alguna, se pliegan tras una pastilla «N hechas» que las muestra y
  las vuelve a plegar (`aria-expanded`, con una flecha que gira); la pastilla no desaparece, así
  que el foco se queda en ella.
- **Omitidas:** fuera de la línea, en un bloque aparte con su motivo.
- **Miniatura (`LineaRutaMini`):** en cada fila del listado de rutas, línea de 2 px con puntos de
  10 px; dibujo con su resumen en `aria-label`.

**La regla del número de casa.** En una dirección colombiana, «# 100-12» se lee como una
unidad: no se parte entre dos líneas (`partirDireccion` y `.sin-cortes`); si no cabe, baja
entero. Leído a pleno sol, «100-» arriba y «12» abajo parecen dos cifras.

**La regla de la acción de quien recorre.** La acción de estado de una parada es verde solo para
quien hace la ruta. Quien coordina también puede avanzarla, pero como secundaria: en su vista la
acción principal es planear.

### La guía de la consulta (componente propio)
`ConsultaGuiada` recorre la consulta clínica como una línea de cinco estaciones (motivo,
anamnesis, examen físico, diagnóstico, tratamiento): un apartado por pantalla.
- **Guía:** horizontal, en un panel blanco. Cinco columnas iguales para que lo recorrido (marino)
  llegue justo a la estación actual; lo que falta, en `ruta-pendiente`. Cada estación es un botón
  de 48 px de alto con su punto de 24 px y su nombre corto en 12 px («Plan» por el tratamiento:
  el título completo no cabe a 390 px). Escrita: llena. Actual: anillo marino con halo verde y
  `aria-current="step"`. Lo que falta para firmar: anillo y nombre en rojo de error.
- **Apartado:** título en GeosansLight de 24 px, la ayuda de 13 px en 600 como descripción del
  campo, un área de texto de al menos 180 px y, bajo un hilo, «En la última consulta» con su
  fecha y lo que se anotó. En el primero, la plantilla y la modalidad antes de crearla.
- **Pie:** «Anterior» (secundario) y «Siguiente: <apartado>» o «Firmar consulta» (verde); en el
  celular, de 48 px y a todo el ancho; desde 900 px, a la derecha y a su tamaño.
- **Guardado:** el borrador nace al dejar el motivo (la historia lo exige) y se guarda al cambiar
  de apartado, solo con lo que cambió. Firmar dice qué falta y lleva a su apartado antes de
  pedirlo al servidor. La consulta de una visita exige además el tratamiento.
- **Identidad:** por debajo de 900 px, donde la historia de la izquierda no está, la cabecera de
  la consulta (guiada o leída) dice la mascota, su familia, la especie y el peso.
- **Lectura:** la consulta firmada se lee como una ficha en columna (etiqueta y texto por
  apartado), con «Emitir fórmula» y «Corregir»; el título va a 24 px, no a 34: no es el nombre
  de nada.

## Do's and Don'ts

### Do:
- **Do** usa solo roles de `tokens.css` en componentes, vistas y `style={{}}`; si falta uno,
  añade el paso (si hace falta), el rol y su par en `@pares`.
- **Do** deja un solo botón verde lleno por vista y haz suaves o secundarias las demás acciones.
- **Do** acompaña todo estado de texto e icono además del color (distintivo, estación vencida,
  «N vencidas»).
- **Do** dibuja el plan como identidad: cuadrado de 12 px o línea de 8 px del color del catálogo,
  con el nombre en texto al lado.
- **Do** usa la escala fija en rem, `.numero` en cifras que se comparan, y etiquetas de 12 px en
  mayúsculas espaciadas para nombrar datos.
- **Do** decide los cambios de forma por el ancho del contenedor (`tabla-apilable`, la línea),
  no por el de la ventana.
- **Do** saca todo `z-index` de `--capa-*` y toda sombra de `--sombra-3`, solo en lo que flota.
- **Do** mantén los controles en 40 px y 44 px en táctil, con foco azul visible de 2 px.

### Don't:
- **Don't** escribas un color a mano ni nombres un paso de la paleta fuera de `tokens.css`.
- **Don't** pongas sombra, borde de adorno ni degradado en paneles, tarjetas o barras.
- **Don't** pongas una etiqueta en mayúsculas encima de un título como antetítulo: la etiqueta
  nombra el dato o el bloque que tiene debajo.
- **Don't** deduzcas el color de un plan de su nombre ni uses el color de plan como estado.
- **Don't** uses verde o naranja de marca como texto sobre claro (regla 1 del manual); sobre la
  barra marina solo blanco, marino-200, verde-500 y naranja-500 (regla 6).
- **Don't** recolorees el logo ni lo dibujes con texto: va el SVG de `MarcaTimu`, a color o en
  blanco (sección 13 del manual).
- **Don't** uses los patrones de siluetas de la marca como decoración en las pantallas de
  trabajo (panel, portal, clínica aliada): son para las páginas públicas y de venta, donde la
  marca se presenta. En una pantalla de trabajo compiten con los datos.
- **Don't** resuelvas la línea con scroll horizontal ni con una ventana de «Anteriores» y
  «Siguientes»: escondían una cuota vencida.
- **Don't** añadas un tema oscuro ni uses GeosansLight por debajo de 20 px, en texto corrido,
  tablas o botones.
- **Don't** uses «+» para «Más» en la navegación: se lee como crear.
