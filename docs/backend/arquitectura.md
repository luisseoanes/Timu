# Backend: arquitectura y reglas transversales

Cómo se organiza el backend (FastAPI, SQLAlchemy, Celery) y las reglas que lo atraviesan. Las reglas, en una línea cada una, están en [`backend/CLAUDE.md`](../../backend/CLAUDE.md),
que es lo que lee cada sesión de Claude Code; aquí está el detalle completo, con el porqué de cada
una. Si una regla cambia, cambia en los dos sitios a la vez. Las rutas de código son relativas a
`backend/`.

## Arquitectura

Un directorio por dominio en `app/modules/<dominio>/`, con hasta cuatro piezas:
`models.py` (SQLAlchemy) · `schemas.py` (Pydantic) · `service.py` (lógica y consultas) ·
`router.py` (HTTP). `app/modules/familias/` es la referencia completa del patrón.

Las capas y la regla de no cerrar ciclos entre dominios están en
[`docs/estandares-calidad.md`](../estandares-calidad.md) y las vigila
`tests/test_arquitectura.py`, que también exige los imports de `app` en la cabecera del
fichero: ninguno dentro de una función (los de terceros opcionales o pesados, como `ortools`,
sí). Lo que es HTTP y conoce dominios vive en `app/api/` (`deps.py`,
`salud.py`), no en `app/core/`; los registros que agregan dominios (`app/models.py`,
`app/transiciones.py`), en `app/`.

Reglas que atraviesan todo el backend:

- **`app/models.py` es el registro único de modelos.** `autogenerate` sólo ve lo
  importado ahí: un modelo que no se añada a ese fichero no llega a las migraciones y,
  por tanto, tampoco a ninguna base de datos.
- **El esquema se aplica con `alembic upgrade head`**, nunca con `create_all`. La
  migración inicial (`F0-01`) crea las 21 tablas y está verificada en los dos sentidos:
  `upgrade` sobre base vacía y `downgrade base` que la deja limpia.
- **Un modelo nuevo exige su migración en el mismo cambio.** Las pruebas construyen el
  esquema aplicando las migraciones, y `tests/test_migraciones.py` compara el resultado
  contra los metadatos: si falta una migración, la suite falla en vez de descubrirse en
  el despliegue. Los índices y restricciones siguen la convención de nombres de
  `CONVENCION_NOMBRES` en `app/core/database.py`, para que una migración posterior
  pueda referirse a ellos por un nombre estable.
- **Los servicios de dominio son síncronos** (reciben `sqlalchemy.orm.Session`). Así los
  comparten los endpoints y los workers de Celery sin duplicar lógica: un router los
  llama con `await db.run_sync(service.funcion, arg1, ...)` —el puente oficial de
  SQLAlchemy, que no bloquea el event loop porque la E/S de base de datos sigue siendo
  async por debajo— y una tarea de Celery, dentro de `with sesion_worker() as db:` (Celery
  no es async: `asyncio.run()` dentro de una tarea crea un event loop por ejecución y no
  reaprovecha conexiones). Lo único que
  queda async en un servicio es E/S propia del endpoint (p. ej. `archivos.leer` de un
  `UploadFile`). Las integraciones HTTP (`httpx.Client`) también son síncronas: se usan
  desde los workers.
- **La transacción la cierra `get_db`**, no los servicios. Las funciones de `service.py`
  hacen `flush()` para obtener IDs; el commit ocurre al terminar la petición, y el rollback
  ante cualquier excepción. No metas `commit()` en un servicio.
- **Autorización con `requiere`** (alias de `require_roles`, en `app/api/deps.py`):
  `dependencies=[Depends(requiere(Rol.ADMIN))]`, o `requiere(*INTERNOS)` para todo el
  equipo. **Ningún endpoint queda abierto por
  omisión** (F1-AUT-02): uno abierto a propósito declara `Depends(publico)`, y
  `tests/test_permisos.py` recorre todas las rutas y falla si alguna no declara ninguna
  de las dos, o si aparece una pública que no está en su lista.
- **Enums de dominio en `app/core/enums.py`**, no en cada módulo. Son `StrEnum` y viajan
  como cadenas en la API. Cuando tipan una columna, la columna es `EnumDb(Clase)`: un enum
  nativo de PostgreSQL llamado como la clase en snake_case (ver «Persistencia»).
