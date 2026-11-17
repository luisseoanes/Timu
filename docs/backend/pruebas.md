# Backend: pruebas

Cómo se prueba el backend contra PostgreSQL y las trampas conocidas de la suite. Las reglas, en una línea cada una, están en [`backend/CLAUDE.md`](../../backend/CLAUDE.md),
que es lo que lee cada sesión de Claude Code; aquí está el detalle completo, con el porqué de cada
una. Si una regla cambia, cambia en los dos sitios a la vez. Las rutas de código son relativas a
`backend/`.

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
- Un servicio (o cualquier fila con estado) en un estado avanzado se inserta ya en él: el trigger de transiciones solo valida `UPDATE` (ver `_atendido` en `tests/test_encuestas.py`).
- `mypy` del CI cubre solo `app/`. Los scripts de datos pasan sin errores y se comprueban a mano al tocarlos: `mypy scripts/datos_demo.py scripts/operacion_demo.py`.
- `dict(db.execute(...).tuples())` falla (TupleResult tiene `keys()`): usa `.tuples().all()`.
- asyncpg quiere un parámetro `text[]` o `uuid[]` como lista de Python, no como tupla.
- En SQL, `fecha + time '11:30' AT TIME ZONE 'America/Bogota'` aplica la zona a la hora sola: va entre paréntesis, `(fecha + time '11:30') AT TIME ZONE …`.
- Un CHECK de fechas (`ck_contratos_renovacion_posterior`) impide insertar un contrato «del pasado» en una prueba: se mueve el reloj con `monkeypatch` sobre el `hoy` del servicio.
- Los diagnósticos de Pyright del editor («Import could not be resolved») son ruido del entorno: mandan `ruff` y `mypy` con `backend/.venv`.
- **`POST /auth/restablecer` abre la sesión** de quien activa o restablece (desde `R3-PUB-01`): un script que lo llame con el cliente del administrador se queda con las cookies de la familia, y sus peticiones siguientes dan 404 o 403. `datos_demo` lo hace con una petición aparte, sin cookies.
- **Los scripts de datos no escriben por debajo de la API**, salvo dos excepciones con su motivo en el código: `datos_demo` lee de la base el token de activación (la API lo tapa), y `operacion_demo` corre al pasado las fechas de lo que creó, con la conexión del dueño del esquema (la única que puede fechar una consulta firmada). Lo que la API no permite hacer (llevar un interesado a «afiliado» sin pasarela) no se fuerza por SQL.
- **`operacion_demo` drena el outbox y llama a tareas del beat en el propio proceso** (`outbox.drenar`, `cartera.generar_cuotas`, `revisar_mora`, `encuestas.enviar_pendientes`, `campanas.lanzar_programadas` y `despachar`): por eso importa al arrancar los mismos módulos de tareas que el worker (`celery_app.conf.include`); sin ellos, un evento sin declarar hace fallar el drenado.
