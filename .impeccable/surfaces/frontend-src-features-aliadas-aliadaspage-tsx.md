---
version: 1
slug: "frontend-src-features-aliadas-aliadaspage-tsx"
primary_target: "frontend/src/features/aliadas/AliadasPage.tsx"
related_targets: ["frontend/src/features/aliadas/Remisiones.tsx","frontend/src/features/aliadas/Clinicas.tsx","frontend/src/features/aliadas/Liquidacion.tsx"]
---

# Panel del equipo · Aliadas (R2-PAN-10, primera parte)

## Alcance y modo

Aliadas: las remisiones a clínicas aliadas, las clínicas con sus convenios y la liquidación del
período. Superficie dentro de la línea visual de Familias (`DESIGN.md`), sin sorteo: hereda los
patrones construidos (bandeja de Cartera, listado con ficha de Comercial). Modo: Operate.
Construcción: en código. Administración, la segunda parte de R2-PAN-10, tiene su propio contrato.

## Público, tarea y restricciones

- Operaciones, comercial, médicos y administración, en la oficina: emitir una remisión para una
  mascota, ver qué remisiones están por usar (y cuáles vencieron sin usarse) y anular la que no se
  usará.
- Administración: registrar clínicas y sus convenios, desactivar una clínica y liquidar lo que TIMU
  le debe a cada aliada en el período.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px en
  táctil, tablas apilables, WCAG 2.2 AA, Radix para lo interactivo. El panel no copia reglas del
  backend: la API dice de quién es cada remisión y si está vencida.

## Direction contract

THESIS: Las remisiones se trabajan como una bandeja: lo que está por usar arriba, la que vence
antes primero, cada fila dice de quién es (titular y mascota), adónde va y qué cubre, y la única
acción de la fila es anularla. Las clínicas se abren como un registro: sus datos, sus convenios y
lo que tiene pendiente. Rechaza la tabla con códigos sin nombre, el filtro de estado en una lista y
la anulación confirmada en verde.

OWN-WORLD: El de `DESIGN.md`. Bandeja: selector segmentado de vistas con recuento, tabla apilable a
todo el ancho de un panel blanco, lo vencido con icono, fecha y la palabra. Listado con ficha
(`.con-ficha`): filas con hilo, ficha blanca con el nombre a 34 px, datos en pares etiqueta/valor,
bloques con su h3 y una sola acción verde.

STORY: Operaciones abre Aliadas y ve en «Por usar» la remisión de Jorge Ramirez para Rocky a la
Clínica Veterinaria del Norte, con su cobertura y cuándo vence. Administración abre la clínica, ve
su convenio de radiografía y la remisión pendiente, y registra un convenio nuevo. A fin de mes
liquida el período y descarga el CSV.

FIRST VIEWPORT: 1440×900: pestañas Remisiones, Clínicas y convenios, Liquidación; en Remisiones, el
título con «Emitir remisión» en verde, las vistas Por usar, Utilizadas, Anuladas y Todas con su
recuento y la tabla. 390×844: las vistas en dos filas de dos y las filas apiladas.

FORM: bandeja heredada de Tareas, Cartera y Preventivos; listado con ficha heredado de Familias,
Comercial y Campañas; seed: none (pinned) — el usuario eligió «Bandeja y ficha» para Aliadas
(«Remisiones como bandeja: vistas Por usar, Utilizadas, Anuladas y Todas con recuento, tabla
apilable y Emitir remisión como verde. Clínicas en listado con ficha: la clínica abierta con sus
datos, sus convenios y sus remisiones. Liquidación sigue en su pestaña, con el período arriba y la
tabla apilable»), el 2026-11-14.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-14)

- **Aliadas en bandeja y ficha** (decidido con el usuario).
- **La API dice de quién es cada remisión** (titular, mascota y clínica en el listado), si está
  vencida (`vencida`: emitida y pasada su fecha) y cuántas hay en cada estado
  (`/aliadas/remisiones/recuentos`). «Por usar» ordena por la que vence antes.
- **Anular confirma en rojo** con «Mantenerla»; antes confirmaba en verde.
- **Activar o desactivar una clínica va en el menú**: es reversible y no compite con «Nuevo
  convenio».

## Pendiente

- Lo que quede, en la hoja de ruta («Lo que quedó de Aliadas y administración»).
