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
6. **Lo que se sospecha grave se reproduce**, no se da por bueno leyendo el código. La prueba
   temporal se escribe en el scratchpad, se copia a `backend/tests/` solo para correrla
   (`pytest tests/<fichero> -s --no-cov`; sin `db-test` arriba no corre) y se borra en el mismo
   comando: no queda en el repositorio. La fila dice que se reprodujo, contra qué y con qué fecha.
   En la fase de arreglos, esa reproducción es la prueba que falla sin el arreglo.
7. **Cómo se trabaja con el usuario** (decidido el 2026-11-24): se audita sin pararse a preguntar,
   salvo que un requisito admita dos lecturas y el veredicto dependa de cuál es la buena. Por cada
   requisito, un commit y un resumen corto (recuento y hallazgos graves). Al cerrar cada bloque, la
   tanda de preguntas para TIMU. Las decisiones se toman al final, agrupadas por problema de diseño
   (abajo), no requisito a requisito.

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
| 1. Estados y ciclo de vida | 6.10, 6.23, 6.1, 6.12 | [bloque-1-estados-y-ciclo-de-vida](bloque-1-estados-y-ciclo-de-vida.md) | Auditado (2026-11-24) |
| 2. Cartera, planes y renovación | 6.2, 6.3, 6.4 | [bloque-2-cartera-planes-y-renovacion](bloque-2-cartera-planes-y-renovacion.md) | Auditado (2026-11-25) |
| 3. Servicios y preventivos | 6.5, 6.6, 6.7, 6.8, 6.9, 6.13 | [bloque-3-servicios-y-preventivos](bloque-3-servicios-y-preventivos.md) | En curso: 6.5 a 6.7 auditados (2026-11-25) |
| 4. Lo clínico | 6.14, 6.15, 6.17 | [bloque-4-clinico](bloque-4-clinico.md) | Sin auditar |
| 5. Comunicación y seguimiento | 6.11, 6.16, 6.18, 6.19, 6.20, 6.21 | [bloque-5-comunicacion-y-seguimiento](bloque-5-comunicacion-y-seguimiento.md) | Sin auditar |
| 6. Clínicas aliadas | 6.22 | [bloque-6-clinicas-aliadas](bloque-6-clinicas-aliadas.md) | Sin auditar |
| 7. Transversales | 7, 8, 12, 13 | por extraer | Sin extraer |
| 8. Técnicas y externas | 9, 10, 11, 14, y 1 a 5 | por extraer | Sin extraer |
| Anexo | Lo que prometió la [propuesta](../propuesta-timu-puntos-15-19.md) (tabla B, sección E) | por extraer | Sin extraer |

## Recuento

| Sección | Obligaciones | Cumple | Equivalente | Parcial | Falta | Contradice | Decidido | Externo | Por decidir | Sin auditar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 267 | 64 | 0 | 29 | 14 | 6 | 0 | 0 | 12 | 142 |

## Problemas de diseño que van apareciendo

Hallazgos de varios requisitos que tienen la misma causa. Se arreglan con una sola pieza, no
requisito a requisito, y son la base de la sesión de decisiones del final. Cada bloque añade los
suyos o amplía los que ya están.

1. **Los cambios de estado no se propagan a los procesos que dependen de ellos.** Una familia
   cancelada sigue en la ruta, en la bandeja de preventivos y con sus tareas abiertas; una
   congelada conserva lo que ya tenía agendado; un peludo retirado sigue en la bandeja. El docstring
   de `familias.cambiar_estado` promete unos enganches que no existen. Obligaciones: 6.23-06,
   6.23-07, 6.23-08 y 6.2-05.
2. **No se registra la gestión con la familia.** Ni el servicio, ni el pendiente, ni el preventivo
   guardan que se la contactó, qué respondió o que no contestó; «no autorizado» se resuelve de tres
   formas distintas; y el portal le dice «Confirmada» a una cita que nadie confirmó. En cartera,
   queda lo que la plataforma le escribe a la familia, pero no que alguien del equipo la llamó ni
   qué prometió. Al programar, lo que la familia pide sin fecha no queda en ninguna parte, la
   autorización del servicio es la del médico y no la de la familia, y no hay confirmación.
   Obligaciones: 6.10-02, 6.10-05, 6.10-09, 6.10-10, 6.2-20, 6.5-02, 6.5-03, 6.5-11, 6.5-13, y por
   revisar en el bloque 3: 6.8-12 y 6.8-13.
