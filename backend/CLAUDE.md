# CLAUDE.md — backend

Reglas del backend (FastAPI, SQLAlchemy, Celery). Lo transversal —comandos, stack con un
solo comando, invariante del CI, commits— está en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
Las rutas de este fichero son relativas a `backend/`.

## Arquitectura

Un directorio por dominio en `app/modules/<dominio>/`, con hasta cuatro piezas:
`models.py` (SQLAlchemy) · `schemas.py` (Pydantic) · `service.py` (lógica y consultas) ·
`router.py` (HTTP). `app/modules/familias/` es la referencia completa del patrón.

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
- **Autorización con `requiere`** (alias de `require_roles`, en `app/core/deps.py`):
  `dependencies=[Depends(requiere(Rol.ADMIN))]`, o `requiere(*INTERNOS)` para todo el
  equipo. **Ningún endpoint queda abierto por
  omisión** (F1-AUT-02): uno abierto a propósito declara `Depends(publico)`, y
  `tests/test_permisos.py` recorre todas las rutas y falla si alguna no declara ninguna
  de las dos, o si aparece una pública que no está en su lista.
- **Enums de dominio en `app/core/enums.py`**, no en cada módulo. Son `StrEnum` y viajan
  como cadenas en la API.
- **Los estados de servicio pasan por `app/modules/servicios/state_machine.py`.** Rutas,
  portal y comunicaciones llaman a `aplicar()`; ningún módulo reimplementa el grafo de
  transiciones ni asigna `servicio.estado` a mano: `aplicar` valida la transición *y*
  publica el evento que dispara los efectos de 6.10.
- **Los listados devuelven `Page[T]`** de `app/schemas/common.py` (`items`, `total`,
  `limit`, `offset`), con filtros combinables como en `familias.service.listar`.
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
  `celery_app.send_task(...)`: el trabajo pesado va en la tarea, no en el drenado.
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

Celery (`app/workers/`) corre en dos contenedores distintos: `worker` ejecuta y `beat`
programa. El `beat_schedule` está en `celery_app.py` en zona `America/Bogota`; las tareas
llevan nombre explícito (`cartera.revisar_mora`) porque el schedule las referencia por
cadena.

Configuración: `Settings` de `pydantic-settings` con `.env`. `DATABASE_URL` es un campo
computado a partir de las variables `POSTGRES_*`; `DATABASE_URL_OVERRIDE` la sustituye.

Tests: `httpx.AsyncClient` sobre ASGI contra PostgreSQL y `dependency_overrides[get_db]`
(ver `tests/conftest.py`). `pytest.ini` fija `asyncio_mode = auto`, así que las pruebas
async no necesitan decorador. Los servicios se llaman como en los routers, con
`await db.run_sync(...)`. El fixture `tareas` drena el outbox de la transacción de la
prueba con sus manejadores reales y registra lo que se habría encolado en Celery
(`await tareas.de("comunicaciones.enviar_mensaje")`); el fixture `almacenamiento`
sustituye S3 por memoria. `login(client, email)` devuelve la cabecera `Cookie` de esa
sesión, para las pruebas que alternan usuarios.

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

Sin Docker se corre desde `backend/` con el `.env` apuntando a la base; para lanzarlo
contra otra distinta, `DATABASE_URL_OVERRIDE` la sustituye sin tocar el `.env`.

Una migración que borra o renombra columnas necesita dos despliegues si no se quiere
cortar el servicio: primero el código que tolera las dos formas, después la migración
destructiva. La primera migración no tiene ese problema porque parte de una base vacía.

## Pruebas

Las del backend corren **contra PostgreSQL**, no contra SQLite: el esquema usa JSONB,
UUID nativo y `FOR UPDATE SKIP LOCKED`, y ninguna de las tres existe en SQLite; una
suite verde sobre SQLite no diría nada sobre producción. `docker compose up -d db-test`
levanta una base efímera en tmpfs en el puerto 5433, y `tests/conftest.py` aborta con
instrucciones si no la encuentra.

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
- Clientes de terceros: se sustituye `httpx.Client` por uno con `httpx.MockTransport` (fixture `red` en `tests/test_integraciones.py`); tareas de Celery con la sesión de la prueba: fixture `en_worker` en `tests/test_tareas_celery.py`.
