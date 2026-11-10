# CLAUDE.md — backend

Reglas del backend (FastAPI, SQLAlchemy, Celery). Lo transversal —comandos, stack con un
solo comando, invariante del CI, commits— está en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
Las rutas de este fichero son relativas a `backend/`.

## Arquitectura

Un directorio por dominio en `app/modules/<dominio>/`, con hasta cuatro piezas:
`models.py` (SQLAlchemy) · `schemas.py` (Pydantic) · `service.py` (lógica y consultas) ·
`router.py` (HTTP). `app/modules/familias/` es la referencia completa del patrón.

Las capas y la regla de no cerrar ciclos entre dominios están en
[`docs/estandares-calidad.md`](../docs/estandares-calidad.md) y las vigila
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
- **`comunicaciones` no depende de ningún dominio**: casi todos encolan en él. Quién es la
  familia de un número y quién contesta un mensaje entrante (encuesta, conversación
  comercial) se lo conecta `app/workers/tasks/comunicaciones.py` con
  `conectar_entrantes`; sin conectar, un entrante falla en lugar de quedar sin respuesta.
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

## Persistencia: la base garantiza, Python explica

Toda regla que PostgreSQL puede hacer cumplir se hace cumplir en PostgreSQL. Python valida
antes para devolver un mensaje claro, pero la regla definitiva está en la base: si Python se
equivoca, o alguien escribe por SQL, la base rechaza la operación. Solo se quedan
exclusivamente en Python las reglas que dependen de un servicio externo o de la hora actual.
El plan completo y su avance están en [`docs/plan-persistencia.md`](../docs/plan-persistencia.md).

- **Dos roles de base de datos.** `timu` (`POSTGRES_USER`) es el dueño del esquema: solo lo
  usan Alembic y `inicializar`. `timu_app` lo crea la migración `0013`, sin superusuario ni
  `BYPASSRLS` ni permisos de DDL, y con él se conectan la API, los workers, los scripts **y
  las pruebas**. Con un rol privilegiado la base no aplica sus políticas, así que la API
  (`lifespan`), el worker (`worker_process_init`) y la suite (`conftest.py`) se niegan a
  arrancar si el rol conectado es superusuario o tiene `BYPASSRLS`. Una tabla nueva le llega
  a `timu_app` sola, por los permisos por defecto de la `0013`.
- **Cada transacción lleva el contexto de quién la hace.** `ContextoDb` (`rol`,
  `usuario_id`, `familia_id`, `clinica_id`, `request_id` y, para `publico`, `llaves`) vive en `session.info` y un listener
  `after_begin` lo fija con `set_config(..., true)` al empezar cada transacción: es local a
  ella, así que no se filtra a la siguiente petición que reutilice la conexión. `get_db`
  empieza en `"publico"`, `get_current_user` lo cambia al usuario y `get_alcance` añade la
  familia. `sesion_worker` y los scripts usan `SISTEMA`. Para cambiarlo a mitad de una
  transacción: `await db.run_sync(fijar_contexto, contexto)`. Sin contexto los ajustes
  quedan vacíos y lo que dependa de ellos se niega: se falla cerrado.
- **Todo conjunto cerrado es un enum de PostgreSQL.** Una columna que guarda un valor de
  una lista que fija el código (estado, tipo, canal, rol, prioridad…) se declara
  `mapped_column(EnumDb(MiStrEnum))`, nunca `String(n)`. Añadir, quitar o renombrar un valor
  exige su migración (`ALTER TYPE … ADD VALUE`, o recrear el tipo para quitar uno), escrita
  a mano porque el autogenerate no detecta cambios en los valores de un enum.
  `test_cada_enum_del_modelo_coincide_con_el_de_la_base` falla si el `StrEnum` y la base no
  tienen los mismos valores, y `test_ningun_conjunto_cerrado_queda_como_texto_libre` si una
  columna con nombre de conjunto (`estado`, `tipo`, `canal`…) sigue siendo texto, salvo las
  abiertas de `_ABIERTAS` con su motivo. Dos trampas: un enum ordena por su declaración, así
  que `aplicar_orden` y cualquier `ORDER BY` que deba ser alfabético usan `cast(col, String)`;
  y `case({...}, value=col)` compara con `varchar`, así que también lleva el `cast`. El valor
  por defecto va en Python (`default=`), no en un `server_default` que el modelo no declare.
  Un `CHECK` que use un valor recién añadido con `ADD VALUE` compara `estado::text`: el valor
  no se puede usar en la transacción que lo crea. Quitarlo en el `downgrade` exige soltar y
  recrear antes `tr_<tabla>_transicion_estado`, que depende de la columna.
