# CLAUDE.md — backend

Reglas del backend (FastAPI, SQLAlchemy, Celery), una línea cada una. Lo transversal —comandos,
stack con un solo comando, invariante del CI, commits— está en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
El porqué y el detalle de cada regla: [arquitectura](../docs/backend/arquitectura.md),
[persistencia](../docs/backend/persistencia.md) y [pruebas](../docs/backend/pruebas.md); si una
regla cambia, cambia aquí y allí a la vez. Las rutas son relativas a `backend/`.

## Arquitectura

Un directorio por dominio en `app/modules/<dominio>/`: `models.py` · `schemas.py` · `service.py`
(lógica y consultas) · `router.py` (HTTP). `app/modules/familias/` es la referencia del patrón. Las
capas y la prohibición de ciclos entre dominios están en
[`docs/estandares-calidad.md`](../docs/estandares-calidad.md); las vigila `tests/test_arquitectura.py`,
que además exige los imports de `app` en la cabecera (ninguno dentro de una función; los de terceros
pesados, como `ortools`, sí). Lo HTTP que conoce dominios vive en `app/api/` (`deps.py`, `salud.py`);
los registros que agregan dominios (`app/models.py`, `app/transiciones.py`), en `app/`.

- **`app/models.py` es el registro único de modelos**: lo que no se importa ahí no llega a las migraciones.
- **El esquema se aplica con `alembic upgrade head`**, nunca con `create_all`.
- **Un modelo nuevo llega con su migración**; índices y restricciones con `CONVENCION_NOMBRES`
  (`app/core/database.py`). `tests/test_migraciones.py` compara el resultado con los metadatos.
- **Los servicios son síncronos** (`Session`): el router los llama con `await db.run_sync(...)` y una
  tarea de Celery dentro de `with sesion_worker() as db:` (nunca `asyncio.run()` en una tarea).
- **La transacción la cierra `get_db`**: los servicios hacen `flush()`, nunca `commit()`.
- **Autorización con `requiere`** (`app/api/deps.py`): ningún endpoint queda abierto por omisión; uno
  público declara `Depends(publico)`. Lo vigila `tests/test_permisos.py` (F1-AUT-02).
- **Enums de dominio en `app/core/enums.py`** (`StrEnum`); la columna es `EnumDb(Clase)`.
- **Los estados de servicio pasan por `servicios/state_machine.py`** (`aplicar()`): nadie reimplementa
  el grafo ni asigna `servicio.estado` a mano; `aplicar` valida y publica el evento (6.10).
- **Los listados devuelven `Page[T]`** (`app/schemas/common.py`), con filtros combinables.
- **Los schemas de lectura no revalidan formatos** (`EmailStr`, `DocumentoCO`, `TelefonoCO` son `str`
  al leer); se valida al escribir. Referencia: `FamiliaRead` y `UsuarioRead`.
- **Un tope de Pydantic (`max_length`, `pattern`) va sobre el `str` de un opcional**: sobre
  `str | None` falla con `None` y da 500 (`planes/router.py`, `Texto2000`).
- **Un PATCH con `exclude_unset` recibe también los `null` que se mandan**: un campo obligatorio no
  admite `None` en su schema o el servicio lo ignora; si no, Python da 500 o la base un 409 que dice
  «ya existe» (`editar_plantilla`).
- **Toda consulta pasa por `restringir()`** (`app/core/scope.py`) con un `Alcance`; cada modelo
  visible desde el portal declara `__columna_familia__`. Se falla cerrado.
- **Ningún `tarea.delay()` dentro de una transacción**: se publica con `app.core.outbox.publicar()`,
  el manejador va en `app/workers/tasks/<dominio>.py` con `@al_ocurrir`, y el nombre se declara con
  `declarar_evento` en el dominio que publica. Un evento que agota `MAX_INTENTOS` queda como
  `outbox.abandonado`.
- **Ningún dominio orquesta lo que no es suyo**: `familias` es la ficha; la baja, las altas y bajas de
  mascotas, la anonimización y el formulario público los orquesta `afiliaciones/ciclo.py`; la vida del
  contrato es de `cartera/contratos.py`.
- **Un schema que leen dos routers va en `<dominio>/schemas.py`**, con sus `Literal` (al revés se
  cierra un import circular).
