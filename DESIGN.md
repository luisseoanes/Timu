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
  plan-varios: "#111537"
  plan-verde-texto: "#111537"
  plan-naranja-texto: "#111537"
  plan-azul-texto: "#FFFFFF"
  ruta-recorrida: "#111537"
  ruta-pendiente: "#85889D"
  linea-aliadas: "#98B833"
  serie-1: "#769116"
  serie-2: "#477095"
  serie-3: "#BE7700"
  serie-4: "#111537"
typography:
  portada:
    fontFamily: "GeosansLight, Inter Variable, Inter, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 1.75rem + 2.2vw, 3.625rem)"
    fontWeight: 400
    lineHeight: 1.02
    letterSpacing: "-0.01em"
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
  barra-publica:
    backgroundColor: "{colors.superficie-marca}"
    textColor: "{colors.texto-sobre-marca}"
    height: "64px"
    padding: "0 40px"
  pie-de-foto:
    backgroundColor: "{colors.superficie-marca}"
    textColor: "{colors.texto-sobre-marca}"
    typography: "{typography.body-menor}"
    rounded: "{rounded.pastilla}"
    padding: "6px 12px"
  pastilla-plan:
    backgroundColor: "{colors.plan-verde}"
    textColor: "{colors.plan-verde-texto}"
    typography: "{typography.body-menor}"
    rounded: "{rounded.campo}"
    padding: "8px 12px"
    height: "56px"
  pastilla-plan-naranja:
    backgroundColor: "{colors.plan-naranja}"
    textColor: "{colors.plan-naranja-texto}"
  pastilla-plan-azul:
    backgroundColor: "{colors.plan-azul}"
    textColor: "{colors.plan-azul-texto}"
  arma-tu-plan:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.texto}"
    rounded: "{rounded.panel}"
    padding: "24px"
  estacion-red:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.pastilla}"
    size: "24px"
  estacion-intercambio:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.pastilla}"
    size: "36px"
---

# Design System: TIMU

Este fichero describe lo construido, no lo planeado. La primera superficie del sistema es la
estructura del panel del equipo (`AppLayout`) y Familias (listado, detalle, pestañas y
ventanas); después, Rutas (la ruta del día del médico y su coordinación) y Clínica (la historia de
cada mascota, la consulta guiada y sus plantillas), el Inicio (las cifras del período y la línea del día), Servicios y Tareas (el listado con
ficha de los servicios y la bandeja), Cartera y Preventivos (sus bandejas, el carnet y el
preventivo atendido desde su estación) y Comercial y Campañas (los interesados del embudo con su
conversación, la bandeja de conversaciones y las campañas en listado con ficha) y Aliadas y
Administración (las remisiones y los usuarios en bandeja; las clínicas, los planes y las reglas en
listado con ficha). El portal de familias está rediseñado entero: la
estructura, el inicio y los peludos (R3-POR-01) y las citas, los pagos y los datos (R3-POR-02).
De las páginas públicas, el acceso (R3-PUB-01): ingreso, recuperación, restablecimiento y
activación de la cuenta; y las dos a las que se llega desde un enlace (R3-PUB-03): la encuesta
que recibe la familia por WhatsApp y la verificación del carnet preventivo para un tercero; y el
registro en línea (R3-PUB-02): la familia arma su manada, elige el plan de cada peludo, paga y
completa sus datos; y la portada de timu.com.co con la página de cada plan (R3-PUB-04, «Álbum de
la manada»), con lo que de ella se edita en Administración. La plantilla pública anterior
(`.publica-tarjeta`) se retiró; `.publica` nombra ahora el marco de la web pública
(`MarcoPublico`). La
clínica aliada tiene su espacio rediseñado: Mi clínica (R3-ALI-01), el mostrador donde valida el
código de una remisión, reporta la atención y ve lo atendido en el mes.
Cada perfil del equipo ve solo sus módulos y su propio Inicio (el
administrador, lo que falta configurar; el médico, su jornada); Mensajes y Encuestas son módulos
propios. Ningún módulo del panel queda ya en la maqueta anterior; lo que falta para cerrar el rediseño está
en [`docs/hoja-de-ruta-rediseno.md`](docs/hoja-de-ruta-rediseno.md). El color, la tipografía, el logo y la voz los fija el
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
- **Verde de la red** (`linea-aliadas`, el mismo verde-500): la línea y las estaciones de «La red
  TIMU» en la portada. Es dibujo, no plan ni estado: la red no es de ningún plan, por eso tiene rol
  propio en vez de tomar `plan-verde`.

### Secondary
- **Azul TIMU** (`foco`, `texto-enlace`): anillo de foco y enlaces. Es el color de la
  navegación y la información, no de la acción. Un enlace dentro de una frase (sin clase, dentro de
  `p`, `li`, `dd` o `span`) va además subrayado con 1 px, para distinguirse sin el color (WCAG
  1.4.1); los que son controles por sí mismos (botones planos, navegación, filas) llevan clase y no
  se subrayan.

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
catálogo (`data-color`), nunca del nombre del plan. Donde el plan se elige (el registro en línea),
la opción lleva el borde de 2 px del color del plan y, elegida, se llena de él con su par de texto
(`plan-verde-texto` y `plan-naranja-texto` marino, `plan-azul-texto` blanco, en `@pares` a 4.5).

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
- **Portada** (GeosansLight 400, `--t-portada` de 2.5rem a 3.625rem / 40 a 58 px según el ancho,
  1.02, −0.01em, `text-wrap: balance`): solo el `h1` de la web pública, «Tu peludito, bien
  cuidado.» en el panel del álbum y el nombre del plan en la cabecera de su página, en blanco sobre
  marino. Uno por página.
- **Display** (GeosansLight 400, `--t-display` 2.125rem / 34 px, 1.2, −0.01em en la ficha): el
  nombre de la familia abierta, el saludo y el título del acceso («Hola de nuevo», «Hola, Ana»,
  «Este enlace venció»). Uno por pantalla; en la web pública es el `h2` de cada sección, con 1.1
  de interlineado («La red TIMU», «Quiénes somos», «Lo que cubre»). En el portal todo `h1` va a este tamaño: «Hola, Ana»,
  «Tus peludos» y el nombre de cada peludo. En el acceso, la frase del panel de marca va también
  a 34 px, en blanco sobre marino; no es un título (`p`), y por debajo de 900 px desaparece.
- **Cifra** (600, `--t-cifra` 1.5rem / 24 px): cifras destacadas de indicadores.
- **Headline** (GeosansLight 400, `--t-titulo` 1.25rem / 20 px, 1.2): título de página
  (`cabecera-pagina`).
- **Title** (600, `--t-seccion` 1rem / 16 px, 1.2): encabezado de bloque, título de ventana,
  cabecera del listado.
- **Body** (400, `--t-cuerpo` 0.875rem / 14 px, 1.55): texto de la interfaz, botones, celdas. El
  texto de cada apartado de una consulta que se lee (`consulta-lectura`) llega hasta 75ch.
- **Menor** (400–600, `--t-menor` 0.8125rem / 13 px): metadatos, pestañas, módulos de la barra,
  rótulos de estación.
- **Label** (700, `--t-etiqueta` 0.75rem / 12 px, `--tracking-etiqueta` 0.09em, mayúsculas, `texto-suave`): cabeceras
  de columna, `dt` de una ficha de datos, la etiqueta de cada valor en la tabla apilada, los
  encabezados de los bloques Mascotas y Cartera del resumen, y «Hoy» en la línea. Nada baja de
  12 px.

### Named Rules
**La regla de la escala fija.** El tipo se mide en rem con los siete pasos de `tokens.css`; una
interfaz de trabajo no escala el tipo con la ventana (nada de `clamp()` ni `vw` en tamaños de
letra). En pantallas táctiles o por debajo de 900 px, campos y buscadores suben a 1rem para que
iOS no amplíe la página al enfocar. La única excepción es `--t-portada`, el titular de la web
pública, que se presenta en vez de trabajar: crece de 40 a 58 px con la ventana. Ningún otro tamaño
de la web pública escala, y nada del panel, el portal ni la clínica aliada usa `--t-portada`.

**La regla de las cifras tabulares.** Importes, fechas, totales y contadores llevan `.numero`
(`font-variant-numeric: tabular-nums`) donde se comparan en columna o se actualizan.

**La regla de la etiqueta que nombra.** La etiqueta en mayúsculas nombra un dato o un bloque de
datos; es el título de lo que tiene debajo, nunca una línea decorativa encima de otro título.
Vale también en la web pública, donde más tienta (decidido con el usuario el 2026-11-18): ni el
álbum, ni las secciones, ni la cabecera de un plan llevan antetítulo; lo que diría pasa al título o
a la frase. Sí nombran lo de debajo las etiquetas de Misión y Visión, las de cada dato de contacto,
las de las condiciones de un plan y las de cada grupo de enlaces del pie.

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
primera pantalla del celular. La encuesta hereda el acceso entero (`AccesoLayout`, en
`src/components/`) con `arriba`: desde 900 px el formulario se ancla arriba, a 80 px del borde
(`.ingreso-contenido-arriba`), en vez de centrarse; por debajo de 900 px ya lo está.

**La verificación del carnet.** Sin barra, sin panel de marca ni tarjeta: una columna de hasta
760 px centrada sobre el lienzo (`.verificacion`: 24 px arriba, 16 a los lados y 40 abajo), con
32 px entre bloques. Arriba, el logo compacto a color de 32 px de alto; debajo, el veredicto,
cerrado por un hilo; las secciones del carnet; y el pie, abierto por otro hilo. Es la misma
columna en el escritorio y en el celular: las tablas se apilan por su contenedor.

**El registro en línea (`MarcoRegistro`).** El registro, el resultado del pago y el formulario de
la familia comparten marco: es el mismo viaje. Sin barra de módulos: una franja marina
(`superficie-marca`, 16 px de relleno) con el logo compacto en blanco de 28 px, y debajo, sobre el
lienzo, `.registro-cuerpo` hasta 1120 px (32 px arriba, 16 a los lados, 40 abajo) en dos columnas
separadas 32 px: el contenido en una columna de hasta 680 px (`.registro-manada`,
`.registro-pago`, 20 px entre bloques) y el resumen de la manada en una de 340 px, fijo al bajar
(`position: sticky`, 24 px del borde). Por debajo de 900 px, una columna (20 px arriba y 180 abajo)
y el resumen se vuelve una barra fija abajo (`--capa-barra`, borde arriba, sin esquina ni sombra,
con el área segura) que solo dice el total y el verde; la lista de la manada y la confianza se
ocultan, y el contacto baja al final del contenido (`.registro-solo-celular`). Cuando el verde de
la vista es otro (en el pago) o ya no lo hay (después del pago), el resumen deja de ser barra y va
como bloque al final (`.registro-resumen-quieto`: panel blanco con esquina de panel y la lista
entera).

