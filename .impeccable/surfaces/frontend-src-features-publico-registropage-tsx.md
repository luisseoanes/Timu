---
version: 1
slug: "frontend-src-features-publico-registropage-tsx"
primary_target: "frontend/src/features/publico/RegistroPage.tsx"
related_targets: ["frontend/src/features/publico/CompletarRegistroPage.tsx"]
---

# Páginas públicas · Registro en línea (R3-PUB-02)

## Alcance y modo

El registro en línea (`/afiliacion`): una familia que no está afiliada elige ciudad, dice quiénes
son sus peludos, elige un plan para cada uno y cómo pagar, paga en Wompi y después completa sus
datos (`/afiliacion/resultado`, `/afiliacion/completar`). Superficie dentro de la línea visual de
`DESIGN.md`. Modo: Persuade (la familia decide y paga). Construcción: en código (sin generación de
imágenes en este entorno).

## Público, tarea y restricciones

- Una familia de Medellín o Bogotá, casi siempre en el celular, a menudo llegando desde un enlace
  de WhatsApp o de la web de TIMU. Ve a su perro o gato como parte de la familia.
- Tiene que creer, para pagar (respuesta del usuario): **qué cubre, de frente**; **cuánto paga en
  total**; **que TIMU es real**; **que es rápido**.
- Intocable (respuesta del usuario): el orden pago → datos (6.12, sin redigitación); solo perros y
  gatos, con su confirmación; un plan por peludo con la tarifa por número de peludos.
- Restricciones: precios, coberturas, carencias, exclusiones y términos salen del catálogo de la
  API, nunca de la interfaz (PRODUCT.md, principio 5); los valores de TIMU son provisionales y se
  dicen como tales donde aplique ([pendientes externos](../../docs/pendientes-externos.md)). Sin
  testimonios, cifras ni fotos inventadas. Voz: «plan de salud prepagado», nunca «seguro» ni
  «ilimitado»; exclusiones y carencias de frente. Una sola acción verde por vista, 44 px en
  táctil, WCAG 2.2 AA.

## Direction contract

THESIS: La familia arma su manada. Una ficha por peludo (su nombre y su especie) y, dentro, los
tres planes como pastillas en su color; la elegida se abre con todo lo que cubre (cupos,
porcentajes, copago, carencia y exclusiones) y un «Comparar los tres» que despliega las mismas
filas alineadas para los tres planes. Abajo, fijo, el total de la familia, que se recalcula al
añadir un peludo («2 peludos · tarifa de 2»). Rechaza los planes como opciones de un `<select>`,
la tarjeta pública con sombra, la tabla de precios genérica de tres columnas y las condiciones en
letra pequeña al final.

OWN-WORLD: El de `DESIGN.md`: lienzo, paneles blancos planos con hilo, la franja marina con el
logo compacto arriba, GeosansLight en el título e Inter en el resto, el color de cada plan
(naranja, verde, azul con sus pares de texto) como pastilla y como filete de la ficha, cifras
tabulares, el verde de acción con texto marino.

STORY: Laura vive en Medellín, abre el enlace en el celular y escribe «Toby, perro»; en su ficha
toca Mi Amigo Fiel y ve una consulta en casa al mes, la clínica aliada al 40 %, la orientación 24/7,
la carencia y lo que excluye. Pulsa «Comparar los tres» y ve las filas lado a lado. Añade a Mishi,
gata, en Colita Feliz; el total pasa a «2 peludos · tarifa de 2 · $ 91.500 al mes». Elige pagar
trimestral, ve el ahorro, paga en Wompi y completa los datos de la familia.

FIRST VIEWPORT: 390×844: la franja marina con el logo compacto; «¿Quiénes se unen a la manada?»
(h1, GeosansLight) con la ciudad; la ficha del primer peludo con nombre y especie, las tres
pastillas de plan y la elegida abierta con su cobertura; «+ Otro peludo»; la barra fija abajo con
el total de la familia y el verde («Elegir cómo pagar»). 1440×900: la misma columna de fichas a la
izquierda y, a la derecha, el resumen de la familia (peludos, planes, total y forma de pago) fijo
mientras se baja, con el verde.

FORM: «Cada peludo, su plan», tercera de siete en la lista ordenada; el sorteo la repartió como
segunda carta. El usuario la eligió el 2026-11-17 con un añadido: «el comparador dentro de cada
ficha» (lo tomado de «Los planes, cara a cara», la carta que sacó el sorteo). seed:08d1ca73cda4d57b

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-17)

- **Sorteo de la skill** para la composición, como pide el criterio de la unidad (decidido con el
  usuario).
- **Campos nuevos en el catálogo de planes** (carencia, exclusiones y enlace de términos) con
  texto provisional de TIMU y anotados como pendientes hasta que TIMU dé los oficiales (decidido
  con el usuario). Las exclusiones provisionales son la nota legal del manual de marca; la
  carencia, la misma que rige al agregar un peludo («sin carencia»); sin enlace de términos
  mientras no exista el documento.
- **Cada beneficio dicho de frente**: la API pública da su nombre, su cupo y periodo, su
  porcentaje de cobertura y su copago, en palabras.

## Pendiente

- Lo que quede, en las notas de cierre del rediseño (`docs/rediseno/notas-de-cierre.md`).
