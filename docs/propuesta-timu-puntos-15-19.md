---
titulo: "Propuesta técnica y económica — TIMU (puntos 15-19)"
tipo: contrato-funcional
estado: normativo
procedencia:
  fichero_original: Propuesta_TIMU_Puntos_15-19.docx
  sha256_original: ce6e40a3474ab8fd0765872b14f73f0acbd68bd534e919d3cf1f4b464f3f84da
  commit_con_el_original: ed34dcaf44eb04a7bbc8a3266501f9ff715d647b
  recuperar_original: "git show ed34dcaf44eb04a7bbc8a3266501f9ff715d647b:docs/Propuesta_TIMU_Puntos_15-19.docx > Propuesta_TIMU_Puntos_15-19.docx"
metadatos_del_documento:
  autor: "Un-named"
  ultima_modificacion_por: "luis seoanes"
  revision: 2
  creado: 2026-08-27T19:36:00Z
  modificado: 2026-08-27T20:33:00Z
  paginas: 5
  palabras: 1989
  caracteres_con_espacios: 12904
conversion:
  conserva: "los 195 bloques de texto, las 4 tablas (51 filas), los 5 encabezados de nivel 1, los 8 de nivel 2, los 21 elementos de lista y las 15 marcas de negrita ajenas a encabezados"
  notas:
    - "En los encabezados no se replican las marcas de énfasis: el nivel del encabezado ya cumple esa función."
    - "Las celdas con varios párrafos separan su contenido con <br> para no romper la fila de la tabla."
    - "El documento original no contenía imágenes, notas al pie, comentarios, encabezados de página ni hipervínculos."
---

**PROPUESTA TÉCNICA Y ECONÓMICA**

*Plataforma Integral de Gestión, Operación, Comercialización y Automatización — TIMU*

En respuesta al Documento de Requerimientos Funcionales compartido por TIMU S.A.S., presentamos a continuación nuestra propuesta técnica y económica, siguiendo la estructura solicitada en la sección 15 del documento base.

# 15. PROPUESTA DEL PROVEEDOR

## A. Descripción de la solución

Proponemos el desarrollo de una plataforma a la medida, propiedad exclusiva de TIMU, construida específicamente sobre los procesos descritos en el documento de requerimientos — no una configuración de un CRM genérico de terceros. Esta decisión responde a la naturaleza del negocio de TIMU: los flujos de cartera, planes grupales, programación clínica y rutas domiciliarias tienen reglas propias que un CRM estándar no modela de forma nativa, y una plataforma a medida evita depender de las limitaciones o costos de licenciamiento de un tercero.

Adicionalmente, incorporamos desde esta primera implementación cinco funcionalidades que el documento original contempla como escalabilidad futura (sección 14): portal de usuarios para las familias, consulta de historia clínica, carnet digital, pagos en línea y autogestión de servicios. Nuestro criterio es que estas funcionalidades, más que un añadido posterior, son las que convierten la plataforma en un producto real y utilizable tanto para el equipo de TIMU como para las familias desde el primer día de operación.

La arquitectura se diseña modular por dominios (familias, cartera, servicios, clínica, rutas, comunicaciones, dashboard, portal), de forma que nuevas funcionalidades — PWA completa, nuevas integraciones, IA ampliada — puedan incorporarse sin reconstruir la base del sistema, conforme al principio de escalabilidad de la sección 3.

## B. Cumplimiento funcional

La siguiente tabla detalla el estado de cumplimiento para cada requerimiento del documento base, incluyendo los módulos de escalabilidad futura que se incorporan desde la Fase 1.

