# Sección 6: requerimientos funcionales

Las obligaciones de la Sección 6 del [documento de requerimientos](../documento-requerimientos-funcionales.md),
una por fila, con el texto del documento. Método, tipos y veredictos: [README](README.md). Las rutas
de la evidencia son relativas a la raíz del repositorio.

## 6.1. Gestión de familias, usuarios y mascotas

**Auditado el 2026-11-24.**

**Lo que hay:**
- La ficha de la familia del panel (`frontend/src/features/familias/FamiliaDetallePage.tsx:46`)
  tiene una cabecera con el plan de cada peludo, el estado y la ciudad; la línea de la familia; un
  resumen de mascotas y de cartera; y las pestañas Datos, Mascotas, Cartera, Servicios, Documentos,
  Comunicaciones e Historial, cada una según el perfil (Sección 12).
- La mascota tiene su ficha en una ventana (`frontend/src/features/familias/FichaMascota.tsx:29`)
  con sus datos, su foto, su plan, sus servicios del mes y los enlaces a su historia clínica (solo el
  médico) y a su carnet.
- Las pruebas del panel están en `frontend/src/features/familias/FamiliaDetallePage.test.tsx`
  (citadas por la línea de su `it`); las del backend, donde se indica.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.1-01 | Crear y administrar un perfil integral de cada familia | Exige | Cumple | La ficha de arriba; se crea, edita, cambia de estado y da de baja (`test_crear_y_listar_familia`, `backend/tests/test_familias.py:54`; `test_baja_logica_oculta_pero_conserva`, `:166`; panel `:94`, `:336`, `:356` y `:584`). |