**La web pública (`MarcoPublico`: la portada en `/` y cada plan en `/planes/<plan>`).** Sin
`.shell`: una barra marina pegada arriba (`position: sticky`, 64 px, `--capa-barra`, 40 px de
relleno a los lados) con el logo, las cuatro secciones (Planes, Aliadas, Nosotros, Contacto, que son
anclas de la portada también desde cada plan), «Ingresar» y «Afiliar a mi peludo»; debajo, el
contenido sobre el lienzo; al final, el pie marino. Desde 1024 px el logo es el completo, con su
fila de animales, a 40 px de alto; por debajo, el compacto a 30 px, las secciones e «Ingresar»
pasan a un menú de tres puntos y la barra deja 16 px a los lados. Las secciones van a todo el
ancho con su fondo y centran su contenido a 1200 px (`padding-inline: max(20px, (100% − 1200px) /
2)`), con 80 px arriba y abajo (40 y 16 a los lados por debajo de 600 px) y `scroll-margin-top`
del alto de la barra para que el ancla no quede debajo de ella. Los fondos alternan: lienzo en
Planes y Nosotros, blanco en Aliadas y Contacto. La cabecera de una sección es el `h2` y su frase,
hasta 680 px, con 32 px hasta el contenido. Un enlace «Saltar al contenido» aparece con el foco
antes de la barra.

**El álbum (la primera pantalla de la portada).** Desde 1100 px, dos tercios de mosaico y un
tercio de panel marino (`2fr` y `minmax(420px, 1fr)`), de alto `min(100vh − 64 px, 860 px)`. El
mosaico va sobre el lienzo con 10 px de hueco y de marco (sin marco hacia el panel): la foto
principal ocupa las dos filas de la izquierda y dos fotos se apilan a la derecha (columnas y filas
en 1,6 : 1). El panel deja 56 px arriba y 40 a los lados, con 20 px entre el titular, la frase, las
pastillas de los planes y «Arma tu plan». Entre 720 y 1099 px, una columna: el mosaico arriba con
dos filas de 200 px y el panel debajo en dos columnas separadas 32 px, el texto y las pastillas a
la izquierda y «Arma tu plan» a la derecha (300–400 px), arriba. Por debajo de 720 px, una sola
foto ancha (la principal, 16 : 10) y el panel en una columna (24 px arriba, 16 a los lados, 16 entre
bloques), con el titular y «Arma tu plan» en la primera pantalla.

**La página de un plan.** La cabecera es una sección marina a todo el ancho (56 px arriba, el
contenido a 1200 px) que cierra con una franja de 10 px del color del plan; dentro, el texto y la
línea del plan (ver Components). Debajo, sobre el lienzo, dos columnas separadas 40 px: lo que
cubre y los adicionales a la izquierda, y a la derecha una de 360 px con el precio y las
condiciones, fija al bajar a 16 px de la barra. Por debajo de 900 px, una columna y lo de la
derecha deja de ser fijo; por debajo de 600, la línea del plan pasa a vertical.

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

**La clínica aliada (Mi clínica).** La estructura del portal (`.shell`, barra marina con la marca
compacta y la cuenta) sin destinos ni barra inferior: la aliada tiene una sola pantalla. Entre la
marca y la cuenta, el nombre de la clínica (ver Navigation). El contenido llega hasta 1120 px, como
el portal, y es un mostrador (`.aliada-mostrador`): desde 900 px, dos columnas alineadas arriba y
separadas 20 px, el trabajo en el resto (el código, la remisión abierta y su reporte) y lo atendido
en una de 300–380 px. Por debajo de 900 px se apilan separadas 16 px, el código primero y lo
atendido debajo. Cada columna es un panel blanco plano (`.aliada-panel`: esquina de panel, 24 px de
relleno y 20 px entre bloques; 16 y 16 por debajo de 900 px).

**Ritmo.** Escala de 4 px (`--e1` a `--e8`). Entre bloques de página 16 px; entre columnas 20
px; dentro de un panel 20–24 px; entre filas de un listado 12 px de relleno con un hilo
(`borde`) entre ellas. Los pares etiqueta/valor se separan 2 px; las fichas de datos van en
`repeat(auto-fill, minmax(180px, 1fr))`.

**Zonas táctiles.** Botones, campos, buscadores, botones de icono y cupos (`.cupo`, también los
filtros de una campaña) miden 40 px y suben a 44 px
por debajo de 900 px o con puntero grueso. Con la misma condición suben a 44 px las pestañas, cada
opción de un selector segmentado, el círculo de la cuenta y el botón del tramo plegado de una línea
(«N hechas», «Ver cada una»). Los enlaces seguidos de una línea de detalle de bandeja miden al menos
24 px de alto, y los teléfonos de la lista de contacto 32 px (44 en táctil), para no tocar el de al
lado (WCAG 2.5.8). Todo corte «por debajo de 900 px» se escribe
`max-width: 899px`, el complemento exacto del `min-width: 900px` de la barra: a 900 justos todo el
sistema está ya en escritorio.

### Named Rules
**La regla del contenedor.** Lo que cambia de forma según el sitio que tiene lo decide su
contenedor, no la ventana: junto al listado, la ficha es estrecha en un escritorio ancho. La
`tabla-apilable` se apila con una container query por debajo de 640 px de su `.scroll-x`, y la
línea de la familia pasa a vertical cuando mide que sus paradas no caben con su rótulo (y
siempre por debajo de 600 px de ventana).

**La regla del formulario anclado arriba.** Un formulario cuyo contenido crece al elegir (un aviso
que aparece, una etiqueta que cambia) se ancla arriba, no se centra en el alto: centrado, lo que
aparece debajo empuja hacia arriba la opción que se acaba de tocar. En el acceso es `arriba`, que
usa la encuesta; el ingreso, de alto fijo, sigue centrado.

**La regla de la barra que deja su alto.** Una barra fija abajo que tapa el contenido le reserva
su alto al desplazar: `scroll-padding-bottom` en la raíz mientras la barra está (160 px en el
registro), además del relleno inferior del contenido, para que lo que el navegador trae a la vista
o recibe el foco no quede debajo (WCAG 2.4.11). Si la vista ya no necesita la barra, la barra deja
de ser fija.

**La regla de sin desborde.** Ninguna ruta desborda en horizontal a 375, 768, 900 ni 1280 px, ni
tiene un fallo de WCAG 2.2 A o AA según axe-core (desde R4-CIE-02, todas sus reglas, no solo el
contraste), ni encabezados que salten un nivel (el título de una tarjeta de primer nivel es un h2); las rutas con pestañas se comprueban
pestaña por pestaña, y las que abren una ficha desde la URL, con la ficha abierta. Lo vigila
`frontend/e2e-stack/responsive.spec.ts`, sin lista de excepciones: un fallo se arregla.

## Elevation & Depth

El sistema es plano. Las superficies quietas (paneles, tarjetas, barras) no llevan sombra: la
profundidad la dan el blanco sobre el lienzo, el hilo entre filas y la barra marina. Hay una sola
sombra, `--sombra-3`. Solo lo que flota sobre la pantalla —menús
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
- **Mensaje destacado** (`box-shadow: 0 0 0 2px var(--foco)`): en la conversación que se abre
  desde Mensajes, la burbuja de la que se partió. Es un anillo de estado, no profundidad.
- **Halo de intercambio** (`box-shadow: 0 0 0 6px var(--accion-suave-fondo-hover)`): la estación de
  la clínica de TIMU en «La red TIMU», la única de intercambio. No es estado: marca de dónde sale
  el ramal a casa.

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
la cuenta; en la web pública, también el pie de foto y los valores de Nosotros, que son rótulos y
no se tocan. Las fotos de la web pública llevan esquina de tarjeta (8 px) y las pastillas de los
planes, pese al nombre, esquina de campo (6 px): son enlaces, no señales. Dos radios menores para
lo que no es contenedor: `--r-fino` (2 px) en las marcas de
«Hoy», las claves de un gráfico y el marcador de plan, que es un cuadrado (el plan es identidad, no
estado), y `--r-barra` (4 px) en las barras del esqueleto y del Inicio. Ningún radio se escribe a
mano: lo comprueba `tokens.test.ts`. Los bordes son
de 1 px; los controles usan `borde-control` y los separadores `borde`. La iconografía es un solo
juego (`Icono`): trazo de 1.6, extremos y uniones redondeados, 20 px por defecto, siempre
`currentColor`.

## Components

### Comunes

#### Buttons
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

#### Chips (distintivos de estado)
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

#### Cards / Containers
- **Corner Style:** panel (12 px) para las columnas del listado y la ficha; tarjeta (8 px) para
  indicadores y avisos.
- **Título:** el de una tarjeta de primer nivel es un `h2` en su cabecera (`.tarjeta-cabeza > h2`),
  con el aspecto de encabezado de bloque (Inter, 16 px, 600), no GeosansLight; sus apartados son
  `h3`. El `h1` es el de la página.
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

#### Inputs / Fields
- **Style:** blanco, borde de control de 1 px, esquina de campo, 40 px de alto, 8 × 12 px de
  relleno. La etiqueta va encima en 13 px y 600, marino; la ayuda debajo en 12 px suave y
  enlazada con `aria-describedby`. El buscador es el mismo control con icono, para que junto a
  un `select` sean un solo tipo de control.
- **Focus:** borde azul y anillo de 1 px azul, sin contorno extra.
- **Solo lectura:** un campo que se ve pero no se cambia (el código de una plantilla de WhatsApp
  al editar su texto) lleva fondo `superficie-hundida` y texto suave, como el deshabilitado, pero
  se puede seleccionar y copiar.
- **Error / Disabled:** `aria-invalid` pone el borde (y el anillo al enfocar) en rojo de error;
  deshabilitado, fondo de lienzo y texto suave. El error de un campo va debajo de él en
  `texto-error` a peso normal (`.campo > .error`, 13 px), enlazado con `aria-describedby`: la
  etiqueta es la que va en 600, el error no compite con ella.
- **Campo con icono** (`campo-adorno`): icono de 18 px a 14 px del borde izquierdo, en texto
  suave y azul de foco al enfocar; el campo sube a 48 px. Una acción dentro del campo (ver la
  contraseña, `CampoClave`) es un botón redondo de 36 px a la derecha, con `aria-pressed` y su
  nombre («Mostrar contraseña»).
- **Avisos** (`aviso-ok`, `aviso-error`, `aviso-alerta`): recuadro tintado del tono de estado con
  esquina de campo, 12 × 16 px de relleno, 13 px e icono de 16 px delante. El icono no encoge
  (`flex-shrink: 0`) y se alinea con la primera línea: con dos líneas de texto, un icono
  aplastado deja de leerse. `aviso-alerta` (tinte de aviso) es para lo que pide actuar sin ser un
  error: en la encuesta, «Si es una urgencia, no esperes…» con el icono del mensaje.
- **Listas y fechas:** con la forma del sistema, no la del navegador. Una lista (`select`) no
  muestra el control nativo: su flecha son dos `linear-gradient` de 5 px que dibujan una «v» en
  el rol de texto suave (`--flecha-lista`), a 13–18 px del borde derecho, y el relleno derecho
  crece para dejarle sitio. El calendario de un campo de fecha es una máscara de 18 px pintada
  con el mismo rol. Deshabilitados, flecha y calendario pasan a `texto-deshabilitado`. Los
  degradados dibujan un glifo, no rellenan una superficie: no contradicen la regla de los
  paneles sin degradado.
- **Formulario:** rejilla de dos columnas con 16 px; una a 900 px o menos. Casillas y radios de
  18 px con `accent-color` verde hondo.
- **Campo con su acción** (`campo-con-accion`): un campo de hasta 360 px y su botón en una línea,
  alineados abajo para que el botón quede a la altura del campo y no de la etiqueta; el error baja a
  su fila. Lo usan «Buscar» en Supresión de datos y «Guardar» del tope de la IA, en secundario.