| **Requerimiento** | **Estado** | **Observación** |
| --- | --- | --- |
| 6.1 Gestión de familias, usuarios y mascotas | Cumple | Incluye autollenado de formularios al perfil. |
| 6.2 Gestión de cartera | Cumple | Alertas, mora, congelamiento y reactivación automatizados. |
| 6.3 Cambios en planes grupales | Cumple | Motor de reglas configurable sin tocar código base. |
| 6.4 Renovación anual | Cumple | Detección automática y generación de tareas. |
| 6.5 Programación de servicios | Cumple | Flujos configurables por tipo de servicio. |
| 6.6 Pendientes derivados de atención | Cumple | Con control de autorización previa. |
| 6.7 Gestión de rutas domiciliarias | Cumple | Optimización de secuencia vía OR-Tools / Maps API. |
| 6.8 Servicios preventivos | Cumple | Cálculo automático de próximas fechas. |
| 6.9 Autorización de servicios preventivos | Cumple | Formulario de autorización integrado al flujo. |
| 6.10 Estados de los servicios | Cumple | Máquina de estados con disparadores de tareas. |
| 6.11 Atención comercial automatizada | Cumple | Motor de reglas + recomendación de plan por ciudad. |
| 6.12 Afiliación y creación automática de usuarios | Cumple | Formulario → pago → contrato → perfil, sin redigitación. |
| 6.13 Alimentación del calendario preventivo | Cumple | Se calcula desde datos de afiliación. |
| 6.14 Gestión clínica veterinaria | Cumple | Historia clínica estructurada con adjuntos. |
| 6.15 Carnet preventivo digital | Cumple | Alimentado automáticamente desde rutas preventivas. |
| 6.16 Segmentación | Cumple | Filtros combinables para campañas y reportes. |
| 6.17 Atención veterinaria virtual | Cumple | Plantillas aprobadas; apoyo, no reemplazo del criterio médico. |
| 6.18 Comunicaciones masivas y campañas | Cumple | Segmentación + envío + trazabilidad. |
| 6.19 Comunicación por WhatsApp | Cumple | Meta Cloud API oficial (ver sección C). |
| 6.20 Encuestas de satisfacción | Cumple | Disparo automático al cierre de atención. |
| 6.21 Seguimiento post atención | Cumple | Configurable por tipo de atención. |
| 6.22 Gestión con clínicas aliadas | Cumple | Validación de plan, pago y beneficio en el flujo. |
| 6.23 Estados de afiliación | Cumple | Cambios de estado propagan a módulos relacionados. |
| Portal de usuarios (familias) | Cumple | Incorporado desde la Fase 1, no como fase futura. |
| Consulta de historia clínica | Cumple | Vista de solo lectura para la familia, con permisos. |
| Carnet digital | Cumple | Accesible desde el portal de usuarios. |
| Pagos en línea | Cumple | Integración con pasarela (Wompi / PayU). |
| Autogestión de servicios | Cumple | Agendar/reprogramar dentro de reglas de disponibilidad. |
| PWA para familias | Cumple parcialmente | El portal se construye API-first; empaquetado PWA es una fase posterior de bajo esfuerzo adicional. |
| Inteligencia artificial como apoyo | Cumple parcialmente | Aplicada en 6.11/6.17; ampliable según se defina alcance. |

## C. Tecnología

La solución se construye sobre un stack moderno, de código abierto en su mayoría, sin dependencia de licencias propietarias costosas:

- Backend: Python + FastAPI — framework asíncrono, con documentación de API autogenerada (OpenAPI/Swagger), adecuado para el alto volumen de integraciones (WhatsApp, pagos, calendario).
- Frontend: React + TypeScript — para el panel operativo interno y el portal de usuarios, con tipado fuerte que reduce errores en producción.
- Base de datos: PostgreSQL — relacional, con integridad referencial fuerte entre familias, mascotas, planes, pagos e historia clínica.
- Automatizaciones y tareas programadas: Celery + Redis — motor de trabajos en segundo plano para recordatorios, calendario preventivo, encuestas y seguimientos.
- WhatsApp: Meta Cloud API (oficial) — integración directa, sin intermediarios adicionales, con gestión de plantillas aprobadas.
- Pagos: Wompi / PayU — pasarelas certificadas en Colombia, con manejo de webhooks para conciliación automática.
- Optimización de rutas: Google OR-Tools + Google Maps Platform — para cálculo de secuencias de desplazamiento.
- Infraestructura: contenedores Docker sobre proveedor cloud (AWS o DigitalOcean), con respaldo automatizado.
- Repositorio de código y base de datos bajo control total de TIMU desde el primer día — sin bloqueo ("vendor lock-in").