| 6.1-02 | Familia: datos de contacto | Exige | Cumple | Titular, documento, celular en E.164 y correo (`backend/app/modules/familias/models.py:47`), y hasta tres contactos adicionales (`ContactoFamilia`, `:135`; `test_contactos_adicionales_como_mucho_tres_y_la_baja_libera_su_lugar`, `backend/tests/test_familias.py:965`; panel `:681`). |
| 6.1-03 | Familia: usuarios asociados | Exige | Por decidir | Lo que hay: el titular, que es el único con cuenta en el portal (`usuario_portal_id`, `backend/app/modules/familias/models.py:75`), y hasta tres contactos adicionales sin acceso. El documento llama «usuarios» a los integrantes de la familia (6.2, 6.3), y aquí solo uno puede entrar. Hay que decidir si los contactos cuentan como usuarios asociados o si cada integrante necesita su propio acceso. |
| 6.1-04 | Familia: mascotas asociadas | Exige | Cumple | `Familia.mascotas`; alta y baja (`test_ciclo_de_mascota`, `backend/tests/test_familias.py:223`; panel `:627`). |
| 6.1-05 | Familia: dirección | Exige | Cumple | Dirección, complemento y coordenadas, geocodificadas al guardar (`backend/app/modules/familias/models.py:58`; `test_guardar_direccion_programa_geocodificacion` y siguientes, `backend/tests/test_familias.py:405` a `:438`; panel `:373`). |
| 6.1-06 | Familia: zona/sector | Exige | Cumple | El barrio, obligatorio (`backend/app/modules/familias/models.py:57`, `CHECK barrio_no_vacio`; panel `:373`). Es **texto libre**: la misma zona puede quedar escrita de varias formas. Se revisa en 6.7 (rutas por zona) y en 6.16 (segmentar por zona). |
| 6.1-07 | Familia: plan contratado | Exige | Cumple | El plan de cada peludo en la cabecera y en el estado de cuenta (`test_estado_de_cuenta`, `backend/tests/test_cartera.py:221`; panel `:129` y `:1104`). |
| 6.1-08 | Familia: estado de afiliación | Exige | Cumple | `Familia.estado` en la cabecera, con su historial (`test_historial_de_estados`, `backend/tests/test_familias.py:186`; panel `:584`). Los estados en sí, en 6.23. |
| 6.1-09 | Familia: estado de pagos | Exige | Cumple | El resumen de cartera (cuota, próximo cobro y vencido) y la pestaña Cartera (`test_estado_de_cuenta`; panel `:122` y `:196`). |
| 6.1-10 | Familia: servicios utilizados mensualmente | Exige | Cumple | La pestaña Servicios abre en el mes en curso, con lo utilizado aparte y el cupo consumido de cada peludo (`GET /servicios/resumen`, `backend/app/modules/servicios/router.py:356`; `test_el_resumen_separa_utilizados_y_pendientes_en_el_rango`, `backend/tests/test_servicios.py:811`, y `:847`; panel `:457` y `:496`). |
| 6.1-11 | Familia: servicios pendientes mensualmente | Exige | Cumple | Igual que 10, con lo pendiente aparte y lo abierto de una atención (mismas pruebas). |
| 6.1-12 | Familia: historial de comunicaciones | Exige | Cumple | La pestaña Comunicaciones, enviado y recibido (`test_traza_por_familia`, `backend/tests/test_comunicaciones.py:216`; panel `:758` y `:790`). |
| 6.1-13 | Familia: historial de atención | Exige | Parcial | Lo atendido en casa, en la clínica y en las clínicas aliadas (las remisiones crean su servicio) sale en Servicios → Utilizados, en cualquier rango (6.1-10). **Las orientaciones virtuales (6.17) no salen en ninguna parte de la ficha**, aunque se guardan con la familia (`backend/app/modules/clinica/models.py:146`). La pestaña «Historial» no es esto: dice qué datos de la ficha cambiaron (`FamiliaDetallePage.tsx:262`). |
| 6.1-14 | Familia: documentos asociados | Exige | Parcial | La pestaña Documentos, con lo subido y lo generado (contrato, comprobantes), y con lo que la familia ve en el portal (panel `:986`, `:999` y `:1037`). Pero **ninguna prueba del backend sube ni lista un documento**: el panel se prueba con la API simulada, y el backend solo aparece en las matrices de permisos y rendimiento (`backend/tests/test_permisos.py:249`, `backend/tests/test_persistencia.py:1252`). |
| 6.1-15 | Cada mascota con un perfil individual asociado a su familia | Exige | Cumple | La ficha de la mascota (arriba); la base no deja que cambie de familia (`test_mascota_no_cambia_de_familia`, `backend/tests/test_familias.py:256`; panel `:843`). |
| 6.1-16 | Mascota: nombre | Exige | Cumple | `test_ciclo_de_mascota`; panel `:874`. |
| 6.1-17 | Mascota: especie | Exige | Cumple | Del catálogo, con llave foránea (`test_especie_fuera_del_catalogo`, `backend/tests/test_familias.py:144`; panel `:112`). |
| 6.1-18 | Mascota: sexo | Exige | Cumple | Enum de la base (`backend/app/modules/familias/models.py:115`); panel `:874`. El listado de Mascotas enseña el valor crudo («hembra») en vez de «Hembra», un detalle de presentación. |
| 6.1-19 | Mascota: edad/fecha de nacimiento | Exige | Cumple | Fecha de nacimiento, que no puede ser futura (`test_fecha_de_nacimiento_futura`, `backend/tests/test_familias.py:267`; `:277`). No hay forma de dar solo una edad aproximada cuando la familia no sabe la fecha. |
| 6.1-20 | Mascota: raza | Exige | Cumple | `backend/tests/test_familias.py:295`; panel `:874`. |
| 6.1-21 | Mascota: peso | Exige | Cumple | `test_ciclo_de_mascota` (edita el peso); `:295`. |
| 6.1-22 | Mascota: información preventiva | Exige | Cumple | Desde su ficha se abre su carnet, con los perfiles que lo ven (panel `:843` y `:866`). El carnet en sí, en 6.15. |
| 6.1-23 | Mascota: plan asociado | Exige | Cumple | Su plan y lo que paga, y el cambio de plan desde la ficha (panel `:843` y `:1104`). |
| 6.1-24 | Mascota: historial de servicios | Exige | Cumple | Sus servicios del mes en la ficha y la pestaña Servicios filtrada por ella, en cualquier rango (panel `:843` y `:520`). |
| 6.1-25 | Mascota: historia clínica | Exige | Cumple | Enlace a su historia, solo para el médico (panel `:843` y `:866`). La historia en sí, en 6.14. |
| 6.1-26 | Mascota: documentos y archivos | Exige | Parcial | Un documento se ata a una mascota de la familia (clave compuesta, `backend/app/modules/documentos/models.py:27`) y la pestaña Documentos filtra por ella (panel `:986`). No están en la ficha de la mascota, y les falta la prueba del backend, como a 14. |
| 6.1-27 | **Requerimiento crítico**: lo obtenido por formularios se registra automáticamente en el perfil correspondiente, sin volver a digitar lo que el usuario ya dio | Exige | Parcial | **Sí**: el registro en línea crea o completa la ficha, sus peludos, sus contactos y su afiliación con lo que la familia escribe (`test_el_formulario_crea_la_familia_la_afiliacion_y_abre_la_sesion`, `backend/tests/test_registro.py:228`; `test_un_documento_existente_completa_su_ficha`, `:349`), y el formulario que sigue al pago trae lo que dio antes de pagar (`frontend/src/features/publico/CompletarRegistroPage.tsx:191`). **No**: (a) el bot comercial pregunta la ciudad y los peludos y manda el enlace `/afiliacion` sin ellos (`backend/app/modules/comercial/conversacion.py:342`), así que la familia los vuelve a escribir, aunque la portada ya abre la afiliación con lo elegido; (b) Comercial no tiene cómo convertir un interesado en familia, y el equipo vuelve a digitar su nombre, celular, correo y ciudad en «Nueva familia»; (c) `POST /formularios/familia` (`backend/app/modules/afiliaciones/router.py:254`), que crea o completa la ficha desde un formulario público, no lo usa ninguna pantalla ni ningún formulario externo: queda huérfano, con sus pruebas (`backend/tests/test_familias.py:460`). Los otros formularios del documento (la autorización de 6.9 y la encuesta de 6.20) se auditan allí. |

