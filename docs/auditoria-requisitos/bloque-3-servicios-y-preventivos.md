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

**Auditado el 2026-11-25.**

**Lo que hay:**
- El médico registra un pendiente desde la ficha del servicio que atiende (`crear_pendiente`,
  `backend/app/modules/servicios/service.py:606`). Lleva una descripción en texto libre y si
  requiere la autorización de la familia (`Pendiente`, `backend/app/modules/servicios/models.py:121`).
  No dice qué servicio es.
- Atención al cliente lo gestiona en Servicios → Pendientes (`frontend/src/features/servicios/ServiciosPage.tsx:70`).
  Registra si la familia lo autorizó o no, y por qué medio. Después lo pasa a gestión y lo marca
  resuelto, con su resolución. La lista dice la descripción, un enlace al servicio de origen y el
  estado; ni la familia ni la mascota.
- La API deja agendar un servicio atado a un pendiente autorizado (`pendiente_id` en
  `POST /servicios`, `backend/app/modules/servicios/router.py:393`). El panel no lo usa: ni el alta
  de un servicio ni la gestión del pendiente lo mandan.
- **Reproducido el 2026-11-25 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Una vacunación, que requiere autorización, nace `pendiente_autorizacion`. «Confirmar
  agenda», el botón verde de su ficha, la pasa a `agendado` sin autorizarla (200). Desde ahí entra
  en lo que se propone para la ruta, y el planificador la mete en la ruta del médico. Al llegar, él
  no puede salir hacia ella (422, «requiere autorización registrada»).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.6-01 | Registrar el pendiente (laboratorio, ecografía, procedimiento, control, seguimiento) asociado a la mascota | Exige | Parcial | Se registra desde la atención, con su descripción y si requiere autorización (`test_pendiente_no_avanza_sin_autorizacion`, `backend/tests/test_servicios.py:271`; panel `ServicioDetallePage.test.tsx:267` y `servicios.test.tsx:228`), y sale en la pestaña Servicios de la familia (6.1-11). Va atado a la mascota solo a través de su servicio de origen: si ese servicio era para toda la familia, el pendiente no tiene mascota. **Es texto libre**: no dice si es un laboratorio, una ecografía o un control, ni a qué tipo de servicio corresponde, y de eso dependen 02, 03 y 07 (la fila 6.6 de [lo que falta](../pendiente-en-el-codigo.md)). |
