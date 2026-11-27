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

**Auditado el 2026-11-27.**

Pide a la propuesta que **indique** cada cosa: se audita que lo que se le dijo a TIMU sea verdad en
el código. Lo que se le dijo está en la [propuesta](../propuesta-timu-puntos-15-19.md) (tabla B y
sección C) y en la sección 3.1 de [integraciones para TIMU](../integraciones-timu.md), con su
corrección del 22 de noviembre.

**Lo que hay:**
- **La plataforma habla directo con la Cloud API de Meta** (`backend/app/integrations/whatsapp.py:37`,
  `graph.facebook.com`). Manda plantillas aprobadas y, dentro de las 24 horas desde el último
  mensaje de la persona, texto libre (`encolar_texto`, `backend/app/modules/comunicaciones/service.py:237`).
- **Por el webhook recibe los mensajes y los estados de entrega**, y comprueba la firma de Meta
  (`X-Hub-Signature-256`, `whatsapp.py:24`).
- **Cada mensaje entrante se guarda con la familia de ese número**, si la hay (`_registrar_entrante`,
  `service.py:417`). Después pasa a quien lo atiende: la encuesta, si es su respuesta, o el bot
  comercial (6.11).
- **Las plantillas se escriben en el panel en versiones que no se editan** (`crear_version_plantilla`,
  `:86`). Su paso a «aprobada» lo marca Administración a mano, después de aprobarla en Meta
  (`cambiar_estado_plantilla`, `:112`): la plataforma no las envía a Meta ni se entera si Meta
  cambia su estado después. Las que manda el código se declaran (`declarar_plantilla`), y el Inicio
  del administrador dice cuáles faltan.
- **Reproducido el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Una familia afiliada escribe y pide un asesor, y el asesor le contesta desde la
  bandeja de Comercial. La ficha de la familia muestra los dos mensajes de ella y los dos del bot,
  pero no el del asesor: es el único de la conversación que se guarda sin la familia
  (`backend/app/modules/comercial/router.py:290`, que no le pasa `familia_id`).

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.19-01 | Qué integración con WhatsApp ofrece | Propuesta | Cumple | Se dijo la Cloud API oficial de Meta, «integración directa, sin intermediarios», y es lo que hay en el código. La corrección del 22 de noviembre le dijo a TIMU que la ruta recomendada, la del número actual en coexistencia, necesita un socio de Meta (360dialog). Con ella deja de ser directa y el conector cambia ([lo que falta](../pendiente-en-el-codigo.md), fila 6.17 y 6.19). |
| 6.19-02 | Si utiliza WhatsApp Business Platform/API | Propuesta | Cumple | La Cloud API de WhatsApp Business Platform (`whatsapp.py:37`). |
| 6.19-03 | Qué funcionalidades permite | Propuesta | Parcial | Son verdad: los avisos con plantillas, la regla de las 24 horas (`test_texto_libre_solo_dentro_de_la_ventana`, `backend/tests/test_comunicaciones.py:364`), el bot comercial (6.11), la encuesta por WhatsApp (6.20), los estados de entrega (`test_estados_de_entrega_avanzan_sin_retroceder`, `:273`), las bajas (`test_pedir_baja_excluye_de_envios_masivos`, `:386`), la firma de Meta (`test_webhook_valida_firma_de_meta`, `:345`), los tokens tapados (`test_el_equipo_no_lee_los_tokens_de_los_enlaces_de_un_solo_uso`, `:238`) y los enlaces que salen también por correo. **No es verdad, para una familia, que «cada conversación queda en la ficha»**: la respuesta del asesor no llega (reproducido, arriba; ver 08). Lo multimedia se anota con el tipo que da Meta («[image]», «[audio]»), no «[imagen]» como dice el documento. |
| 6.19-04 | Qué costos adicionales genera | Propuesta | Externo | Las tarifas son de Meta, que las revisa cada trimestre, y no se comprueban en el código: se verifican en la web antes de volver a mandarle el documento a TIMU. Lo que sí es del código: la plataforma no estima ni limita lo que gasta ([lo que falta](../pendiente-en-el-codigo.md), fila 6.18 y 6.19, que TIMU tiene que elegir). |
| 6.19-05 | Qué límites existen | Propuesta | Cumple | Los que se dijeron son de Meta: las 24 horas, que el código respeta (`ventana_abierta`, `service.py:177`), y las 250 personas al día sin verificar la empresa. La plataforma reparte el envío de las campañas por minuto, pero no lleva la cuenta de ese tope diario: pasado el tope, los mensajes fallan en Meta y quedan como fallidos (`test_fallo_reportado_por_meta`, `:292`). |
| 6.19-06 | Qué automatizaciones permite | Propuesta | Cumple | Avisos de acceso, afiliación, cartera, preventivos, ruta, encuesta, seguimiento y orientación virtual, el bot comercial y las campañas, cada uno auditado en su requisito. Que cada plantilla que manda el código esté declarada lo vigila `test_cada_plantilla_que_envia_el_codigo_esta_declarada` (`:529`). |
| 6.19-07 | Cómo se gestionan las plantillas | Propuesta | Cumple | Como se dijo: el equipo prepara los textos y los registra en Meta, y en la plataforma cada versión pasa por revisión y se activa solo aprobada (`test_version_nueva_vuelve_a_borrador`, `:74`; `test_no_se_activa_sin_aprobacion`, `:137`; `test_aprobar_el_texto_nuevo_lo_pone_en_uso`, `:101`). Que esté aprobada en Meta lo marca una persona. Si Meta pausa o rechaza después una plantilla, por su calidad, la plataforma no se entera y sus envíos fallan. |
| 6.19-08 | Cómo queda registrada la conversación | Propuesta | **Contradice** | Se le dijo a TIMU que «cada conversación queda en la ficha del interesado o de la familia». **Para una familia no es así**: lo que el asesor le contesta se guarda sin la familia, y su ficha no lo muestra (reproducido, arriba). Lo que la familia escribe y lo que le manda la plataforma sí quedan (`test_entrante_se_asocia_a_la_familia_una_sola_vez`, `:312`; `test_traza_por_familia`, `:216`). De la multimedia solo queda que llegó, y lo que el equipo escriba desde la aplicación en coexistencia no se recoge (dicho así a TIMU; fila 6.17 y 6.19 de [lo que falta](../pendiente-en-el-codigo.md)). Nada de la conversación se ata a la mascota (6.17-02). |

