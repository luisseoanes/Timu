# Bloque 3: servicios y preventivos

Las obligaciones de 6.5, 6.6, 6.7, 6.8, 6.9 y 6.13 del [documento de
requerimientos](../documento-requerimientos-funcionales.md), una por fila, con el texto del
documento, en el orden en que se auditan. Método, tipos, veredictos y avance: [README](README.md).
Las rutas de la evidencia son relativas a la raíz del repositorio.

## 6.5. Programación de servicios

**Auditado el 2026-11-25.**

**Lo que hay:**
- **Agendar es un solo paso**, desde el panel (`NuevoServicioModal`: familia, mascota, tipo, día y
  franja con cupo) o desde el portal. Hace la solicitud y la programación a la vez y exige una
  fecha con cupo (`agendar`, `backend/app/modules/servicios/service.py:381`). Antes valida la
  elegibilidad: plan vigente y sin vencer, cartera al día, mascota afiliada, beneficio del plan de
  ese peludo con cupo, y las reglas `servicio.elegibilidad` (`elegibilidad`, `:80`).
- **El servicio nace `agendado`, o `pendiente_autorizacion` si su tipo lo pide**
  (`:412`). En ese caso la regla `servicio_requiere_autorizacion` le deja una tarea al médico
  (`backend/app/modules/reglas/datos.py:123`), y el médico lo autoriza (`autorizar`, `:526`). La
  cita ya tiene su fecha y ocupa su cupo mientras espera (`OCUPAN_CUPO`, `:45`).
- **La disponibilidad son franjas semanales** por ciudad y modalidad, con una capacidad (cuántas
  atenciones caben a la vez), más días bloqueados (`Franja`,
  `backend/app/modules/servicios/models.py:25`). El profesional no se asigna al agendar: se asigna
  al armar la ruta (`backend/app/modules/rutas/service.py:498`).
- **Cada tipo de servicio tiene su duración, si requiere autorización y sus pasos obligatorios**
  (`TIPOS_SERVICIO`, `backend/app/modules/catalogos/datos.py:264`). Hay siete tipos y ninguno es
  la ecografía. Administración solo los activa o los apaga (`backend/app/modules/catalogos/router.py:204`;
  `frontend/src/features/admin/Catalogos.tsx`).
- **Reproducido el 2026-11-25 contra `db-test`**, con pruebas temporales que no quedaron en el
  repositorio:
  - (a) Con un plan de una consulta domiciliaria al mes, la familia A agenda una para diciembre, y
    después la de noviembre se rechaza: «Se agotó el cupo». La familia B agenda la de noviembre, y
    la de diciembre se rechaza igual.
  - (b) Un beneficio con 30 días de carencia se agenda el mismo día de la afiliación (201).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.5-01 | Facilitar la gestión de solicitudes y la programación de servicios veterinarios | Exige | Cumple | Se agenda desde el panel y desde el portal contra la agenda real, y los servicios se listan con filtros combinables y se gestionan desde su ficha (`test_disponibilidad_descuenta_lo_agendado`, `backend/tests/test_servicios.py:79`; `test_listado_de_servicios_combina_filtros`, `:634`; `test_agenda_reprograma_y_cancela_dentro_de_las_reglas`, `backend/tests/test_portal.py:196`; panel `servicios.test.tsx:79`). |
