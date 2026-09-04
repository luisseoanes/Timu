---
titulo: "Propuesta técnica TIMU — alcance funcional y arquitectura"
tipo: contrato-funcional
estado: normativo
alcance: >
  Versión podada para consulta durante el desarrollo. Conserva la descripción de la
  solución (A), la tabla de cumplimiento de los requisitos 6.1 a 6.23 y los módulos de
  escalabilidad (B), el stack tecnológico (C) y el reparto de alcance por fases (D).
  Los comentarios del código citan estas secciones por su letra.
retirado: >
  Capacitación, soporte, garantía, costos de terceros, modelo económico, criterios de
  evaluación y los cierres comerciales: nada de eso condiciona una decisión de código.
procedencia:
  fichero_original: Propuesta_TIMU_Puntos_15-19.docx
  sha256_original: ce6e40a3474ab8fd0765872b14f73f0acbd68bd534e919d3cf1f4b464f3f84da
  commit_con_el_original: ed34dcaf44eb04a7bbc8a3266501f9ff715d647b
  recuperar_original: "git show ed34dcaf44eb04a7bbc8a3266501f9ff715d647b:docs/Propuesta_TIMU_Puntos_15-19.docx > Propuesta_TIMU_Puntos_15-19.docx"
  version_integra_en_markdown: "git show 416796e:docs/propuesta-timu-puntos-15-19.md"
---

**PROPUESTA TÉCNICA**

*Plataforma Integral de Gestión, Operación, Comercialización y Automatización — TIMU*

# 15. PROPUESTA DEL PROVEEDOR

## A. Descripción de la solución

Proponemos el desarrollo de una plataforma a la medida, propiedad exclusiva de TIMU, construida específicamente sobre los procesos descritos en el documento de requerimientos — no una configuración de un CRM genérico de terceros. Esta decisión responde a la naturaleza del negocio de TIMU: los flujos de cartera, planes grupales, programación clínica y rutas domiciliarias tienen reglas propias que un CRM estándar no modela de forma nativa, y una plataforma a medida evita depender de las limitaciones o costos de licenciamiento de un tercero.

Adicionalmente, incorporamos desde esta primera implementación cinco funcionalidades que el documento original contempla como escalabilidad futura (sección 14): portal de usuarios para las familias, consulta de historia clínica, carnet digital, pagos en línea y autogestión de servicios. Nuestro criterio es que estas funcionalidades, más que un añadido posterior, son las que convierten la plataforma en un producto real y utilizable tanto para el equipo de TIMU como para las familias desde el primer día de operación.

La arquitectura se diseña modular por dominios (familias, cartera, servicios, clínica, rutas, comunicaciones, dashboard, portal), de forma que nuevas funcionalidades — PWA completa, nuevas integraciones, IA ampliada — puedan incorporarse sin reconstruir la base del sistema, conforme al principio de escalabilidad de la sección 3.

## B. Cumplimiento funcional

La siguiente tabla detalla el estado de cumplimiento para cada requerimiento del documento base, incluyendo los módulos de escalabilidad futura que se incorporan desde la Fase 1.

| **Requerimiento** | **Estado** | **Observación** |
| --- | --- |
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

La construcción avanza por fases, cada una con entregables funcionales verificables.

| **Fase** | **Alcance** |
| --- | --- |
| Fase 1 — Núcleo operativo | Familias/mascotas/usuarios, cartera y pagos recurrentes, planes grupales, programación de servicios, estados, WhatsApp (mensajería base), autenticación y roles. |
| Fase 2 — Operación y clínica | Rutas domiciliarias y optimización, servicios preventivos, autorización preventiva, gestión clínica veterinaria, carnet digital, clínicas aliadas. |
| Fase 3 — Portal, pagos y autogestión | Portal de usuarios, consulta de historia, autogestión de servicios, pagos en línea, encuestas, seguimiento post atención, segmentación y campañas. |
| Fase 4 — Inteligencia y cierre | Dashboard gerencial, automatizaciones transversales adicionales, apoyo de IA en atención comercial/virtual, migración final de datos, pruebas integradas y estabilización. |

Al cierre de cada fase se realiza una entrega funcional en ambiente de pruebas, validación conjunta con TIMU, y ajustes antes de pasar a producción.