#### Navigation
- **Barra de marca:** marino noche, 64 px, fija. Marca en texto blanco a la izquierda; módulos
  en 13 px y 600, marino claro (`texto-sobre-marca-suave`); hover a blanco sobre marino de
  hover; activo en blanco con subrayado verde de 4 px. Buscador blanco a la derecha y avatar
  circular con iniciales en una pastilla translúcida. Foco en verde sobre la marca.
- **Saltar al contenido:** el primer elemento enfocable del panel, el portal y la clínica aliada
  (`SaltarAlContenido`), fuera de la vista hasta recibir el foco del teclado; entonces aparece
  arriba a la izquierda, sobre la barra: blanco, esquina de campo, marino en 600 y la sombra de lo
  que flota. Lleva el foco al `main` sin tocar la URL.
- **«Más»:** los módulos que no caben, en un menú (Radix DropdownMenu) blanco con esquina de
  tarjeta y sombra flotante; el elemento resaltado en verde tenue. Arriba lleva una flecha;
  en la barra inferior, tres puntos (nunca «+», que se lee como crear).
- **Barra inferior (celular):** blanca con hilo arriba, 56 px por elemento, icono de 22 px y
  rótulo de 12 px; activo en marino con una marca verde de 3 px en el borde superior.
- **Portal:** la misma barra de marca y la misma barra inferior, con la marca compacta y cinco
  destinos (Inicio, Peludos, Citas, Pagos, Mis datos) que caben siempre: no hay «Más». A la
  derecha, el avatar de la cuenta con su menú (cerrar sesión). Por debajo de 900 px los destinos
  bajan a la barra inferior.
- **Clínica aliada:** la barra del portal sin destinos y sin barra inferior. En su lugar, el nombre
  de la clínica en 13 px y 600, marino claro (`texto-sobre-marca-suave`), en una línea que se corta
  con puntos suspensivos: en un computador compartido de recepción dice en qué clínica se está. El
  menú de la cuenta lleva el nombre del usuario, «Clínica · ciudad» debajo y «Cerrar sesión».
- **El menú de la cuenta es uno** (`MenuCuenta`, en `src/components/`) en los tres espacios: las
  iniciales en la pastilla translúcida y, al abrirlo, el nombre, un detalle (el perfil en el panel,
  «Portal de familias», la clínica y su ciudad) y «Cerrar sesión».

#### Tabs
- Sobre Radix Tabs (`Pestanas`): 13 px en 700, texto suave, subrayado de 3 px verde hondo en la
  activa y hilo bajo la lista. Por debajo de 600 px no se reparten en varias filas: se desplazan
  en la suya.

#### Ventanas (Modal)
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
- **Con una franja fija arriba del cuerpo** (solo el editor de reglas, `DEU-8`): lo que resume lo
  que se está escribiendo (la regla en palabras, en una caja `superficie-hundida`) se queda fijo
  arriba del cuerpo desde 600 px, sobre una franja blanca de 12 px que corta en limpio lo que pasa
  por detrás; el resto del cuerpo se desplaza bajo ella. En la hoja inferior (menos de 600 px) no se
  fija: ocuparía media hoja.

#### Tabla apilable
- **Escritorio:** cabeceras en etiqueta (12 px, mayúsculas espaciadas, texto suave), celdas con
  12 px de relleno e hilo entre filas, fila en hover sobre lienzo, acciones a la derecha.
- **Contenedor de menos de 640 px:** cada fila es un bloque. La primera celda es su título en
  marino y 700; el resto, pares etiqueta y valor con la etiqueta (de `data-etiqueta`, que repite
  la cabecera) en la misma voz que la cabecera de columna. Las acciones bajan a una fila propia.
  La cabecera sigue en el DOM para los lectores de pantalla.
- Hoy la usan las pestañas de Familias, las bandejas (Tareas, Cartera, Preventivos,
  Conversaciones, Remisiones, Usuarios y los eventos de la pasarela), Mensajes,
  los convenios de una clínica, la liquidación, los beneficios de un plan y las consultas de la IA; las tablas de los demás módulos la adoptan en su
  unidad de la hoja de ruta.

#### Historial
- Lista de cambios con la fecha (suave, tabular) en una columna de hasta 11 rem a la izquierda y
  qué cambió a la derecha (título de 14 px y detalle suave); hilo entre entradas. Por debajo de
  600 px la fecha va encima.

#### Espera de sesión
- Mientras se comprueba la sesión (`ProtectedRoute`): la marca y un esqueleto centrados en el
  lienzo. Si falla, un aviso blanco con esquina de panel, icono de error, título de 16 px y el
  botón para reintentar. El esqueleto es una barra del color de pista que respira
  (opacidad 1 → 0.45, 1.2 s).
- **Mientras llega una pantalla** (`CargandoPantalla`): el código va partido por espacio y por
  módulo (la portada no descarga el panel), y lo que se ve mientras llega es el mismo esqueleto de
  tres líneas de una consulta que carga, con «Cargando…» para lectores de pantalla. Va dentro del
  layout (`AppLayout`, `PortalLayout`): la barra de marca y la navegación no desaparecen al cambiar
  de módulo.

#### Menú de acciones (tres puntos)
Lo que una fila o una ficha hace de vez en cuando, fuera de la vista y junto a la única acción que
le toca.
- **Disparador:** botón plano de icono con los tres puntos (18 px) y un nombre que dice de qué es
  («Más acciones de Rocky»). Abre un menú de Radix (DropdownMenu, no modal) alineado al final, con
  la forma de «Más» (blanco, esquina de tarjeta, sombra flotante, elemento resaltado en verde
  tenue).
- **Elementos:** lo destructivo en rojo de error (`menu-item-peligro`: «Dar de baja» una mascota,
  «Cancelar preventivo») y confirma en su ventana; lo reversible se hace sin preguntar (ver la regla
  de lo que se deshace). Un elemento que no aplica queda deshabilitado en texto suave, y el actual
  va en marino y 700.
- **Submenú:** un elemento que abre otra lista lleva la flecha a la derecha, lejos del texto
  («Asignar a…» en Tareas, con «Sin asignar» y quienes ven el área; quien ya la tiene, marcado y
  deshabilitado, y quien mira con «(tú)»).
- Lo usan las filas de Tareas, Preventivos y Mascotas de una familia, y las fichas de plantillas,
  clínicas, planes, reglas e interesados.

#### Bandejas (componente común: Tareas, Cartera, Preventivos, Conversaciones, Remisiones y Usuarios)
Lo que hay por resolver, en una `tabla-apilable` a todo el ancho de un panel blanco.
- **Vistas:** un selector segmentado (hundido con hilo y la esquina de un campo en todos los
  anchos, 4 px de relleno y opciones con esquina fina, concéntricas; la vista activa
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

### El panel

#### El Inicio del panel (componentes propios)
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
  las de consulta («Ver», «Ver la agenda») nunca lo llevan. Una parada de ruta cuya franja ya pasó
  sin empezarse va antes de Hoy como vencida («Su franja terminó a las 9:00 · …»).
- **Un Inicio por perfil:** Gerencia, el tablero entero (periodo, ciudad, exportar y la franja de
  seis). Comercial, Atención al cliente y Operaciones, dos o tres cifras de su área, que llenan la
  fila (`data-cuantas`; en el celular, la tercera baja a lo ancho), y la línea con solo su trabajo,
  ordenada por lo vencido de su área. El médico, «Tu jornada»: sin cifras, la línea con las
  consultas sin firmar, sus tareas vencidas y sus paradas (las atrasadas antes de Hoy) y sus tareas.
  El administrador, «Lo que falta configurar».
- **Lo que falta configurar** (`inicio-config`): una lista de filas con el icono en un cuadrado
  (`fila-icono`), el título y qué deja de pasar en texto suave («Sin ella no sale por WhatsApp…»), y
  la acción que lleva a su pestaña de Administración («Registrarla», «Ver las plantillas»,
  «Completar los datos»). Lo que bloquea lleva el triángulo con el tinte de aviso; lo demás, el
  icono de usuario. Todas las acciones son suaves e iguales: son del mismo peso, y la vista no tiene
  verde (decidido con el usuario el 2026-11-20). Sin nada pendiente, «Todo está configurado.». En
  un contenedor de 600 px o menos la acción baja bajo su texto, a lo ancho.

**La regla de las series que se distinguen.** El manual pone el azul en segundo lugar: verde,
azul, naranja y marino. Antes del 2026-11-15 las series 1 y 2 eran el verde-600 y el naranja-600,
casi iguales para quien no distingue el rojo del verde (ΔE 2,7, medido con el validador de la
skill `dataviz`), y el Inicio usaba la 1 y la 3 como excepción. Ahora un gráfico de dos series usa
la 1 y la 2 (verde y azul, ΔE 20,4) sin excepción; uno de una serie, la 1. El rojo nunca es una serie.

#### La línea de la familia (componente propio)
El elemento que identifica el producto. `LineaFamilia` dibuja el año de la familia como un plano
de metro: espaciado esquemático, no proporcional al tiempo.
- **Línea:** 8 px, pastilla, del color del plan (`data-color` del catálogo) o gris
  (`plan-ninguno`) sin plan. Con varios planes, marina (`plan-varios`): pintarla con uno diría que
  todos los peludos están en él. Entonces cada estación lleva el color del plan de su peludo (la
  de una cuota, o la que junta peludos de planes distintos, se queda en marino), también en la
  miniatura del listado; el estado (vencida, próxima) manda sobre el plan.
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

#### La línea de la ruta (componente propio)
`LineaRuta` dibuja la ruta del día con la misma gramática que la línea de la familia, en
vertical siempre: es una lista que se recorre de arriba abajo.
- **Línea:** 8 px marina, nunca del color de un plan (una ruta no es un plan). Recorrida en
  `ruta-recorrida` hasta la parada que toca; por recorrer, en `ruta-pendiente`.
- **Estaciones:** 24 px con borde de 4 px. Hecha: llena de marino. La que toca: anillo marino con
  halo verde hondo de 3 px. Pendiente: contorno gris.
- **Estados:** los del camino normal (en curso, en camino, en sitio, próxima) van en tono
  informativo; la alerta queda para lo que la merece, como lo que falta por rutear. La parada que
  toca y nadie empezó cuando su franja ya pasó dice «Atrasada» (aviso) en vez de «Próxima»: así la
  ve también quien coordina.
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

#### La guía de la consulta (componente propio)
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
  apartado, el texto hasta 75ch), con «Emitir fórmula» y «Corregir»; el título va a 24 px, no a
  34: no es el nombre de nada.

#### Las plantillas de consulta
La pestaña «Plantillas de consulta» de Clínica, en listado con ficha, con la abierta en la URL
(`?plantilla=`). La página controla la pestaña: una plantilla que aparece en la URL lleva a la
suya, y «Volver» cierra la ficha sin salir de ella.
- **Listado:** el título lleva el total, con las inactivas incluidas («Plantillas 3»). «Nueva
  plantilla», con el icono «mas», es verde solo sin ficha abierta (con ella, suave). Cada fila: el
  nombre y, debajo en texto suave, lo que prellena en palabras y en el orden de la consulta
  («Prellena el motivo de consulta y el tratamiento», «Prellena los cinco apartados», «No prellena
  ningún apartado»). Las inactivas van al final, con la insignia neutra «Inactiva».
