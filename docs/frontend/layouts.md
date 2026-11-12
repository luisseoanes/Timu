# Plantillas de página

La estructura de cada pantalla vive en [`vistas.css`](../../frontend/src/styles/vistas.css).
Los componentes no saben en qué página están: la rejilla la pone la plantilla. El porqué de
cada decisión visual está en [`DESIGN.md`](../../DESIGN.md) y en el contrato de la
superficie (`.impeccable/surfaces/`).

> En rediseño ([hoja de ruta](../hoja-de-ruta-rediseno.md)). **Rediseñado:** la estructura
> del panel, el listado con ficha (Familias, Rutas y Clínica), la ruta propia del médico, la
> consulta guiada, las ventanas y la espera de sesión. **Aún con la
> composición anterior** (aunque ya con la paleta, la tipografía y el logo): el ingreso, el
> inicio, el detalle de un registro, el portal y las páginas públicas. Cada uno se rehace en
> su unidad.

## Estructura del panel — `AppLayout`

```
┌──────────────────────────────────────────────────────────────────────┐
│ TIMU  Panel  Familias  Cartera  …  Más ▾        [🔍 Buscar familia] (VR)│  barra marina, 64 px
├──────────────────────────────────────────────────────────────────────┤
│ Título del módulo  (h1)                                               │
│ Subtítulo                                                            │
│                                                                      │
│                         contenido (máx. 1440 px)                     │
└──────────────────────────────────────────────────────────────────────┘
```

- **Barra marina** (`.barra-marca`, fija arriba): el logo compacto en blanco, los módulos del
  perfil que caben y el resto en «Más» (menú), el buscador de familias y el menú de la cuenta
  (nombre, perfil y «Cerrar sesión»). El módulo activo lleva el subrayado verde
  (`--indicador-sobre-marca`). Caben 8 módulos desde 1360 px, 6 desde 1180 y 3 desde 900
  (`CORTES` en `AppLayout.tsx`).
- **Cabecera** (`.cabecera-pagina`): el `h1` de la pantalla es el título del módulo, en
  GeosansLight, con su subtítulo. Los títulos de dentro de la pantalla empiezan en `h2`. El
  título sale de la entrada de navegación activa: un módulo nuevo es una entrada en `NAV`.
- **Contenido** (`.contenido`): hasta 1440 px, centrado. Sus hijos pueden encoger
  (`min-width: 0`), así que una tabla ancha se desplaza dentro de su `.scroll-x` en vez de
  estirar la página. Lo mismo vale para `.pila`, `.con-rail` y `.rail`.
- **Por debajo de 900 px** la barra se queda con el logo y la cuenta, y los módulos bajan a
  una **barra inferior fija** (`.barra-inferior`, 56 px) con los cuatro que más usa cada
  perfil (`PRINCIPALES`: el médico en ruta lleva Rutas, Servicios, Clínica y Familias) y
  «Más» para el resto.

## Listado con ficha — `.con-ficha` (Familias, Rutas, Clínica)

El patrón de un módulo cuyo trabajo es abrir un registro y actuar sobre él.

```
┌─ listado (420 px) ─────┐ ┌─ ficha ───────────────────────────────────┐
│ Familias 5  [+ Nueva]  │ │ Jorge Ramirez            (h2, 34 px)      │
│ [Buscar] [Estado ▾]    │ │ ■ Plan Familiar · Congelada · Bogotá      │
│ Marcela Torres  ⚠ 3    │ │ [Acción de la próxima] [Habilitar] [Gest▾]│
│ ●──●──●──|──○          │ │ ●───●───●───|HOY───○   (la línea)         │
│▌Jorge Ramirez (abierta)│ │ MASCOTAS            CARTERA               │
│ …                      │ │ [Datos|Mascotas|Cartera|Servicios|…]      │
└────────────────────────┘ └───────────────────────────────────────────┘
```

