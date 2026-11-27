# Bloque 5: comunicación y seguimiento

Las obligaciones de 6.11, 6.16, 6.18, 6.19, 6.20 y 6.21 del [documento de
requerimientos](../documento-requerimientos-funcionales.md), una por fila, con el texto del
documento, en el orden en que se auditan. Método, tipos, veredictos y avance: [README](README.md).
Las rutas de la evidencia son relativas a la raíz del repositorio.

## 6.11. Atención comercial automatizada

**Auditado el 2026-11-27.**

**Lo que hay:**
- **Todo mensaje de WhatsApp que entra lo atiende el bot comercial** (`procesar_entrante`,
  `backend/app/modules/comercial/conversacion.py:161`), salvo la respuesta a una encuesta
  (`backend/app/workers/tasks/comunicaciones.py:30`). Es un árbol de nodos que se edita como dato y
  se valida antes de activarse (`ARBOL_POR_DEFECTO`, `:43`; `validar_arbol`, `:78`).
- **El árbol sembrado** ofrece conocer el plan ideal, las ciudades donde se atiende o un asesor.
  Para el plan pregunta la ciudad, que valida contra el catálogo, y cuántos peludos y de qué
  especie («2 perros y un gato»). Recomienda un plan con su precio y manda el enlace del registro
  en línea.
- **Una pregunta abierta la responde la IA** dentro del guion aprobado; si sale de él, o si el bot
  no entiende tres veces, la conversación pasa a un asesor comercial. Pasa con una tarea que lleva lo
  capturado y los últimos mensajes (`_asesor`, `:352`).
- **Quien escribe queda en el embudo de interesados**, con las etapas nuevo, contactado,
  cotizado, en afiliación, afiliado y perdido. También entra quien deja sus datos en el formulario
  de la portada.
- **La recomendación** (`planes.recomendar`, `backend/app/modules/planes/service.py:250`) evalúa
  las reglas `plan.recomendacion` con la ciudad y los peludos (total, perros, gatos, especies). Salta
  el plan que no esté activo, no se venda en esa ciudad o no cubra las especies; sin regla que
  sirva, da el más económico que cubra a la familia. La única regla sembrada recomienda Mi Amigo
  Fiel, de forma provisional ([pendientes externos](../pendientes-externos.md)).
- **Reproducido el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio.
  - (a) Una familia afiliada escribe «Hola, mi perro está vomitando desde ayer». El bot le responde
    con el menú de ventas («Conocer el plan ideal para mi familia…»), después con «No te entendí»,
    y al tercer mensaje la pasa a un asesor comercial, con una tarea del área comercial.
  - (b) Un plan que solo se vende en Bogotá no se recomienda en Cali. Al añadirle Cali, pasa a
    recomendarse allí.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.11-01 | Flujos de atención y calificación comercial por canales digitales | Exige | Cumple | El bot de WhatsApp con su árbol editable, el embudo con sus etapas, el reparto de interesados por carga y el formulario de la portada (`test_de_hola_a_la_recomendacion_y_la_afiliacion`, `backend/tests/test_comercial.py:112`; `test_arbol_editable_y_validado`, `:185`; `test_reparto_por_carga`, `:202`; `test_quien_escribe_desde_la_portada_entra_al_embudo_con_su_mensaje`, `:473`; `test_los_recuentos_siguen_el_embudo`, `:400`). |
