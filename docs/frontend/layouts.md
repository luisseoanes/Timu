# Plantillas de página

La estructura de cada pantalla vive en [`vistas.css`](../../frontend/src/styles/vistas.css).
Los componentes no saben en qué página están: la rejilla la pone la plantilla. El porqué de
cada decisión visual está en [`DESIGN.md`](../../DESIGN.md) y en el contrato de la
superficie (`.impeccable/surfaces/`).

> En rediseño ([hoja de ruta](../hoja-de-ruta-rediseno.md)). **Rediseñado:** la estructura
> del panel, el listado con ficha (Familias, Rutas y Clínica), la ruta propia del médico, la
> consulta guiada, el inicio del panel, las bandejas (Tareas, Cartera y Preventivos), Comercial y Campañas, Aliadas y Administración, las ventanas, la espera de sesión, el portal de familias entero y el acceso. **Aún con la composición anterior** (aunque ya con la paleta, la
> tipografía y el logo): el detalle de un registro y las
> páginas públicas. Cada uno se rehace en su
> unidad.

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
  perfil (`PRINCIPALES`: el médico lleva Inicio, Rutas, Servicios y Clínica) y
  «Más» para el resto.

## Listado con ficha — `.con-ficha` (Familias, Rutas, Clínica, Servicios, Comercial, Campañas, Aliadas, Administración)

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
`/clinica/historias/:id`). En Servicios (R2-PAN-05) el listado agrupa los servicios por día
(«Hoy · sáb 14 nov», «Mañana · …») y cada fila dice a quién se atiende: la mascota y el tipo en
el título, la hora, el titular y la ciudad debajo, y «Por autorizar» si espera la autorización.
Los filtros (estado, ciudad, desde y hasta, en dos columnas) viven en la URL; sin `desde` la
agenda empieza hoy y `desde=` vacío la abre a todo lo anterior. En esa vista (desde hoy, sin estado
ni «hasta»), encima de Hoy va el grupo «Atrasados · N»: lo anterior que sigue abierto
(`abiertos=true`), cada fila con su fecha. El recuento de la cabecera los incluye, y cada día dice
cuántos servicios tiene. La ficha (`/servicios/:id`) es
el servicio: título de 24 px, «Mascota (especie) · Titular», el estado, la fecha y la
autorización, y las acciones con una sola verde (salir en ruta si es a domicilio, iniciar o
completar la atención); completar se bloquea mientras falten pasos obligatorios y dice cuáles.
Debajo, los pasos de la atención como estaciones (en atención abre en el primero que falta y,
al guardarlo, pasa al siguiente) y los pendientes derivados. Con `?origen=ruta` (llega desde
«Registrar la atención» de Rutas) ofrece «Volver a mi ruta». Las pestañas (Servicios, Pendientes y
Franjas) siguen a la vista con un servicio abierto: `/servicios/:id` es la pestaña Servicios con
la ficha dentro (`FichaServicio`), así que el listado no salta al abrir uno. Al abrir una fila del
final del listado, la ficha se trae a la vista. Los demás módulos que
abren un registro deberían partir de aquí.

En Comercial (R2-PAN-09) el listado son los interesados, con las vistas «Abiertos», «Afiliados» y
«Perdidos» (con su recuento, de `/comercial/interesados/recuentos`), el buscador y, en «Abiertos»,
los grupos por etapa con el rótulo de los días de Servicios. La ficha (`/comercial?interesado=`)
lleva la línea de etapas, los datos (el responsable se cambia ahí), y la conversación de WhatsApp
como burbujas con el campo para responder. La verde es contestar si la persona espera a un asesor;
si no, pasar a la etapa siguiente que dice la API (`siguiente_etapa`). «Marcar como perdido» va en el
menú, con el motivo y `btn-peligro`. Las pestañas son Interesados, Conversaciones (la bandeja de las
que esperan a un asesor, con «Abrir conversación» hacia la ficha) y Guion del asistente (solo
administración). En Campañas (`/campanas?campana=`) el listado son las campañas con su estado y
cuándo salen; la ficha dice a quién le llega, la plantilla, la audiencia con ejemplos del mensaje, el
envío y «Cómo le fue». Enviar ahora confirma con la audiencia («Enviar ahora a 3 familias»);
programar no, porque se cancela antes de salir. Segmentos, Encuestas, Mensajes y Plantillas de
WhatsApp siguen en sus pestañas, cada una en su fichero (`CampanasPage.tsx` solo arma las pestañas).

