# Backlog de desarrollo — Backend

Desglose del trabajo de servidor comprometido en la propuesta técnica (`docs/propuesta-timu-puntos-15-19.md`): los 23 requisitos funcionales del documento base más los cinco módulos de escalabilidad incorporados desde la Fase 1.

Versión navegable con filtros: [https://claude.ai/code/artifact/15e07e31-e456-40c7-a743-e503b84a2681](https://claude.ai/code/artifact/15e07e31-e456-40c7-a743-e503b84a2681)

**101 unidades de trabajo · 162,5 días-persona de backend · 1,7 desarrolladores en promedio · 3,2 de pico en la Fase 1**

Los días-persona incluyen desarrollo, pruebas unitarias y documentación de API. No incluyen frontend, QA de aceptación ni tiempos de aprobación de terceros. Los IDs siguen el patrón `fase-módulo-consecutivo`.

## El cronograma cierra, pero la carga está mal repartida

Los 162,5 días-persona de backend caben en las 19 semanas de la propuesta con **1,7 desarrolladores en promedio**. El problema es otro: el trabajo está adelantado. La Fase 1 exige 3,2 personas durante 4 semanas —el núcleo operativo más la base técnica— y la Fase 2 exige 2,4; en cambio las Fases 3 y 4 se sostienen con una sola. Subir y bajar el equipo cada mes no es realista, así que hay dos salidas:

1. **Nivelar**, moviendo hacia adelante lo que no bloquea la operación diaria. Los mejores candidatos son `F1-CAR-08` (cobro recurrente tokenizado, que además espera aprobación de la pasarela) y `F1-SER-02` (flujos configurables, que en Fase 1 pueden quedar fijos).
2. **Sostener dos desarrolladores** de punta a punta y aceptar que la Fase 1 entregue en 6 semanas en vez de 4.

## Carga por fase

| Fase | Unidades | Días-persona | Peso | Personas que exige su ventana | Hito de pago |
| --- | ---: | ---: | ---: | ---: | --- |
| Base técnica transversal | 12 | 11,5 | 7% | reparte en todo el proyecto | — |
| Fase 1 — Núcleo operativo | 36 | 52 | 32% | 2,6 | Hito 1 — 30% a la firma · $2.550.000 COP |
| Fase 2 — Operación y clínica | 21 | 36 | 22% | 2,4 | Hito 2 — 30% a la entrega · $2.550.000 COP |
| Fase 3 — Portal, pagos y autogestión | 20 | 35 | 22% | 1,2 | Hito 3 — 20% a la entrega · $1.700.000 COP |
| Fase 4 — Inteligencia y cierre | 12 | 28 | 17% | 0,9 | Hito 4 — 20% a producción · $1.700.000 COP |
| **Total** | **101** | **162,5** | **100%** | **1,7 en promedio** | **$8.500.000 COP** |

## Base técnica transversal

Atraviesa las cuatro fases; se construye al inicio y se mantiene. · **11,5 días-persona en 12 unidades**

### Fundaciones · 11,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F0-01` | Migración inicial del esquema | Una base vacía queda completa con un solo upgrade, con convención de nombres para índices y llaves foráneas. | — | 0,5 |
| `F0-02` | Errores, identificador de petición y bitácora técnica | Todo error responde con el mismo formato y un identificador rastreable en los registros del servidor. | — | 1 |
| `F0-03` | Integración continua | Ningún cambio se fusiona si falla el análisis estático, los tipos, las pruebas o la construcción de imágenes. | — | 1 |
| `F0-04` | Bitácora de auditoría | Cada alta, edición o cambio de estado en familias, cartera, servicios e historia clínica guarda quién, cuándo y qué valor tenía antes. | Seguridad | 1,5 |
| `F0-05` | Configuración y secretos por ambiente | Ningún secreto vive en el repositorio y el servicio se niega a arrancar si falta una variable obligatoria. | Seguridad | 0,5 |
| `F0-06` | Endurecimiento de la capa HTTP | Límite de peticiones por IP y por usuario, orígenes permitidos por ambiente, encabezados de seguridad y tope de tamaño de carga. | Seguridad | 1 |
| `F0-07` | Respaldo y restauración | Respaldo diario automático y una restauración completa probada en el ambiente de pruebas, con evidencia. | Sección C | 1 |
| `F0-08` | Monitoreo y alertas | El chequeo de salud verifica base de datos, Redis y trabajadores; los errores no controlados llegan a la herramienta de monitoreo. | — | 1 |
| `F0-09` | Catálogos maestros | Ciudades, tipos de servicio, especies y esquemas preventivos se cargan con un comando repetible sin duplicar datos. | — | 0,5 |
| `F0-10` | Listados, filtros y orden reutilizables | Todos los módulos comparten el mismo contrato de listado y paginación. | 6.16 | 0,5 |
| `F0-11` | Almacenamiento de archivos | Los adjuntos se guardan fuera del servidor y se sirven con enlaces firmados de vida corta; nada queda público. | 6.14 | 1 |
| `F0-12` | Motor de reglas configurable | Una regla nueva de condición y acción entra en operación desde la base de datos, sin desplegar código. | 6.3 · 6.11 | 2 |

## Fase 1 — Núcleo operativo

4 semanas. Familias, cartera, planes, servicios, afiliación y WhatsApp base. · **52 días-persona en 36 unidades** · exige 2,6 personas · Hito 1 — 30% a la firma · $2.550.000 COP

### Acceso y roles · 3,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-AUT-01` | Sesión larga con renovación y cierre | El usuario mantiene la sesión sin volver a autenticarse y al cerrar sesión el token deja de servir de inmediato. | Seguridad | 1 |
| `F1-AUT-02` | Matriz de permisos por perfil | Cada endpoint declara qué perfiles lo pueden usar; una prueba recorre la matriz completa y falla si algo queda abierto. | Seguridad | 1 |
| `F1-AUT-03` | Recuperación de contraseña | El usuario recibe un enlace de un solo uso por correo o WhatsApp y define contraseña nueva. | — | 1 |
| `F1-AUT-04` | Usuario de portal ligado a la familia | Al afiliarse, la familia queda con acceso propio que sólo ve su información. | Portal | 0,5 |

### Familias y mascotas · 5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-FAM-01` | Ficha de familia completa | Edición, baja lógica e historial de cambios de estado consultable. | 6.1 | 1 |
| `F1-FAM-02` | Ficha de mascota completa | Alta, edición, baja y foto, con la mascota siempre atada a una familia. | 6.1 | 1 |
| `F1-FAM-03` | Autollenado desde formularios | Un formulario público crea o actualiza el perfil sin que nadie vuelva a digitar los datos. | 6.1 · 6.12 | 1,5 |
| `F1-FAM-04` | Validaciones de datos colombianos | Documento sin duplicados, teléfono en formato internacional y ciudad tomada del catálogo. | 6.1 | 0,5 |
| `F1-FAM-05` | Ubicación de la dirección en el mapa | Al guardar una dirección se obtienen sus coordenadas, que luego alimentan la planeación de rutas. | 6.7 | 1 |

### Planes · 5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-PLA-01` | Planes y beneficios | Administración de planes con su valor, cupos y beneficios asociados por tipo de servicio. | 6.3 | 1 |
| `F1-PLA-02` | Cambios de plan grupal | Subir o bajar de plan recalcula el valor con prorrateo y deja registro del cambio, gobernado por reglas configurables. | 6.3 | 2 |
| `F1-PLA-03` | Cupos de mascotas del plan | Agregar o retirar una mascota respeta el cupo contratado y ajusta el valor cuando la regla lo indica. | 6.3 | 1 |
| `F1-PLA-04` | Recomendación de plan por ciudad | Dada la ciudad y la composición de la familia, el sistema devuelve el plan sugerido y por qué. | 6.11 | 1 |

### Cartera · 16 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-CAR-01` | Contrato de afiliación | La afiliación genera contrato con fecha de inicio, día de corte y fecha de renovación calculada. | 6.2 · 6.4 | 1,5 |
| `F1-CAR-02` | Generación mensual de cuotas | Un proceso diario emite las cuotas del período sin duplicarlas si se vuelve a ejecutar. | 6.2 | 1 |
| `F1-CAR-03` | Estados de cartera | Al día, en mora, congelada y reactivada se derivan de reglas de días parametrizables, no de código. | 6.2 · 6.23 | 2 |
| `F1-CAR-04` | Alertas escalonadas de mora | El proceso diario notifica en los cortes definidos y deja traza de cada aviso enviado. | 6.2 | 1,5 |
| `F1-CAR-05` | Congelamiento y reactivación automáticos | Superado el plazo, la afiliación se congela y bloquea el agendamiento; al pagar se reactiva sola. | 6.2 · 6.23 | 1,5 |
| `F1-CAR-06` | Pagos manuales y conciliación | Un pago registrado a mano aplica sobre la cuota correcta y actualiza el estado de la familia. | 6.2 | 1 |
| `F1-CAR-07` | Renovación anual | Los contratos próximos a vencer se detectan solos y generan la tarea comercial con la anticipación definida. | 6.4 | 1,5 |
| `F1-CAR-08` | Cobro recurrente con tarjeta | La familia autoriza una vez y el cobro mensual se ejecuta solo, con reintentos ante rechazo. | 6.2 | 3 |
| `F1-CAR-09` | Conciliación por webhook de la pasarela | El evento se procesa una sola vez aunque llegue repetido, y un evento perdido se puede reprocesar. | 6.2 | 2 |
| `F1-CAR-10` | Estado de cuenta de la familia | Consulta única con cuotas, pagos, saldo y próximo cobro, reutilizada luego por el portal. | 6.2 | 1 |

### Servicios · 11 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-SER-01` | Agendamiento de servicios | Se agenda contra disponibilidad real y el sistema rechaza cupos ya tomados. | 6.5 | 2 |
| `F1-SER-02` | Flujos configurables por tipo de servicio | Cada tipo define sus pasos y requisitos desde configuración, sin tocar el código base. | 6.5 | 2 |
| `F1-SER-03` | Cambios de estado con disparadores | Cada transición válida queda auditada y dispara las tareas o mensajes que la regla defina. | 6.10 | 2 |
| `F1-SER-04` | Pendientes derivados de una atención | Un pendiente no avanza hasta que exista autorización registrada. | 6.6 | 1,5 |
| `F1-SER-05` | Reglas de elegibilidad | Antes de agendar se valida plan vigente, estado de afiliación y cartera al día, con motivo explícito del rechazo. | 6.5 · 6.23 | 1,5 |
| `F1-SER-06` | Bandeja de tareas internas | Las tareas generadas por los disparadores se asignan, priorizan y cierran desde una sola bandeja. | 6.4 · 6.6 | 2 |

### Afiliación · 6 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-AFI-01` | Formulario, pago, contrato y perfil sin redigitación | El ciclo completo corre solo desde el envío del formulario hasta el perfil creado y el plan activo. | 6.12 | 3 |
| `F1-AFI-02` | Contrato en PDF y aceptación | Se genera el documento con los datos reales y queda registrada la aceptación con fecha y medio. | 6.12 | 1,5 |
| `F1-AFI-03` | Calendario preventivo desde la afiliación | Al afiliar, cada mascota queda con su calendario preventivo calculado por especie y edad. | 6.13 | 1,5 |

### WhatsApp · 5,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F1-WHA-01` | Envío de plantillas con cola y reintentos | El envío no bloquea la operación, reintenta ante fallo temporal y queda registrado por destinatario. | 6.19 | 2 |
| `F1-WHA-02` | Recepción de mensajes y estados de entrega | Entregado, leído y fallido se reflejan en la traza de cada mensaje; los entrantes quedan asociados a la familia. | 6.19 | 1,5 |
| `F1-WHA-03` | Registro de plantillas aprobadas | Las plantillas y sus variables se administran desde el sistema, con control de versión y estado de aprobación. | 6.19 | 1 |
| `F1-WHA-04` | Ventana de 24 horas y baja voluntaria | Fuera de la ventana sólo se envían plantillas, y quien pide no recibir más queda excluido de todo envío masivo. | 6.19 | 1 |

## Fase 2 — Operación y clínica

3 semanas. Rutas, preventivos, historia clínica, carnet y clínicas aliadas. · **36 días-persona en 21 unidades** · exige 2,4 personas · Hito 2 — 30% a la entrega · $2.550.000 COP

### Rutas domiciliarias · 10,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F2-RUT-01` | Planeación de la ruta del día | Los servicios domiciliarios de una fecha y ciudad se agrupan en rutas con responsable asignado. | 6.7 | 2 |
| `F2-RUT-02` | Optimización de la secuencia | La ruta se ordena con distancias y tiempos reales del proveedor de mapas, con caché y tope de consultas. | 6.7 | 2,5 |
| `F2-RUT-03` | Ventanas horarias y capacidad | La optimización respeta el horario acordado con cada familia y el máximo de atenciones por técnico. | 6.7 | 2 |
| `F2-RUT-04` | Ejecución de la ruta | Cada parada registra llegada, salida y evidencia, y mueve el servicio a su siguiente estado. | 6.7 · 6.10 | 1,5 |
| `F2-RUT-05` | Reprogramación en caliente | Sacar o agregar una parada reordena el resto sin rehacer la ruta a mano. | 6.7 | 1,5 |
| `F2-RUT-06` | Aviso de ventana de llegada | La familia recibe por WhatsApp el rango horario estimado y el aviso cuando el técnico va en camino. | 6.7 · 6.19 | 1 |

### Preventivos · 10 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F2-PRE-01` | Esquemas preventivos por especie y edad | Los esquemas se administran como catálogo, no como código, y aplican al crear la mascota. | 6.8 | 1,5 |
| `F2-PRE-02` | Cálculo de próximas fechas | Aplicar un preventivo recalcula la siguiente fecha según el esquema y actualiza el calendario. | 6.8 | 1,5 |
| `F2-PRE-03` | Autorización previa del preventivo | El formulario de autorización queda dentro del flujo y sin él la aplicación no puede registrarse. | 6.9 | 2 |
| `F2-PRE-04` | Agenda preventiva automática | El proceso diario convierte los eventos próximos en servicios agendables y notifica a la familia. | 6.8 · 6.13 | 1,5 |
| `F2-PRE-05` | Carnet preventivo digital | El carnet se arma solo con lo efectivamente aplicado y muestra lo vencido y lo próximo. | 6.15 | 2 |
| `F2-PRE-06` | Carnet descargable y verificable | Se genera en PDF con código de verificación que un tercero puede validar sin entrar al sistema. | 6.15 | 1,5 |

### Clínica · 8,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F2-CLI-01` | Historia clínica estructurada | Motivo, anamnesis, diagnóstico y tratamiento por atención; una entrada firmada no se edita, se corrige con nueva versión. | 6.14 | 2,5 |
| `F2-CLI-02` | Adjuntos clínicos | Exámenes e imágenes se cargan y sólo se abren con enlace firmado por quien tiene permiso. | 6.14 | 1,5 |
| `F2-CLI-03` | Plantillas de consulta y fórmulas | El profesional parte de plantillas por tipo de atención y genera la fórmula en PDF. | 6.14 | 1,5 |
| `F2-CLI-04` | Atención veterinaria virtual | La solicitud entra a una cola atendida por el profesional, con respuestas basadas en plantillas aprobadas y registro en la historia. | 6.17 | 2 |
| `F2-CLI-05` | Permisos sobre la historia | Sólo personal médico escribe; la familia y el resto del equipo ven lo que su perfil permite. | 6.14 · Seguridad | 1 |

### Clínicas aliadas · 7 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F2-ALI-01` | Directorio de aliadas y convenios | Cada aliada tiene sus beneficios, coberturas y tarifas vigentes por plan. | 6.22 | 1,5 |
| `F2-ALI-02` | Autorización de atención en aliada | Antes de emitir la remisión se valida plan vigente, cartera al día y beneficio disponible. | 6.22 | 2 |
| `F2-ALI-03` | Acceso para la clínica aliada | La aliada valida el beneficio y reporta la atención sin ver más información de la familia que la necesaria. | 6.22 | 2 |
| `F2-ALI-04` | Liquidación de convenios | Reporte por período con atenciones, valores cubiertos y saldo a pagar por aliada. | 6.22 | 1,5 |

## Fase 3 — Portal, pagos y autogestión

6 semanas. Portal de familias, comercial automatizado, campañas y encuestas. · **35 días-persona en 20 unidades** · exige 1,2 personas · Hito 3 — 20% a la entrega · $1.700.000 COP

### Portal de familias · 12 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F3-POR-01` | Datos de la familia en el portal | Perfil, mascotas, plan vigente y estado de cuenta, siempre limitados a la familia que consulta. | Portal | 2 |
| `F3-POR-02` | Consulta de historia clínica | La familia ve la historia de sus mascotas en sólo lectura, sin campos de uso interno. | Escalabilidad | 1,5 |
| `F3-POR-03` | Carnet digital en el portal | El carnet se consulta y descarga desde la ficha de cada mascota. | 6.15 | 0,5 |
| `F3-POR-04` | Autogestión de servicios | La familia agenda, reprograma o cancela dentro de las reglas de disponibilidad y de su plan. | Escalabilidad | 3 |
| `F3-POR-05` | Pagos en línea | Pago de la cuota desde el portal, con actualización inmediata del estado y comprobante descargable. | Escalabilidad | 2 |
| `F3-POR-06` | Actualización de datos por la familia | Los cambios de contacto y dirección se validan y quedan auditados. | 6.1 | 1 |
| `F3-POR-07` | Ingreso con clave temporal por WhatsApp | La familia entra con un código de un solo uso, con intentos limitados y expiración. | Seguridad | 2 |

### Comercial automatizado · 7,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F3-COM-01` | Captura de interesados y embudo | Todo interesado, venga de donde venga, entra al embudo con origen y responsable. | 6.11 | 2 |
| `F3-COM-02` | Conversación comercial automatizada | El árbol de conversación por WhatsApp resuelve las consultas frecuentes y lleva hasta la afiliación. | 6.11 | 3 |
| `F3-COM-03` | Recomendación de plan en la conversación | Según ciudad y mascotas, la conversación propone el plan y su valor con las reglas ya definidas. | 6.11 | 1,5 |
| `F3-COM-04` | Paso a asesor humano | Cuando la regla lo indica o el interesado lo pide, la conversación pasa a un asesor con todo el contexto. | 6.11 | 1 |

### Segmentación y campañas · 9 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F3-SEG-01` | Segmentos guardados | Los filtros combinables se guardan como segmento reutilizable y muestran cuántas familias alcanzan. | 6.16 | 2,5 |
| `F3-CAM-01` | Creación de campañas | Campaña con segmento, plantilla y previsualización de la audiencia antes de enviar. | 6.18 | 1,5 |
| `F3-CAM-02` | Envío masivo controlado | El envío respeta el ritmo permitido por el proveedor, excluye a quien pidió no recibir y deja traza por destinatario. | 6.18 · 6.19 | 2,5 |
| `F3-CAM-03` | Resultados de la campaña | Enviados, entregados, leídos y respondidos por campaña, exportables. | 6.18 | 1,5 |
| `F3-CAM-04` | Campañas programadas y recurrentes | Una campaña se programa a futuro o se repite en el ciclo definido sin intervención manual. | 6.18 | 1 |

### Encuestas y seguimiento · 6,5 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F3-ENC-01` | Encuesta al cierre de la atención | Al completarse un servicio la encuesta sale sola, con la demora configurada por tipo de atención. | 6.20 | 1,5 |
| `F3-ENC-02` | Captura de respuestas | La familia responde por WhatsApp o enlace y el puntaje queda asociado al servicio y al responsable. | 6.20 | 2 |
| `F3-ENC-03` | Seguimiento post atención | Cada tipo de atención define su seguimiento y el sistema lo ejecuta en el plazo configurado. | 6.21 | 2 |
| `F3-ENC-04` | Alerta por calificación baja | Un puntaje bajo genera tarea inmediata de servicio al cliente con el contexto de la atención. | 6.20 · 6.21 | 1 |

## Fase 4 — Inteligencia y cierre

6 semanas. Dashboard, apoyo de IA, migración y estabilización. · **28 días-persona en 12 unidades** · exige 0,9 personas · Hito 4 — 20% a producción · $1.700.000 COP

### Dashboard gerencial · 6 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F4-DAS-01` | Definición de indicadores | Afiliaciones, retiros, recaudo, mora, cumplimiento de rutas, servicios por tipo y satisfacción, con fórmula acordada y documentada. | Sección 18 | 2,5 |
| `F4-DAS-02` | Consultas del dashboard | Las agregaciones responden en menos de dos segundos sobre volumen real, con caché y filtros por período y ciudad. | Sección 18 | 2 |
| `F4-DAS-03` | Exportables y reportes programados | Cualquier vista se descarga en Excel o CSV, y los reportes definidos llegan por correo en su periodicidad. | Sección 18 | 1,5 |

### Apoyo de inteligencia artificial · 8 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F4-IAA-01` | Capa de IA con control | Un solo punto de integración con prompts versionados, límite de gasto y registro de cada consulta. | Sección 14 | 2 |
| `F4-IAA-02` | IA en la atención comercial | Responde consultas abiertas dentro del guion aprobado y entrega al asesor cuando sale del alcance. | 6.11 | 2,5 |
| `F4-IAA-03` | IA en la atención virtual | Redacta un borrador para el profesional, que siempre debe aprobarlo: nunca responde sola al usuario. | 6.17 | 2 |
| `F4-IAA-04` | Medición de calidad de las respuestas | Conjunto de casos de prueba con resultado esperado, corrido antes de cada cambio de prompt. | 6.11 · 6.17 | 1,5 |

### Migración de datos · 4 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F4-MIG-01` | Migración de la información actual | Mapeo campo a campo, dos corridas de prueba con conteos cuadrados y plan de reversa antes de la definitiva. | Sección 16 | 4 |

### Cierre · 10 días

| ID | Trabajo | Criterio de aceptación | Req. | Días |
| --- | --- | --- | --- | ---: |
| `F4-QAA-01` | Pruebas integradas de los ciclos completos | Los recorridos de captar, afiliar, cobrar, agendar, atender, prevenir y fidelizar corren de extremo a extremo en automático. | Sección 18 | 3 |
| `F4-QAA-02` | Pruebas de carga y ajuste de índices | El sistema sostiene el volumen proyectado a doce meses dentro de los tiempos acordados. | Escalabilidad | 2 |
| `F4-DOC-01` | Documentación técnica y de operación | Manual por perfil, documentación de la API y guía de despliegue y recuperación, entregadas a TIMU. | Sección E | 2 |
| `F4-EST-01` | Estabilización y salida a producción | Lista de verificación de seguridad, respaldos, monitoreo y plan de reversa ejecutados antes del corte. | Sección F | 3 |

## Punto de partida ya construido

Lo que el scaffold del repositorio ya resuelve, y que este backlog no vuelve a estimar:

- **Autenticación JWT con roles** y guard por perfil (admin, comercial, operaciones, médico, familia).
- **Módulo de familias y mascotas** operativo: alta con mascotas anidadas, búsqueda, filtros combinables y paginación.
- **Modelos de datos de los 14 dominios** con sus relaciones e índices, listos para migrar.
- **Máquina de estados de servicios** con transiciones validadas y pruebas.
- **Esqueleto de integraciones**: cliente de Meta Cloud API, pasarela con validación de firma, optimizador OR-Tools.
- **Celery y beat** con los cuatro trabajos recurrentes declarados, y despliegue en Docker Compose.

## Riesgos y dependencias de terceros

- **Verificación de WhatsApp Business.** Meta puede tardar semanas y bloquea las pruebas reales de mensajería. Arrancar el trámite el día 1 y trabajar con simulador local mientras tanto.
- **Habilitación de la pasarela.** El cobro recurrente tokenizado (`F1-CAR-08`) requiere aprobación comercial de Wompi o PayU; sin ella la Fase 1 entrega sólo pago manual.
- **Calidad de los datos a migrar.** `F4-MIG-01` asume archivos consistentes; duplicados de familias o mascotas sin titular pueden duplicar el esfuerzo.
- **Cuota de Google Maps.** La matriz de distancias se factura por consulta. Definir tope diario y caché antes de producción (`F2-RUT-02`).
- **Definición del alcance de IA.** La propuesta lo deja abierto. Cuanto más tarde se cierre, más presión sobre la Fase 4.

## Definición de terminado

Aplica a toda unidad de este backlog:

- Pruebas automáticas del camino feliz y de al menos un caso de error, con la suite en verde.
- Migración de Alembic aplicable y reversible, verificada sobre una base vacía.
- Endpoints documentados en el OpenAPI que se genera solo, con ejemplos de petición y respuesta.
- Permisos por rol declarados explícitamente: ningún endpoint queda abierto por omisión.
- Cambios de estado y datos sensibles registrados en la bitácora de auditoría (`F0-04`).
- Revisión de código de otro desarrollador y despliegue verificado en el ambiente de pruebas.
