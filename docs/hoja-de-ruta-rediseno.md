# Hoja de ruta del rediseño del frontend

Rediseño completo de la interfaz con la marca real de TIMU: el panel del equipo, el portal de
familias, el espacio de la clínica aliada y las páginas públicas, todo responsive. Sustituye
por completo el aspecto actual, con su paleta en tonos menta, Poppins y Nunito Sans. No cambia
qué hace la plataforma: funciones, datos, permisos y textos de producto siguen igual, salvo
donde se diga.

Documentos que manda este trabajo:

- [`PRODUCT.md`](../PRODUCT.md): usuarios, prioridades por espacio, posicionamiento y principios.
- [Manual de marca](manual-de-marca.md): paleta, roles de color, tipografía, logo y voz.
- `DESIGN.md`: el sistema de interfaz. Lo escribe la skill al cerrar la primera superficie
  (`R2-PAN-03`), a partir de lo construido.
- [Pendientes externos](pendientes-externos.md#marca-e-identidad-manual-de-marca): lo que tiene
  que falta de TIMU (los precios, los originales de las fotos).

Los IDs siguen el patrón `fase-módulo-consecutivo` del [backlog](backlog.md), con fases `R0` a
`R4` para no confundirlas con las del backend.

## Estado

Creada el 2026-11-10. R0 y R1 se trabajaron el mismo día; lo marcado **Parcial** dice qué falta y en qué unidad se cierra. Cuando una cambia de estado se
actualiza aquí, igual que en el backlog.

| Fase | Unidades | Hecho | Parcial | Pendiente |
| --- | ---: | ---: | ---: | ---: |
| R0 — Preparación | 4 | 4 | 0 | 0 |
| R1 — Fundaciones | 7 | 5 | 2 | 0 |
| R2 — Panel del equipo | 10 | 10 | 0 | 0 |
| R3 — Familias, aliada y páginas públicas | 6 | 3 | 0 | 3 |
| R4 — Cierre | 4 | 0 | 0 | 4 |
| **Total** | **31** | **22** | **2** | **7** |

Al cierre de `R2-PAN-10` (2026-11-15) el panel del equipo está rediseñado entero, y con `R3-PUB-01`
(el mismo día) también el acceso.

### Dónde se retoma (2026-11-16)

Para la sesión siguiente, que no tiene la conversación anterior: todo lo decidido está en esta
hoja, en `pendientes-externos.md` y en los `CLAUDE.md`.

- **El techo del revisor (`DEU-28`–`DEU-70`) y la deuda decidida están hechos**, salvo lo que la
  tabla de [deuda decidida](rediseno/deuda.md) marca como pendiente: `DEU-8` (editor de reglas por
  campos), `DEU-14` (terminar la siembra gruesa), `DEU-15` (plantillas de consulta, decidida, TODO)
  y `DEU-27` (va en `R4-CIE-03`). `DEU-E` espera a TIMU.
- **Siguiente unidad: `R3-ALI-01`, pero solo cuando el usuario lo diga** (lo dejó para otra
  sesión). Orden que Claude propuso y el usuario **aún no confirmó**: `R3-ALI-01`, `R3-PUB-03`,
  `R3-PUB-02` (con los precios provisionales de TIMU dichos como tales); `DEU-8`, `DEU-14` y `DEU-15`
  intercaladas, porque no dependen de decisiones de diseño; y el cierre `R4` (recorrido,
  auditoría, documentación y umbrales). Se le pregunta antes de empezar.
- **`R1-CMP-02` y `R1-CMP-03` siguen parciales** y se cierran con R3 y R4 (paginación, filtros y
  orden comunes; vacíos que orientan en las pantallas de R3).
- **Datos**: `datos_demo` y luego `operacion_demo` (ocho semanas de operación). La base local se
  recreó y sembró con los dos el 2026-11-16. Sin pasarela de pruebas (Wompi, pendiente de TIMU)
  ningún interesado llega a «afiliado».

## Alcance medido

Medido el 2026-11-10 sobre `frontend/src`. Hay que tocarlo todo; nada se puede rediseñar solo
desde el CSS.

- 34 rutas en tres espacios con acceso propio, más las páginas públicas.
- 60 componentes de pantalla, con unas 13.300 líneas.
- 9 componentes base en `src/components/`.
- 26 tablas y 85 `style={{}}` en línea.
- Unas 2.000 clases CSS aplicadas desde los componentes.
- El responsive solo llega hasta 900 px: no hay nada pensado para el teléfono.

## Cómo se trabaja

El diseño lo gobierna la skill del repositorio (`.claude/skills/impeccable`). Las reglas
técnicas las gobierna el repositorio: el `CLAUDE.md`, las guardas de pruebas y el
`CONTRIBUTING.md`. Si chocan, se resuelve con el usuario antes de seguir.

### Orden según la skill

1. **Se elige una sola línea visual**, en la primera superficie (`R0-DIR-01`). Como la
   identidad se reemplaza, la skill exige un sorteo de direcciones (`concept-seed --scope
   direction --mode operate`) y que el usuario elija una en su página de decisión. La paleta,
   la tipografía y la voz ya están fijadas por el manual; el sorteo decide lo que el manual no
   cubre: composición, densidad, formas, movimiento y el gesto propio de TIMU.
2. **La primera superficie se construye entera con esa línea** y se cierra con el revisor
   final de la skill. Después, la skill escribe `DESIGN.md` a partir de lo construido.
3. **El resto de superficies heredan la línea.** Solo cuando la composición de una pantalla
   está de verdad abierta (inicio, rutas, entrada clínica, registro) se hace un sorteo de
   superficie (`--scope surface`). Las demás siguen los patrones ya construidos.
4. **No hay generación de imágenes en este entorno.** Todo se construye directamente en
   código, y las opciones de cada sorteo se presentan como bocetos HTML. La skill lo prevé para
   las pantallas de trabajo.

### El ciclo de una unidad

Así se trabajó R2 entero; la siguiente sesión lo retoma igual.

1. **Al empezar**: el stack y `db-test` arriba, el último CI de `main` en verde (si no, se arregla
   antes que nada) y `datos_demo` sembrado hoy (si no, la ruta de la médica no aparece). Se leen los
   `CLAUDE.md`, esta hoja, `DESIGN.md`, `PRODUCT.md` y `docs/frontend/`.
2. **Se mira la pantalla actual** con capturas a 1440 y 390 de cada pestaña, con los perfiles que la
   usan, antes de proponer nada.
3. **La composición la decide el usuario.** Se le pregunta con dos opciones con boceto ASCII y la
   recomendada primero (bandeja, listado con ficha o lo que corresponda), y se le avisa en cada punto
   en que haya que decidir algo más. Sin sorteo, el contrato lleva `seed: none (pinned)` con sus
   palabras literales (`impeccable surface-brief write`).
4. **Lo que el panel necesita y no debe calcular lo da la API** (recuentos, nombres, el siguiente
   paso, textos en palabras), con sus pruebas, sus tipos regenerados y su sitio en la guarda de
   caminos calientes.
5. **Un fichero de más de unas 500 líneas se reparte antes**, en un commit `refactor` que no cambia
   nada (las pruebas de antes pasan sin tocarlas).
6. **Capturas a 1440, 1180, 900 y 390** en `.impeccable/review/<superficie>/`, y el revisor final
   hasta `ship`. Sus arreglos se aplican todos; del «techo», lo que sea de una línea, y el resto se
   apunta en «Lo que quedó» de la unidad, en las [notas de cierre](rediseno/notas-de-cierre.md).
7. **Documentación**: el documentador de la skill pone al día `DESIGN.md` y su sidecar; a mano, la
   fila de la unidad, su apartado en las [notas de cierre](rediseno/notas-de-cierre.md), la tabla de estado y `docs/frontend/`.
8. **Commits** en un worktree, cada uno verificado sobre su propio estado: backend primero, el
   refactor aparte, el panel por dominio y la documentación al final. Antes de empujar, la e2e contra
   el stack; después, el CI hasta verde.
9. **No se empieza la unidad siguiente sin que el usuario lo diga.** Al terminar una, se le informa
   y se espera. Tampoco se aplican por iniciativa propia decisiones abiertas de «Lo que quedó» ni de
   la tabla de deuda: se le preguntan, con la opción recomendada primero.

### Capturas para el revisor final

Cómo se capturan las pantallas para el revisor (anchos, sesiones, cupos, estados simulados y el
esqueleto del script): [`frontend/capturas-revisor.md`](frontend/capturas-revisor.md).

### Definición de terminado de cada unidad

Una unidad está **Hecha** cuando:

1. Sus componentes solo usan roles de color del manual: la guarda de tokens está en verde.
2. Sus rutas salieron de la lista de pendientes del recorrido responsive y pasan a 375, 768, 900
   y 1280 px, sin desborde horizontal y sin fallos de contraste de `axe-core`.
3. Cada control tiene sus estados (normal, al pasar el cursor, foco, activo, deshabilitado,
   cargando y error), y cada pantalla sus estados de carga, vacío y error. Todo funciona con el
   teclado.
4. Las pruebas cubren el comportamiento que cambió y pasan `npm run verificar`,
   `npm run test:e2e` y `npm run test:e2e:stack`.
5. El hook de la skill no deja hallazgos sin resolver. Si se ignora alguno, es con una excepción
   y su motivo en `.impeccable/config.json`.
6. Si la unidad cierra una superficie: hay capturas en `.impeccable/review/` (1440 px de
   escritorio y 390 px de móvil) y el revisor final (`impeccable-finish-reviewer`) da veredicto
   `ship`.
7. Si añade una dependencia, se verificó que el stack sigue arrancando con un solo comando
   (`CLAUDE.md`).
8. El commit sigue `CONTRIBUTING.md`.

## R0 — Preparación

Ninguna unidad de esta fase cambia cómo se ve la aplicación.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R0-DOC-01` | Documentación de entrada | El `CLAUDE.md` de la raíz y el de `frontend/` enlazan `PRODUCT.md`, el manual de marca y esta hoja de ruta. `docs/frontend/design-system.md` deja de describir la paleta menta como vigente y remite al manual. | Hecho |
| `R0-QAA-01` | Guarda de colores escritos a mano | Una prueba de Vitest (`src/test/tokens.test.ts`) falla si hay un color escrito a mano (`#hex`, `rgb()`, `hsl()`, `oklch()` o un nombre de color) en un `.css`, `.ts` o `.tsx` de `src/` fuera de `tokens.css`, incluidos los `style={{}}`, o si se usa un `var(--…)` que no está definido. Se corrigen los tres colores escritos a mano de hoy (`componentes.css`). La guarda queda en la tabla de guardas del `CLAUDE.md`. | Hecho |
| `R0-QAA-02` | Recorrido responsive y de contraste | Una prueba de Playwright recorre cada ruta de `App.tsx`, con el perfil que la usa, a 375, 768 y 1280 px. Falla si el documento desborda en horizontal o si `axe-core` encuentra un contraste insuficiente. Las rutas sin rediseñar están en una lista explícita de pendientes que solo puede encogerse, y otra comprobación falla si una ruta no está ni verificada ni pendiente. `@axe-core/playwright` entra con versión fija y pasa la auditoría de vulnerabilidades. La guarda queda en la tabla del `CLAUDE.md`. | Hecho: midió 107 fallos con la paleta anterior (98 de contraste y 9 de desborde), que quedan en `PENDIENTES`. Administración se recorre con `gerencia@timu.co`, que crea `datos_demo`. |
| `R0-DIR-01` | Dirección visual | Con `/impeccable`, sorteo de dirección en modo operativo sobre la primera superficie: el panel del equipo, con su estructura y el listado y detalle de Familias. El usuario elige una dirección en la página de decisión, y el contrato de dirección (los seis bloques y la referencia del sorteo) queda en el brief de la superficie (`.impeccable/surfaces/`). | Hecho: el usuario eligió «La línea de metro» (cada familia es una línea cuyas estaciones son cuotas, preventivos y visitas). Contrato en `.impeccable/surfaces/frontend-src-features-familias-familiaspage-tsx.md`, boceto en `docs/rediseno/boceto-familias-linea-de-metro.html`. |

## R1 — Fundaciones

Empieza cuando `R0-DIR-01` tiene dirección elegida: las formas, la densidad y el movimiento
salen de su contrato.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R1-TOK-01` | Paleta y roles | `tokens.css` implementa las secciones 9 y 10 del manual en tres capas: paleta, roles y pares permitidos. La paleta menta desaparece. La guarda de `R0-QAA-01` también falla si un componente usa un paso de la paleta en lugar de un rol, si un par declarado no llega a su mínimo o si un rol de texto o de borde no tiene ningún par. La nota de estado de la sección 15 del manual se actualiza. | Hecho: con la paleta de la marca desaparecieron los 98 fallos de contraste del recorrido. |
| `R1-TOK-02` | Tipografía y escalas | Inter sustituye a Poppins y Nunito Sans. La escala tipográfica (fija, en rem), el espaciado, los radios, las sombras y el movimiento salen del contrato de dirección. Las cifras que se comparan en columna usan números tabulares. | Hecho: `@fontsource-variable/inter` 5.3.0. Inter, algo más ancha, destapó un desborde en Tareas: los hijos de `.contenido` ahora pueden encoger, y eso resolvió además cuatro desbordes antiguos. |
| `R1-PLA-01` | Color de plan en el catálogo | El catálogo de planes gana un campo de color (`verde`, `naranja` o `azul`), con migración, restricción en la base, `Literal` en el schema y tipos del panel regenerados. Administración → Planes permite elegirlo. La interfaz no deduce nunca el color a partir del nombre del plan (regla 5 del manual). | Hecho: migración `0038` (enum `color_plan`), los tres planes de TIMU con el color del manual y los demás en verde; selector en Administración → Planes y marcador junto a cada plan. |
| `R1-CMP-01` | Acciones y campos | Botones (principal, secundario, suave, destructivo y de icono), campos de texto, listas, áreas de texto, casillas, opciones e interruptores, cada uno con su etiqueta, ayuda y error. Tienen todos los estados y una zona táctil de 44 px o más en el móvil. | Hecho: `.btn-secundario` y `.btn-peligro` nuevos, estados completos, campos con estado inválido y deshabilitado, 44 px y letra de 16 px en pantallas táctiles; selección de texto, cursor, casillas y barras de desplazamiento con la paleta. |
| `R1-CMP-02` | Datos | La tabla con su versión para el móvil (la forma la fija la dirección), la paginación, los filtros y el orden. El distintivo de estado (pastilla, icono y texto) y el marcador de plan (regla 4 del manual). | Parcial: `Insignia` (pastilla con icono por tono) sustituye a los 23 distintivos escritos a mano, y el marcador de plan está hecho. La versión móvil de la tabla está hecha con las de Familias: `tabla-apilable` pasa a una fila por bloque cuando su contenedor mide menos de 640 px, con la etiqueta de cada celda en `data-etiqueta`. Cada módulo la adopta en su unidad. Faltan la paginación, los filtros y el orden comunes. |
| `R1-CMP-03` | Capas y avisos | La ventana modal sobre Radix (en el móvil, hoja que sube desde abajo), los avisos, las pestañas y los menús. Los estados de carga con esqueleto, los vacíos que explican qué hacer y los errores con «Reintentar». | Parcial: esqueleto de carga anunciado a los lectores de pantalla, «Reintentar» solo ante fallos pasajeros y la ventana modal como hoja inferior en pantallas estrechas. Que cada vacío diga qué hacer se revisa con cada pantalla: R2 ya está, queda R3. Los menús existen desde R2 (Radix DropdownMenu, en `docs/frontend/components.md`): lo reversible de un registro va en el de tres puntos. |
| `R1-CMP-04` | Marca e iconos | `MarcaTimu` pasa a ser el marcador de texto del manual (sección 13), con el lema «Medicina veterinaria prepagada». Los iconos se ajustan al lenguaje de la dirección. | Hecho: `MarcaTimu` pinta el logo en SVG sacado del vector de TIMU (2026-11-11), completo o compacto, a color o en blanco; antes era un marcador de texto. Los iconos se mantienen: un trazo y sin relleno, como los pictogramas de señalética de la dirección. |

## R2 — Panel del equipo

La primera superficie fija la línea visual de todo lo demás. Los médicos usan sobre todo el
celular para Rutas, el detalle de Servicios y Clínica: esas pantallas se diseñan primero para
el móvil.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R2-PAN-01` | Estructura del panel | `AppLayout` con la navegación de escritorio y una navegación de móvil que llegue a todo el menú del perfil, más la cabecera. Los estados de `ProtectedRoute` (cargando y «Reintentar»). | Hecho. Hecho: barra marina con los módulos que caben y el resto en «Más», menú de la cuenta, cabecera con el h1 del módulo, y en el móvil barra inferior con los cuatro módulos de cada perfil más «Más». Los estados de `ProtectedRoute` muestran la marca sobre el lienzo, sin la barra de ningún espacio, con un esqueleto mientras se comprueba la sesión o un aviso con «Reintentar» si el servidor no responde. Cerrado con el veredicto `ship` de `R2-PAN-03`. |
| `R2-PAN-02` | Familias | Listado, detalle con sus siete pestañas y las ventanas de nueva familia, afiliar y ficha de mascota, según el contrato de dirección. La API expone la línea de cada familia (cuotas, preventivos y servicios) en un endpoint propio, y el listado la muestra en miniatura sin pedir tres recursos por fila. La tabla tiene su versión para el móvil (pendiente de `R1-CMP-02`). | Hecho. Hecho: endpoint de la línea, listado con la miniatura, ficha sobre la línea (orientación medida, pliegue de hechas, mismo día en una estación), mascotas y cartera bajo la línea, pago de una cuota desde su estación y acciones de estado en un menú. También: las tablas de las pestañas se apilan en el celular, servicios separa el cupo de cada mascota y sus apartados, el historial va de lo más reciente a lo más antiguo, las cuotas con mora se ven vencidas, y las ventanas quedan por encima de las barras con los campos a su altura. El barrido responsive mide cada pestaña de la ficha. Cerrado con el veredicto `ship` de `R2-PAN-03`. Agendar un preventivo desde su estación se dejó, decidido con el usuario, para `R2-PAN-08`. |
| `R2-PAN-03` | Cierre de la línea visual | Revisor final sobre la estructura y Familias con veredicto `ship`. Después, la skill escribe `DESIGN.md` y `.impeccable/design.json` desde lo construido, y `docs/frontend/design-system.md` remite a `DESIGN.md` (el 2026-11-12 se fusionó en `DESIGN.md` y `conventions.md` y se eliminó). | Hecho: `ship` del revisor final tras cuatro pasadas (fallos corregidos: rótulos de la línea que se pisaban, pestañas en lugar del resumen, lo vencido solo con color, cupos duplicados, ventanas bajo las barras, pie de ventana cortado y dos acciones verdes a la vez). `DESIGN.md` y `.impeccable/design.json` escritos desde lo construido; `docs/frontend/design-system.md` remite a `DESIGN.md` (el 2026-11-12 se fusionó en `DESIGN.md` y `conventions.md` y se eliminó), y la deuda que encontró la skill está en `docs/frontend/conventions.md`. |
| `R2-PAN-04` | Inicio | Sorteo de superficie para el tablero de inicio. Indicadores con su evolución, y series de gráfico según el manual. | Hecho (2026-11-13): sorteo de superficie en modo Operate, elegida «La línea de hoy» con el gesto del «Cuadro», a petición del usuario (contrato en `.impeccable/surfaces/frontend-src-features-dashboard-dashboardpage-tsx.md`, boceto en `docs/rediseno/boceto-inicio-linea-de-hoy.html`). El saludo es el `h1` (el módulo pasa a llamarse «Inicio»). Encima, una franja de seis cifras del período, ordenada por perfil, cada una con su variación contra el período comparable y su serie en miniatura; pulsar una cifra abre su serie de 12 meses en grande, con eje, el mes en curso punteado, teclado y la tabla de los datos. Debajo, la línea del día: lo vencido agrupado con un ejemplo, Hoy y lo que viene, cada estación con su acción y una sola verde; al lado, servicios por tipo y recaudo contra facturado. **El médico tiene su Inicio de jornada**, decidido con el usuario: sus consultas sin firmar, sus tareas, Hoy y las paradas de su ruta; el Inicio entra en su barra inferior y Familias pasa a «Más». **Backend**: `GET /dashboard/evolucion` (12 meses y el período comparable, con la misma fórmula y caché); «Mora al cierre» pasa a ser histórica (lo pagado después del cierre cuenta como pendiente ese día; antes, la serie habría mostrado meses pasados sin mora), y las fórmulas llevan tildes. La serie entra en la prueba de carga. Cerrado con el veredicto `ship` del revisor final tras dos pasadas de arreglos. |
| `R2-PAN-05` | Servicios y tareas | Listado de servicios, detalle (pensado primero para el móvil), nuevo servicio y tareas. | Hecho (2026-11-14), sin sorteo: hereda el listado con ficha, elegido por el usuario (contrato en `.impeccable/surfaces/frontend-src-features-servicios-serviciospage-tsx.md`). **Listado**: agrupado por día con su recuento, cada fila dice a quién se atiende (la API trae el titular y la mascota, decidido con el usuario), los filtros viven en la URL y, en la vista de la agenda, encima de Hoy van los «Atrasados» que siguen abiertos (`abiertos=true`, decidido con el usuario). **Ficha** (`/servicios/:id`, con las pestañas a la vista): la identidad, el estado y una sola acción verde (salir en ruta a domicilio, iniciar o completar la atención); completar se bloquea mientras falten pasos obligatorios y dice cuáles; los pasos como estaciones, abiertos en el primero que falta. **Los pasos de un servicio que no es consulta se registran en su ficha**, pensada primero para el celular (decidido con el usuario): Rutas lleva ahí con `?origen=ruta` y la ficha ofrece «Volver a mi ruta». Pendientes y franjas en tablas apilables con nombres legibles (antes, códigos como `domiciliario` o `whatsapp`), y la cancelación se confirma en rojo. **Tareas** en tabla apilable: cada tarea dice a quién afecta (la API trae el titular y, si es de un servicio, cuál y de quién; decidido con el usuario) y lo vencido lleva icono y palabra; sale de `PENDIENTES` (ya no desborda a 375 px). **Distintivos**: En ruta, En atención y la prioridad Alta llevan icono propio (decidido con el usuario). El Inicio nombra la mascota y la familia en sus estaciones. Cerrado con el veredicto `ship` del revisor final tras dos pasadas de arreglos. |
| `R2-PAN-06` | Rutas | Sorteo de superficie. Pensada primero para el móvil: la ruta del día de un médico en la calle. | Hecho (2026-11-12): sorteo de superficie, elegida «La línea del día» (contrato en `.impeccable/surfaces/frontend-src-features-rutas-rutaspage-tsx.md`, boceto en `docs/rediseno/boceto-rutas-linea-del-dia.html`). El médico abre en su ruta del día como una línea vertical: hechas plegadas, la que toca abierta con dirección, familia, mascota, franja y su acción, y las que faltan debajo. Quien coordina ve las rutas del día en la plantilla de listado con ficha (generalizada desde Familias a `.con-ficha`), lo que falta por rutear, y planea, agrega y cancela. La API da en cada parada a quién se atiende y dónde. También: «Registrar la atención» cuando al servicio le faltan pasos obligatorios, la llegada ya no deja dos paradas abiertas (fallo del backend), y `datos_demo` deja una ruta de la médica que recorren el barrido y dos recorridos nuevos. Cerrado con el veredicto `ship` del revisor final tras cuatro pasadas. |
| `R2-PAN-07` | Clínica | Sorteo de superficie para la entrada clínica. Listado, historia de la mascota y registro de la atención en casa de la familia, desde el celular. | Hecho (2026-11-12): sorteo de superficie, elegida «Pasos guiados» (contrato en `.impeccable/surfaces/frontend-src-features-clinica-clinicapage-tsx.md`, boceto en `docs/rediseno/boceto-clinica-pasos-guiados.html`). La consulta se recorre como una línea de cinco estaciones, un apartado por pantalla, con lo anotado en la última consulta como referencia; el borrador se guarda al cambiar de apartado y la firma dice qué falta. **La consulta es el registro de la visita**, decidido con el usuario: al firmar la de una visita en atención se registran los pasos del servicio y la visita se puede terminar en Rutas, cuyo «Registrar la atención» abre esa consulta. El médico abre Clínica en su trabajo pendiente (su ruta de hoy y sus consultas sin firmar); la historia usa la plantilla de listado con ficha, y la cola virtual, las respuestas y las plantillas pasan a los patrones del sistema. También: la identidad de la mascota en la consulta en el celular, el halo de la estación actual visible en las tres líneas (Familias, Rutas y Clínica) y el campo de archivo con la forma del botón secundario. Cerrado con el veredicto `ship` del revisor final tras tres pasadas. |
| `R2-PAN-08` | Cartera y preventivos | Cuotas, mora, renovaciones, calendario, autorizaciones y carnet. **El carnet en PDF lleva la marca**, como el carnet impreso de TIMU: el logo, los colores, GeosansLight en el título e Inter en el resto, con fuentes que no estropeen las tildes, y el peso de cada desparasitación (`F2-PRE-07`, pedido por el usuario el 2026-11-11). Hecho por adelantado el 2026-11-11, con `app/core/marca_pdf.py` para el resto de documentos. **Incluye, decidido con el usuario (2026-11-11):** agendar un preventivo desde su estación en la línea de la ficha de Familias, como ya se registra el pago de una cuota. La acción se inyecta desde fuera (`App.tsx` o el espacio de entrada) para que `familias` no importe `preventivos`. Hasta entonces, tocar un preventivo solo lleva a la pestaña de mascotas. | Hecho (2026-11-14), sin sorteo: hereda la bandeja de Tareas, elegida por el usuario (contrato en `.impeccable/surfaces/frontend-src-features-cartera-carterapage-tsx.md`). **El servicio manda** (decidido con el usuario): agendar un preventivo autorizado crea la visita autorizada, autorizar uno autoriza el otro, completar la visita aplica el preventivo con el producto y el lote del paso, y cancelarla lo deja por agendar (antes la vacuna y su autorización se registraban dos veces, y un preventivo con la visita cancelada ya no se podía agendar). **Cartera** como bandeja: «En mora», «Por renovar» (ventana de 90 días) y «Todos» con su recuento; cada fila con el plan, lo que debe y desde cuándo, la cuota, la renovación y el estado, y «Registrar pago» (con la cuota más antigua puesta y nombrada por su mes) o «Renovar»; el titular lleva a la pestaña Cartera de su familia. La API dice qué contrato es renovable. **Preventivos** como bandeja por siguiente paso: «Por autorizar», «Por agendar», «Agendados» y «Todos», agrupada por familia; la familia autoriza de una vez (`POST /preventivos/autorizaciones`, todo o nada) y cada preventivo lleva solo su siguiente paso, que dice la API; «Registrar aplicación» queda para lo aplicado sin visita. **Agendar desde la estación** de la línea de Familias, con la acción inyectada desde `App.tsx`: abre la autorización (o la visita) de todos los preventivos de la estación. **La consulta dice qué pasos registra**: el catálogo de tipos lo trae en cada paso (`lo_registra_la_consulta`) y desaparece la copia `CAMPOS_DE_LA_CONSULTA`. También: la ventana de pago y el estado de cuenta pasan a `cartera`, y el nombre de las cuotas sube del portal a `cartera`. El carnet en PDF con la marca se hizo por adelantado el 2026-11-11. Cerrado con el veredicto `ship` del revisor final tras tres pasadas. |
| `R2-PAN-09` | Comercial y campañas | Bandeja de interesados y conversaciones; segmentos, envíos y encuestas. `CampanasPage` (931 líneas) se divide si su tamaño lo exige. | Hecho (2026-11-14), sin sorteo: hereda el listado con ficha, elegido por el usuario para los dos módulos (contrato en `.impeccable/surfaces/frontend-src-features-comercial-comercialpage-tsx.md`). **Comercial**: los interesados agrupados por etapa con las vistas «Abiertos», «Afiliados» y «Perdidos» y su recuento (sustituyen las tarjetas del embudo); la ficha con la línea de etapas, sus datos y su conversación de WhatsApp, y una sola verde: contestar si espera a un asesor, si no pasar a la etapa siguiente. «Perdido» en un menú, con su motivo. La API dice la etapa siguiente (`siguiente_etapa`), los recuentos por etapa y la conversación de cada interesado, y la bandeja de conversaciones nombra al interesado. `datos_demo` siembra una conversación que pide un asesor, por el mismo camino que un mensaje de Meta. **Campañas**: listado con ficha (a quién le llega, plantilla, audiencia con ejemplos, envío y resultados); enviar ahora pide confirmar con la audiencia. `CampanasPage.tsx` se reparte en un fichero por pestaña; mensajes y plantillas en tablas apilables, con la dirección en palabras. **La traza de mensajes tapa los tokens de un solo uso** (activación, restablecimiento, afiliación y encuesta): el revisor vio en la pestaña Mensajes un correo de activación con su token vigente, legible para el perfil comercial. Campañas sale de `PENDIENTES` y las dos se miden con sus pestañas. Cerrado con el veredicto `ship` del revisor final tras dos pasadas. |
| `R2-PAN-10` | Aliadas y administración | Convenios, remisiones y liquidación; usuarios, planes, reglas, catálogos, IA y reportes. | Hecho (2026-11-14), sin sorteo, en dos superficies con su contrato (`.impeccable/surfaces/frontend-src-features-aliadas-aliadaspage-tsx.md` y `…-admin-adminpage-tsx.md`). **Aliadas en bandeja y ficha** (decidido con el usuario): Remisiones como bandeja (Por usar, Utilizadas, Anuladas y Todas con recuento), cada fila con el titular y la mascota, adónde va y qué cubre, y la vencida con icono y palabra; la API nombra a cada uno, dice `vencida` y da los recuentos. Clínicas en listado con ficha (sus convenios y sus remisiones por usar), Liquidación con período y total. Anular confirmaba en verde y ahora confirma en rojo; el motivo pedía menos de lo que exige la API. `AliadasPage.tsx` se repartió en un fichero por pestaña. **Administración con sus pestañas y los patrones** (decidido con el usuario): Usuarios como bandeja (Equipo, Clínicas aliadas, Familias e Inactivos; la API los agrupa, con un índice en la migración 0042), cambiar el perfil y desactivar se confirman; Planes y Reglas en listado con ficha, con cada regla en palabras y «Probar» dentro de ella (el motor la describe: `condicion_texto`, `accion_texto`, `campos_condicion`), y una regla de un evento retirado se lee pero no se edita; Catálogos dice su estado y qué deja de pasar al apagar; IA con un solo verde y dólares con formato colombiano. **`PENDIENTES` del barrido responsive queda vacía**: ninguna ruta desborda ni falla en contraste a 375, 768 y 1280 px. Cerrado con `ship` del revisor final: Aliadas tras dos pasadas, Administración tras tres. |

## R3 — Familias, aliada y páginas públicas

Todo se diseña primero para el móvil. Las familias suelen llegar desde un enlace de WhatsApp.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R3-PUB-01` | Ingreso | Ingreso, recuperación, restablecimiento y activación de la cuenta (`AccesoLayout`). El panel de marca pasa a marino, con los colores permitidos sobre marino (regla 6 del manual). | Hecho (2026-11-15), sin sorteo: el usuario eligió «Marino con la línea» (contrato en `.impeccable/surfaces/frontend-src-features-auth-accesolayout-tsx.md`). **Composición**: desde 900 px, el panel marino plano con el logo completo en blanco, una frase que le habla a quien llega («Tu peludito, bien cuidado.»; en la activación, «Te damos la bienvenida a la manada TIMU.») y la línea de una familia dibujada como señalética (hechas en verde, «Hoy», la próxima con halo); el formulario en una columna de 400 px. Por debajo, una franja marina con el logo compacto y la línea en miniatura. Desaparecen el antetítulo en pastilla, la tarjeta de vidrio y las tres funciones que vendían la plataforma al equipo. **Ingreso por público, con la contraseña en Familias** (decidido con el usuario): Familias ofrece el código por WhatsApp y, debajo, «Ingresar con contraseña»; antes, una familia que activaba su cuenta solo podía usar esa contraseña en «Equipo TIMU», y una sin celular no tenía cómo entrar. Quien llega desde el portal encuentra abierta la pestaña Familias. **La API dice si el enlace sirve antes de pedir la contraseña** (decidido con el usuario): `POST /auth/enlace` (el token en el cuerpo, no en la URL, que el registro de accesos escribe entera) da vigente, usado, vencido o inválido, el propósito y el nombre de pila, sin gastarlo y con el límite estricto de las credenciales; la pantalla saluda («Hola, Ana») o lo dice de entrada con «Pedir un enlace nuevo». Antes se escribía la contraseña dos veces para enterarse al final. **Al activar o restablecer se entra directo** (decidido con el usuario): `POST /auth/restablecer` abre la sesión y lleva a cada perfil a su espacio. También: la recuperación enviada dice qué pasó y nombra el dato, los campos no heredan la negrita de su etiqueta (el ejemplo parecía un valor escrito), el error de un campo va en rojo y enlazado, y el teléfono del código se agrupa como en el campo. Cerrado con el veredicto `ship` del revisor final tras tres pasadas. |
| `R3-POR-01` | Portal: estructura y mascotas | Navegación del portal en el móvil, inicio, mascotas, carnet y «Agregar un peludo». | Hecho (2026-11-12): sorteo de superficie en modo Operate, elegida «Hoy, estás aquí» (contrato en `.impeccable/surfaces/frontend-src-features-portal-inicioportal-tsx.md`, boceto en `docs/rediseno/boceto-portal-hoy-estas-aqui.html`). El portal toma la estructura del panel (barra marina y, en el celular, barra inferior de cinco destinos). El inicio es la línea de la familia abierta en «hoy», servida por `GET /portal/linea`: lo hecho plegado, lo vencido agrupado (cuotas y preventivos, con el reparto por peludo), una sola acción verde (pagar lo vencido, agendar los preventivos o pagar la próxima cuota), el próximo cobro aunque su cuota no exista y un cierre que dice qué viene. El plan se dice en una frase («En pausa» para la familia) y solo ofrece agendar si el backend lo permitiría. Cada peludo tiene su ficha con su propia línea, su carnet sin contradicciones, su historia y su plan con los cupos de frente (desaparece «ilimitado»). También: las listas y los campos de fecha de todo el sistema dejan de mostrar el control del navegador, decidido con el usuario. Cerrado con el veredicto `ship` del revisor final tras tres pasadas. |
| `R3-POR-02` | Portal: citas, pagos y datos | Citas, pagos, datos y documentos. Se aplica la voz del manual: desaparece «ilimitado» (`PortalPages.tsx`), sustituido por lo que sí aplica, como «sin tope de usos al mes». | Hecho (2026-11-13), sin sorteo: hereda los patrones de `R3-POR-01` («ilimitado» ya había desaparecido allí). **Citas**: agendar es el verde solo si el plan lo permite (si no, dice por qué y lleva a pagos); pestañas Próximas y Pasadas; cada cita con su día en la zona de Colombia, su estado dicho a la familia («Confirmada», «Por autorizar», «En camino») y solo las acciones que el backend acepta (antes se ofrecían en citas que rechazaba); la cancelación se confirma en rojo. **Pagos**: un solo verde por todo lo pendiente y, con varias cuotas, cada una se paga sola; las cuotas se nombran por su mes (la descripción del backend es técnica); el historial dice «No se cobró» en un rechazo, y al volver de la pasarela un aviso dice qué pasó con ese pago, preguntando mientras siga pendiente (antes esa ruta lo ignoraba). **Datos**: titular y documento de solo lectura, el contrato solo si hay uno vigente y los documentos en su panel. `PortalPages.tsx` desaparece, repartido por pantalla. Cerrado con el veredicto `ship` del revisor final. |
| `R3-PUB-02` | Registro en línea | Sorteo de superficie en modo persuasivo para `/afiliacion`, el resultado y el formulario posterior. El plan es protagonista, con su color y con sus condiciones y carencias dichas de frente. Precios y coberturas salen del catálogo. | Pendiente |
| `R3-PUB-03` | Encuesta y carnet | Encuesta de satisfacción y verificación pública del carnet. | Pendiente |
| `R3-ALI-01` | Mi clínica | Validación de remisiones y reporte de la atención de la clínica aliada. | Pendiente |

## R4 — Cierre

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R4-CIE-01` | Recorrido completo | La lista de rutas pendientes de `R0-QAA-02` está vacía (desde `R2-PAN-10`) y se elimina. El recorrido cubre todas las rutas a los cuatro anchos (375, 768, 900 y 1280 px). | Pendiente |
| `R4-CIE-02` | Auditoría | `/impeccable audit` en cada espacio y `/impeccable critique` en el panel y el portal. Se corrigen todos los hallazgos P0 y P1; los P2 y P3 quedan como deuda escrita. | Pendiente |
| `R4-CIE-03` | Documentación final | La skill refresca `DESIGN.md`. Se reescriben `docs/frontend/` (componentes, plantillas y convenciones) y la sección 15 del manual. El `CLAUDE.md` describe las guardas definitivas, y los tres `CLAUDE.md` se condensan (el del backend pasa de 35 KB) sin perder ninguna regla: lo que sea historia o explicación larga va a `docs/`. | Pendiente |
| `R4-CIE-04` | Umbrales de cobertura | Los umbrales de `vitest.config.ts` se ajustan a lo medido, según la regla del `CLAUDE.md`. | Pendiente |

## Mientras dura el rediseño

- **Una pantalla nueva se construye ya con la línea nueva.** La lista de pendientes del barrido
  responsive está vacía desde `R2-PAN-10` y no vuelve a crecer: un fallo de desborde o contraste se
  arregla en el cambio que lo trae.
- **Nada vuelve a la paleta menta.** La guarda lo impide desde `R1-TOK-01`.
- Cada fase se entrega por separado y deja la aplicación usable. Hasta cerrar R3 conviven pantallas
  con la línea nueva y con la antigua (el registro, la encuesta, el carnet y la aliada); es lo
  esperado.
- **Una pantalla con pestañas que se cierra activa `pestanas: true`** en su ruta del barrido
  (`e2e-stack/responsive.spec.ts`), como la ficha de familia: si no, el barrido solo mide la
  pestaña inicial.
- **Cada superficie se cierra con el revisor final de la skill** hasta su `ship`, como
  `R2-PAN-03`, con capturas a 1440, 1180, 900 y 390 px.

### Deuda decidida y notas de cierre

Viven en dos anexos de `docs/rediseno/`, separados de esta hoja el 2026-11-16:

- [**Deuda decidida y techo del revisor**](rediseno/deuda.md): la tabla `DEU-1` a `DEU-70` y
  `DEU-E` con cada decisión del usuario y su estado. Lo que sigue pendiente está arriba, en
  «Dónde se retoma».
- [**Notas de cierre de cada unidad**](rediseno/notas-de-cierre.md): «lo que quedó» al cerrar cada
  una. Una nota abierta nueva se añade allí.

### Orden de lo que sigue

Confirmado por el usuario el 2026-11-12. Primero lo que más se usa desde el celular (`PRODUCT.md`): Rutas
(`R2-PAN-06`) y Clínica (`R2-PAN-07`) para los médicos, y el portal (`R3-POR-01`, `R3-POR-02`)
para las familias. Después el resto del panel (`R2-PAN-04`, `05`, `08`, `09`, `10`), el
ingreso, el registro en línea, la encuesta y la aliada (`R3-PUB-01` a `03`, `R3-ALI-01`), y el
cierre (R4).

## Decisiones tomadas

Confirmadas por el usuario el 2026-11-10:

1. **Primera superficie (`R0-DIR-01`):** el panel con Familias. Es el espacio de uso diario y
   el que más componentes reúne.
2. **Lista de rutas pendientes (`R0-QAA-02`):** se acepta como deuda explícita. Cada entrada es
   una ruta, un ancho y un fallo medido. La prueba falla si una entrada ya pasa, así que la
   lista solo puede encogerse, y debe quedar vacía en `R4-CIE-01`.
3. **El recorrido corre en `e2e-stack/`**, contra el stack real con `datos_demo`.
4. **Inter se sirve desde el proyecto** con un paquete de npm de versión fija, no desde Google
   Fonts.
5. **El color de plan es un campo del catálogo** (`R1-PLA-01`), con su cambio de backend.

Confirmadas por el usuario el 2026-11-10 y el 2026-11-11, cada una escrita donde se aplica:

- **Dirección «la línea de metro»**, navegación inferior en el celular, línea del año completo
  y línea servida por un endpoint: decisiones del contrato de la superficie
  (`.impeccable/surfaces/`).
- **Agendar un preventivo desde su estación va en `R2-PAN-08`**: fila de esa unidad, contrato
  de la superficie y comentario en `FamiliaDetallePage.tsx`.
- **Valen los colores del logo** (naranja ajustado a `#D48200`); **GeosansLight en los títulos
  de 20 px o más** e Inter en el resto; **el logo en SVG**, completo o compacto: manual de
  marca (secciones 2, 12 y 13).
- **La plataforma no gestiona los servicios fúnebres**, **las fotos son de TIMU** y **los
  precios quedan aplazados**: pendientes externos.
- **El carnet lleva el peso de cada desparasitación, quién aplicó y la marca en el PDF**, y el
  peso pasa a la ficha si es el más reciente: `F2-PRE-07` en el backlog y `R2-PAN-08`.

## Riesgos

- **Volumen.** El alcance de arriba se toca entero. Las pantallas más grandes (Campañas con 931
  líneas, Servicios con 562) concentran el riesgo. El portal (821 líneas en un fichero) ya se
  repartió por pantalla.
- **Pruebas que buscan textos.** Las pruebas consultan por rol y etiqueta, pero cambiar un
  texto rompe las que lo buscan literalmente. Se ajustan en la misma unidad.
- **El sorteo necesita red.** La telemetría está apagada, pero los sorteos consultan el
  catálogo de direcciones de impeccable.style.
- **Las entregas de marca de TIMU ya están aplicadas.** El logo en vector y GeosansLight
  (títulos de 20 px o más) están integrados.
- **El recorrido de `e2e-stack/` solo corre en CI al empujar a `main`.** En local hay que
  correrlo con el stack y `datos_demo` antes de empujar.

## Fuera de alcance

- **Tema oscuro.** Por decisión de producto, el panel es de tema claro (`docs/frontend/conventions.md`).
- **PWA de familias.** Es una fase posterior, según la propuesta.
- **Portada pública (index).** Una página de inicio pública de TIMU se construirá aparte,
  cuando TIMU entregue los recursos gráficos (pendientes externos). Las demás páginas públicas
  sí entran: ingreso, registro en línea, encuesta y verificación de carnet.
- **Contenidos de la web pública timu.com.co.** Es de TIMU; sus contradicciones con el manual
  están en pendientes externos.