- **Ficha:** el nombre; la insignia «Activa» o «Inactiva», «Prellena 2 de 5 apartados», cuánto se
  ha usado («Usada en 12 consultas firmadas», «Usada en 1 consulta firmada» o «Aún sin consultas
  firmadas»; solo cuentan las firmadas y vigentes) y, si la plantilla es de un tipo de atención,
  «Para <tipo>» en minúscula. «Editar plantilla» es el verde; «Desactivar plantilla» o «Activar
  plantilla» va en el menú de tres puntos y se hace sin preguntar. Inactiva, una nota dice qué deja
  de pasar: «Inactiva: la consulta ya no la ofrece. Las consultas que
  partieron de ella no cambian.». Debajo, los apartados con texto en `consulta-lectura`, y una nota
  con el resto: «Deja en blanco la anamnesis, el examen físico y el diagnóstico.».
- **Ventana:** la misma para crear y editar, con el pie «Guardar plantilla». «Nombre» y «Tipo de
  atención» comparten fila (por debajo de 900 px se apilan). El tipo es opcional: una lista que
  empieza en «Cualquier atención», y su ayuda dice qué significa lo elegido: «Se ofrece en cualquier visita.» o «En una visita solo
  se ofrece si es de este tipo.». Debajo, un área de texto de tres líneas por apartado, a lo ancho y con el título de la
  consulta. La descripción dice el alcance: al editar, «Los cambios valen para las consultas
  nuevas; las que ya partieron de ella no cambian.». El código lo saca la API del nombre y no se
  pide ni se muestra. Al crear, se abre la ficha de la plantilla creada.
- **Qué ofrece la consulta:** la lista «Plantilla» del primer apartado, al crear la consulta. La de
  una visita agrupa «Para esta visita» (las de su tipo) y «Generales» (las de cualquier atención),
  y no ofrece las de otra atención; si ninguna es de su tipo, las generales van sin grupo. Mientras
  no se conoce el tipo de la visita, o si falla, solo las generales. Sin visita, todas y sin
  agrupar.

#### Servicios y Tareas
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
- **Tareas:** vistas «Mis tareas» (la de entrada si hay propias; si no, «Sin asignar»), «Pedidas
  por mí», «Sin asignar», «Vencidas» y «Todas». Cada fila: la tarea con su estado al lado y debajo
  su área, quién la pidió («Pedida por Luisa Gómez (Comercial)») o de dónde salió si es automática,
  y a quién afecta, con enlaces; la descripción en una sola línea (el texto entero en su título). Lo
  vencido con icono y la palabra («jue 5 nov · vencida»), nunca solo en rojo.
- **Una sola acción por tarea:** a la vista, suave, la que le toca a quien mira: «Tomar» si nadie la
  tiene, «Cerrar» si es suya, «Ver la conversación» si viene del asistente de WhatsApp (se cierra
  sola al terminarla). El resto (asignarla con el submenú «Asignar a…», iniciarla, cerrarla, ver la
  familia) va en el menú de tres puntos. Solo se asigna a quien ve el área de la tarea; una de otra
  área, en «Pedidas por mí», se sigue sin acciones.

#### Cartera y Preventivos
Dos bandejas de trabajo: cada fila dice a quién, cuánto o qué, desde cuándo, y lleva la única
acción que le toca.
- **Cartera:** vistas «Vencidas» (la de entrada: toda cuota vencida; «en mora» es el estado del
  contrato desde el día 5, y el Inicio lleva aquí con «Ver las vencidas»), «Por renovar» (contratos en su ventana de 90 días)
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
  cabecera del grupo es el titular (enlace de 16 px en 700) con «Bogotá · 7 preventivos» en suave
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

#### Comercial y Campañas
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
- **Mensajes** (módulo propio): una tabla apilable con el mensaje, la dirección
  en palabras («Escribió» o «Le escribimos a») y el celular con `telefono()` debajo, cuándo y el
  estado; nunca una flecha sola. Encima, el buscador («Buscar en el mensaje o el número», se lleva
  la fila), «Quién escribió», el estado y «Desde» y «Hasta» con su etiqueta encima, a su ancho. El
  texto del mensaje es un botón de 44 px que se lee como la fila (subrayado al pasar) y abre la
  conversación en una ventana, con las mismas burbujas (`BurbujaMensaje`, en `src/components/`),
  desplazable dentro (hasta `min(60vh, 560px)`) y con el mensaje del que se partió a la vista,
  rodeado por el anillo de foco de 2 px y con `aria-current`.
  Los enlaces de un solo uso llegan ya tapados de la API (`token=[oculto]`): el panel no muestra
  credenciales en un registro. Las bajas, en el rail.

**La regla del verde de quien espera.** En la ficha de un interesado, si su conversación espera a
un asesor, el verde es «Enviar» (contestarle) y «Pasar a <etapa>» queda suave; si no, el verde es
pasar a la etapa siguiente que dice la API (`siguiente_etapa`; el panel no copia el embudo) y
«Enviar» queda secundario.

#### Aliadas y Administración
Lo que se toca poco, con los dos patrones ya construidos: lo que hay por resolver en bandeja y cada
registro en listado con ficha, abierto en la URL (`?clinica=`, `?plan=`, `?regla=`). Como en
Comercial, «Nueva clínica», «Nuevo plan» y «Nueva regla» son verdes solo sin ficha abierta (con
ella, suaves).
- **El índice de Administración:** sus diez secciones en cuatro apartados (Equipo; Planes y
  catálogos; Automatizaciones; TIMU y privacidad), como los ajustes de una aplicación: una columna
  de 232 px a la izquierda, fija al desplazar, con el título de cada apartado en etiqueta y sus
  secciones como enlaces de 40 px; la abierta en blanco, en marino y 600 (`aria-current`), sin
  borde de color. Desde 1180 px; por debajo, un selector «Sección» con los apartados como grupos,
  encima de la sección, para no quitarle ancho a sus fichas. Cada sección tiene su dirección
  (`?pestana=`), y una ficha pedida por enlace (`?plan=`) completa la suya.
- **Remisiones:** bandeja con «Por usar» (la de entrada, la que vence antes primero),
  «Utilizadas», «Vencidas» (las que vencieron sin usarse y liberaron el cupo), «Anuladas» y «Todas»,
  con su recuento de la API; solo «Por usar» tiene acciones; «Emitir remisión» es el verde.
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
  columnas de cifras van a la derecha. «Descargar CSV» es suave: la vista no tiene verde. Cada
  clínica abre debajo el detalle de sus atenciones, el mismo del CSV: su nombre es un botón de 44 px
  en 600 marino con una flecha suave que gira al abrir (`aria-expanded`), y el detalle es una fila
  sobre `superficie-hundida` con su propia tabla apilable (remisión, atendida y beneficio a la
  izquierda; valor, lo que cubre TIMU y lo que paga la familia a la derecha).
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
  ESCALONADOS DE MORA · 4»); cada fila dice en palabras cuándo aplica (`condicion_texto`). «Nueva
  regla», con el icono «mas», va en la cabecera del listado; sin reglas, «Aún no hay reglas. Crea la
  primera con «Nueva regla».». La ficha:
  el nombre, el evento, «Editar regla» como verde y activar o desactivar en el menú; «Cuándo aplica»
  y «Qué hace» (`accion_texto`) a todo el ancho, prioridad y «Si aplica» como datos. Ni la ficha ni
  la ventana muestran JSON: la regla se escribe por campos (abajo). Una regla de un evento retirado
  lleva la insignia «Retirada» y una nota que dice por qué; no tiene acciones ni «Probar»: se lee,
  no se edita.
- **Editor de reglas (DEU-8):** una sola ventana para crear y editar, con la franja fija de
  Ventanas. Título «Nueva regla» (descripción «Elige cuándo se revisa, cuándo aplica y qué hace.»)
  o «Editar «Aviso de mora a los 25 días»» con el evento como descripción; el pie, «Crear regla» o
  «Guardar». De arriba abajo, en el formulario de dos columnas (una por debajo de 900 px):
  - **La regla en palabras:** una caja hundida (`superficie-hundida`, esquina de tarjeta, relleno
    de 12 por 16 px) con dos datos, «CUÁNDO APLICA» y «QUÉ HACE» en etiqueta (12 px, 600,
    mayúsculas espaciadas, texto suave) y su frase debajo en 600 marino, 12 px entre uno y otro. La
    API la rehace con el borrador 300 ms después del último cambio; mientras falta algo dice
    «Completa cada condición y lo que hace para leer la regla entera.», al pedirla «Leyendo la
    regla…» en apagado, y si la API la objeta, su error en rojo.
  - **«Cuándo se revisa»** (el evento, solo al crear, con su ayuda debajo) y **«Nombre»**, a lo ancho.
  - **«Cuándo aplica»:** la leyenda en 14 px, 600, marino. Desde dos condiciones, «Aplica si se
    cumplen» con «Todas las condiciones» o «Al menos una», en una lista de hasta 16rem. Cada
    condición es una fila de lista con hilo arriba (y abajo la última), 12 px de relleno vertical,
    en dos filas en todos los anchos: «Dato» en dos columnas con el «quitar» a su derecha (botón
    plano de icono «cerrar», columna de 44 px); debajo «Comparación» y «Valor», o, para «es uno de»,
    las casillas «Valores» a todo el ancho en columnas de 9rem como mínimo (leyenda de 13 px). Cada
    control lleva su etiqueta visible y un nombre accesible con su número («Dato de la condición
    2»). Debajo, «Añadir una condición» u «Otra condición» en botón secundario con el icono «mas»;
    sin condiciones, la nota «Sin condiciones: aplica siempre.». Una condición con grupos dentro de
    grupos no se edita: se lee su frase y una nota dice que se escribió fuera del panel y que al
    guardar se conserva.
  - **«Qué hace»:** la «Acción» en lista si el evento admite varias; si admite una, como dato
    («Acción» en 13 px, 600, marino, como etiqueta de campo, y «Avisar por WhatsApp» debajo en
    texto), no como otro título. Sus parámetros siguen en el formulario; un texto libre o una lista
    con algún nombre de más de 24 caracteres («Aviso de mora · aún sin registrar») van a todo el
    ancho.
  - **«Orden y vigencia»:** «Prioridad» (con la ayuda «Las de un mismo evento se evalúan de menor a
    mayor.»), «Si aplica» («Sigue con las siguientes» o «No evalúa las siguientes»), «Planes» a lo
    ancho si el evento lo admite («Todos los planes» o «Solo <plan>»), «Vale desde» y «Vale hasta».
  - **«Para qué sirve»:** un área de texto de dos líneas, a lo ancho.

  Al crear, se abre la ficha de la regla creada (`?regla=`): lo siguiente es probarla.
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
  El tope mensual se cambia ahí mismo («Tope mensual (US$)» y «Guardar» en secundario, en un campo
  con su acción), con la nota de que al llegar al tope la IA se apaga hasta el mes siguiente.
- **Plantillas de WhatsApp:** una nota encima dice que Meta aprueba cada plantilla y que al marcar
  aprobada la versión más reciente pasa a ser la que se envía. «Editar texto», en plano de acción,
  solo en la versión más reciente de cada una; abre «Editar «Aviso de mora»» con la descripción de
  lo que pasa («El texto nuevo queda como versión 3, en borrador. Hasta que Meta lo apruebe…») y el
  código de solo lectura, porque cambiarlo sería otra plantilla.
- **Supresión de datos:** el documento y «Buscar» en un campo con su acción; la familia encontrada
  en una fila con sus mascotas y su estado, «Ya anonimizada» (neutro) o «Contrato vigente» (aviso,
  con la frase de quién lo cancela antes) cuando no se puede. Anonimizar confirma en una ventana
  «Anonimizar a <titular>» que dice que no se recupera, con «No anonimizar» y `btn-peligro`.
