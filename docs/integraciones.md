# Integraciones

Cada servicio externo vive detrás de un cliente en `backend/app/integrations/` y se configura
solo con variables de `backend/.env.example`. Ningún dominio llama a una API externa por su
cuenta. Con las variables vacías, la integración se apaga y la plataforma sigue funcionando
sin ella; la excepción es el almacenamiento S3, que el compose levanta en local.

**Estado de validación:** ninguna integración se ha probado todavía contra el proveedor
real desde el repositorio. Las pruebas usan dobles: `httpx.MockTransport` (fixture `red` de
`tests/test_integraciones.py`), almacenamiento en memoria (fixture `almacenamiento`) y
eventos de la pasarela firmados en la prueba (`_evento` de `tests/test_cartera.py`). Lo que
falta validar está en [pendientes externos](pendientes-externos.md); cuánto cuesta cada una,
en [costos](costos-infraestructura.md).

| Integración | Para qué | Código | Sin configurar |
| --- | --- | --- | --- |
| Wompi | Pagos: afiliación, alta de peludos, cuotas del portal y cobro recurrente | `integrations/payments.py`, `modules/cartera/pasarela.py` | El enlace sale sin llave y la pasarela lo rechaza; los eventos sin secreto solo se aceptan en local |
| WhatsApp (Meta Cloud API) | Avisos por plantilla, conversación comercial, estados de entrega | `integrations/whatsapp.py`, `modules/comunicaciones` | El mensaje queda como enviado con `id_externo = no_configurado` y no sale |
| Google Maps Platform | Geocodificar direcciones y matriz de tiempos para las rutas | `integrations/geocodificacion.py`, `integrations/mapas.py`, `modules/rutas/distancias.py` | Distancias estimadas en línea recta |
| IA (Claude; decidido pasar a Gemini) | Bot comercial y borradores de orientación virtual | `integrations/claude.py`, `modules/ia` | Flujos sin IA |
| Correo (SMTP) | Enlaces de registro y de cuenta, reportes programados | `integrations/correo.py` | Se registra en el log y no se envía |
| Almacenamiento S3 | Fotos, contratos, carnets, fórmulas, documentos y respaldos | `integrations/storage.py` | Requerido |
| Sentry | Errores de la API y de los workers | `configurar_sentry` | Desactivado |

## Decisiones del 2026-11-16

Tomadas con el usuario al preparar la reunión de integraciones con TIMU. Lo que tiene que hacer TIMU
en cada una, paso a paso, y las opciones de lo que falta decidir están en el documento para la
cliente: [integraciones para TIMU](integraciones-timu.md), la versión en Markdown del Word y el PDF
«TIMU - Integraciones» que se le entregaron. Su fuente de verdad son los requisitos del
[documento de requerimientos](documento-requerimientos-funcionales.md).

