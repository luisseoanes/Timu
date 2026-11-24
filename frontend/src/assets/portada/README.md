# Fotos de la portada pública (R3-PUB-04)

Del banco de marca que entregó TIMU (carpeta `marca`, recibida el 2026-10-08). Hay dos clases, y
no se tratan igual:

- **Fotos del equipo** (la médica con el bulldog, la recepción, el equipo junto al logo): fotos
  propias de TIMU, que confirmó el 2026-11-11 que son suyas. Son las del mosaico de la primera
  pantalla.
- **Fotos de las piezas impresas** (el parque y los gatitos): salen de
  los PDF de las piezas, el plegable y el carnet. Por su aspecto son de banco de imágenes (los
  gatitos, quizá generados), compradas o descargadas por quien diseñó las piezas. No muestran a TIMU:
  la portada no les pone pie ni les atribuye nada, y van en «Nosotros» como ilustración.

No se usan las imágenes del tema de WordPress de la web actual (`bg-featured-title.jpg`,
`fancy-image-cat.jpg`, `service-single-03.jpg`).

Permisos (resuelto el 2026-11-24, en `docs/pendientes-externos.md`): las personas de las fotos
del equipo dieron su permiso para aparecer en la web pública (Ley 1581: la imagen es un dato
personal), y TIMU tiene la licencia de las fotos de las piezas.

| Fichero | Origen | Qué muestra |
| --- | --- | --- |
| `medica-bulldog-{1600,800}.webp` | `WhatsApp-Image-2025-03-27-at-10.08.33-PM-2.jpeg` | La médica de TIMU con un bulldog en la clínica (del equipo) |
| `recepcion-{1600,800}.webp` | `Sin título.jpeg` | Una persona del equipo en la recepción (del equipo) |
| `frente-al-logo-{1600,800}.webp` | `WhatsApp-Image-2025-03-28-at-12.55.55-PM.jpeg` | Una persona del equipo señala el logo de la clínica (del equipo) |
| `gatitos-{1600,800}.webp` | `Piezas TIMU impresión.pdf …`, imagen 7 | Cuatro gatitos en la hierba (de banco o generada) |
| `parque-{1200,700}.webp` | `Piezas TIMU impresión.pdf …`, imagen 6 | Una mujer abraza a su perro en un parque (de banco) |

Cómo se prepararon: las imágenes de los PDF se sacaron con `pdfimages -png` (sin volver a
comprimir); todo se reduce y se exporta a WebP (calidad 0,78) con un lienzo de Chromium. Dos
anchos por foto para `srcset`: el grande para escritorio y el pequeño para el celular.
