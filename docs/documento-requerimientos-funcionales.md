# DOCUMENTO DE REQUERIMIENTOS FUNCIONALES

**Plataforma Integral de Gestión, Operación, Comercialización y Automatización — TIMU**

**Empresa:** TIMU S.A.S.\
**Proyecto:** Implementación de plataforma digital integral\
**Objeto de la solicitud:** Cotización para diseño, implementación, configuración y/o desarrollo de plataforma tecnológica escalable.

---

## 1. CONTEXTO

TIMU es una empresa dedicada a la prestación de servicios veterinarios y al acompañamiento integral de familias con animales de compañía, mediante servicios domiciliarios, orientación veterinaria vía WhatsApp, planes de salud y una red de aliados.

La empresa cuenta actualmente con un producto y modelo de servicio validado en el mercado y se encuentra en una etapa de fortalecimiento de sus capacidades comerciales, operativas y tecnológicas con el propósito de incrementar su capacidad de atención, mejorar la experiencia del usuario y facilitar el crecimiento de la organización.

Actualmente, diferentes procesos de TIMU se encuentran distribuidos entre herramientas independientes, hojas de cálculo, WhatsApp, formularios y plataformas externas, generando reprocesos, digitación duplicada, dependencia de procesos manuales y riesgo de pérdida de trazabilidad.

Por esta razón, TIMU busca implementar una **plataforma digital integral**, cuyo núcleo contemple funcionalidades de CRM, gestión operativa y automatización de procesos.

---

## 2. OBJETIVO GENERAL

Implementar una plataforma digital que permita **centralizar, gestionar y automatizar los principales procesos comerciales, administrativos, operativos y de acompañamiento al usuario de TIMU**, integrando la información de familias, mascotas, planes, servicios, pagos, atención veterinaria, comunicaciones y seguimiento.

La plataforma deberá contribuir a:

- Reducir procesos manuales y reprocesos.
- Disminuir la duplicidad de digitación.
- Mejorar la trazabilidad de los procesos.
- Facilitar la delegación de funciones.
- Mejorar la gestión comercial.
- Automatizar comunicaciones y recordatorios.
- Optimizar la programación de servicios domiciliarios.
- Fortalecer el seguimiento preventivo.
- Mejorar la experiencia de las familias.
- Generar información para la toma de decisiones.
- Preparar a TIMU para una mayor escala operativa.

---

## 3. PRINCIPIO DE ESCALABILIDAD

La solución propuesta deberá ser **modular, escalable y preparada para crecimiento futuro**.

TIMU requiere inicialmente resolver un conjunto prioritario de procesos; sin embargo, la plataforma deberá permitir incorporar posteriormente nuevas funcionalidades, módulos, automatizaciones e integraciones **sin necesidad de reemplazar la estructura base de la solución**.

El proveedor deberá indicar:

- Qué funcionalidades están contempladas en la propuesta inicial.
- Qué funcionalidades pueden incorporarse posteriormente.
- Qué integraciones soporta actualmente.
- Qué arquitectura o tecnología utiliza.
- Qué posibilidades de ampliación ofrece.
- Qué costos podrían generarse por futuras ampliaciones.
- Qué elementos quedan bajo propiedad o control de TIMU.

---

## 4. PRINCIPIO DE SOLUCIÓN

TIMU establece en este documento **las necesidades funcionales y los resultados esperados**, pero no pretende imponer una arquitectura tecnológica específica.

El proveedor podrá proponer la solución técnica que considere más adecuada, siempre que permita cumplir los requerimientos y garantice, en la medida técnicamente aplicable:

- Escalabilidad.
- Seguridad.
- Disponibilidad.
- Integridad de la información.
- Trazabilidad.
- Interoperabilidad.
- Facilidad de uso.
- Capacidad de integración.
- Sostenibilidad tecnológica.

Se solicita al proveedor indicar claramente **cómo propone resolver cada necesidad planteada**.

---

## 5. ESTRUCTURA GENERAL ESPERADA

