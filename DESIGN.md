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
cada mascota y la consulta guiada), el Inicio (las cifras del período y la línea del día), Servicios y Tareas (el listado con
ficha de los servicios y la bandeja), Cartera y Preventivos (sus bandejas, el carnet y el
preventivo atendido desde su estación) y Comercial y Campañas (los interesados del embudo con su
conversación, la bandeja de conversaciones y las campañas en listado con ficha) y Aliadas y
Administración (las remisiones y los usuarios en bandeja; las clínicas, los planes y las reglas en
listado con ficha). El portal de familias está rediseñado entero: la
estructura, el inicio y los peludos (R3-POR-01) y las citas, los pagos y los datos (R3-POR-02).
De las páginas públicas, el acceso (R3-PUB-01): ingreso, recuperación, restablecimiento y
activación de la cuenta. El resto de módulos del panel y las demás páginas públicas (el registro
en línea, la encuesta y la verificación del carnet), y la clínica aliada, todavía usan la maqueta
anterior y adoptan este sistema en sus unidades de
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
escritorio y para el médico en ruta con el celular. En el portal, la misma línea es el inicio de
la familia: abierta en «Hoy», como el «usted está aquí» de un plano de metro.

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
  nombre de la familia abierta, el saludo y el título del acceso («Hola de nuevo», «Hola, Ana»,
  «Este enlace venció»). Uno por pantalla. En el portal todo `h1` va a este tamaño: «Hola, Ana»,
  «Tus peludos» y el nombre de cada peludo. En el acceso, la frase del panel de marca va también
  a 34 px, en blanco sobre marino; no es un título (`p`), y por debajo de 900 px desaparece.
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

**Listado y ficha (`.con-ficha`: Familias, Rutas, Clínica, Comercial, Campañas, las clínicas de
Aliadas, Planes y Reglas).** Dos columnas: listado de 320–420 px
(`.listado`) y el registro abierto en el resto (`.ficha-abierta`), separadas 20 px. Por debajo
de 900 px se ve uno u otro: el listado sin registro abierto, la ficha (con botón de volver) con
él.

**El acceso.** Sin barra de marca ni `.shell`: desde 900 px, dos columnas iguales a todo el alto
(`100dvh`), el panel de marca marino a la izquierda y el formulario sobre blanco a la derecha,
centrado en una columna de 400 px. Por debajo de 900 px, una franja marina arriba y el formulario
debajo, alineado arriba con 24 px de relleno (16 a los lados), para que el verde quede en la
primera pantalla del celular.

**La ruta propia (Rutas).** Quien solo sale a campo no ve listado: su ruta del día ocupa una
columna de hasta 760 px, que se lee igual en el escritorio que en el celular. Encima, una línea
con el avance («1 de 3 paradas · 22,3 km · hasta las 1:15 p. m.») y el día, un botón compacto
que dice «Hoy» con el campo de fecha nativo superpuesto; fuera de hoy, el día y «Volver a hoy»
bajan a su fila.

**El portal de familias.** La misma estructura que el panel (`.shell`, barra de marca y, por
debajo de 900 px, barra inferior) con un contenido más estrecho: hasta 1120 px. Las pantallas se
apilan como paneles blancos separados 16 px (`portal-panel`: 16 px arriba, 20 px a los lados y
abajo, esquina de panel).
- **Inicio:** en el celular, en este orden, el saludo, el plan (cuadrado y nombre, estado y la
  frase que lo explica, y las acciones secundarias, a todo el ancho), los accesos a los peludos y
  la línea en su panel. Desde 900 px, dos columnas separadas 24 px: la línea en la columna de
  lectura y el plan y los peludos en una de 340 px al lado; el saludo, encima de las dos. Lo
  vencido se agrupa, así que «Hoy» queda en la primera pantalla del celular.
- **Peludos:** cabecera con el título y «Agregar un peludo» (el verde de la vista); los accesos
  en una rejilla de `minmax(240px, 1fr)` (150 px en el inicio).
- **Ficha de un peludo:** tres bloques apilados. La identidad en un panel (volver con un botón de
  icono, el nombre, «Felino · 4 años · 4,2 kg» con el plan como cuadrado y nombre, y la foto);
  su propia línea, sin cuotas, que son de la familia; y un panel con las pestañas Carnet,
  Historia clínica y Su plan.

**Ritmo.** Escala de 4 px (`--e1` a `--e8`). Entre bloques de página 16 px; entre columnas 20
px; dentro de un panel 20–24 px; entre filas de un listado 12 px de relleno con un hilo
(`borde`) entre ellas. Los pares etiqueta/valor se separan 2 px; las fichas de datos van en
`repeat(auto-fill, minmax(180px, 1fr))`.

**Zonas táctiles.** Botones, campos, buscadores, botones de icono y cupos (`.cupo`, también los
filtros de una campaña) miden 40 px y suben a 44 px
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
  próxima de la línea. Sobre marino (la línea del acceso), el halo es `indicador-sobre-marca`.

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
  destructivo dentro de una fila. **Plano de acción** (`btn-accion`) para la acción de una fila
  que no es la principal, en el color de enlace: «Pagar esta» o «Comprobante» en los pagos del
  portal. En gris parecería deshabilitada.
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
  `Insignia` es la pastilla sin dominio. Un estado que comparte tono con otros lleva icono propio
  para distinguirse sin leer (R2-PAN-05): En ruta el pin de Rutas, En atención el pulso (los dos
  del camino normal, en tono informativo como Agendado), y la prioridad Alta una flecha hacia
  arriba, porque la × del tono peligro se lee como anulado. «Por autorizar» lleva la llave en tono
  de aviso y «Por agendar» el calendario en tono informativo (R2-PAN-08): el triángulo de alerta
  es de lo vencido, y dos seguidos en una fila diluían esa señal.

