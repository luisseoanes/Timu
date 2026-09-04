# Componentes

Cada componente es una clase raíz más modificadores, definidos en
[`componentes.css`](../../frontend/src/styles/componentes.css). Si una pantalla necesita
algo que no está aquí, se agrega a ese archivo con su documentación, no dentro de la vista.

## Botones — `.btn`

| Variante | Clase | Cuándo |
| --- | --- | --- |
| Principal | `.btn-primario` | La acción que la pantalla quiere que ocurra. **Una sola por vista.** |
| Suave | `.btn-suave` | Acciones secundarias: cerrar sesión, gestionar, ver detalle |
| Plano | `.btn-plano` | Acciones terciarias dentro de una tarjeta |
| Bloque | `+ .btn-bloque` | Ocupa todo el ancho: ingreso, tarjetas del panel derecho |
| Icono | `.btn-icono` | Botón circular de 38 px sin texto. **Exige `aria-label`.** |

El texto dice exactamente lo que pasa: *Ingresar*, *Gestionar cartera*, *Nueva familia*.
Nunca *Aceptar* ni *Enviar*. Deshabilitado baja a 55% de opacidad y el cursor deja de ser
mano; durante el envío el texto cambia a gerundio (*Ingresando…*).

## Campos — `.campo` + `.input`

`.campo` es la etiqueta más el control; la etiqueta siempre es visible, nunca sólo un
marcador de posición.

- `.input` — caja con borde, radio de campo, foco en verde con halo. Es el estándar.
- `.input-linea` — sólo subrayado. **Exclusivo del ingreso**, siguiendo la referencia; no
  se usa dentro del panel.
- `.buscador` — pastilla hundida con icono de lupa y campo transparente. Va en la cabecera
  y en los filtros de listado.
- `.campo-icono` — envoltura que posiciona un icono al final del campo subrayado.

Los errores se muestran con `.error` bajo el campo, dicen qué pasó y cómo resolverlo, y no
piden disculpas: *El correo o la contraseña no coinciden. Intenta de nuevo.*

## Tarjetas — `.tarjeta`

Superficie blanca, radio de panel, sombra 2. Es el contenedor de todo bloque de contenido.

- `.tarjeta-plana` — sin sombra, con borde. Para tarjetas dentro de otra tarjeta.
- `.tarjeta-cabeza` — título a la izquierda y enlace o dato a la derecha (*Ver todos*,
  conteo de registros). Es el patrón de encabezado de la referencia.

No todo va en tarjeta: los accesos rápidos y los filtros viven sueltos sobre el lienzo.

## Distintivos — `.distintivo`

Pastilla en mayúsculas que comunica estado. Siempre con su modificador semántico:
`-ok`, `-alerta`, `-info`, `-peligro`, `-neutro`. El mapeo de estados de afiliación a tono
está en `FamiliasPage.tsx` y es el que se replica en el resto de módulos:

| Estado | Tono |
| --- | --- |
| Activa | `ok` |
| Prospecto | `info` |
| En mora | `alerta` |
| Congelada | `neutro` |
| Cancelada | `peligro` |

`-neutro` también marca datos de ejemplo mientras un módulo no tenga backend.

## Filas — `.fila`

El patrón de lista de la referencia: icono cuadrado con fondo verde suave, cuerpo con
título y subtítulo, y un dato o distintivo a la derecha. Se usa para próximos servicios,
movimientos de cartera y alertas de preventivos. La última fila no lleva separador.

## Accesos rápidos — `.accesos` / `.acceso`

Cuatro botones en fila bajo el saludo, con icono arriba y texto debajo. El activo se
marca con `aria-current="true"` y se pinta en verde sólido. Nunca más de cuatro: es un
atajo, no un menú.

## Tablas — `.tabla`

Encabezados en mayúsculas pequeñas y apagadas, filas separadas por línea suave, hover con
superficie hundida. La primera columna lleva `.principal` (tinta y negrita) porque es la
que identifica el registro. Los números van con `.numero`. La tabla siempre va dentro de
`.scroll-x` para que sea ella la que se desplace y no la página.

## Anillo de progreso — `AnilloProgreso`

SVG de dos círculos: pista en `--verde-100` y valor en `--verde-500` con extremo redondo.
El porcentaje se centra por posicionamiento absoluto. Acota el valor entre 0 y 100 y expone
`role="img"` con su etiqueta. Se acompaña de `.metricas` —tres cifras compactas— para dar
el desglose que el anillo resume.

## Avisos — `.aviso`

Bloque en verde suave para información contextual dentro de una tarjeta. Para una condición
que exige acción, el aviso va acompañado de un botón suave de ancho completo.

## Estados de carga, error y vacío

Los tres son obligatorios en cualquier pantalla que consulte la API:

- **Cargando** — texto apagado, `Cargando familias…`. Sin animaciones de esqueleto.
- **Error** — `.error` con la causa y qué hacer.
- **Vacío** — fila de tabla o texto apagado que explica por qué no hay nada:
  *Ninguna familia coincide con el filtro.* Nunca una tabla en blanco.