La solución deberá contemplar, inicialmente, los siguientes componentes:

1. Gestión de familias, usuarios y mascotas.
2. Gestión de planes y cartera.
3. Gestión comercial y adquisición de usuarios.
4. Programación y operación de servicios.
5. Gestión de rutas y servicios preventivos.
6. Gestión clínica veterinaria.
7. Comunicaciones y automatizaciones.
8. Seguimiento de experiencia y postatención.
9. Dashboard e información gerencial.
10. Integraciones con herramientas externas.

Estos componentes deberán estar **interconectados**, evitando que cada módulo opere como una herramienta aislada.

---

## 6. REQUERIMIENTOS FUNCIONALES

---

### 6.1. Gestión de familias, usuarios y mascotas

La plataforma deberá permitir crear y administrar un perfil integral de cada familia.

#### Información esperada:

- Datos de contacto.
- Usuarios asociados.
- Mascotas asociadas.
- Dirección.
- Zona/sector.
- Plan contratado.
- Estado de afiliación.
- Estado de pagos.
- Servicios utilizados mensualmente.
- Servicios pendientes mensualmente.
- Historial de comunicaciones.
- Historial de atención.
- Documentos asociados.

Cada mascota deberá contar con un perfil individual asociado a su familia.

#### Información de mascota:

- Nombre.
- Especie.
- Sexo.
- Edad/fecha de nacimiento.
- Raza.
- Peso.
- Información preventiva.
- Plan asociado.
- Historial de servicios.
- Historia clínica.
- Documentos y archivos.

#### Requerimiento crítico

La información obtenida mediante formularios deberá poder **registrarse automáticamente en el perfil correspondiente**, evitando la digitación manual de información que ya fue suministrada por el usuario.

---

### 6.2. Gestión de cartera

La plataforma deberá permitir identificar y realizar seguimiento a usuarios con novedades de pago.

#### Actualmente

TIMU utiliza una plataforma externa que genera tareas programadas según las fechas de pago. El equipo debe revisar diariamente dichas tareas, identificar usuarios próximos a pagar o en mora, ingresar posteriormente a WhatsApp y realizar manualmente los diferentes contactos.

El sistema actual contempla diferentes momentos de comunicación, por ejemplo:

- Recordatorio previo al vencimiento.
- Seguimiento al vencimiento.
- Seguimiento a usuarios con varios días de mora.
- Congelamiento del servicio según las políticas establecidas.
- Reactivación una vez realizado el pago.

#### Resultado esperado

La nueva plataforma deberá permitir:

- Identificar automáticamente usuarios próximos al vencimiento.
- Identificar usuarios morosos.
- Generar alertas.
- Crear tareas de seguimiento.
- Automatizar o facilitar comunicaciones.
- Registrar pagos.
- Actualizar el estado del usuario.
- Programar automáticamente la próxima fecha de cobro.
- Manejar diferentes periodicidades de pago:
  - mensual;
  - trimestral;
  - semestral;
  - anual.
- Mantener historial de pagos y gestiones de cartera.

---

### 6.3. Cambios en planes grupales

La plataforma deberá permitir gestionar usuarios vinculados a planes grupales.

Cuando un integrante se retire del grupo, deberá permitir:

- Identificar el cambio.
- Actualizar la composición del grupo.
- Aplicar la regla correspondiente.
- Actualizar el valor a pagar.
- Generar alerta o tarea.
- Registrar la modificación.
- Facilitar la comunicación al usuario.

Las reglas deberán poder modificarse posteriormente sin requerir una reconstrucción completa de la plataforma.

---

### 6.4. Renovación anual

La plataforma deberá identificar automáticamente usuarios que cumplen un año en el plan.

Deberá permitir:

- Generar alerta.
- Aplicar la regla de actualización correspondiente.
- Actualizar condiciones económicas.
- Generar tarea de comunicación.
- Registrar la renovación.
- Mantener trazabilidad.

---

### 6.5. Programación de servicios

La plataforma deberá facilitar la gestión de solicitudes y programación de servicios veterinarios.