| 6.5-02 | Flujo: solicitud → validación → disponibilidad → autorización → programación → confirmación → realización → seguimiento | Exige | Parcial | Están la validación (la elegibilidad, y la del médico si el tipo la pide), la disponibilidad, la realización (en atención y completado, con sus pasos) y el seguimiento (la encuesta al completar, 6.20). Pero **la solicitud y la programación son un solo paso** (03); **la autorización va después de programar** y es la del médico, no la de la familia (11); y **la confirmación no existe** (13, y 6.10-05). Que la cita ocupe su cupo mientras espera autorización puede ser lo que TIMU quiera, pero no es el orden del documento. Es el problema de diseño 2. |
| 6.5-03 | Registrar la solicitud | Exige | Parcial | Solo queda registrada la solicitud que se puede programar en ese momento. Si la familia no es elegible o no hay cupo, `agendar` la rechaza con su motivo y no queda nada: el estado `solicitado` solo existe un instante dentro de `agendar` (`backend/app/modules/servicios/service.py:408`) y en las remisiones a una clínica aliada (`backend/app/modules/aliadas/service.py:178`). Lo que la familia pide por WhatsApp sin fecha, o lo que espera un cupo, no tiene dónde quedar. El servicio tampoco guarda por qué canal llegó. |
| 6.5-04 | Identificar usuario y mascota | Exige | Cumple | Cada servicio lleva su familia y su mascota. Con varios peludos hay que decir cuál, y la mascota tiene que ser de la familia y estar afiliada (`backend/app/modules/servicios/service.py:102`; `test_la_elegibilidad_y_el_cupo_son_los_del_plan_de_cada_peludo`, `backend/tests/test_servicios.py:945`; `test_el_listado_dice_a_quien_se_atiende`, `:898`). |
| 6.5-05 | Identificar plan | Exige | Cumple | El plan del peludo que recibe el servicio, de su línea del contrato (`:121`; misma prueba de 04). |
| 6.5-06 | Validar beneficios disponibles | Exige | Parcial | **Valida** que el plan incluya el tipo y que quede cupo, y las reglas adicionales (`test_cupo_del_beneficio`, `backend/tests/test_servicios.py:142`; `test_elegibilidad_explica_los_motivos`, `:123`). **No valida la carencia**: el beneficio guarda desde cuántos días de afiliada aplica, y la familia lo lee en el portal, el registro y el contrato, pero agendar no la mira (reproducido, b; `carencia_dias` no aparece fuera de `planes` y del contrato). Y un plan sin ningún beneficio cargado lo cubre todo, sin cupo (`if plan.beneficios and beneficio is None`, `backend/app/modules/servicios/service.py:123`). |
| 6.5-07 | Identificar servicios ya utilizados dentro del periodo correspondiente | Exige | **Contradice** | `_usos` (`backend/app/modules/servicios/service.py:142`) cuenta los servicios del peludo desde el inicio del mes o del año de **hoy**, sin límite hacia adelante, y no mira la fecha del servicio que se va a agendar. **Una cita del mes siguiente gasta el cupo de este, y una de este bloquea la del siguiente** (reproducido, a). La prueba que hay agenda dos en el mismo mes (`test_cupo_del_beneficio`). Además, el periodo anual es el año calendario, no el año del contrato: una familia que se afilia en noviembre tiene un cupo anual completo en noviembre y diciembre, y otro en enero. Cuál es el «periodo correspondiente» lo tiene que decir TIMU. |
| 6.5-08 | Generar solicitud para validación profesional cuando sea necesario | Exige | Cumple | Un tipo que requiere autorización deja el servicio `pendiente_autorizacion`, con una tarea de prioridad alta para el médico, y no se atiende hasta que él lo autoriza (`test_ciclo_de_vacunacion`, `backend/tests/test_servicios.py:161`; panel `ServicioDetallePage.test.tsx:93`). Qué tipos lo requieren está fijo en el código (15). |
| 6.5-09 | Registrar disponibilidad del profesional | Exige | Parcial | Se registra la disponibilidad de la ciudad, no la de cada profesional: franjas por ciudad, modalidad y día con una capacidad, y días bloqueados (`test_operaciones_crea_franjas_con_la_ciudad_del_catalogo`, `backend/tests/test_servicios.py:550`; `test_franjas_se_filtran_por_ciudad_y_se_ajustan`, `:603`; panel `ServiciosPage.gestion.test.tsx:352` y `:397`). Que un médico no trabaje un día se hace bajando la capacidad a mano, y quién atiende se sabe al armar la ruta. Los días bloqueados no se listan ni se deshacen ([lo que falta](../pendiente-en-el-codigo.md), fila 6.5). |
| 6.5-10 | Proponer opciones al usuario | Exige | Cumple | La disponibilidad devuelve los bloques libres del día según la duración del tipo, y tanto el panel como el portal los ofrecen (`disponibilidad`, `:337`; `test_disponibilidad_descuenta_lo_agendado`; `test_agenda_reprograma_y_cancela_dentro_de_las_reglas`; panel `servicios.test.tsx:79`). El portal solo deja agendar los tipos que la familia gestiona sola (`test_no_agenda_lo_que_no_es_autogestionable`, `backend/tests/test_portal.py:230`). |
| 6.5-11 | Registrar autorización | Exige | Parcial | En el servicio, la autorización es la del médico: quién y cuándo (`autorizado_por_id`, `backend/app/modules/servicios/models.py:86`), y solo la da un perfil clínico (`backend/app/modules/servicios/router.py:438`). **La de la familia**, que es la del documento («autorización del usuario», en el ejemplo de la ecografía), se registra con su medio en un pendiente (6.6; `ServiciosPage.gestion.test.tsx:227`) y en un preventivo (6.9), pero **no en un servicio que se agenda directamente**. |
| 6.5-12 | Programar el servicio | Exige | Cumple | Contra un cupo real, bloqueando la franja para que dos personas no tomen el mismo, nunca en el pasado ni en un día bloqueado, y se reprograma con motivo (`_reservar`, `backend/app/modules/servicios/service.py:354`; `test_rechaza_cupo_tomado`, `backend/tests/test_servicios.py:94`; `test_fuera_de_franja_y_dia_bloqueado`, `:105`; `test_no_agenda_en_el_pasado`, `:115`; `test_reprogramar_dispara_tarea_de_operaciones`, `:255`). |
| 6.5-13 | Generar confirmaciones | Exige | Parcial | Al agendar no sale nada: ninguna regla sembrada ni ningún manejador avisa. El motor admite una regla `servicio.transicion` que avise por WhatsApp al pasar a `agendado` (`_disparadores`, `:488`), pero ninguna prueba la ejercita. Lo único parecido es la franja de llegada que se le avisa a la familia cuando se arma la ruta, solo en lo domiciliario (`test_planificar_avisa_la_ventana_de_llegada`, `backend/tests/test_rutas.py:216`). Y el portal dice «Confirmada» sin que nadie confirme (6.10-05, Contradice). |
| 6.5-14 | Mantener trazabilidad | Exige | Parcial | La base audita cada cambio del servicio y de sus pasos, con quién y cuándo, y cada cambio de estado publica su evento. Pero la ficha solo muestra el motivo del último cambio (`ServicioDetallePage.test.tsx:53`); la historia de estados del servicio no la lee ninguna pantalla ni ruta. Es el problema de diseño 7. |
| 6.5-15 | Configurar flujos distintos según el tipo de servicio (la ecografía: cobertura, disponibilidad y autorización del usuario antes de programarse) | Exige | Parcial | Cada tipo cambia el flujo: su duración, si requiere autorización y los pasos sin los que no se completa (`test_ciclo_de_vacunacion`; `test_un_paso_se_corrige_en_atencion_y_queda_fijo_al_completar`, `backend/tests/test_servicios.py:198`). Las reglas de elegibilidad y de cada cambio de estado se editan sin desplegar. **Pero el flujo de un tipo no se configura**: duración, autorización y pasos están en el código, Administración solo apaga un tipo, y uno nuevo (la ecografía) necesita un despliegue. **Y en el ejemplo del documento la autorización va antes de programar**, mientras que aquí la cita se programa y después espera la autorización del médico, no la de la familia (11). |

**Lo que hay que decidir:**
- 07: contar el cupo en el periodo de la fecha del servicio, y qué periodo es (el calendario o el
  año del contrato: pregunta para TIMU).
- 06: que la carencia se valide al agendar, y qué cubre un plan sin beneficios cargados.
- 02, 03, 11 y 13: el orden del flujo y lo que falta en él (la solicitud sin fecha, la
  autorización de la familia y la confirmación), junto con 6.10 (problema de diseño 2).
- 15: que el flujo de cada tipo se configure desde Administración, con tipos nuevos.
- 09: si la disponibilidad tiene que ser por profesional.

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
