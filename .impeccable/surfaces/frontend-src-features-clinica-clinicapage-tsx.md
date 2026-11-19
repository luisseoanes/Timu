---
version: 1
slug: "frontend-src-features-clinica-clinicapage-tsx"
primary_target: "frontend/src/features/clinica/ClinicaPage.tsx"
related_targets: ["frontend/src/features/clinica/HistoriaMascotaPage.tsx","frontend/src/features/clinica/EntradaPage.tsx"]
---

# Panel del equipo · Clínica (R2-PAN-07)

## Alcance y modo

La clínica del panel: la historia de cada mascota y la consulta, que el médico registra en casa
de la familia desde el celular, más la cola de orientación virtual, las respuestas aprobadas y
las plantillas. Superficie dentro de la línea visual del panel (`DESIGN.md`); el sorteo fue de
composición. Modo: Operate. Construcción: en código. Boceto elegido:
`docs/rediseno/boceto-clinica-pasos-guiados.html`.

## Público, tarea y restricciones

- Médico en la visita: de pie, con la mascota delante y el celular en una mano. Registra la
  consulta (motivo, anamnesis, examen físico, diagnóstico, tratamiento) y la firma; con eso la
  visita de la ruta se puede terminar.
- Médico en consultorio y administración: abren cualquier historia, corrigen, adjuntan y emiten
  fórmulas; atienden la cola de orientación virtual.
- Restricciones: roles de color del manual, una sola acción verde por vista, 44 px en táctil,
  WCAG 2.2 AA, Radix para lo interactivo. La consulta firmada no se edita: se corrige.

## Direction contract

THESIS: La consulta es una línea de cinco estaciones (motivo, anamnesis, examen físico,
diagnóstico, tratamiento) que se recorre una por pantalla, con la estación en la que vas
marcada y cualquiera a un toque. Rechaza el formulario de seis áreas de texto en una ventana,
donde en el celular el médico escribe a ciegas y no sabe qué le falta.

OWN-WORLD: El de `DESIGN.md`. La guía es la línea de metro en horizontal: 8 px, recorrida en
marino y por recorrer en gris, estaciones de 24 px (hecha llena, actual con anillo marino y halo
verde, pendiente en contorno) con su nombre debajo en 12 px. El apartado actual lleva su título
en GeosansLight de 24 px y un campo grande; debajo, lo anotado en la última consulta como
referencia. Superficies blancas planas sobre el lienzo.

STORY: El médico abre la consulta de la mascota que atiende, escribe un apartado por pantalla
con lo de la última vez a la vista, salta a cualquier estación si quiere, y firma en la última.
La consulta firmada registra los pasos del servicio y la visita se puede terminar en Rutas.

FIRST VIEWPORT: 390×844. Barra marina de 64 px. Una línea con la mascota y su familia, y especie
y peso a la derecha. Panel blanco con la guía de cinco estaciones. Panel blanco con el apartado
actual: título a 24 px, ayuda de 13 px, el campo y, bajo un hilo, «En la última consulta» con
fecha y lo anotado. Abajo, al pulgar, «Anterior» (secundario) y «Siguiente: <apartado>» (verde);
en la última estación, «Firmar consulta». Barra inferior. A 1440: la historia a la izquierda y la
consulta a la derecha con la misma guía. Interacción propia: la guía es navegable (cada estación
es un botón con su estado), guarda el borrador al avanzar y dice qué falta antes de firmar.

FORM: pasos guiados por la línea de la consulta; candidato 6 de 7 de la lista ordenada (repartido
por el sorteo junto al 7, que lo encabezaba, y al 4; elegido por el usuario); seed:6810b776658f0cd2.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-12)

- **La consulta es el registro de la visita.** El médico no llena además los pasos del servicio:
  al firmar una consulta enlazada a un servicio en atención, se registran los pasos que falten
  con su contenido (valoración con el examen físico y el diagnóstico; plan con el tratamiento).
  `clinica` pasa a depender de `servicios`, sin ciclo. Decidido con el usuario.
- **El médico abre Clínica en su trabajo pendiente**: las mascotas de su ruta de hoy y sus
  consultas en borrador; debajo, el buscador. Administración y operaciones, el buscador.
  Decidido con el usuario.
- **La unidad abarca todo Clínica**: la cola de orientación virtual, las respuestas y las
  plantillas pasan a la línea siguiendo los patrones construidos, sin sorteo. Decidido con el
  usuario.
- **«Registrar la atención» en Rutas lleva a la consulta guiada** de esa mascota y ese servicio.

- **El nombre corto de la quinta estación es «Plan»**: «Tratamiento» no cabe junto a
  «Diagnóstico» a 390 px. El título del apartado sigue siendo «Tratamiento», y el botón nombra el
  apartado siguiente por su título completo («Siguiente: examen físico»).
- **La consulta nace al dejar el motivo**, que la historia exige; hasta entonces no se puede
  saltar a otro apartado. Una consulta nueva pasa a su propia dirección al nacer.
- **En el celular la consulta dice a quién se atiende** (mascota, familia, especie y peso),
  porque la historia de la izquierda no está. Pedido por el revisor final.
- **El halo de la estación actual pasa a verde hondo** en las tres líneas (Familias, Rutas y
  Clínica): el verde tenue no se veía sobre blanco. Pedido por el revisor final.

## Sorteo (2026-11-12)

Sobre la mesa: «Bitácora» (notas con hora que se ordenan al firmar), «Pasos guiados» y «Listado
con ficha». Los bocetos descartados quedaron en `.impeccable/mocks/decision/`, sin versionar.

## Plantillas de consulta editables (DEU-15, 2026-11-18)

Sin sorteo (`seed: none (pinned)`): hereda el listado con ficha de Historia clínica y de
Administración → Planes. Palabras del usuario, que eligió la opción recomendada en las dos
preguntas: «Listado con ficha (Recomendada)» y «La API lo saca del nombre (Recomendada)».

- **Listado con ficha** en la pestaña «Plantillas de consulta», con la abierta en la URL
  (`?plantilla=<codigo>`; al recargar, la página abre en esa pestaña). El listado dice en palabras
  qué apartados prellena cada una y deja las inactivas al final con su insignia «Inactiva», como
  Planes, Reglas y Clínicas aliadas (sin el separador «Desactivadas» del boceto ASCII: el revisor
  final lo dio por adaptación aceptable). El título lleva el total, con las inactivas.
- **La página controla la pestaña**: una plantilla que aparece en la URL lleva a «Plantillas de
  consulta», y «Volver» (cerrar la ficha) se queda en ella.
- **La ficha lee la plantilla por apartado**, en el orden de la consulta y con la misma lectura de
  la consulta firmada (`consulta-lectura`), y dice lo que deja en blanco. «Editar plantilla» es el
  verde; «Desactivar plantilla» y «Activar plantilla», en el menú de tres puntos (es reversible),
  con la nota de qué deja de pasar al estar inactiva.
- **Nada se borra** (regla del proyecto); la bitácora guarda cada versión. La consulta copia los
  textos de la plantilla al crearse: editarla o desactivarla no cambia lo ya registrado.
- **El código lo saca la API del nombre** y no se enseña: la ventana pide el nombre y el texto de
  cada apartado, igual al crear que al editar.