- **Toda referencia a un catálogo es una clave foránea.** Una columna que guarda la
  ciudad, la especie, un plan, una plantilla o una regla (`ciudad`, `especie`, `*_codigo`)
  lleva `ForeignKey` a su catálogo, con `onupdate="CASCADE"` si apunta a un código o un
  nombre, para que una corrección en el catálogo se propague en vez de bloquearse. Las
  ciudades se guardan por nombre canónico (`ciudades.nombre` es único). Python sigue
  validando antes para dar el mensaje (`catalogos.ciudad_valida`).
  `test_toda_referencia_a_un_catalogo_tiene_llave_foranea` falla si falta una, salvo las de
  `_REFERENCIAS_SIN_LLAVE` con su motivo.
- **Las invariantes de cada fila son `CHECK` y las de «solo uno» son índices únicos.** Se
  declaran en el modelo, junto a sus columnas: `__checks__ = {"nombre": "expresión SQL"}`
  (rangos, formatos, importes no negativos, campos que exige un estado: «firmada ⇒ firma y
  diagnóstico», «pagada ⇒ cubre su valor») y `__unicos__ = {"nombre": (["columnas"],
  "condición" | None)}` («un contrato vigente por familia»). `_restricciones_de_la_tabla`
  las convierte en `ck_<tabla>_<nombre>` y `uq_<tabla>_<nombre>`. El autogenerate no detecta
  un `CHECK` nuevo en una tabla existente ni la condición de un índice parcial: su migración
  se escribe a mano, con la expresión copiada dentro, y antes se comprueba contra los datos
  (`SELECT count(*) … WHERE NOT (expresión)`). Comprobar y luego insertar no es una regla:
  deja una ventana a dos peticiones simultáneas. Un índice único parcial no es diferible,
  así que el código que retira la versión activa y activa otra hace `flush()` entre los
  dos pasos. `test_cada_check_y_cada_unico_del_modelo_estan_en_la_base` compara modelo y
  base en los dos sentidos. Teléfonos: E.164 con `+` en todas las tablas
  (`normalizar_telefono`); `telefono_whatsapp` quita el `+` solo al enviar a Meta.
- **Los cambios de estado los valida la base.** `app/transiciones.py` tiene el grafo de
  cada entidad con estado (servicios y pendientes los importa de su módulo); la tabla
  `transiciones_estado` guarda las mismas aristas y el trigger `validar_transicion`
  (`BEFORE UPDATE OF estado`) rechaza cualquier cambio que no esté en ella, con
  `check_violation`. La tabla solo la escribe el dueño del esquema: añadir una transición
  exige editar el módulo y escribir la migración que inserta la arista, y
  `test_los_grafos_de_la_base_son_los_del_codigo` falla si no coinciden o falta un trigger.
  Una entidad nueva con estado lleva su grafo, su trigger y su migración. Quedan fuera, con
  el motivo en el módulo, los estados que cambian por información externa o por decisión
  libre del equipo (mensajes, pagos, cuotas, afiliación, embudo, plantillas de Meta).
- **La auditoría la escribe la base.** Un modelo que herede `Auditable` lleva el trigger
  `tr_<tabla>_auditoria`, que con `auditar()` registra cada alta, edición, cambio de estado
  o borrado, también los hechos por SQL, con el usuario y la petición del contexto de la
  transacción. Python no escribe la bitácora: `auditoria` solo admite `SELECT` para
  `timu_app`, y un trigger rechaza cualquier `UPDATE` o `DELETE` que no venga del dueño. Lo
  que es constancia de algo no cambia una vez escrito (`INMUTABLES` en
  `app/core/auditoria.py`, trigger `inmutable()`), y una historia clínica firmada solo pasa
  a `corregida`. Un modelo `Auditable` o una tabla de `INMUTABLES` sin su trigger hace
  fallar `test_cada_tabla_auditable_e_inmutable_tiene_su_trigger`; añadir uno exige su
  migración con el `CREATE TRIGGER`.