| Integración | Decisión | Lo que falta de nuestro lado |
| --- | --- | --- |
| Pagos | **Wompi** (no PayU ni Refacil) | La prueba de punta a punta en el sandbox ([pendientes externos](pendientes-externos.md)) |
| WhatsApp | **El número actual de TIMU.** El documento deja tres formas: A, coexistencia con la app WhatsApp Business (recomendada); B, el número solo en la plataforma; C, un número nuevo | Con A: registrar los mensajes que el equipo escribe desde la app (Meta los reenvía como «echoes»; hoy `_registrar_entrante` no los recoge). Con B o C: mostrar fotos, audios y documentos (hoy se guarda `[image]`, `[audio]`…). **2026-11-22:** la coexistencia solo se conecta por un *Solution Partner* o *Tech Provider*, no desde la app de TIMU; la ruta se vuelve a decidir con TIMU ([lo que falta en el código](pendiente-en-el-codigo.md)). Y la verificación de la empresa no es necesaria para empezar: sin ella el límite es de 250 destinatarios al día fuera de la ventana de 24 horas ([límites de Meta](https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits)) |
| Correo | **Google Workspace**, que TIMU ya tiene (cuenta de envío con contraseña de aplicación o retransmisión SMTP; SPF, DKIM y DMARC) | `SMTP_FROM` vale `no-responder@timu.co` por defecto: el dominio real es `timu.com.co` |
| Dominio | **La plataforma reemplaza la web actual en `timu.com.co`** (sin subdominio). El cambio de DNS no puede tocar los registros del correo y conviene hacerlo después de la verificación de Meta | La portada pública, que estaba fuera de alcance ([hoja de ruta](hoja-de-ruta-rediseno.md)) |
| Google Maps | Decidida (cuenta de Google Cloud de TIMU) | La Distance Matrix API que usa `integrations/mapas.py` quedó como «legacy»: un proyecto nuevo puede no habilitarla. Pasar a la Routes API (`computeRouteMatrix`) |
| IA | Gemini (decidido el 2026-11-10) | Adaptar el conector |
| Mapa visual de las rutas | **Google Maps** (Maps JavaScript API, opción A del documento; lo eligió TIMU y lo informó el usuario el 2026-11-21) | Construir el mapa (`6.7`, [pendientes externos](pendientes-externos.md#mapa-de-las-rutas-requisito-67-r2-pan-06)). Clave de navegador aparte de la del servidor, restringida a timu.com.co, y un límite diario de cargas en la consola de Google para no pasar de las 10.000 gratis al mes |
| Calendario | Por decidir. La propuesta firmada lo da como incluido: «Integraciones (WhatsApp, pasarela de pago, calendario) — Incluido» | Nada construido todavía. Recomendado: calendario ICS suscribible más invitación en las confirmaciones |
| Hojas de cálculo, formularios, redes, APIs externas | Por decidir (opciones en el documento) | El 6.20 pide exportar las encuestas a Excel y hoy no se puede (`Sección 8` dice «cualquier vista» y solo cubre el dashboard, la liquidación y los destinatarios) |

## Wompi (pagos)

Variables: `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_EVENTS_SECRET`,
`WOMPI_INTEGRITY_SECRET`, `WOMPI_API_URL` y `PAYMENTS_PROVIDER` (solo admite `wompi`).

**Checkout web** (`construir_link_pago`). Enlace a `checkout.wompi.co` con la firma de
integridad `SHA256(referencia + monto en centavos + moneda + [fecha de expiración +] secreto)`.
El registro en línea y el alta de peludos mandan `expiration-time` (24 h, ISO 8601 en UTC con
el formato `2026-11-11T14:30:00.000Z`), y esa fecha entra en la firma.

**Cada pago se reconoce por el prefijo de su referencia**, que decide quién lo procesa al
aprobarse (`@pasarela.al_aprobar`):

| Prefijo | Origen | Al aprobarse |
| --- | --- | --- |
| `AFI-` | Afiliación asistida y registro en línea | `afiliaciones.service.completar` |
| `ALT-` | Alta de un peludo desde el portal | `afiliaciones.altas.completar` |
| `POR-` | Pago de cuotas desde el portal | `cartera.aplicar_pago` |
| `REC-` | Cobro recurrente con tarjeta tokenizada | `cartera.aplicar_pago` |

Un manejador se registra al importar su módulo, así que tiene que importarse en la API y en
el worker.

**Eventos.** `POST /api/v1/webhooks/pagos` verifica el checksum (`signature.properties` más el
timestamp y `WOMPI_EVENTS_SECRET`), guarda el evento (idempotente por su id) y lo procesa el
worker. Un pago aprobado no retrocede por un evento tardío, y el monto aprobado tiene que
coincidir con el del pago. `recuperar_transaccion` consulta un evento perdido y
`conciliar_pendientes` (beat) revisa los pagos que siguen pendientes.

**Lo que no se paga.** El registro en línea y el alta de peludos se cancelan a las 48 h del
último enlace (`afiliaciones.cerrar_registros_sin_pago`, beat), y su pago pendiente pasa a
`anulado`. Tras un rechazo, «Intentar de nuevo» da otro pago con referencia nueva a la misma
solicitud; las anteriores quedan en `referencias_anteriores`. Si se aprueba una referencia
anterior (el reintento propio de Wompi, que usa la misma), ese pago cuenta. Si se pagan las
dos, queda la tarea «Pago doble de un registro en línea».

**Cobro recurrente.** `ClienteWompi` tokeniza la tarjeta (token de aceptación y fuente de
pago) y `cartera.pasarela.cobrar_recurrentes` cobra cada cuota fuera de la transacción del
lote, con reintentos según `COBRO_RECURRENTE_REINTENTOS_DIAS`. Depende de la habilitación
comercial de Wompi (`6.2`).

## WhatsApp Business (Meta Cloud API)

Variables: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`,
`WHATSAPP_API_VERSION` y `WHATSAPP_APP_SECRET`. Aparte, el WhatsApp al que escribe quien visita la
portada o se afilia y tiene una duda (la portada, el registro en línea y su pago rechazado) no es una
variable de entorno desde `R3-PUB-04`: lo escribe Administración → Datos de TIMU, y lo lógico es que
sea el número que TIMU elija en la sección 3.1 del documento de integraciones. En local, `datos_demo`
siembra uno ficticio (solo corre con `ENVIRONMENT=local`); desplegado empieza vacío, y vacío la
portada y el registro no ofrecen WhatsApp ([pendientes externos](pendientes-externos.md#valores-provisionales)).

- **Envío** por cola, con reintentos y traza por destinatario (`comunicaciones.encolar_*`).
  Fuera de la ventana de 24 horas que abre un mensaje de la persona solo salen plantillas
  aprobadas; el texto libre solo dentro de ella. Quien pide no recibir más queda en
  `bajas_comunicaciones`.
- **Webhook:** `GET /api/v1/webhooks/whatsapp` responde la verificación con
  `WHATSAPP_VERIFY_TOKEN`; `POST` valida la firma `X-Hub-Signature-256` con
  `WHATSAPP_APP_SECRET` y registra estados de entrega y mensajes entrantes, que atiende la
  conversación comercial.

**Plantillas que el sistema envía.** Cada una tiene que estar aprobada en Meta con el mismo
nombre y las mismas variables:

| Plantilla | Cuándo | Dónde |
| --- | --- | --- |
| `bienvenida` | Al activarse una afiliación | `afiliaciones/service.py` |
| `completar_afiliacion` | Registro en línea pagado, y otra vez a las 24 h sin formulario | `afiliaciones/enlaces.py` |
| `activar_cuenta`, `recuperar_clave` | Enlace para crear o cambiar la contraseña del portal | `auth/service.py` |
| `codigo_ingreso` | Ingreso al portal con código | `auth/service.py` |
| `cuota_vencida`, `aviso_mora`, `aviso_congelamiento` | 1, 5 y 15, y 25 días de mora (reglas configurables) | `reglas/datos.py` |
| `afiliacion_congelada`, `afiliacion_reactivada` | Cambio de estado del contrato | `cartera/service.py` |
| `recordatorio_preventivo` | Días antes de un evento preventivo (`PREVENTIVO_ANTICIPACION_DIAS`) | `preventivos/service.py` |
| `ventana_llegada`, `tecnico_en_camino` | Ruta del día | `rutas/service.py` |
| `encuesta_satisfaccion`, `seguimiento_post` | Tras un servicio (configurables por tipo) | `encuestas/service.py` |
| `respuesta_virtual` | Respuesta de orientación virtual fuera de la ventana | `clinica/service.py` |
| La que elija el equipo | Campañas y reglas de servicio | `campanas`, `servicios` |

Desde el 1 de octubre de 2026 Meta cobra también las plantillas de utilidad dentro de la
ventana de 24 horas, y las respuestas de servicio después de las primeras 1.000 al mes por
número.

## Google Maps Platform

Variable: `GOOGLE_MAPS_API_KEY`.

- **Geocodificación:** al guardar o cambiar una dirección, el evento
  `familia.ubicacion_cambiada` encola `familias.geocodificar` en el worker.
- **Matriz de tiempos** para optimizar las rutas (`rutas/distancias.py`). Primero busca en
  `distancias_cache`, por coordenada redondeada a 4 decimales (unos 11 m), y pide a Google
  solo lo que falta, en bloques de 25 orígenes. Lleva un tope diario de elementos
  (`MAPS_TOPE_DIARIO`, 2.000 por defecto, contado en `consumo_mapas`). Sin clave, con el tope
  agotado o con el proveedor caído, estima por distancia en línea recta y
  `RUTA_VELOCIDAD_KMH`.
- **Optimización** con OR-Tools, solo en el worker (`integrations/routing.py`), con los
  parámetros `RUTA_*` de la configuración.

La matriz crece con el cuadrado de las visitas que se planifican juntas. El tope diario
acota el gasto, a cambio de rutas estimadas cuando se agota.

## IA

Variables: `ANTHROPIC_API_KEY`, `IA_MODELO` (por defecto `claude-haiku-5-5`, valor provisional) e
`IA_TIMEOUT_SEGUNDOS` (30). El tope de gasto mensual no es una variable: lo cambia Administración en
la pestaña de IA (tabla `configuracion_ia`, migración 0058, auditado). Siempre hay tope, de US$ 1 como
mínimo; al llegar a él, la IA se apaga hasta el mes siguiente. Lo calcula la plataforma con el costo
de cada consulta (`claude.costo`), así que no es el saldo de la cuenta del proveedor.

- **Un solo punto de integración** (`modules/ia`). Los prompts tienen versiones: cada una
  nace en borrador y solo se activa tras correr sus casos de evaluación. Cada consulta queda
  en `consultas_ia` con tokens, costo y latencia. Al agotar el presupuesto del mes, la
  consulta no se hace (`presupuesto_agotado`) y el flujo sigue sin IA.
- **Usos:** `comercial_guion` responde dentro del guion aprobado en la conversación
  comercial de WhatsApp y pasa a un asesor cuando la pregunta se sale de él.
  `veterinario_borrador` redacta un borrador para la orientación virtual, que siempre aprueba
  un profesional.
- **Decidido pasar a Gemini:** qué falta y por qué, en
  [pendientes externos](pendientes-externos.md).

## Correo (SMTP)

Variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM`. Sin
`SMTP_HOST` el correo se registra en el log y no se envía. Lo usan los enlaces del registro en
línea, la activación y recuperación de la cuenta del portal y los reportes programados del
dashboard, que llevan el Excel adjunto.

## Almacenamiento S3

Variables `STORAGE_*` y `RESPALDO_BUCKET`. En desarrollo apunta al servicio `almacenamiento`
del compose (SeaweedFS); en producción, al bucket del proveedor, sin cambiar código. Nada se
sirve público: todo se entrega con `url_firmada()`, que firma con
`STORAGE_PUBLIC_ENDPOINT_URL` (el host que ve el navegador) y caduca a los
`STORAGE_URL_TTL_SEGUNDOS`. Los respaldos diarios van a `RESPALDO_BUCKET`
([respaldos](../infra/respaldos/README.md)). Anonimizar una familia purga sus ficheros
después de confirmar la transacción (`familias.purgar_archivos`).

## Sentry

Variable: `SENTRY_DSN`. La API y los workers reportan errores cuando está definida, y un
evento del outbox que agota sus reintentos llega como error (`outbox.abandonado`).