### Cards / Containers
- **Corner Style:** panel (12 px) para las columnas del listado y la ficha; tarjeta (8 px) para
  métricas, indicadores y avisos.
- **Background:** blanco sobre el lienzo.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** ninguno en los paneles; el hilo `borde` separa filas y bloques dentro de ellos.
- **Internal Padding:** 16 px en el listado, 24 px en la ficha (16 px por debajo de 900 px).
- **Bloque:** un apartado dentro de un panel (título de 14 px y su tabla o lista), separado
  24 px del anterior.
- **Ficha de datos** (`dl.ficha`): pares etiqueta/valor en la rejilla de 180 px. Cada par se
  alinea arriba (`align-content: start`), así un valor corto junto a uno de dos líneas no queda
  flotando a media altura; `.ancho` ocupa la fila entera, para lo que es texto y no dato
  («Cuándo aplica», «Qué hace», «Servicios que presta», «Especies»).

### Inputs / Fields
- **Style:** blanco, borde de control de 1 px, esquina de campo, 40 px de alto, 8 × 12 px de
  relleno. La etiqueta va encima en 13 px y 600, marino; la ayuda debajo en 12 px suave y
  enlazada con `aria-describedby`. El buscador es el mismo control con icono, para que junto a
  un `select` sean un solo tipo de control.
- **Focus:** borde azul y anillo de 1 px azul, sin contorno extra.
- **Error / Disabled:** `aria-invalid` pone el borde (y el anillo al enfocar) en rojo de error;
  deshabilitado, fondo de lienzo y texto suave. El error de un campo va debajo de él en
  `texto-error` a peso normal (`.campo > .error`, 13 px), enlazado con `aria-describedby`: la
  etiqueta es la que va en 600, el error no compite con ella.
- **Campo con icono** (`campo-adorno`): icono de 18 px a 14 px del borde izquierdo, en texto
  suave y azul de foco al enfocar; el campo sube a 48 px. Una acción dentro del campo (ver la
  contraseña, `CampoClave`) es un botón redondo de 36 px a la derecha, con `aria-pressed` y su
  nombre («Mostrar contraseña»).
- **Avisos** (`aviso-ok`, `aviso-error`): recuadro tintado del tono de estado con esquina de
  campo, 12 × 16 px de relleno, 13 px e icono de 16 px delante. El icono no encoge
  (`flex-shrink: 0`) y se alinea con la primera línea: con dos líneas de texto, un icono
  aplastado deja de leerse.
- **Listas y fechas:** con la forma del sistema, no la del navegador. Una lista (`select`) no
  muestra el control nativo: su flecha son dos `linear-gradient` de 5 px que dibujan una «v» en
  el rol de texto suave (`--flecha-lista`), a 13–18 px del borde derecho, y el relleno derecho
  crece para dejarle sitio. El calendario de un campo de fecha es una máscara de 18 px pintada
  con el mismo rol. Deshabilitados, flecha y calendario pasan a `texto-deshabilitado`. Los
  degradados dibujan un glifo, no rellenan una superficie: no contradicen la regla de los
  paneles sin degradado.
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
- **Portal:** la misma barra de marca y la misma barra inferior, con la marca compacta y cinco
  destinos (Inicio, Peludos, Citas, Pagos, Mis datos) que caben siempre: no hay «Más». A la
  derecha, el avatar de la cuenta con su menú (cerrar sesión). Por debajo de 900 px los destinos
  bajan a la barra inferior.

### Tabs
- Sobre Radix Tabs (`Pestanas`): 13 px en 700, texto suave, subrayado de 3 px verde hondo en la
  activa y hilo bajo la lista. Por debajo de 600 px no se reparten en varias filas: se desplazan
  en la suya.

### Ventanas (Modal)
- Sobre Radix Dialog: blanca, esquina de panel, sombra flotante, 560 px de ancho como máximo y
  20 px de relleno, sobre el velo marino. Cabecera (título de 16 px, descripción de 13 px suave y
  cierre con botón de icono) y pie fijos; solo el cuerpo se desplaza, así la acción principal
  del pie se ve siempre. El pie va alineado a la derecha sobre un hilo.
- **Confirmación sin cuerpo:** sin `children`, la ventana es solo título, descripción y pie. El
  título nombra lo que se hace y a quién («Desactivar a Luisa Gómez», «¿Luisa Gómez pasa a
  Comercial?», «Apagar Cali»), la descripción dice su efecto, y el botón de cancelar nombra lo que
  se conserva («Mantener el acceso», «Dejar en Operaciones», «Dejarlo activo»). Si hace falta un
  dato (el motivo de anular), lleva cuerpo.
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
- Hoy la usan las pestañas de Familias, las bandejas (Tareas, Cartera, Preventivos,
  Conversaciones, Remisiones, Usuarios y los eventos de la pasarela), los mensajes de Campañas,
  los convenios de una clínica, la liquidación, los beneficios de un plan y las consultas de la IA; las tablas de los demás módulos la adoptan en su
  unidad de la hoja de ruta.

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
  de un servicio). La de un preventivo pendiente abre su siguiente paso para todos los preventivos
  que reúne: la autorización de una vez si a alguno le falta («Antes de agendar la visita, la
  familia tiene que autorizarlo»), si no la ventana para agendar el primero sin visita, y si ya la
  tiene, «Abrir la visita». La acción la inyecta `App.tsx` (`GestionarPreventivo`), para que
  Familias no dependa de Preventivos; sin ella, la estación lleva a la pestaña de mascotas.
- **Miniatura (`LineaMini`):** en cada fila del listado, línea de 2 px con puntos de 10 px y la
  marca de hoy de 2 × 12 px; es dibujo (`role="img"`) con el resumen en `aria-label`, y la fila
  repite las vencidas en texto.

