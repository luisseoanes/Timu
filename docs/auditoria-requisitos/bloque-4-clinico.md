# Bloque 4: lo clínico

Las obligaciones de 6.14, 6.15 y 6.17 del [documento de
requerimientos](../documento-requerimientos-funcionales.md), una por fila, con el texto del
documento, en el orden en que se auditan. Método, tipos, veredictos y avance: [README](README.md).
Las rutas de la evidencia son relativas a la raíz del repositorio.

## 6.14. Gestión clínica veterinaria

**Auditado el 2026-11-27.**

**Lo que hay:**
- **Clínica es el espacio del médico** (Sección 12): busca la mascota, abre su historia y escribe
  sus consultas. Administración la lee completa; el resto del equipo, un resumen (cuándo, por qué y
  quién); la familia la ve en el portal, firmada y sin las notas internas (`vista_para`,
  `backend/app/modules/clinica/service.py:72`).
- **Cada consulta es una entrada de la historia** (`HistoriaClinica`,
  `backend/app/modules/clinica/models.py:20`), presencial, domiciliaria o virtual, atada a su visita
  si la tiene. Se recorre por apartados (`ESTACIONES`, `frontend/src/features/clinica/consulta.ts:4`):
  motivo de consulta, anamnesis, examen físico, diagnóstico y tratamiento, más notas internas.
  Puede partir de una plantilla del equipo médico.
- **Para firmarla hace falta el diagnóstico**, y una firmada no se edita, ni siquiera por SQL: se
  corrige con una versión nueva y la anterior queda «corregida».
- **De cada entrada cuelgan sus adjuntos** (exámenes o imágenes, JPG, PNG, WEBP o PDF, que se abren
  con una URL firmada) **y sus fórmulas médicas en PDF.** Las dos cosas salen además en la pestaña
  Documentos de la familia.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.14-01 | Un módulo de gestión clínica | Exige | Cumple | El espacio Clínica, con la historia por mascota, las consultas, las plantillas y la atención virtual, solo para el médico (`test_solo_el_medico_escribe`, `backend/tests/test_clinica.py:342`; `test_solo_el_personal_medico_lee_la_historia`, `:352`; `test_el_medico_busca_la_mascota_sin_abrir_familias`, `:363`; panel `clinica.test.tsx:48` y `:441`). |