| 6.11-02 | Una familia que entra por WhatsApp u otros canales inicia una interacción guiada | Exige | Parcial | Quien escribe por primera vez recibe el menú y sigue el árbol (mismas pruebas). Pero **hay una sola interacción, la de ventas, y le toca a todo el que escribe**: una familia afiliada que pregunta por su mascota recibe el menú de planes y termina en una tarea comercial (reproducido, a). El bot recibe la familia (`familia_id`) y no la usa para cambiar de camino. Lo que una familia afiliada pide por WhatsApp no llega ni a la orientación virtual (6.17-01) ni a servicio al cliente. |
| 6.11-03 | Información: especie | Opcional | Cumple | De cada peludo, leída del texto (`leer_mascotas`; `test_lectura_de_mascotas`, `:100`). |
| 6.11-04 | Información: edad | Opcional | Falta | No se pregunta. |
| 6.11-05 | Información: sexo | Opcional | Falta | No se pregunta. |
| 6.11-06 | Información: ubicación | Opcional | Cumple | La ciudad, validada contra el catálogo. Sin cobertura, la conversación pasa a un asesor (`_capturar`, `backend/app/modules/comercial/conversacion.py:132`; `test_ciudad_sin_cobertura_va_a_un_asesor`, `backend/tests/test_comercial.py:175`). No se pregunta el barrio. |
| 6.11-07 | Información: necesidades | Opcional | Falta | No se pregunta. La IA responde preguntas abiertas, pero no guarda lo que la persona necesita. |
| 6.11-08 | Información: interés | Opcional | Parcial | Lo dice la etapa del embudo y la opción que elige en el menú, no una pregunta. |
| 6.11-09 | Información: características de la mascota | Opcional | Falta | Solo la especie y cuántas. |
| 6.11-10 | Información: lo relevante para determinar el plan | Opcional | Cumple | La ciudad y los peludos, que es lo que usan la regla y el precio (`test_de_hola_a_la_recomendacion_y_la_afiliacion`). Lo capturado no pasa al registro en línea (6.1-27). |
| 6.11-11 | Reglas configuradas previamente para recomendar el plan más adecuado | Exige | Cumple | Las reglas `plan.recomendacion`, que Administración edita (`test_recomendacion_provisional_es_el_plan_principal`, `backend/tests/test_planes.py:400`). La sembrada es provisional hasta que TIMU diga el criterio. |
| 6.11-12 | La recomendación considera la ciudad | Exige | Cumple | Es un dato de la regla, y un plan que no se vende en la ciudad se salta (`test_recomendacion_salta_plan_de_otra_ciudad`, `:418`). |
| 6.11-13 | … la disponibilidad del plan | Exige | Cumple | Un plan inactivo, fuera de la ciudad o que no cubre las especies no se recomienda (`validar_para_familia`, `backend/app/modules/planes/service.py:236`; misma prueba). |
| 6.11-14 | … las condiciones comerciales vigentes | Exige | Parcial | El precio que se dice es la tarifa vigente para ese número de peludos (`planes.tarifa`). Pero la regla no puede mirar precios, descuentos por periodo ni promociones: su contexto solo tiene la ciudad y los peludos (`PlanRecomendacion`, `backend/app/modules/reglas/contextos.py:140`). El bot no dice el descuento por pagar varios meses. |
| 6.11-15 | … las características del usuario | Exige | Parcial | Solo cuántos peludos y de qué especie: lo demás no se pregunta (04, 05, 07 y 09), así que ninguna regla lo puede usar. |
| 6.11-16 | Un plan no disponible en una ciudad no se recomienda allí | Exige | Cumple | `test_recomendacion_salta_plan_de_otra_ciudad`, y reproducido (b). |
| 6.11-17 | La configuración permite habilitarlo después | Exige | Cumple | Administración le añade la ciudad al plan sin borrar nada (`test_el_administrador_cambia_tarifas_y_ciudades_sin_borrar_nada`, `backend/tests/test_planes.py:341`), y desde entonces se recomienda allí (reproducido, b). |
| 6.11-18 | El usuario puede escoger un plan distinto al recomendado | Exige | Cumple | El enlace del bot lleva al registro en línea sin un plan fijo, y allí se elige el de cada peludo (`backend/app/modules/comercial/conversacion.py:342`; `registro.test.tsx:127`). |

**Lo que hay que decidir:**
- 02: que WhatsApp distinga a quien ya es familia (atención, orientación virtual, servicio al
  cliente) de quien pregunta por un plan.
- 04, 05, 07 y 09 (opcionales) y 15: qué más pregunta el bot, y si la recomendación lo usa.
- 14: si la recomendación tiene que poder mirar precios y promociones.

## 6.16. Segmentación

**Auditado el 2026-11-27.**

**Lo que hay:**
- **Un segmento es una combinación de filtros sobre las familias** (`FiltrosSegmento`,
  `backend/app/modules/campanas/segmentos.py:30`). Todos deben cumplirse, y nunca entra una familia
  dada de baja. Los filtros:
  - de la familia: ciudad, estado de afiliación y origen;
  - del contrato: plan, días de mora, fecha de afiliación y renovación;
  - de los peludos: especie, mínimo de peludos, edad, preventivo vencido o por vencer y su tipo;
  - del barrio, y de los días sin un servicio completado.
- **Comercial lo arma en Campañas** (`frontend/src/features/campanas/FormFiltros.tsx`), lo guarda
  con nombre y ve cuántas familias alcanza, con una muestra de 20 (`previsualizar`, `:166`).
- **Solo se usa para mandar campañas** (6.18): nada más lee un segmento.
- **Comprobado el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio: los filtros de plan, estado y mínimo de peludos, que ninguna prueba del backend
  afirmaba, cuentan bien.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.16-01 | Segmentar usuarios y mascotas por: edad | Ejemplo | Cumple | La edad de sus peludos, en años cumplidos (`test_segmentar_por_zona_edad_y_preventivos`, `backend/tests/test_campanas.py:70`; panel `CampanasPage.secciones.test.tsx:346`). Se segmentan familias, no mascotas: el resultado es la familia que tiene alguna. |
