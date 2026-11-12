---
version: 1
slug: "frontend-src-features-rutas-rutaspage-tsx"
primary_target: "frontend/src/features/rutas/RutasPage.tsx"
related_targets: []
---

# Panel del equipo · Rutas (R2-PAN-06)

## Alcance y modo

La ruta del día: el médico en la calle con el celular (primero) y operaciones planeando y
siguiendo las rutas desde el escritorio. Superficie dentro de la línea visual de Familias
(`DESIGN.md`); el sorteo fue de composición, no de identidad. Modo: Operate. Construcción: en
código. El boceto elegido es `docs/rediseno/boceto-rutas-linea-del-dia.html` (copia versionada
del de la página de decisión).

## Público, tarea y restricciones

- Médico en ruta: de pie, en casa ajena, con una mano. Necesita saber cuál sigue, a qué
  dirección va, a quién atiende, y avanzar la parada sin buscarla.
- Operaciones y administración: planean las rutas del día con el optimizador, ven el avance de
  cada responsable, agregan lo que quedó por rutear y cancelan una ruta sin arrancar.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px
  en táctil, WCAG 2.2 AA, Radix para lo interactivo, sin mapa embebido.

## Direction contract

THESIS: La ruta del día es una línea vertical de metro. Cada parada es una estación: las hechas
se pliegan arriba y la próxima se abre en su sitio con a dónde ir, a quién se atiende y la
acción que toca. Rechaza el tablero de tarjetas con un anillo de cumplimiento, donde el médico
busca su parada entre las de todos y la parada no dice ni la dirección.

OWN-WORLD: El de `DESIGN.md`. Línea de 8 px marina (una ruta no es un plan: no toma color de
plan), recorrida en marino y por recorrer en gris. Estaciones de 24 px: llena = hecha, anillo
marino con halo verde = la próxima, contorno gris = pendiente, omitida aparte con su motivo.
Dirección en Inter 600 de 24 px (es casi toda cifras y se lee a pleno sol), horas tabulares,
etiquetas de 12 px. Superficies blancas planas sobre el lienzo.

STORY: El médico abre Rutas y ve su ruta de hoy: cuántas lleva, cuál sigue y a dónde va. Abre
la navegación, avisa que va en camino, llega, termina la visita, y la línea avanza. Operaciones
ve cada ruta del día con su línea en miniatura, planea y ajusta.

FIRST VIEWPORT: 390×844. Barra marina de 64 px. Cabecera con «Rutas», el avance («2 de 6
paradas · 18,4 km») y el selector de día. Panel blanco con la línea: la pastilla «2 hechas», la
próxima estación abierta (hora y franja, estado, dirección a 24 px, barrio, familia, mascota,
servicio, y su fila de acciones: la de estado en verde, «Cómo llegar» y llamar) y debajo las
siguientes con hora, familia, mascota, servicio y dirección. Barra inferior. A 1440: listado de
rutas del día (420 px), cada una con su línea en miniatura, y la ruta abierta a la derecha.
Interacción propia: la estación próxima lleva la acción de estado y la línea avanza al
cumplirla; activar otra estación la abre en su sitio.

FORM: línea vertical del día; candidato 1 de 7 de la lista ordenada (repartido por el sorteo
junto al 6, que lo encabezaba, y al 5; elegido por el usuario); seed:1c7dba19a64a22da.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-12)

- **Cada parada trae sus datos desde la API**: familia, mascota, dirección, teléfono, servicio y
  franja acordada, en la misma respuesta de `GET /rutas`. Antes la parada solo decía el tipo de
  servicio y la hora. Decidido con el usuario.
- **Sin mapa embebido**: cada parada lleva «Cómo llegar», que abre la navegación del celular con
  sus coordenadas. El mapa que nombra el requisito 6.7 queda como deuda escrita en la hoja de
  ruta y en pendientes externos. Decidido con el usuario.
- **El médico abre en su ruta de hoy**; operaciones y administración ven todas las del día. La
  ciudad deja de estar escrita a mano. Decidido con el usuario.
- **El marcador de plan no va en la parada.** El boceto lo dibuja junto a la familia, pero el
  plan es de cada mascota y traerlo exige cruzar `rutas` con el contrato. La familia enlaza a su
  ficha, donde está el plan.
- **La dirección va en Inter 600, no en GeosansLight.** Es casi toda cifras («Cra 43A # 7
  sur-170») y el médico la lee a pleno sol; `DESIGN.md` ya deja las cifras en Inter.
- **La acción de estado es verde solo para quien hace la ruta.** Quien coordina también puede
  avanzar una parada (la API se lo permite y le sirve para cerrar el día si alguien olvidó
  marcar), pero como botón secundario: en su vista la acción principal es planear.
- **Una parada en sitio no ofrece terminar mientras falten pasos obligatorios del servicio**: la
  API rechaza cerrarla. La acción verde pasa a «Registrar la atención», que lleva a la ficha del
  servicio, y dice qué falta. Registrar los pasos desde la propia parada queda para cuando se
  rediseñe el detalle del servicio (`R2-PAN-05`).
- **Llegar sin haber avisado** («Ya llegué», en el menú) existe para quien ya está en la puerta:
  «Voy en camino» le escribe a la familia, y decírselo allí sobra.

## Sorteo (2026-11-12)

Sobre la mesa: «Paso a paso» (una parada por pantalla, la línea como paginador), «La línea del
día» y «El plano» (las paradas dibujadas donde quedan, con hoja inferior). Los bocetos
descartados quedaron en `.impeccable/mocks/decision/`, sin versionar.