**Lo que hay que decidir:**
- 6.1-03: qué es un «usuario asociado» (¿basta con los contactos o cada integrante necesita
  acceso?).
- 6.1-27: cómo pasa a la ficha lo que la familia le dijo al bot o al asesor, y qué se hace con
  `POST /formularios/familia`: o lo alimenta algún formulario de TIMU o se retira.

## 6.2. Gestión de cartera

Las filas 02 a 06 son los momentos de comunicación del sistema actual de TIMU («por ejemplo»): no
los exige por sí mismos, pero describen el proceso que la plataforma sustituye.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.2-01 | Identificar y hacer seguimiento a usuarios con novedades de pago | Exige | Sin auditar | |
| 6.2-02 | Momento: recordatorio previo al vencimiento | Ejemplo | Sin auditar | |
| 6.2-03 | Momento: seguimiento al vencimiento | Ejemplo | Sin auditar | |
| 6.2-04 | Momento: seguimiento a usuarios con varios días de mora | Ejemplo | Sin auditar | |
| 6.2-05 | Momento: congelamiento del servicio según las políticas establecidas | Ejemplo | Sin auditar | |
| 6.2-06 | Momento: reactivación una vez realizado el pago | Ejemplo | Sin auditar | |
| 6.2-07 | Identificar automáticamente usuarios próximos al vencimiento | Exige | Sin auditar | |
| 6.2-08 | Identificar usuarios morosos | Exige | Sin auditar | |
| 6.2-09 | Generar alertas | Exige | Sin auditar | |
| 6.2-10 | Crear tareas de seguimiento | Exige | Sin auditar | |
| 6.2-11 | Automatizar o facilitar comunicaciones | Exige | Sin auditar | |
| 6.2-12 | Registrar pagos | Exige | Sin auditar | |
| 6.2-13 | Actualizar el estado del usuario | Exige | Sin auditar | |
| 6.2-14 | Programar automáticamente la próxima fecha de cobro | Exige | Sin auditar | |
| 6.2-15 | Periodicidad de pago mensual | Exige | Sin auditar | |
| 6.2-16 | Periodicidad de pago trimestral | Exige | Sin auditar | |
| 6.2-17 | Periodicidad de pago semestral | Exige | Sin auditar | |
| 6.2-18 | Periodicidad de pago anual | Exige | Sin auditar | |
| 6.2-19 | Mantener historial de pagos | Exige | Sin auditar | |
| 6.2-20 | Mantener historial de gestiones de cartera | Exige | Sin auditar | |

## 6.3. Cambios en planes grupales

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.3-01 | Gestionar usuarios vinculados a planes grupales | Exige | Sin auditar | |
| 6.3-02 | Al retirarse un integrante: identificar el cambio | Exige | Sin auditar | |
| 6.3-03 | … actualizar la composición del grupo | Exige | Sin auditar | |
| 6.3-04 | … aplicar la regla correspondiente | Exige | Sin auditar | |
| 6.3-05 | … actualizar el valor a pagar | Exige | Sin auditar | |
| 6.3-06 | … generar alerta o tarea | Exige | Sin auditar | |
| 6.3-07 | … registrar la modificación | Exige | Sin auditar | |
| 6.3-08 | … facilitar la comunicación al usuario | Exige | Sin auditar | |
| 6.3-09 | Las reglas se pueden modificar después sin reconstruir la plataforma | Exige | Sin auditar | |

## 6.4. Renovación anual

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.4-01 | Identificar automáticamente usuarios que cumplen un año en el plan | Exige | Sin auditar | |
| 6.4-02 | Generar alerta | Exige | Sin auditar | |
| 6.4-03 | Aplicar la regla de actualización correspondiente | Exige | Sin auditar | |
| 6.4-04 | Actualizar condiciones económicas | Exige | Sin auditar | |
| 6.4-05 | Generar tarea de comunicación | Exige | Sin auditar | |
| 6.4-06 | Registrar la renovación | Exige | Sin auditar | |
| 6.4-07 | Mantener trazabilidad | Exige | Sin auditar | |

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

## 6.10. Estados de los servicios

**Auditado el 2026-11-24** (ejemplo del método).