- **Listado** (`.listado`, filas en `.listado-filas` > `.listado-fila`): título con el total, la acción de crear (verde lleno solo si
  no hay registro abierto: una acción verde por vista), filtros y filas. La búsqueda, el
  estado y la página viven en la URL, así que abrir un registro y volver no los pierde. La
  fila entera es el enlace (el `a` del nombre se extiende con `::after`), y la abierta se
  marca con `data-seleccionada`.
- **Ficha** (`.ficha-abierta`; `.ficha-vacia` sin registro abierto): cabecera (`.ficha-cabeza`, con el nombre, los datos y
  `.ficha-acciones`), la línea, los resúmenes siempre visibles (`.ficha-resumen`) y las
  pestañas, que abren en «Datos». Dentro de la ficha, las `.tarjeta` de las pestañas pierden
  fondo y relleno.
- **Por debajo de 900 px** se ve el listado o la ficha, no los dos, con un botón de volver.

En Familias la acción de crear es «Nueva familia» y la ficha lleva pestañas. En Rutas el listado
son las rutas del día, cada una con su línea en miniatura, y debajo lo que falta por rutear; la
ficha es la ruta abierta con su línea (`LineaRuta`). En los dos, el registro abierto vive en la
URL (`/familias/:id`, `/rutas?ruta=`), igual que los filtros. En Clínica el listado es la
historia de la mascota (su ficha y sus consultas) y la ficha, la consulta abierta: guiada si es
un borrador propio, leída si no (`/clinica/mascotas/:id`, `?nueva=1`, `?servicio=` y
`/clinica/historias/:id`). Los demás módulos que abren un registro deberían partir de aquí.

## La consulta guiada — `.consulta` (Clínica)

```
┌─ consulta (sobre el lienzo) ──────────────┐
│ ← Rocky · Jorge Ramirez      canino · 32 kg│  identidad (solo < 900 px)
│   Consulta nueva  De la visita de hoy      │
│ ┌───────────────────────────────────────┐ │
│ │ ●━━━━◉────○────○────○                 │ │  la guía: cinco estaciones
│ │ Motivo Anam. Examen Diagn. Plan        │ │
│ └───────────────────────────────────────┘ │
│ ┌───────────────────────────────────────┐ │
│ │ Examen físico          (24 px)        │ │  el apartado actual
│ │ Lo que encuentras al examinar a Rocky │ │
│ │ [                                   ] │ │
│ │ ─ EN LA ÚLTIMA CONSULTA · 12 ago      │ │
│ └───────────────────────────────────────┘ │
│ [Anterior] [   Siguiente: diagnóstico   ] │  al pulgar; en escritorio, a la derecha
│ ┌ Adjuntos ─────────────────────────────┐ │
└───────────────────────────────────────────┘
```

La guía y el apartado son dos paneles sobre el lienzo, no una ficha blanca. Por debajo de
900 px la cabecera dice a quién se atiende, porque la historia de la izquierda no está.

## La ruta propia — `.rutas-propia` (Rutas)

Quien solo sale a campo (el médico) no ve listado: abre en su ruta del día.