En Aliadas (R2-PAN-10) la pestaña Clínicas y convenios es un listado con ficha (`/aliadas?clinica=`):
la ficha dice sus datos, sus convenios en tabla apilable (beneficio y plan, lo que cubre, la tarifa y
la vigencia) y las remisiones que tiene por usar. «Nuevo convenio» es la verde, para administración;
activar o desactivar la clínica va en el menú. Una clínica recién registrada abre su ficha. En
Administración, Planes (`?plan=`) y Reglas (`?regla=`) siguen el mismo patrón. El plan dice lo que paga
cada peludo, el pago por periodo, sus beneficios y dónde se vende, con «Editar plan» en verde. Las
reglas van agrupadas por el evento que las evalúa, y la abierta dice en palabras cuándo aplica y qué
hace (lo genera el motor del backend) y se prueba ahí mismo, con un campo por cada dato que mira la
condición. Una regla de un evento retirado se lee pero no se edita.

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

## Acceso — `.ingreso` (`AccesoLayout`, R3-PUB-01)

La misma plantilla sirve al ingreso, la recuperación, el restablecimiento y la activación.

```
≥ 900 px                                        < 900 px
┌──────── marino ────────┬──── blanco ────────┐ ┌──── marino ────┐
│ TIMU (logo completo)   │                    │ │ TIMU (compacto)│
│                        │ Hola de nuevo      │ │ ●━━●━━|◉──○    │
│ Tu peludito, bien      │ [Equipo|Familias]  │ ├──── blanco ────┤
│ cuidado.               │ Correo             │ │ Hola de nuevo  │
│ ●━━━━●━━━|━◉────○      │ Contraseña         │ │ …formulario…   │
│ Afiliación … Renovación│ [    Ingresar    ] │ │ [  Ingresar  ] │
│ Datos protegidos …     │                    │ │ Datos protegid…│
└────────────────────────┴────────────────────┘ └────────────────┘
```

- **Desde 900 px, dos columnas iguales.** A la izquierda, el panel marino plano: el logo completo
  en blanco, la frase de la pantalla (`frase`; «Tu peludito, bien cuidado.», y en la activación
  «Te damos la bienvenida a la manada TIMU.») con la línea de una familia dibujada como
  señalética, y la nota de datos protegidos abajo. A la derecha, el formulario en una columna de
  400 px, centrada.
- **Por debajo de 900 px**, una franja marina arriba con el logo compacto y la línea en miniatura
  (sin rótulos ni frase), el formulario debajo y la nota al final. El verde queda dentro de la
  primera pantalla del celular (lo comprueba `e2e/sesion.spec.ts`).
- **Ingreso**: el selector Equipo TIMU / Familias. Equipo, con correo y contraseña; Familias, con
  el celular y el código por WhatsApp y, debajo, «Ingresar con contraseña» (correo o celular).
  Quien llega desde una ruta del portal lo encuentra abierto en Familias.
- **Enlace** (`/restablecer`, `/activar`): la pantalla pregunta a la API si el enlace sirve
  (`POST /auth/enlace`) antes de pedir nada. Vigente, saluda por el nombre y pide la contraseña
  según su propósito; al guardar entra directo al espacio de cada perfil. Usado, vencido,
  inválido o sin token, lo dice de entrada con «Pedir un enlace nuevo»; si el servidor no
  respondió, «Reintentar».
- **Recuperación**: al enviar, el título pasa a «Revisa tu correo o tu WhatsApp» y nombra el dato
  escrito, sin decir si la cuenta existe.

Las páginas públicas sencillas (encuesta, verificación del carnet, registro, clínica aliada)
usan `.publica` + `.publica-tarjeta`: el logo arriba y una tarjeta centrada.

## Inicio — `.inicio` («La línea de hoy», R2-PAN-04)

El módulo se llama «Inicio» y su pantalla escribe su propio `h1`: el saludo («Hola, Valentina»,
GeosansLight de 34 px) con el día. `AppLayout` no pinta la cabecera del módulo (`cabeceraPropia`).