**Lo que hay que decidir:**
- 08: que la respuesta del asesor quede con la familia, y que la conversación se pueda atar a la
  mascota (con 6.17-02).
- 07: si la plataforma consulta en Meta el estado de sus plantillas.
- 05 y 04: el tope de gasto (ya en manos de TIMU) y si la plataforma respeta el tope diario de
  Meta.

## 6.20. Encuestas de satisfacción

**Auditado el 2026-11-27.**

**Lo que hay:**
- **Es un módulo propio** (`backend/app/modules/encuestas/`). Al completarse un servicio
  (`backend/app/workers/tasks/encuestas.py:15`) se programa su encuesta (`programar`,
  `backend/app/modules/encuestas/service.py:65`), con la configuración de su tipo de atención o la
  general: si se envía, cuántas horas después, con qué plantilla y desde qué puntaje se alerta
  (`ConfiguracionEncuesta`).
- **Cada 15 minutos salen las que ya tocan** (`enviar_pendientes`, `:97`), por WhatsApp, con un
  enlace público de un solo uso.
- **La familia responde con un puntaje de 1 a 5 y un comentario**, en el enlace o contestando el
  número en el chat. Un puntaje en el umbral o por debajo crea una tarea de prioridad alta para
  servicio al cliente, con el contexto de la atención (`_alertar`, `:229`).
- **La encuesta guarda** el servicio, la familia, el responsable (el profesional del servicio), las
  fechas y la respuesta.
- **Gerencia ve el resumen del periodo** (`resumen`, `:299`): enviadas, respondidas, tasa,
  promedio, por responsable y por tipo de atención, y el indicador de satisfacción del dashboard.
  Atención y Gerencia ven las respuestas en Encuestas (`frontend/src/features/campanas/Encuestas.tsx:25`).
- **Reproducido el 2026-11-27 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. Un médico firma la consulta de un servicio en la clínica, que se completa. El
  servicio no tiene profesional, porque solo lo asigna la ruta, y su encuesta queda sin
  responsable.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.20-01 | Un flujo independiente | Exige | Cumple | Su módulo, su configuración por tipo de atención y sus tareas del worker (`test_completar_el_servicio_programa_la_encuesta`, `backend/tests/test_encuestas.py:75`; `test_configuracion_general_y_por_tipo_se_reemplaza`, `:321`; panel `CampanasPage.secciones.test.tsx:498`). |