#### Flujo esperado

**Solicitud → validación → disponibilidad → autorización → programación → confirmación → realización → seguimiento**

La plataforma deberá permitir:

- Registrar la solicitud.
- Identificar usuario y mascota.
- Identificar plan.
- Validar beneficios disponibles.
- Identificar servicios ya utilizados dentro del periodo correspondiente.
- Generar solicitud para validación profesional cuando sea necesario.
- Registrar disponibilidad del profesional.
- Proponer opciones al usuario.
- Registrar autorización.
- Programar el servicio.
- Generar confirmaciones.
- Mantener trazabilidad.

#### Importante

No todos los servicios deben tener el mismo flujo.

Por ejemplo, una ecografía puede requerir validación de cobertura, disponibilidad profesional y autorización del usuario antes de ser programada.

Por lo tanto, la plataforma deberá permitir configurar **diferentes flujos según el tipo de servicio**.

---

### 6.6. Gestión de pendientes derivados de una atención

Cuando durante una atención veterinaria se genere un servicio pendiente —por ejemplo:

- examen de laboratorio;
- ecografía;
- procedimiento;
- control;
- seguimiento;

la plataforma deberá permitir registrar dicho pendiente directamente asociado a la mascota.

El sistema deberá poder:

1. Registrar el pendiente.
2. Identificar cobertura según el plan.
3. Determinar condiciones y/o valor aplicable.
4. Generar tarea para el equipo.
5. Facilitar la comunicación con la familia.
6. Registrar autorización o rechazo.
7. Iniciar programación únicamente cuando corresponda.
8. Mantener trazabilidad.

**No deberá enviarse automáticamente un servicio a una ruta o agenda cuando aún requiera autorización o validación de disponibilidad.**

---

### 6.7. Gestión de rutas domiciliarias

La plataforma deberá permitir organizar y optimizar servicios domiciliarios.

Deberá contemplar variables como:

- Ubicación.
- Zona.
- Tipo de servicio.
- Duración estimada.
- Disponibilidad.
- Franja horaria.
- Profesional asignado.
- Orden de desplazamiento.

#### Resultado esperado

La plataforma deberá permitir visualizar usuarios/servicios en un mapa y proponer una secuencia de atención que optimice desplazamientos.

Ejemplo:

**Usuario A → Usuario B → Usuario C → Usuario D**

considerando ubicación y duración estimada de cada servicio.

Deberá permitir establecer una duración aproximada por tipo de servicio para calcular bloques horarios coherentes.

---

### 6.8. Gestión de servicios preventivos

La plataforma deberá identificar automáticamente usuarios próximos a recibir servicios preventivos incluidos o asociados a su plan.

#### Servicios iniciales:

- Desparasitación interna.
- Desparasitación externa.
- Vacunación.
- Bravecto u otros productos preventivos.

La plataforma deberá permitir:

- Registrar última aplicación.
- Registrar producto.
- Registrar fecha.
- Registrar peso cuando sea pertinente.
- Determinar próxima fecha.
- Generar alerta.
- Contactar a la familia.
- Registrar respuesta.
- Reprogramar si no desea el servicio.
- Incorporar a ruta cuando sea autorizado.
- Actualizar automáticamente la próxima fecha una vez realizado el servicio.

---

### 6.9. Autorización de servicios preventivos

Antes de realizar determinados servicios preventivos, TIMU requiere obtener autorización de la familia mediante formulario.

El flujo esperado es:

**Sistema identifica servicio próximo → comunicación → formulario de autorización → revisión → autorización/reprogramación → programación → realización.**

La información suministrada por la familia deberá quedar registrada y asociada a la mascota.

---

### 6.10. Estados de los servicios

La plataforma deberá permitir manejar estados como:

- Pendiente.
- Contactado.
- Autorizado.
- Programado.
- Confirmado.
- Realizado.
- Reprogramado.
- Cancelado.
- No autorizado.
- Sin respuesta.

Estos estados deberán permitir generar tareas, alertas y acciones posteriores.

