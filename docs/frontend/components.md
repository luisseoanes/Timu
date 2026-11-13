# Componentes

Inventario de lo que una pantalla reutiliza: la clase o el componente, cuándo va y qué regla
no se rompe. El aspecto y sus razones están en [`DESIGN.md`](../../DESIGN.md); aquí, cómo se
usa en el código. Las clases viven en
[`componentes.css`](../../frontend/src/styles/componentes.css) (y las de una vista concreta en
`vistas.css`). Si una pantalla necesita algo que no está aquí, se agrega a ese fichero y a
este documento, no dentro de la vista.

> En rediseño ([hoja de ruta](../hoja-de-ruta-rediseno.md)): la estructura del panel,
> Familias, Rutas y Clínica ya usan la línea nueva; el resto de pantallas usa estas mismas piezas con la
> composición anterior hasta su unidad.

## Botones — `.btn`

| Variante | Clase | Cuándo |
| --- | --- | --- |
| Principal | `.btn-primario` | Verde lleno con texto marino. La acción que la pantalla quiere que ocurra. **Una sola por vista** (manual, sección 11); una ventana abierta es su propia vista. |
| Secundario | `.btn-secundario` | Blanco con borde. Alternativa de igual peso que no es la principal. |
| Suave | `.btn-suave` | Verde muy claro. Acciones secundarias: «Gestionar afiliación», «Registrar pago» dentro de una pestaña, «Agregar mascota». |
| Plano | `.btn-plano` | Sin fondo. Acciones terciarias y de fila (*Ficha*, *Historia*, *Editar*). |
| Plano de peligro | `+ .btn-plano-peligro` | Acción destructiva dentro de una fila (*Dar de baja*, *Quitar*): rojo, para que no pese como las demás. |
| Peligro | `.btn-peligro` | Rojo lleno. **Confirmar** algo destructivo en una ventana (*Confirmar baja*, *Quitar contacto*). |
| Bloque | `+ .btn-bloque` | Ocupa todo el ancho. |
| Icono | `.boton-icono` | Cuadrado sin texto ni borde (cerrar una ventana, volver). **Exige `aria-label`.** |
| Variante de icono | `+ .btn-icono` | Un botón o enlace de la variante que sea, solo con icono, cuadrado de 40 px (44 en táctil): llamar y «Más acciones» en una parada. **Exige `aria-label`.** |

El texto dice exactamente lo que pasa: *Registrar pago*, *Abrir consulta de Luna*. Nunca
*Aceptar* ni *Enviar*. Deshabilitados, todos los llenos usan el mismo gris; durante el envío
el texto cambia a gerundio (*Registrando…*). En pantallas táctiles miden 44 px de alto.

## Campos — `.campo` + `.input`

`.campo` es la etiqueta más el control; la etiqueta siempre es visible, nunca solo un marcador
de posición. La ayuda va en `.campo-ayuda`, enlazada con `aria-describedby`. Un `.campo` no se
estira si su vecino de fila es más alto (`align-content: start`).

- `.input` — caja con borde, radio de campo y foco en azul. Es el estándar, también para
  `select`, `textarea` y el campo de archivo, cuyo botón toma la forma del secundario
  (`::file-selector-button`). La lista (`select`) lleva su propia flecha, dos degradados del
  rol de texto suave, y el calendario de los campos de fecha es una máscara pintada con el
  mismo rol: ninguno enseña el control del navegador. En pantallas táctiles, 44 px de alto y letra de 16 px (si no, iOS
  amplía la página al enfocar).
- `.buscador` — la misma forma que `.input`, con lupa y campo transparente. En la barra del
  panel y en los filtros de listado.
- `.input-linea` — solo subrayado. **Exclusivo del ingreso.**
- Una casilla entre campos va en `label.acciones`; dentro de un `.formulario` se alinea con la
  base de los campos.