| 6.16-02 | … especie | Ejemplo | Cumple | `test_filtros_combinables`, `:57`; panel `:346`. |
| 6.16-03 | … plan | Ejemplo | Cumple | El de cualquiera de sus peludos con el contrato vigente (comprobado, arriba; panel `CampanasPage.secciones.test.tsx:300`). |
| 6.16-04 | … ciudad | Ejemplo | Cumple | `test_filtros_combinables`. |
| 6.16-05 | … zona | Ejemplo | Cumple | El barrio, sin distinguir mayúsculas ni espacios de más (`test_segmentar_por_zona_edad_y_preventivos`). Como el barrio es texto libre (6.1-06), un mismo barrio escrito de dos formas son dos zonas. |
| 6.16-06 | … estado de afiliación | Ejemplo | Cumple | Comprobado (arriba), y en un segmento guardado (`test_segmento_guardado_muestra_su_alcance`, `:119`). |
| 6.16-07 | … grupo familiar | Ejemplo | Por decidir | Depende de qué es un «grupo familiar», la misma pregunta que 6.3. **Si es la familia con varios peludos: Cumple**, con el mínimo de peludos (comprobado, arriba). **Si son las personas de la familia o un grupo de familias: Falta**: no hay con qué segmentar. |
| 6.16-08 | … servicios | Ejemplo | Parcial | Solo «sin un servicio completado en los últimos N días» (`:148`; `test_filtros_combinables`). No se puede segmentar por qué servicio recibió, ni por lo que tiene agendado o pendiente. |
| 6.16-09 | … condiciones preventivas | Ejemplo | Cumple | Preventivo vencido o que vence en N días, y de qué tipo (`test_segmentar_por_zona_edad_y_preventivos`). Arrastra lo de 6.13: un adulto aparece con todo vencido el día después de afiliarse (6.15-06). |
| 6.16-10 | … otros criterios definidos posteriormente | Exige | Parcial | Ya hay más de los que pide: días de mora, origen, fecha de afiliación, renovación y días sin servicio. Pero un criterio nuevo lo añade un desarrollador en `FiltrosSegmento` y en `consulta` (`:58`); TIMU no lo puede definir. Es el problema de diseño 10. |
| 6.16-11 | La segmentación sirve para campañas | Exige | Cumple | La campaña toma un segmento guardado o sus propios filtros (`test_campana_se_valida_contra_la_plantilla`, `:146`; `test_previsualizacion_con_exclusiones`, `:161`; panel `CampanasPage.secciones.test.tsx:276`). |
| 6.16-12 | … comunicaciones | Exige | Cumple | Las comunicaciones masivas son las campañas, también las recurrentes (`test_campana_recurrente_se_repite_sola`, `:307`). |
| 6.16-13 | … seguimiento | Exige | Falta | Un segmento no crea tareas ni una lista de familias para seguir: solo da el total y una muestra de 20. |
| 6.16-14 | … reportes | Exige | Falta | No se exporta la lista de un segmento, y el dashboard no filtra por segmento (solo por ciudad, Sección 8). Lo único descargable es la lista de destinatarios de una campaña ya enviada (`test_resultados_y_exportacion`, `:254`). |
| 6.16-15 | … acciones comerciales | Exige | Parcial | Sirve para las campañas comerciales a las familias. Pero **los interesados del embudo no se pueden segmentar**: el segmento solo lee familias (`consulta`, `:58`), así que una acción comercial a quien aún no se afilió no pasa por aquí. |

**Lo que hay que decidir:**
- 07: qué es un grupo familiar (con 6.3, pregunta para TIMU).
- 13 a 15: si un segmento tiene que poder crear tareas, exportarse y alcanzar a los interesados.
- 08: por qué servicios se segmenta.

## 6.18. Comunicaciones masivas y campañas

**Auditado el 2026-11-27.**

**Lo que hay:**
- **Una campaña** (`backend/app/modules/campanas/service.py`) toma un segmento guardado o sus
  propios filtros (6.16), una plantilla de WhatsApp aprobada y activa, y la fuente de cada variable:
  el titular, la ciudad, el nombre de la mascota, el plan o un texto fijo (`_validar`, `:53`).
- **Antes de enviar**, muestra cuántas familias alcanza, cuántas se excluyen por haber pedido no
  recibir más y cómo se verá el mensaje. Se manda ahora o se programa, una vez o cada día, semana o
  mes.
