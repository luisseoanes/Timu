# R4-CIE-02: auditoría y crítica del rediseño (2026-11-21)

Anexo de la [hoja de ruta del rediseño](../hoja-de-ruta-rediseno.md). `R4-CIE-02` pide
`/impeccable audit` en cada espacio y `/impeccable critique` en el panel y el portal, corregir todos
los P0 y P1 y dejar los P2 y P3 como deuda escrita. Aquí está lo que se midió, lo que se encontró, lo
que se decidió con el usuario y lo que se hizo. Lo que quedó sin hacer está en [deuda](deuda.md)
(`DEU-71` a `DEU-82`). Las dos críticas completas se guardaron con la skill en
`.impeccable/critique/` (fuera del repositorio).

## Auditoría técnica: 17/20 (Bien)

**Cómo se midió.** El detector de impeccable sobre el código (`frontend/src`, 0 hallazgos) y sobre las
47 rutas renderizadas del barrido, con el perfil que usa cada una, sus pestañas y sus fichas, a 1280 y
390 px (72 hallazgos en 7 reglas); axe-core con todas las reglas WCAG 2.2 A y AA en las mismas rutas
(137 fallos en 4 reglas); la medida de los objetivos táctiles a 390 px y el tamaño del build. Chromium
de Playwright con viewport emulado, sin gesto táctil sintetizado.

| Dimensión | Nota | Hallazgo clave |
| --- | --- | --- |
| Accesibilidad | 3 | Nombre accesible distinto del texto visible en el botón de la cuenta, en todas las pantallas con sesión (WCAG 2.5.3) |
| Rendimiento | 3 | Un solo paquete de 998 kB (277 kB gzip) para los cuatro espacios |
| Temas | 4 | Tokens y roles del manual, con guarda; el tema oscuro está fuera de alcance por decisión de producto |
| Responsive | 3 | Sin desbordes; pestañas, segmentos y la cuenta, de 38–40 px en el celular |
| Integridad | 4 | Código limpio para el detector; lo renderizado, casi todo falsos positivos verificados |

**P1, los seis corregidos** (`fix(frontend): las pantallas cumplen las reglas A y AA de WCAG 2.2`):

- **2.5.3, nombre con el texto visible**: el botón de la cuenta («MO, cuenta de …»), el mensaje que
  abre su conversación en Mensajes, «Editar texto» de Plantillas y el apartado «Plan» de la consulta
  guiada («Plan (Tratamiento)»).
- **1.4.1, enlaces dentro de una frase**: van subrayados los enlaces sin clase dentro de `p`, `li`,
  `dd` o `span` (`base.css`).
- **2.5.8, tamaño del objetivo**: los teléfonos de la portada y los enlaces de la línea de detalle de
  las bandejas.
- **2.1.1, teclado**: la tabla de beneficios del plan, que se desplaza en el celular, recibe el foco.

La guarda del barrido (`e2e-stack/responsive.spec.ts`) y la de `e2e/publicas.spec.ts` pasaron de
pedir solo el contraste a pedir todas las reglas WCAG 2.2 A y AA: con ellas salieron los dos últimos,
a anchos que la auditoría no midió.

**P2, hechos los tres** (decidido con el usuario):

- **Encabezados**: 35 vistas saltaban del h1 de la página al h3 de sus tarjetas. Las 28 cabeceras de
  tarjeta de primer nivel son h2 (con el aspecto de siempre, `.tarjeta-cabeza > h2`) y sus subapartados,
  h3. El barrido falla ahora si una pantalla salta un nivel.
- **Objetivos táctiles de 44 px**: pestañas, segmentos de las bandejas, el círculo de la cuenta y «Ver
  cada una» de la línea, en pantallas estrechas o táctiles (el criterio de `R1-CMP-01`).
- **El paquete**: las páginas públicas y el ingreso cargan con la app; cada módulo del panel, el portal
  y la clínica aliada, al abrirse, con la pantalla cargando dentro de su layout (`CargandoPantalla`).
  El principal pasó de 998 kB (277 kB gzip) a 498 kB (159 kB gzip).

