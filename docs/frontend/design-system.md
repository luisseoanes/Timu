# Sistema de diseño

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

> Se reemplaza en `R1-TOK-02`: el [manual de marca](../manual-de-marca.md#12-tipografía-en-la-plataforma)
> fija Inter para toda la interfaz, servida desde el propio proyecto. Lo que sigue describe
> lo que hay hoy en el código.

Dos familias, cargadas desde Google Fonts en `index.html`:

- **Poppins** (`--fuente-titulo`) para títulos, cifras destacadas y la marca. Pesos 500–700.
- **Nunito Sans** (`--fuente-texto`) para todo el cuerpo, controles y tablas. Pesos 400–700.

| Token | Tamaño | Dónde |
| --- | --- | --- |
| `--t-display` | 30 px | Saludo del panel, título del ingreso |
| `--t-titulo` | 20 px | Título de la página en la cabecera |
| `--t-seccion` | 16 px | Encabezado de tarjeta |
| `--t-cuerpo` | 14 px | Texto general, botones, celdas |
| `--t-menor` | 13 px | Texto secundario, enlaces de tarjeta |
| `--t-etiqueta` | 11 px | Mayúsculas con `letter-spacing: .09em`: encabezados de tabla, distintivos |

Reglas: interlineado 1.55 en cuerpo y 1.2 en títulos; el texto corrido no pasa de 70
caracteres de ancho; los números que se comparan en columna llevan la clase `.numero`
(`font-variant-numeric: tabular-nums`).

## Espaciado

Escala de 4, de `--e1` (4 px) a `--e8` (40 px). El espacio lo pone el contenedor con
`gap`, no cada hijo con su margen. Referencias: 20 px de aire interno en una tarjeta,
16 px entre tarjetas, 12 px entre elementos de una fila.

## Radios

Mientras más grande el bloque, más redonda la esquina.

| Token | Valor | Dónde |
| --- | --- | --- |
| `--r-pastilla` | `999px` | Botones, distintivos, buscador, avatar |
| `--r-campo` | `12px` | Campos, iconos cuadrados, elementos de navegación |
| `--r-tarjeta` | `16px` | Tarjetas internas, métricas, avisos |
| `--r-panel` | `24px` | Tarjetas de primer nivel, barra lateral, tarjeta de ingreso |

## Sombras

Difusas y de baja opacidad; nunca un borde y una sombra fuerte a la vez.

| Token | Uso |
| --- | --- |
| `--sombra-1` | Apoyo mínimo, casi imperceptible |
| `--sombra-2` | Tarjetas y barra lateral, el valor por defecto |
| `--sombra-3` | Elementos que flotan sobre el resto: tarjeta de ingreso, menús |

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