- **El envío va a un ritmo que no sature a Meta y respeta las bajas** (`despachar`, `:232`).
- **De cada ejecución queda la lista de destinatarios**, con su estado y su motivo de exclusión, y
  el resultado: enviados, entregados, leídos, respondidos (cualquier mensaje suyo en las 72 horas
  siguientes) y fallidos. La lista se descarga en CSV (`resultados`, `:363`; `detalle`, `:395`).
- **Solo sale por WhatsApp**: la campaña rechaza cualquier otro canal (`:56`), aunque la plataforma
  manda correos para otras cosas.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.18-01 | Crear campañas dirigidas a segmentos específicos | Exige | Cumple | `test_campana_se_valida_contra_la_plantilla`, `backend/tests/test_campanas.py:146`; `test_solo_comercial_o_admin_crean_campanas`, `:172`; panel `CampanasPage.test.tsx:94` y `CampanasPage.secciones.test.tsx:276`. |
| 6.18-02 | Campañas preventivas | Ejemplo | Cumple | Con los filtros de preventivo vencido o por vencer (6.16-09; panel `CampanasPage.secciones.test.tsx:346`). Lo vencido arrastra lo de 6.13: un adulto recién afiliado aparece con todo vencido. |
| 6.18-03 | Recordatorios | Ejemplo | Cumple | Programadas y recurrentes (`test_campana_programada_a_futuro`, `:293`; `test_campana_recurrente_se_repite_sola`, `:307`; panel `CampanasPage.secciones.test.tsx:180`). Aparte están los recordatorios automáticos de preventivos y de mora (6.8-11 y 6.2). |
| 6.18-04 | Comunicaciones comerciales | Ejemplo | Parcial | A las familias, sí. A los interesados del embudo, que aún no son familia, no: el segmento solo alcanza familias (6.16-15). |
| 6.18-05 | Información institucional | Ejemplo | Cumple | Cualquier plantilla aprobada a cualquier segmento, también a todas las familias (`test_filtros_combinables`, `:57`, sin filtros). |
| 6.18-06 | Campañas por especie | Ejemplo | Cumple | 6.16-02. |
| 6.18-07 | Campañas por zona | Ejemplo | Cumple | 6.16-05, con el barrio en texto libre. |
| 6.18-08 | Campañas por plan | Ejemplo | Cumple | 6.16-03. |
| 6.18-09 | Seleccionar audiencia | Exige | Cumple | Por segmento o por filtros, con la vista previa y las exclusiones (`test_previsualizacion_con_exclusiones`, `:161`; `test_envio_al_ritmo_permitido_y_respetando_bajas`, `:199`; `test_baja_posterior_a_congelar_la_audiencia_tambien_se_respeta`, `:219`). |
| 6.18-10 | Crear mensaje | Exige | Cumple | El texto es una plantilla de WhatsApp, como exige Meta para escribirle primero a alguien. Administración la escribe en el panel, en versiones que no se editan, y la campaña elige la plantilla y llena sus variables (`test_campana_se_valida_contra_la_plantilla`; panel `CampanasPage.secciones.test.tsx:262`). La aprobación ocurre en Meta y se copia a mano (6.19-07). Con varios peludos, la variable «mascota» nombra solo al primero (`_variables`, `:97`). |
| 6.18-11 | Enviar por los canales disponibles | Exige | Parcial | Solo WhatsApp (`:56`). El correo es un canal que la plataforma ya usa (`CanalComunicacion.EMAIL`), pero una campaña no puede usarlo. Lo que cuesta cada mensaje no tiene tope en la plataforma ([lo que falta](../pendiente-en-el-codigo.md), fila 6.18 y 6.19). |
| 6.18-12 | Registrar interacción cuando la integración lo permita | Exige | Cumple | Entregado y leído, con los estados que manda Meta, y respondido (`test_resultados_y_exportacion`, `backend/tests/test_campanas.py:254`; panel `CampanasPage.secciones.test.tsx:141`). «Respondido» es cualquier mensaje de esa persona en las 72 horas siguientes, conteste o no a la campaña. |
| 6.18-13 | Mantener trazabilidad | Exige | Cumple | Cada ejecución, cada destinatario con su estado o su motivo de exclusión y su mensaje, y la lista en CSV (`test_resultados_y_exportacion`; `test_cancelar_detiene_lo_pendiente`, `:238`; panel `CampanasPage.secciones.test.tsx:159` y `:230`). |

**Lo que hay que decidir:**
- 11: si las campañas tienen que poder salir por correo.
- 04: si las campañas alcanzan a los interesados (con 6.16-15).

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