| 6.14-02 | Historia clínica: consultas | Exige | Cumple | Cada atención es una entrada con fecha, tipo, profesional y visita. Pasa de borrador a firmada, y se corrige en versiones (`test_firmada_no_se_edita_se_corrige_con_version`, `backend/tests/test_clinica.py:90`; `test_una_historia_firmada_no_se_edita_ni_por_sql`, `backend/tests/test_persistencia.py:748`; panel `clinica.test.tsx:72`, `:107` y `:298`). |
| 6.14-03 | … motivo de consulta | Exige | Cumple | Su primer apartado. Sin él no nace la entrada (`crear_entrada`, `backend/app/modules/clinica/service.py:268`; panel `clinica.test.tsx:72`, «nace al dejar el motivo»). |
| 6.14-04 | … hallazgos | Exige | Por decidir | Se escriben en el apartado «Examen físico» («Lo que encuentras al examinar…»), con la anamnesis aparte, y el propio código los trata como hallazgos: al firmar, el paso «hallazgos» de la visita se llena con el examen físico y el diagnóstico (`_PASOS_DESDE_LA_CONSULTA`, `:56`; `test_firmar_la_consulta_de_la_visita_registra_los_pasos_del_servicio`, `backend/tests/test_clinica.py:608`). Es la equivalencia «examen físico = hallazgos», por aprobar. |
| 6.14-05 | … diagnósticos | Exige | Cumple | Su apartado, que la firma exige (`test_firmar_exige_diagnostico`, `:122`; panel `EntradaPage.test.tsx:105`). Es texto libre, sin catálogo de diagnósticos. |
| 6.14-06 | … tratamientos | Exige | Cumple | Su apartado («Plan» en el celular), que la visita pide para cerrarse (`test_sin_tratamiento_el_plan_del_servicio_sigue_pendiente`, `:644`; panel `clinica.test.tsx:212`), y la fórmula médica (11). |
| 6.14-07 | … evoluciones | Exige | Parcial | No hay apartado ni tipo de entrada para la evolución. Se registra como una consulta más de la mascota, que la historia ordena por fecha (`historia`, `backend/app/modules/clinica/service.py:416`), pero sin vínculo con la consulta que sigue: no se ve qué evoluciones son de qué episodio. |
| 6.14-08 | … procedimientos | Exige | Parcial | Solo caben como texto dentro de un apartado (el tratamiento o el examen) o como una consulta más. No hay un registro del procedimiento: qué se hizo, cuándo, quién y con qué. El pendiente de un procedimiento también es texto libre (6.6-01). |
| 6.14-09 | … seguimientos | Exige | Parcial | En la historia, un seguimiento es una consulta más, por ejemplo virtual. Lo que responde la familia al seguimiento posterior a la atención (6.21) queda en su encuesta y, si preocupa, crea una tarea para servicio al cliente (`_alertar`, `backend/app/modules/encuestas/service.py:229`), pero no llega a la historia de la mascota. El control posterior existe como tipo de servicio (`control_post`), sin relación con la consulta que lo pidió. |
| 6.14-10 | … exámenes | Exige | Cumple | El resultado se adjunta a la entrada con su descripción, también después de firmarla (`adjuntar`, `:433`; `test_adjunto_solo_por_url_firmada_y_con_permiso`, `backend/tests/test_clinica.py:421`; panel `EntradaPage.test.tsx:219`). Es un archivo, sin datos estructurados del examen. Pedir un examen es otra cosa (11). |
| 6.14-11 | … órdenes médicas | Exige | Parcial | **La fórmula médica**, en PDF, con medicamento, presentación, dosis, frecuencia, duración e indicaciones (`emitir_formula`, `:489`; `test_formula_en_pdf`, `backend/tests/test_clinica.py:456`; panel `clinica.test.tsx:312`). **Las órdenes de examen o de procedimiento no existen como orden**: lo más cercano es el pendiente de la atención, que es texto libre (6.6-01). |
| 6.14-12 | … kardex | Exige | Falta | No hay registro de la medicación administrada: qué, cuándo, cuánto y quién la dio ([lo que falta](../pendiente-en-el-codigo.md), fila 6.14). La fórmula dice lo que se receta, no lo que se administró. |
| 6.14-13 | … archivos adjuntos | Exige | Cumple | Por entrada, con tipos permitidos y URL firmada solo para quien ve la historia completa (`test_adjunto_solo_por_url_firmada_y_con_permiso`; `test_adjunto_rechaza_tipo_no_permitido`, `:443`; panel `EntradaPage.test.tsx:198` y `:219`). La familia los ve una vez firmada la entrada (`test_una_familia_no_ve_historias_en_borrador`, `backend/tests/test_persistencia.py:896`). |

**Lo que hay que decidir:**
- 04: la equivalencia «examen físico = hallazgos».
- 07 a 09 y 11: si la historia necesita episodios (una consulta con sus evoluciones, controles y
  seguimientos), un registro de procedimientos y órdenes de examen, o si basta con consultas
  sueltas y texto libre. Va con 6.6-01, el pendiente que es texto libre.
- 12: el kardex, ya anotado en [lo que falta](../pendiente-en-el-codigo.md).

## 6.15. Carnet preventivo digital

**Auditado el 2026-11-27.**

**Lo que hay:**
- **El carnet de cada mascota** (`carnet`, `backend/app/modules/preventivos/service.py:626`) separa
  lo aplicado, lo vencido (programado con fecha pasada) y lo próximo. Nada programado figura como
  aplicado.
- **Lo ven** el médico y Atención en el panel, y la familia en el portal, solo los de sus
  mascotas.
- **El PDF tiene una tabla por tipo** (`backend/app/modules/preventivos/documento.py:18`):
  - Vacunación: vacuna, dosis, fecha, producto, lote, próxima y quién aplicó.
  - Desparasitación interna y externa: fecha, peso, producto, lote, próxima y quién aplicó.
  - Lo pendiente, aparte.
- **Cada PDF lleva un código.** Con él un tercero lo verifica sin entrar al sistema, y ve lo que el
  carnet decía al emitirse (`emitir_carnet`, `:670`; `verificar_carnet`, `:705`).