| 6.6-02 | Identificar cobertura según el plan | Exige | Falta | Sin tipo de servicio no hay con qué mirar el plan. La cobertura solo se comprueba si el pendiente se agenda como servicio (6.5-06), después de que la familia ya autorizó. Además, laboratorio, ecografía y procedimiento no existen como tipos de servicio (`TIPOS_SERVICIO`, `backend/app/modules/catalogos/datos.py:264`): no se pueden agendar ni comprobar. |
| 6.6-03 | Determinar condiciones y/o valor aplicable | Exige | Falta | Nada calcula un valor. El beneficio tiene cobertura, copago y tope por episodio, pero solo se usan para decírselos a la familia (`backend/app/modules/planes/service.py:294`); el único cálculo de lo cubierto es el de las remisiones a una clínica aliada (`backend/app/modules/aliadas/service.py:327`, 6.22). |
| 6.6-04 | Generar tarea para el equipo | Exige | Falta | Crear un pendiente no crea ninguna tarea ni publica nada a lo que una regla pueda engancharse. Lo que hay es la lista de Servicios → Pendientes, que se abre en «pendiente de autorización». No tiene responsable ni vencimiento, y no sale en Tareas ni en el Inicio. |
| 6.6-05 | Facilitar la comunicación con la familia | Exige | Falta | No se le dice nada a la familia, que tampoco ve sus pendientes en el portal. Desde la lista de pendientes no se ve ni a quién llamar: hay que abrir el servicio de origen. Y el equipo no puede escribirle desde el panel (6.2-11). |
| 6.6-06 | Registrar autorización o rechazo | Exige | Cumple | Con quién la tomó, cuándo y por qué medio (WhatsApp, llamada, en persona, portal o correo), y sin autorización no avanza (`autorizar_pendiente`, `backend/app/modules/servicios/service.py:631`; `test_pendiente_no_avanza_sin_autorizacion`; `test_pendiente_rechazado_no_se_agenda`, `backend/tests/test_servicios.py:303`; panel `ServiciosPage.gestion.test.tsx:227` y `:244`). Lo registra el equipo, por lo que la familia le dijo. |
| 6.6-07 | Iniciar programación únicamente cuando corresponda | Exige | Parcial | La API solo deja agendar un servicio atado a un pendiente autorizado o en gestión (`backend/app/modules/servicios/router.py:393`; `test_pendiente_rechazado_no_se_agenda`). Pero **el panel no agenda desde un pendiente**: la gestión solo ofrece pasar a gestión y marcar resuelto, y el alta de un servicio no manda `pendiente_id`. El servicio que se agenda después no queda atado a su pendiente. Autorizar no inicia nada, y ninguna prueba agenda un pendiente autorizado. |
| 6.6-08 | Mantener trazabilidad | Exige | Parcial | El pendiente guarda quién lo autorizó, cuándo, por qué medio y cómo se resolvió, y la base audita cada cambio. El servicio que sale de él lo apunta (`pendiente_origen_id`), pero solo si se agendó por la API (07). Ninguna pantalla muestra la historia del pendiente (problema de diseño 7). |
| 6.6-09 | **No enviar automáticamente a ruta o agenda un servicio que aún requiere autorización o validación de disponibilidad** | Exige | **Contradice** | **Reproducido** (arriba). El grafo deja pasar de `pendiente_autorizacion` a `agendado` (`backend/app/modules/servicios/state_machine.py:16`), y `cambiar_estado` solo exige la autorización para salir en ruta o atender (`backend/app/modules/servicios/service.py:453`). La ficha ofrece ese paso como su acción principal, «Confirmar agenda», a cualquier perfil (`frontend/src/features/servicios/FichaServicio.tsx:181`). Lo que se propone para la ruta solo mira el estado (`por_rutear`, `backend/app/modules/rutas/service.py:98`), y el planificador la mete en la ruta sola. Y antes de eso, mientras espera la autorización, la cita ya está en la agenda con su fecha y ocupa un cupo (6.5-02). |

**Lo que hay que decidir:**
- 01 a 03: que el pendiente diga qué servicio es (un tipo del catálogo, con laboratorio, ecografía y
  procedimiento), para que se mire su cobertura y su valor antes de pedirle la autorización a la
  familia.
- 04, 05 y 07: la tarea que crea, cómo se le comunica a la familia, y que se agende desde el propio
  pendiente.
- 09: que nada que espere autorización llegue a `agendado` ni a una ruta, y si mientras espera
  ocupa un cupo.

## 6.7. Gestión de rutas domiciliarias

**Auditado el 2026-11-25.**

Las filas 02 a 09 son las «variables como…» del documento. Se extrajeron como Exige y aquí pasan a
Ejemplo, como manda el método («como»). Se auditan igual.

**Lo que hay:**
- Operaciones pide la planificación del día para una ciudad, con quiénes salen a campo, y el
  worker la resuelve (`solicitar`, `backend/app/modules/rutas/service.py:65`; `planificar`,
  `:142`). Toma los servicios domiciliarios y preventivos agendados de ese día, sin ruta, y los
  reparte en una ruta por persona con OR-Tools. El optimizador respeta la franja de llegada de
  cada servicio (la hora agendada más 60 minutos), su duración, la jornada (7:00 a 19:00) y un
  máximo de 8 atenciones (`backend/app/core/config.py:120`). Lo que no cabe queda sin asignar,
  con su motivo.