---

### 6.11. Atención comercial automatizada

La plataforma deberá permitir implementar flujos de atención y calificación comercial a través de canales digitales.

El objetivo es que una familia que ingrese por WhatsApp u otros canales pueda iniciar una interacción guiada.

#### Información potencial:

- Especie.
- Edad.
- Sexo.
- Ubicación.
- Necesidades.
- Interés.
- Características de la mascota.
- Información relevante para determinar el plan.

El sistema deberá utilizar reglas previamente configuradas para recomendar el plan más adecuado.

#### Importante

La recomendación deberá considerar:

- Ciudad.
- Disponibilidad del plan.
- Condiciones comerciales vigentes.
- Características del usuario.

Por ejemplo, un plan que actualmente no esté disponible en Bogotá **no deberá ser recomendado allí**, pero la configuración deberá permitir habilitarlo posteriormente.

El usuario deberá poder escoger un plan diferente al recomendado.

---

### 6.12. Afiliación y creación automática de usuarios

La plataforma deberá permitir conectar los procesos de:

**Formulario → pago → afiliación → contrato → creación de perfil.**

Cuando una familia complete el formulario de afiliación, la información deberá poder alimentar automáticamente:

- Perfil de familia.
- Perfil de mascota.
- Plan.
- Datos de contacto.
- Información preventiva.
- Información necesaria para programación.

---

### 6.13. Alimentación automática del calendario preventivo

Los datos suministrados durante la afiliación, como:

- última desparasitación;
- producto utilizado;
- fecha;
- peso;
- vacunación;

deberán poder alimentar el calendario preventivo.

El sistema deberá calcular o identificar la fecha correspondiente y generar las tareas necesarias.

---

### 6.14. Gestión clínica veterinaria

La plataforma deberá contemplar un módulo de gestión clínica.

#### Historia clínica

Debe permitir registrar:

- Consultas.
- Motivo de consulta.
- Hallazgos.
- Diagnósticos.
- Tratamientos.
- Evoluciones.
- Procedimientos.
- Seguimientos.
- Exámenes.
- Órdenes médicas.
- Kardex.
- Archivos adjuntos.

---

### 6.15. Carnet preventivo digital

Cada mascota deberá contar con un registro preventivo que permita consultar:

- Vacunaciones.
- Desparasitación interna.
- Desparasitación externa.
- Productos utilizados.
- Fechas.
- Próximas fechas.

Este módulo deberá alimentarse, cuando corresponda, de los servicios realizados desde la gestión de rutas preventivas.

---

### 6.16. Segmentación

La plataforma deberá permitir segmentar usuarios y mascotas por diferentes variables, por ejemplo:

- Edad.
- Especie.
- Plan.
- Ciudad.
- Zona.
- Estado de afiliación.
- Grupo familiar.
- Servicios.
- Condiciones preventivas.
- Otros criterios definidos posteriormente.

La segmentación deberá poder utilizarse para:

- Campañas.
- Comunicaciones.
- Seguimiento.
- Reportes.
- Acciones comerciales.

---

### 6.17. Atención veterinaria virtual

TIMU requiere facilitar la atención veterinaria mediante canales digitales.

La plataforma deberá permitir:

- Registrar solicitudes de orientación.
- Asociar la conversación al paciente.
- Consultar antecedentes.
- Consultar historial.
- Registrar la atención.
- Generar seguimiento.
- Guardar la interacción.

Adicionalmente, podrá contemplarse un sistema de **plantillas y respuestas previamente estructuradas**, aprobadas por el equipo médico, para agilizar consultas frecuentes.

La herramienta deberá funcionar como apoyo al profesional y **no sustituir el criterio médico veterinario**.

---

### 6.18. Comunicaciones masivas y campañas

La plataforma deberá permitir crear campañas dirigidas a segmentos específicos.

Ejemplos:

- Campañas preventivas.
- Recordatorios.
- Comunicaciones comerciales.
- Información institucional.
- Campañas por especie.
- Campañas por zona.
- Campañas por plan.