- **Los estados de servicio pasan por `app/modules/servicios/state_machine.py`.** Rutas,
  portal y comunicaciones llaman a `aplicar()`; ningún módulo reimplementa el grafo de
  transiciones ni asigna `servicio.estado` a mano: `aplicar` valida la transición *y*
  publica el evento que dispara los efectos de 6.10.
- **Los listados devuelven `Page[T]`** de `app/schemas/common.py` (`items`, `total`,
  `limit`, `offset`), con filtros combinables como en `familias.service.listar`.
- **Los schemas de lectura no revalidan formatos** (`EmailStr`, `DocumentoCO`, `TelefonoCO`):
  al leer son `str`. Un dato guardado por SQL, o que una versión nueva del validador rechace,
  no puede tumbar la respuesta ni un listado entero. Se valida al escribir (`*Create`,
  `*Update`); `FamiliaRead` y `UsuarioRead` son la referencia.
- **Un PATCH con `model_dump(exclude_unset=True)` recibe también los `null` que se mandan.**
  `exclude_unset` deja fuera lo que no vino, no lo que vino vacío: `{"nombre": null}` llega como
  cambio. Un campo obligatorio se declara sin `None` en su schema de edición, o el servicio trata
  `None` como «sin cambio». Si no, falla Python (un 500: `editar_plantilla` lo daba hasta el
  2026-11-18) o la base, que lo frena con un 409 cuyo mensaje dice que el registro ya existe (la
  deuda está en [estándares de calidad](../estandares-calidad.md#integridad-de-la-información)).
- **Toda consulta pasa por `restringir()` de `app/core/scope.py`.** `require_roles`
  dice *quién puede llamar*; el alcance dice *qué filas ve*, y el portal de familias
  necesita las dos. Los servicios reciben un `Alcance` como primer argumento tras la
  sesión, y cada modelo visible desde el portal declara `__columna_familia__`. Un
  modelo que no lo declare hace fallar la consulta: **se falla cerrado, nunca abierto**.
  `familias` es la referencia del patrón.
- **Ningún módulo llama a `tarea.delay()` dentro de una transacción.** Se publica un
  evento con `app.core.outbox.publicar()`, que escribe en la misma transacción; si
  ésta revienta, el efecto externo se va con ella. El worker `outbox.drenar` lo
  despacha después. Los manejadores se registran con `@al_ocurrir("nombre.evento")`
  en `app/workers/tasks/<dominio>.py`, junto a la tarea que encolan, y se limitan a
  `celery_app.send_task(...)`: el trabajo pesado va en la tarea, no en el drenado. El
  nombre se declara en el dominio que lo publica (`EVENTO_X = declarar_evento("x.ocurrido")`)
  y se usa la constante; `EventoDominio` y `al_ocurrir` rechazan uno sin declarar. Un evento
  que agota `MAX_INTENTOS` se registra como `outbox.abandonado` (error, llega a Sentry).
- **Ningún dominio orquesta lo que no es suyo.** `familias` es la ficha (titular, mascotas,
  ubicación) y no importa ningún dominio de negocio. La baja de la familia, el alta y la baja
  de mascotas, la anonimización y el formulario público cruzan la ficha con el contrato: los
  orquesta `afiliaciones/ciclo.py`, síncronos y en la misma transacción, y sus rutas viven en
  `afiliaciones/router.py` con la misma URL bajo `/familias`, `/mascotas` y `/formularios`.
  La vida del contrato (vigente, cupo de mascotas, valor, cambio de plan) es de
  `cartera/contratos.py`; `planes` es solo el catálogo. Un caso de uso nuevo que cruce
  dominios se orquesta en el de arriba; si el router del de abajo lo llamara, la guarda de
  ciclos fallaría.
- **Un schema que leen dos routers va en `<dominio>/schemas.py`**, no en el router (otro dominio
  no puede importarlo). Si el servicio también usa sus `Literal`, se declaran en el schema y el
  servicio los importa de ahí: al revés se cierra un import circular (`afiliaciones/schemas.py`).
- **`comunicaciones` no depende de ningún dominio**: casi todos encolan en él. Quién es la
  familia de un número y quién contesta un mensaje entrante (encuesta, conversación
  comercial) se lo conecta `app/workers/tasks/comunicaciones.py` con
  `conectar_entrantes`; sin conectar, un entrante falla en lugar de quedar sin respuesta.
- **La traza de mensajes tapa los tokens de un solo uso.** `MensajeRead` cambia `?token=…` y
  `/encuesta/<token>` por `[oculto]` al responder (lo leía el equipo en Campañas y en la API). Un script
  que necesite uno, como `datos_demo` para activar la cuenta de Ana, lo lee de la base con
  `sesion_worker`, no de la API.
- **Las reglas se describen en palabras en `reglas/motor.py`** (`describir_condicion`,
  `describir_accion`, `campos`), y la API las da como `condicion_texto`, `accion_texto` y
  `campos_condicion`. Un campo, un estado o un evento nuevo lleva su nombre en `_CAMPOS`, `_VALORES` o
  `_NOMBRES_EVENTOS`: sin él, Administración lo enseña por su código.
- **Lo que da cada evento a sus reglas es un tipo** (`reglas/contextos.py`, `DEU-8`): una dataclass por
  evento (`CarteraAlerta`, `ServicioElegibilidad`…) que el módulo que evalúa construye y pasa a
  `reglas.evaluar`; mypy rechaza un dato que falte o sobre. De ella salen los campos que ofrece el
  editor de Administración (`GET /reglas/eventos`, con su tipo, sus comparaciones y los valores del
  catálogo), y al guardar se rechaza una condición sobre un dato que el evento no da o un valor que
  no está en el catálogo: antes se guardaba y la regla no aplicaba nunca, sin aviso. Las acciones de
  cada evento, con sus parámetros, están en `reglas/acciones.py`. Los planes llegan a `reglas` por
  `reglas.conectar_planes` (planes importa reglas). Una condición con grupos anidados solo se
  escribe por la API: el editor la lee en palabras y la conserva. La clave de un aviso
  (`notificar`) no la escribe el equipo: al crear sale del código de la regla y al editar se
  conserva, porque dice qué avisos ya se enviaron.
- **`tareas` no importa `servicios`** (que crea tareas): `servicios/service.py` le conecta al
  importarse cómo describir sus servicios (`tareas.conectar_servicios`) para nombrar cada tarea
  de la bandeja; sin conectar, el listado falla.
- **`servicios` no importa `preventivos`** (que agenda sus visitas): `preventivos/service.py` le
  conecta al importarse qué hacer cuando la visita de un preventivo se autoriza, se completa o se
  cancela (`servicios.conectar_al_cambiar_estado`, ver `docs/flujo-de-la-visita.md`); sin
  conectar, `cambiar_estado` falla.
- **`cartera` no importa `aliadas`** (que valida la cartera al remitir): `aliadas/service.py` le conecta al
  importarse qué hacer al cancelar un contrato (`cartera.conectar_al_cancelar`: corta la vigencia de las
  remisiones por usar); sin conectar, cancelar falla.
- **`catalogos` no importa `clinica`** (que lee el catálogo): `clinica/service.py` le conecta al
  importarse qué campos llena la consulta firmada (`catalogos.conectar_campos_de_la_consulta`), y el
  catálogo de tipos dice en cada paso si lo registra la consulta (`lo_registra_la_consulta`), para
  que el panel no copie la tabla; sin conectar, el catálogo de tipos falla.
- **Las cadenas que la API devuelve para mostrarse tal cual llevan tildes** (nombres y fórmulas
  de `dashboard/definiciones`); la regla de evitarlas es para docstrings y comentarios. Los
  mensajes de error aún no las llevan: es deuda, no la norma.
- **Una tarea que llama a un tercero con efectos (cobrar, enviar) no lo hace dentro de
  la transacción del lote.** Se registra el intento y se confirma, se llama al tercero
  fuera de cualquier transacción y se anota el resultado en otra
  (`cartera.pasarela.cobrar_recurrentes`). Los procesos diarios que recorren muchos
  registros aíslan cada uno en un savepoint: un dato raro no revierte el lote entero.
- **Los campos JSON usan `JSONTipo`** de `app/core/database.py`, que es JSONB en
  PostgreSQL (indexable con GIN) y JSON en el resto. Nunca el `JSON` de SQLAlchemy.
- **La sesión son dos cookies httpOnly**: la de acceso (JWT corto, lleva el `sid` de una
  fila de `sesiones` para poder revocarlo al instante) y la de renovación (opaca, rota en
  cada uso y solo viaja a `/api/v1/auth`). Reusar una de renovación ya rotada se trata
  como robo y cierra todas las sesiones del usuario; por eso el frontend comparte una
  única renovación entre peticiones simultáneas (`frontend/src/api/client.ts`).
- **Los tokens se firman y verifican con PyJWT**, y `decode_access_token` declara el
  algoritmo de forma explícita en lugar de aceptar el que venga en el token: confiar en
  esa cabecera permite un ataque de confusión de algoritmos. No vuelvas a introducir
  `python-jose`, que está sin mantener desde 2021 y arrastra CVE conocidas.
- **OR-Tools vive sólo en `requirements-worker.txt`**, no en la imagen de la API. La
  optimización de rutas (6.7) es CPU-bound: llamarla desde un endpoint async bloquearía
  el event loop, así que `app/integrations/routing.py` se invoca siempre desde una tarea
  de Celery. Una dependencia pesada que sólo use el worker va en ese fichero.
- **Los registros salen por `structlog`, no por `logging` a pelo.** Cada petición lleva
  su identificador en `X-Request-ID` (F0-02), que el middleware propaga a todas las
  líneas de log para poder seguirla de punta a punta. Sentry se activa solo si hay
  `SENTRY_DSN`, así que en local no estorba y en producción no se olvida.
- **Los adjuntos van a `app/integrations/storage.py`**, que habla S3. En desarrollo
  apunta al servicio `almacenamiento` del compose (SeaweedFS; MinIO dejó de publicar
  imágenes) y en producción al bucket del cliente: cambian las variables `STORAGE_*`,
  no el código. Nada se sirve público, todo con `url_firmada()`, que firma con
  `STORAGE_PUBLIC_ENDPOINT_URL` (el host que ve el navegador; en compose lo fija el propio
  compose).
- **Los PDF usan `app/core/marca_pdf.py`** (`PdfMarca`: logo, paleta, GeosansLight e Inter,
  que no estropean las tildes como las fuentes base del PDF), y sus piezas comunes: `cabecera`,
  `datos`, `titulo_seccion`, `tabla` y `parrafo`. Todos los documentos las usan (carnet, contrato,
  fórmula y comprobante) y dicen las cosas en palabras: nunca un código ni «ilimitado».
- **Un dato del equipo que la familia ve en el portal se guarda como constancia en la fila**
  (como `aplicado_por_nombre` en `eventos_preventivos`): RLS no le deja leer `usuarios`, y
  buscarlo al mostrarlo devolvería vacío sin error.

Integraciones (`app/integrations/`) y webhooks (`app/api/v1/webhooks.py`) están separados a
propósito: los webhooks son públicos y se validan por token de verificación (Meta) o firma
HMAC (pasarela), nunca por JWT. Su trabajo es responder rápido y encolar en Celery.
`@pasarela.al_aprobar(PREFIJO)` registra el manejador de un pago aprobado al importar su
módulo: tiene que importarse en la API y en el worker (`afiliaciones/altas.py` lo importan
`portal/router.py` y `workers/tasks/afiliaciones.py`).

Celery (`app/workers/`) corre en dos contenedores distintos: `worker` ejecuta y `beat`
programa. El `beat_schedule` está en `celery_app.py` en zona `America/Bogota`; las tareas
llevan nombre explícito (`cartera.revisar_mora`) porque el schedule las referencia por
cadena.

Configuración: `Settings` de `pydantic-settings` con `.env`. `DATABASE_URL` (rol de la
aplicación) y `DATABASE_URL_PROPIETARIO` (dueño del esquema) se calculan a partir de
`POSTGRES_*` y `APP_DB_PASSWORD`; `DATABASE_URL_OVERRIDE` y
`DATABASE_URL_PROPIETARIO_OVERRIDE` las sustituyen.

Tests: `httpx.AsyncClient` sobre ASGI contra PostgreSQL y `dependency_overrides[get_db]`
(ver `tests/conftest.py`). `pytest.ini` fija `asyncio_mode = auto`, así que las pruebas
async no necesitan decorador. Los servicios se llaman como en los routers, con
`await db.run_sync(...)`. El fixture `tareas` drena el outbox de la transacción de la
prueba con sus manejadores reales y registra lo que se habría encolado en Celery
(`await tareas.de("comunicaciones.enviar_mensaje")`); el fixture `almacenamiento`
sustituye S3 por memoria. `login(client, email)` devuelve la cabecera `Cookie` de esa
sesión, para las pruebas que alternan usuarios.