- **Eventos de la pasarela:** bandeja con «Con error» (la de entrada), «Procesados» y «Todos» en
  una fila de tres; cada evento en palabras («Cambio en un pago», «Wompi»), el error debajo en rojo,
  el estado con su distintivo y «Reprocesar» suave en los que no se procesaron.

**La regla de lo que se deshace.** Lo reversible que no sale del registro (desactivar un plan, una
regla o una clínica) va en el menú de tres puntos y se hace sin preguntar. Lo que no se deshace, o
cuyo efecto alcanza a otros (anular una remisión, desactivar a alguien o cambiarle el perfil, que
cierran sus sesiones, apagar una ciudad), se confirma en una ventana que dice ese efecto: en
`btn-peligro` si quita algo, en verde si es el camino normal. Deshacerlo (activar, encender) es
directo.

**La regla de la regla leída antes de guardarla.** Quien escribe una regla la lee como la leerá
el equipo antes de guardarla: la frase de arriba del editor la arma la API con el borrador
(`/reglas/describir`), no el panel, y queda a la vista mientras se escribe. El control y la frase
dicen lo mismo («al menos», «como mucho», «igual a», «más de», «menos de», «distinto de»), y un dato
del catálogo se nombra, nunca por su código.

**La regla de las palabras de la API.** El panel no muestra códigos del backend: la API dice cada
cosa en palabras (`condicion_texto`, `accion_texto`, `retirada`, los grupos de usuarios, de quién
es una remisión y si venció) y los estados llegan a la vista por `Distintivo` con su nombre. El
panel no deduce nada de un código ni copia una regla del backend para decidir qué mostrar.

### El portal de la familia

#### La línea del portal (componente propio)
`LineaPortal` es la línea de la familia contada a la familia: vertical siempre, abierta en «Hoy»
y en un panel blanco. Las estaciones no son botones: cada una dice en palabras qué es y, si
toca, lleva su acción debajo. La familia no tiene por qué leer un diagrama.
- **Línea:** 8 px del color del plan (`data-color`), o gris sin plan; con varios planes, marina, y
  cada estación en el color del plan de su peludo, como la de la familia. Cada parada dibuja su
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

#### Acceso a un peludo
- Tarjeta blanca (esquina de tarjeta, mínimo 56 px de alto) que abre la ficha: foto o huella en
  un círculo de 40 px con hilo y fondo de lienzo, el nombre en marino y debajo «N vencidos» en
  rojo de error y 600, o «Al día» en suave. Mientras la línea no ha llegado no dice ninguna de
  las dos. Hover en verde tenue.
- En la ficha, sin foto, la huella va en el mismo círculo a 56 px, no en un hueco vacío.

#### Los avisos del plan y la urgencia
- **En pausa:** con cuotas vencidas, el panel del plan del inicio y la pestaña «Su plan» de cada
  peludo llevan debajo de la frase lo que sigue disponible y lo que no (`aviso_pausa`, lo escribe el
  backend) en un `portal-aviso` (13 px, hasta 70 ch); los beneficios dejan de llevar el check de
  disponibles.
- **Sin poder afiliar otro peludo:** si la API da un motivo (`motivo_sin_alta`), Peludos y «Agregar
  un peludo» no ofrecen el formulario ni el verde: dicen el motivo en un aviso y, si la familia
  debe, «Ir a tus pagos» al lado.
- **«Escríbenos por WhatsApp» es un enlace:** en cualquier texto del portal, también los que llegan
  del backend (`ConWhatsApp`), la frase enlaza al WhatsApp que guarda Administración → Datos de
  TIMU; sin número guardado queda como texto.
- **La urgencia:** en la ventana de hablar con un veterinario, antes del formulario y separada 16 px
  de su primer campo, «¿Es una urgencia? Llámanos al …» con el primer teléfono de TIMU (con `telefono()`)
  como enlace `tel:`; sin teléfono, el enlace de WhatsApp.

**La regla del estado dicho.** El estado del plan se le dice a la familia con sus palabras: una
pastilla (Activo, Cuotas vencidas, «En pausa» con tono de aviso, Cancelado) y al lado una frase
que explica por qué y qué hacer («Tus 3 cuotas vencidas pausaron el plan. Al pagar, Luna y Michi
recuperan sus beneficios.»). La pastilla y la frase usan la misma palabra; el panel conserva la
del equipo («congelada»). Los cupos del plan se dicen de frente («le quedan 4 de 6 este año»,
«sin tope de usos este mes»), nunca «ilimitado». Si se puede agendar o no lo decide el plan, y
la línea dice por qué antes de ofrecerlo.

**La regla de hoy a la vista.** En el portal, «Hoy» está en la primera pantalla del celular: lo
hecho se pliega y lo vencido se agrupa en vez de crecer una estación por cuota o por vacuna.

### La clínica aliada

#### Mi clínica
El espacio de la clínica aliada (`/aliada`) es un mostrador: a la izquierda, el código que trae la
familia y la remisión que abre, con su reporte; a la derecha, lo atendido en el mes (ver Layout).
De la familia solo se ve lo necesario para atender: el titular, los últimos dígitos de su documento
y la mascota.
- **El código:** el `h1` «Validar una remisión» y debajo una fila con el campo y «Validar»,
  alineados por el campo. El campo del código (`.codigo-input`, el mismo del ingreso por WhatsApp)
  va en 20 px, centrado y con espaciado ancho (0,5 em), en mayúsculas aunque se escriba en
  minúsculas (se ve como se valida), en una columna de hasta 320 px y de 48 px de alto; «Validar»
  se iguala a ese alto. Por debajo de 600 px el campo toma el ancho que deja el botón. La ayuda
  («El que trae la familia. Da igual en mayúsculas o en minúsculas.») va debajo de los dos.
- **Un solo verde que se mueve:** sin remisión abierta, o con una que no se puede usar, el verde
  es «Validar». Con una remisión por usar, «Validar» pasa a secundario y el verde es «Reportar
  atención», a la derecha al pie del reporte; por debajo de 900 px, a todo el ancho, de 48 px y en
  16 px.
- **Mientras valida y si falla:** un esqueleto de tres líneas con «Validando la remisión…» para
  lectores de pantalla. Un código que no existe en esta clínica es un aviso de error con icono que
  nombra el código en `.numero` y dice qué hacer («Revisa el código con la familia: si está bien
  escrito, la remisión es de otra clínica o TIMU no la ha emitido»); otro error, el aviso con su
  causa y «Reintentar» si es pasajero.
- **La línea de estado:** la remisión abierta empieza bajo un hilo, con 20 px arriba y 16 entre
  bloques. Primero el distintivo y debajo, a 8 px, la frase, con el mismo ritmo en todos los
  estados y anchos: «Por usar» (ok) «Se puede atender hasta el 16 dic.»; «Vencida» (peligro, con
  icono) «Venció el … y ya no se puede usar para atender. Lo atendido hasta ese día se puede
  reportar hasta el …» (o, vencida sin usarse y pasado ese plazo, «Venció el … sin usarse y ya pasó
  el plazo para reportar.», sin botón de reporte), y «La familia puede pedirle una nueva a TIMU.»;
  «Atendida» (neutro, con el check) «Ya se reportó: la atención fue el …»; «Anulada» (neutro)
  «TIMU la anuló y ya no se puede usar.». La línea es `role="status"`.
- **La remisión abierta:** la mascota como `h2` de 24 px (GeosansLight, marino) con «· Canino,
  Labrador» en el mismo renglón, en la fuente de texto a 14 px y suave. Debajo, el titular en prosa
  («Jorge Ramírez, documento terminado en 6123»), con «documento terminado en 6123» en
  `.sin-cortes` y los dígitos en `.numero`: si la línea se parte, la cierra la coma, no un «·»
  suelto, y el dato que se verifica no se corta. Después, la ficha
  de datos: Motivo a todo el ancho; Beneficio, Cobertura (`cobertura()`: «80 % hasta $ 200.000») y
  Código.
- **La vencida sin usar:** bajo la ficha, un botón plano de acción «Reportar una atención hecha
  hasta el 6 nov» (la fecha es `atencion_hasta`): una atención hecha dentro de su vigencia se
  reporta después, también si la vigencia la cortó la baja de la familia. Abre el mismo reporte con
  el foco en la fecha y su envío en secundario: «Validar» sigue siendo el verde, porque lo normal
  ante una vencida es no atender, y el formulario no queda abierto invitando a reportar.
- **El reporte** (con la remisión por usar, o abierto a propósito sobre una vencida): bajo un hilo, el `h3` «Reportar la atención» y el
  formulario de dos columnas: la fecha, limitada a las fechas que dice la API (`atencion_desde`,
  `atencion_hasta`, y con la última por defecto), y el valor, numérico, que se escribe y se ve con
  formato («$ 180.000»). Debajo, a todo el ancho y en `aria-live`, el reparto que calcula la API
  para ese valor, unos 300 ms después de dejar de escribir: «TIMU cubre» y «Paga la familia» en
  cifras. Solo se pinta cuando la respuesta corresponde al valor escrito; antes, una nota dice qué
  falta («Escribe el valor para ver cuánto cubre TIMU y cuánto le cobras a la familia.»,
  «Calculando cuánto cubre TIMU…»). Si el valor llega al tope, una nota lo dice («Llega al tope de
  $ 200.000 de esta remisión: el resto lo paga la familia.»). Al final, el resumen clínico (hasta
  75 ch) con su ayuda, que nombra a la mascota.
- **Tras reportar:** la remisión pasa a «Atendida», el código se vacía y el campo recupera el foco:
  el mostrador queda listo para la siguiente familia.
- **Lo reportado:** en una remisión atendida, bajo un hilo, «Lo que se reportó» (`h3` en la fuente
  de texto, 600) con tres cifras en pasado: «Valor de la atención», «TIMU cubrió» y «Pagó la
  familia».
- **Lo atendido:** el `h2` «Atendidas» y, al lado, el mes como lista (el mes en curso y los doce
  anteriores, «noviembre de 2026»), guardado en la URL (`?mes=2026-10`; el mes en curso no lleva
  parámetro). Debajo, cuatro cifras («Atenciones», «Facturado», «TIMU cubrió», «Pagaron las
  familias») y la lista con hilo, sin tabla: el titular y la mascota en marino a 14 px; debajo,
  en 13 px suave, la fecha y el motivo, y el valor, lo que cubrió TIMU y el código. Sin atenciones,
  una frase sola: «Todavía no hay atenciones reportadas este mes. Al reportar una, aparece aquí con
  lo que cubre TIMU.», o «No se reportaron atenciones en octubre de 2026.» en un mes pasado.
- **Las cifras** (`.cifras`, común desde que la usa también el tope de la IA): dos a cuatro importes que se leen juntos, en celdas blancas
  iguales en fila, separadas por hilos de 1 px (el fondo `borde` asoma por el hueco), con borde de
  1 px y esquina de tarjeta. Cada celda, 12 px de relleno: la etiqueta de 12 px en mayúsculas
  espaciadas y suave, y la cifra en 24 px y 600, marino, `.numero`. Ocupan el ancho de lo que
  acompañan, así el hilo del reparto cae en el hueco entre las dos columnas del formulario. En un
  contenedor de menos de 480 px (el celular, la columna de lo atendido) cada cifra es una fila de
  libro de cuentas: la etiqueta a la izquierda y el importe a la derecha en 20 px, en columna para
  cuadrar. Sin datos no se pintan: un mes sin atenciones no lleva cuatro ceros.