- **Inyecciones entre dominios** (el de abajo no importa al de arriba; el de arriba le conecta al
  importarse, y sin conectar falla):
  - `comunicaciones` no depende de nadie: `app/workers/tasks/comunicaciones.py` le conecta los
    entrantes (`conectar_entrantes`).
  - `tareas` ← `servicios`: `tareas.conectar_servicios` para nombrar cada tarea.
  - `servicios` ← `preventivos`: `servicios.conectar_al_cambiar_estado` (ver
    `docs/flujo-de-la-visita.md`).
  - `cartera` ← `aliadas`: `cartera.conectar_al_cancelar` corta la vigencia de las remisiones por usar.
  - `catalogos` ← `clinica`: `catalogos.conectar_campos_de_la_consulta` (`lo_registra_la_consulta`).
  - `reglas` ← `planes`: `reglas.conectar_planes` da los planes al editor de reglas y a su validación.
- **La traza de mensajes tapa los tokens de un solo uso** (`MensajeRead`); un script que necesite uno
  lo lee de la base con `sesion_worker`.
- **Cada evento de reglas declara lo que da y lo que admite**: su contexto es una dataclass en
  `reglas/contextos.py` (quien evalúa la construye: `reglas.evaluar(db, CarteraAlerta(...))`) y sus
  acciones, en `reglas/acciones.py`; un campo, estado o evento nuevo lleva además su nombre en
  `_CAMPOS`, `_VALORES` o `_NOMBRES_EVENTOS` de `motor.py` (lo exige `test_reglas.py`).
- **Las cadenas que la API devuelve para mostrarse llevan tildes**; los docstrings y comentarios, no.
  Los mensajes de error aún no las llevan (deuda, no norma).
- **Un tercero con efectos (cobrar, enviar) se llama fuera de la transacción del lote**
  (`cartera.pasarela.cobrar_recurrentes`); los procesos diarios aíslan cada registro en un savepoint.
- **Los campos JSON usan `JSONTipo`**, nunca el `JSON` de SQLAlchemy.
- **La sesión son dos cookies httpOnly** (acceso corto con `sid`; renovación opaca que rota y solo
  viaja a `/api/v1/auth`); reusar una rotada cierra todas las sesiones del usuario.
- **Tokens con PyJWT y algoritmo explícito**; nunca `python-jose`.
- **OR-Tools solo en `requirements-worker.txt`** y solo desde el worker (`app/integrations/routing.py`).
- **Registros con `structlog`** y `X-Request-ID`; Sentry solo con `SENTRY_DSN`.
- **Adjuntos por `app/integrations/storage.py`** (S3), siempre con `url_firmada()`.
- **Los PDF usan `app/core/marca_pdf.py`** (`PdfMarca` y sus piezas) y dicen las cosas en palabras.
- **Un dato del equipo que la familia ve en el portal se guarda como constancia en la fila**
  (`aplicado_por_nombre`): RLS no le deja leer `usuarios`.
- **Webhooks públicos validados por token (Meta) o firma HMAC (pasarela)**, nunca por JWT: responden
  rápido y encolan. `@pasarela.al_aprobar(PREFIJO)` se registra al importar su módulo, que tiene que
  importarse en la API y en el worker.
- **Celery**: `worker` ejecuta y `beat` programa (`celery_app.py`, zona `America/Bogota`); las tareas
  llevan nombre explícito (`cartera.revisar_mora`).
- **Configuración** con `Settings` (`pydantic-settings`): `DATABASE_URL` y `DATABASE_URL_PROPIETARIO`
  salen de `POSTGRES_*` y `APP_DB_PASSWORD`; los `*_OVERRIDE` las sustituyen.
- **Un valor de `.env.example` que solo vale en local** (token, número ficticio) se rechaza desplegado
  en `Settings._validar_ambiente`, con su caso en `test_produccion_con_valores_inseguros_no_arranca`.

## Persistencia: la base garantiza, Python explica

Toda regla que PostgreSQL puede hacer cumplir se hace cumplir en PostgreSQL; Python valida antes
para dar el mensaje. Una regla nueva entra aquí en una línea y con su detalle en
[persistencia](../docs/backend/persistencia.md).