3. **Lo que la familia ya dio no siempre llega a su ficha.** El bot comercial pregunta la ciudad y
   los peludos y no los pasa al registro; Comercial no convierte un interesado en familia; la
   afiliación no pregunta lo preventivo y el calendario no sabe qué recibió ya la mascota; y
   `POST /formularios/familia` no lo alimenta nadie. Obligaciones: 6.1-27, 6.12-06, y por revisar en
   el bloque 3: 6.13.
4. **Lo automático le habla a la familia, no al equipo.** La cartera le escribe sola a la familia
   (avisos de mora, congelamiento, reactivación), pero al equipo no le crea tareas ni alertas: la
   mora de una familia sin tarjeta no deja ninguna tarea, el motor no deja que una regla de cartera
   cree una ni avise al equipo, y nadie se entera de un congelamiento ni del retiro de un peludo
   de un contrato. Las dos tareas que sí existen son del cobro con tarjeta guardada, y ninguna
   pantalla registra una tarjeta. Mientras las plantillas de mora no estén aprobadas en Meta, la
   mora solo la ve quien entra al panel (el Inicio y la bandeja). Tampoco crea tarea un pendiente
   de una atención. Obligaciones: 6.2-01, 6.2-09, 6.2-10, 6.3-06 y 6.6-04.
5. **El periodo congelado no tiene política.** Congelada, la afiliación deja de emitir cuotas,
   pero la emisión retoma desde la última emitida: al reactivarse se cobran de golpe los meses
   congelados, ya vencidos, y la familia vuelve a congelarse al día siguiente (reproducido el
   2026-11-25). Ni el código ni el documento dicen si esos meses se cobran, se perdonan o corren la
   renovación. Obligaciones: 6.2-05, 6.2-06 y 6.2-14 (junto con 6.23-03 y 6.23-08).
6. **La renovación es solo una fecha.** Renovar mueve `fecha_renovacion` un año y nada más: no
   aplica ninguna regla, no actualiza el precio, no deja un registro que se vea y no cierra su
   tarea. El precio, en cambio, se vuelve a cotizar con la lista del día cada vez que entra o sale
   un peludo. Y no renovar solo impide agendar: la familia con el plan vencido sigue recibiendo
   cuotas, cobros y avisos de mora. Obligaciones: 6.4-03, 6.4-04, 6.4-06 y 6.3-04.
7. **Lo que se registra no se ve.** La base guarda cada aviso de mora con su regla, cada cambio
   de valor de un contrato (`cambios_plan`) y la auditoría de cada cambio del contrato, pero
   ninguna pantalla ni ruta los lee: el Historial de la familia solo muestra los cambios de su
   ficha. Lo mismo con la historia de estados de un servicio, de la que la ficha solo dice el
   motivo del último cambio, y con la de un pendiente. La trazabilidad existe solo para quien
   consulta la base. Obligaciones: 6.2-20, 6.3-07, 6.4-06, 6.4-07, 6.5-14 y 6.6-08.
8. **El equipo no puede escribirle a una familia desde el panel.** La API tiene cómo mandar una
   plantilla o un texto (`POST /comunicaciones/mensajes/plantilla` y `/texto`), pero ninguna
   pantalla lo usa: ni la ficha, ni la bandeja de cartera, ni un pendiente. Lo que la plataforma
   no manda sola, el equipo lo escribe fuera, por WhatsApp. Va junto con la fila de 6.17 y 6.19 de
   [lo que falta](../pendiente-en-el-codigo.md) (WhatsApp en coexistencia). Obligaciones: 6.3-08,
   6.6-05, y el hueco de 6.2-11.
9. **La autorización es una marca que se revisa tarde.** El servicio que la requiere se programa
   primero: toma su fecha y su cupo, y después espera. La autorización es la del médico, no la de
   la familia, y solo se exige para salir en ruta o atender. Antes de eso, «Confirmar agenda» lo
   pasa a `agendado` sin ella, y el planificador lo mete en una ruta (reproducido el 2026-11-25).
   Obligaciones: 6.5-02, 6.5-11, 6.5-15 y 6.6-09 (junto con 6.10-03).
10. **Lo que TIMU tendría que poder ajustar está en el código o en variables de entorno.** El
    motor de reglas y las tarifas se editan sin desplegar, pero otras cosas no: el flujo de cada
    tipo de servicio (su duración, si requiere autorización y sus pasos) y los tipos nuevos; los
    tramos de peludos y su máximo; la ventana de renovación de 90 días; y la jornada y el máximo de
    atenciones de una ruta. Las Secciones 3 y 4 piden reglas que se modifiquen sin reconstruir la
    plataforma. Obligaciones: 6.3-09, 6.5-15 y 6.7-12 (y lo fijo de 6.4-02 y 6.7-06).

