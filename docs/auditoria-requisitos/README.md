# Auditoría de cumplimiento del documento de requerimientos

Empezada el 2026-11-24, decidida con el usuario. Contrasta **cada obligación** del [documento de
requerimientos](../documento-requerimientos-funcionales.md) con lo que hace la plataforma, para
partir de una versión que cumple antes de cerrar la deuda y las integraciones, y antes de que el
equipo de TIMU revise staging.

## La base: el documento, comprobado contra el PDF

El 2026-11-24 se comparó palabra a palabra el `.md` con el PDF original
(`~/Descargas/documento-requerimientos-funcionales.pdf`, 24 páginas, extraído con `pdftotext`):
las 3133 palabras coinciden en el mismo orden. La única diferencia son cuatro viñetas «○» de la
sublista de periodicidades de 6.2, que en el `.md` son viñetas de markdown. **El `.md` es una copia
fiel y se audita sobre él.**

## Método

1. **Primero se audita todo, después se arregla.** Durante la auditoría no se cambia código: se
   anota. Los arreglos se diseñan cuando el mapa está completo, en orden de dependencia, para no
   arreglar un requisito sin saber qué piden los otros de lo mismo.
2. **La unidad es la obligación atómica**: cada cosa que el documento pide, con un ID
   (`6.10-05`) y su texto. Un requisito tiene varias.
3. **Ningún «Cumple» sin evidencia**: el `fichero:línea` que lo hace y la prueba que lo afirma, o
   la comprobación contra el stack, con fecha. Sin prueba, como mucho «Parcial».
4. **Los agentes solo buscan evidencia** (en lectura); ningún veredicto suyo entra sin que se
   verifique en el código, y «Contradice» y «Parcial» se revisan con el usuario.
5. **Al arreglar, cada obligación queda atada a la prueba que lleva su ID**, y una guarda hará
   fallar el CI si una fila «Cumple» no apunta a una prueba que existe: así un arreglo posterior
   no afloja uno anterior sin que se vea.

### Tipo de cada obligación

| Tipo | Cuándo | Cómo se audita |
| --- | --- | --- |
| **Exige** | «deberá», «debe permitir», lo que el documento pide sin matiz | Tiene que cumplirse. |
| **Ejemplo** | Lo pone como ejemplo de lo que exige («por ejemplo», «como») | Se audita igual, porque es lo que TIMU va a probar, pero se puede cumplir con algo equivalente. |
| **Opcional** | «podrá contemplarse», «información potencial» | No cumplirlo no incumple; se anota qué hay. |
| **Propuesta** | Pide al proveedor que **indique** algo (6.19, Secciones 3 y 4) | Se responde con documentación; se audita que lo indicado sea verdad en el código. |

### Veredictos

| Veredicto | Significa |
| --- | --- |
| **Cumple** | Hace lo que pide, con `fichero:línea` y una prueba que lo afirma. |
| **Equivalente** | Lo cumple con otro nombre u otra forma (el estado `agendado` por «Programado»). Solo vale si el usuario aprobó la equivalencia y está escrita aquí; hasta entonces, **Por decidir**. |
| **Parcial** | Hace una parte, o lo hace sin prueba que lo afirme. |
| **Falta** | No existe. |
| **Contradice** | Está construido de una forma que va contra lo que pide. El más grave: no basta añadir, hay que cambiar. |
| **Decidido** | Se apartó del documento con el visto bueno del usuario (fecha y motivo). |
| **Externo** | Depende de TIMU o de un tercero ([pendientes externos](../pendientes-externos.md)). |
| **Por decidir** | Hace falta una decisión del usuario (o una pregunta a TIMU) para dar el veredicto. |
| **Sin auditar** | Aún no se revisó. |

## Orden de la auditoría

Por dependencia, no por número: lo que todo lo demás usa va primero.

| Bloque | Requisitos | Fichero | Estado |
| --- | --- | --- | --- |
| 1. Estados y ciclo de vida | 6.10, 6.23, 6.1, 6.12 | [seccion-6.md](seccion-6.md) | 6.10 y 6.23 auditados; 6.1 y 6.12, sin auditar |
| 2. Cartera, planes y renovación | 6.2, 6.3, 6.4 | [seccion-6.md](seccion-6.md) | Sin auditar |
| 3. Servicios y preventivos | 6.5, 6.6, 6.7, 6.8, 6.9, 6.13 | [seccion-6.md](seccion-6.md) | Sin auditar |
| 4. Lo clínico | 6.14, 6.15, 6.17 | [seccion-6.md](seccion-6.md) | Sin auditar |
| 5. Comunicación y seguimiento | 6.11, 6.16, 6.18, 6.19, 6.20, 6.21 | [seccion-6.md](seccion-6.md) | Sin auditar |
| 6. Clínicas aliadas | 6.22 | [seccion-6.md](seccion-6.md) | Sin auditar |
| 7. Transversales | 7, 8, 12, 13 | por extraer | Sin extraer |
| 8. Técnicas y externas | 9, 10, 11, 14, y 1 a 5 | por extraer | Sin extraer |
| Anexo | Lo que prometió la [propuesta](../propuesta-timu-puntos-15-19.md) (tabla B, sección E) | por extraer | Sin extraer |

## Recuento

| Sección | Obligaciones | Cumple | Equivalente | Parcial | Falta | Contradice | Decidido | Externo | Por decidir | Sin auditar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 267 | 6 | 0 | 4 | 3 | 2 | 0 | 0 | 4 | 248 |

## Preguntas para TIMU

Lo que el documento deja abierto y solo TIMU puede aclarar. Se juntan aquí para mandarlas por
tandas, sin esperar al final de la auditoría.

- **6.23-05.** El documento pide los estados «Cancelado» y «Retirado». ¿En qué se diferencian para
  TIMU? Por ejemplo: ¿«Cancelado» lo decide TIMU (por mora, por política) y «Retirado» es la familia
  que se va por decisión propia? ¿O «Retirado» es el integrante que sale de un plan grupal (6.3)?