| 6.20-02 | Al culminar un servicio o atención, activar automáticamente una comunicación a la familia por WhatsApp u otro canal | Exige | Parcial | Al completarse un servicio sale sola, a la hora configurada (`test_envio_solo_cuando_llega_la_hora`, `:103`). Sin la plantilla aprobada se queda pendiente (`test_sin_plantilla_queda_pendiente`, `:113`), y no hay otro canal: no sale por correo. **Una atención que no es un servicio no la recibe**: la orientación virtual (6.17-06). |
| 6.20-03 | Flujo: servicio realizado → cierre de atención → envío automático → respuesta → registro → análisis | Exige | Cumple | El servicio completado la programa, sale sola, se responde por enlace o por WhatsApp, queda registrada y entra al resumen (`test_respuesta_por_enlace`, `:122`; `test_respuesta_por_whatsapp`, `:238`; `test_resumen_por_responsable`, `:275`). |
| 6.20-04 | Respuesta asociada a la familia | Exige | Cumple | `familia_id` (`backend/app/modules/encuestas/models.py:43`; `test_respuesta_por_enlace`). |
| 6.20-05 | … a la mascota | Exige | Cumple | A través de su servicio, que es de una mascota (`servicio_id`, único por tipo de encuesta). Un servicio para toda la familia no tiene mascota. La encuesta no la nombra al leerla (`EncuestaRead`), ni la lista de respuestas la muestra. |
| 6.20-06 | … al servicio | Exige | Cumple | `servicio_id` (`test_completar_el_servicio_programa_la_encuesta`), con un enlace al servicio desde la lista. |
| 6.20-07 | … a la fecha | Exige | Cumple | Cuándo se programó, se envió y se respondió, y la fecha del servicio en el enlace (`test_respuesta_por_enlace`). |
| 6.20-08 | … al profesional, cuando corresponda | Exige | Parcial | Es el profesional del servicio al completarse (`programar`, `:65`; `test_resumen_por_responsable`), y ese solo lo asigna la ruta (`backend/app/modules/rutas/service.py:498`). **En una consulta en la clínica la encuesta queda sin profesional**, aunque la consulta la haya firmado un médico (reproducido, arriba), y su promedio cae en «sin asignar». La lista de respuestas no dice quién atendió. |
| 6.20-09 | Consultar la información posteriormente | Exige | Cumple | La lista de respuestas, con las calificaciones bajas aparte, y el resumen del periodo (`test_listado_de_encuestas_combina_filtros`, `:303`; panel `CampanasPage.test.tsx:132`; `CampanasPage.secciones.test.tsx:461` y `:478`). La lista no deja filtrar por fechas ni por profesional, aunque la API filtra por responsable. |
| 6.20-10 | Exportarla a Excel u otro formato | Exige | Falta | No hay exportación de las respuestas ([lo que falta](../pendiente-en-el-codigo.md), fila 6.20). El dashboard exporta su indicador de satisfacción, que es un promedio (Sección 8). |
| 6.20-11 | Medir satisfacción | Exige | Cumple | El puntaje de 1 a 5, el promedio, la tasa de respuesta, y el promedio por responsable y por tipo de atención (`test_resumen_por_responsable`). |
| 6.20-12 | … experiencia | Exige | Parcial | La misma y única pregunta: no hay una dimensión de experiencia (la puntualidad, el trato, la explicación) aparte de la satisfacción. Solo el comentario libre la puede decir. |
| 6.20-13 | … calidad percibida | Exige | Parcial | Como 12. |
| 6.20-14 | … posibles inconformidades | Exige | Cumple | Un puntaje en el umbral o por debajo crea una tarea de prioridad alta con el contexto, y la lista filtra las calificaciones bajas (`test_calificacion_baja_crea_tarea_con_contexto`, `backend/tests/test_encuestas.py:145`; panel `CampanasPage.secciones.test.tsx:478`). |
| 6.20-15 | … oportunidades de mejora | Exige | Parcial | Solo el comentario libre, que no se clasifica ni entra al resumen: para encontrarlas hay que leer las respuestas una a una. |