- **Las ayudas, fuera del label:** la ayuda de un campo es hermana de su etiqueta, no está dentro
  de ella: el `.campo` es un `div` con `label` (`htmlFor`), control y ayuda enlazada con
  `aria-describedby`; la del código va en el formulario, debajo del campo y del botón. Dentro del
  `label`, la ayuda entraría en el nombre del campo para un lector de pantalla.

**La regla del código como prueba.** La clínica no ve las remisiones por usar, ni las busca: solo
abre la que la familia trae, por su código. El código es la prueba de que la familia se presentó,
y lo que se ve de ella es lo justo para atenderla (titular, últimos dígitos del documento, la
mascota): ni contacto, ni dirección, ni cartera, ni historia.

**La regla de la cifra antes del compromiso.** Lo que cubre TIMU y lo que paga la familia se ve
antes de reportar, no al terminar: lo calcula la API con la misma cuenta del reporte, sobre el
valor que se está escribiendo. El panel no copia la regla de cobertura ni el tope para adelantar
una cifra; si la API no respondió, lo dice en vez de estimar.

### El acceso y las páginas públicas

#### El acceso
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
- **Quién ingresa:** bajo «Hola de nuevo», un selector segmentado (Radix Tabs) «Equipo y
  aliadas» (icono de clínica) / «Familias» (huella). Equipo y clínica aliada: correo,
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

#### La portada pública y la página de cada plan
«Álbum de la manada»: la portada abre con la gente y los peludos reales de TIMU y deja la oferta a
un toque; cada plan tiene su página con todo lo que cubre (ver Layout). Lo que dice de un plan sale
del catálogo, de las aliadas lo que decide Administración → Aliadas y de TIMU lo que se escribe en
Administración → «Datos de TIMU»: la portada no escribe ninguno.
- **La barra:** marino plano, sin borde ni sombra. Las secciones en blanco y 600, subrayadas al
  pasar; «Ingresar» igual (con la sesión abierta dice «Ir a mi espacio» y lleva al de su perfil).
  «Afiliar a mi peludo» es un botón de contorno sobre la marca (`publica-btn-marca`: sin fondo,
  borde `borde-sobre-marca`, texto blanco; al pasar, `superficie-sobre-marca`), nunca verde: el
  verde de la vista está más abajo. Sobre marino (barra, panel del álbum, pie y cabecera de un
  plan) el foco es `foco-sobre-marca`, salvo dentro de «Arma tu plan», que es blanco y conserva el
  azul.
- **Las fotos del álbum** (`.album-foto`): esquina de tarjeta, `object-fit: cover`, dos anchos en
  `srcset` y la principal con carga prioritaria. Cada una lleva su pie (`figcaption`) en pastilla
  marina, 13 px, 600 y blanco, a 16 px del borde izquierdo y 12 del inferior: «Consulta en nuestra
  clínica», «Te recibimos en la clínica», «El equipo de TIMU». La del equipo junto al logo se
  encuadra desde el logo para que se lea «TIMU» y la persona; donde la celda no da para los dos,
  manda la cara.
- **El panel del álbum:** el `h1` en `--t-portada` y blanco; debajo, la frase en 16 px y
  marino-200 (`texto-sobre-marca-suave`, hasta 46 ch) que dice qué es TIMU; las pastillas de los
  planes; y «Arma tu plan».
- **Las pastillas de los planes** (`.pastillas-planes`): los planes del catálogo en tres columnas
  iguales a 8 px, también en el celular. Cada una es un enlace a la página del plan, llena del
  color del plan con su par de texto (ver Colors), esquina de campo, 56 px de alto como mínimo, 8 ×
  12 px de relleno: el nombre arriba en 13 px y 600 y abajo lo que paga cada peludo al mes con los
  peludos que dice «Arma tu plan», en 16 px y cifras tabulares. Al pasar, el nombre se subraya.
- **«Arma tu plan»** (`ArmaTuPlan`): un formulario en un recuadro blanco con esquina de panel y 24
  px de relleno (20 por debajo de 720 px), 16 px entre bloques. El título en 16 px y 600 (Inter),
  «¿Dónde vives?» (la lista de ciudades donde se vende; abre en la de la clínica de TIMU), y dos
  contadores en fila, Perros y Gatos: el número en 16 px y 600 entre «−» y «+» planos de icono,
  dentro de un borde de control de 44 px; entre los dos, al menos un peludo. Al pie, «Tu peludo,
  desde» / «2 peludos, desde» con la cifra en 24 px y 600 y «al mes» o «al mes cada uno», en
  `aria-live`, con el menor precio que da la API para esa manada; y a su derecha «Ver mis
  planes», el verde de la portada (48 px de alto), que abre el registro con la ciudad y los peludos
  ya elegidos. En una ciudad sin planes: «Aún no vendemos planes en esta ciudad.».
- **Planes:** el `h2` cuenta los planes y nombra la ciudad («Tres planes en Medellín, lado a
  lado»), la frase dice cómo leer el precio, y debajo la misma comparación del registro
  (`Comparador`), con una fila por adicional además de los servicios, y la regla de lo igual una
  vez. Al pie, un enlace por plan, «Todo lo que cubre Mi Amigo Fiel», con su cuadrado de 12 px del
  color del plan delante y 44 px de alto.
- **La red TIMU** (`RedTimu`): las aliadas como el plano de una línea de metro, en el orden que fija
  Administración. La línea es vertical, de 8 px, esquina de pastilla y verde (`linea-aliadas`). Cada
  estación es un barrio y una fila con hilo encima: el punto, el barrio en 16 px y 600 (Inter) con
  la ciudad en 13 px suave debajo, y sus aliadas, una por renglón (36 px | hasta 150 px | el resto,
  16 px entre columnas). El punto es una estación de 24 px con borde de 6 px verde y centro blanco.
  La de la clínica de TIMU es la de **intercambio**: 36 px, borde de 9 px marino
  (`ruta-recorrida`) y el halo de intercambio (ver Elevation); su primer renglón es la clínica, con
  «Nuestra clínica» en verde oscuro y 600. De ella sale el **ramal a casa** si algún plan trae
  consulta domiciliaria: un círculo de 16 px con borde punteado de 3 px verde y «**Tu casa** ·
  Consulta domiciliaria en los 3 planes» en 13 px. Cada aliada: el nombre en 600 y marino, «·» y lo
  que es en suave; debajo, en 13 px, horario, dirección y teléfono (el «·» va pegado al dato de
  delante y nunca abre renglón; teléfono y hora no se parten); el logo, si lo hay, en 32 px con
  hilo y esquina de campo (se oculta por debajo de 720 px); y «Más de <aliada>» como `details` en
  color de enlace si hay presentación. Un horario corto va a la derecha como distintivo: «24 horas»
  ok y otro corto («12 horas») neutro, con su icono. Lo que no tiene sede abierta (especialistas,
  farmacia, funeraria) va aparte, en «Especialistas y servicios de la red»: un recuadro sobre el
  lienzo con esquina de panel y 24 px de relleno, fijo al bajar desde 1100 px y debajo de la línea
  por debajo. Por debajo de 720 px, la estación queda en dos columnas: el punto y, debajo del
  barrio, sus aliadas.
- **Nosotros:** dos fotos de banco sin pie (4 : 5 y 1 : 1, 10 px entre ellas, alineadas abajo) al
  lado del texto («Quiénes somos», la presentación en 16 px y hasta 60 ch, Misión y Visión como
  pares de etiqueta y texto) y los valores en pastillas de verde tenue con texto verde oscuro, 13
  px y 600. Por debajo de 900 px, apilado. Lo que Administración no escribió no se pinta.
- **Contacto** («Hablemos de tu peludo»): a la izquierda, cómo llegar sin escribir, con
  «Escríbenos por WhatsApp» y el número en un recuadro de verde tenue (esquina de panel, icono de
  mensaje; al pasar, su hover) y debajo los pares Llámanos, Correo, la clínica con su dirección y
  horario, Cuándo te atendemos y Redes; a la derecha, «Déjanos un mensaje» en un panel blanco con
  hilo. El envío, «Enviar mensaje», es secundario. Sin celular ni correo, el error «Escribe tu
  celular o tu correo para poder responderte.»; la casilla de autorización en 13 px dice para qué
  se usan los datos. Enviado, el panel dice «Recibimos tu mensaje» con el check verde y cómo se
  responde. El mensaje entra a Comercial como interesado con origen web.
- **El pie:** marino, el logo completo de 40 px con la razón social y el NIT en 13 px, y tres
  grupos de enlaces blancos (TIMU, Ingresar, Escríbenos), cada uno con su etiqueta en mayúsculas en
  verde-500 (`texto-sobre-marca-acento`). Ingresar lista Familias afiliadas, Clínicas aliadas y
  Equipo TIMU, que llevan al mismo ingreso. El correo se parte tras la arroba si no cabe. Cuatro
  columnas; dos por debajo de 900 px y una por debajo de 480.
- **La cabecera de un plan:** el nombre del plan en `--t-portada`; la frase del catálogo en 16 px y
  marino-200 (hasta 56 ch); «Desde $ 69.000 al mes por peludo en Medellín» con la cifra en 24 px y
  blanco; y el verde de la página, «Afiliar a mi peludo con Mi Amigo Fiel», que abre el registro
  con el plan elegido. Debajo, **el plan como su línea** (`.plan-linea`): una estación por servicio
  del catálogo, en su orden, en columnas iguales; tramos de 8 px y estaciones de 24 px huecas
  (borde de 6 px y centro marino), todo del color del plan; bajo cada estación el servicio en 13 px,
  600 y blanco. La línea empieza y acaba en una estación. Es dibujo con nombre para los lectores
  de pantalla («Los servicios de Mi Amigo Fiel»); por debajo de 600 px baja en vertical.
  **El azul sobre el marino es gráfico, nunca texto**: la línea y la franja de un plan azul van en
  azul-500 sobre marino (3.39:1, por encima del 3:1 de WCAG para lo que no es texto), que la regla 6
  del manual admite para un gráfico; el nombre de cada servicio va en blanco.
- **El cuerpo de un plan:** «Lo que cubre» y «Además» (los adicionales) como listas con hilo
  entre filas (16 px): el servicio en 600 y marino, lo que dice la API debajo, y en 13 px suave
  la carencia y el detalle, cada uno una frase con su punto («Lo presta un tercero» si es de un
  tercero). A la derecha, «Lo que pagas»: un panel blanco con hilo, esquina de panel y 20 px de
  relleno, con la ciudad, una fila por número de peludos («2 peludos · $ 61.000 al mes cada uno») y
  los pagos por adelantado si los hay; y «Condiciones» (Carencia, No cubre y los términos) solo si
  el catálogo trae alguna. Cierra un enlace «Compararlo con los otros planes». Un plan que no se
  vende en la ciudad: «Este plan no está a la venta en Medellín» con el camino a los planes.