```
┌─ ruta propia (hasta 760 px) ──────────────┐
│ 1 de 3 paradas · 22,3 km · hasta… [Hoy]   │  resumen y día (.rutas-barra)
│ ┌───────────────────────────────────────┐ │
│ │ (✓ 1 hecha ⌄)                         │ │  pliega y despliega las hechas
│ │ ◉ Llegó 12:06 · franja 11:45–12:45    │ │  la que toca, abierta
│ │ │ Avenida 19 # 100-12                 │ │
│ │ │ Laura Gomez · Nala, felino, 11,3 kg │ │
│ │ │ [   Registrar la atención   ]       │ │
│ │ │ [Cómo llegar] [☎] [⋯]              │ │
│ │ ○ 1:15 p. m. · Jorge Ramirez · Rocky ⌄│ │  las que faltan, plegadas
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

El día es un botón que dice «Hoy» (o «vie 13 nov», con «Volver a hoy» al lado) con el campo de
fecha del navegador encima, transparente. Fuera de hoy los controles del día bajan a su fila;
el resumen no lleva la pastilla de estado de la ruta, que la línea ya dice. Con dos rutas el
mismo día, una ficha por ruta, con su título y su estado. Sin ruta, la ficha vacía dice por
qué y a quién avisar.

## Ventanas — `Modal`

Centradas, de hasta 560 px, con cabecera y pie fijos y solo el cuerpo desplazable. Hasta
600 px son una hoja que sube desde abajo, a todo el ancho. Quedan por encima de las barras y
de la línea por la escala de capas (`--capa-velo`, `--capa-ventana`).

## Espera de sesión — `.espera-sesion` (`ProtectedRoute`)

Mientras se comprueba la sesión todavía no se sabe a qué espacio va el usuario: el logo a
color sobre el lienzo y un esqueleto anunciado a los lectores de pantalla, sin la barra de
ningún espacio. Si el servidor no responde, una tarjeta con su título, la explicación y
«Reintentar».

## Ingreso — `.ingreso` (`AccesoLayout`), pendiente de `R3-PUB-01`

La misma plantilla sirve al ingreso, la recuperación y la activación de la cuenta. Dos
columnas: el panel de marca (marino, con el logo completo en blanco, el mensaje, tres
funciones y una vista previa decorativa) y el formulario. El formulario tiene un selector
entre **Equipo** (correo y contraseña) y **Familias** (celular y código por WhatsApp). Por
debajo de 900 px el panel de marca desaparece y el logo a color sube encima del formulario.
Su vista previa en vidrio y su antetítulo en pastilla contradicen el sistema y se rehacen en
su unidad (`docs/frontend/conventions.md`, deuda).

Las páginas públicas sencillas (encuesta, verificación del carnet, registro, clínica aliada)
usan `.publica` + `.publica-tarjeta`: el logo arriba y una tarjeta centrada.

## Inicio — `.con-rail`, pendiente de `R2-PAN-04`

Contenido principal más una columna derecha de 300 px (`--ancho-rail`): saludo
(`.bienvenida`), accesos rápidos (`.accesos`), dos columnas (`.dos-columnas`) con próximos
servicios y cartera, y en la columna derecha el cumplimiento del día y lo que requiere
atención. Bajo 1180 px la columna derecha baja en dos columnas; bajo 900, en una. Los
indicadores salen de `GET /dashboard/indicadores`; el perfil médico ve su jornada.

## Detalle de un registro — `.detalle-cabeza`

Las fichas que aún no siguen el patrón de Familias (un servicio, una entrada clínica, la
historia de una mascota): volver, el título en `h2` y sus datos.

## Portal de familias — `.portal`, pendiente de `R3-POR-01` y `R3-POR-02`

Primero para el celular: cabecera corta con el logo compacto y navegación fija abajo con
cinco destinos. Desde 900 px la navegación sube a la cabecera como pastillas.

## Reglas de adaptación

| Ancho | Qué cambia |
| --- | --- |
| ≥ 1360 px | Barra con 8 módulos |
| 1180–1359 px | 6 módulos y buscador más estrecho |
| 900–1179 px | 3 módulos; el inicio baja su columna derecha; Familias y Rutas siguen con listado y ficha lado a lado |
| < 900 px | Barra inferior; listado o ficha; ingreso en una columna; formularios en una columna |
| ≤ 600 px | Ventanas como hoja inferior; la línea siempre vertical; pestañas en una fila desplazable |

Además de la ventana, hay piezas que deciden por el **ancho de su contenedor**: la tabla
apilable (menos de 640 px), la línea de la familia (cuando sus paradas no caben con su
rótulo) y cada parada de la ruta (en 440 px o menos su acción de estado ocupa su fila). El cuerpo de la página nunca se desplaza en horizontal: lo que no cabe se desplaza
dentro de su propio contenedor. Toda pantalla se revisa a 1440, 1180, 900 y 390 px.