- **Nada de negocio se borra.** `timu_app` solo tiene `DELETE` en las tablas de estado técnico
  de `BORRABLES` (`app/core/database.py`); los permisos por defecto ya no lo conceden a una
  tabla nueva. Una baja, una anulación o un reemplazo es un estado o una marca (`activo`,
  `reactivada_en`, `dada_de_baja_en`), y las colecciones de negocio no usan `delete-orphan`.
  El único borrado es la función `anonimizar_familia()` (habeas data, Ley 1581), que solo
  admite el contexto de un administrador y se niega con un contrato vigente: sustituye los
  datos personales y su rastro en la bitácora, conserva lo clínico y lo contable, y devuelve
  las claves de los ficheros que `familias.purgar_archivos` borra del almacenamiento después
  de confirmar. `test_anonimizar_no_deja_datos_personales` recorre todas las tablas: un dato
  personal nuevo lo borra esa función (con su migración) o su tabla va en `CONSERVAN_DATOS`
  con su motivo. En texto libre clínico solo se borran menciones (`borrar_menciones`).
  `test_la_aplicacion_solo_borra_estado_tecnico` falla si una tabla de negocio recupera
  `DELETE`. Una familia dada de baja no tiene contrato vigente, por los dos lados (migración `0027`):
  `tr_familias_baja_sin_contrato_vigente` rechaza marcar la baja con uno vigente, así que la
  baja completa cancela antes el contrato (`afiliaciones.ciclo.dar_de_baja`), y
  `tr_contratos_vigente_de_familia_activa` rechaza crear o reactivar uno para una familia que
  ya se fue.
- **Lo que ve y escribe cada perfil lo decide la base (RLS).** Toda tabla tiene RLS y cuatro
  políticas para `timu_app` (`p_<tabla>_<operación>`), generadas de la matriz de
  `app/core/permisos_db.py`: `PERMISOS` (perfil → tabla → `S`, `I`, `U`, `D` y `L`, que es
  bloquear con `FOR UPDATE` sin poder editar), `CONDICIONES` (las filas de `familia`,
  `aliada` y `publico`, y las sesiones propias del equipo) y `CATALOGOS`. Sin contexto, la base no
  devuelve nada. `sistema` lo tiene todo; los webhooks pasan a `sistema` tras validar la
  firma, y las rutas públicas con token de un solo uso (registro en línea), tras validarlo.
  Toda escritura lleva lectura, porque `INSERT … RETURNING` exige pasar la política de
  `SELECT`. Una ruta nueva, o una que pase a tocar otra tabla, exige actualizar la matriz y
  escribir la migración que regenera sus políticas; si no, la prueba de esa ruta falla
  porque la base niega el acceso. Esa migración no importa la matriz, la congela: se genera
  comparando `politicas(TABLAS)` con las expresiones de la última migración de RLS, y lleva
  la anterior y la nueva de cada política cambiada para que el `downgrade` restaure la
  anterior (patrón de la `0026`). Para derivar lo que toca una ruta:
  `TIMU_REGISTRO_ACCESOS=<fichero> pytest` anota cada perfil, ruta, operación y tabla, con
  una sesión propia por petición para que ninguna lectura se sirva de memoria. En ese modo
  `test_pedir_asesor_con_contexto_y_el_bot_se_calla` falla siempre (lo que escribe el webhook
  queda en otra sesión) y pasa en la suite normal: no es un fallo. Ojo con los
  efectos: cambiar el estado de un servicio ejecuta reglas configurables que crean tareas y
  mensajes, y quien cambia ese estado tiene esos permisos aunque hoy ninguna regla los use.
  `test_toda_tabla_tiene_rls_y_las_politicas_de_la_matriz` compara cada política con lo que
  genera hoy la matriz, a través de su comentario. `restringir()` sigue en Python como
  segunda capa y para responder 404, y lo que filtra columnas (la vista por perfil de la
  historia clínica) también sigue en Python: RLS filtra filas.
