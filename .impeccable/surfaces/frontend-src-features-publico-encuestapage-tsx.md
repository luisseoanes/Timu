---
version: 1
slug: "frontend-src-features-publico-encuestapage-tsx"
primary_target: "frontend/src/features/publico/EncuestaPage.tsx"
related_targets: ["frontend/src/features/publico/VerificarCarnetPage.tsx","frontend/src/components/AccesoLayout.tsx"]
---

# Páginas públicas · Encuesta y verificación del carnet (R3-PUB-03)

## Alcance y modo

Dos páginas sin sesión. La encuesta (`/encuesta/:token`): la familia llega desde un enlace de
WhatsApp tras una atención y la califica (satisfacción, 6.20) o dice cómo sigue su peludo
(seguimiento, 6.21). La verificación del carnet (`/verificar/:codigo`): un tercero (clínica,
guardería, aerolínea) confirma con el código impreso al pie del PDF que el carnet preventivo es
auténtico y ve lo que decía (6.15, F2-PRE-06). Superficie dentro de la línea visual de `DESIGN.md`,
sin sorteo. Modo: Operate (la encuesta tiene algo de persuasivo: que la familia responda).
Construcción: en código.

## Público, tarea y restricciones

- Encuesta: una familia, casi siempre en el celular, que abre el enlace del mensaje de WhatsApp.
  Tarea: elegir una calificación (o cómo sigue la mascota), contar algo si quiere y enviar; saber
  qué pasa después. Con una duda o una novedad, saber que el equipo la contacta y qué hacer si es
  urgente.
- Carnet: alguien que no es de TIMU ni de la familia, en el celular o en un computador, que tecleó
  la dirección impresa. Tarea: saber de un vistazo si el carnet es auténtico, de qué mascota es y
  qué se le aplicó, con producto, lote, fecha y la próxima dosis, y lo que estaba pendiente.
- Restricciones: el carnet no muestra datos de la familia. La verificación dice lo mismo que el
  PDF el día que se emitió (lo aplicado por tipo con su próxima fecha y lo pendiente): lo aplicado
  después no aparece. Roles de color del manual, una sola acción verde por vista, controles de 44 px
  en táctil, WCAG 2.2 AA. La API dice el tipo de encuesta, si dejó tarea (`te_contactamos`), las
  secciones del carnet con su dosis en palabras y lo pendiente; el panel no copia el umbral de
  alerta ni agrupa por tipo.

## Direction contract

THESIS: La encuesta es otra puerta de entrada de la familia, como la activación: hereda el acceso
(panel marino con la frase que le habla a quien llega y la línea de marca, y el formulario en la
columna de 400 px). La verificación es un documento para un tercero: una columna sobre el lienzo,
el veredicto arriba («Carnet auténtico», la mascota, el código y la emisión) y debajo lo que decía
el carnet impreso, sección por sección, con qué certifica al pie. Rechaza la tarjeta pública con
sombra, la tabla que se desplaza en el celular, el «Carnet no encontrado» del servidor repetido en
pantalla, la escala del 1 al 5 para preguntar cómo sigue una mascota y el «¡Gracias!» que no dice
qué pasa después.

OWN-WORLD: El de `DESIGN.md`. El acceso (`AccesoLayout`, ahora en `src/components/`) para la
encuesta; para el carnet, el lienzo con el logo compacto, el distintivo con icono y palabra, la
ficha de datos en pares etiqueta/valor y la tabla apilable.

STORY: La familia de Nina recibe por WhatsApp el enlace de la encuesta de la consulta en casa del
martes. Lo abre en el celular: «¿Cómo te fue en la atención de Nina?», elige 2 y envía; la
pantalla le dice que alguien del equipo TIMU la contacta hoy. Días después llega el seguimiento:
«¿Cómo sigue Nina después de la atención?»; elige «Algo no va bien», ve que si es urgente escriba
ya por el chat y cuenta que no quiere comer. En otra ciudad, una guardería teclea la dirección del
carnet de Coco: «Carnet auténtico, emitido por TIMU», la polivalente aplicada el 15 de octubre con
su lote y la próxima en 2027, y lo pendiente al emitirse.

FIRST VIEWPORT: Encuesta, 1440×900: el panel marino con «Tu opinión nos ayuda a cuidar mejor a
Nina.» y la línea; a la derecha el título en GeosansLight, la atención y su fecha, la escala de
cinco y el comentario, con «Enviar respuesta» en verde (deshabilitado hasta elegir). 390×844: la
franja marina con el logo compacto y la línea en miniatura, y el formulario entero a la vista.
Carnet, 1440×900: el logo compacto, el sello «Carnet auténtico», «Carnet preventivo de Coco», la
especie y la raza, el código y la emisión, y la sección de Vacunación. 390×844: lo mismo apilado,
cada aplicación como un bloque de pares.

FORM: la encuesta, `AccesoLayout` heredado de `R3-PUB-01`; el carnet, una columna de 760 px sobre el
lienzo con el veredicto, las tres secciones del PDF y «Pendiente al emitirse» en tablas apilables.
seed: none (pinned). El usuario eligió el 2026-11-16, para la encuesta, «Hereda el acceso»
(«AccesoLayout: panel marino con la frase y la línea de marca desde 900 px, y la franja marina en
el celular; el formulario en la columna de 400 px … Al responder, “¡Gracias!” dice qué pasa
después»), y para el carnet, «Veredicto y aplicaciones» («Una columna de unos 720 px sobre el
lienzo, con el logo compacto. Arriba, el veredicto que busca quien verifica … Debajo, las
aplicaciones en tabla apilable con cada dato en palabras … Al pie, qué certifica y la huella»).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-16)

- **La encuesta hereda el acceso; el carnet, veredicto y aplicaciones** (decidido con el usuario).
- **El seguimiento (6.21) tiene su pregunta propia** (decidido con el usuario): «Sigue bien»,
  «Tenemos una duda» o «Algo no va bien», guardado en `como_sigue` (migración `0050`) y sin
  mezclarse con el promedio de satisfacción. Una duda o una novedad dejan tarea de servicio al
  cliente con su propio título; un número por WhatsApp solo responde la satisfacción.
- **La verificación muestra las próximas fechas** (decidido con el usuario, 6.15): el carnet guarda
  al emitirse lo pendiente y la API devuelve las secciones del PDF con la próxima fecha de cada
  aplicación. Un carnet emitido antes lo dice en vez de inventarlo.

## Pendiente

- Lo que quede, en las notas de cierre del rediseño (`docs/rediseno/notas-de-cierre.md`).