Los errores van en `.error` bajo el campo, dicen qué pasó y cómo resolverlo, y no piden
disculpas: *El correo o la contraseña no coinciden. Intenta de nuevo.*

## Tarjetas — `.tarjeta`

Superficie blanca y radio de panel, sin sombra (las superficies son planas). Contenedor de un
bloque de contenido. Dentro de la ficha de familia pierden fondo y relleno: blanco sobre
blanco solo añadía sangría.

- `.tarjeta-cabeza` — título a la izquierda y enlace, dato o acción a la derecha.
- `.bloque` — un apartado dentro de una tarjeta (título `h4` y su tabla o lista), separado del
  anterior.

## Insignias de estado — `Insignia` y `Distintivo`

`src/components/Distintivo.tsx`. **Todo estado lleva icono y texto, nunca solo color**
(manual, regla 4). `<Insignia tono="alerta">En mora</Insignia>` pinta la pastilla con su
icono; `<Distintivo dominio="servicio" valor="agendado" />` toma etiqueta y tono del mapeo
único de `src/lib/estados.ts`, para que un estado se vea igual en todos los módulos. Un
estado que el mapeo no conozca sale en tono neutro en vez de romper la pantalla. Tonos: `ok`,
`alerta`, `info`, `peligro`, `neutro`.

Un estado derivado se calcula en `lib/estados.ts`, no en la pantalla: `estadoCuota(cuota)`
devuelve `vencida` para una cuota pendiente o parcial con días de mora, que la API no guarda
como estado.

## Tablas — `.tabla` y `.tabla-apilable`

Cabeceras en versalitas apagadas, filas separadas por línea suave. La primera columna lleva
`.principal`, los números `.numero`, y la tabla va siempre dentro de `.scroll-x` para que se
desplace ella y no la página.

**Una tabla nueva es `tabla tabla-apilable`.** Cuando su contenedor mide menos de 640 px (no
la ventana: junto al listado, la ficha es estrecha también en un escritorio), cada fila se
vuelve un bloque: la primera celda es el título y el resto, pares etiqueta y valor. Para eso
cada celda lleva `data-etiqueta` con el texto de su cabecera, y la de acciones va en
`td.tabla-acciones` (sin etiqueta), que se pasa a una fila de botones debajo. Las tablas de
los módulos aún sin rediseñar la adoptan en su unidad.

## Ventanas — `Modal`

`src/components/Modal.tsx`, sobre Radix Dialog. Cabecera y pie fijos, y **solo el cuerpo se
desplaza**: la acción principal se ve siempre. En pantallas de hasta 600 px es una hoja que
sube desde abajo.

El formulario de una ventana lleva un `id` y el botón de guardar, en el `pie`, lo envía con
`form="<id>"`. Los campos vacíos no viajan (`undefined`, no `""`). Mientras guarda, el botón
dice «Guardando…» y queda deshabilitado; el error del servidor aparece con `role="alert"`
dentro del formulario, y al cerrar se limpia (`mutation.reset()`).

## Capas — `--capa-*`

Todo `z-index` sale de la escala de `tokens.css`: `--capa-elevada` (algo que pisa a sus
vecinos, como una estación sobre su línea), `--capa-barra` (barras fijas), `--capa-velo`,
`--capa-ventana` y `--capa-menu` (un menú abierto desde una ventana). La guarda de tokens
rechaza un número suelto.

## Menús — Radix DropdownMenu

`.menu` y `.menu-item` (en `vistas.css`): el «Más» de la barra, la cuenta y «Gestionar
afiliación». `.menu-item-peligro` para una entrada destructiva, tras un `.menu-separador`.
Lo raro o destructivo va en un menú, no junto a la acción principal.

## Logo — `MarcaTimu`

`src/components/MarcaTimu.tsx` pinta el SVG del vector de TIMU: completo (con lema y
siluetas) o `compacta` (solo el logotipo, donde el lema no se leería, por debajo de unos
60 px de alto), y a color o `claro` (en blanco) sobre la superficie de marca. Nunca se dibuja
con texto ni se recolorea. Cómo se regeneran los SVG: `src/assets/marca/README.md`.