- **`publico` solo ve las filas de quien declara la petición.** Es el perfil de toda petición
  sin sesión y del comienzo de cada petición autenticada, hasta que `get_current_user`
  reconoce al usuario. Sin llaves no ve nada. El código fija las llaves con
  `acotar_publico(db, …)` (`LLAVES_PUBLICAS` en `app/core/database.py`), donde ya conoce el
  valor y con el mismo valor que usa la consulta: el email o el teléfono de ingreso, el hash
  del token, el documento del formulario, el token de la encuesta, el código del carnet. Hay
  dos llaves de cuenta distintas: `usuario` (identificada, basta para enviarle un enlace) y
  `autenticado` (probó una credencial). Solo `autenticado` abre una sesión o cambia la
  contraseña, y un token de renovación reutilizado solo da `revocar`. Una ruta pública nueva,
  o una que pase a leer otra fila, declara sus llaves y amplía la condición de `publico` en la
  matriz (`CONDICIONES` admite una expresión por operación). Ojo: una lectura que la base
  filtra no da error, devuelve menos filas, y el código que trata ese dato como opcional sigue
  adelante con un resultado peor (así se detectó la encuesta que nombraba al profesional como
  «sin asignar»). Para buscarlos: contar cada `SELECT` de `publico` también como `sistema` en
  la misma transacción (`SAVEPOINT`, `set_config('app.rol', 'sistema', true)`, `ROLLBACK TO`)
  y anotar las sentencias en que `publico` ve menos filas. Lo que necesite ver lo de todos,
  como el reparto por carga de los comerciales, va en una función `SECURITY DEFINER` que solo
  devuelve el resultado (`comercial_con_menos_carga()`). Límite: el contexto se fija con
  `set_config`, así que esto protege de errores de la aplicación, no de quien ejecute SQL
  arbitrario con su conexión.
- **Lo que crece con el negocio se consulta por índice.** Toda clave foránea lleva
  `index=True` (`test_toda_llave_foranea_tiene_indice`).
  `test_los_caminos_calientes_no_recorren_tablas_enteras` recorre los listados del panel y
  todas las tareas del beat, captura cada sentencia y la analiza con
  `EXPLAIN (GENERIC_PLAN)` y `enable_seqscan = off`. Si aun así una tabla que crece con el
  negocio se recorre entera, ningún índice sirve esa consulta y la prueba falla. Un listado
  o una tarea nueva se añade a `_LISTADOS`, o entra sola si es del beat. Las tablas acotadas
  por naturaleza van en `_ACOTADAS`, y los procesos por lotes que leen casi toda la tabla a
  propósito en `_RECORRIDOS_A_PROPOSITO`, siempre con su motivo. Ordenar por una expresión
  (`CASE`) impide usar un índice: la bandeja de tareas ordena por el enum `prioridad`, cuyo
  orden de declaración es el de urgencia.
- **Límites y pool.** `timu_app` tiene `statement_timeout` de 30 s, `lock_timeout` de 10 s e
  `idle_in_transaction_session_timeout` de 60 s (migración `0024`). En compose, API, worker y
  beat llegan a la base por PgBouncer en modo transacción (`APP_DB_HOST`); el contexto de RLS
  es local a la transacción, así que no se cruza entre clientes, y asyncpg necesita
  `MAX_PREPARED_STATEMENTS`. Las migraciones e `inicializar` van directo. `db` precarga
  `pg_stat_statements` y registra en el log las consultas de más de 500 ms. Los límites se
  comprueban con una conexión de `timu_app` o en `pg_db_role_setting`: tras
  `SET ROLE timu_app`, `SHOW statement_timeout` da 0, porque los ajustes del rol solo se
  cargan al iniciar sesión.
- **Toda clave primaria es UUIDv7** (RFC 9562), con tres capas: `UUIDMixin` lo genera en
  Python (`nuevo_id()`, de `uuid-utils`, porque Python 3.12 no trae `uuid7`), la columna
  tiene `DEFAULT uuidv7()` para quien inserte por SQL, y `ck_<tabla>_id_uuidv7` rechaza
  cualquier otra versión. El `CHECK` lo añade un evento de mapper a nivel de tabla: a nivel
  de columna, el autogenerate de Alembic lo descartaría. Todo modelo hereda `UUIDMixin`, y
  `test_toda_tabla_tiene_id_uuidv7_generado_y_exigido_por_la_base` falla si una tabla no
  cumple. `nuevo_id()` solo se llama cuando el ID hace falta antes del `flush`. Lo que deba
  ser imposible de adivinar (referencias de pago, claves de almacenamiento, tokens) sigue
  usando `uuid4` o `secrets`: un v7 revela la fecha de creación.