### La línea del portal (componente propio)
`LineaPortal` es la línea de la familia contada a la familia: vertical siempre, abierta en «Hoy»
y en un panel blanco. Las estaciones no son botones: cada una dice en palabras qué es y, si
toca, lleva su acción debajo. La familia no tiene por qué leer un diagrama.
- **Línea:** 8 px del color del plan (`data-color`), o gris sin plan; cada parada dibuja su
  tramo y la primera y la última lo cierran en pastilla. Columna de 24 px para la estación y el
  texto a 16 px; entre una parada y la siguiente, un hilo sobre el texto.
- **Estaciones:** las mismas formas de 24 px con borde de 4 px que la línea de la familia (hecha
  llena, vencida roja con el icono de alerta, próxima con anillo marino y halo verde hondo de
  3 px, futura en contorno). Título en 14 px marino (rojo de error si está vencida), con la
  fecha delante en cifras tabulares; detalle en 13 px suave.
- **Hecho, plegado:** todo lo anterior a hoy que ya se hizo va en una sola estación llena con
  la pastilla «N hechas» (la del tramo plegado), que despliega la lista con fecha y qué.
- **Vencido, agrupado:** las cuotas vencidas en una estación («3 cuotas vencidas · $ 225.000»,
  los meses y «Pagar …»); los preventivos vencidos en otra («7 preventivos vencidos desde el 4
  nov», cuántos por peludo con enlace a cada uno, y «Agendar» o el motivo por el que aún no se
  puede). Una visita vencida va suelta. Los grupos se ordenan por lo más antiguo.
- **Hoy:** una marca marina de 24 × 4 px que cruza la línea y «Hoy · jue 12 nov» en etiqueta.
- **Lo que viene:** cada estación con su fecha y su título («· Michi» en la del inicio; en la
  ficha del peludo sobra). Una cuota muestra su valor; un servicio, su distintivo y el enlace a
  las citas.
- **Próximo cobro:** si el estado de cuenta anuncia un cobro cuya cuota aún no existe (el plan
  en pausa no las genera), entra como estación «Próximo cobro» con su valor y sin botón de pago.
- **Cierre:** si no hay nada después de hoy, la línea no muere en «Hoy»: cierra con una
  estación en contorno y una frase que dice qué aparecerá ahí.
- **Una sola acción verde:** `accionPrincipal` la elige por urgencia (pagar lo vencido, si no
  agendar los preventivos vencidos, si no pagar la próxima cuota); las demás acciones de la
  línea son secundarias y, sin ninguna de esas tres, la línea no lleva verde. En el celular las
  acciones ocupan su fila y la principal sube a 48 px y 16 px.

### Acceso a un peludo
- Tarjeta blanca (esquina de tarjeta, mínimo 56 px de alto) que abre la ficha: foto o huella en
  un círculo de 40 px con hilo y fondo de lienzo, el nombre en marino y debajo «N vencidos» en
  rojo de error y 600, o «Al día» en suave. Mientras la línea no ha llegado no dice ninguna de
  las dos. Hover en verde tenue.
- En la ficha, sin foto, la huella va en el mismo círculo a 56 px, no en un hueco vacío.

**La regla del estado dicho.** El estado del plan se le dice a la familia con sus palabras: una
pastilla (Activo, Cuotas vencidas, «En pausa» con tono de aviso, Cancelado) y al lado una frase
que explica por qué y qué hacer («Tus 3 cuotas vencidas pausaron el plan. Al pagar, Luna y Michi
recuperan sus beneficios.»). La pastilla y la frase usan la misma palabra; el panel conserva la
del equipo («congelada»). Los cupos del plan se dicen de frente («le quedan 4 de 6 este año»,
«sin tope de usos este mes»), nunca «ilimitado». Si se puede agendar o no lo decide el plan, y
la línea dice por qué antes de ofrecerlo.

**La regla de hoy a la vista.** En el portal, «Hoy» está en la primera pantalla del celular: lo
hecho se pliega y lo vencido se agrupa en vez de crecer una estación por cuota o por vacuna.

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

### Servicios y Tareas (R2-PAN-05)
Servicios hereda el listado con ficha; Tareas, la tabla apilable.
- **Listado agrupado por día:** rótulo en etiqueta («HOY · SÁB 14 NOV · 4», con su recuento) y
  filas con «Mascota · Tipo» en el título, la hora tabular, el titular y la ciudad debajo, y
  «Por autorizar» con icono si espera la autorización y el estado no lo dice ya. En la vista de
  la agenda, encima de Hoy, el grupo «Atrasados · N» en tono de aviso, cada fila con su fecha.
- **Ficha del servicio:** título de 24 px, la identidad («Rocky (canino) · Jorge Ramirez») en
  14 px y color de texto para leerla de pie, y una fila de acciones con una sola verde: salir en
  ruta si es a domicilio, iniciar o completar la atención. Completar se bloquea mientras falten
  pasos obligatorios, o mientras no se sepa cuáles faltan, y dice cuáles. Cancelar va en rojo
  plano y se confirma con `btn-peligro`. En el celular, la principal ocupa su fila a 48 px.
- **Pasos de la atención como estaciones:** línea de 4 px en `ruta-pendiente`, estación hecha
  llena de marino con el check, el obligatorio que falta en contorno marino con «Obligatorio» en
  tono de aviso, el opcional en contorno gris. En atención abre en el primero que falta y, al
  guardarlo, pasa al siguiente; con un paso abierto, el único verde es «Guardar paso».
- **Tareas:** la tarea con su estado al lado y debajo su área y a quién afecta, con enlaces; lo
  vencido con icono y la palabra («jue 5 nov · vencida»), nunca solo en rojo.

