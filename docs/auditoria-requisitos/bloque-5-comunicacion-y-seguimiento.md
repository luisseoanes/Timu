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