Deberá permitir:

- Seleccionar audiencia.
- Crear mensaje.
- Enviar mediante los canales disponibles.
- Registrar interacción cuando la integración lo permita.
- Mantener trazabilidad.

---

### 6.19. Comunicación por WhatsApp

WhatsApp constituye actualmente uno de los principales canales comerciales y de atención de TIMU.

La solución propuesta deberá indicar:

- Qué integración con WhatsApp ofrece.
- Si utiliza WhatsApp Business Platform/API.
- Qué funcionalidades permite.
- Qué costos adicionales genera.
- Qué límites existen.
- Qué automatizaciones permite.
- Cómo se gestionan las plantillas.
- Cómo queda registrada la conversación.

---

### 6.20. Encuestas de satisfacción

Este proceso deberá incorporarse como un flujo independiente.

Una vez culminado un servicio o atención, la plataforma deberá permitir activar automáticamente una comunicación a la familia mediante WhatsApp u otro canal disponible.

#### Flujo esperado:

**Servicio realizado → cierre de atención → envío automático de encuesta → respuesta → registro → análisis.**

La respuesta deberá quedar almacenada y asociada a:

- Familia.
- Mascota.
- Servicio.
- Fecha.
- Profesional, cuando corresponda.

La información deberá poder consultarse posteriormente y, de ser necesario, exportarse a Excel u otro formato.

#### Objetivo

Medir:

- Satisfacción.
- Experiencia.
- Calidad percibida.
- Posibles inconformidades.
- Oportunidades de mejora.

---

### 6.21. Seguimiento post atención

Después de determinadas atenciones, la plataforma deberá permitir generar automáticamente un seguimiento a la familia.

Ejemplo:

> “¿Cómo sigue [mascota] después de la atención? ¿Tienen alguna duda con la medicación o las recomendaciones?”

El sistema deberá permitir:

- Configurar cuándo se realiza el seguimiento.
- Enviar comunicación.
- Registrar respuesta.
- Generar alerta si la familia manifiesta una novedad.
- Crear tarea para el equipo.
- Mantener trazabilidad.

Esto busca que TIMU no solamente cierre una atención, sino que **acompañe al usuario posteriormente**.

---

### 6.22. Gestión con clínicas aliadas

La plataforma deberá permitir registrar solicitudes provenientes de clínicas veterinarias aliadas.

Por ejemplo:

**Clínica aliada → paciente requiere hospitalización → TIMU valida plan → valida beneficio disponible → valida estado de pago → calcula/indica descuento → registra solicitud.**

El sistema deberá identificar:

- Familia.
- Mascota.
- Plan.
- Estado de afiliación.
- Estado de pago.
- Beneficio disponible.
- Utilización previa del beneficio.
- Descuento o condición aplicable.

Todo el proceso deberá quedar registrado.

---

### 6.23. Estados de afiliación

La plataforma deberá manejar como mínimo:

- Activo.
- Moroso.
- Congelado.
- Cancelado.
- Retirado.

Los cambios de estado deberán afectar automáticamente los procesos relacionados.

Por ejemplo:

**Usuario cancelado → deja de aparecer en tareas preventivas y procesos activos.**

**Usuario congelado → se suspenden los servicios de acuerdo con las reglas configuradas.**

---

## 7. AUTOMATIZACIONES TRANSVERSALES

Además de las funcionalidades anteriores, la plataforma deberá permitir crear automatizaciones basadas en:

- Fechas.
- Estados.
- Eventos.
- Respuestas.
- Condiciones del plan.
- Datos de la mascota.
- Pagos.
- Servicios realizados.
- Ubicación.
- Segmentación.

Las automatizaciones deberán poder ampliarse posteriormente.

---

## 8. DASHBOARD Y GESTIÓN GERENCIAL

La plataforma deberá permitir generar información para la toma de decisiones.

Inicialmente se consideran relevantes:

#### Comercial

- Leads.
- Conversión.
- Ventas.
- Fuente del lead.
- Plan adquirido.
- Seguimientos pendientes.