## D. Implementación

Proponemos una implementación por fases, cada una con entregables funcionales verificables, en lugar de una única entrega al final del proyecto. El uso de herramientas de asistencia de IA en el desarrollo (generación de código base, pruebas y documentación) permite acelerar los tiempos de escritura de código, aunque los tiempos de aprobación de terceros (verificación de cuenta de WhatsApp Business, habilitación de pasarela de pago) dependen de esos proveedores externos y corren en paralelo.

| **Fase** | **Duración estimada** | **Alcance** |
| --- | --- | --- |
| Fase 1 — Núcleo operativo | 4 semanas | Familias/mascotas/usuarios, cartera y pagos recurrentes, planes grupales, programación de servicios, estados, WhatsApp (mensajería base), autenticación y roles. |
| Fase 2 — Operación y clínica | 3 semanas | Rutas domiciliarias y optimización, servicios preventivos, autorización preventiva, gestión clínica veterinaria, carnet digital, clínicas aliadas. |
| Fase 3 — Portal, pagos y autogestión | 6 semanas | Portal de usuarios, consulta de historia, autogestión de servicios, pagos en línea, encuestas, seguimiento post atención, segmentación y campañas. |
| Fase 4 — Inteligencia y cierre | 6 semanas | Dashboard gerencial, automatizaciones transversales adicionales, apoyo de IA en atención comercial/virtual, migración final de datos, pruebas integradas y estabilización. |

Al cierre de cada fase se realiza una entrega funcional en ambiente de pruebas, validación conjunta con TIMU, y ajustes antes de pasar a producción.

## E. Capacitación

- 4 sesiones de capacitación (una al cierre de cada fase), de 2 horas cada una, por videollamada o presencial según disponibilidad.
- Material entregado: manual de usuario por perfil (administrador, comercial, operaciones, personal médico) y guías en video de los flujos principales.
- Acompañamiento inicial de 2 semanas posteriores a la puesta en producción de cada fase, para resolver dudas de uso en caliente.

## F. Soporte

- Canal: WhatsApp y correo electrónico dedicados durante el periodo de soporte incluido.
- Horario: lunes a viernes, horario laboral (8:00 a.m. – 6:00 p.m.).
- Tiempo de respuesta: máximo 24 horas hábiles para incidencias, prioridad inmediata para caídas del sistema.
- Soporte incluido: 3 meses posteriores a la entrega final (Fase 4). Soporte posterior se cotiza aparte, bajo modalidad mensual o por bolsa de horas.

## G. Garantía

Garantía de 90 días posteriores a la entrega de cada fase sobre errores o defectos de funcionamiento ("bugs") atribuibles al desarrollo, sin costo adicional. No cubre cambios de alcance ni nuevas funcionalidades no contempladas en esta propuesta.

## H. Costos adicionales

Para mantener la transparencia solicitada en el documento base, se listan explícitamente los costos que no dependen del proveedor sino de terceros, y que TIMU asumirá de forma directa:

- WhatsApp Business (Meta Cloud API): costo por conversación/plantilla, facturado directamente por Meta según su tarifario vigente.
- Pasarela de pago (Wompi/PayU/Refacil): comisión por transacción, definida por el proveedor de pagos, no por nosotros, Refacil contempla 1.200 pesos por transacción, sin comisión.
- Hosting/infraestructura cloud: costo mensual estimado entre $150.000 y $400.000 COP, según volumen de uso, facturado directamente por el proveedor cloud (AWS/DigitalOcean).
- Dominio y certificado SSL: costo anual menor, si TIMU no cuenta ya con uno.
- No hay costos de licenciamiento por usuario ni por módulo — la plataforma es propiedad de TIMU sin cobros recurrentes hacia nosotros salvo soporte post-garantía si se contrata.