- **Reproducido el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Un perro adulto afiliado ayer tiene los cuatro refuerzos programados para el día de
  la afiliación (6.13-06). Hoy su carnet, y la verificación pública que vería otra clínica o un
  hotel canino, los dice vencidos: polivalente, antirrábica y las dos desparasitaciones.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.15-01 | Registro preventivo por mascota que permite consultar: vacunaciones | Exige | Cumple | Su tabla, con la dosis y si es refuerzo (`test_carnet_separa_aplicado_vencido_y_proximo`, `backend/tests/test_preventivos.py:531`; `test_carnet_de_sus_mascotas`, `backend/tests/test_portal.py:179`; panel `PreventivosPage.test.tsx:207`). |
| 6.15-02 | … desparasitación interna | Exige | Cumple | Su tabla, con el peso de cada una (`test_el_carnet_lleva_el_peso_de_cada_desparasitacion`, `backend/tests/test_preventivos.py:553`). |
| 6.15-03 | … desparasitación externa | Exige | Cumple | Su tabla, armada igual que la interna (`filas_seccion`, `backend/app/modules/preventivos/documento.py:40`), y en lo pendiente (`test_carnet_separa_aplicado_vencido_y_proximo`, con una externa vencida). |
| 6.15-04 | … productos utilizados | Exige | Cumple | Producto y lote de cada aplicación (`test_completar_la_visita_aplica_el_preventivo`, `backend/tests/test_preventivos.py:378`; panel `PreventivosPage.test.tsx:207`, «Drontal · 8,4 kg · aplicó…»). |
| 6.15-05 | … fechas | Exige | Cumple | La de aplicación de cada uno y la programada de lo pendiente (`test_carnet_separa_aplicado_vencido_y_proximo`; `test_la_verificacion_dice_lo_pendiente_como_el_carnet_impreso`, `:710`). |
| 6.15-06 | … próximas fechas | Exige | Parcial | La columna «Próxima» de cada aplicación y la sección de lo pendiente (mismas pruebas). Pero **solo son ciertas para lo que se aplicó en la plataforma**: a un adulto le marca vencido lo que pudo recibir antes de afiliarse, también en la verificación que ve un tercero (reproducido, arriba; la causa es 6.13-06). Y lo que la familia no autorizó desaparece sin próxima fecha (6.8-14). |
| 6.15-07 | Se alimenta, cuando corresponda, de los servicios realizados desde las rutas preventivas | Exige | Cumple | Completar la visita de un preventivo lo aplica con el producto, el lote y el peso de su paso, y pasa al carnet (`test_completar_la_visita_aplica_el_preventivo`; `test_la_desparasitacion_en_visita_lleva_el_peso_al_carnet`, `:401`). Desde la ruta, registrar la atención de una vacunación lleva al servicio (panel `RutasPage.test.tsx:283`). |

**Lo que hay que decidir:**
- 06: qué dice el carnet mientras no se sepa lo que la mascota recibió antes de afiliarse (con
  6.13). Hoy le dice «vencido» a un tercero.

## 6.17. Atención veterinaria virtual

**Auditado el 2026-11-27.**

**Lo que hay:**
- **La solicitud de orientación** (`SolicitudVirtual`, `backend/app/modules/clinica/models.py:134`)
  la manda la familia desde el portal, o la registra el médico en el panel con su canal (portal,
  WhatsApp o panel) y su prioridad. Pide un plan vigente y la mascota activa (`solicitar_virtual`,
  `backend/app/modules/clinica/service.py:543`).
- **El médico la toma de una cola, lo urgente primero, y la responde** con una respuesta tipo
  aprobada por el equipo médico, cuyas variables completa (`responder`, `:592`). La respuesta queda
  como una consulta virtual firmada en la historia de la mascota y le llega a la familia: como texto
  si la ventana de WhatsApp está abierta, o como aviso con plantilla si no.
- **La IA le puede preparar un borrador al médico**, que nunca se envía. Lo arma con la especie, la
  raza, la edad, el peso y el motivo, no con la historia (`borrador_veterinario`,
  `backend/app/modules/ia/service.py:347`).
- **Toda respuesta sale de una plantilla aprobada**: el médico no escribe una propia. Solo
  `datos_demo` siembra una, en local y en staging. En producción no habrá ninguna, y no se podrá
  responder hasta que el equipo cree y apruebe la primera.