### El Inicio del panel (componentes propios, R2-PAN-04)
«La línea de hoy»: el día del equipo como una línea de metro, con las cifras del período encima.
- **Franja de cifras** (`FranjaCifras`): seis celdas blancas separadas por hilos (un hueco de 1 px
  sobre fondo `borde`), en 2, 3 o 6 columnas según el contenedor. Cada celda: etiqueta de 12 px,
  cifra de 24 px en 600, la variación contra el período comparable con flecha y palabra («3 más»,
  «12%», «4 puntos»; verde oscuro si es buena noticia, rojo de error si es mala, suave si no
  cambia) y su serie en miniatura de 2 px en `--serie-1`, cortada donde no hay dato y punteada en
  el mes en curso, con punto hueco. Con qué se compara se dice una vez, en la línea del saludo.
- **La cifra abre su serie**: la celda es un botón (`aria-expanded`); abierta, fondo de selección
  y subrayado verde hondo de 3 px abajo. Debajo se abre un panel con el título («Recaudo en los
  últimos 12 meses»), la cifra con su variación, la fórmula del indicador y el gráfico. Escape lo
  cierra y devuelve el foco a la cifra.
- **Gráfico de serie** (`GraficoSerie`): un solo eje, rejilla de hilo sólida, líneas de 2 px,
  puntos de 8 px con anillo de 2 px del color de superficie, el año bajo el primer mes rotulado y
  donde cambia, y el mes en curso punteado con el punto hueco y una nota que lo dice. La cruz da el
  valor de cada mes con el cursor o con las flechas (con anuncio para lectores de pantalla), y
  «Ver los datos» abre la misma serie como tabla apilable. Versión `compacto` (180 px) en la
  columna del Inicio.
- **Línea del día** (`LineaDelDia`): la gramática de la línea de la ruta, marina, en un panel. Lo
  vencido agrupado arriba con un ejemplo («El más atrasado: Ana Ruiz, 84 días»), la marca de Hoy y
  lo que viene; cada estación lleva su acción. La primera acción es el único verde de la vista;
  las de consulta («Ver», «Ver la agenda») nunca lo llevan.

**La regla de las series que se distinguen.** Las series 1 y 2 del manual (verde-600 y
naranja-600) son casi iguales para quien no distingue el rojo del verde (ΔE 2,7, medido con el
validador de la skill `dataviz`). Un gráfico de dos series usa la 1 y la 3 (verde y azul,
ΔE 20,4); uno de una serie, la 1. El rojo nunca es una serie.

### Bandejas (componente común: Tareas, Cartera, Preventivos, Conversaciones, Remisiones y Usuarios)
Lo que hay por resolver, en una `tabla-apilable` a todo el ancho de un panel blanco.
- **Vistas:** un selector segmentado (pastilla hundida con hilo, 4 px de relleno; la vista activa
  en blanco y marino, las demás en texto suave, 13 px en 700) con el recuento de cada vista en
  cifras tabulares a la derecha de su nombre, suave y en texto en la activa: cuánto hay sin
  entrar. Es un grupo de botones con `aria-pressed`; la vista vive en la URL.
- **Filtros:** en una fila, las vistas, el buscador y las listas. Por debajo de 1180 px las vistas
  ocupan su fila y el buscador baja junto con las listas (si no, la ciudad bajaba sola y el
  buscador cortaba su texto). Por debajo de 600 px, cuatro vistas van en dos filas de dos (al
  desplazarse, la activa quedaba fuera) y tres en una fila de tres; buscador y listas, a todo el
  ancho.
- **Fila:** el título en marino y, debajo, el detalle en 13 px suave separado 12 px por pieza. La
  acción de la fila es suave, a la derecha; apilada, la primera va a todo el ancho, al pulgar.
- **Lo vencido:** icono de alerta, fecha (o importe) y la palabra, en rojo de error y 600: «⚠ 4 nov
  · vencido», «⚠ $ 225.000 · hace 85 días». El separador cierra la primera pieza, así que si
  bajan de línea ninguna empieza con él, y cada pieza baja entera.

### Cartera y Preventivos (R2-PAN-08)
Dos bandejas de trabajo: cada fila dice a quién, cuánto o qué, desde cuándo, y lleva la única
acción que le toca.
- **Cartera:** vistas «En mora» (la de entrada), «Por renovar» (contratos en su ventana de 90 días)
  y «Todos», en una fila de tres en el celular. Cada fila: el titular, que lleva a la pestaña
  Cartera de su familia, con el plan como cuadrado y nombre, el número de contrato y la ciudad
  debajo; lo que debe, vencido con icono o «Al día» en suave; la cuota con su periodicidad («$
  75.000 al mes», en una sola pieza); la renovación en fecha compacta y «· ya se puede renovar» si
  la API lo dice; y el estado de la afiliación. Las acciones son suaves: «Registrar pago» si debe y
  «Renovar» si se puede; con las dos, renovar pasa a plano de acción. El verde solo aparece en la
  ventana que se abre.
- **Registrar pago:** la ventana abre con la cuota más antigua elegida, nombrada por su mes
  («Cuota de octubre», «Cuota de enero a marzo», el año solo si no es este) y su saldo, el valor
  puesto en ese saldo y una ayuda debajo del campo: «Le faltan $ 75.000 a esta cuota.». Renovar
  confirma en una ventana que dice qué pasa («su vigencia se extiende un año con el mismo plan y
  la misma cuota») con «Ahora no» y «Renovar un año».
- **Preventivos, por siguiente paso:** pestañas «Por hacer» y «Carnet por mascota». La bandeja
  tiene las vistas «Por autorizar», «Por agendar», «Agendados» y «Todos», y es una sola tabla con
  un grupo (`tbody`) por familia: la cabecera de columnas una vez y las columnas alineadas. La
  cabecera del grupo es el titular (enlace de 16 px en 700) con «Bogota · 7 preventivos» en suave
  y, si algo espera autorización, «Escribir» (plano de acción, WhatsApp) y «Registrar autorización
  (7)» (suave). Cada fila: «Luna · Antirrábica canina» con la dosis debajo, la fecha en que toca,
  el estado y la única acción de su paso («Agendar visita»); el resto («Registrar aplicación sin
  visita», «Cancelar preventivo» en rojo) va en el menú de tres puntos.
