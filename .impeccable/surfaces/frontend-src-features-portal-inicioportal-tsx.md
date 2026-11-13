---
version: 1
slug: "frontend-src-features-portal-inicioportal-tsx"
primary_target: "frontend/src/features/portal/InicioPortal.tsx"
related_targets: ["frontend/src/features/portal/PortalLayout.tsx","frontend/src/features/portal/PeludosPortal.tsx","frontend/src/features/portal/LineaPortal.tsx","frontend/src/features/portal/CitasPortal.tsx","frontend/src/features/portal/PagosPortal.tsx","frontend/src/features/portal/DatosPortal.tsx"]
---

# Portal de familias · Inicio, cada peludo y navegación (R3-POR-01)

## Alcance y modo

Estructura del portal (`PortalLayout`), el inicio (`InicioPortal`) y la ficha de cada peludo
(`PeludosPortal`). Mascotas, citas, pagos, datos y «Agregar un peludo» heredan estos patrones
(R3-POR-02 incluido, en `CitasPortal`, `PagosPortal` y `DatosPortal`), sin sorteo propio.
`PortalPages.tsx`, el fichero original de la superficie, se repartió por pantalla en R3-POR-02. Modo: Operate. Construcción en código: el boceto elegido es
`docs/rediseno/boceto-portal-hoy-estas-aqui.html` (copia versionada del de la página de
decisión).

## Público, tarea y restricciones

- Familias afiliadas, desde el celular y a menudo desde un enlace de WhatsApp; en escritorio,
  lo mismo en más ancho.
- Tarea: saber en qué está su plan y sus peludos y hacer lo que toca (pagar, agendar, ver el
  carnet) sin llamar.
- Restricciones: el sistema de `DESIGN.md` (la línea de metro) sin cambios; voz cercana y
  tuteo, condiciones de frente, nada de «ilimitado»; con el plan congelado o en mora no se
  agenda (la elegibilidad del backend), así que la interfaz lo dice antes de ofrecerlo.

## Direction contract

THESIS: El inicio es la línea de la familia abierta en «Hoy», como el «usted está aquí» de un
plano de metro: encima lo vencido, debajo lo que viene. Rechaza el tablero de accesos en
mosaico y tarjetas sueltas, donde el estado del plan es una pastilla sin explicar.

OWN-WORLD: El de `DESIGN.md`: barra marina, lienzo y superficies blancas planas, línea de 8 px
del color del plan, estaciones de 24 px (hecha llena, vencida roja con icono, próxima con
halo, futura en contorno), marca de «Hoy» marina, etiquetas de 12 px en mayúsculas, Inter y
GeosansLight en el saludo.

STORY: La familia lee en una frase por qué su plan está como está y qué hacer; ve lo vencido
agrupado (las cuotas en una estación, los preventivos en otra, con cuántos por peludo) y lo
próximo, y actúa desde la estación. Cada peludo abre su propia línea con su carnet y su
historia.

FIRST VIEWPORT: 390×844. Barra marina con el logo y la cuenta. «Hola, Ana» a 34 px; el plan
(cuadrado del color y nombre) con su estado y la frase que lo explica; los peludos como
accesos con lo que tienen vencido. Debajo, la línea vertical en un panel blanco: estaciones
vencidas con su acción (pagar lo pendiente, la única verde), la marca «Hoy · jue 12 nov» y la
próxima. Barra inferior de cinco destinos. En escritorio, la línea en una columna de lectura y
el plan y los peludos al lado. Interacción propia: la línea abre en «Hoy» y lo vencido se
agrupa, así que «Hoy» siempre está en la primera pantalla.

FORM: «Hoy, estás aquí»; candidato 3 de 7 de la lista ordenada (repartido por la tirada; la
principal era el 7, «La conversación»); seed: 333dd5f645937a6a.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-12)

- **Sorteo de superficie en modo Operate**, con alcance inicio, ficha del peludo y navegación;
  el resto del portal hereda. Decidido con el usuario.
- **La línea llega al portal por un endpoint propio** (`GET /portal/linea`), con la misma forma
  que la del panel y el alcance de la familia. Decidido con el usuario.