- **En Administración:** lo que dice la portada se edita como lectura con su ventana, y cada vacío
  dice qué deja de mostrar la portada («Sin escribir: la portada no la muestra.»). «Datos de TIMU»
  es una pestaña con la tarjeta «Lo que dice la portada de TIMU» en cuatro bloques (Quiénes somos,
  La clínica, Contacto, La empresa, al pie de la portada) y «Editar», que abre «Editar los datos
  de TIMU» con los mismos bloques. En la ficha de un plan, cada beneficio dice su tope por episodio
  y desde qué día aplica, y el bloque «Beneficios adicionales» lista nombre y lo que cubre (con su
  carencia y si lo presta un tercero, apagado) y abre con «Editar adicionales» (secundario) una
  ventana de filas ordenables (subir y bajar con botones de icono, «Quitar» plano). En la ficha de
  una aliada, el bloque «En la portada» (qué es, con «24 horas» si atiende siempre; lugar en la red;
  barrio; horario; presentación; logo), o la nota «No sale en la portada…», y «Editar cómo sale en
  la portada», separado de sus datos internos. Un `fieldset` que es él mismo la rejilla del
  formulario (`fieldset.formulario`, los bloques de una ventana) no lleva la caja del navegador:
  sin borde, relleno ni margen, con su `legend` como subtítulo.

**La regla de la foto con pie.** Solo las fotos reales del equipo de TIMU llevan pie, y el pie dice
lo que se ve («Consulta en nuestra clínica»). Una foto de banco (las de Nosotros) va sin pie y no
se le atribuye nada a TIMU: un pie sobre ella diría que es TIMU sin serlo. Nunca imágenes de
plantilla ni de la web anterior.

**La regla del plano.** Lo que la web pública dibuja como sistema (la red de aliadas, los servicios
de un plan) se dibuja como una línea de metro del sistema: 8 px, estaciones de 24 px, tramo que
empieza y acaba en una estación, y una sola de intercambio con halo. El color dice de quién es la
línea: el del plan para un plan, `linea-aliadas` para la red.

**La regla del verde que arma.** En la portada el único verde lleno es el de «Arma tu plan» («Ver
mis planes»); en la página de un plan, «Afiliar a mi peludo con <plan>». La afiliación de la barra
va en contorno y el envío del contacto en secundario.

#### El registro en línea
«Cada peludo, su plan»: una familia que no está afiliada dice quiénes son sus peludos, elige un plan
para cada uno, paga en Wompi y después completa sus datos (`/afiliacion`, `/afiliacion/resultado`,
`/afiliacion/completar`), en el marco del registro (ver Layout). Precios, coberturas y condiciones
salen del catálogo público de la API; el panel no escribe ninguno.
- **La manada:** el `h1` «¿Quiénes se unen a la manada?» y debajo, en texto suave, «Plan de salud
  prepagado para perros y gatos. Tres pasos: tu manada, el pago y los datos de la familia.»;
  después la ciudad («¿En qué ciudad vives?», una lista de hasta 320 px). La primera ciudad abre
  una ventana «Antes de seguir» («Por ahora afiliamos solo perros y gatos.») cuyo verde nombra lo
  que se confirma («Confirmo que solo voy a afiliar perros o gatos»); cambiarla después limpia los
  planes elegidos, porque cada ciudad vende los suyos. Debajo, una ficha por peludo y, al final,
  «Otro peludo» (`.registro-otro`): 56 px, borde discontinuo de 1,5 px en `borde-control-hover`,
  esquina de panel y sin fondo; al pasar, blanco y borde continuo. Es la única caja discontinua del
  sistema: dice «aquí cabe otro», no es un panel.
- **La ficha de un peludo** (`FichaPeludo`, `.registro-ficha`): panel blanco con hilo, esquina de
  panel, 20 px de relleno y 16 entre bloques; es contenedor (`container-type: inline-size`). El
  `h2` es el nombre y la especie («Toby · Perro», la especie en texto suave) con «Quitar a Toby» en
  plano a la derecha si hay más de uno. Nombre y especie van en una fila: el campo y, al lado, el
  segmentado «Es» Perro / Gato (`.registro-segmento`, los dos segmentos pegados con borde de
  control, 40 px y 44 en pantallas táctiles; el elegido, lleno de marino con texto blanco y 600).
  Cambiar la especie limpia el plan.
  Un nombre repetido en la manada es un error bajo el campo.
- **Los planes como opciones en su color** (`.registro-planes`, fieldset «Su plan»): tres columnas
  iguales a 8 px, también en el celular. Cada opción, esquina de campo, 56 px, borde de 2 px del
  color del plan (`data-color` del catálogo), el nombre en 600 y debajo el precio con la tarifa por
  número de peludos («$ 35.500 al mes», «al mes» sin partirse). Al pasar, lienzo; elegida, llena
  del color del plan con su par de texto (ver Colors); con el foco, doble anillo blanco y azul. En
  una ficha de menos de 360 px, 64 px de alto, 8 de relleno, nombre a 13 px y precio a 12, para que
  lo que cubre el plan elegido suba a la primera pantalla por encima de la barra.
- **Lo que cubre** (`.registro-cobertura`): el plan elegido se abre debajo, con borde de hilo y
  esquina de campo. La cabecera «Lo que cubre Mi Amigo Fiel» va llena del color del plan con su par
  de texto. Después, una fila por servicio con hilo entre ellas: el servicio a la izquierda y lo que
  dice la API (`texto` del beneficio: «1 al mes», «2 al año · cubre el 40 %») a la derecha en 600,
  marino y cifras tabulares. Al pie, sobre el lienzo, las condiciones como pares de etiqueta en
  mayúsculas y valor: Carencia, No cubre y Términos (enlace «Términos y condiciones de <plan>»).
  Cada una solo si el catálogo la trae; sin ninguna, no hay pie. Sin plan elegido, una nota: «Elige
  un plan para ver todo lo que cubre y sus condiciones.».
- **Comparar los planes** (botón plano con la flecha, «Comparar los 3 planes» / «Cerrar la
  comparación», `aria-expanded`): despliega dentro de la ficha una `tabla` con las mismas filas para
  todos los planes, en el orden del catálogo: «Al mes», cada servicio que trae alguno (el que un plan
  no trae dice «No incluye») y, si alguno las tiene, Carencia y No cubre. Las cabeceras de plan van
  llenas de su color, sin mayúsculas. Una fila igual en todos ocupa todas las columnas y se dice una
  vez: «4 al año · igual en los 3» (la nota en texto suave). En un contenedor de menos de 480 px se
  apila: cada servicio es un bloque con hilo y cada valor lleva delante su plan con su marcador de
  color (`.registro-comparador-plan`), porque la columna de color ya no se ve; lo igual va a todo el
  ancho.
- **El resumen de la manada** (`.registro-resumen`, `aside` «Tu afiliación»): panel blanco, 20 px
  de relleno y 16 entre bloques. «Tu manada en Medellín» (16 px, Inter 600); cada peludo con su
  nombre en 600 y debajo el marcador de plan, el plan y su valor («Mi Amigo Fiel · $ 69.000»), o
  «Sin plan todavía» apagado. Bajo un hilo, el total en `aria-live`: «2 peludos · tarifa de 2» en
  13 px suave y la cifra en 24 px y 600 («$ 91.500 al mes»); en la barra del celular, la cifra a
  16 px en la misma fila. Antes de poder calcular, «Elige un plan para cada peludo y ves el total.».
  El verde «Elegir cómo pagar», a todo el ancho y de 48 px (`btn-grande`), deshabilitado hasta que
  cada peludo tiene un nombre propio en la manada y un plan. Debajo, la confianza: «El pago lo procesa Wompi.» con el candado
  y «¿Dudas? Escríbenos por WhatsApp» (`Contacto`), que solo aparece si la API da el número.
- **El pago** (`PagoRegistro`): «Volver a la manada» en plano arriba; el `h1` «¿Cómo quieres
  pagar?» y la frase, que solo promete ahorro si algún periodo lo trae («Pagando por varios meses
  ahorras.»; si no, «Puedes pagar varios meses de una vez.»). Las periodicidades en 2 × 2
  (`.registro-periodos`, fieldset «Cada cuánto»): cada una con borde de control, el nombre en 600 y
  el valor del periodo; elegida, el tono de selección (borde e hilo interior de
  `indicador-seleccion` sobre `superficie-seleccion`); «Ahorras $ X» en 13 px, 600 y texto de ok solo
  en la que lo da la API. Después, «¿A quién le enviamos el comprobante?» (nombre a todo el ancho;
  celular y correo en dos columnas, una por debajo de 900 px) con la nota de que el enlace llega por
  correo y WhatsApp; las casillas de aceptación, con «Leer el contrato con lo que elegiste (PDF)» en
  plano (el modelo que genera la API con lo elegido); y el verde «Pagar $ X» a todo el ancho y de
  48 px. El resumen va al final como bloque, sin verde.
- **El resultado del pago** (`ResultadoRegistroPage`): el `h1` dice lo que pasó («Estamos
  confirmando tu pago», «Tu pago no se aprobó», «Este registro se cerró», «Tu afiliación ya está
  activa»), sacado del estado que da la API. La espera es un pulso verde de 12 px
  (`.registro-espera-pulso`, `accion-fondo`, 1,4 s de ida y vuelta, apagado sin movimiento) junto a
  la frase con el importe y la hora de la última consulta («última vez a las 3:42 p. m.»), en
  `role="status"`. El rechazo: «Intentar de nuevo» (otro enlace de pago para lo mismo elegido),
  «Empezar de nuevo con otra forma de pago» en plano y el contacto. La manada pagada va al final
  (`ManadaPagada`), con «Pagaste» o «Por pagar» y la cifra.
- **Los datos de la familia** (`CompletarRegistroPage`): el formulario por bloques
  (`.registro-bloque`: `fieldset` blanco con hilo, esquina de panel, 20 px de relleno y la `legend`
  en 16 px y 600): Titular, Otros contactos (opcional), uno por peludo («Toby · Perro», la especie
  suave) y Tu acceso al portal. La foto de cada peludo se elige con un botón secundario propio
  («Elegir foto» / «Cambiar foto», icono de subir) sobre el `input` de archivo oculto, con el foco
  visible en el botón.
- **En Administración → Planes:** «Condiciones que ve quien se afilia» (Carencia, Exclusiones y el
  enlace a los términos, solo `https`) en la ficha del plan y en la ventana de editar; cada ayuda
  dice qué pasa vacío («Vacío: el registro no dice nada de la carencia.»), y la ficha dice «Sin
  escribir: el registro no la muestra.».

**La regla del plan de frente.** El plan se elige en su color y con todo lo que cubre a la vista
antes de pagar: opciones del color del catálogo, la elegida abierta con cada servicio, su carencia y
lo que no cubre, y la comparación a un toque dentro de la misma ficha. Nunca un `<select>` de planes,
ni las condiciones en letra pequeña al final o detrás de un enlace.

**La regla de lo que el catálogo no dice.** Lo que se le muestra a quien se afilia (precio, lo que
cubre cada servicio, carencia, exclusiones, términos, el número de WhatsApp) sale de la API; si la
API no lo da, no se muestra: ni un texto por defecto, ni «ilimitado», ni un enlace vacío. Para que
aparezca, TIMU lo escribe en el catálogo (Administración → Planes).

**La regla del ahorro que se sostiene.** Una promesa de ahorro (en la frase, en una opción) solo se
dice si el dato de la API la sostiene para lo que se está eligiendo: sin descuento en ningún
periodo, la frase no habla de ahorrar y ninguna opción dice «Ahorras».

**La regla de lo igual una vez.** En una comparación, lo que es igual en todas las opciones se dice
una sola vez, a todo el ancho y con «igual en los N»; las columnas quedan para lo que cambia, y la
diferencia salta a la vista.