- **Reproducido el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Con un plan que no incluye la orientación virtual se aceptan tres solicitudes
  seguidas. Responder y cerrar una no deja ninguna tarea ni encuesta de seguimiento.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.17-01 | Registrar solicitudes de orientación | Exige | Cumple | Desde el portal y desde el panel, con cola por prioridad (`test_ciclo_virtual_queda_en_la_historia`, `backend/tests/test_clinica.py:507`; `test_cola_prioriza_lo_urgente`, `:569`; `test_virtual_requiere_plan_vigente`, `:584`; portal `PortalPages.secciones.test.tsx:132`). Dos salvedades. **No mira lo que cubre el plan**: ni si incluye la orientación ni su cupo (reproducido, arriba). Y lo que llega por WhatsApp no crea la solicitud sola: el médico la registra a mano. |
| 6.17-02 | Asociar la conversación al paciente | Exige | Parcial | La solicitud es de la mascota, y su respuesta queda en la historia de esa mascota. Pero la conversación son una pregunta y una respuesta: otra pregunta de la familia es otra solicitud. Los mensajes de WhatsApp quedan con la familia, no con la mascota ni con la solicitud (`Mensaje.familia_id`, `backend/app/modules/comunicaciones/models.py:65`). |
| 6.17-03 | Consultar antecedentes | Exige | Cumple | El médico abre la historia completa y el carnet de la mascota desde Clínica (`test_el_medico_busca_la_mascota_sin_abrir_familias`, `backend/tests/test_clinica.py:363`; panel `clinica.test.tsx:48`). Desde la solicitud no hay enlace a ellos mientras la atiende, solo a la consulta ya respondida, y el borrador de la IA no los usa. |
| 6.17-04 | Consultar historial | Exige | Cumple | La historia lista todas las consultas de la mascota, también las virtuales (`test_ciclo_virtual_queda_en_la_historia`). En la ficha de la familia, las orientaciones virtuales no salen (6.1-13). |
| 6.17-05 | Registrar la atención | Exige | Cumple | Consulta virtual firmada, con el motivo, el diagnóstico (opcional), la respuesta como tratamiento y las notas internas, quién y cuándo (`test_ciclo_virtual_queda_en_la_historia`; `test_respuesta_virtual_va_por_texto_si_la_ventana_esta_abierta`, `:545`; panel `clinica.test.tsx:391`). |
| 6.17-06 | Generar seguimiento | Exige | Falta | Responder y cerrar no deja nada después (reproducido, arriba). La orientación no es un servicio, así que no le llega la encuesta (6.20) ni el seguimiento posterior (6.21), y no crea ninguna tarea. Tampoco gasta el cupo del beneficio. |
| 6.17-07 | Guardar la interacción | Exige | Cumple | La solicitud guarda el motivo, la respuesta y la plantilla de la que salió, quién la tomó y cuándo, y el borrador de la IA. El mensaje enviado queda en las comunicaciones de la familia (`test_respuesta_virtual_va_por_texto_si_la_ventana_esta_abierta`). Lo que la familia escriba por WhatsApp fuera de eso no queda con la solicitud (02). |
| 6.17-08 | Plantillas y respuestas estructuradas, aprobadas por el equipo médico, para consultas frecuentes | Opcional | Cumple | Las respuestas tipo, con variables, pasan de borrador a aprobada o retirada, y la aprueba un médico (`aprobar_respuesta`, `backend/app/modules/clinica/service.py:677`; `test_respuesta_con_variables_mal_declaradas`, `backend/tests/test_clinica.py:499`; panel `ClinicaPage.pestanas.test.tsx:342`). **Va más allá de lo que dice el documento**: no son una ayuda para las consultas frecuentes sino la única forma de responder. Cualquier médico aprueba, también la que él mismo escribió. Una plantilla que solo diga `{{1}}` permitiría responder libre, pero eso ya no es una respuesta aprobada. |
| 6.17-09 | La herramienta apoya al profesional y no sustituye el criterio médico veterinario | Exige | Cumple | El borrador de la IA no se envía nunca: queda en la solicitud para que el médico lo lea (`test_borrador_para_el_profesional_nunca_se_envia`, `backend/tests/test_ia.py:273`). La respuesta la elige, la completa y la firma el médico. |

**Lo que hay que decidir:**
- 08: si toda respuesta tiene que salir de una plantilla aprobada, como hoy, o solo las de
  consultas frecuentes, como dice el documento. Y quién aprueba.
- 06: qué seguimiento deja una orientación virtual (con 6.20 y 6.21).
- 01: si la orientación consume un beneficio del plan, con su cupo.
- 02: si la conversación de WhatsApp se ata a la mascota o a la solicitud.
