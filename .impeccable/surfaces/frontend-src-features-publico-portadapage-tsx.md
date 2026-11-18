---
version: 1
slug: "frontend-src-features-publico-portadapage-tsx"
primary_target: "frontend/src/features/publico/PortadaPage.tsx"
related_targets: []
---

# Portada pública de timu.com.co (R3-PUB-04)

## Alcance y modo

La raíz de `timu.com.co` (`/`): el punto de acceso a todo (afiliarse, portal de familias, equipo y
clínicas aliadas) y toda la información que hoy expone la web de TIMU: planes con su detalle,
aliadas, nosotros y contacto. Modo: Persuade. Construcción: en código (sin generación de imágenes).
Mundo: el de `DESIGN.md` («La línea de metro»), sin cambiar paleta, tipografía ni logo.

## Público, tarea y restricciones

- Familias con perro o gato, sobre todo desde el celular y a menudo desde un enlace de WhatsApp o
  de redes; también el equipo, las familias afiliadas y las clínicas aliadas que entran a su espacio.
- Restricciones: roles de color del manual, una sola acción verde llena por vista, WCAG 2.2 AA,
  responsive sin desborde (375, 768, 900 y 1280 en el barrido), voz del manual (sin «seguro» ni
  «ilimitado»), nada de contenido inventado (testimonios, cifras de afiliados, premios).
- Todo lo que dice de un plan sale del catálogo (Administración → Planes) y las aliadas, de
  Administración → Aliadas.

## Direction contract

THESIS: La portada abre con la gente y los peludos reales de TIMU, en un reportaje de fotos con pie,
y deja la oferta a un toque: la familia arma su plan sin salir de la primera pantalla. Rechaza el
héroe genérico de foto de banco con un titular encima y una fila de tarjetas iguales, las fotos de
plantilla y los precios o coberturas escritos a mano.

OWN-WORLD: El de `DESIGN.md`: barra marina con el logo en blanco, lienzo cálido, mosaico de fotos
reales con esquina de panel y pie de foto en pastilla marina, panel marino con el título en
GeosansLight, los planes como pastillas en su color y «Arma tu plan» (ciudad, perros, gatos y el
precio que da la API) con el único verde lleno.

STORY: Una familia llega desde WhatsApp, ve a la médica de TIMU con un bulldog y a su equipo,
entiende en una frase que es un plan de salud prepagado para perros y gatos, dice cuántos peludos
tiene y ve cuánto paga; abre el plan para leer lo que cubre de frente y se afilia, o escribe por
WhatsApp. Quien ya es familia, equipo o aliada entra a su espacio desde «Ingresar».

FIRST VIEWPORT: 1440×900: barra marina de 64 px (logo, Planes, Aliadas, Nosotros, Contacto,
«Ingresar» y «Afiliar a mi peludo»); dos tercios de mosaico (la médica con el bulldog en grande a
la izquierda, la recepción y la consulta en el parque a la derecha, cada una con su pie) y un
tercio de panel marino con la etiqueta, el `h1` «Tu peludito, bien cuidado.», la frase, los tres
planes en su color con su precio y «Arma tu plan». 390×844: barra, una foto ancha con su pie y el
panel debajo con el título y «Arma tu plan» a la vista.

FORM: «Álbum de la manada», posición 7 de la lista propia ordenada; seed:e497aa8da47f29f1. La
sección de aliadas es «La red TIMU» (posición 5, el reparto que encabezó el sorteo): el plano de la
red como una línea de metro con sus estaciones, elegida por el usuario para esa sección.
Bocetos: `docs/rediseno/boceto-portada-album.html` y `docs/rediseno/boceto-portada-red-aliadas.html`.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-17)

- **El usuario eligió «Álbum de la manada» para la primera pantalla y «La red TIMU» para la
  sección de aliadas** («elijo el álbum y la red va en aliadas»), con la recomendación de Claude: el
  álbum da confianza en el celular, y el plano, como sección, no promete «todo el valle» en el
  titular y puede crecer a una línea por ciudad.
- **Todas las características de un plan se editan en Administración** y la portada muestra lo que
  diga el catálogo, también lo que hoy no guarda (topes por episodio, carencias por beneficio,
  servicio fúnebre, especialistas, beneficios de terceros).
- **Las aliadas salen de Administración → Aliadas**: si se muestran en la portada, su tipo, su
  horario y su logo.
- **El formulario de contacto crea un interesado** en Comercial con origen «web» y autorización de
  datos; sin boletín.
- **La portada va en `/` y el panel pasa a `/panel`**; las direcciones viejas de la web llevan a su
  sitio nuevo.
- **El catálogo se amplía así** (decidido con el usuario): el beneficio de un plan gana tope por
  episodio, carencia en días, detalle y orden; el plan gana una lista de beneficios adicionales
  (nombre, lo que cubre, detalle, carencia y si lo presta un tercero).
- **Portada con secciones y una página por plan** (`/planes/<plan>`), con las direcciones viejas
  llevando a su ancla o a su plan.
- **Lo institucional y de contacto se edita en Administración → «Datos de TIMU»**: misión,
  visión, valores, sede, horarios, teléfonos, correo, redes, NIT y el WhatsApp de contacto.
- **En Administración** (decidido con el usuario): los beneficios adicionales de un plan, en un
  bloque propio de su ficha con su ventana «Editar adicionales»; «Datos de TIMU», una pestaña con
  ficha de lectura y ventana para editar; lo que dice de una aliada la portada, en un bloque
  «En la portada» de su ficha con su ventana, sin mezclarlo con sus datos internos.
- **Tras la primera revisión final** (decidido con el usuario el 2026-11-18): **sin etiquetas en
  mayúsculas encima de los títulos**, tampoco la de la primera pantalla del boceto (regla de la
  etiqueta que nombra, DESIGN.md): lo que decían pasa al título o a la frase. **La cabecera de cada
  plan dibuja el plan como su línea** en el color del plan, una estación por servicio, en vez del
  recorte de banco. **La línea de la red es verde**, como en el boceto, con la estación de la
  clínica de TIMU en marino con halo.
- **Material**: las fotos reales de TIMU (equipo, recortes y fotos de los PDF de piezas, plegable y
  carnet) y, del `.ai`, las variantes del logo con animales y los patrones de siluetas en vector. No
  se usan las imágenes del tema de WordPress de la web actual.
