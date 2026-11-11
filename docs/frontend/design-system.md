# Sistema de diseño

> **El sistema de diseño es [`DESIGN.md`](../../DESIGN.md)**, escrito por la skill de diseño
> desde lo construido (`R2-PAN-03`), con su versión para herramientas en
> `.impeccable/design.json`. Este documento queda como guía de los tokens y sus guardas; si
> los dos dicen cosas distintas, manda `DESIGN.md`.

Todo lo de este documento está implementado en [`frontend/src/styles/tokens.css`](../../frontend/src/styles/tokens.css).
Los nombres de los tokens son los que se usan en el código.

## Color

El color lo define el [manual de marca](../manual-de-marca.md): la paleta de TIMU, los tonos
auxiliares, los roles que usan los componentes y los contrastes mínimos. La paleta en tonos
menta que describía esta sección está descartada.

`tokens.css` lo implementa en tres capas: la paleta, que solo se nombra dentro de ese fichero;
los roles, que son lo único que usan los componentes; y el bloque `@pares`, con cada
combinación permitida y su contraste mínimo.

`src/test/tokens.test.ts` hace fallar la suite si un componente escribe un color a mano, usa
un color de la paleta en vez de un rol o una variable que no está definida, si un par no
llega a su mínimo o si un rol de texto o de control no tiene ningún par declarado.

## Tipografía

Dos familias, servidas desde el propio proyecto (no hay petición a Google Fonts), como fija
el [manual de marca](../manual-de-marca.md#12-tipografía-en-la-plataforma):

- **Inter** (`--fuente`, `@fontsource-variable/inter` importada en `main.tsx`) para toda la
  interfaz.
- **GeosansLight** (`--fuente-titulos`, `@font-face` en `base.css` sobre
  `src/assets/fuentes/geosans-light.woff2`) solo en `h1` y `h2`, que miden 20 px o más. Un
  título que se reduce por debajo vuelve a Inter.

La escala es fija en `rem`: una interfaz de trabajo no escala el tipo con la ventana.

| Token | Tamaño | Dónde |
| --- | --- | --- |
| `--t-display` | 34 px | Nombre de la familia abierta, saludo del panel, título del ingreso |
| `--t-cifra` | 24 px | Cifras destacadas de indicadores y métricas |
| `--t-titulo` | 20 px | Título de la página en la cabecera |
| `--t-seccion` | 16 px | Encabezado de bloque |
| `--t-cuerpo` | 14 px | Texto general, botones, celdas |
| `--t-menor` | 13 px | Texto secundario, enlaces de bloque |
| `--t-etiqueta` | 12 px | Mayúsculas con `letter-spacing`: encabezados de tabla, distintivos. Nada va por debajo |

Reglas: interlineado 1.55 en cuerpo y 1.2 en títulos; el texto corrido no pasa de 70
caracteres de ancho; los números que se comparan en columna llevan la clase `.numero`
(`font-variant-numeric: tabular-nums`). En pantallas táctiles los campos van a 16 px, para que
iOS no amplíe la página al enfocar.

## Espaciado

Escala de 4, de `--e1` (4 px) a `--e8` (40 px). El espacio lo pone el contenedor con
`gap`, no cada hijo con su margen. Referencias: 20 px de aire interno en una tarjeta,
16 px entre tarjetas, 12 px entre elementos de una fila.

## Radios

Esquinas contenidas, como la señalética de la línea visual elegida («la línea de metro»). La
pastilla queda para distintivos y estaciones.

| Token | Valor | Dónde |
| --- | --- | --- |
| `--r-pastilla` | `999px` | Distintivos de estado, avatar, estaciones de la línea |
| `--r-campo` | `6px` | Botones, campos, elementos de navegación |
| `--r-tarjeta` | `8px` | Tarjetas internas, métricas, avisos |
| `--r-panel` | `12px` | Bloques de primer nivel, barra lateral, ventanas |

## Sombras

Las superficies son planas: las separa el color, no la sombra. Solo lo que flota sobre la
pantalla lleva sombra, difusa y teñida de marino.

| Token | Uso |
| --- | --- |
| `--sombra-1`, `--sombra-2` | `none`: se conservan para no romper a quien los use, sin efecto |
| `--sombra-3` | Lo que flota: menús desplegables, ventanas, la tarjeta de ingreso |

## Movimiento

`--duracion` (160 ms) y `--curva` (salida rápida) para todo cambio de estado. Nada se anima por
decorar, y con `prefers-reduced-motion` no se anima nada.

## Iconografía

Un único componente, [`Icono.tsx`](../../frontend/src/components/Icono.tsx): trazo de 1.6,
extremos y uniones redondeadas, 20 px por defecto y 16–18 px dentro de botones y filas.
Toma el color del texto por herencia (`currentColor`), así que nunca se le pinta un color.
Es decorativo (`aria-hidden`): el significado siempre lo lleva el texto que lo acompaña, y
un botón que sólo muestre icono necesita `aria-label`.

## Tema

El panel es de tema claro por decisión de producto: se opera bajo luz de consultorio y en
pantallas compartidas. Los tokens están declarados en un solo bloque `:root`, de modo que
agregar un tema oscuro sea redefinirlos sin tocar un solo componente.