# 16. MODELO ECONÓMICO

El valor total de la propuesta cubre el desarrollo completo descrito en la sección 15, incluyendo los cinco módulos de escalabilidad futura incorporados desde la Fase 1 (portal de usuarios, consulta de historia, carnet digital, pagos y autogestión de servicios).

| **Concepto** | **Valor** |
| --- | --- |
| Implementación inicial (Fases 1 a 4, desarrollo completo) | $8.500.000 COP |
| Licencia / suscripción / alquiler recurrente | $0 — no aplica (propiedad 100% de TIMU, sin licenciamiento por uso) |
| Desarrollo personalizado | Incluido en la implementación inicial |
| Integraciones (WhatsApp, pasarela de pago, calendario) | Incluido en la implementación inicial |
| Migración de información | Incluido en la implementación inicial |
| Capacitación | Incluido en la implementación inicial |
| Soporte (primeros 3 meses post-entrega) | Incluido — ver sección F |
| Otros (hosting, WhatsApp API, pasarela de pago) | A cargo de TIMU, pagados directamente al proveedor externo — ver sección H |
| **VALOR TOTAL DE LA PROPUESTA** | **$8.500.000 COP + IVA si aplica** |

**Forma de pago propuesta (por hitos)**

| **Hito** | **%** | **Valor** |
| --- | --- | --- |
| Hito 1 — Firma de contrato | 30% | $2.550.000 COP |
| Hito 2 — Entrega Fase 2 (fin operación/clínica) | 30% | $2.550.000 COP |
| Hito 3 — Entrega Fase 3 (portal, pagos, autogestión) | 20% | $1.700.000 COP |
| Hito 4 — Entrega final Fase 4 y puesta en producción | 20% | $1.700.000 COP |

Los valores no incluyen IVA. Cualquier funcionalidad adicional no contemplada explícitamente en el documento de requerimientos ni en esta propuesta (por ejemplo, PWA empaquetada, nuevos módulos comerciales o ampliaciones de IA más allá de lo descrito) se cotizará de forma independiente una vez definido su alcance.

# 17. CRITERIOS DE EVALUACIÓN

Entendemos que TIMU evaluará esta propuesta bajo los criterios y pesos definidos en el documento base (cumplimiento funcional 30%, automatización 15%, integraciones 10%, seguridad 10%, escalabilidad 10%, implementación y soporte 10%, experiencia del proveedor 5%, costo total 10%). Consideramos que la incorporación temprana de los módulos de portal, pagos y autogestión fortalece particularmente los criterios de escalabilidad y automatización, sin sacrificar el cumplimiento del alcance funcional base.

# 18. RESULTADO ESPERADO

Nuestro compromiso es entregar una plataforma que permita a TIMU recorrer el ciclo completo descrito en el documento base — captar, convertir, afiliar, gestionar, prevenir, atender, hacer seguimiento, medir y fidelizar — de forma integrada desde la primera fase, y que la incorporación temprana del portal de usuarios y la autogestión permitan que las familias empiecen a interactuar directamente con la plataforma sin esperar a una fase posterior. La arquitectura modular garantiza que futuras funcionalidades (nuevas integraciones, nuevos servicios, ampliación de IA) se incorporen sin reconstruir la infraestructura base.

# 19. CONSIDERACIÓN FINAL

Entendemos que TIMU no busca únicamente un CRM, sino una infraestructura digital propia que acompañe el crecimiento de la operación comercial, preventiva, veterinaria y de experiencia del usuario. Por eso proponemos construir la plataforma completa desde ahora, con una arquitectura pensada para escalar, en lugar de entregar un producto parcial que deba reconstruirse más adelante. Quedamos atentos a cualquier ajuste de alcance, cronograma o condiciones que TIMU considere pertinente antes de la firma del contrato.