**Lo que hay:**
- El servicio tiene ocho estados (`backend/app/core/enums.py:29`): `solicitado`, `agendado`,
  `en_ruta`, `en_atencion`, `completado`, `pendiente_autorizacion`, `reprogramado` y `cancelado`.
- Su grafo está en `backend/app/modules/servicios/state_machine.py:14` y la base lo hace cumplir
  (`test_la_base_rechaza_una_transicion_fuera_del_grafo`, `backend/tests/test_persistencia.py:612`).
- Aparte, el pendiente de una atención tiene sus propios estados (`pendiente_autorizacion`,
  `autorizado`, `en_gestion`, `resuelto` y `rechazado`, en `backend/app/modules/servicios/models.py:113`),
  y el preventivo tiene `programado`, `aplicado` y `cancelado` (`backend/app/core/enums.py:333`).
- Ninguno de los tres modela el contacto con la familia.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.10-01 | Estado «Pendiente» | Ejemplo | Por decidir | Equivale a `solicitado`: registrado y sin agendar. Probado en `test_flujo_normal` (`backend/tests/test_state_machine.py:7`). La equivalencia no está escrita ni decidida. |
| 6.10-02 | Estado «Contactado» | Ejemplo | Falta | No existe ni en el servicio, ni en el pendiente, ni en el preventivo. Nada registra que se contactó a la familia; ver también 6.8-12 y 6.8-13. |
| 6.10-03 | Estado «Autorizado» | Ejemplo | Por decidir | En el servicio es una marca, no un estado: `autorizado`, `autorizado_por_id` y `autorizado_en` (`backend/app/modules/servicios/models.py:86`). Al autorizar, `pendiente_autorizacion` pasa a `agendado` (`backend/app/modules/servicios/service.py:526`; prueba en `test_ciclo_de_vacunacion`, `backend/tests/test_servicios.py:161`). El pendiente sí tiene el estado `autorizado`. Equivalencia posible: la marca más el paso a `agendado`. |
| 6.10-04 | Estado «Programado» | Ejemplo | Por decidir | Equivale a `agendado`, que tiene fecha y franja (`backend/app/modules/servicios/service.py:421`). |
| 6.10-05 | Estado «Confirmado» | Ejemplo | **Contradice** | No hay paso de confirmación, pero el portal le dice «Confirmada» a la familia en cuanto la cita está `agendado` (`frontend/src/features/portal/citas.ts:14`). La familia lee como confirmado algo que nadie confirmó. El documento pone la confirmación como un paso propio, después de la programación (6.5-02) y como algo que se genera (6.5-13). |
| 6.10-06 | Estado «Realizado» | Ejemplo | Por decidir | Equivale a `completado`, que exige los pasos obligatorios del tipo (`backend/app/modules/servicios/service.py:456`; `test_flujo_normal`). |
| 6.10-07 | Estado «Reprogramado» | Ejemplo | Cumple | Existe, exige motivo y dispara la tarea «Acordar nueva fecha con la familia» (regla `servicio_reprogramado`, `backend/app/modules/reglas/datos.py:136`; `test_reprogramar_dispara_tarea_de_operaciones`, `backend/tests/test_servicios.py:255`). Es de paso: `reprogramar` lo atraviesa y deja el servicio en `agendado` con la fecha nueva (`backend/app/modules/servicios/service.py:425`), así que un listado nunca lo muestra en ese estado. Queda en la auditoría de la fila. |
| 6.10-08 | Estado «Cancelado» | Ejemplo | Cumple | Existe, exige motivo y libera el cupo (`test_cancelar_exige_motivo_y_libera_cupo`, `backend/tests/test_servicios.py:245`). |
| 6.10-09 | Estado «No autorizado» | Ejemplo | Parcial | Tres caminos distintos. El pendiente tiene `rechazado`, probado en `backend/tests/test_servicios.py:315`. El preventivo pasa a `cancelado` con el motivo «La familia no autorizo el preventivo» (`backend/app/modules/preventivos/service.py:335`), sin ninguna prueba. Y el servicio no tiene rechazo: solo se puede cancelar. Por eso no se distingue un «no autorizado» de una cancelación cualquiera, ni para filtrar ni para disparar una regla. |
| 6.10-10 | Estado «Sin respuesta» | Ejemplo | Falta | No existe en ninguno de los tres. Una familia que no contesta no deja rastro ni dispara nada. |
| 6.10-11 | Los estados permiten generar tareas, alertas y acciones posteriores | Exige | Parcial | El mecanismo existe y está probado. Cada cambio de estado evalúa las reglas `servicio.transicion`, con acciones de tarea y de mensaje (`backend/app/modules/servicios/service.py:488`, `backend/app/modules/reglas/acciones.py:104`), y publica el evento `servicio.<estado>` (`backend/app/modules/servicios/state_machine.py:28`). La encuesta se engancha al de `completado` (`backend/app/workers/tasks/encuestas.py:15`; `test_completar_el_servicio_programa_la_encuesta`). Las reglas se editan en Administración (`DEU-8`). Pero los estados que faltan (02, 05, 09, 10) no pueden disparar nada, y la acción «notificar» es un mensaje a la familia, no una alerta al equipo: las alertas, en 7 y 8. |