**Lo que hay que decidir:**
- 10: la exportación (ya en [lo que falta](../pendiente-en-el-codigo.md)).
- 08: de dónde sale el profesional cuando no hay ruta (el que firma la consulta).
- 12, 13 y 15: si la encuesta pregunta algo más que un puntaje, y qué (pregunta para TIMU).
- 02: si la orientación virtual también se encuesta.

## 6.21. Seguimiento post atención

**Auditado el 2026-11-27.**

**Lo que hay:**
- **El seguimiento es una encuesta de otro tipo** (6.20). Si la configuración del tipo de atención
  dice a cuántos días (de 1 a 180), al completarse el servicio se programa para esa fecha
  (`programar`, `backend/app/modules/encuestas/service.py:65`). Sale por WhatsApp con la plantilla
  «Seguimiento después del servicio», con un enlace en el que la familia dice cómo sigue la mascota:
  bien, con una duda o con una novedad, y un comentario.
- **Una novedad crea una tarea de prioridad alta** para servicio al cliente, y una duda, una de
  prioridad media. Las dos llevan lo que respondió y el contexto de la atención (`_alertar`, `:229`).
- **En el panel solo se edita la configuración general** (`frontend/src/features/campanas/Encuestas.tsx`),
  así que el seguimiento va tras todas las atenciones o tras ninguna. La API admite una por tipo de
  atención (`PUT /encuestas/configuracion`), pero ninguna pantalla la usa. Solo `operacion_demo`
  la configura, en local y en staging: en producción no habrá ninguna, y sin ella no sale ningún
  seguimiento.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.21-01 | Generar automáticamente un seguimiento a la familia tras determinadas atenciones | Exige | Parcial | Se genera solo y se puede limitar a ciertos tipos de atención (`test_seguimiento_segun_el_tipo_de_atencion`, `backend/tests/test_encuestas.py:89`). Pero esa elección solo se hace por la API: desde el panel es tras todas o tras ninguna. Una atención que no es un servicio no tiene seguimiento: la orientación virtual (6.17-06). |
| 6.21-02 | Configurar cuándo se realiza | Exige | Cumple | A cuántos días del servicio, en Administración (`test_configuracion_general_y_por_tipo_se_reemplaza`, `:321`; panel `CampanasPage.secciones.test.tsx:498`). |
| 6.21-03 | Enviar comunicación | Exige | Cumple | Por WhatsApp, a su fecha, con el nombre de la mascota y el enlace (`enviar_pendientes`, `backend/app/modules/encuestas/service.py:97`; `test_el_seguimiento_pregunta_como_sigue_y_una_duda_deja_tarea`, `backend/tests/test_encuestas.py:171`). Como la encuesta, sin la plantilla aprobada se queda pendiente, y no tiene otro canal. |
| 6.21-04 | Registrar respuesta | Exige | Cumple | Cómo sigue, más el comentario, con su fecha y su canal (mismas pruebas; `test_el_seguimiento_que_va_bien_no_deja_tarea_y_una_novedad_si`, `:192`). Contestar en el chat, en lugar del enlace, no cuenta como respuesta del seguimiento (`test_un_numero_por_whatsapp_no_responde_el_seguimiento`, `:230`). |
| 6.21-05 | Generar alerta si la familia manifiesta una novedad | Exige | Cumple | La tarea de prioridad alta, que vence ese día (`test_el_seguimiento_que_va_bien_no_deja_tarea_y_una_novedad_si`). |
| 6.21-06 | Crear tarea para el equipo | Exige | Cumple | Para servicio al cliente, con la atención, la fecha, quién atendió, lo que respondió y su comentario. La duda también deja una (`test_el_seguimiento_pregunta_como_sigue_y_una_duda_deja_tarea`). |
| 6.21-07 | Mantener trazabilidad | Exige | Cumple | El seguimiento queda con su servicio, sus fechas, su respuesta y su tarea (`tarea_id`), y el mensaje en las comunicaciones de la familia. Sale en Encuestas con su insignia (panel `CampanasPage.test.tsx:132`). No llega a la historia clínica de la mascota (6.14-09). |

**Lo que hay que decidir:**
- 01: que el panel configure el seguimiento por tipo de atención, y tras qué atenciones lo quiere
  TIMU.
