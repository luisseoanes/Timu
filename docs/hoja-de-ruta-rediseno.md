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
  que entregar TIMU (logo en vector, GeosansLight).

Los IDs siguen el patrón `fase-módulo-consecutivo` del [backlog](backlog.md), con fases `R0` a
`R4` para no confundirlas con las del backend.

## Estado

Creada el 2026-11-10. R0 y R1 se trabajaron el mismo día; lo marcado **Parcial** dice qué falta y en qué unidad se cierra. Cuando una cambia de estado se
actualiza aquí, igual que en el backlog.

| Fase | Unidades | Hecho | Parcial | Pendiente |
| --- | ---: | ---: | ---: | ---: |
| R0 — Preparación | 4 | 4 | 0 | 0 |
| R1 — Fundaciones | 7 | 5 | 2 | 0 |
| R2 — Panel del equipo | 10 | 0 | 0 | 10 |
| R3 — Familias, aliada y páginas públicas | 6 | 0 | 0 | 6 |
| R4 — Cierre | 4 | 0 | 0 | 4 |
| **Total** | **31** | **9** | **2** | **20** |

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

### Definición de terminado de cada unidad

Una unidad está **Hecha** cuando:

1. Sus componentes solo usan roles de color del manual: la guarda de tokens está en verde.
2. Sus rutas salieron de la lista de pendientes del recorrido responsive y pasan a 375, 768 y
   1280 px, sin desborde horizontal y sin fallos de contraste de `axe-core`.
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
| `R1-CMP-02` | Datos | La tabla con su versión para el móvil (la forma la fija la dirección), la paginación, los filtros y el orden. El distintivo de estado (pastilla, icono y texto) y el marcador de plan (regla 4 del manual). | Parcial: `Insignia` (pastilla con icono por tono) sustituye a los 23 distintivos escritos a mano, y el marcador de plan está hecho. La versión móvil de la tabla se construye con la primera tabla real, en `R2-PAN-02`. |
| `R1-CMP-03` | Capas y avisos | La ventana modal sobre Radix (en el móvil, hoja que sube desde abajo), los avisos, las pestañas y los menús. Los estados de carga con esqueleto, los vacíos que explican qué hacer y los errores con «Reintentar». | Parcial: esqueleto de carga anunciado a los lectores de pantalla, «Reintentar» solo ante fallos pasajeros y la ventana modal como hoja inferior en pantallas estrechas. Que cada vacío diga qué hacer se revisa con cada pantalla en R2 y R3; hoy no hay menús. |
| `R1-CMP-04` | Marca e iconos | `MarcaTimu` pasa a ser el marcador de texto del manual (sección 13), con el lema «Medicina veterinaria prepagada». Los iconos se ajustan al lenguaje de la dirección. | Hecho: `MarcaTimu` es el marcador de texto con el lema del manual, sin la huella. Los iconos se mantienen: un trazo y sin relleno, como los pictogramas de señalética de la dirección. |

## R2 — Panel del equipo