**Lo que hay que decidir:**
- Las equivalencias de 01, 03, 04 y 06.
- Si «Contactado», «Confirmado», «No autorizado» y «Sin respuesta» se añaden como estados del
  servicio o como registro de contacto aparte. Los dos primeros y el último describen la gestión
  con la familia, que hoy no se modela en ningún sitio. Es la misma pregunta que 6.8-12 y 6.8-13,
  y conviene decidirla junto con 6.5 y 6.8.
- Que el portal deje de decir «Confirmada» sin confirmación, sea cual sea la decisión anterior.

## 6.11. Atención comercial automatizada

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.11-01 | Flujos de atención y calificación comercial por canales digitales | Exige | Sin auditar | |
| 6.11-02 | Una familia que entra por WhatsApp u otros canales inicia una interacción guiada | Exige | Sin auditar | |
| 6.11-03 | Información: especie | Opcional | Sin auditar | |
| 6.11-04 | Información: edad | Opcional | Sin auditar | |
| 6.11-05 | Información: sexo | Opcional | Sin auditar | |
| 6.11-06 | Información: ubicación | Opcional | Sin auditar | |
| 6.11-07 | Información: necesidades | Opcional | Sin auditar | |
| 6.11-08 | Información: interés | Opcional | Sin auditar | |
| 6.11-09 | Información: características de la mascota | Opcional | Sin auditar | |
| 6.11-10 | Información: lo relevante para determinar el plan | Opcional | Sin auditar | |
| 6.11-11 | Reglas configuradas previamente para recomendar el plan más adecuado | Exige | Sin auditar | |
| 6.11-12 | La recomendación considera la ciudad | Exige | Sin auditar | |
| 6.11-13 | … la disponibilidad del plan | Exige | Sin auditar | |
| 6.11-14 | … las condiciones comerciales vigentes | Exige | Sin auditar | |
| 6.11-15 | … las características del usuario | Exige | Sin auditar | |
| 6.11-16 | Un plan no disponible en una ciudad no se recomienda allí | Exige | Sin auditar | |
| 6.11-17 | La configuración permite habilitarlo después | Exige | Sin auditar | |
| 6.11-18 | El usuario puede escoger un plan distinto al recomendado | Exige | Sin auditar | |

## 6.12. Afiliación y creación automática de usuarios

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.12-01 | Conectar formulario → pago → afiliación → contrato → creación de perfil | Exige | Sin auditar | Sin pasarela de pruebas (Wompi) no hay prueba de punta a punta; el pago manual no tiene pantalla ([lo que falta](../pendiente-en-el-codigo.md)). |
| 6.12-02 | El formulario alimenta automáticamente el perfil de familia | Exige | Sin auditar | |
| 6.12-03 | … el perfil de mascota | Exige | Sin auditar | |
| 6.12-04 | … el plan | Exige | Sin auditar | |
| 6.12-05 | … los datos de contacto | Exige | Sin auditar | |
| 6.12-06 | … la información preventiva | Exige | Sin auditar | |
| 6.12-07 | … la información necesaria para programación | Exige | Sin auditar | |

## 6.13. Alimentación automática del calendario preventivo

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.13-01 | Lo dado en la afiliación alimenta el calendario: última desparasitación | Exige | Sin auditar | |
| 6.13-02 | … producto utilizado | Exige | Sin auditar | |
| 6.13-03 | … fecha | Exige | Sin auditar | |
| 6.13-04 | … peso | Exige | Sin auditar | |
| 6.13-05 | … vacunación | Exige | Sin auditar | |
| 6.13-06 | Calcular o identificar la fecha correspondiente | Exige | Sin auditar | |
| 6.13-07 | Generar las tareas necesarias | Exige | Sin auditar | |

## 6.14. Gestión clínica veterinaria

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.14-01 | Un módulo de gestión clínica | Exige | Sin auditar | |
| 6.14-02 | Historia clínica: consultas | Exige | Sin auditar | |
| 6.14-03 | … motivo de consulta | Exige | Sin auditar | |
| 6.14-04 | … hallazgos | Exige | Sin auditar | |
| 6.14-05 | … diagnósticos | Exige | Sin auditar | |
| 6.14-06 | … tratamientos | Exige | Sin auditar | |
| 6.14-07 | … evoluciones | Exige | Sin auditar | |
| 6.14-08 | … procedimientos | Exige | Sin auditar | |
| 6.14-09 | … seguimientos | Exige | Sin auditar | |
| 6.14-10 | … exámenes | Exige | Sin auditar | |
| 6.14-11 | … órdenes médicas | Exige | Sin auditar | |
| 6.14-12 | … kardex | Exige | Sin auditar | La fila 6.14 de [lo que falta](../pendiente-en-el-codigo.md) dice que no existe. |
| 6.14-13 | … archivos adjuntos | Exige | Sin auditar | |