## Migraciones

```bash
# generar, tras cambiar o anadir un modelo
docker compose exec api alembic revision --autogenerate -m "descripcion"
# aplicar
docker compose exec api alembic upgrade head
# deshacer la ultima
docker compose exec api alembic downgrade -1
```

Dónde se aplica `alembic upgrade head`:

| Entorno | Cuándo |
| --- | --- |
| Desarrollo | automático: el servicio `inicializar` en cada `docker compose up`; `docker compose run --rm inicializar` si llega una migración con el stack ya arriba |
| Pruebas | automático: `tests/conftest.py` levanta el esquema con las migraciones |
| Producción | como paso del despliegue, **antes** de arrancar la API, con el servicio anterior aún sirviendo |

Alembic se conecta siempre como dueño del esquema (`DATABASE_URL_PROPIETARIO`). Sin Docker
se corre desde `backend/` con el `.env` apuntando a la base; para lanzarlo contra otra
distinta, `DATABASE_URL_PROPIETARIO_OVERRIDE` la sustituye sin tocar el `.env`.

Una migración que borra o renombra columnas necesita dos despliegues si no se quiere
cortar el servicio: primero el código que tolera las dos formas, después la migración
destructiva. La primera migración no tiene ese problema porque parte de una base vacía.

- Una migración que redefine una función SQL (`anonimizar_familia`) copia la versión anterior
  de la migración previa con `runpy.run_path(...)["_ANONIMIZAR"]`: el `downgrade` queda exacto.
- Columna `NOT NULL` nueva en una tabla con filas: `server_default` para rellenarlas y
  `alter_column(..., server_default=None)` después; el valor por defecto lo declara el modelo.
- Lo que corre dentro de una función plpgsql no lo ve la guarda de caminos calientes (analiza
  `SELECT f()`): dentro, filtra `auditoria` por `entidad` para usar `ix_auditoria_entidad`.

## Pruebas

Las del backend corren **contra PostgreSQL**, no contra SQLite: el esquema usa JSONB,
UUID nativo y `FOR UPDATE SKIP LOCKED`, y ninguna de las tres existe en SQLite; una
suite verde sobre SQLite no diría nada sobre producción. `docker compose up -d db-test`
levanta una base efímera en tmpfs en el puerto 5433, y `tests/conftest.py` aborta con
instrucciones si no la encuentra.

Las pruebas se conectan como `timu_app`, igual que la aplicación: el esquema lo monta el
dueño (`TEST_DATABASE_URL`) y todo lo demás corre con el rol sin privilegios, para que una
restricción o una política de la base que falle se vea en la suite. El fixture `db` actúa
como `SISTEMA`; cada petición de `client` empieza como `"publico"`, pasa al usuario que se
autentique y al terminar vuelve a `SISTEMA`.

Cada prueba corre dentro de una transacción que se revierte al terminar, así que no se
ven entre sí y no hay que limpiar tablas. Los marcadores `unit` e `integration` los pone
`conftest.py` solo: la prueba que usa el fixture `db` es de integración y el resto,
unitaria. `pytest -m unit` y `pytest -m integration` suman la suite entera. Una prueba
marcada `unit` que usa la base, o con las dos marcas, es un error de colección
(`--strict-markers` rechaza además los inventados). Ojo: `-m unit` también necesita
`db-test`, porque el fixture `esquema` aplica las migraciones al arrancar la sesión.

Trampas conocidas:

- **Nunca dos `pytest` a la vez contra `db-test`**: el fixture `esquema` borra y recrea el esquema al arrancar y rompe la otra ejecución.
- Dentro de una prueba todo comparte transacción y `created_at`: no se compara orden por fecha de creación; se comparan conjuntos.
- Clientes de terceros: se sustituye `httpx.Client` por uno con `httpx.MockTransport` (fixture `red` en `tests/test_integraciones.py`); tareas de Celery con la sesión de la prueba: fixture `en_worker` en `tests/conftest.py`.
- Tras `await db.commit()` los objetos ORM caducan: leer un atributo en una prueba async da `MissingGreenlet`. Guarda los ids antes del `commit`.
- asyncpg no acepta dos sentencias en un mismo `text()`: una `db.execute` por sentencia.
