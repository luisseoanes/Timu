---
version: 1
slug: "frontend-src-features-aliadas-miclinicapage-tsx"
primary_target: "frontend/src/features/aliadas/MiClinicaPage.tsx"
related_targets: ["frontend/src/features/aliadas/ValidarRemision.tsx","frontend/src/features/aliadas/Atendidas.tsx"]
---

# Clínica aliada · Mi clínica (R3-ALI-01)

## Alcance y modo

El espacio de la clínica aliada (`/aliada`): validar el código de una remisión que trae la familia,
reportar la atención y ver lo que la clínica ya atendió en el mes con lo que cubrió TIMU. Superficie
dentro de la línea visual de `DESIGN.md`, sin sorteo: hereda la estructura del portal (barra marina
y cuenta) y los patrones del panel (ficha de datos, distintivo de estado, lista con hilo, cifras en
celdas). Modo: Operate. Construcción: en código.

## Público, tarea y restricciones

- Recepción o el veterinario de una clínica aliada, en su mostrador o consultorio, casi siempre en
  un computador y a veces en el celular o una tableta. Usa la plataforma pocas veces al día y no es
  de TIMU: necesita saber de un vistazo si la remisión sirve, qué cubre TIMU y cuánto le cobra a la
  familia.
- Tarea: escribir el código, ver si sirve (y por qué no, si no), reportar la fecha, el valor y un
  resumen clínico, y comprobar después lo que ya reportó en el mes.
- Restricciones: F2-ALI-03, no ver de la familia más de lo necesario (titular, últimos dígitos del
  documento y la mascota; nada de contacto, dirección, cartera ni historia). El código es la prueba
  de que la familia se presentó: la clínica no ve las remisiones por usar. Roles de color del
  manual, una sola acción verde por vista, controles de 44 px en táctil, WCAG 2.2 AA, Radix para lo
  interactivo. El panel no copia reglas del backend: la API dice si la remisión sirve, entre qué
  fechas se puede atender, cuánto cubre TIMU de un valor y los totales del mes.

## Direction contract

THESIS: Un mostrador. A la izquierda, lo que se hace ahora: el código y, debajo, la remisión abierta
con su estado dicho en palabras, a quién se atiende, qué cubre TIMU y el reporte con lo que cubre y
lo que paga la familia antes de enviarlo. A la derecha, lo ya atendido en el mes, con lo que cubrió
TIMU, para cuadrar con la liquidación. Rechaza la tarjeta pública con sombra, los dos verdes, el
«no está vigente» sin decir por qué y la cifra de lo cubierto que solo aparece al terminar.

OWN-WORLD: El de `DESIGN.md`. Barra marina con el logo compacto y la cuenta; paneles blancos planos
sobre el lienzo; ficha de datos en pares etiqueta/valor; distintivo con icono y palabra; lo cubierto
en celdas blancas separadas por hilos (la franja del Inicio, «Cómo le fue» de Campañas); lista con
hilo para lo atendido (las remisiones por usar de la ficha de la clínica).

STORY: Recepción de la Clínica Veterinaria del Norte recibe a Jorge Ramírez con Rocky. Escribe el
código que trae en WhatsApp, ve «Por usar · vence el 16 dic», «Rocky · Canino», el titular con los
últimos dígitos de su documento para verificarlo, la radiografía de cadera y que TIMU cubre el 80 %
hasta $ 200.000. Escribe $ 180.000: TIMU cubre $ 144.000 y Jorge paga $ 36.000. Reporta, la remisión
pasa a «Atendida» y aparece arriba en lo atendido de noviembre, que suma lo que TIMU le debe.

FIRST VIEWPORT: 1440×900: la barra marina; a la izquierda «Validar una remisión» (h1) con el campo
del código y «Validar» en verde; a la derecha, «Atendidas» con el mes, sus cuatro totales
(atenciones, facturado, lo que cubrió TIMU y lo que pagaron las familias) y la lista. Con una remisión abierta que se puede usar, el verde pasa a «Reportar
atención» y «Validar» queda secundario. 390×844: lo mismo apilado, el código primero y lo atendido
debajo.

FORM: estructura del portal (`PortalLayout`) sin destinos; ficha de datos, distintivo, lista con
hilo y celdas de cifras heredados del panel. seed: none (pinned) — el usuario eligió «Mostrador con
historial» el 2026-11-16: «Estructura del portal (barra marina, logo compacto y cuenta, sin menú de
módulos porque hay un solo destino). En escritorio, dos columnas: a la izquierda validar y la
remisión abierta con su reporte; a la derecha, lo que la clínica ya atendió este mes y lo que cubrió
TIMU, para cuadrar con la liquidación. En el celular se apilan. Un solo verde: «Validar» sin
remisión abierta y «Reportar atención» con una que se puede usar.»

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-16)

- **Mostrador con historial** (decidido con el usuario).
- **La clínica no ve las remisiones por usar**, solo el código que trae la familia (decidido con el
  usuario): el código es la prueba de que la familia se presentó.
- **Lo que cubre TIMU y lo que paga la familia se ve antes de reportar**, y lo calcula la API con
  la misma función que usa al reportar (decidido con el usuario).
- **Lo atendido, por mes** (decidido con el usuario): abre en el mes en curso con un selector de los
  12 anteriores, y la API da la lista y sus totales: atenciones, valor facturado, lo que cubrió TIMU
  y lo que pagaron las familias (la opción elegida lo decía con esas cuatro cifras). Las cuatro van
  como filas de libro de cuentas; con el mes vacío, solo la frase.
- **La barra dice el nombre de la clínica** (decidido con el usuario): la aliada lee su propia fila
  (migración `0049`).

## Pendiente

- Lo que quede, en las notas de cierre del rediseño (`docs/rediseno/notas-de-cierre.md`).