## 6.15. Carnet preventivo digital

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.15-01 | Registro preventivo por mascota que permite consultar: vacunaciones | Exige | Sin auditar | |
| 6.15-02 | … desparasitación interna | Exige | Sin auditar | |
| 6.15-03 | … desparasitación externa | Exige | Sin auditar | |
| 6.15-04 | … productos utilizados | Exige | Sin auditar | |
| 6.15-05 | … fechas | Exige | Sin auditar | |
| 6.15-06 | … próximas fechas | Exige | Sin auditar | |
| 6.15-07 | Se alimenta, cuando corresponda, de los servicios realizados desde las rutas preventivas | Exige | Sin auditar | |

## 6.16. Segmentación

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.16-01 | Segmentar usuarios y mascotas por: edad | Ejemplo | Sin auditar | |
| 6.16-02 | … especie | Ejemplo | Sin auditar | |
| 6.16-03 | … plan | Ejemplo | Sin auditar | |
| 6.16-04 | … ciudad | Ejemplo | Sin auditar | |
| 6.16-05 | … zona | Ejemplo | Sin auditar | |
| 6.16-06 | … estado de afiliación | Ejemplo | Sin auditar | |
| 6.16-07 | … grupo familiar | Ejemplo | Sin auditar | |
| 6.16-08 | … servicios | Ejemplo | Sin auditar | |
| 6.16-09 | … condiciones preventivas | Ejemplo | Sin auditar | |
| 6.16-10 | … otros criterios definidos posteriormente | Exige | Sin auditar | |
| 6.16-11 | La segmentación sirve para campañas | Exige | Sin auditar | |
| 6.16-12 | … comunicaciones | Exige | Sin auditar | |
| 6.16-13 | … seguimiento | Exige | Sin auditar | |
| 6.16-14 | … reportes | Exige | Sin auditar | |
| 6.16-15 | … acciones comerciales | Exige | Sin auditar | |

## 6.17. Atención veterinaria virtual

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.17-01 | Registrar solicitudes de orientación | Exige | Sin auditar | |
| 6.17-02 | Asociar la conversación al paciente | Exige | Sin auditar | |
| 6.17-03 | Consultar antecedentes | Exige | Sin auditar | |
| 6.17-04 | Consultar historial | Exige | Sin auditar | |
| 6.17-05 | Registrar la atención | Exige | Sin auditar | |
| 6.17-06 | Generar seguimiento | Exige | Sin auditar | |
| 6.17-07 | Guardar la interacción | Exige | Sin auditar | |
| 6.17-08 | Plantillas y respuestas estructuradas, aprobadas por el equipo médico, para consultas frecuentes | Opcional | Sin auditar | |
| 6.17-09 | La herramienta apoya al profesional y no sustituye el criterio médico veterinario | Exige | Sin auditar | |

## 6.18. Comunicaciones masivas y campañas

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.18-01 | Crear campañas dirigidas a segmentos específicos | Exige | Sin auditar | |
| 6.18-02 | Campañas preventivas | Ejemplo | Sin auditar | |
| 6.18-03 | Recordatorios | Ejemplo | Sin auditar | |
| 6.18-04 | Comunicaciones comerciales | Ejemplo | Sin auditar | |
| 6.18-05 | Información institucional | Ejemplo | Sin auditar | |
| 6.18-06 | Campañas por especie | Ejemplo | Sin auditar | |
| 6.18-07 | Campañas por zona | Ejemplo | Sin auditar | |
| 6.18-08 | Campañas por plan | Ejemplo | Sin auditar | |
| 6.18-09 | Seleccionar audiencia | Exige | Sin auditar | |
| 6.18-10 | Crear mensaje | Exige | Sin auditar | |
| 6.18-11 | Enviar por los canales disponibles | Exige | Sin auditar | |
| 6.18-12 | Registrar interacción cuando la integración lo permita | Exige | Sin auditar | |
| 6.18-13 | Mantener trazabilidad | Exige | Sin auditar | |

## 6.19. Comunicación por WhatsApp

