# Bloque 3: servicios y preventivos

Las obligaciones de 6.5, 6.6, 6.7, 6.8, 6.9 y 6.13 del [documento de
requerimientos](../documento-requerimientos-funcionales.md), una por fila, con el texto del
documento, en el orden en que se auditan. Método, tipos, veredictos y avance: [README](README.md).
Las rutas de la evidencia son relativas a la raíz del repositorio.

## 6.5. Programación de servicios

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.5-01 | Facilitar la gestión de solicitudes y la programación de servicios veterinarios | Exige | Sin auditar | |
| 6.5-02 | Flujo: solicitud → validación → disponibilidad → autorización → programación → confirmación → realización → seguimiento | Exige | Sin auditar | |
| 6.5-03 | Registrar la solicitud | Exige | Sin auditar | |
| 6.5-04 | Identificar usuario y mascota | Exige | Sin auditar | |
| 6.5-05 | Identificar plan | Exige | Sin auditar | |
| 6.5-06 | Validar beneficios disponibles | Exige | Sin auditar | |
| 6.5-07 | Identificar servicios ya utilizados dentro del periodo correspondiente | Exige | Sin auditar | |
| 6.5-08 | Generar solicitud para validación profesional cuando sea necesario | Exige | Sin auditar | |
| 6.5-09 | Registrar disponibilidad del profesional | Exige | Sin auditar | |
| 6.5-10 | Proponer opciones al usuario | Exige | Sin auditar | |
| 6.5-11 | Registrar autorización | Exige | Sin auditar | |
| 6.5-12 | Programar el servicio | Exige | Sin auditar | |
| 6.5-13 | Generar confirmaciones | Exige | Sin auditar | Visto al auditar 6.10-05: ninguna regla sembrada ni ningún manejador avisa al agendar. |
| 6.5-14 | Mantener trazabilidad | Exige | Sin auditar | |
| 6.5-15 | Configurar flujos distintos según el tipo de servicio (la ecografía: cobertura, disponibilidad y autorización del usuario antes de programarse) | Exige | Sin auditar | |

## 6.6. Gestión de pendientes derivados de una atención

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.6-01 | Registrar el pendiente (laboratorio, ecografía, procedimiento, control, seguimiento) asociado a la mascota | Exige | Sin auditar | La fila 6.6 de [lo que falta en el código](../pendiente-en-el-codigo.md) dice que es texto libre. |
| 6.6-02 | Identificar cobertura según el plan | Exige | Sin auditar | |
| 6.6-03 | Determinar condiciones y/o valor aplicable | Exige | Sin auditar | |
| 6.6-04 | Generar tarea para el equipo | Exige | Sin auditar | |
| 6.6-05 | Facilitar la comunicación con la familia | Exige | Sin auditar | |
| 6.6-06 | Registrar autorización o rechazo | Exige | Sin auditar | |
| 6.6-07 | Iniciar programación únicamente cuando corresponda | Exige | Sin auditar | |
| 6.6-08 | Mantener trazabilidad | Exige | Sin auditar | |
| 6.6-09 | **No enviar automáticamente a ruta o agenda un servicio que aún requiere autorización o validación de disponibilidad** | Exige | Sin auditar | Visto al auditar 6.10: un servicio con `requiere_autorizacion` puede pasar de `solicitado` a `agendado` sin autorización; solo se le impide pasar a `en_ruta` o `en_atencion` (`backend/app/modules/servicios/service.py:453`). Revisar si eso es «enviar a la agenda». |