#### La encuesta y la verificación del carnet
Las dos páginas públicas a las que se llega desde un enlace: la familia, desde el WhatsApp de la
encuesta; un tercero (clínica, guardería, aerolínea), desde el código impreso en el carnet.
- **La encuesta hereda el acceso:** el panel de marca con la frase según el tipo («Tu opinión nos
  ayuda a cuidar mejor a Nina.»; en el seguimiento, «Seguimos pendientes de Nina.»; sin mascota,
  la del acceso) y el formulario de 400 px anclado arriba (ver Layout). El `h1` hace la pregunta
  («¿Cómo te fue en la atención de Nina?», «¿Cómo sigue Nina después de la atención?») y debajo,
  en texto suave, de qué atención se pregunta («Consulta domiciliaria del martes, 27 de
  octubre.»). El verde es «Enviar respuesta», a todo el ancho y de 48 px (`btn-grande`),
  deshabilitado hasta elegir.
- **La calificación** (`.calificacion`, satisfacción, 6.20): un `fieldset` con su `legend` («Califica
  la atención», 13 px y 700, sin relleno) y cinco opciones iguales en fila; cada una, el número en
  20 px y la palabra debajo (Muy mala, Mala, Regular, Buena, Excelente), con borde de control y
  el radio oculto. Al pasar, borde de control hover y texto marino; elegida, borde y fondo de
  selección; con el foco, anillo azul de 2 px.
- **El seguimiento** (`.calificacion-seguimiento`, 6.21): tres respuestas apiladas, una por fila de
  48 px, con su icono de 20 px a la izquierda y la frase entera en 16 px: «Sigue bien» (check, en
  ok), «Tenemos una duda» (ayuda, en info) y «Algo no va bien» (el triángulo, en alerta). Elegida,
  toma la selección del sistema; «Algo no va bien» elegida toma el tinte de alerta (borde y fondo
  de alerta) y abre debajo un `aviso-alerta`: «Si es una urgencia, no esperes: escríbenos ya por el
  chat de WhatsApp en el que te llegó este enlace.». La etiqueta del comentario cambia con la
  respuesta («¿Cuál es tu duda? (opcional)», «¿Qué notaste? (opcional)»).
- **«¡Gracias!»** dice qué pasa ahora según lo que devuelve la API (`te_contactamos`): «Alguien del
  equipo TIMU te va a contactar para saber más y ayudarte con Nina.» o «Tu respuesta nos ayuda a
  cuidar mejor a Nina.». No deduce del puntaje si habrá contacto, ni promete una hora que la
  plataforma no puede asegurar (decidido con el usuario).
- **Un error al enviar** se dice en palabras propias: «Esta encuesta ya tenía una respuesta.» (422),
  «Intenta de nuevo en un momento» si es pasajero, y si no, que abra otra vez el enlace.
- **Los estados de la encuesta:** mientras abre, el esqueleto de tres líneas del acceso con «Abriendo
  la encuesta…» para lectores de pantalla. Un enlace que no sirve: «Esta encuesta no está
  disponible» y qué hacer («Ábrelo de nuevo desde el mensaje de WhatsApp…»), sin aviso ni botón.
  Si el servidor no respondió: «No pudimos abrir la encuesta», el aviso con su causa y
  «Reintentar» como verde. Ya respondida: «Ya nos respondiste». Respondida en otra pestaña con
  esta abierta (422): el aviso «Esta encuesta ya tenía una respuesta.» y el verde deshabilitado.
- **En el panel** (Campañas, Encuestas): la respuesta del seguimiento se dice con un distintivo
  en palabras («Sigue bien» ok, «Tiene una duda» info, «Algo no va bien» alerta) y la fila dice
  «Seguimiento ·» antes de la fecha; la de satisfacción sigue con su puntaje («4 / 5»).
- **El veredicto del carnet:** el `h1` es el veredicto: «Carnet auténtico» (34 px, GeosansLight)
  con el escudo de 32 px delante en el texto de ok. Debajo, en texto suave, «Carnet preventivo
  emitido por TIMU.» y una ficha de pares en fila que se parte (`.verificacion-datos`: Mascota
  «Coco · Canino · Pug», Código y Emitido, en `.numero`), etiqueta de 12 px en mayúsculas
  espaciadas en 700 y valor marino en 600.
- **Lo que decía el carnet:** las secciones del PDF en el mismo orden y con sus títulos
  (Vacunación, Desparasitación interna, Desparasitación externa), cada una un `h2` de 16 px en la
  fuente de texto y una `tabla-apilable` con las columnas del PDF: las vacunas, Vacuna, Dosis y
  Aplicada; las desparasitaciones, Aplicada y Peso; y todas, Producto, Lote, Próxima y Aplicó. Los
  encabezados no se parten. Sin aplicaciones, «Sin aplicaciones registradas.». Después, «Pendiente
  al emitirse»: Preventivo y Programado para; la columna Estado solo sale si algo está vencido, y
  solo lo vencido lleva distintivo («Vencido», alerta): lo próximo dice su fecha y nada más
  (decidido con el usuario); sin nada, «No había nada pendiente.»; un carnet emitido antes de guardarse lo
  pendiente lo dice en una frase («Este carnet se emitió antes de que la verificación guardara lo
  pendiente.»). No hay datos de la familia.
- **El pie** (`.verificacion-pie`, 13 px suave): qué certifica («Certifica que TIMU emitió este
  carnet el … y que lo de arriba es lo que decía ese día. Lo aplicado después no aparece: pide a la
  familia un carnet nuevo.») y la huella SHA-256 del PDF entera, en texto normal, cifras tabulares
  y partida en cualquier carácter (`overflow-wrap: anywhere`) antes que recortada.
- **Código que no existe:** el `h1` «No encontramos este carnet», la frase que nombra el código en
  `.numero` y dice cómo es («son diez letras y números») y, debajo, «Código del carnet» con
  «Verificar» al lado (hasta 440 px), que lleva a la verificación del código corregido en
  mayúsculas. Si el servidor no respondió: «No pudimos verificar el carnet», el aviso con su causa
  y «Reintentar».

**La regla del veredicto como título.** Lo que una verificación concluye es el `h1` de la página,
con su icono, no una etiqueta ni un distintivo encima de otro título: quien verifica lee primero
la respuesta. Lo que la sostiene (de quién es, el código, cuándo se emitió) va debajo como ficha.

**La regla de la huella entera.** Un código, una huella o un número que alguien compara con otro
documento se muestra entero: se parte de línea si no cabe, nunca se recorta con «…» ni se abrevia.

**La regla del enlace en palabras propias.** Una página a la que se llega desde un enlace dice lo
que pasó con sus palabras y qué hacer («Esta encuesta no está disponible», «No encontramos este
carnet»), nunca el `detail` del servidor: quien llega no pidió nada todavía y no sabe qué es un
token. Solo un fallo pasajero muestra su causa, junto a «Reintentar».

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
- **Do** muestra lo que cuesta algo a quien se compromete antes de que se comprometa, con la cifra
  que calcula la API para lo que escribió (en la aliada, lo que cubre TIMU y lo que paga la
  familia antes de «Reportar atención»).
- **Do** deja la ayuda de un campo fuera de su `label`, como hermana enlazada con
  `aria-describedby`.
- **Do** en un mostrador que atiende a una persona tras otra, al terminar vacía el campo de
  entrada y devuélvele el foco.
- **Do** haz del veredicto de una verificación el `h1`, con su icono, y deja debajo lo que lo
  sostiene.
- **Do** ancla arriba un formulario que crece al elegir, para que lo que aparece no mueva la
  opción tocada.
- **Do** tras una respuesta, di qué pasa ahora según lo que devuelve la API («Alguien del equipo
  TIMU te va a contactar…»), sin prometer una hora.
- **Do** deja elegir un plan con opciones en su color y abre la elegida con todo lo que cubre,
  su carencia y lo que no cubre antes de pedir el pago; la comparación, dentro de la misma ficha.
- **Do** en una comparación, di una vez lo que es igual en todas las opciones («igual en los 3»)
  y deja las columnas para lo que cambia; apilada, cada valor lleva su opción con su marcador.
- **Do** a una barra fija abajo resérvale su alto al desplazar (`scroll-padding-bottom`) y quítala
  de fija cuando la vista ya no la necesita.
- **Do** muestra a quien se afilia solo lo que da el catálogo de la API; lo que falta se escribe en
  Administración → Planes, no en la pantalla.
- **Do** en la web pública, pon un pie en pastilla marina solo a las fotos reales del equipo de TIMU,
  y deja sin pie las de banco.
- **Do** dibuja la red de aliadas y los servicios de un plan como una línea de metro de 8 px con
  estaciones de 24 px, con una sola estación de intercambio.
- **Do** en la web pública, centra el contenido de cada sección a 1200 px con la sección a todo el
  ancho, y deja el verde lleno a «Arma tu plan» o a la afiliación del plan.
- **Do** deja a la vista una sola acción por fila, la que le toca a quien mira, y lleva el resto al
  menú de tres puntos, con lo destructivo en rojo y confirmado en su ventana.
- **Do** subraya un enlace que va dentro de una frase; un enlace que es control por sí mismo lleva
  su clase.
- **Do** muestra la espera de una pantalla que carga dentro de su layout, con el esqueleto de tres
  líneas, sin quitar la barra ni la navegación.
- **Do** resume en palabras, en la fila de un listado, lo que hace cada registro («Prellena el
  motivo de consulta y el tratamiento»), y dentro de una frase nombra los apartados de la consulta
  con su artículo (`enFrase`).

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
- **Don't** metas la ayuda de un campo dentro de su `label`: se vuelve parte de su nombre.
- **Don't** pintes ceros sobre un vacío: un mes sin atenciones dice que no las hubo en una frase,
  sin cuatro cifras a cero.
- **Don't** le listes a la clínica aliada las remisiones por usar: abre solo la del código que trae
  la familia.
- **Don't** recortes ni abrevies una huella o un código que se compara con otro documento: se
  muestra entero, aunque se parta de línea.
- **Don't** muestres el `detail` del servidor en una página a la que se llega desde un enlace: di
  lo que pasó en palabras propias y qué hacer.
- **Don't** pongas el veredicto de una verificación como etiqueta o distintivo sobre otro título.
- **Don't** pongas los planes en un `<select>` ni las condiciones (carencia, exclusiones) en letra
  pequeña al final: se ven con el plan, antes de pagar.
- **Don't** inventes lo que la API no da (una condición por defecto, «ilimitado», un enlace de
  términos vacío, un número de contacto): sin el dato, no se muestra.
- **Don't** prometas ahorro si ningún periodo lo trae: la frase y las opciones solo hablan de
  ahorrar cuando el dato lo sostiene.
- **Don't** uses la plantilla pública anterior (`.publica-tarjeta`): se retiró con el registro en
  línea; las páginas públicas usan el marco de la web pública (`MarcoPublico`, `.publica`), el
  acceso, la columna de la verificación o el marco del registro.
- **Don't** pongas un antetítulo en mayúsculas sobre el titular del álbum, una sección o la cabecera
  de un plan: lo que diría va al título o a la frase.
- **Don't** pongas un pie a una foto de banco ni uses fotos de plantilla o de la web anterior.
- **Don't** uses `--t-portada` ni un tamaño que escale con la ventana fuera del titular de la web
  pública.