- **Dos roles**: `timu` (dueño, solo Alembic e `inicializar`) y `timu_app` (API, workers, scripts y
  pruebas). API, worker y suite se niegan a arrancar con superusuario o `BYPASSRLS`.
- **Cada transacción lleva su contexto** (`ContextoDb` en `session.info`, fijado con `set_config`
  local): `get_db` empieza en `publico`, `get_current_user` pasa al usuario; `sesion_worker` y los
  scripts usan `SISTEMA`; a mitad de transacción, `fijar_contexto`.
- **Todo conjunto cerrado es un enum de PostgreSQL** (`EnumDb`); cambiar sus valores exige migración a
  mano. Guardas: `test_cada_enum_del_modelo_coincide_con_el_de_la_base` y
  `test_ningun_conjunto_cerrado_queda_como_texto_libre` (`_ABIERTAS`). Ordenar o comparar un enum como
  texto lleva `cast(col, String)`; un `CHECK` con un valor recién añadido compara `estado::text`.
- **Toda referencia a un catálogo es una clave foránea** (`onupdate="CASCADE"`); las ciudades por su
  nombre canónico con tildes («Bogotá», `catalogos.ciudad_valida`). Guarda:
  `test_toda_referencia_a_un_catalogo_tiene_llave_foranea` (`_REFERENCIAS_SIN_LLAVE`).
- **Las invariantes de fila son `__checks__` y las de «solo uno», `__unicos__`** en el modelo; su
  migración se escribe a mano, comprobando antes los datos. Guarda:
  `test_cada_check_y_cada_unico_del_modelo_estan_en_la_base`. Teléfonos en E.164 (`normalizar_telefono`).
- **Los cambios de estado los valida la base** (`app/transiciones.py`, tabla `transiciones_estado`,
  trigger `validar_transicion`): una transición nueva lleva su migración. Guarda:
  `test_los_grafos_de_la_base_son_los_del_codigo`.
- **La auditoría la escribe la base** (`Auditable`, trigger `tr_<tabla>_auditoria`); lo de
  `INMUTABLES` no cambia. Guarda: `test_cada_tabla_auditable_e_inmutable_tiene_su_trigger`.
- **Nada de negocio se borra**: `DELETE` solo en `BORRABLES`; una baja es un estado o una marca. El
  único borrado es `anonimizar_familia()` (Ley 1581). Guardas: `test_anonimizar_no_deja_datos_personales`
  (`CONSERVAN_DATOS`) y `test_la_aplicacion_solo_borra_estado_tecnico`.
- **Lo que ve y escribe cada perfil lo decide la base (RLS)**, generado de `app/core/permisos_db.py`
  (`PERMISOS`, `CONDICIONES`, `CATALOGOS`). Una ruta nueva, o que toque otra tabla, actualiza la matriz
  y escribe la migración que congela sus políticas (patrón de la `0026`). Para derivar lo que toca una
  ruta: `TIMU_REGISTRO_ACCESOS=<fichero> pytest` (en ese modo
  `test_pedir_asesor_con_contexto_y_el_bot_se_calla` falla siempre y no es un fallo). Guarda:
  `test_toda_tabla_tiene_rls_y_las_politicas_de_la_matriz`.
- **Una lectura que la base filtra no da error: devuelve menos filas.** Vale también para un catálogo:
  un perfil acotado (`aliada`) sin la tabla en `PERMISOS` la lee vacía (pasó con `especies`).
- **`publico` solo ve las filas de quien declara la petición** (`acotar_publico`, `LLAVES_PUBLICAS`;
  `usuario` identifica, `autenticado` abre sesión). Lo que necesite ver lo de todos va en una función
  `SECURITY DEFINER` (`comercial_con_menos_carga()`).
- **Lo que crece se consulta por índice**: toda clave foránea con `index=True`
  (`test_toda_llave_foranea_tiene_indice`); un listado o una tarea nueva entra en
  `test_los_caminos_calientes_no_recorren_tablas_enteras` (`_LISTADOS`; los de la aliada, en
  `_LISTADOS_DE_ALIADA`; las tablas acotadas en `_ACOTADAS` y los lotes a propósito en
  `_RECORRIDOS_A_PROPOSITO`). Sin índice en `created_at`, se ordena por `id` (UUIDv7).