La primera superficie fija la línea visual de todo lo demás. Los médicos usan sobre todo el
celular para Rutas, el detalle de Servicios y Clínica: esas pantallas se diseñan primero para
el móvil.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R2-PAN-01` | Estructura del panel | `AppLayout` con la navegación de escritorio y una navegación de móvil que llegue a todo el menú del perfil, más la cabecera. Los estados de `ProtectedRoute` (cargando y «Reintentar»). | En curso. Hecho: barra marina con los módulos que caben y el resto en «Más», menú de la cuenta, cabecera con el h1 del módulo, y en el móvil barra inferior con los cuatro módulos de cada perfil más «Más». Falta: los estados de `ProtectedRoute`. |
| `R2-PAN-02` | Familias | Listado, detalle con sus siete pestañas y las ventanas de nueva familia, afiliar y ficha de mascota, según el contrato de dirección. La API expone la línea de cada familia (cuotas, preventivos y servicios) en un endpoint propio, y el listado la muestra en miniatura sin pedir tres recursos por fila. La tabla tiene su versión para el móvil (pendiente de `R1-CMP-02`). | En curso. Hecho: endpoint de la línea, listado con la miniatura, ficha sobre la línea (orientación medida, pliegue de hechas, mismo día en una estación), mascotas y cartera bajo la línea, pago de una cuota desde su estación y acciones de estado en un menú. Falta: el contenido de las siete pestañas (sus tablas se cortan a 390 px), las ventanas de nueva familia, afiliar y ficha de mascota, y la tabla para el móvil. Decisión abierta: agendar un preventivo desde su estación cruza a `preventivos` (ver `R2-PAN-08`). |
| `R2-PAN-03` | Cierre de la línea visual | Revisor final sobre la estructura y Familias con veredicto `ship`. Después, la skill escribe `DESIGN.md` y `.impeccable/design.json` desde lo construido, y `docs/frontend/design-system.md` remite a `DESIGN.md`. | Pendiente |
| `R2-PAN-04` | Inicio | Sorteo de superficie para el tablero de inicio. Indicadores con su evolución, y series de gráfico según el manual. | Pendiente |
| `R2-PAN-05` | Servicios y tareas | Listado de servicios, detalle (pensado primero para el móvil), nuevo servicio y tareas. | Pendiente |
| `R2-PAN-06` | Rutas | Sorteo de superficie. Pensada primero para el móvil: la ruta del día de un médico en la calle. | Pendiente |
| `R2-PAN-07` | Clínica | Sorteo de superficie para la entrada clínica. Listado, historia de la mascota y registro de la atención en casa de la familia, desde el celular. | Pendiente |
| `R2-PAN-08` | Cartera y preventivos | Cuotas, mora, renovaciones, calendario, autorizaciones y carnet. Si se aprueba, la acción de agendar un preventivo se inyecta en la ficha de Familias para atenderlo desde su estación de la línea, sin que `familias` importe `preventivos`. | Pendiente |
| `R2-PAN-09` | Comercial y campañas | Bandeja de interesados y conversaciones; segmentos, envíos y encuestas. `CampanasPage` (931 líneas) se divide si su tamaño lo exige. | Pendiente |
| `R2-PAN-10` | Aliadas y administración | Convenios, remisiones y liquidación; usuarios, planes, reglas, catálogos, IA y reportes. | Pendiente |

## R3 — Familias, aliada y páginas públicas

Todo se diseña primero para el móvil. Las familias suelen llegar desde un enlace de WhatsApp.

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R3-PUB-01` | Ingreso | Ingreso, recuperación, restablecimiento y activación de la cuenta (`AccesoLayout`). El panel de marca pasa a marino, con los colores permitidos sobre marino (regla 6 del manual). | Pendiente |
| `R3-POR-01` | Portal: estructura y mascotas | Navegación del portal en el móvil, inicio, mascotas, carnet y «Agregar un peludo». | Pendiente |
| `R3-POR-02` | Portal: citas, pagos y datos | Citas, pagos, datos y documentos. Se aplica la voz del manual: desaparece «ilimitado» (`PortalPages.tsx`), sustituido por lo que sí aplica, como «sin tope de usos al mes». | Pendiente |
| `R3-PUB-02` | Registro en línea | Sorteo de superficie en modo persuasivo para `/afiliacion`, el resultado y el formulario posterior. El plan es protagonista, con su color y con sus condiciones y carencias dichas de frente. Precios y coberturas salen del catálogo. | Pendiente |
| `R3-PUB-03` | Encuesta y carnet | Encuesta de satisfacción y verificación pública del carnet. | Pendiente |
| `R3-ALI-01` | Mi clínica | Validación de remisiones y reporte de la atención de la clínica aliada. | Pendiente |

## R4 — Cierre

| ID | Trabajo | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| `R4-CIE-01` | Recorrido completo | La lista de rutas pendientes de `R0-QAA-02` está vacía y se elimina. El recorrido cubre las 34 rutas a los tres anchos. | Pendiente |
| `R4-CIE-02` | Auditoría | `/impeccable audit` en cada espacio y `/impeccable critique` en el panel y el portal. Se corrigen todos los hallazgos P0 y P1; los P2 y P3 quedan como deuda escrita. | Pendiente |
| `R4-CIE-03` | Documentación final | La skill refresca `DESIGN.md`. Se reescriben `docs/frontend/` (componentes, plantillas y convenciones) y la sección 15 del manual. El `CLAUDE.md` describe las guardas definitivas. | Pendiente |
| `R4-CIE-04` | Umbrales de cobertura | Los umbrales de `vitest.config.ts` se ajustan a lo medido, según la regla del `CLAUDE.md`. | Pendiente |

## Mientras dura el rediseño

- **Una pantalla nueva se construye ya con la línea nueva**, salvo que su espacio todavía no
  tenga componentes base. En ese caso entra en la lista de pendientes con su ID de esta hoja.
- **Nada vuelve a la paleta menta.** La guarda lo impide desde `R1-TOK-01`.
- Cada fase se entrega por separado y deja la aplicación usable. Durante R2 y R3 conviven
  pantallas con la línea nueva y con la antigua; es lo esperado.

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

## Riesgos

- **Volumen.** El alcance de arriba se toca entero. Las pantallas más grandes (Campañas con 931
  líneas, el portal con 821, Servicios con 562) concentran el riesgo.
- **Pruebas que buscan textos.** Las pruebas consultan por rol y etiqueta, pero cambiar un
  texto rompe las que lo buscan literalmente. Se ajustan en la misma unidad.
- **El sorteo necesita red.** La telemetría está apagada, pero los sorteos consultan el
  catálogo de direcciones de impeccable.style.
- **Faltan dos entregas de TIMU.** Sin logo en vector se usa el marcador de texto, y sin
  GeosansLight todo va en Inter. Cuando lleguen, se abre una unidad para aplicarlos.
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