- **El estado solo donde no lo dice la vista:** la columna Estado aparece en «Agendados» y
  «Todos»; en «Por autorizar» y «Por agendar» repetirlo en cada fila era ruido. Un agendado
  muestra el distintivo de su visita y su día y hora, enlazados al servicio.
- **Apilada:** cada grupo se separa 12 px; la cabecera del grupo pierde su hilo y sus acciones
  bajan debajo del titular, la autorización estirada. El menú de la fila va arriba a la derecha
  del bloque, junto a su título, no en una fila propia.
- **Autorización de una familia:** una ventana con todos los pedidos marcados (quien atiende
  desmarca lo que la familia no autorizó), cada uno con su casilla a la izquierda y el texto al
  lado aunque ocupe dos líneas («Qué autorizó»), «Por dónde respondió» y la ayuda «Si no autorizó,
  lo desmarcado sigue pendiente y lo marcado se cancela». El pie: «No autorizó» en rojo plano y el
  verde «La familia autorizó los 4».
- **Carnet por mascota:** la familia y la mascota arriba; el carnet en tres columnas (Aplicados,
  Vencidos, Próximos), cada una con su recuento en una pastilla del tono. Cada fila lleva el icono
  de preventivos en un cuadrado de 38 px; en Vencidos, el cuadrado en tono de peligro y «⚠ Tocaba
  el 4 nov · vencido» con la gramática de la bandeja. El verde de la vista es «Emitir carnet PDF».

**La regla de una sola redacción.** Un preventivo se escribe igual en la bandeja, la estación y la
autorización: «Luna · Antirrábica canina, refuerzo» (`pedido`). La dosis es «dosis N» en la serie
inicial y «refuerzo» después, sin número: «dosis 1, refuerzo» se leía como dos cosas a la vez.

### Comercial y Campañas (R2-PAN-09)
Los dos en listado con ficha, con el registro abierto en la URL (`?interesado=`, `?campana=`).
«Nuevo interesado» y «Nueva campaña» son verdes solo sin ficha abierta; con ella pasan a suaves,
porque el verde es de la ficha.
- **Interesados:** vistas «Abiertos», «Afiliados» y «Perdidos» con su recuento en el selector
  segmentado (`comercial-vistas`, a todo el ancho del listado), el buscador debajo y una línea
  suave con el mes («Este mes: 8 interesados · conversión 0%»). En «Abiertos», agrupados por
  etapa en el orden del embudo con el rótulo de los días de Servicios («CONTACTADO · 3», el
  recuento de la API); en las otras dos, una lista con el distintivo de la etapa. Cada fila: el
  nombre y, debajo, cómo llegó, la ciudad y el último contacto en fecha compacta.
- **La línea de etapas** (`ol.comercial-etapas`): las cinco etapas (Nuevo, Contactado, Cotizado,
  En afiliación, Afiliado) con la geometría de la guía de la consulta, pero sin botones: no se
  salta de etapa. Línea de 8 px en `ruta-pendiente` con lo recorrido en marino (`--avance`), punto
  de 24 px lleno en lo hecho y anillo marino con halo verde de 3 px en la actual, con su nombre en
  700 y `aria-current="step"`. Un perdido la deja toda pendiente y dice su motivo debajo. Por
  debajo de 600 px la línea usa también el relleno de la ficha (margen negativo de 16 px):
  «Contactado» en negrita no cabía en su columna.
- **Ficha del interesado:** el nombre a 34 px, el distintivo de la etapa con el celular (con
  `telefono()`), el correo y la ciudad; las acciones; la línea; los datos (responsable como lista
  que se cambia ahí, cómo llegó, plan sugerido, mascotas, primer contacto y, si ya es familia,
  «Abrir su ficha»); y la conversación. «En afiliación» no tiene «Pasar a»: lo dice una nota («Se
  afilia desde Familias…»). «Marcar como perdido» va en el menú de tres puntos y abre una ventana
  con el motivo en una lista y el `btn-peligro`; un perdido tiene «Reactivar» como verde.
- **La conversación como burbujas:** un fondo hundido con esquina de tarjeta, hasta 420 px de alto
  y abierto en lo último. Lo que escribió la persona, en blanco a la izquierda; lo que le
  respondimos, en `accion-suave-fondo` a la derecha; cada burbuja ajustada a su texto (hasta
  `min(48ch, 85%)`) con la fecha y la hora en 12 px suave debajo, y «· no se envió» si falló. La
  dirección se dice también para lectores de pantalla («Escribió:», «Respondimos:»). Encima, la
  insignia del estado: «Espera a un asesor» en aviso con el icono de mensaje, o «Atiende el
  asistente» en informativo. Debajo, el campo para responder y, a la derecha, «Devolver al
  asistente» (plano) y «Enviar».
- **Bandeja de conversaciones:** la gramática de las bandejas, con tres vistas en una fila
  (`bandeja-vistas-tres`, etiquetas cortas: «Por atender», «Con el asistente», «Todas»). Cada
  fila: el interesado (o el celular con `telefono()`) y si es interesado o familia afiliada; lo
  que contó al asistente con cada dato por su nombre en palabras («Ciudad», «Plan sugerido»,
  nunca la clave del guion); el último mensaje; el estado; y una acción suave: «Abrir
  conversación» lleva a la ficha del interesado, «Responder» abre una ventana para una familia.