Pide a la propuesta que **indique** cada cosa: se audita que lo que se le dijo a TIMU sea verdad en
el código (la propuesta y [integraciones para TIMU](../integraciones-timu.md)).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.19-01 | Qué integración con WhatsApp ofrece | Propuesta | Sin auditar | |
| 6.19-02 | Si utiliza WhatsApp Business Platform/API | Propuesta | Sin auditar | |
| 6.19-03 | Qué funcionalidades permite | Propuesta | Sin auditar | |
| 6.19-04 | Qué costos adicionales genera | Propuesta | Sin auditar | |
| 6.19-05 | Qué límites existen | Propuesta | Sin auditar | |
| 6.19-06 | Qué automatizaciones permite | Propuesta | Sin auditar | |
| 6.19-07 | Cómo se gestionan las plantillas | Propuesta | Sin auditar | |
| 6.19-08 | Cómo queda registrada la conversación | Propuesta | Sin auditar | |

## 6.20. Encuestas de satisfacción

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.20-01 | Un flujo independiente | Exige | Sin auditar | |
| 6.20-02 | Al culminar un servicio o atención, activar automáticamente una comunicación a la familia por WhatsApp u otro canal | Exige | Sin auditar | |
| 6.20-03 | Flujo: servicio realizado → cierre de atención → envío automático → respuesta → registro → análisis | Exige | Sin auditar | |
| 6.20-04 | Respuesta asociada a la familia | Exige | Sin auditar | |
| 6.20-05 | … a la mascota | Exige | Sin auditar | |
| 6.20-06 | … al servicio | Exige | Sin auditar | |
| 6.20-07 | … a la fecha | Exige | Sin auditar | |
| 6.20-08 | … al profesional, cuando corresponda | Exige | Sin auditar | |
| 6.20-09 | Consultar la información posteriormente | Exige | Sin auditar | |
| 6.20-10 | Exportarla a Excel u otro formato | Exige | Sin auditar | La fila 6.20 de [lo que falta](../pendiente-en-el-codigo.md) dice que no existe. |
| 6.20-11 | Medir satisfacción | Exige | Sin auditar | |
| 6.20-12 | … experiencia | Exige | Sin auditar | |
| 6.20-13 | … calidad percibida | Exige | Sin auditar | |
| 6.20-14 | … posibles inconformidades | Exige | Sin auditar | |
| 6.20-15 | … oportunidades de mejora | Exige | Sin auditar | |

## 6.21. Seguimiento post atención

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.21-01 | Generar automáticamente un seguimiento a la familia tras determinadas atenciones | Exige | Sin auditar | |
| 6.21-02 | Configurar cuándo se realiza | Exige | Sin auditar | |
| 6.21-03 | Enviar comunicación | Exige | Sin auditar | |
| 6.21-04 | Registrar respuesta | Exige | Sin auditar | |
| 6.21-05 | Generar alerta si la familia manifiesta una novedad | Exige | Sin auditar | |
| 6.21-06 | Crear tarea para el equipo | Exige | Sin auditar | |
| 6.21-07 | Mantener trazabilidad | Exige | Sin auditar | |

## 6.22. Gestión con clínicas aliadas

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.22-01 | Registrar solicitudes provenientes de clínicas aliadas | Exige | Sin auditar | |
| 6.22-02 | Flujo: la clínica pide (hospitalización) → TIMU valida plan → beneficio disponible → estado de pago → calcula o indica el descuento → registra la solicitud | Ejemplo | Sin auditar | |
| 6.22-03 | Identificar la familia | Exige | Sin auditar | |
| 6.22-04 | … la mascota | Exige | Sin auditar | |
| 6.22-05 | … el plan | Exige | Sin auditar | |
| 6.22-06 | … el estado de afiliación | Exige | Sin auditar | |
| 6.22-07 | … el estado de pago | Exige | Sin auditar | |
| 6.22-08 | … el beneficio disponible | Exige | Sin auditar | |
| 6.22-09 | … la utilización previa del beneficio | Exige | Sin auditar | |
| 6.22-10 | … el descuento o condición aplicable | Exige | Sin auditar | |
| 6.22-11 | Todo el proceso queda registrado | Exige | Sin auditar | |

## 6.23. Estados de afiliación

**Auditado el 2026-11-24.**

**Lo que hay:**
- El estado de afiliación tiene cinco valores (`backend/app/core/enums.py:19`): `prospecto`,
  `activa`, `en_mora`, `congelada` y `cancelada`. Vive en el contrato y la familia lo copia de su
  contrato vigente (`_sincronizar_familia`, `backend/app/modules/cartera/service.py:249`).
- Los tres primeros cambios los deciden las reglas `cartera.estado`, con días editables en
  Administración: en mora a los 5 días, congelada a los 30 y activa al ponerse al día
  (`backend/app/modules/reglas/datos.py:27`; `reevaluar_estado`, `backend/app/modules/cartera/service.py:258`).
- La cancelación la hace `cartera.cancelar` (`backend/app/modules/cartera/service.py:525`), sola o
  dentro de la baja de la familia.