## Preguntas para TIMU

Lo que el documento deja abierto y solo TIMU puede aclarar. Se juntan aquí para mandarlas por
tandas, sin esperar al final de la auditoría.

### Primera tanda (bloque 1, 2026-11-24)

- **6.23-05.** El documento pide los estados «Cancelado» y «Retirado». ¿En qué se diferencian para
  TIMU? Por ejemplo: ¿«Cancelado» lo decide TIMU (por mora, por política) y «Retirado» es la familia
  que se va por decisión propia? ¿O «Retirado» es el integrante que sale de un plan grupal (6.3)?
- **6.12-06 y 6.13.** ¿Qué preguntan hoy en su formulario de afiliación sobre vacunas y
  desparasitaciones (producto, fecha, peso)? ¿Nos pueden compartir ese formulario, y los demás que
  usen hoy con las familias? Con eso se decide qué pide la afiliación y qué formularios tiene que
  recibir la plataforma (6.1-27).
- **6.1-03.** ¿Quiénes de una familia necesitan entrar al portal? Hoy entra solo el titular, y hasta
  tres contactos más quedan registrados pero sin acceso.

### Segunda tanda (bloque 2, 2026-11-25)

- **6.3. Necesitamos que TIMU aclare qué es un «plan grupal».** ¿Es la afiliación de una familia
  con varios peludos, en la que cada uno paga menos según cuántos son (como la escala de precios
  de hoy)? ¿O es un plan que agrupa a varias personas o familias, por ejemplo de una empresa o de
  un grupo familiar con varios titulares? Si es lo segundo, ¿cómo funciona hoy: quién paga, cómo
  se reparte el valor y qué pasa cuando alguien sale? Hasta que respondan, 6.3 queda «Por
  decidir» y se audita con las dos lecturas.
- **6.3, si es la familia con varios peludos.** Cuando un peludo sale del plan (fallece, se da en
  adopción), ¿desde cuándo cambia lo que paga la familia? ¿Se le devuelve o se le abona lo que ya
  pagó del periodo en curso? Hoy cambia desde la siguiente cuota y no se devuelve nada: en un pago
  anual, puede ser casi un año.
- **6.2. La política de mora.** Hoy, de forma provisional, se avisa a la familia el día 1, el 5, el
  15 y el 25 después del vencimiento, la afiliación pasa a «en mora» el día 5 y se congela el día
  30. ¿Son esos los momentos de TIMU? ¿Después del congelamiento llega un momento en que se
  cancela? ¿Y qué dice cada aviso? (Hay que registrar esos textos en Meta.)
- **6.2-02.** ¿Cuántos días antes del vencimiento recuerdan hoy el pago, y qué le dicen a la
  familia?
- **6.2-05 y 6.2-06.** Mientras una afiliación está congelada, ¿se siguen causando sus cuotas?
  Cuando la familia se pone al día, ¿paga solo lo que debía al congelarse o también los meses
  congelados? ¿La fecha de renovación se corre por el tiempo congelado?
- **6.2-10.** ¿Qué tareas les genera hoy su plataforma de cobro, para quién y en qué momento? ¿Y
  alguna familia paga hoy con débito automático a una tarjeta, o todas pagan cada cuota?
- **6.4.** ¿Cómo se actualiza hoy el precio al renovar: con la lista de precios vigente, un
  porcentaje fijo, el IPC? ¿Cambia algo más (beneficios, carencias)? Cuando TIMU sube los precios,
  ¿las familias ya afiliadas conservan el suyo hasta renovar?
- **6.4.** ¿Qué pasa si una familia no renueva: se renueva sola, se cancela, o sigue pagando? Hoy
  sigue pagando pero no puede agendar servicios.

### Tercera tanda (bloque 3, en curso)

- **6.5-07.** Un beneficio con cupo «al año» (por ejemplo, cuatro consultas en la clínica), ¿se
  cuenta por año calendario o por año de afiliación? Hoy es el calendario: quien se afilia en
  noviembre usa su cupo en noviembre y diciembre, y tiene otro completo en enero.
- **6.5-06.** ¿Los beneficios tienen periodo de carencia (días desde la afiliación antes de poder
  usarlos)? ¿Cuáles y de cuántos días?