- Los tiempos entre casas salen de la matriz de Google, guardada en caché y con un tope diario. Sin
  clave, se estiman en línea recta (`distancias.matriz`, `backend/app/modules/rutas/distancias.py:71`).
  La llamada usa la Distance Matrix API, que la clave de TIMU no admite: hasta pasarla a la Routes
  API, las rutas caerían siempre a la estimación (fila 6.7 de [lo que falta](../pendiente-en-el-codigo.md)).
- En campo, la ruta se arranca, cada parada se avisa como «en camino», se marca la llegada y la
  salida, y se omite con motivo. Operaciones agrega una parada en caliente donde menos tiempo suma.
  Cada parada abre la navegación del celular («Cómo llegar»,
  `frontend/src/features/rutas/AccionesParada.tsx:61`).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.7-01 | Organizar y optimizar servicios domiciliarios | Exige | Cumple | La planificación y la ejecución de arriba (`test_planificar_agrupa_ordena_y_reporta_lo_que_no_cabe`, `backend/tests/test_rutas.py:189`; `test_dos_tecnicos_se_reparten_la_carga`, `:207`; `test_ejecucion_mueve_el_servicio_y_cierra_la_ruta`, `:264`; `test_en_campo_se_omite_una_parada_y_operaciones_agrega_otra`, `:502`; panel `RutasPage.test.tsx:122` a `:329`). Dos salvedades: con la clave de TIMU los tiempos serían en línea recta (arriba), y lo que espera autorización puede entrar a la ruta (6.6-09). |
