# Sistema de diseño

Todo lo de este documento está implementado en [`frontend/src/styles/tokens.css`](../../frontend/src/styles/tokens.css).
Los nombres de los tokens son los que se usan en el código.

## Color

### Marca

El verde menta es el único color de acento. Se usa para acción, selección y énfasis;
nunca para decorar superficies grandes fuera del ingreso.

| Token | Valor | Uso |
| --- | --- | --- |
| `--verde-50` | `#edf8f6` | Fondo de estado activo, botón suave, avisos |
| `--verde-100` | `#d7f0ec` | Pista del anillo, avatares, hover de botón suave |
| `--verde-200` | `#aee2db` | Bordes en hover |
| `--verde-300` / `--verde-400` | `#7cd0c7` / `#4fc3b7` | Degradados e ilustración |
| `--verde-500` | `#2fb7aa` | **Color principal**: botones, barra del activo, foco |
| `--verde-600` | `#20998e` | Hover y presionado del botón principal, título del ingreso |
| `--verde-700` | `#177b73` | Texto de marca sobre fondo claro, enlaces |
| `--verde-800` | `#12615b` | Texto sobre fondos verdes suaves |

### Neutros

Los grises llevan una pizca de verde para que convivan con la marca; un gris puro se ve
sucio al lado del menta.

| Token | Valor | Uso |
| --- | --- | --- |
| `--fondo` | `#e9f4f1` | Lienzo de la aplicación. Nunca blanco. |
| `--superficie` | `#ffffff` | Tarjetas, barra lateral, campos |
| `--superficie-2` | `#f5faf9` | Zonas hundidas: buscador, métricas, fila en hover |
| `--tinta` | `#1d2e33` | Títulos y valores destacados |
| `--texto` | `#3a4e54` | Cuerpo |
| `--apagado` | `#7a9198` | Etiquetas, texto secundario, iconos inactivos |
| `--linea` | `#e4efec` | Separadores y bordes de tarjeta plana |
| `--linea-fuerte` | `#cfe0dc` | Bordes de campos y controles |

### Semánticos

Se declaran siempre en pares fondo + texto, y **no** se mezclan con el verde de marca: el
verde significa "acción", no "correcto".

| Estado | Fondo | Texto | Se usa en |
| --- | --- | --- | --- |
| Correcto | `--ok-bg` `#e4f5ec` | `--ok-tx` `#257f52` | Afiliación activa, cuota al día, preventivo aplicado |
| Alerta | `--alerta-bg` `#fdf1e3` | `--alerta-tx` `#a9631f` | Mora temprana, preventivo por vencer |
| Información | `--info-bg` `#e6f1fa` | `--info-tx` `#2b6f9e` | Prospecto, servicio programado |
| Peligro | `--peligro-bg` `#fbe9e7` | `--peligro-tx` `#b23f34` | Cancelada, preventivo vencido, errores |

### Contraste

Texto sobre superficie y cualquier par semántico cumplen AA (4.5:1). El blanco sobre
`--verde-500` se usa sólo con peso 700 y a partir de 14 px; para texto pequeño sobre verde
se usa `--verde-700` sobre `--verde-50`.

## Tipografía

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