## Línea de la familia — `LineaFamilia` y `LineaMini`

`features/familias/LineaFamilia.tsx`, el componente propio de la dirección «la línea de
metro». `LineaFamilia` dibuja el año de una familia: estaciones como botones (llena = hecha,
anillo marino = próxima, roja con icono = vencida), «Hoy» marcado, lo del mismo día en una
estación y las hechas antiguas plegadas en «N hechas». Mide su propio ancho y pasa a vertical
cuando las paradas no caben con su rótulo (`orientacion` en `linea.ts`). `LineaMini` es la
miniatura de una fila del listado, con su resumen en `aria-label`. El color es el del plan
(`data-color`), gris sin plan.

## Línea de la ruta — `LineaRuta` y `LineaRutaMini`

`features/rutas/LineaRuta.tsx`. La ruta del día como una lista vertical de estaciones (`ol` con
`aria-label="Paradas de la ruta"`): las hechas plegadas tras la pastilla «N hechas» (un
interruptor con `aria-expanded` que no desaparece), la que toca abierta con su
dirección como `h3` y sus acciones (`AccionesParada`), las que faltan con un botón de resumen
(`aria-expanded`) que las abre en su sitio, y las omitidas aparte. Qué parada toca, el avance y
los enlaces de navegación y WhatsApp salen de `ruta.ts`, sin React, con sus pruebas.
`LineaRutaMini` es la miniatura de una fila del listado de rutas, con su resumen en
`aria-label`. La línea es marina (`--ruta-recorrida` y `--ruta-pendiente`), nunca del color de un
plan.

## Consulta guiada — `ConsultaGuiada`

`features/clinica/ConsultaGuiada.tsx`. La consulta clínica como una línea de cinco estaciones
(`ol` con `aria-label="Apartados de la consulta"`, cada estación un botón con su estado en el
nombre accesible y `aria-current="step"` en la actual), un apartado por pantalla con su título
como etiqueta del campo y su ayuda como descripción, y el pie con «Anterior» y «Siguiente:
<apartado>» o «Firmar consulta». La lógica (qué falta para firmar, qué cambió, dónde abrir, la
consulta anterior de referencia) está en `consulta.ts`, sin React, con sus pruebas. La lectura
de una consulta firmada y sus adjuntos están en `LecturaConsulta.tsx`.

## Estados de carga, error y vacío — `Consulta`

Los tres son obligatorios en cualquier pantalla que consulte la API. `src/components/
Consulta.tsx` los resuelve: recibe la consulta de React Query y los textos, y entrega los
datos al contenido.

- **Cargando** — esqueleto (`.esqueleto`) con el texto para lectores de pantalla en
  `role="status"`.
- **Error** — la causa que devuelve el servidor (`detail`, ya escrita para quien usa el
  sistema) y «Reintentar» solo ante un fallo pasajero.
- **Vacío** — texto que explica por qué no hay nada y qué hacer: *Ninguna familia coincide
  con el filtro.* Nunca una tabla en blanco.

## Formularios — `.formulario`

Rejilla de dos columnas; `.ancho` hace que un campo ocupe la fila completa. Bajo 900 px pasa
a una columna. El resultado de guardar se dice con `.error` o `.exito`, nunca solo con color.

## Ficha de datos — `.ficha`

Lista de definiciones (`<dl>`) para mostrar un registro: etiqueta en versalitas y valor en
tinta. Se acomoda sola en tantas columnas como quepan.

## Acciones — `.acciones`

Fila de botones de una tarjeta o una ficha. En la cabecera de una ficha, `.ficha-acciones`:
una sola fila que se pliega en orden, alineada a la izquierda, con la principal primero.

## Pestañas — `Pestanas`

