# Perfiles y permisos

Qué hace cada perfil y qué ve, según la [Sección 12 del documento de
requerimientos](documento-requerimientos-funcionales.md): «Cada perfil deberá contar con permisos
diferenciados de acuerdo con sus funciones». Decidido con el usuario el 2026-11-19: **cada perfil hace
lo suyo y nada más**, cerrado en la API y en la base, no solo ocultando el menú. Cuando TIMU dé su
opinión se verá qué se junta; de inicio queda así.

Antes de esto el equipo tenía cuatro perfiles que leían casi todo (cada endpoint de lectura admitía a
`admin`, `comercial`, `operaciones` y `medico`), y solo las escrituras iban por perfil.

## Los perfiles

| Perfil | Código | Para qué (requisitos) |
| --- | --- | --- |
| Administrador | `admin` | Configura la plataforma: usuarios, planes, reglas, catálogos, plantillas de WhatsApp, IA y Datos de TIMU (12, 6.3, 6.5, 6.11, 6.19, 7, 11). **No ve nada operativo.** |
| Gerencia | `gerencia` | Mide: el tablero de la Sección 8, los exportables, los reportes programados, las encuestas y la liquidación de aliadas como informe (8, 6.20). Solo cifras agregadas; ninguna ficha. |
| Comercial | `comercial` | Capta, afilia y renueva: interesados y conversaciones, afiliación asistida, renovaciones, campañas y segmentos (6.4, 6.11, 6.12, 6.16, 6.18). |
| Atención al cliente | `atencion_cliente` | La familia afiliada en su día a día: ficha, cartera y pagos, solicitudes y pendientes por autorizar, autorizaciones preventivas, remisiones a aliadas, encuestas con novedad (6.1, 6.2, 6.3, 6.5, 6.6, 6.9, 6.20, 6.21, 6.22). |
| Operaciones | `operaciones` | Agenda y rutas: franjas, programación de lo autorizado, rutas, red de aliadas y su liquidación (6.5, 6.7, 6.8, 6.22). |
| Personal médico | `medico` | Atiende: su ruta y sus servicios, historia clínica, atención virtual, validación profesional, pendientes de una atención, aplicación de preventivos (6.5, 6.6, 6.8, 6.14, 6.17). |
| Familia | `familia` | Su portal (Sección 14). Sin cambios. |
| Clínica aliada | `aliada` | Valida sus remisiones y reporta la atención (6.22). Sin cambios. |

## Qué ve cada perfil del equipo

| Módulo | Administrador | Gerencia | Comercial | Atención | Operaciones | Médico |
| --- | --- | --- | --- | --- | --- | --- |
| Inicio | estado de la configuración | tablero (Sección 8) y reportes | embudo y renovaciones | mora, autorizaciones y novedades | la operación del día | su jornada |
| Familias | — | — | para afiliar y renovar | ficha completa, sin historia clínica | datos de la visita | — |
| Cartera | — | — | renovaciones | ✓, con la pasarela de pagos | — | — |
| Servicios | — | — | — | solicitudes y pendientes | agenda y franjas | los suyos |
| Rutas | — | — | — | — | ✓ | la suya |
| Preventivos | — | — | — | autorizaciones | agendar en ruta | aplicar |
| Clínica | — | — | — | — | — | ✓, con las respuestas aprobadas |
| Tareas | — | — | área comercial | áreas cartera y servicio al cliente | área operaciones | área médico |
| Comercial | — | — | ✓ | — | — | — |
| Campañas y segmentos | — | — | ✓ | — | — | — |
| Mensajes y bajas de WhatsApp | — | — | ✓ (da de baja) | ✓ (y quita la baja) | — | — |
| Encuestas | configuración | análisis: satisfacción del mes y todas las respuestas | — | respuestas con novedad (entra en las de 3 o menos) | — | — |
| Aliadas | — | liquidación (informe) | — | remisiones | clínicas, convenios y liquidación | — |
| Administración | ✓, con plantillas de WhatsApp y supresión de datos | — | — | — | — | — |

Decisiones del 2026-11-19, a pregunta del usuario:

- **El Administrador no ve nada operativo**: ni familias, ni cartera, ni historia clínica.
- **Cartera pasa de Comercial a Atención al cliente**; Comercial conserva las renovaciones (6.4).
- **La liquidación de aliadas es de Operaciones**; Gerencia la ve como informe.
- **Las remisiones las emite y anula Atención al cliente**: la remisión depende del estado de pago
  (6.22), que es de Cartera.
- **Las plantillas de WhatsApp las registra el Administrador** (6.19); Comercial las elige al
  crear una campaña.