- **Límites y pool**: `statement_timeout` 30 s, `lock_timeout` 10 s e
  `idle_in_transaction_session_timeout` 60 s para `timu_app` (`0024`); API, worker y beat por PgBouncer
  en modo transacción; migraciones directo.
- **Toda clave primaria es UUIDv7** (`UUIDMixin`, `nuevo_id()`, `DEFAULT uuidv7()` y
  `ck_<tabla>_id_uuidv7`). Guarda: `test_toda_tabla_tiene_id_uuidv7_generado_y_exigido_por_la_base`. Lo
  imposible de adivinar (tokens, referencias de pago) usa `uuid4` o `secrets`.

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
| Staging (Railway) | automático: el *pre-deploy* de `api` corre `inicializar` en cada despliegue desde `main` ([despliegue de staging](../docs/despliegue-staging.md)); nunca a mano |
| Producción | como paso del despliegue, **antes** de arrancar la API, con el servicio anterior aún sirviendo |

Alembic se conecta siempre como dueño del esquema (`DATABASE_URL_PROPIETARIO`). Sin Docker
se corre desde `backend/` con el `.env` apuntando a la base; para lanzarlo contra otra
distinta, `DATABASE_URL_PROPIETARIO_OVERRIDE` la sustituye sin tocar el `.env`.

Una migración que borra o renombra columnas necesita dos despliegues si no se quiere
cortar el servicio: primero el código que tolera las dos formas, después la migración
destructiva. La primera migración no tiene ese problema porque parte de una base vacía.

- Una migración de datos se prueba en `tests/test_migraciones.py` con `_base_en("<revisión anterior>")`:
  se llena la base, `upgrade`, se comprueba, `downgrade` y se vuelve a comprobar (`test_0048_…`).
- Una migración que redefine una función SQL (`anonimizar_familia`) copia la versión anterior
  de la migración previa con `runpy.run_path(...)["_ANONIMIZAR"]`: el `downgrade` queda exacto.
- Columna `NOT NULL` nueva en una tabla con filas: `server_default` para rellenarlas y
  `alter_column(..., server_default=None)` después; el valor por defecto lo declara el modelo.
- Lo que corre dentro de una función plpgsql no lo ve la guarda de caminos calientes (analiza
  `SELECT f()`): dentro, filtra `auditoria` por `entidad` para usar `ix_auditoria_entidad`.
- Una política de `SELECT` no lleva `WITH CHECK`: copia el `_alterar` de la `0049`, que admite `None`.
- Un `CHECK` se crea con `op.execute("ALTER TABLE … ADD CONSTRAINT ck_<tabla>_<nombre> …")`,
  no con `op.create_check_constraint`, que le añade otra vez el prefijo de la convención.

## Pruebas

Contra **PostgreSQL** (`docker compose up -d db-test`, puerto 5433), nunca SQLite, y con el rol
`timu_app`. Cada prueba corre en una transacción que se revierte; las marcas `unit` e `integration` las
pone `conftest.py` (`-m unit` también necesita `db-test`). Fixtures: `db` (actúa como `SISTEMA`),
`client` (empieza en `publico`), `tareas` (drena el outbox con sus manejadores reales),
`almacenamiento` (S3 en memoria), `en_worker` y `login(client, email)`. Las trampas conocidas, en
[pruebas](../docs/backend/pruebas.md); las que más se tropiezan:

- **Nunca dos `pytest` a la vez contra `db-test`**, tampoco el de un subagente (un revisor): el fixture
  `esquema` recrea el esquema al arrancar y la otra suite deja de valer.
- Dentro de una prueba todo comparte `created_at`: se comparan conjuntos, no órdenes por fecha.
- Tras `await db.commit()` los objetos ORM caducan (`MissingGreenlet`): guarda los ids antes.
- Una fila con estado avanzado se inserta ya en él: el trigger de transiciones solo valida `UPDATE`.
- `mypy` del CI cubre solo `app/`: los scripts de datos se comprueban a mano
  (`mypy scripts/datos_demo.py scripts/operacion_demo.py`).
- `POST /auth/restablecer` abre la sesión de quien activa: un script lo llama sin cookies.
- Los scripts de datos no escriben por debajo de la API, salvo las dos excepciones con su motivo en el
  código (el token de activación de `datos_demo` y las fechas al pasado de `operacion_demo`).
