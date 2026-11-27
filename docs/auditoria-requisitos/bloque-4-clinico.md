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
