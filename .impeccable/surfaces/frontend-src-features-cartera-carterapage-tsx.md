---
version: 1
slug: "frontend-src-features-cartera-carterapage-tsx"
primary_target: "frontend/src/features/cartera/CarteraPage.tsx"
related_targets: ["frontend/src/features/preventivos/PreventivosPage.tsx","frontend/src/features/familias/FamiliaDetallePage.tsx"]
---

# Panel del equipo · Cartera y preventivos (R2-PAN-08)

## Alcance y modo

La bandeja de Cartera (mora, renovaciones y todos los contratos), la bandeja de Preventivos (lo que
falta autorizar, agendar y lo ya agendado), el carnet por mascota y agendar un preventivo desde su
estación en la línea de la ficha de Familias. Superficie dentro de la línea visual de Familias
(`DESIGN.md`), sin sorteo: la hoja de ruta no lo pide y hereda los patrones construidos. Modo:
Operate. Construcción: en código.

## Público, tarea y restricciones

- Comercial y administración en Cartera, en la oficina: a quién cobrar hoy (lo más atrasado
  primero), registrar el pago que llegó por fuera de la pasarela y renovar los contratos que entran
  en su ventana de 90 días.
- Operaciones (y comercial) en Preventivos: pedir a cada familia la autorización de lo que se
  acerca, de una vez por familia (la autorización llega por WhatsApp o por teléfono), y agendar la
  visita de lo autorizado. El médico consulta el carnet y registra una aplicación hecha sin visita.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px en
  táctil, tablas apilables, WCAG 2.2 AA, Radix para lo interactivo. El panel no copia reglas del
  backend: la API dice qué contrato se puede renovar y cuál es el siguiente paso de cada
  preventivo.

## Direction contract

THESIS: Cartera y Preventivos son bandejas de trabajo: cada fila dice a quién (la familia, y en
preventivos sus peludos), cuánto o qué, desde cuándo, y lleva la única acción que toca. Rechaza el
listado de 9 columnas sin acción, las fechas `04/11/2026` repetidas y la ventana con cuatro
botones conmutables para decidir qué hacer con un preventivo.

OWN-WORLD: El de `DESIGN.md`. La bandeja de Tareas (`tabla-apilable` a todo el ancho, selector
segmentado de vistas con su recuento, filas con 12 px de relleno e hilo), el marcador de plan
(cuadrado de 12 px del color del catálogo y el nombre), los distintivos por tono e icono, lo
vencido con icono y palabra, las cifras tabulares. En Preventivos las filas se agrupan por familia,
con el titular como cabecera del grupo y una acción por grupo cuando la familia decide de una vez
(autorizar).

STORY: Comercial abre Cartera en «En mora», ve primero a Ana Ruiz, que debe $ 225.000 desde hace
85 días, y registra el pago que le llegó por transferencia sin salir de la bandeja; pasa a «Por
renovar» y renueva un contrato que vence en 30 días. Operaciones abre Preventivos en «Por
autorizar», escribe a Jorge Ramírez, registra de una vez la autorización de los cuatro preventivos
de Rocky y los agenda desde «Por agendar». El médico completa la visita en la ficha del servicio y
el preventivo queda aplicado solo.

FIRST VIEWPORT: 1440×900: el `h1` del módulo; vistas segmentadas con recuento, buscador y ciudad;
la tabla con titular y plan, lo que debe y desde cuándo, la renovación y el estado, con la acción
de la fila a la derecha. 390×844: vistas en dos filas, cada fila de la tabla como bloque con su
título (el titular), sus pares etiqueta y valor y la acción a todo el ancho.

FORM: bandeja heredada de Tareas; seed: none (pinned) — el usuario eligió «Bandeja» para Cartera
(«tabla apilable como Tareas, con vistas En mora, Por renovar y Todos, con su recuento. Cada fila
ofrece su acción… El titular lleva a la pestaña Cartera de su familia») y «Bandeja por siguiente
paso» para Preventivos («Por autorizar, Por agendar, Agendados y Todos… Lo de una misma familia va
junto… Cada fila lleva una sola acción, la de su siguiente paso»), el 2026-11-14.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-14)

- **El servicio manda** (decidido con el usuario): la visita de un preventivo es su registro. Un
  preventivo autorizado agenda una visita ya autorizada, autorizar uno autoriza al otro, completar
  la visita aplica el preventivo con el producto y el lote del paso, y cancelarla lo deja por
  agendar. «Registrar aplicación» queda para lo aplicado sin visita.
- **Cartera es una bandeja** y **Preventivos, una bandeja por siguiente paso** (decidido con el
  usuario). La API trae a quién afecta cada preventivo y su siguiente paso; la de cartera, los
  planes con su color, si el contrato se puede renovar y los recuentos de cada vista.
- **Agendar un preventivo desde su estación** de la línea de Familias (decidido con el usuario el
  2026-11-11): la acción se inyecta desde `App.tsx` para que `familias` no importe `preventivos`.
- **La consulta dice qué pasos registra**: se cierra la copia `CAMPOS_DE_LA_CONSULTA` del panel.

- **Revisión final (2026-11-14)**: `ship` tras tres pasadas. Arreglos: la acción de fila a todo el
  ancho al apilar, una sola redacción del preventivo («refuerzo» en vez de «dosis 1, refuerzo»), los
  filtros que bajan juntos por debajo de 1180 px, sin cortes en importes y fechas, la cuota nombrada
  por su mes en la ventana de pago, «Por autorizar» con su propio icono, la estación que pide todos
  sus preventivos de una vez y lo vencido del carnet en una pieza.

## Pendiente

- Lo que quede, en las notas de cierre del rediseño (`docs/rediseno/notas-de-cierre.md`, «Lo que quedó de Cartera y preventivos»).