- **Reproducido el 2026-11-24 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Una familia con una visita a domicilio agendada y su calendario preventivo, tras
  cancelar su contrato, conserva el servicio en `agendado`, que sigue saliendo en `por_rutear` (lo
  que se propone al planear la ruta del día), y sus preventivos siguen en la bandeja.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.23-01 | Estado «Activo» (como mínimo) | Exige | Cumple | `activa`. Se vuelve a él al ponerse al día (`test_estados_por_dias_de_mora_y_reactivacion`, `backend/tests/test_cartera.py:87`). |
| 6.23-02 | Estado «Moroso» | Exige | Cumple | `en_mora`, por regla a los 5 días de mora (misma prueba). |
| 6.23-03 | Estado «Congelado» | Exige | Cumple | `congelada`, por regla a los 30 días: no genera cuotas ni avisos de mora y avisa a la familia (misma prueba; `test_congelada_no_genera_cuotas`, `backend/tests/test_cartera.py:69`). |
| 6.23-04 | Estado «Cancelado» | Exige | Cumple | `cancelada`: anula las cuotas futuras, apaga la tarjeta y corta las remisiones por usar (`test_baja_de_familia_cancela_contrato_y_tarjeta`, `backend/tests/test_cartera.py:526`; `test_contrato_por_api_se_crea_renueva_y_cancela`, `:629`). |
| 6.23-05 | Estado «Retirado» | Exige | Falta | No existe. El indicador «Retiros» del dashboard cuenta los contratos `cancelada` (`backend/app/modules/dashboard/service.py:77`), y «retirar» solo existe para un peludo que sale de un plan de varios (`contratos.retirar_mascota`, 6.3). El documento no dice en qué se diferencia de «Cancelado»: pregunta para TIMU (en el [README](README.md#preguntas-para-timu)). |
| 6.23-06 | Los cambios de estado afectan automáticamente los procesos relacionados | Exige | Parcial | **Lo que sí se ve afectado**: las cuotas y la tarjeta; los avisos de mora, que el proceso diario no manda a una afiliación cancelada ni congelada (`backend/app/modules/cartera/service.py:383` y `:399`); agendar, que se rechaza en mora, congelada o sin contrato (`backend/app/modules/servicios/service.py:98`); los recordatorios de preventivos, que solo reciben los contratos vigentes (`backend/app/modules/preventivos/service.py:437`); los segmentos de campañas (`backend/app/modules/campanas/segmentos.py:27`); y las remisiones al cancelar. **Lo que no**: las visitas ya agendadas, la bandeja de preventivos y las tareas abiertas (ver 07 y 08). El docstring de `familias.cambiar_estado` (`backend/app/modules/familias/service.py:182`) dice que «cartera y servicios se enganchan aquí para propagar sus efectos», pero la función no llama a nada. |
| 6.23-07 | Un usuario cancelado deja de aparecer en tareas preventivas y procesos activos | Ejemplo | **Contradice** | Reproducido (arriba). La bandeja de preventivos no filtra por afiliación ni por baja: `_de_la_bandeja` y `_condicion_vista` solo miran el preventivo (`backend/app/modules/preventivos/service.py:138` y `:153`). Tampoco filtra por `Mascota.activa`, así que un peludo retirado también sigue en ella. Sus visitas agendadas siguen en `por_rutear` (`backend/app/modules/rutas/service.py:98`), que solo mira el servicio, y llegan a la ruta. Sus preventivos quedan `programado` y sus tareas siguen abiertas: el listado de tareas no mira a la familia (`backend/app/modules/tareas/service.py:93`). Hay que decidir cuáles de esas tareas se cierran y cuáles no (una de cobro de lo vencido quizá deba seguir). |
| 6.23-08 | Un usuario congelado tiene los servicios suspendidos según las reglas configuradas | Ejemplo | Parcial | Cuándo se congela lo dice una regla editable (6.23-03), y no se le agenda nada nuevo, ni en el panel ni en el portal (`test_elegibilidad_explica_los_motivos`, `backend/tests/test_servicios.py:123`; `test_el_plan_dice_por_que_no_se_puede_agendar`, `backend/tests/test_portal.py:698`). Pero lo ya agendado no se suspende: sigue en `por_rutear`, por el mismo camino que 07, y no se reprodujo con una congelada porque el código no mira el estado. Además, qué se suspende está fijo en el código y no sale de ninguna regla. Qué sigue disponible en pausa lo tiene que decir TIMU ([pendientes externos](../pendientes-externos.md), «Qué sigue disponible con el plan en pausa o en mora»). |

**Lo que hay que decidir:**
- Qué es «Retirado» frente a «Cancelado» (pregunta para TIMU).
- Al cancelar o congelar, qué pasa con lo que ya está en marcha: las visitas agendadas (¿se
  cancelan, se suspenden o se avisa al equipo?), los preventivos programados y las tareas abiertas.
  Junto con 6.10 y 6.8, es la misma pregunta: los cambios de estado no se propagan a los procesos.
