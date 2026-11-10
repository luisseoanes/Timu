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
comercial de Wompi (`F1-CAR-08`).

## WhatsApp Business (Meta Cloud API)

Variables: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`,
`WHATSAPP_API_VERSION` y `WHATSAPP_APP_SECRET`.

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

Variables: `ANTHROPIC_API_KEY`, `IA_MODELO` (por defecto `claude-opus-5-5`),
`IA_PRESUPUESTO_MENSUAL_USD` (50) e `IA_TIMEOUT_SEGUNDOS` (30).

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
