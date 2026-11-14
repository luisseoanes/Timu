---
version: 1
slug: "frontend-src-features-comercial-comercialpage-tsx"
primary_target: "frontend/src/features/comercial/ComercialPage.tsx"
related_targets: ["frontend/src/features/campanas/CampanasPage.tsx","frontend/src/features/campanas/Campanas.tsx","frontend/src/features/comercial/FichaInteresado.tsx"]
---

# Panel del equipo · Comercial y campañas (R2-PAN-09)

## Alcance y modo

Comercial: los interesados del embudo, la ficha de cada uno con su conversación de WhatsApp, la bandeja
de conversaciones que esperan a un asesor y el guion del asistente. Campañas: las campañas por WhatsApp
con su ficha, los segmentos, las encuestas, los mensajes con las bajas y las plantillas de WhatsApp.
Superficie dentro de la línea visual de Familias (`DESIGN.md`), sin sorteo: hereda los patrones
construidos. Modo: Operate. Construcción: en código.

## Público, tarea y restricciones

- Comercial y administración, en la oficina: a quién atender hoy en el embudo, contestar a quien pidió
  un asesor por WhatsApp, mover a cada interesado de etapa y marcar lo perdido con su motivo.
- Mercadeo (comercial y administración): crear y programar campañas, ver a quién le llegan y cómo les
  fue; operaciones las ve sin gestionarlas.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px en
  táctil, tablas apilables, WCAG 2.2 AA, Radix para lo interactivo. El panel no copia reglas del
  backend: la API dice la etapa siguiente de cada interesado.

## Direction contract

THESIS: El embudo se lee como la línea de una familia: cada interesado tiene su línea de etapas
(Nuevo → Contactado → Cotizado → En afiliación → Afiliado), lo que toca hacer arriba y su conversación
debajo. Una campaña se abre como un registro: a quién le llega, qué mensaje sale y cómo le fue. Rechaza
la tabla con una lista de etapas por fila, los orígenes en código y las campañas en una ventana.

OWN-WORLD: El de `DESIGN.md`. Listado con ficha (`.con-ficha`): filas de 12 px de relleno con hilo,
agrupadas por etapa con su recuento (como los días de Servicios); ficha blanca en panel de 12 px con el
nombre a 34 px, la línea de etapas con la geometría de la guía de la consulta (marina, la actual con su
halo) y una sola acción verde. La conversación como burbujas: lo que escribió la persona en blanco, lo
que respondimos en verde tenue.

STORY: Comercial abre Comercial, ve a Natalia Gómez en «Contactado» con su conversación esperando a un
asesor, le contesta por WhatsApp desde la ficha y, cuando le cotiza, la pasa a «Cotizado». Mercadeo
abre una campaña, ve que le llega a 4 de 5 familias y cómo le llega el mensaje, y la programa.

FIRST VIEWPORT: 1440×900: pestañas; listado de 420 px con las vistas Abiertos, Afiliados y Perdidos
con su recuento, el buscador y los interesados agrupados por etapa; la ficha a la derecha con la línea
de etapas, sus datos y la conversación. 390×844: el listado o la ficha, no los dos, con volver.

FORM: listado con ficha heredado de Familias, Rutas, Clínica y Servicios; seed: none (pinned) — el
usuario eligió «Listado con ficha» para Comercial («a la izquierda, los interesados con vistas por etapa
y su recuento… a la derecha, el interesado abierto con su línea de etapas… su conversación de WhatsApp
y una sola acción verde») y «Listado con ficha y repartir» para Campañas («a la derecha, la abierta con
su plantilla, su audiencia, la programación, los resultados y una sola acción verde… CampanasPage.tsx
se reparte en un fichero por pestaña»), el 2026-11-14.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-14)

- **Comercial y Campañas en listado con ficha** y **CampanasPage.tsx repartido** (decidido con el usuario).
- **La API dice la etapa siguiente** de cada interesado (`siguiente_etapa`), los recuentos por etapa y
  la conversación de cada uno; la bandeja de conversaciones nombra al interesado.
- **Si alguien espera a un asesor, contestarle es el verde** de la ficha; si no, pasar a la etapa
  siguiente. «En afiliación» no avanza a mano: la afiliación lo pasa a «Afiliado».
- **`datos_demo` siembra una conversación** de WhatsApp que pide un asesor (Natalia Gómez).

## Pendiente

- Lo que quede, en la hoja de ruta («Lo que quedó de Comercial y campañas»).