**P3**: el peso con coma y sin partir en la tabla de Mascotas se hizo de paso; los demás, en la
deuda.

**Falsos positivos del detector, verificados en captura**: `first-viewport-column-overflow` (el
listado con ficha), `icon-tile-stack` (la flecha de volver de la ficha en el celular) y los enlaces de
las filas de los listados (22 px, pero su `::after` cubre la fila).

## Crítica del panel: 25/40 (Aceptable)

Dos evaluaciones aisladas en subagentes (revisión de diseño, y detector con navegador), sin
superposición visual porque la sesión no tenía navegador a la vista del usuario.

**Especificidad: propio de TIMU.** La línea de metro es la gramática del panel (Familias, el Inicio,
la ruta, la consulta, el embudo de Comercial). Lo intercambiable: las bandejas y las diez pestañas de
Administración.

**P1, los tres corregidos:**

- **El médico no podía abrir una historia fuera de su ruta** (el buscador pedía `/familias`, que le da
  403, y la lista salía vacía en silencio; la historia no decía de quién era la mascota). Ahora busca
  en el módulo clínico (`GET /clinica/mascotas`), la historia lee el titular de
  `GET /clinica/mascotas/{id}`, y un fallo de búsqueda se dice, también en `SelectorFamilia`
  (decidido con el usuario: buscar historias, no quitarle el buscador).
- **Las cifras no cuadraban entre pantallas**: el Inicio cuenta los preventivos por autorizar con el
  recuento de la bandeja (decía 62 donde la bandeja decía 15); la vista de Cartera se llama «Vencidas»
  y el Inicio dice «contratos con cuotas vencidas» (listaba contratos activos con uno o dos días de
  atraso bajo «En mora»); la parada cuya franja pasó se dice «Atrasada» en la ruta y va antes de Hoy en
  el Inicio de la médica.
- **Tareas era un muro**: una sola acción por fila («Tomar», «Cerrar» o la conversación) y el resto en
  el menú de tres puntos, con «Asignar a…» en submenú; la descripción en una línea; abre en «Mis
  tareas» y, sin tareas propias pendientes, en «Sin asignar» (decidido con el usuario sobre dos
  bocetos).

**P2 de la evaluación B, hecho**: «Dar de baja» de la tabla de Mascotas quedaba fuera de la vista a
1280 px; pasó al menú de tres puntos, en rojo (decidido con el usuario).

## Crítica del portal: 24/40 (Aceptable)

El detector no encontró nada en las 22 vistas. **Especificidad**: propio en el Inicio y la ficha del
peludo; genérico en Pagos, Citas y Datos.

**P1, los tres corregidos**, todos en el momento de la familia con el plan en pausa:

- **Se ofrecía en verde un alta que iba a fallar**: el plan trae `motivo_sin_alta`, el mismo texto con
  que la cotización la rechaza, y Peludos y la pantalla del alta lo dicen antes del formulario, con «Ir
  a tus pagos».
- **«En pausa» no decía qué se pierde y «Su plan» marcaba los beneficios con ✓**: el plan trae
  `aviso_pausa`, que el Inicio y «Su plan» dicen de frente, sin marcar los beneficios como disponibles.
  Valor provisional (el comportamiento de hoy: no se agenda ni se agrega un peludo; la orientación
  virtual sigue), decidido con el usuario y anotado en
  [pendientes externos](../pendientes-externos.md#valores-provisionales).
- **La urgencia no tenía salida**: cada «escríbenos por WhatsApp» es un enlace al WhatsApp de TIMU, y
  la orientación virtual da para una urgencia el primer teléfono de Datos de TIMU (provisional: la
  línea propia la da TIMU).

De paso, `R1-CMP-03`: los vacíos de R3 (portal y páginas públicas) dicen qué aparecerá o qué hacer.