- **Ficha de la campaña:** el nombre, su estado y cuándo sale (fecha con el día, hora y, si se
  repite, «cada mes»); a quién le llega y la plantilla en Meta como datos; la audiencia en una frase («Le llega
  a **3** de 3 familias», y cuántos se dieron de baja de los mensajes) y ejemplos del mensaje como le llega a cada familia,
  con la burbuja saliente de la conversación (`campana-ejemplo`, hasta 56ch); el envío; y «Cómo le
  fue», con las cifras (enviados, entregados, leídos, respondidos, no se enviaron) en celdas
  blancas separadas por hilos como la franja del Inicio, y «Destinatarios en CSV» en plano de
  acción.
- **Envío con un solo verde:** el botón dice lo que hará: «Enviar ahora» con el campo de fecha
  vacío, «Programar envío» con él. Programar sale sin confirmar (se cancela antes de salir);
  enviar ahora confirma en una ventana que dice a cuántas («Enviar ahora a 3 familias», que los
  mensajes no se retiran, la plantilla y el segmento) con «Volver» y el verde. «Cancelar campaña»
  va en rojo plano y confirma con `btn-peligro` y «Mantenerla».
- **Mensajes:** una tabla apilable con el mensaje, la dirección en palabras («Escribió» o «Le
  escribimos a») y el celular con `telefono()` debajo, cuándo y el estado; nunca una flecha sola.
  Los enlaces de un solo uso llegan ya tapados de la API (`token=[oculto]`): el panel no muestra
  credenciales en un registro. Las bajas, en el rail.

**La regla del verde de quien espera.** En la ficha de un interesado, si su conversación espera a
un asesor, el verde es «Enviar» (contestarle) y «Pasar a <etapa>» queda suave; si no, el verde es
pasar a la etapa siguiente que dice la API (`siguiente_etapa`; el panel no copia el embudo) y
«Enviar» queda secundario.

### Aliadas y Administración (R2-PAN-10)
Lo que se toca poco, con los dos patrones ya construidos: lo que hay por resolver en bandeja y cada
registro en listado con ficha, abierto en la URL (`?clinica=`, `?plan=`, `?regla=`). Como en
Comercial, «Nueva clínica» y «Nuevo plan» son verdes solo sin ficha abierta.
- **Remisiones:** bandeja con «Por usar» (la de entrada, la que vence antes primero),
  «Utilizadas», «Anuladas» y «Todas», con su recuento de la API; «Emitir remisión» es el verde.
  Cada fila: el titular y la mascota («Jorge Ramirez · Rocky», enlace a la familia) con el código y
  el motivo debajo; la clínica; lo que cubre (`cobertura()`: «80 % hasta $ 200.000»); y cuándo
  vence. La vencida (lo dice la API, `vencida`) lleva icono y «Venció el 4 nov» con la gramática de
  lo vencido; una utilizada cambia la columna a «Atendida», con la fecha de la atención, y la
  cobertura a «Cubrió $ 180.000». La columna Estado solo aparece en «Todas». La única acción de una
  remisión por usar es «Anular», plana en rojo; abre una ventana con el motivo, «Mantenerla» y
  `btn-peligro` «Anular remisión», y la descripción dice qué pasa («la clínica ya no la acepta y el
  cupo del beneficio vuelve a la familia. No se deshace»).
- **Ficha de la clínica:** el nombre a 34 px, la ciudad y el teléfono (`telefono()`, también el
  fijo: «601 765 4321»); «Nuevo convenio» como verde y activar o desactivar en el menú de tres
  puntos (inactiva, una nota: «no recibe remisiones nuevas», y el verde deshabilitado). NIT,
  dirección y servicios como ficha de datos; los convenios (beneficio y plan, cubre, tarifa,
  vigencia) en tabla apilable; y las remisiones por usar como lista con hilo, sin tabla: el titular
  y la mascota en 700, el código y «Vence el 4 dic» (o vencida, con icono) debajo, con una línea de
  recuentos encima («1 por usar · 3 atendidas · 0 anuladas»).
- **Liquidación:** el período (Desde y Hasta) en una fila de dos campos de hasta 180 px, que en el
  celular reparten el ancho; la tabla apilable con una fila por clínica (NIT debajo del nombre) y
  un `tfoot` de total en 700 marino sobre un hilo de 2 px, que apilada es un bloque más. Las
  columnas de cifras van a la derecha. «Descargar CSV» es suave: la vista no tiene verde.
- **Usuarios:** bandeja con «Equipo», «Clínicas aliadas», «Familias» e «Inactivos» (la API agrupa y
  cuenta), buscador y una nota fija encima: cambiar el perfil o desactivar cierra sus sesiones al
  instante. Cada fila: el nombre con el correo y el teléfono debajo; el perfil como lista que se
  cambia ahí (solo en el equipo activo) y confirma en una ventana con el verde «Cambiar el perfil»;
  y «Desactivar» plano en rojo, que confirma con `btn-peligro`. Activar de nuevo es directo, suave.
  La propia fila lleva la insignia «Tú» y ni lista ni acciones.
- **Ficha del plan:** el plan como cuadrado y nombre, «Editar plan» como verde y activar o
  desactivar en el menú. Debajo, «Valor mensual por peludo» («1 peludo», «2 peludos (c/u)»… como
  ficha de datos, con la nota de que cuenta la afiliación entera), el pago por período, los beneficios en
  tabla apilable («2 al año», «Ilimitado») y «Se vende en 12 ciudades» con las ciudades en una línea
  separadas por «·».
- **Reglas:** el listado agrupado por evento con el rótulo de los días de Servicios («AVISOS
  ESCALONADOS DE MORA · 4»); cada fila dice en palabras cuándo aplica (`condicion_texto`). La ficha:
  el nombre, el evento, «Editar regla» como verde y activar o desactivar en el menú; «Cuándo aplica»
  y «Qué hace» (`accion_texto`) a todo el ancho, prioridad y «Si aplica» como datos. El JSON solo
  aparece en la ventana de editar. Una regla de un evento retirado lleva la insignia «Retirada» y
  una nota que dice por qué; no tiene acciones ni «Probar»: se lee, no se edita.