#### Usuarios

- Usuarios activos.
- Nuevos usuarios.
- Cancelaciones.
- Renovaciones.
- Morosidad.

#### Servicios

- Servicios realizados.
- Servicios pendientes.
- Servicios preventivos.
- Servicios reprogramados.

#### Experiencia

- Satisfacción.
- Encuestas respondidas.
- Inconformidades.
- Seguimientos pendientes.

El proveedor deberá indicar qué dashboards están incluidos en la propuesta inicial.

---

## 9. INTEGRACIONES

El proveedor deberá indicar la capacidad de integración con:

- WhatsApp.
- Formularios.
- Correo electrónico.
- Google Calendar u otros calendarios.
- Herramientas de pago.
- Hojas de cálculo.
- Página web.
- Redes sociales, cuando técnicamente sea posible.
- APIs externas.
- Otras herramientas actualmente utilizadas por TIMU.

También deberá indicar si las integraciones están:

**incluidas / requieren costo adicional / requieren desarrollo.**

---

## 10. MIGRACIÓN DE INFORMACIÓN

TIMU actualmente utiliza diferentes herramientas, hojas de cálculo y sistemas para administrar información.

El proveedor deberá indicar:

- Si puede realizar migración de datos.
- Qué formatos soporta.
- Qué información puede migrarse.
- Qué proceso utilizará.
- Qué costo tiene.
- Cómo garantiza integridad de la información.

---

## 11. SEGURIDAD Y PROPIEDAD DE LOS DATOS

La propuesta deberá especificar:

- Sistema de autenticación.
- Roles y permisos.
- Control de acceso.
- Copias de seguridad.
- Recuperación de información.
- Protección de datos.
- Registro de actividad.
- Seguridad de la información.
- Disponibilidad del sistema.
- Infraestructura utilizada.
- Ubicación del almacenamiento cuando sea relevante.

#### Propiedad de la información

Los datos generados y almacenados por TIMU deberán permanecer bajo control de TIMU.

El proveedor deberá indicar:

- Cómo se exportan los datos.
- En qué formatos.
- Qué sucede con la información si termina la relación contractual.
- Si existe algún costo de migración o exportación.
- Qué información puede ser recuperada.

---

## 12. USUARIOS Y PERMISOS

La plataforma deberá permitir manejar diferentes perfiles, por ejemplo:

- Administrador.
- Gerencia.
- Comercial.
- Atención al cliente.
- Operaciones.
- Personal médico.
- Otros perfiles que puedan incorporarse posteriormente.

Cada perfil deberá contar con permisos diferenciados de acuerdo con sus funciones.

---

## 13. EXPERIENCIA DE USUARIO

La solución deberá procurar una interfaz:

- Intuitiva.
- Fácil de aprender.
- Adaptable a dispositivos móviles.
- Adecuada para personal no técnico.
- Que reduzca pasos innecesarios.

El proveedor deberá indicar si la solución es:

- Web.
- Responsive.
- PWA.
- Aplicación móvil.
- SaaS.
- Desarrollo a medida.

---

## 14. ESCALABILIDAD FUTURA

La plataforma deberá permitir incorporar posteriormente funcionalidades adicionales.

Entre ellas podrían contemplarse:

- PWA para familias.
- Portal de usuarios.
- Autogestión de servicios.
- Consulta de historia.
- Carnet digital.
- Pagos.
- Nuevos módulos comerciales.
- Nuevas integraciones.
- Nuevas automatizaciones.
- Inteligencia artificial como herramienta de apoyo.
- Nuevos servicios y productos.

Estas funcionalidades **no necesariamente hacen parte de la primera fase**, pero la solución deberá evitar una arquitectura que impida su incorporación futura.

---

## 15. PROPUESTA DEL PROVEEDOR

Para facilitar la evaluación comparativa, cada proveedor deberá presentar:

#### A. Descripción de la solución

¿Qué plataforma propone y por qué considera que es adecuada para TIMU?

#### B. Cumplimiento funcional