## 6.7. Gestión de rutas domiciliarias

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.7-01 | Organizar y optimizar servicios domiciliarios | Exige | Sin auditar | |
| 6.7-02 | Variable: ubicación | Exige | Sin auditar | |
| 6.7-03 | Variable: zona | Exige | Sin auditar | |
| 6.7-04 | Variable: tipo de servicio | Exige | Sin auditar | |
| 6.7-05 | Variable: duración estimada | Exige | Sin auditar | |
| 6.7-06 | Variable: disponibilidad | Exige | Sin auditar | |
| 6.7-07 | Variable: franja horaria | Exige | Sin auditar | |
| 6.7-08 | Variable: profesional asignado | Exige | Sin auditar | |
| 6.7-09 | Variable: orden de desplazamiento | Exige | Sin auditar | |
| 6.7-10 | Visualizar usuarios/servicios en un mapa | Exige | Sin auditar | Unidad aparte, con Google Maps ([pendientes externos](../pendientes-externos.md#mapa-de-las-rutas-requisito-67-r2-pan-06)). |
| 6.7-11 | Proponer una secuencia de atención que optimice desplazamientos, considerando ubicación y duración | Exige | Sin auditar | |
| 6.7-12 | Duración aproximada por tipo de servicio para calcular bloques horarios coherentes | Exige | Sin auditar | |

## 6.8. Gestión de servicios preventivos

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.8-01 | Identificar automáticamente usuarios próximos a recibir preventivos incluidos o asociados a su plan | Exige | Sin auditar | |
| 6.8-02 | Servicio inicial: desparasitación interna | Exige | Sin auditar | |
| 6.8-03 | Servicio inicial: desparasitación externa | Exige | Sin auditar | |
| 6.8-04 | Servicio inicial: vacunación | Exige | Sin auditar | |
| 6.8-05 | Servicio inicial: Bravecto u otros productos preventivos | Exige | Sin auditar | |
| 6.8-06 | Registrar última aplicación | Exige | Sin auditar | |
| 6.8-07 | Registrar producto | Exige | Sin auditar | |
| 6.8-08 | Registrar fecha | Exige | Sin auditar | |
| 6.8-09 | Registrar peso cuando sea pertinente | Exige | Sin auditar | |
| 6.8-10 | Determinar próxima fecha | Exige | Sin auditar | |
| 6.8-11 | Generar alerta | Exige | Sin auditar | |
| 6.8-12 | Contactar a la familia | Exige | Sin auditar | |
| 6.8-13 | Registrar respuesta | Exige | Sin auditar | Visto al auditar 6.10: el preventivo solo tiene `programado`, `aplicado` y `cancelado`; no guarda que se contactó ni qué respondió la familia. |
| 6.8-14 | Reprogramar si no desea el servicio | Exige | Sin auditar | |
| 6.8-15 | Incorporar a ruta cuando sea autorizado | Exige | Sin auditar | |
| 6.8-16 | Actualizar automáticamente la próxima fecha una vez realizado el servicio | Exige | Sin auditar | |

## 6.9. Autorización de servicios preventivos

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.9-01 | Autorización de la familia **mediante formulario** antes de determinados preventivos | Exige | Sin auditar | |
| 6.9-02 | Flujo: el sistema identifica el servicio próximo → comunicación → formulario de autorización → revisión → autorización/reprogramación → programación → realización | Exige | Sin auditar | |
| 6.9-03 | Lo que da la familia queda registrado y asociado a la mascota | Exige | Sin auditar | |

## 6.13. Alimentación automática del calendario preventivo

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.13-01 | Lo dado en la afiliación alimenta el calendario: última desparasitación | Exige | Sin auditar | Visto al auditar 6.12-06: la afiliación no lo pregunta. |
| 6.13-02 | … producto utilizado | Exige | Sin auditar | Visto al auditar 6.12-06: la afiliación no lo pregunta. |
| 6.13-03 | … fecha | Exige | Sin auditar | Visto al auditar 6.12-06: la afiliación no lo pregunta. |
| 6.13-04 | … peso | Exige | Sin auditar | Visto al auditar 6.12-06: la afiliación pide el peso (6.12-03), pero el calendario no lo usa. |
| 6.13-05 | … vacunación | Exige | Sin auditar | Visto al auditar 6.12-06: la afiliación no lo pregunta. |
| 6.13-06 | Calcular o identificar la fecha correspondiente | Exige | Sin auditar | |
| 6.13-07 | Generar las tareas necesarias | Exige | Sin auditar | |