- **Probar esta regla:** un bloque dentro de la ficha con un campo con nombre por dato que mira la
  condición («Días de mora»; ninguno si aplica siempre, y lo dice) y «Probar» suave. El resultado,
  en un recuadro hundido con esquina de tarjeta: «Esta regla aplica.» o «no aplica con estos
  datos», en negrita, y las reglas del evento que aplicarían, cada una con lo que hace en palabras.
- **Catálogos:** ciudades, tipos de servicio y esquemas preventivos en filas, con una nota encima
  que dice qué deja de pasar al apagar. Cada fila lleva su estado escrito («Activo» en tono ok,
  «Apagado» en neutro) y la acción al lado: «Apagar» plano, que confirma en rojo con la nota como
  descripción y «Dejarlo activo»; «Encender», suave y directo. No se borran: hay registros que los
  usan.
- **Inteligencia artificial:** el gasto del mes en indicadores (`dolares()`: «US$ 50,00»; cuatro
  decimales en el costo de una consulta) y la barra del presupuesto; los prompts, cada versión con
  su distintivo de estado, «Correr casos» en plano de acción y «Activar» suave, y las instrucciones
  plegadas. Un solo verde: «Cargar versiones iniciales» sin prompts, «Nueva versión» con ellos.
- **Eventos de la pasarela:** bandeja con «Con error» (la de entrada), «Procesados» y «Todos» en
  una fila de tres; cada evento en palabras («Cambio en un pago», «Wompi»), el error debajo en rojo,
  el estado con su distintivo y «Reprocesar» suave en los que no se procesaron.

**La regla de lo que se deshace.** Lo reversible que no sale del registro (desactivar un plan, una
regla o una clínica) va en el menú de tres puntos y se hace sin preguntar. Lo que no se deshace, o
cuyo efecto alcanza a otros (anular una remisión, desactivar a alguien o cambiarle el perfil, que
cierran sus sesiones, apagar una ciudad), se confirma en una ventana que dice ese efecto: en
`btn-peligro` si quita algo, en verde si es el camino normal. Deshacerlo (activar, encender) es
directo.

**La regla de las palabras de la API.** El panel no muestra códigos del backend: la API dice cada
cosa en palabras (`condicion_texto`, `accion_texto`, `retirada`, los grupos de usuarios, de quién
es una remisión y si venció) y los estados llegan a la vista por `Distintivo` con su nombre. El
panel no deduce nada de un código ni copia una regla del backend para decidir qué mostrar.

### El acceso (R3-PUB-01)
Ingreso, recuperación, restablecimiento y activación comparten `AccesoLayout`: el único sitio de
la aplicación donde la marca se presenta, y un formulario que no hace nada más (ver Layout).
- **Panel de marca (desde 900 px):** marino plano (`superficie-marca`), sin tarjeta, sin borde y
  sin sombra, 40 px de relleno arriba y abajo. Arriba, el logo completo en blanco (`MarcaTimu
  claro`, 104 px de alto); a media altura, la frase de la pantalla en GeosansLight de 34 px en
  blanco («Tu peludito, bien cuidado.»; en la activación, «Te damos la bienvenida a la manada
  TIMU.») y, 40 px debajo, la línea de marca; abajo, la nota «Datos protegidos · Ley 1581 de
  2012» con el icono del escudo, en 13 px y marino-200 (`texto-sobre-marca-suave`).
- **Franja (por debajo de 900 px):** el mismo marino, 20 × 16 px de relleno, con el logo compacto
  en blanco (28 px) y debajo la línea en miniatura: estaciones y marca de Hoy sin rótulos ni la
  palabra «Hoy». La frase y la nota se ocultan; la nota baja bajo el formulario, separada por un
  hilo y con el escudo en verde oscuro (`accion-suave-texto`).
- **La línea de marca** (`LineaDeMarca`): el año de una familia (Afiliación, Vacunas, Visita en
  casa, Renovación) en la señalética del metro y con los colores que admite el marino (regla 6
  del manual). Tramo de 8 px; lo recorrido en verde-500 (`indicador-sobre-marca`), lo que falta
  translúcido (`borde-sobre-marca`). Estaciones de 24 px con borde de 4 px: hechas llenas de
  verde-500; la próxima con anillo blanco y halo verde-500 de 3 px, su rótulo en blanco y 600;
  la programada en contorno marino-200 sobre el marino. «Hoy», justo antes de la próxima, es una
  marca blanca de 4 × 24 px con «Hoy» en etiqueta blanca encima. Las cuatro columnas son
  `minmax(max-content, 1fr)` y los rótulos (13 px, marino-200) no se parten: la línea crece antes
  que cortar «Visita en casa». Es dibujo (`aria-hidden`): no dice nada que la pantalla necesite.
- **Formulario:** columna de 400 px con 24 px entre bloques y 16 px entre campos. El título en
  `h1` de 34 px y, si hace falta, una frase en texto suave debajo; campos con icono (ver
  Inputs); el verde a todo el ancho y de 48 px en 16 px (`btn-grande`); lo secundario en plano y
  centrado («Volver al ingreso», «Ir al ingreso», con la flecha de volver).
- **Quién ingresa:** bajo «Hola de nuevo», un selector segmentado (Radix Tabs) «Equipo TIMU»
  (icono de clínica) / «Familias» (huella). Equipo, también la clínica aliada: correo,
  contraseña, «¿Olvidaste tu contraseña?» a la derecha y «Ingresar». Familias: el celular
  registrado con la ayuda «Te enviamos un código de un solo uso por WhatsApp.», el verde «Recibir
  código» y debajo, plano, «Ingresar con contraseña» (correo o celular), que vuelve con «Recibir
  un código por WhatsApp». Enviado el código, un aviso ok nombra el número con `telefono()` y el
  campo del código va centrado a 20 px con espaciado ancho. Si se llega desde una ruta del portal,
  el selector abre en Familias. Credenciales que no coinciden se dicen en palabras propias («El
  correo o la contraseña no coinciden»); un bloqueo o una caída, con su causa.