Indicar para cada requerimiento:

- Cumple.
- Cumple parcialmente.
- Requiere desarrollo.
- No disponible.

#### C. Tecnología

Indicar:

- Plataforma.
- Arquitectura.
- Infraestructura.
- Base de datos.
- Integraciones.
- Escalabilidad.

#### D. Implementación

Indicar:

- Tiempo estimado.
- Etapas.
- Configuración.
- Migración.
- Pruebas.
- Puesta en producción.

#### E. Capacitación

Indicar:

- Número de sesiones.
- Modalidad.
- Material entregado.
- Acompañamiento inicial.

#### F. Soporte

Indicar:

- Canales.
- Horarios.
- Tiempos de respuesta.
- SLA, si aplica.

#### G. Garantía

Indicar duración y condiciones.

#### H. Costos adicionales

Especificar claramente:

- Licencias.
- Usuarios adicionales.
- WhatsApp.
- Mensajería.
- Hosting.
- Integraciones.
- Mantenimiento.
- Soporte.
- Actualizaciones.
- Desarrollo adicional.

---

## 16. MODELO ECONÓMICO

La cotización deberá diferenciar claramente:

#### Implementación inicial

$\_\_\_\_\_\_\_\_\_\_

#### Licencia / suscripción/alquiler o cualquier pago que TIMU deba seguir haciendo

$\_\_\_\_\_\_\_\_\_\_ mensual/anual

#### Desarrollo personalizado

$\_\_\_\_\_\_\_\_\_\_

#### Integraciones

$\_\_\_\_\_\_\_\_\_\_

#### Migración

$\_\_\_\_\_\_\_\_\_\_

#### Capacitación

$\_\_\_\_\_\_\_\_\_\_

#### Soporte

$\_\_\_\_\_\_\_\_\_\_

#### Otros

$\_\_\_\_\_\_\_\_\_\_

#### VALOR TOTAL DE LA PROPUESTA

$\_\_\_\_\_\_\_\_\_\_

El proveedor deberá especificar si los valores incluyen IVA.

---

## 17. CRITERIOS DE EVALUACIÓN

TIMU evaluará las propuestas considerando:

| Criterio | Peso |
| --- | --- |
| Cumplimiento de requerimientos funcionales | 30% |
| Automatización y capacidad de optimización | 15% |
| Integraciones | 10% |
| Seguridad y gestión de información | 10% |
| Escalabilidad | 10% |
| Implementación y soporte | 10% |
| Experiencia del proveedor | 5% |
| Costo total | 10% |
| **TOTAL** | **100%** |

La selección del proveedor no se realizará exclusivamente por precio.

Se priorizará la alternativa que presente la **mejor relación entre funcionalidad, capacidad de crecimiento, seguridad, soporte, costo y correspondencia con las necesidades reales de TIMU**.

---

## 18. RESULTADO ESPERADO

TIMU busca que la implementación permita pasar de una operación basada en múltiples herramientas y procesos manuales a una **gestión integrada y automatizada**, donde la información fluya entre los diferentes procesos.

El resultado esperado es una plataforma que permita:

> **Captar → convertir → afiliar → gestionar → prevenir → atender → hacer seguimiento → medir → fidelizar.**

Y que, a medida que TIMU crezca, pueda incorporar nuevos procesos sin tener que reconstruir su infraestructura tecnológica.

---

## 19. CONSIDERACIÓN FINAL PARA EL PROVEEDOR

> TIMU no busca únicamente adquirir un CRM o una base de datos de clientes. Busca construir una infraestructura digital que permita integrar su operación comercial, preventiva, veterinaria y de experiencia del usuario.
>
> La plataforma deberá contribuir a que el equipo pueda dedicar menos tiempo a tareas repetitivas y mayor tiempo a actividades de alto valor para las familias y para el crecimiento de la empresa.
>
> La propuesta deberá, por tanto, considerar no solamente las funcionalidades actuales, sino la capacidad de evolución de la solución frente al crecimiento futuro de TIMU.