Sobre Radix Tabs (`src/components/Pestanas.tsx`): flechas, roles `tab`/`tabpanel` y foco los
pone Radix. Admite modo controlado (`valor`, `onCambio`) para que otra parte de la pantalla
abra una pestaña. En pantallas estrechas se desplazan en una sola fila. Son secciones de un
registro, no navegación entre módulos.

## Historial — `.historial`

Lista de cambios de un registro: lo más reciente primero, fecha a la izquierda y qué cambió a
la derecha, con los campos por su nombre legible.

## Paginación — `Paginacion`

Para listados que devuelven `Page<T>`: rango visible (*1–50 de 120*) y botones *Anterior* y
*Siguiente*. No aparece cuando todo cabe en una página.

## Filas — `.fila`

Lista compacta: icono cuadrado, cuerpo con título y subtítulo, y un dato o insignia a la
derecha (próximos servicios, movimientos de cartera). La fecha de la derecha se parte en dos
líneas antes de apretar el texto.

## Accesos rápidos — `.accesos` / `.acceso`

Botones en fila con icono y texto (inicio del panel). Nunca más de cuatro: es un atajo, no un
menú.

## Avisos — `.aviso`, `.aviso-error`, `.aviso-ok`

Bloque informativo dentro de una tarjeta, o resultado de una acción en las páginas de acceso.
Una condición que exige acción va con su botón.

## Indicadores — `.indicadores` / `.indicador`

Tarjetas de cifra: título en versalitas, valor grande (`--t-cifra`, números tabulares) y una
línea de detalle. La fórmula va en `title`.

## Anillo de progreso — `AnilloProgreso` y barras — `.barras`

El anillo resume un porcentaje (`role="img"` con su etiqueta) y se acompaña de `.metricas`.
Las barras comparan magnitudes de una sola serie (`--serie-1`), con el valor rotulado y sin
leyenda; es una lista accesible con `aria-label`.

## Selector de familia — `SelectorFamilia`

`features/familias/SelectorFamilia.tsx`, exportado desde `@/features/familias`: widget del
dominio (consulta familias), así que no sube a `src/components/`. Buscar y elegir una familia
dentro de un formulario (servicios, tareas, remisiones, orientación virtual).

## Franjas y opciones — `.cupo`

Chips con `aria-pressed` para elegir un horario disponible, un estado o una ciudad en un
filtro. Los agotados quedan deshabilitados.

## Línea de tiempo — `.linea-tiempo`

Lista con un punto por elemento; `li.hecho` lo marca como hecho. Los pasos de una atención,
la historia clínica y el carnet del portal. Las paradas de una ruta ya no la usan: tienen
`LineaRuta`.

## Borrador de IA — `.borrador-ia`

Recuadro punteado en tono informativo para todo lo que sugiere la IA. Siempre dice que el
profesional lo revisa y nunca se envía solo.

## Utilidades de `src/lib/`

- **`formato.ts`**: moneda, fechas (`fecha`, `fechaCorta`, `fechaLarga`, `fechaHora`), horas y
  franjas (`hora`, `rangoHoras`: «10:00 – 11:00 a. m.»), `edad` de una mascota, `peso` («8,4 kg»)
  y porcentajes, como en Colombia.
- **`estados.ts`**: el mapeo único de estados a etiqueta y tono, y los estados derivados
  (`estadoCuota`).
- **`permisos.ts`**: `puede(usuario, accion)` decide qué se muestra e `inicioDeRol(rol)` a
  dónde va cada perfil al ingresar. El mapa repite los roles que exige el backend en cada
  `requiere(...)`: si cambia allá, se cambia aquí en el mismo commit. Ocultar un botón no
  autoriza nada; el servidor sigue respondiendo 403.
- **`descargas.ts`**: `descargar(ruta, params, nombrePorDefecto)` baja un CSV, Excel o PDF con
  la sesión del usuario y respeta el nombre de `Content-Disposition`.
