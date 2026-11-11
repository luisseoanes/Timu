---
version: 1
slug: "frontend-src-features-familias-familiaspage-tsx"
primary_target: "frontend/src/features/familias/FamiliasPage.tsx"
related_targets: ["frontend/src/features/familias/FamiliaDetallePage.tsx","frontend/src/layouts/AppLayout.tsx"]
---

# Panel del equipo · Familias (R2-PAN-01 a R2-PAN-03)

## Alcance y modo

Estructura del panel del equipo (navegación y cabecera, `AppLayout`) y Familias: listado, detalle
con sus pestañas y ventanas de alta. Primera superficie de la nueva línea visual: lo que se fije
aquí lo heredan el resto del panel, el portal y las páginas públicas. Modo: Operate.
Construcción: en código (no hay generación de imágenes); el boceto elegido es
`docs/rediseno/boceto-familias-linea-de-metro.html` (copia versionada del boceto elegido en la página de decisión).

## Público, tarea y restricciones

- Equipo TIMU: operaciones y comercial en escritorio; médicos en ruta desde el celular.
- Tarea: encontrar una familia, entender su situación (plan, cuota, mascotas, lo próximo que toca)
  y actuar sin cambiar de pantalla.
- Restricciones: roles de color del manual (docs/manual-de-marca.md, sección 10), Inter, marcador
  de texto en lugar del logo, WCAG 2.2 AA, controles estándar sobre Radix, responsive completo.

## Direction contract

THESIS: Cada familia es una línea de metro. Su plan se dibuja como una línea cuyas estaciones son
cuotas, preventivos y visitas: hechas, próxima o vencidas. Rechaza la ficha de pestañas con tablas
sueltas, donde el estado de una familia se reconstruye leyendo cinco pestañas.

OWN-WORLD: La señalética del Metro de Medellín en la paleta de TIMU. Barra superior marina con
los módulos y el activo subrayado en verde. Lienzo y superficies blancas planas, sin sombras ni
bordes de adorno. Línea de 8 px en el color del plan (gris sin plan). Estaciones circulares:
llena = hecha, anillo marino con halo = próxima, roja con icono = vencida, contorno = futura.
Inter con escala fija en rem, cifras tabulares, etiquetas de 12 px en mayúsculas espaciadas.

STORY: En el listado, cada fila lleva la línea en miniatura de su familia, y quien la recorre ve
de un vistazo quién tiene una estación vencida. Al abrirla entiende plan, cuota y lo próximo que
toca, y lo agenda o registra desde la misma estación.

FIRST VIEWPORT: 1440×900. Barra marina de 64 px con «TIMU» en texto, los módulos y el buscador a
la derecha. Debajo, un listado de 420 px (título y total, filtros, filas con nombre, plan,
mascotas y línea en miniatura) y el detalle sobre el lienzo: nombre a 34 px, plan y estado, la
acción principal verde ligada a la próxima estación, la línea de tres meses a todo el ancho, y
debajo mascotas y cartera. En el celular, listado y detalle se apilan y la línea pasa a vertical.
Interacción propia: enfocar una estación muestra su detalle; activar la próxima abre su acción.

FORM: diagrama de líneas de metro; candidato 1 de 7 de la lista ordenada (elegido por el usuario
como IMPECCABLE’S PICK frente al asignado, el 6); seed: 4d6d5b4435b41ead.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-10)

- **Las estaciones salen de un endpoint de la API**: una «línea» por familia que reúne cuotas,
  preventivos y servicios. El listado la pide en miniatura para cada fila sin tres llamadas por
  fila. Es trabajo de backend dentro de `R2-PAN-02`.
- **Navegación en el celular: barra inferior** con los cuatro módulos que más usa cada perfil y
  «Más» para el resto (los médicos: Rutas, Servicios, Clínica y Familias).
- **La línea del detalle muestra el año completo**, como un plano de metro: estaciones con
  espaciado esquemático (no proporcional al tiempo) y «hoy» marcado como «estás aquí». Siempre
  llevan etiqueta «hoy», la próxima estación y cualquier vencida, esté donde esté; las demás
  son puntos que muestran su detalle al enfocarlos o al pasar el cursor. Las estaciones hechas
  antiguas se pliegan en un tramo («8 hechas») que se despliega al activarlo, y los eventos del
  mismo día comparten estación. En el celular la línea es vertical, con el pasado plegado y la
  vista abierta en «hoy». Descartados: el scroll horizontal (con ratón no se descubre y es
  incómodo con teclado) y una ventana con «Anteriores» y «Siguientes» (escondía una cuota
  vencida fuera de la ventana). Decidido con el usuario.

## Decisiones tomadas (2026-11-11)

- **Atender un preventivo desde su estación se hace en `R2-PAN-08`**, no en `R2-PAN-02`. La STORY
  pide agendar o registrar desde la misma estación. Hoy una cuota pendiente abre el registro de
  pago y un servicio abre su ficha, pero un preventivo (vacuna, desparasitación) solo lleva a la
  pestaña de mascotas: agendarlo es una acción de `preventivos`, y traerla a Familias exige
  inyectarla sin que `familias` importe `preventivos`. Se hace cuando `R2-PAN-08` rediseñe esa
  acción. Hasta entonces la STORY se cumple a medias para los preventivos, a sabiendas, y
  `R2-PAN-08` no se cierra sin esto. Decidido con el usuario.