- **Las respuestas de la atención virtual las aprueba el médico** (6.17: «aprobadas por el equipo
  médico»).
- **La supresión de datos (Ley 1581) la hace el Administrador sin ver la ficha**: busca por documento,
  ve solo el nombre del titular y confirma en rojo. Con un contrato vigente no se ofrece: la base no lo
  deja anonimizar y el contrato lo cancela antes Atención al cliente.
- **Los usuarios se vuelven a sembrar** con los perfiles nuevos (`datos_demo`).
- **Quitar una baja de WhatsApp lo hace Atención al cliente**, a pedido de la familia; Comercial da de
  baja pero no reactiva. Por eso Mensajes (los mensajes y las bajas) sale de Campañas a un módulo propio
  para Comercial y Atención.
- **El Inicio de Comercial, Atención al cliente y Operaciones es la línea de hoy de cada uno**: lo
  vencido, Hoy y lo que viene, con solo su trabajo, una sola acción verde y encima sus cifras del mes
  (la composición del Inicio de `R2-PAN-04`). La agenda de servicios solo entra en la de Operaciones.
  Gerencia conserva el tablero de la Sección 8 y el médico su jornada.
- **Las cifras de cada perfil, por función** (decidido el mismo día): Comercial, vigentes y
  afiliaciones con sus retiros (6.4, 6.12); Atención, recaudo, mora y satisfacción (6.2, 6.9, 6.20);
  Operaciones, rutas, satisfacción y servicios completados (6.7, 6.8). La API solo les sirve esas
  (`INDICADORES_POR_ROL` en `dashboard/service.py`); los exportables y los filtros siguen siendo de
  Gerencia.
- **El carnet de vacunas (6.15) lo ven Atención al cliente y el médico** (2026-11-20): Atención lo emite
  a la familia y el médico lo consulta; Operaciones agenda desde la bandeja de preventivos, que ya le
  dice qué toca. La historia clínica sigue siendo solo del médico: la ficha de la mascota solo
  enlaza a lo que el perfil puede abrir.
- **El Inicio del Administrador dice lo que falta configurar**: lo que impide que algo funcione
  (plantillas de WhatsApp que envía la plataforma o citan las reglas y no están aprobadas en el
  catálogo, con lo que deja de salir sin cada una; Datos de TIMU incompletos; usuarios inactivos),
  cada fila con su pestaña. Las acciones van todas iguales, sin verde (2026-11-20); la plantilla que no
  está registrada se registra desde ahí, con su código y su nombre ya puestos.

## Lo que se filtra por fila

Además de qué rutas puede llamar cada perfil:

- **Médico**: los servicios cuyo `profesional_id` es él y las rutas cuyo `responsable_id` es él. La
  historia clínica la lee de cualquier mascota: la atención virtual necesita los antecedentes de quien
  escribe (6.17).
- **Tareas**: cada perfil ve las de su área (`comercial` → Comercial; `cartera` y
  `servicio_cliente` → Atención al cliente; `operaciones` → Operaciones; `medico` → Médico).
  Una tarea solo se asigna a quien ve su área. Guarda quién la pidió (o qué regla la creó) y lo dice en
  la bandeja; quien la pide a otra área la sigue en «Pedidas por mí», sin trabajarla (2026-11-20).

## Pantallas que cruzan dominios

| Pantalla | Cómo cambia |
| --- | --- |
| Ficha de familia | Atención: todas las pestañas. Comercial: datos, mascotas, cartera (contrato y renovación) e historial. Operaciones: datos y servicios. |
| La línea de la familia | Solo las estaciones del perfil: cuotas para Atención y Comercial, servicios y preventivos para Atención y Operaciones. |
| Inicio | Uno por perfil. |
| Buscador de la barra | Solo para quien tiene Familias. |
| Administración | Pierde «Reportes y pasarela»: los reportes van al Inicio de Gerencia y la pasarela a Cartera. Gana «Plantillas de WhatsApp» y «Supresión de datos». |
| Campañas | Pierde «Encuestas» (a Atención y Gerencia) y «Plantillas de WhatsApp» (a Administración). |

## Cómo se hace cumplir

- **API**: cada ruta declara sus perfiles con `requiere(...)`. `tests/test_permisos.py` compara la
  matriz real con la esperada, ruta por ruta (`MATRIZ`): un perfil de más o de menos falla.
- **Base**: la matriz de RLS (`app/core/permisos_db.py`) da a cada perfil solo las tablas que tocan sus
  rutas, derivada con `TIMU_REGISTRO_ACCESOS`, y una migración congela sus políticas.
- **Panel**: el menú, las pestañas y las acciones salen de `lib/permisos.ts`, el mismo mapa que la API.