| 6.7-02 | Variable: ubicación | Ejemplo | Cumple | Las coordenadas de la familia, geocodificadas al guardar su dirección (6.1-05). Sin ellas, el servicio queda sin asignar, «sin ubicación» (`planificar`, `:159`; `test_planificar_agrupa_ordena_y_reporta_lo_que_no_cabe`). |
| 6.7-03 | Variable: zona | Ejemplo | Parcial | La zona (el barrio, que es texto libre, 6.1-06) se muestra en cada parada, pero no entra en la planificación: se planea por ciudad, y la cercanía la dan las coordenadas. No se puede organizar por zonas, por ejemplo el norte los lunes. |
| 6.7-04 | Variable: tipo de servicio | Ejemplo | Cumple | Solo entran las modalidades que se atienden en casa, domiciliaria y preventiva (`MODALIDADES_EN_CASA`, `:34`), y cada una con la duración de su tipo (05). Las pruebas planean consultas domiciliarias (`test_planificar_agrupa_ordena_y_reporta_lo_que_no_cabe`). |
| 6.7-05 | Variable: duración estimada | Ejemplo | Cumple | La de su tipo de servicio (`_duracion`, `:121`), que el optimizador suma a cada visita (`test_optimizador_respeta_ventanas`, `backend/tests/test_rutas.py:35`). Que TIMU no la pueda cambiar, en 12. |
| 6.7-06 | Variable: disponibilidad | Ejemplo | Cumple | Las personas que Operaciones elige para el día, activas y de un perfil que sale a campo (`test_solo_se_planea_en_ciudades_habilitadas_y_con_quien_sale_a_campo`, `:157`), dentro de la jornada y con su máximo de atenciones (`test_optimizador_respeta_capacidad_y_descarta_lo_imposible`, `:51`). La jornada y el máximo son variables de entorno, iguales para todos: no hay horario por persona (6.5-09). |
| 6.7-07 | Variable: franja horaria | Ejemplo | Cumple | La atención empieza entre la hora agendada y 60 minutos después (`_visita`, `:130`; `test_optimizador_respeta_ventanas`), y a la familia se le avisa esa franja al planear (`test_planificar_avisa_la_ventana_de_llegada`, `:216`). |
| 6.7-08 | Variable: profesional asignado | Ejemplo | Cumple | Una ruta por persona, y cada servicio queda con quien lo atiende (`test_dos_tecnicos_se_reparten_la_carga`; `test_listado_de_rutas_por_dia_ciudad_y_responsable`, `:420`). Es un resultado de la planificación, no un dato que respete: si la familia tiene su médico de siempre, el optimizador no lo sabe. |
| 6.7-09 | Variable: orden de desplazamiento | Ejemplo | Cumple | Cada parada lleva su orden y su llegada estimada, se recalcula al omitir, y una parada nueva se inserta donde menos tiempo agrega (`test_omitir_renumera_y_libera_el_servicio`, `:345`; `test_agregar_inserta_donde_menos_cuesta`, `:360`; `test_insercion_mas_barata_respeta_lo_recorrido`, `:64`). |
| 6.7-10 | Visualizar usuarios/servicios en un mapa | Exige | Falta | No hay mapa: la ruta es una línea de paradas, y cada una abre la navegación del celular. El mapa con Google Maps es una unidad aparte que TIMU eligió y sigue sin construir ([pendientes externos](../pendientes-externos.md#mapa-de-las-rutas-requisito-67-r2-pan-06); fila 6.7 de [lo que falta](../pendiente-en-el-codigo.md)). |
| 6.7-11 | Proponer una secuencia de atención que optimice desplazamientos, considerando ubicación y duración | Exige | Cumple | La secuencia de cada ruta minimiza el tiempo con la matriz de la ciudad, la duración de cada visita y las franjas (`optimizar`, `backend/app/integrations/routing.py:48`; las pruebas de 01, 05 y 09). Con la clave de TIMU sería en línea recta hasta pasar a la Routes API. |
| 6.7-12 | Duración aproximada por tipo de servicio para calcular bloques horarios coherentes | Exige | Parcial | Cada tipo tiene su duración (`duracion_min`, `backend/app/modules/catalogos/models.py:51`), y con ella se parten las franjas en bloques (`disponibilidad`, `backend/app/modules/servicios/service.py:337`; `test_disponibilidad_descuenta_lo_agendado`, «bloques de 45 minutos», `backend/tests/test_servicios.py:79`) y se arma la ruta (05). **Pero TIMU no la puede establecer**: está en el código (`TIPOS_SERVICIO`, `backend/app/modules/catalogos/datos.py:264`) y Administración solo apaga un tipo (6.5-15). Los bloques de la agenda no cuentan el desplazamiento entre casas: con capacidad 1, ofrece 9:00 y 9:45 en dos puntos de la ciudad, y es la franja de llegada de la ruta la que absorbe el trayecto. |

**Lo que hay que decidir:**
- 10: el mapa (unidad aparte, ya decidida con Google Maps).
- 12: que la duración de cada tipo se edite en Administración (con 6.5-15).
- 03 y 08: si la planificación tiene que respetar zonas y el médico de cada familia.
- La jornada y el máximo de atenciones, iguales para todos y fijos en variables de entorno: si
  cambian por persona o por día.

## 6.8. Gestión de servicios preventivos

**Auditado el 2026-11-25.**

**Lo que hay:**
- **El calendario de cada mascota** sale de los esquemas de su especie, que Administración edita
  (`EsquemaPreventivo`, `backend/app/modules/catalogos/models.py:59`; `calendario_inicial`,
  `backend/app/modules/preventivos/service.py:66`). Un cachorro recibe la serie y un adulto, un
  refuerzo. Hay siete esquemas sembrados (`backend/app/modules/catalogos/datos.py:316`): polivalente,
  antirrábica y desparasitación interna para perros y gatos, y desparasitación externa solo para
  perros. Los tipos de preventivo son tres: vacuna, desparasitación interna y externa
  (`TipoPreventivo`, `backend/app/core/enums.py:327`).
- **Cada preventivo está `programado`, `aplicado` o `cancelado`.** Requiere la autorización de la
  familia (6.9) antes de aplicarse.
- **La bandeja de Preventivos los agrupa por familia** (`bandeja`, `:195`), con el teléfono, en las
  vistas «por autorizar», «por agendar», «agendados» y «todos». Las dos primeras toman lo que
  vence en los próximos 30 días (`VENTANA_BANDEJA_DIAS`, `:133`).
- **Cada día a las 9:00, a la familia se le recuerda por WhatsApp** lo que se acerca en los próximos
  7 días, una sola vez y en un solo mensaje (`agenda_diaria`, `:468`). Lo ya vencido no se recuerda.
- **Agendar un preventivo crea su visita** (`agendar`, `:520`). Lo que pasa en la visita le pasa al
  preventivo: completarla lo aplica con el producto, el lote y el peso del paso, y programa la
  dosis siguiente (`_seguir_servicio`, `:555`).
- **Reproducido el 2026-11-25 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Un perro adulto, en un plan que solo incluye la consulta domiciliaria, recibe cuatro
  preventivos (polivalente, antirrábica y las dos desparasitaciones), y la bandeja pide autorizar
  los cuatro. La familia dice que no a la antirrábica, y queda `cancelada`. Volver a calendarizar
  no la crea de nuevo, así que la mascota se queda sin antirrábica.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.8-01 | Identificar automáticamente usuarios próximos a recibir preventivos incluidos o asociados a su plan | Exige | Parcial | **Identifica a los próximos**: en la bandeja (`test_la_bandeja_agrupa_por_familia_con_el_siguiente_paso`, `backend/tests/test_preventivos.py:452`; panel `PreventivosPage.test.tsx:66`), en el Inicio (`DashboardPage.test.tsx:244`) y en el recordatorio (`test_agenda_diaria_avisa_una_sola_vez`, `:221`). **Pero por el esquema de la especie, no por el plan**: ni el calendario, ni la bandeja, ni el recordatorio miran si el plan incluye ese preventivo (reproducido, arriba). Al agendarlo, la elegibilidad lo rechaza (6.5-06), y para entonces ya se le pidió la autorización a la familia. Además, la bandeja sigue mostrando los de una familia cancelada (6.23-07, Contradice). |
| 6.8-02 | Servicio inicial: desparasitación interna | Exige | Cumple | Esquemas para perros y gatos, que se agendan como «Desparasitación» y se aplican con el peso (`test_la_desparasitacion_en_visita_lleva_el_peso_al_carnet`, `backend/tests/test_preventivos.py:401`). |
| 6.8-03 | Servicio inicial: desparasitación externa | Exige | Cumple | Esquema mensual para perros (`can_desp_externa`, `backend/app/modules/catalogos/datos.py:347`), que entra al calendario (reproducido, arriba) y se agenda como la interna. Para gatos no hay esquema sembrado; Administración lo puede crear (`test_esquema_nuevo_desde_el_catalogo_sin_desplegar`, `:67`). |
| 6.8-04 | Servicio inicial: vacunación | Exige | Cumple | La serie del cachorro y el refuerzo del adulto (`test_cachorro_recibe_la_serie_y_el_adulto_un_refuerzo`, `:53`), con su tipo de servicio y sus pasos (`test_completar_la_visita_aplica_el_preventivo`, `:378`). |
| 6.8-05 | Servicio inicial: Bravecto u otros productos preventivos | Exige | Parcial | Bravecto se puede anotar como el producto de una desparasitación externa (el producto es texto libre). Pero **la próxima fecha la da el esquema, no el producto**: el externo sembrado es cada 30 días, y Bravecto dura unas 12 semanas. Un esquema nuevo solo aplica a las mascotas que se calendaricen después. No hay un tipo para otros productos preventivos fuera de los tres. |
| 6.8-06 | Registrar última aplicación | Exige | Cumple | Al aplicarlo queda `aplicado`, con fecha, producto, lote y quién (`aplicar`, `backend/app/modules/preventivos/service.py:359`). Se registra desde la visita o sin visita, por el médico (`test_aplicar_reprograma_la_serie_desde_la_fecha_real`, `backend/tests/test_preventivos.py:118`; `test_completar_la_visita_aplica_el_preventivo`; panel `PreventivosPage.test.tsx:154`). **Lo aplicado fuera** (otra clínica, antes de afiliarse) se registra mal: aplicarlo exige la autorización de la familia para algo ya hecho, y la alternativa que usan las pruebas, cancelarlo con «la familia lo aplicó en otra clínica» (`:512`), termina su serie (14). Va con 6.13. |
| 6.8-07 | Registrar producto | Exige | Cumple | Obligatorio al aplicar, con el lote (el paso «Aplicación», `backend/app/modules/catalogos/datos.py:255`; `test_ciclo_de_vacunacion`, `backend/tests/test_servicios.py:161`). Es texto libre, sin catálogo de productos. |
| 6.8-08 | Registrar fecha | Exige | Cumple | La de aplicación, nunca futura, y la base no deja un `aplicado` sin ella (`CHECK aplicado_con_fecha`, `backend/app/modules/preventivos/models.py:26`; `test_aplicar_reprograma_la_serie_desde_la_fecha_real`). |
| 6.8-09 | Registrar peso cuando sea pertinente | Exige | Cumple | Opcional en la desparasitación. Va al carnet y, si es el más reciente, a la ficha de la mascota (`test_la_desparasitacion_en_visita_lleva_el_peso_al_carnet`; `test_el_peso_de_la_aplicacion_pasa_a_la_ficha_si_es_el_mas_reciente`, `:578`; `test_un_peso_imposible_no_se_registra`, `:188`). |
| 6.8-10 | Determinar próxima fecha | Exige | Cumple | Desde la fecha real de aplicación, con el intervalo de la serie o del refuerzo del esquema (`test_aplicar_reprograma_la_serie_desde_la_fecha_real`). Depende del esquema y no del producto (05). |
| 6.8-11 | Generar alerta | Exige | Cumple | A la familia, el recordatorio de 7 días, que sale cuando su plantilla esté aprobada en Meta (`test_la_agenda_junta_los_peludos_de_una_familia_en_un_mensaje`, `:235`; `test_agenda_sin_plantilla_no_marca_como_avisado`, `:283`). Al equipo, la bandeja, con lo vencido incluido, y el Inicio con los preventivos por autorizar (`DashboardPage.test.tsx:244`). Lo vencido no se le recuerda a la familia (`test_la_agenda_no_recuerda_lo_ya_vencido`, `:267`). |
| 6.8-12 | Contactar a la familia | Exige | Parcial | Lo automático es el recordatorio. Para lo demás, la bandeja da el teléfono de cada familia, y el contacto se hace fuera de la plataforma, que no deja escribirle desde el panel (problema de diseño 8). Que se la contactó no queda en ninguna parte (13). |
| 6.8-13 | Registrar respuesta | Exige | Parcial | Solo dos respuestas: autorizó o no autorizó, con quién la registró, cuándo y por qué medio (`autorizar`, `backend/app/modules/preventivos/service.py:320`; `test_rechazo_de_la_familia_cancela`, `backend/tests/test_preventivos.py:146`; panel `PreventivosPage.test.tsx:91`). No caben «no contestó», «más adelante» ni «ya se lo pusieron». Es el problema de diseño 2. |
| 6.8-14 | Reprogramar si no desea el servicio | Exige | **Contradice** | **Reproducido** (arriba). Si la familia no lo quiere ahora, el panel solo ofrece «No autorizó» o cancelarlo con un motivo. Las dos cosas lo dejan `cancelado` (`:320` y `:425`), y la dosis siguiente solo nace al aplicar (`aplicar`, `:359`): **la serie de ese esquema se acaba**. Volver a calendarizar tampoco la recupera, porque cuenta como programado cualquier esquema que la mascota ya tuvo (`calendario_inicial`, `:66`). No hay cómo mover la fecha de un preventivo; solo se reprograma su visita, una vez agendada. |
| 6.8-15 | Incorporar a ruta cuando sea autorizado | Exige | Cumple | Lo autorizado se agenda desde la bandeja como una visita en casa (modalidad preventiva), que entra a la ruta (6.7-04), y la visita nace autorizada (`test_agendar_crea_el_servicio`, `:307`; `test_la_visita_de_un_preventivo_autorizado_nace_autorizada`, `:354`; panel `PreventivosPage.test.tsx:110`). La API deja agendar uno sin autorizar, y su visita puede llegar a la ruta por el atajo de 6.6-09. |
| 6.8-16 | Actualizar automáticamente la próxima fecha una vez realizado el servicio | Exige | Cumple | Completar la visita aplica el preventivo con lo registrado en su paso y programa la dosis siguiente (`test_completar_la_visita_aplica_el_preventivo`; `_seguir_servicio`, `backend/app/modules/preventivos/service.py:555`). |

**Lo que hay que decidir:**
- 14: que «no lo quiere ahora» mueva la fecha en vez de cancelar, y qué pasa con la serie cuando de
  verdad no lo quiere.
- 01: que el calendario, la bandeja y el recordatorio miren lo que incluye el plan.
- 05: que la próxima fecha pueda depender del producto (Bravecto), y qué otros productos maneja
  TIMU.
- 06, 12 y 13: cómo se registra lo aplicado fuera y la respuesta de la familia (con 6.13 y el
  problema de diseño 2).

## 6.9. Autorización de servicios preventivos

**Auditado el 2026-11-25.**

**Lo que hay:**
- **No hay un formulario de autorización.** La autorización llega por dos caminos.
  - El equipo la registra en la bandeja por lo que la familia le dijo, con el medio: WhatsApp,
    teléfono, en persona, portal o «formulario», que es una opción de la lista sin formulario
    detrás (`backend/app/modules/preventivos/router.py:99`).
  - La familia agenda la visita de un preventivo concreto en el portal, y agendarla cuenta como su
    autorización, con el medio «portal» (`agendar_desde_el_portal`,
    `backend/app/modules/preventivos/service.py:803`).
- **El recordatorio de 7 días** (6.8-11) dice el titular, los peludos, los preventivos y la fecha.
  No lleva un enlace para autorizar ni para agendar.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.9-01 | Autorización de la familia **mediante formulario** antes de determinados preventivos | Exige | Parcial | **Lo que hay**: sin autorización registrada, un preventivo que la requiere no se aplica (`test_sin_autorizacion_no_se_aplica`, `backend/tests/test_preventivos.py:105`). Qué esquemas la requieren lo decide cada esquema (`requiere_autorizacion`). **Lo que falta es el formulario**: la familia no llena nada. O le dice algo al equipo, que lo anota, o agenda en el portal, donde solo elige la visita y una observación (`test_la_familia_agenda_un_preventivo_concreto`, `backend/tests/test_portal.py:729`). Si agendar en el portal cuenta como el formulario es una equivalencia por decidir, y qué debe preguntar el formulario de TIMU ya está en la primera tanda de preguntas (6.12-06 y 6.13). |
| 6.9-02 | Flujo: el sistema identifica el servicio próximo → comunicación → formulario de autorización → revisión → autorización/reprogramación → programación → realización | Exige | Parcial | Están la identificación (6.8-01, sin mirar el plan), la comunicación (el recordatorio, sin enlace), la autorización, la programación (la visita) y la realización (la visita completada aplica el preventivo, 6.8-16). **Faltan** el formulario (01) y la revisión: lo que la familia agenda en el portal queda autorizado sin que nadie lo revise. **La reprogramación va al revés**: «no» cancela el preventivo y termina su serie (6.8-14, Contradice). |
| 6.9-03 | Lo que da la familia queda registrado y asociado a la mascota | Exige | Cumple | La autorización o el rechazo quedan en el preventivo, que es de la mascota: quién los registró (el usuario del equipo o el de la familia en el portal), cuándo y por qué medio (`autorizar`, `backend/app/modules/preventivos/service.py:320`; `test_flujo_http_autorizar_y_aplicar`, `backend/tests/test_preventivos.py:166`; `test_autorizar_varios_es_todo_o_nada`, `:512`; `test_la_familia_agenda_un_preventivo_concreto`). La observación del portal va a la visita. Hoy la familia no da más que eso: lo que pregunte el formulario (01) no tiene dónde quedar. |

**Lo que hay que decidir:**
- 01 y 02: si agendar en el portal es el formulario o hace falta uno que pregunte algo (el estado de
  la mascota, lo aplicado fuera, el consentimiento), con su enlace en el recordatorio y una
  revisión del equipo. Depende de los formularios que comparta TIMU.

## 6.13. Alimentación automática del calendario preventivo

**Auditado el 2026-11-25.**

Las filas 01 a 05 son los datos que el documento da «como» ejemplo: se extrajeron como Exige y aquí
pasan a Ejemplo, como manda el método. Se auditan igual.

**Lo que hay:**
- **El calendario se crea solo al afiliar**: al completarse el registro en línea o la afiliación
  desde el panel (`_calendario_preventivo`, `backend/app/modules/afiliaciones/service.py:415`), al
  agregar un peludo con el contrato vigente (`backend/app/modules/afiliaciones/ciclo.py:61`) y a
  pedido (`backend/app/modules/preventivos/router.py:217`). El contrato directo
  (`POST /cartera/contratos`) no lo crea, pero ninguna pantalla lo usa.
- **Sale solo del esquema de la especie y de la fecha de nacimiento** (`fechas_esquema`,
  `backend/app/modules/preventivos/service.py:44`). Un cachorro recibe la serie desde su edad
  mínima. Un adulto, o uno sin fecha de nacimiento, recibe cada refuerzo el día de la afiliación.
- **Ni la afiliación en línea ni el alta del panel preguntan nada preventivo.** Piden, por peludo,
  nombre, especie, raza, sexo, nacimiento, peso y si está esterilizado (`MascotaBase`,
  `backend/app/modules/familias/schemas.py:20`; 6.12-06).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.13-01 | Lo dado en la afiliación alimenta el calendario: última desparasitación | Ejemplo | Falta | La afiliación no lo pregunta (arriba), y el calendario no tiene de dónde tomarlo. |
| 6.13-02 | … producto utilizado | Ejemplo | Falta | Igual que 01. Además, la próxima fecha depende del esquema y no del producto (6.8-05). |
| 6.13-03 | … fecha | Ejemplo | Falta | Igual que 01. |
| 6.13-04 | … peso | Ejemplo | Parcial | La afiliación pide el peso y lo guarda en la ficha (6.12-03), pero el calendario no lo usa: ni en las fechas ni como dato del preventivo. El peso de cada desparasitación se anota al aplicarla (6.8-09). |
| 6.13-05 | … vacunación | Ejemplo | Falta | Igual que 01. |
| 6.13-06 | Calcular o identificar la fecha correspondiente | Exige | Parcial | Calcula las fechas del esquema desde la edad (`test_cachorro_recibe_la_serie_y_el_adulto_un_refuerzo`, `backend/tests/test_preventivos.py:53`; `test_fechas_esquema_respeta_la_edad_minima`, `:754`). **Sin la última aplicación, a todo adulto le programa cada refuerzo el día que se afilia**: la misma prueba lo afirma (`refuerzo.fecha_programada == HOY`, `:64`). A una perra vacunada el mes pasado se le vuelve a programar la vacuna, y corregirlo deja mal la serie (6.8-06). La prueba del registro solo afirma que hay preventivos (`preventivos > 0`, `backend/tests/test_registro.py:266`). |
| 6.13-07 | Generar las tareas necesarias | Exige | Parcial | Lo programado llega al equipo como el trabajo de la bandeja de preventivos y su recuento en el Inicio (6.8-01 y 6.8-11), no como tareas. Nada genera la tarea de pedirle a la familia el carnet o lo aplicado antes de afiliarse, que es lo que haría falta mientras la afiliación no lo pregunte. |

**Lo que hay que decidir:**
- 01 a 06: qué preventivo pregunta la afiliación y cómo ajusta el calendario (con 6.12-06 y el
  formulario que comparta TIMU, primera tanda de preguntas). Es el problema de diseño 3.
- 07: si mientras tanto la afiliación crea una tarea para pedir el carnet.