- **Recuperación:** «Recupera tu acceso» con «Correo o celular» y «Enviar enlace». Enviada, el
  título cambia a «Revisa tu correo o tu WhatsApp» y la frase nombra el dato escrito («Si hay una
  cuenta con <lo que escribió>, en unos minutos te llega un enlace…»), igual exista o no la cuenta.
- **La pantalla del enlace** (`RestablecerPage`, `/restablecer` y `/activar`): antes de pedir
  nada, la API dice si el enlace sirve (`POST /auth/enlace`, con el token en el cuerpo: vigente,
  usado, vencido o inválido, su propósito y el nombre de pila). Mientras comprueba, un esqueleto
  de tres líneas con «Comprobando el enlace…» para lectores de pantalla. Vigente: «Hola, Ana», la
  frase según el propósito, la contraseña nueva con «Al menos 8 caracteres.» y su confirmación
  (si no coinciden, el error bajo el campo y el verde deshabilitado), y el verde «Activar mi
  cuenta» o «Guardar y entrar». Al guardar se entra directo, al espacio de cada perfil. Si el
  enlace deja de servir con la pantalla abierta, el aviso de error lo dice con «Pide uno nuevo».
- **El enlace que no sirve:** el título dice qué pasó («Este enlace ya se usó», «Este enlace
  venció», «Este enlace no sirve», «El enlace está incompleto») y la frase qué hacer; el verde es
  «Pedir un enlace nuevo» y «Ir al ingreso» va plano y centrado. Si el servidor no respondió:
  «No pudimos comprobar el enlace», el aviso con su causa y, si el error es pasajero,
  «Reintentar» como verde (la comprobación comparte el límite del ingreso y no se reintenta
  sola).

**La regla del enlace que se dice de entrada.** El acceso no pide una contraseña con un enlace que
no sirve: lo dice la API al abrirlo, y la pantalla responde a lo que dijo. El panel no deduce el
estado de un enlace ni deja escribir dos veces la clave para enterarse después.

**La regla de la frase que le habla a quien llega.** El panel de marca dice una frase a la persona
que llega, no vende la plataforma: ni funciones con icono, ni antetítulo. La frase cambia con la
pantalla (la activación le da la bienvenida a la familia) y el título del formulario la saluda
por su nombre cuando la API lo sabe.

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
- **Do** en el portal, abre la línea en «Hoy», pliega lo hecho y agrupa lo vencido, y deja que
  `accionPrincipal` elija la única acción verde de la línea.
- **Do** acompaña el estado del plan, para la familia, de una frase que diga por qué y qué hacer.
- **Do** escribe lo vencido de una bandeja con icono, fecha o importe y la palabra, y cada
  preventivo con la misma redacción (`pedido`, `dosis`) en todas partes.
- **Do** confirma lo que no se deshace diciendo su alcance («Enviar ahora a 3 familias»): en verde
  si es el camino normal, con `btn-peligro` si anula (cancelar, marcar como perdido).
- **Do** di la dirección de un mensaje en palabras («Escribió», «Le escribimos a») y los
  teléfonos con `telefono()`.
- **Do** lleva lo reversible al menú de tres puntos, y en una confirmación nombra en el botón de
  cancelar lo que se conserva («Mantenerla», «Mantener el acceso», «Dejarlo activo»).
- **Do** muestra lo que la API dice en palabras (`condicion_texto`, `accion_texto`, estados con
  nombre) y los importes en dólares con `dolares()`.
- **Do** en un aviso o una frase que nombra un teléfono, escríbelo con `telefono()` y envuélvelo
  en `.sin-cortes`: «300 123 4567» no se parte entre dos líneas.
- **Do** en el acceso, pregunta a la API si un enlace sirve antes de pedir la contraseña, y ante
  uno que no sirve ofrece «Pedir un enlace nuevo» como el verde.

### Don't:
- **Don't** escribas un color a mano ni nombres un paso de la paleta fuera de `tokens.css`.
- **Don't** pongas sombra, borde de adorno ni degradado en paneles, tarjetas o barras.
- **Don't** pongas una etiqueta en mayúsculas encima de un título como antetítulo: la etiqueta
  nombra el dato o el bloque que tiene debajo.
- **Don't** deduzcas el color de un plan de su nombre ni uses el color de plan como estado.
- **Don't** uses verde o naranja de marca como texto sobre claro (regla 1 del manual); sobre
  marino (la barra o el panel de marca del acceso) solo blanco, marino-200, verde-500 y
  naranja-500 (regla 6), más el translúcido `borde-sobre-marca` para lo que es tramo o hilo.
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
- **Don't** uses el triángulo de alerta para un estado que no está vencido: «Por autorizar» lleva
  la llave.
- **Don't** muestres un código del backend a la vista (`dias_mora gte 25`, `borrador`, `aliada`):
  si la API no lo dice en palabras, se arregla en la API.
- **Don't** confirmes en verde lo que anula o desactiva, ni pongas un interruptor o una casilla
  suelta que apague algo sin decir qué deja de pasar.
- **Don't** pongas en el panel de marca un antetítulo en pastilla, una tarjeta de vidrio
  (`backdrop-filter`) ni sombra, ni una lista de funciones con icono: es marino plano con el logo,
  la frase y la línea.
- **Don't** pidas una contraseña con un enlace del que no sabes si sirve, ni digas que venció
  después de que la persona la escribió dos veces.