```
┌─ 1440 px ──────────────────────────────────────────────────────────────────┐
│ Hola, Valentina                        [Este mes ▾] [Todas las ciudades ▾] │
│ Viernes, 13 de noviembre · cifras del 1 nov al 13 nov        [Excel] CSV   │
│ Variación contra 1 oct – 13 oct                                            │
│ ┌VIGENTES─┬AFILIACIONES┬RECAUDO──┬EN MORA──┬RUTAS────┬SATISFACCIÓN┐        │
│ │ 412 ▲10 │ 18  6 ret. │ $ 30,9 M│ 21  ▲3  │ 94 %    │ 4,6 / 5    │ ← cada │
│ │ ╱╲__╱   │            │         │         │         │            │  cifra │
│ └─────────┴────────────┴─────────┴─────────┴─────────┴────────────┘  abre  │
│ ┌ Recaudo en los últimos 12 meses ─────────────────────────────── × ┐ su   │
│ │ eje, rejilla, Recaudo y Facturado, nov punteado (en curso)        │ serie│
│ └───────────────────────────────────────────────────────────────────┘      │
│ ┌ Hoy en la operación ─────────────────┐ ┌ Servicios completados ──┐       │
│ │ ▲ 21 contratos en mora   [Ver la mora]│ │ Consulta ████████ 64    │       │
│ │ ▲ 2 tareas vencidas      [Ver tareas] │ └─────────────────────────┘       │
│ │ ━ HOY · VIE 13 NOV                    │                                   │
│ │ ◎ 11:00 a. m. Consulta domiciliaria   │                                   │
│ └───────────────────────────────────────┘                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

- **La franja** (`FranjaCifras`): seis cifras del período, en celdas blancas separadas por hilos;
  2 columnas en el celular, 3 desde 600 px de contenido y 6 desde 1100 (container queries sobre
  `.inicio`). Cada cifra dice su variación contra el período comparable (flecha, texto y tono:
  verde oscuro si es buena noticia, rojo si es mala, según `subeEsBueno`) y su serie de 12 meses
  en miniatura. El orden depende del perfil (`ordenCifras`).
- **La serie abierta** (`GraficoSerie`): una cifra es un botón (`aria-expanded`) que abre debajo
  su serie de 12 meses (`GET /dashboard/evolucion`), con la fórmula del indicador, eje y rejilla de
  hilo, una o dos líneas (series 1 y 3 del manual, nunca la 1 con la 2), el mes en curso
  punteado y con el punto hueco, la cruz con el valor de cada mes (cursor o flechas, con anuncio
  para lectores de pantalla) y «Ver los datos», la tabla apilable con los mismos valores. Escape
  la cierra y devuelve el foco a la cifra.
- **La línea del día** (`LineaDelDia`): vertical, marina (no es un plan). Arriba lo vencido
  agrupado y con un ejemplo (el contrato más atrasado, la tarea más antigua); la marca de Hoy; lo
  que viene (servicios agendados, o un preventivo por autorizar que aún no llega). La primera
  acción lleva el único verde de la vista; «Ver la agenda» nunca. Sin nada después de hoy, cierra
  con una frase que dice qué aparecerá.
- **El médico** (sin permiso de indicadores): sin franja. «Tu jornada» con sus consultas sin
  firmar y sus tareas vencidas, Hoy y las paradas que le faltan de su ruta («Abrir mi ruta»), y al
  lado sus tareas abiertas. En el celular su barra inferior empieza por Inicio.
- Desde 1000 px de contenido, la línea y su columna de 400 px lado a lado; por debajo, apiladas.

## Bandeja de trabajo — `.tabla-apilable` (Tareas)

Lo que hay por resolver, en una tabla a todo el ancho que se apila en el celular: la tarea con su
estado al lado, su área y a quién afecta (la familia y, si es de un servicio, cuál y de quién, con
enlace a cada uno), cuándo vence (lo vencido con icono y la palabra, no solo en rojo),
la prioridad y el responsable (una lista para reasignar), con «Tomar», «Iniciar» y «Cerrar» en la
fila. Las vistas (mías, sin asignar, vencidas, todas) son un selector segmentado que en el celular
pasa a dos filas de dos. «Nueva tarea» es la verde.

### Cartera (R2-PAN-08)

La misma bandeja, a todo el ancho, para cobrar y renovar. Las vistas «En mora» (la de entrada, adonde
lleva «Ver la mora» del Inicio), «Por renovar» (los vigentes en la ventana de 90 días) y «Todos», con
su recuento (`GET /cartera/contratos/recuentos`); el buscador y la ciudad viven en la URL. Cada fila:
la familia (el titular enlaza a la pestaña Cartera de su ficha, que tiene el estado de cuenta) con su
plan (cuadrado y nombre), el contrato y la ciudad; lo que debe con icono y «hace N días» o «Al día»;
la cuota y su periodicidad; la renovación («21 ago 2027», con «ya se puede renovar» si la API dice
`renovable`), y el estado. Acciones de fila suaves: «Registrar pago» si debe (la ventana abre con la
cuota más antigua y su saldo) y «Renovar» si es renovable, que se confirma en una ventana. Sin verde
lleno en la bandeja: cada ventana tiene el suyo.

### Remisiones y usuarios (R2-PAN-10)

Remisiones, en Aliadas: «Por usar» (la de entrada, por la que vence antes), «Utilizadas», «Anuladas» y
«Todas» con su recuento, y «Emitir remisión» en verde en la cabecera. Cada fila: el titular y la
mascota (enlace a la familia), el código y el motivo; la clínica; lo que cubre («80 % hasta $ 200.000»,
o «Cubrió …» si ya se atendió); cuándo vence (la vencida, con icono y palabra) o cuándo se atendió; y
«Anular», que confirma en rojo. La pestaña Liquidación pide el período y da una fila por clínica con su
total. Usuarios, en Administración: «Equipo», «Clínicas aliadas», «Familias» e «Inactivos» con su
recuento y un buscador. El perfil se cambia en la fila (solo entre perfiles del equipo) y se confirma
antes, porque cierra las sesiones de esa persona; «Desactivar» confirma en rojo y «Activar» es
directo. La propia fila lleva «Tú», sin acciones. Los eventos de la pasarela, en Reportes, son otra
bandeja: «Con error», «Procesados» y «Todos», con «Reprocesar».

### Preventivos (R2-PAN-08)

Dos pestañas: «Por hacer» (la bandeja) y «Carnet por mascota». La bandeja va por siguiente paso:
«Por autorizar», «Por agendar» (los dos, lo que vence en el próximo mes), «Agendados» y «Todos», con
su recuento. Una sola tabla con un grupo (`tbody`) por familia, así la cabecera de columnas sale una
vez y las columnas se alinean: el grupo abre con el titular (enlace a la familia), la ciudad y cuántos
preventivos tiene y, si falta autorizar, «Escribir» (WhatsApp) y «Registrar autorización (N)», que
pide de una vez lo de la familia en una ventana con todo marcado. Cada fila: «Mascota · esquema», la
dosis, cuándo toca (lo vencido con icono y la palabra), el estado solo en «Agendados» y «Todos» (en las
otras repetiría la vista), «Agendar visita» si toca agendar y un menú con «Registrar aplicación sin
visita» (médico y administración, si está autorizado) y «Cancelar preventivo». Apilada, el menú va
arriba a la derecha del bloque. El siguiente paso de cada preventivo lo dice la API (`siguiente`).

## Detalle de un registro — `.detalle-cabeza`

Las fichas que aún no siguen el patrón de Familias: volver, el título en `h2` y sus datos.

## Portal de familias — `PortalLayout` (R3-POR-01)

La estructura del panel con los destinos de la familia: barra marina con el logo, Inicio,
Peludos, Citas, Pagos y Mis datos, y el menú de la cuenta; por debajo de 900 px, la barra
inferior con los cinco (caben siempre: no hay «Más»). Reutiliza `.shell`, `.barra-marca`,
`.modulos`, `.cuenta` y `.barra-inferior`; el contenido va en `.contenido.portal-contenido`,
hasta 1120 px. Cada pantalla abre con su `h1` en GeosansLight de 34 px.

### El inicio — `.portal-inicio` («Hoy, estás aquí»)

```
┌─ 390 px ───────────────────────┐   ┌─ desde 900 px ─────────────────────────────┐
│ Hola, Ana            (h1, 34)  │   │ Hola, Ana                                   │
│ ■ Plan Familiar  [Congelada]   │   │ ┌─ la línea ──────────────┐  ■ Plan · estado│
│ Tus 3 cuotas vencidas pausaron │   │ │ ⚠ 3 cuotas vencidas     │  frase          │
│ el plan. Al pagar, …           │   │ │   [Pagar $ 225.000]     │  [Agendar] [Vet]│
│ [Agendar] [Hablar con un vet]  │   │ │ ⚠ 7 preventivos …       │  [Michi][Luna]  │
│ [Michi 3 venc.] [Luna 4 venc.] │   │ │ ━ HOY · JUE 12 NOV      │                 │
│ ┌─ la línea ────────────────┐  │   │ │ ○ 21 nov · Cuota …      │                 │
│ │ ⚠ 3 cuotas vencidas       │  │   │ └─────────────────────────┘                 │
│ │ ━ HOY · JUE 12 NOV        │  │   └─────────────────────────────────────────────┘
└────────────────────────────────┘
```

- **El plan**: el marcador y el nombre de cada plan (de la línea, con el color del
  catálogo), su estado y una frase que dice por qué está así y qué hacer (`frase` en
  `features/portal/plan.ts`). «Agendar una visita» solo aparece si el plan deja agendar
  (`motivoSinAgendar`, la misma regla que la elegibilidad del backend).
- **Los peludos** (`AccesoPeludo`): foto o huella, nombre y lo que tiene vencido; abren su ficha.
- **La línea** (`LineaPortal`, `.linea-portal`): la de la familia en vertical, del color del
  plan, abierta en «hoy». Lo hecho se pliega en una pastilla; lo vencido se agrupa (las
  cuotas en una estación, los preventivos en otra, con cuántos por peludo) para que «hoy»
  quede en la primera pantalla; debajo, lo que viene. Una sola acción verde, la más
  urgente (`accionPrincipal` en `features/portal/linea.ts`): pagar lo vencido, si no
  agendar los preventivos vencidos, si no pagar la próxima cuota.

### La ficha de un peludo

Un panel con la identidad (volver, nombre, especie, edad, peso y plan) y la foto; su propia
línea (sus preventivos y sus visitas, por `mascota_id`), y las pestañas Carnet, Historia
clínica y Su plan, con el cupo de cada beneficio dicho de frente («le quedan 5 de 6 este
año», «sin tope de usos este mes»; nunca «ilimitado»).

### Citas, pagos y datos (R3-POR-02)

La misma cabecera (`.portal-cabecera`: `h1` y la acción de la vista) y paneles blancos
(`.portal-panel`, con `.portal-panel-titulo`) con filas (`.portal-lista`, `.citas`): qué a la
izquierda, su estado y su acción a la derecha; en un contenedor de 480 px o menos la acción
baja a su fila, alineada a la derecha. Las acciones de fila que no son la principal son planas
con el color de enlace (`.btn-plano.btn-accion`).

- **Citas**: «Agendar una visita» es el verde solo si el plan lo permite; si no, un aviso
  dice por qué y lleva a pagos. Pestañas Próximas y Pasadas; cada cita con su día y hora
  (`.cita-cuando`), qué y para quién, su estado dicho a la familia (`citas.ts`) y sus acciones.
- **Pagos**: el saldo (`.portal-saldo`) con el único verde por todo lo pendiente y, si el
  plan está en pausa, qué cambia al pagar; las cuotas por pagar por su mes (`pagos.ts`), y el
  historial. Al volver de la pasarela, un aviso tintado (`.portal-aviso-<tono>`) con el
  estado de ese pago.
- **Datos**: titular y documento como ficha de lectura, el formulario de contacto con su
  verde («Guardar»), el contrato como acción secundaria si hay uno vigente, y los documentos.

## Reglas de adaptación

| Ancho | Qué cambia |
| --- | --- |
| ≥ 1360 px | Barra con 8 módulos |
| 1180–1359 px | 6 módulos y buscador más estrecho |
| 900–1179 px | 3 módulos; el inicio apila la línea y su columna; Familias y Rutas siguen con listado y ficha lado a lado |
| < 900 px | Barra inferior; listado o ficha; acceso con la franja marina arriba; formularios en una columna |
| ≤ 600 px | Ventanas como hoja inferior; la línea siempre vertical; pestañas en una fila desplazable |

Además de la ventana, hay piezas que deciden por el **ancho de su contenedor**: la tabla
apilable (menos de 640 px), la línea de la familia (cuando sus paradas no caben con su
rótulo) y cada parada de la ruta (en 440 px o menos su acción de estado ocupa su fila). El cuerpo de la página nunca se desplaza en horizontal: lo que no cabe se desplaza
dentro de su propio contenedor. Toda pantalla se revisa a 1440, 1180, 900 y 390 px.
