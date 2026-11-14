---
version: 1
slug: "frontend-src-features-servicios-serviciospage-tsx"
primary_target: "frontend/src/features/servicios/ServiciosPage.tsx"
related_targets: ["frontend/src/features/servicios/ServicioDetallePage.tsx","frontend/src/features/servicios/FichaServicio.tsx","frontend/src/features/tareas/TareasPage.tsx"]
---

# Panel del equipo · Servicios y tareas (R2-PAN-05)

## Alcance y modo

El listado de servicios, la ficha de un servicio (pensada primero para el celular), el alta de un
servicio, los pendientes, las franjas de agenda y Tareas. Superficie dentro de la línea visual de
Familias (`DESIGN.md`), sin sorteo: la hoja de ruta no lo pide para esta unidad y hereda los
patrones construidos. Modo: Operate. Construcción: en código.

## Público, tarea y restricciones

- Operaciones y administración, en la oficina: ven la agenda del día y los siguientes, a quién se
  atiende y en qué estado está cada servicio, agendan, reprograman, cancelan y gestionan pendientes
  y franjas.
- Médico, con el celular: llega a la ficha desde su parada de Rutas («Registrar la atención») o
  desde Servicios, avanza el servicio y registra los pasos de la atención, y vuelve a su ruta.
- Comercial y operaciones en Tareas: lo que hay por resolver, quién lo tiene y qué vence.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px en
  táctil, tablas apilables, WCAG 2.2 AA, Radix para lo interactivo.

## Direction contract

THESIS: Un servicio se lee como una parada de la ruta: a quién se atiende (la mascota y su
familia), cuándo y en qué estado, con la acción que toca arriba y los pasos de la atención como
una lista que se completa. Rechaza la tabla de códigos sin nombres y la ficha de datos sueltos con
las acciones al final y dos verdes a la vez.

OWN-WORLD: El de `DESIGN.md`. Listado con ficha (`.con-ficha`): filas de 12 px de relleno con hilo,
el servicio y su hora tabular, «Mascota · Titular», distintivo de estado por tono e icono. Ficha
blanca en panel de 12 px: título de 24 px, identidad («Mascota (especie) · Titular») en 14 px y
color de texto, no en 13 px suave (el médico la lee de pie, con el celular), acción de estado en verde
lleno (una), el resto suaves, secundarias o planas. Pasos como estaciones: hecho lleno, el que
falta en contorno, el obligatorio pendiente dicho en texto.

STORY: Quien coordina abre Servicios y ve de un vistazo a quién se atiende hoy y qué falta por
autorizar; abre uno y lo reprograma o lo cancela sin perder el listado. El médico abre la ficha
desde su parada, ve qué pasos faltan, los registra uno a uno, termina la atención y vuelve a su
ruta.

FIRST VIEWPORT: 1440×900: pestañas Servicios, Pendientes y Franjas; listado de 420 px con
filtros (estado, ciudad, desde y hasta) y «Agendar servicio»; la ficha abierta a la derecha con el
servicio, la mascota y la familia, la hora, el estado y su acción, y debajo los pasos y los
pendientes. 390×844: la ficha sola, con volver, la acción de estado de 48 px a todo el ancho y
los pasos que faltan inmediatamente debajo.

FORM: listado con ficha heredado de Familias, Rutas y Clínica; seed: none (pinned) — el usuario
eligió «Listado con ficha» («la plantilla de Familias, Rutas y Clínica: el listado a la izquierda
y el servicio abierto a la derecha; en el celular, uno u otro»), el 2026-11-14.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-14)

- **Los pasos de un servicio que no es consulta se registran en su ficha**, pensada primero para
  el celular; Rutas sigue llevando ahí con «Registrar la atención». Decidido con el usuario (antes
  se había dejado abierto en el cierre de Rutas). La consulta sigue registrándose al firmar la
  consulta clínica (`R2-PAN-07`).
- **El listado trae a quién se atiende**: `GET /servicios` devuelve el titular y la mascota de
  cada servicio, en lote. Decidido con el usuario.
- **Servicios usa el listado con ficha**, como Familias, Rutas y Clínica. Decidido con el usuario.

- **Atrasados encima de hoy** (decidido con el usuario el 2026-11-14, tras la primera revisión):
  sin filtros, la agenda pinta antes de Hoy lo anterior que sigue abierto (`abiertos=true`).
- **La bandeja de tareas dice a quién afecta** (decidido con el usuario): titular y, si es de un
  servicio, su tipo y su mascota, con enlace a cada uno.
- **Icono propio para En ruta, En atención y la prioridad Alta** (decidido con el usuario): los
  tonos no cambian; se distinguen sin leer la palabra. Afecta a todas las superficies.
- **El barrido responsive no mide 900 px**: añadirlo sumaría a `PENDIENTES` fallos de módulos sin
  rediseñar, y esa lista solo puede encoger. Los 900 px de esta superficie se comprueban en las
  capturas del revisor.

- **Revisión final (2026-11-14)**: `ship` tras dos pasadas de arreglos (Tareas a 900, atrasados,
  pestañas con la ficha abierta, a quién afecta cada tarea, la ficha traída a la vista, iconos de
  estado, la identidad a 14 px con su motivo; después, «Operaciones» partido a 390, el recuento con
  los atrasados y el separador de la fecha vencida).

## Pendiente

- Lo que quedó, en la hoja de ruta («Lo que quedó de Servicios y Tareas tras cerrar `R2-PAN-05`»).
