# Inventario de los tres `CLAUDE.md` (R4-CIE-03)

Anexo de la [hoja de ruta del rediseño](../hoja-de-ruta-rediseno.md). `R4-CIE-03` condensa los tres
`CLAUDE.md` sin perder ninguna regla. Aquí está cada unidad que tenían antes (cada viñeta, fila de
tabla, párrafo y comando, numerados por fichero en el orden en que aparecían) y dónde queda. Lo sacó
un script de los ficheros tal como estaban antes del commit que los condensa; el mismo script comprobó que los identificadores de
cada unidad (lo que va entre comillas invertidas) siguen en el `CLAUDE.md` nuevo o en el documento de
`docs/` al que se movió. Las excepciones están anotadas.

| Fichero | Antes | Después | Unidades | Se mueven a `docs/` | Se quitan |
| --- | --- | --- | --- | --- | --- |
| `CLAUDE.md` | 22.3 KB | 20.5 KB | 106 | 0 | 1 |
| `backend/CLAUDE.md` | 16.0 KB | 16.0 KB | 86 | 0 | 0 |
| `frontend/CLAUDE.md` | 14.8 KB | 8.4 KB | 63 | 25 | 0 |

## `CLAUDE.md`

| Id | Línea | Sección | Unidad (comienzo) | Destino |
| --- | --- | --- | --- | --- |
| R001 | 3 | CLAUDE.md | This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. | **Se quita**: la frase de plantilla en inglés; no es una regla. |
| R002 | 7 | Qué es este repositorio | TIMU, plataforma de gestión veterinaria por afiliación. **La única fuente de verdad de lo que hay que construi… | Queda. |
| R003 | 15 | Qué es este repositorio | El código y la documentación citan los dos documentos así: | Queda (comando o texto conservado). |
| R004 | 17 | Qué es este repositorio | - Requisito por número (`6.10`, `6.16`) o sección por número (`Sección 8`, `Sección 14`): el documento de requ… | Queda, sin el segundo ejemplo (`6.16`). |
| R005 | 21 | Qué es este repositorio | - Sección por letra (`sección A`, `Sección C`): los apartados A a E de la sección 15 de la propuesta. | Queda, con «`sección A` a `E`» en lugar de los dos ejemplos. |
| R006 | 24 | Qué es este repositorio | Al implementar algo, parte del requisito del documento (cita su número en el código y en el commit) y no de un… | Queda. |
| R007 | 40 | Comandos | # Todo el stack (api, worker, beat, db, pgbouncer, redis, almacenamiento S3, web) en un solo comando. | Queda: los cinco comentarios del arranque, en cuatro líneas. |
| R008 | 41 | Comandos | # El servicio `inicializar` migra, carga catálogos, crea admin@timu.co / cambiar123 y el | Queda (ver R007). |
| R009 | 42 | Comandos | # bucket antes de que arranquen api, worker y beat. No hace falta copiar ningún .env: | Queda (ver R007). |
| R010 | 43 | Comandos | # backend/.env.example es la base y backend/.env (si existe) la sobrescribe. | Queda (ver R007). |
| R011 | 44 | Comandos | # Puertos del host ocupados por otro proyecto → .env de la raíz (ver .env.example). | Queda (ver R007). |
| R012 | 45 | Comandos | docker compose up --build | Queda (comando o texto conservado). |
| R013 | 46 | Comandos | docker compose exec api python -m scripts.datos_demo # usuarios, familias, ruta… de prueba (solo local; solo c… | Queda (comando o texto conservado). |
| R014 | 47 | Comandos | docker compose exec api python -m scripts.operacion_demo # después: ocho semanas de operación (~5 min; si ya s… | Queda (comando o texto conservado). |
| R015 | 49 | Comandos | docker compose run --rm inicializar # tras traer una migración nueva, sin reiniciar el stack | Queda (comando o texto conservado). |
| R016 | 50 | Comandos | docker compose up -d api # tras cambiar backend/.env.example: el entorno se lee al crear el contenedor; --relo… | Queda (comando o texto conservado). |
| R017 | 52 | Comandos | docker compose up -d --build -V # tras traer dependencias nuevas: el código va montado, las librerías van en l… | Queda. |
| R018 | 58 | Comandos | # Backend sin Docker | Queda (comando o texto conservado). |
| R019 | 59 | Comandos | cd backend && pip install -r requirements-dev.txt | Queda (comando o texto conservado). |
| R020 | 60 | Comandos | uvicorn app.main:app --reload | Queda (comando o texto conservado). |
| R021 | 62 | Comandos | docker compose up -d db-test # PostgreSQL de pruebas (puerto 5433, perfil `test`: el up general no la levanta)… | Queda. |
| R022 | 63 | Comandos | pytest # suite completa, con cobertura y umbral del 91% | Queda (comando o texto conservado). |
| R023 | 64 | Comandos | pytest -m unit # sólo lo que no toca la base de datos | Queda (comando o texto conservado). |
| R024 | 65 | Comandos | pytest tests/test_alcance.py::test_una_familia_solo_se_ve_a_si_misma # una sola prueba | Queda (comando o texto conservado). |
| R025 | 66 | Comandos | ruff format . && ruff check . && mypy app | Queda (comando o texto conservado). |
| R026 | 67 | Comandos | python scripts/generar_tipos_frontend.py # regenera frontend/src/types/api.ts desde el OpenAPI; no se edita a … | Queda (comando o texto conservado). |
| R027 | 70 | Comandos | # Frontend | Queda (comando o texto conservado). |
| R028 | 71 | Comandos | cd frontend && npm install | Queda (comando o texto conservado). |
| R029 | 72 | Comandos | npm run dev # 5173, con proxy /api → localhost:8000 | Queda (comando o texto conservado). |
| R030 | 73 | Comandos | npm run verificar # lint + typecheck + cobertura + build (lo mismo que CI) | Queda (comando o texto conservado). |
| R031 | 74 | Comandos | npm run test:watch # pruebas de componentes en vigilancia | Queda (comando o texto conservado). |
| R032 | 75 | Comandos | npm run test:e2e # Playwright con la API interceptada (requiere: npx playwright install chromium) | Queda (comando o texto conservado). |
| R033 | 76 | Comandos | npm run test:e2e:stack # recorridos contra el stack real: docker compose up + datos_demo antes | Queda (comando o texto conservado). |
| R034 | 78 | Comandos | # CI: log de un job (`gh run view --log-failed` a veces sale vacío) | Queda. |
| R035 | 79 | Comandos | gh api --allow-escape-sequences repos/{owner}/{repo}/actions/jobs/<id>/logs \| sed 's/\x1b\[[0-9;]*m//g' | Queda (comando o texto conservado). |
| R036 | 80 | Comandos | gh run watch <id> --exit-status --interval 60 && gh run view <id> --json jobs --jq '.jobs[] \| "\(.name): \(.c… | Queda (comando o texto conservado). |
| R037 | 81 | Comandos | # `gh run watch` puede salir con 1 a mitad del run: confírmalo con `gh run view <id> --json status,conclusion` | Queda. |
| R038 | 84 | Comandos | - `npm run verificar 2>&1 \| tail` o `pytest \| tail` devuelven el código de `tail`, no el de la prueba: guard… | Queda. |
| R039 | 86 | Comandos | - `docker compose down -v` no baja `db-test` (va en el perfil `test`): sigue arriba con su base efímera. | Queda. |
| R040 | 90 | Prueba de carga | Mide el volumen proyectado a 12 meses (Sección 14) y mete datos sintéticos, así que se corre en un proyecto ap… | Queda, como viñeta de Comandos (antes, apartado propio). |
| R041 | 96 | Entorno de desarrollo: un solo | **Desde un clon limpio, `docker compose up --build` deja el stack completo funcionando, sin pasos manuales ni … | Queda. |
| R042 | 101 | Entorno de desarrollo: un solo | \| Si el cambio… \| …también tiene que \| | Queda (comando o texto conservado). |
| R043 | 103 | Entorno de desarrollo: un solo | \| añade una variable de entorno \| ir en `backend/.env.example` con un valor que funcione en local (o vacía s… | Queda. |
| R044 | 104 | Entorno de desarrollo: un solo | \| añade una dependencia \| ir con versión fija en `requirements.txt` (API) o `requirements-worker.txt` (solo … | Queda. |
| R045 | 105 | Entorno de desarrollo: un solo | \| necesita un paso de preparación (datos base, un bucket, un recurso externo) \| ir en `backend/scripts/inici… | Queda. |
| R046 | 106 | Entorno de desarrollo: un solo | \| añade una migración \| nada más: `inicializar` aplica `upgrade head` en cada arranque. \| | Queda. |
| R047 | 107 | Entorno de desarrollo: un solo | \| añade un servicio \| ir en el compose con `healthcheck` si otros dependen de él, `depends_on` con condición… | Queda. |
| R048 | 108 | Entorno de desarrollo: un solo | \| toca un Dockerfile, el contexto de build o la estructura de directorios que montan los volúmenes \| comprob… | Queda. |
| R049 | 110 | Entorno de desarrollo: un solo | Cómo se verifica cuando el cambio toca cualquiera de esas filas. Se usa un proyecto aparte para no borrar los … | Queda, en una frase. |
| R050 | 115 | Entorno de desarrollo: un solo | docker compose stop | Queda (comando o texto conservado). |
| R051 | 116 | Entorno de desarrollo: un solo | docker compose -p timu-verificacion up --build -d | Queda (comando o texto conservado). |
| R052 | 117 | Entorno de desarrollo: un solo | docker compose -p timu-verificacion ps -a # inicializar «Exited (0)», el resto en marcha | Queda (comando o texto conservado). |
| R053 | 118 | Entorno de desarrollo: un solo | curl -fsS "$(docker compose -p timu-verificacion port api 8000)/health" # db, redis y workers en «ok» | Queda (comando o texto conservado). |
| R054 | 119 | Entorno de desarrollo: un solo | # recién levantado responde 503 unos segundos, hasta que los workers se registran: reintenta | Queda (comando o texto conservado). |
| R055 | 120 | Entorno de desarrollo: un solo | docker compose -p timu-verificacion down -v --rmi local | Queda (comando o texto conservado). |
| R056 | 121 | Entorno de desarrollo: un solo | docker compose up -d | Queda (comando o texto conservado). |
| R057 | 124 | Entorno de desarrollo: un solo | Si no se ha hecho esta comprobación, se dice explícitamente al entregar el cambio. El job **Stack con un solo … | Queda. |
| R058 | 131 | Staging en Railway: cada empuj | Railway (proyecto `timu`, entorno `staging`) despliega `api`, `worker` y `web` desde `main` en cuanto el CI de… | Queda. |
| R059 | 135 | Staging en Railway: cada empuj | - **Las migraciones llegan a staging solas**: el *pre-deploy* de la API corre `inicializar`. Nunca se aplican … | Queda. |
| R060 | 138 | Staging en Railway: cada empuj | - **Una variable que `Settings` exige desplegado se pone en Railway antes de empujar** el cambio que la pide; … | Queda. |
| R061 | 140 | Staging en Railway: cada empuj | - **El panel de staging es el compilado** (`frontend/Dockerfile.despliegue`, Caddy): un cambio que toca su bui… | Queda. |
| R062 | 142 | Staging en Railway: cada empuj | - **Tras empujar, se comprueba también el despliegue** de los servicios que el cambio toca (`railway deploymen… | Queda (el comando va partido en dos líneas). |
| R063 | 150 | Dónde está cada cosa | Este fichero es lo transversal. Las reglas de cada lado viven junto a su código y se cargan al trabajar allí: | Queda, en la cabecera del fichero. |
| R064 | 153 | Dónde está cada cosa | - [`backend/CLAUDE.md`](backend/CLAUDE.md): las reglas del backend en una línea cada una (arquitectura, persis… | Queda, en la cabecera. |
| R065 | 156 | Dónde está cada cosa | - [`frontend/CLAUDE.md`](frontend/CLAUDE.md): arquitectura del panel, sesión en el navegador, estilos y prueba… | Queda, en la cabecera. |
| R066 | 159 | Dónde está cada cosa | Un cambio que cruza los dos lados (un schema nuevo, una regla de sesión) lee los dos. | Queda, en la cabecera. |
| R067 | 163 | Estándares de calidad (Seccion | El documento de requerimientos exige una solución modular que crezca sin reemplazar su base, y escalabilidad, … | Queda. |
| R068 | 170 | Estándares de calidad (Seccion | - **Capas**: `core` y `schemas` no importan ningún dominio, `integrations` solo la base, y un dominio no impor… | Queda. |
| R069 | 174 | Estándares de calidad (Seccion | - **Eventos**: todo nombre que se publica o se escucha se declara con `declarar_evento` en el dominio que lo e… | Queda. |
| R070 | 176 | Estándares de calidad (Seccion | - **Dependencias**: ninguna vulnerabilidad publicada en lo que se despliega; si no hay versión corregida, `--i… | Queda. |
| R071 | 182 | Invariante: el CI ejecuta toda | Ninguna prueba existe sin que el CI la ejecute en cada empuje a `main`, y ningún cambio se da por terminado si… | Queda. |
| R072 | 186 | Invariante: el CI ejecuta toda | \| Guarda \| Qué hace fallar \| | Queda (comando o texto conservado). |
| R073 | 188 | Invariante: el CI ejecuta toda | \| `backend/tests/conftest.py` (`pytest_sessionfinish`) \| Cualquier prueba saltada o `xfail` en el backend. \… | Queda, unida con R074 y R075 en la fila de `conftest.py`. |
| R074 | 189 | Invariante: el CI ejecuta toda | \| `backend/tests/conftest.py` (`pytest_collection_modifyitems`) \| Una prueba `unit` que usa la base, o una c… | Queda (ver R073). |
| R075 | 190 | Invariante: el CI ejecuta toda | \| `backend/tests/conftest.py` (`esquema`) y `backend/tests/test_persistencia.py` \| Que la suite se conecte c… | Queda (ver R073). |
| R076 | 191 | Invariante: el CI ejecuta toda | \| `backend/tests/test_persistencia.py` y `backend/tests/test_migraciones.py` \| Que el modelo y la base dejen… | Queda condensada: remite a las reglas de «Persistencia» de `backend/CLAUDE.md`, que nombran cada prueba, y enumera las cinco que allí no están. |
| R077 | 192 | Invariante: el CI ejecuta toda | \| `backend/tests/test_suite.py` \| Una prueba del backend fuera de `tests/test_*.py`. \| | Queda. |
| R078 | 193 | Invariante: el CI ejecuta toda | \| `backend/tests/test_base_tecnica.py` (`test_cada_ajuste_de_la_configuracion_esta_en_el_env_de_ejemplo`) \| … | Queda. |
| R079 | 194 | Invariante: el CI ejecuta toda | \| `backend/tests/test_arquitectura.py` \| Una capa que importa de otra superior, un dominio que usa el router… | Queda. |
| R080 | 195 | Invariante: el CI ejecuta toda | \| `backend/tests/test_permisos.py` (`test_la_guarda_recorre_todas_las_rutas_de_la_api`) \| Que la guarda de p… | Queda. |
| R081 | 196 | Invariante: el CI ejecuta toda | \| Job **Vulnerabilidades conocidas** de `ci.yml` \| Una dependencia de la API, el worker o el panel con una v… | Queda. |
| R082 | 197 | Invariante: el CI ejecuta toda | \| `frontend/src/test/tokens.test.ts` \| Un color escrito a mano en `frontend/src` fuera de `styles/tokens.css… | Queda. |
| R083 | 198 | Invariante: el CI ejecuta toda | \| `frontend/e2e-stack/responsive.spec.ts` \| Una ruta que, a 375, 768, 900 o 1280 px, desborda en horizontal … | Queda, sin el ejemplo `?plan=` ni la historia de `PENDIENTES` (retirada en `R4-CIE-01`): «Sin lista de excepciones». |
| R084 | 199 | Invariante: el CI ejecuta toda | \| `frontend/e2e-stack/recorridos.spec.ts` (ficha de familia) \| Barras o línea pintadas sobre una ventana abi… | Queda. |
| R085 | 200 | Invariante: el CI ejecuta toda | \| `frontend/src/test/arquitectura.test.ts` y `no-restricted-imports` de ESLint \| Un import a un fichero inte… | Queda. |
| R086 | 201 | Invariante: el CI ejecuta toda | \| `frontend/src/test/suite.test.ts` \| Una prueba del panel fuera de los patrones de Vitest (`src/**/*.{test,… | Queda. |
| R087 | 202 | Invariante: el CI ejecuta toda | \| `frontend/src/test/setup.ts` \| Una petición del panel que ninguna prueba simuló con MSW: la prueba falla e… | Queda (ruta abreviada a `src/test/handlers.ts`). |
| R088 | 203 | Invariante: el CI ejecuta toda | \| `forbidOnly` en `frontend/playwright.config.ts` y `frontend/playwright.stack.config.ts` \| Un `.only` en e2… | Queda (ruta abreviada). |
| R089 | 204 | Invariante: el CI ejecuta toda | \| Umbrales de cobertura \| Que la cobertura baje del mínimo (abajo). \| | Queda (comando o texto conservado). |
| R090 | 205 | Invariante: el CI ejecuta toda | \| Umbrales `count>0` de `infra/carga/recorrido.js` \| Una prueba de carga que no llegó a hacer peticiones: si… | Queda. |
| R091 | 206 | Invariante: el CI ejecuta toda | \| Mínimos de `backend/scripts/operacion_demo.py` (`MINIMOS`) \| Una siembra de la operación por debajo de sus… | Queda. |
| R092 | 208 | Invariante: el CI ejecuta toda | Reglas que mantienen esto vivo: | Queda (comando o texto conservado). |
| R093 | 210 | Invariante: el CI ejecuta toda | - **Los pasos de pruebas del CI corren las suites enteras**: `pytest`, `npm run test:coverage`, `npm run test:… | Queda. |
| R094 | 215 | Invariante: el CI ejecuta toda | - **Hay dos e2e y no se sustituyen**: `e2e/` intercepta la API y prueba el panel aislado, rápido y determinist… | Queda. |
| R095 | 219 | Invariante: el CI ejecuta toda | - Una sola sesión por perfil (`e2e-stack/sesiones.setup.ts`): ingreso y renovación comparten un límite de 10 p… | Queda resumida en la viñeta de las dos e2e; el detalle (usuario por perfil, Sección 12) ya estaba en `docs/frontend/e2e-stack.md`. |
| R096 | 222 | Invariante: el CI ejecuta toda | - Un recorrido busca lo que dejó `datos_demo` por su identidad (el motivo, el nombre), nunca el primero del li… | Queda resumida (ver R095); el detalle, en `docs/frontend/e2e-stack.md`. |
| R097 | 225 | Invariante: el CI ejecuta toda | - El detalle de los límites y los datos: [`docs/frontend/e2e-stack.md`](docs/frontend/e2e-stack.md). | Queda (ver R095). |
| R098 | 226 | Invariante: el CI ejecuta toda | - **Una prueba que no puede pasar se arregla o se borra**, con la razón en el cuerpo del commit. No se salta, … | Queda. |
| R099 | 228 | Invariante: el CI ejecuta toda | - **Un tipo de prueba nuevo llega cableado al CI en el mismo cambio**: un runner, una carpeta fuera de los pat… | Queda. |
| R100 | 232 | Invariante: el CI ejecuta toda | - **Todo cambio de comportamiento llega con sus pruebas**, y toda corrección con la prueba que habría detectad… | Queda (comando o texto conservado). |
| R101 | 234 | Invariante: el CI ejecuta toda | - **Antes de empujar se corre en local lo que el cambio toca**. No hay pull requests, así que el CI llega cuan… | Queda. |
| R102 | 237 | Invariante: el CI ejecuta toda | Umbrales de cobertura: backend **91%** combinando líneas y ramas (`--cov-fail-under` en `pytest.ini`; la cober… | Queda. |
| R103 | 248 | Invariante: el CI ejecuta toda | `.github/workflows/ci.yml` ejecuta formato, análisis estático (con las reglas de seguridad `S` de Ruff), tipos… | Queda. |
| R104 | 255 | Commits y publicación de versi | Todo está en [`CONTRIBUTING.md`](CONTRIBUTING.md): **léelo antes de cada commit**. Fija qué va en cada commit,… | Queda. |
| R105 | 262 | Commits y publicación de versi | Con mucho trabajo sin commit, los commits se construyen en un worktree aparte: cómo, con sus trampas (el enlac… | Queda, unida al párrafo de commits. |
| R106 | 269 | Convenciones de escritura | Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`, `cartera`), clases CS… | Queda. |

## `backend/CLAUDE.md`

| Id | Línea | Sección | Unidad (comienzo) | Destino |
| --- | --- | --- | --- | --- |
| B001 | 3 | CLAUDE.md — backend | Reglas del backend (FastAPI, SQLAlchemy, Celery), una línea cada una. Lo transversal —comandos, stack con un s… | Sin cambios. |
| B002 | 11 | Arquitectura | Un directorio por dominio en `app/modules/<dominio>/`: `models.py` · `schemas.py` · `service.py` (lógica y con… | Sin cambios. |
| B003 | 19 | Arquitectura | - **`app/models.py` es el registro único de modelos**: lo que no se importa ahí no llega a las migraciones. | Sin cambios. |
| B004 | 20 | Arquitectura | - **El esquema se aplica con `alembic upgrade head`**, nunca con `create_all`. | Sin cambios. |
| B005 | 21 | Arquitectura | - **Un modelo nuevo llega con su migración**; índices y restricciones con `CONVENCION_NOMBRES` (`app/core/data… | Sin cambios. |
| B006 | 23 | Arquitectura | - **Los servicios son síncronos** (`Session`): el router los llama con `await db.run_sync(...)` y una tarea de… | Sin cambios. |
| B007 | 25 | Arquitectura | - **La transacción la cierra `get_db`**: los servicios hacen `flush()`, nunca `commit()`. | Sin cambios. |
| B008 | 26 | Arquitectura | - **Autorización con `requiere`** (`app/api/deps.py`): ningún endpoint queda abierto por omisión; uno público … | Sin cambios. |
| B009 | 28 | Arquitectura | - **Enums de dominio en `app/core/enums.py`** (`StrEnum`); la columna es `EnumDb(Clase)`. | Sin cambios. |
| B010 | 29 | Arquitectura | - **Los estados de servicio pasan por `servicios/state_machine.py`** (`aplicar()`): nadie reimplementa el graf… | Sin cambios. |
| B011 | 31 | Arquitectura | - **Los listados devuelven `Page[T]`** (`app/schemas/common.py`), con filtros combinables. | Sin cambios. |
| B012 | 32 | Arquitectura | - **Los schemas de lectura no revalidan formatos** (`EmailStr`, `DocumentoCO`, `TelefonoCO` son `str` al leer)… | Sin cambios. |
| B013 | 34 | Arquitectura | - **Un tope de Pydantic (`max_length`, `pattern`) va sobre el `str` de un opcional**: sobre `str \| None` fall… | Sin cambios. |
| B014 | 36 | Arquitectura | - **Un PATCH con `exclude_unset` recibe también los `null` que se mandan**: un campo obligatorio no admite `No… | Sin cambios. |
| B015 | 39 | Arquitectura | - **Toda consulta pasa por `restringir()`** (`app/core/scope.py`) con un `Alcance`; cada modelo visible desde … | Sin cambios. |
| B016 | 41 | Arquitectura | - **Ningún `tarea.delay()` dentro de una transacción**: se publica con `app.core.outbox.publicar()`, el maneja… | Sin cambios. |
| B017 | 45 | Arquitectura | - **Una plantilla de WhatsApp que envía el código se declara** con `declarar_plantilla(código, título, uso)` (… | Sin cambios (el identificador va partido en dos líneas). |
| B018 | 48 | Arquitectura | - **Ningún dominio orquesta lo que no es suyo**: `familias` es la ficha; la baja, las altas y bajas de mascota… | Sin cambios. |
| B019 | 51 | Arquitectura | - **Un schema que leen dos routers va en `<dominio>/schemas.py`**, con sus `Literal` (al revés se cierra un im… | Sin cambios. |
| B020 | 53 | Arquitectura | - **Inyecciones entre dominios** (el de abajo no importa al de arriba; el de arriba le conecta al importarse, … | Queda: la regla y las seis inyecciones, en una viñeta (detalle en `docs/backend/arquitectura.md`). |
| B021 | 55 | Arquitectura | - `comunicaciones` no depende de nadie: `app/workers/tasks/comunicaciones.py` le conecta los entrantes (`conec… | Queda (ver B020). |
| B022 | 57 | Arquitectura | - `tareas` ← `servicios`: `tareas.conectar_servicios` para nombrar cada tarea. | Queda (ver B020). |
| B023 | 58 | Arquitectura | - `servicios` ← `preventivos`: `servicios.conectar_al_cambiar_estado` (ver `docs/flujo-de-la-visita.md`). | Queda (ver B020). |
| B024 | 60 | Arquitectura | - `cartera` ← `aliadas`: `cartera.conectar_al_cancelar` corta la vigencia de las remisiones por usar. | Queda (ver B020). |
| B025 | 61 | Arquitectura | - `catalogos` ← `clinica`: `catalogos.conectar_campos_de_la_consulta` (`lo_registra_la_consulta`). | Queda (ver B020). |
| B026 | 62 | Arquitectura | - `reglas` ← `planes`: `reglas.conectar_planes` da los planes al editor de reglas y a su validación. | Queda (ver B020). |
| B027 | 63 | Arquitectura | - **La traza de mensajes tapa los tokens de un solo uso** (`MensajeRead`); un script que necesite uno lo lee d… | Sin cambios. |
| B028 | 65 | Arquitectura | - **Cada evento de reglas declara lo que da y lo que admite**: su contexto es una dataclass en `reglas/context… | Sin cambios. |
| B029 | 69 | Arquitectura | - **Las cadenas que la API devuelve para mostrarse llevan tildes**; los docstrings y comentarios, no. Los mens… | Sin cambios. |
| B030 | 71 | Arquitectura | - **Un tercero con efectos (cobrar, enviar) se llama fuera de la transacción del lote** (`cartera.pasarela.cob… | Sin cambios. |
| B031 | 73 | Arquitectura | - **Los campos JSON usan `JSONTipo`**, nunca el `JSON` de SQLAlchemy. | Sin cambios. |
| B032 | 74 | Arquitectura | - **La sesión son dos cookies httpOnly** (acceso corto con `sid`; renovación opaca que rota y solo viaja a `/a… | Sin cambios. |
| B033 | 76 | Arquitectura | - **Tokens con PyJWT y algoritmo explícito**; nunca `python-jose`. | Sin cambios. |
| B034 | 77 | Arquitectura | - **OR-Tools solo en `requirements-worker.txt`** y solo desde el worker (`app/integrations/routing.py`). | Sin cambios. |
| B035 | 78 | Arquitectura | - **Registros con `structlog`** y `X-Request-ID`; Sentry solo con `SENTRY_DSN`. | Sin cambios. |
| B036 | 79 | Arquitectura | - **Adjuntos por `app/integrations/storage.py`** (S3), siempre con `url_firmada()`. | Sin cambios. |
| B037 | 80 | Arquitectura | - **Los PDF usan `app/core/marca_pdf.py`** (`PdfMarca` y sus piezas) y dicen las cosas en palabras. | Sin cambios. |
| B038 | 81 | Arquitectura | - **Un dato del equipo que la familia ve en el portal se guarda como constancia en la fila** (`aplicado_por_no… | Sin cambios. |
| B039 | 83 | Arquitectura | - **Webhooks públicos validados por token (Meta) o firma HMAC (pasarela)**, nunca por JWT: responden rápido y … | Sin cambios. |
| B040 | 86 | Arquitectura | - **Celery**: `worker` ejecuta y `beat` programa (`celery_app.py`, zona `America/Bogota`); las tareas llevan n… | Sin cambios. |
| B041 | 88 | Arquitectura | - **Configuración** con `Settings` (`pydantic-settings`): `DATABASE_URL` y `DATABASE_URL_PROPIETARIO` salen de… | Sin cambios. |
| B042 | 90 | Arquitectura | - **Un valor de `.env.example` que solo vale en local** (token, número ficticio) se rechaza desplegado en `Set… | Sin cambios. |
| B043 | 95 | Persistencia: la base garantiz | Toda regla que PostgreSQL puede hacer cumplir se hace cumplir en PostgreSQL; Python valida antes para dar el m… | Sin cambios. |
| B044 | 99 | Persistencia: la base garantiz | - **Dos roles**: `timu` (dueño, solo Alembic e `inicializar`) y `timu_app` (API, workers, scripts y pruebas). … | Sin cambios. |
| B045 | 101 | Persistencia: la base garantiz | - **Cada transacción lleva su contexto** (`ContextoDb` en `session.info`, fijado con `set_config` local): `get… | Sin cambios. |
| B046 | 104 | Persistencia: la base garantiz | - **Todo conjunto cerrado es un enum de PostgreSQL** (`EnumDb`); cambiar sus valores exige migración a mano. G… | Sin cambios. |
| B047 | 108 | Persistencia: la base garantiz | - **Toda referencia a un catálogo es una clave foránea** (`onupdate="CASCADE"`); las ciudades por su nombre ca… | Sin cambios. |
| B048 | 111 | Persistencia: la base garantiz | - **Las invariantes de fila son `__checks__` y las de «solo uno», `__unicos__`** en el modelo; su migración se… | Sin cambios. |
| B049 | 114 | Persistencia: la base garantiz | - **Los cambios de estado los valida la base** (`app/transiciones.py`, tabla `transiciones_estado`, trigger `v… | Sin cambios. |
| B050 | 117 | Persistencia: la base garantiz | - **La auditoría la escribe la base** (`Auditable`, trigger `tr_<tabla>_auditoria`); lo de `INMUTABLES` no cam… | Sin cambios. |
| B051 | 119 | Persistencia: la base garantiz | - **Nada de negocio se borra**: `DELETE` solo en `BORRABLES`; una baja es un estado o una marca. El único borr… | Sin cambios. |
| B052 | 122 | Persistencia: la base garantiz | - **Lo que ve y escribe cada perfil lo decide la base (RLS)**, generado de `app/core/permisos_db.py` (`PERMISO… | Sin cambios. |
| B053 | 128 | Persistencia: la base garantiz | - **Una lectura que la base filtra no da error: devuelve menos filas.** Vale también para un catálogo: un perf… | Sin cambios. |
| B054 | 132 | Persistencia: la base garantiz | - **`publico` solo ve las filas de quien declara la petición** (`acotar_publico`, `LLAVES_PUBLICAS`; `usuario`… | Sin cambios. |
| B055 | 135 | Persistencia: la base garantiz | - **Lo que crece se consulta por índice**: toda clave foránea con `index=True` (`test_toda_llave_foranea_tiene… | Sin cambios. |
| B056 | 140 | Persistencia: la base garantiz | - **Límites y pool**: `statement_timeout` 30 s, `lock_timeout` 10 s e `idle_in_transaction_session_timeout` 60… | Sin cambios. |
| B057 | 143 | Persistencia: la base garantiz | - **Toda clave primaria es UUIDv7** (`UUIDMixin`, `nuevo_id()`, `DEFAULT uuidv7()` y `ck_<tabla>_id_uuidv7`). … | Sin cambios. |
| B058 | 150 | Migraciones | # generar, tras cambiar o anadir un modelo | Sin cambios. |
| B059 | 151 | Migraciones | docker compose exec api alembic revision --autogenerate -m "descripcion" | Sin cambios. |
| B060 | 152 | Migraciones | # aplicar | Sin cambios. |
| B061 | 153 | Migraciones | docker compose exec api alembic upgrade head | Sin cambios. |
| B062 | 154 | Migraciones | # deshacer la ultima | Sin cambios. |
| B063 | 155 | Migraciones | docker compose exec api alembic downgrade -1 | Sin cambios. |
| B064 | 158 | Migraciones | Dónde se aplica `alembic upgrade head`: | Sin cambios. |
| B065 | 160 | Migraciones | \| Entorno \| Cuándo \| | Sin cambios. |
| B066 | 162 | Migraciones | \| Desarrollo \| automático: el servicio `inicializar` en cada `docker compose up`; `docker compose run --rm i… | Sin cambios. |
| B067 | 163 | Migraciones | \| Pruebas \| automático: `tests/conftest.py` levanta el esquema con las migraciones \| | Sin cambios. |
| B068 | 164 | Migraciones | \| Staging (Railway) \| automático: el *pre-deploy* de `api` corre `inicializar` en cada despliegue desde `mai… | Sin cambios. |
| B069 | 165 | Migraciones | \| Producción \| como paso del despliegue, **antes** de arrancar la API, con el servicio anterior aún sirviend… | Sin cambios. |
| B070 | 167 | Migraciones | Alembic se conecta siempre como dueño del esquema (`DATABASE_URL_PROPIETARIO`). Sin Docker se corre desde `bac… | Sin cambios. |
| B071 | 171 | Migraciones | Una migración que borra o renombra columnas necesita dos despliegues si no se quiere cortar el servicio: prime… | Sin cambios. |
| B072 | 175 | Migraciones | - Una migración de datos se prueba en `tests/test_migraciones.py` con `_base_en("<revisión anterior>")`: se ll… | Sin cambios. |
| B073 | 177 | Migraciones | - Una migración que redefine una función SQL (`anonimizar_familia`) copia la versión anterior de la migración … | Sin cambios. |
| B074 | 179 | Migraciones | - Columna `NOT NULL` nueva en una tabla con filas: `server_default` para rellenarlas y `alter_column(..., serv… | Sin cambios. |
| B075 | 181 | Migraciones | - Lo que corre dentro de una función plpgsql no lo ve la guarda de caminos calientes (analiza `SELECT f()`): d… | Sin cambios. |
| B076 | 183 | Migraciones | - Una política de `SELECT` no lleva `WITH CHECK`: copia el `_alterar` de la `0049`, que admite `None`. | Sin cambios. |
| B077 | 184 | Migraciones | - Un `CHECK` se crea con `op.execute("ALTER TABLE … ADD CONSTRAINT ck_<tabla>_<nombre> …")`, no con `op.create… | Sin cambios. |
| B078 | 189 | Pruebas | Contra **PostgreSQL** (`docker compose up -d db-test`, puerto 5433), nunca SQLite, y con el rol `timu_app`. Ca… | Sin cambios. |
| B079 | 199 | Pruebas | - **Nunca dos `pytest` a la vez contra `db-test`**, tampoco el de un subagente (un revisor): el fixture `esque… | Sin cambios. |
| B080 | 201 | Pruebas | - Para ver que una prueba de RLS falla sin el arreglo, quita la matriz **y** la migración: la base de pruebas … | Sin cambios. |
| B081 | 203 | Pruebas | - Dentro de una prueba todo comparte `created_at`: se comparan conjuntos, no órdenes por fecha. | Sin cambios. |
| B082 | 204 | Pruebas | - Tras `await db.commit()` los objetos ORM caducan (`MissingGreenlet`): guarda los ids antes. | Sin cambios. |
| B083 | 205 | Pruebas | - Una fila con estado avanzado se inserta ya en él: el trigger de transiciones solo valida `UPDATE`. | Sin cambios. |
| B084 | 206 | Pruebas | - `mypy` del CI cubre solo `app/`: los scripts de datos se comprueban a mano (`mypy scripts/datos_demo.py scri… | Sin cambios. |
| B085 | 208 | Pruebas | - `POST /auth/restablecer` abre la sesión de quien activa: un script lo llama sin cookies. | Sin cambios. |
| B086 | 209 | Pruebas | - Los scripts de datos no escriben por debajo de la API, salvo las dos excepciones con su motivo en el código … | Sin cambios. |

## `frontend/CLAUDE.md`

| Id | Línea | Sección | Unidad (comienzo) | Destino |
| --- | --- | --- | --- | --- |
| F001 | 3 | CLAUDE.md — frontend | Reglas del panel (React 18, Vite, React Query). Lo transversal —comandos, stack con un solo comando, invariant… | Queda, en la cabecera. |
| F002 | 9 | Arquitectura | React 18 + Vite, alias `@/` → `src/`. Un directorio por dominio en `src/features/<dominio>/` con su `api.ts` (… | Queda, en la primera viñeta de Arquitectura. |
| F003 | 16 | Arquitectura | Hay tres espacios con sesión y su propio layout: el panel del equipo en `/panel` (`AppLayout`, menú según el p… | Queda, en el párrafo de Arquitectura. |
| F004 | 22 | Arquitectura | - **`src/api/client.ts` es el único que habla con la API.** Ningún componente arma una URL ni usa `fetch`; ESL… | Queda. |
| F005 | 24 | Arquitectura | - **La sesión vive en una cookie httpOnly + SameSite=lax que pone el backend.** El frontend no guarda ni lee t… | Queda. |
| F006 | 31 | Arquitectura | - **Un fallo pasajero nunca cierra la sesión.** Pasajero es sin respuesta, 408, 429 o 5xx (`esErrorPasajero` e… | Queda. |
| F007 | 38 | Arquitectura | - **Los componentes interactivos se construyen sobre primitivas de Radix** (diálogo, select, tooltip, tabs, to… | Queda. |
| F008 | 42 | Arquitectura | - **`src/types/api.ts` se genera desde el OpenAPI** (`backend/scripts/generar_tipos_frontend.py`): si cambias … | Queda. |
| F009 | 46 | Arquitectura | - **Una página nueva en `App.tsx` va con `perezosa(<módulo>, '<Página>')`**, nunca con un import estático: el … | Queda. |
| F010 | 48 | Arquitectura | - **Los estilos son CSS propio con cascada de orden fijo**: `tokens → base → componentes → vistas`, impuesto p… | Queda. |
| F011 | 50 | Arquitectura | - **Ningún color, radio o sombra literal en un componente**: todo sale de `tokens.css`. `src/test/tokens.test.… | Queda condensada («todo sale de `tokens.css`»); la lista de lo que rechaza la guarda, en `docs/frontend/conventions.md` («Tokens y su guarda») y en la tabla de guardas de la raíz. |
| F012 | 56 | Arquitectura | - Toda lectura va por React Query con clave que incluya los filtros (`['familias', filtros]`) y toda pantalla … | Queda. |
| F013 | 58 | Arquitectura | - **El día de un instante (`2026-11-13T00:30:00Z`) sale de `diaISO` (`lib/formato.ts`)**, en la zona de Colomb… | Sin cambios: «La interfaz está en rediseño» pasa a «Todas las pantallas están rediseñadas». |
| F014 | 61 | Arquitectura | - **Toda pantalla nueva llega con sus pruebas.** Vitest + Testing Library para componentes, con la API simulad… | Queda. |
| F015 | 71 | Diseño | La interfaz está en rediseño con la marca real de TIMU: el orden y el estado de cada unidad están en [`docs/ho… | Queda. |
| F016 | 74 | Diseño | - **El hook de diseño solo revisa lo editado con Edit/Write**: un fichero de interfaz copiado o generado con u… | Queda, en la viñeta del hook de Diseño (con F063). |
| F017 | 77 | Diseño | - **Sorteos de la skill**: `serve-question --wait --key <k>` sale con 3 cada 60 s sin respuesta: repítelo en b… | Queda, en dos viñetas (sorteos y contrato de la superficie). |
| F018 | 86 | Diseño | - **Color, tipografía, logo y voz**: [`docs/manual-de-marca.md`](../docs/manual-de-marca.md). Los componentes … | Queda, en el párrafo de Diseño. |
| F019 | 88 | Diseño | - **Decisiones de diseño**: la skill del repositorio, `/impeccable`, con [`PRODUCT.md`](../PRODUCT.md) y el si… | Queda, en el párrafo de Diseño y en la viñeta del revisor final. |
| F020 | 92 | Diseño | - **Una sola acción verde llena (`btn-primario`) por vista**; las confirmaciones destructivas van con `btn-pel… | Queda, en la viñeta del revisor final. |
| F021 | 94 | Diseño | - **Las tablas nuevas usan `tabla-apilable`**, con `data-etiqueta` en cada celda y las acciones de fila en `td… | Queda. |
| F022 | 96 | Diseño | - **El título de una tarjeta de primer nivel es un `h2` en `.tarjeta-cabeza`** (Inter, no GeosansLight: `.tarj… | Queda, sin el selector `> h2`; entera, en `docs/frontend/conventions.md` y `components.md`. |
| F023 | 98 | Diseño | - **GeosansLight (`--fuente-titulos`) solo en `h1` y `h2` de 20 px o más**; uno más pequeño vuelve a Inter. El… | Queda. |
| F024 | 101 | Diseño | - **Para mirar una pantalla** (un script de Playwright contra :5173, con sesión o sin ella, y sus trampas de s… | Queda, en la viñeta del revisor final. |
| F025 | 103 | Diseño | - [`docs/frontend/`](../docs/frontend/) (components, layouts, conventions) describe lo construido: qué pieza y… | Queda, en la cabecera (enlaces a convenciones, componentes, plantillas y trampas). |
| F026 | 109 | Trampas conocidas (pruebas, es | - La ficha vacía y la abierta de un listado con ficha comparten `aria-label` («Ruta abierta»): espera a un ele… | **Se mueve** a `docs/frontend/trampas.md`. |
| F027 | 110 | Trampas conocidas (pruebas, es | - Si una prueba falla con «peticiones sin handler» que no son suyas, eran de la anterior: `setup.ts` ya espera… | Queda resumida entre las trampas que más se tropiezan; entera, en `docs/frontend/trampas.md`. |
| F028 | 113 | Trampas conocidas (pruebas, es | - Con una ventana de Radix abierta, el resto de la página queda oculto a los lectores de pantalla y `findByRol… | Queda resumida entre las trampas que más se tropiezan; entera, en `docs/frontend/trampas.md`. |
| F029 | 114 | Trampas conocidas (pruebas, es | - `Pestanas` sin `valor` no cambia de pestaña al cambiar la URL: un enlace desde otra pestaña que abre un regi… | **Se mueve** a `docs/frontend/trampas.md`. |
| F030 | 115 | Trampas conocidas (pruebas, es | - Dentro de `.fila-cuerpo` cada `span` es un bloque: un dato en un `span` propio («60 min», un número) parte l… | **Se mueve** a `docs/frontend/trampas.md`. |
| F031 | 116 | Trampas conocidas (pruebas, es | - `npx eslint`, `npx tsc` o `npx vitest` desde la raíz del repositorio descargan otra versión y fallan: se cor… | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F032 | 117 | Trampas conocidas (pruebas, es | - Con la máquina cargada (`uptime` alto), `verificar` agota los tiempos de Vitest: corre los mismos pasos por … | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F033 | 119 | Trampas conocidas (pruebas, es | - `playwright test -g` compara con el título unido por espacios, no por «›»: la ruta `admin` del barrido es `-… | **Se mueve** a `docs/frontend/trampas.md`. |
| F034 | 120 | Trampas conocidas (pruebas, es | - **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana `base`. Los comunes van … | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F035 | 121 | Trampas conocidas (pruebas, es | - En jsdom el parser multipart de undici no acepta el `File` de jsdom, y el nombre llega como `blob`: una subi… | **Se mueve** a `docs/frontend/trampas.md`. |
| F036 | 122 | Trampas conocidas (pruebas, es | - Al simular `window.location` con `vi.stubGlobal`, dale el `pathname` de una página pública: si no, el client… | **Se mueve** a `docs/frontend/trampas.md`. |
| F037 | 123 | Trampas conocidas (pruebas, es | - El proyecto no usa Prettier: no corras `npx prettier`, que descarga uno y reformatea el fichero entero. El f… | Queda, unida a la de `npx eslint`; también en `docs/frontend/trampas.md`. |
| F038 | 124 | Trampas conocidas (pruebas, es | - Vite incrusta como `data:` los recursos de menos de 4 KB: compara el `src` con el import del fichero, no con… | **Se mueve** a `docs/frontend/trampas.md`. |
| F039 | 125 | Trampas conocidas (pruebas, es | - Con una ventana de Radix abierta, el `body` lleva `pointer-events: none` y `elementFromPoint` se lo salta: q… | **Se mueve** a `docs/frontend/trampas.md`. |
| F040 | 126 | Trampas conocidas (pruebas, es | - Una regla con `display:` le gana al atributo `hidden`, y jsdom no aplica el CSS: un pliegue que no pliega pa… | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F041 | 128 | Trampas conocidas (pruebas, es | - `moneda()` separa con espacio duro (`$ 225.000`), y lo mismo cualquier `\u00a0` (el «40 %» que da la API): T… | **Se mueve** a `docs/frontend/trampas.md`. |
| F042 | 131 | Trampas conocidas (pruebas, es | - En `e2e/`, `page.route` da prioridad al último registrado: el comodín (`**/api/v1/**`) primero y las rutas d… | **Se mueve** a `docs/frontend/trampas.md`. |
| F043 | 133 | Trampas conocidas (pruebas, es | - Un handler de MSW que ignora los parámetros contesta igual a dos consultas de la misma ruta: si la pantalla … | **Se mueve** a `docs/frontend/trampas.md`. |
| F044 | 135 | Trampas conocidas (pruebas, es | - Para congelar la hora sin romper MSW ni userEvent: `vi.useFakeTimers({ toFake: ['Date'] })` y `vi.useRealTim… | **Se mueve** a `docs/frontend/trampas.md`. |
| F045 | 137 | Trampas conocidas (pruebas, es | - `useNombreTipoServicio` devuelve el código («consulta domiciliaria») hasta que llega el catálogo: un nombre … | **Se mueve** a `docs/frontend/trampas.md`. |
| F046 | 139 | Trampas conocidas (pruebas, es | - `npm run test:e2e` sirve `dist/` con `vite preview` (y en local reutiliza el que ya esté arriba): no recompi… | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F047 | 141 | Trampas conocidas (pruebas, es | - Para enfocar un campo al abrir un `Modal`, `autoFocus` en el campo: Radix respeta el foco que ya está dentro… | **Se mueve** a `docs/frontend/trampas.md`. |
| F048 | 143 | Trampas conocidas (pruebas, es | - `:is()` no admite pseudoelementos (`:is(.a::after, .b)` invalida la regla entera): sepáralos con coma. | **Se mueve** a `docs/frontend/trampas.md`. |
| F049 | 144 | Trampas conocidas (pruebas, es | - jsdom no desplaza: para probar un manejador de `scroll`, `Object.defineProperty(el, 'scrollTop', { value, co… | **Se mueve** a `docs/frontend/trampas.md`. |
| F050 | 146 | Trampas conocidas (pruebas, es | - Una animación de CSS se prueba en `e2e/` leyendo `getComputedStyle(el, '::before').animationName`; con `test… | **Se mueve** a `docs/frontend/trampas.md`. |
| F051 | 148 | Trampas conocidas (pruebas, es | - `margin-inline: auto` en un hijo de grid o flex lo encoge a su contenido: dale también `width: min(<máx>, 10… | **Se mueve** a `docs/frontend/trampas.md`. |
| F052 | 150 | Trampas conocidas (pruebas, es | - `verificar` muestra un aviso previo de ESLint en `AuthContext.tsx` (`react-refresh/only-export-components`):… | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F053 | 152 | Trampas conocidas (pruebas, es | - Una ayuda dentro del `<label>` entra en el nombre accesible del campo («Valor de la atención Lo que…») y `ge… | **Se mueve** a `docs/frontend/trampas.md`. |
| F054 | 154 | Trampas conocidas (pruebas, es | - El `onSuccess` que se pasa a `mutate(datos, { onSuccess })` no se ejecuta si el componente que llamó se desm… | **Se mueve** a `docs/frontend/trampas.md`. |
| F055 | 159 | Trampas conocidas (pruebas, es | - Un bloque nuevo de `vistas.css` insertado antes de `.filtros` o `.listado .filtros > .input` pierde contra e… | **Se mueve** a `docs/frontend/trampas.md`. |
| F056 | 163 | Trampas conocidas (pruebas, es | - `role="status"` en o dentro de un `h1` deja el encabezado sin nombre accesible en Chromium; jsdom sí lo calc… | **Se mueve** a `docs/frontend/trampas.md`. |
| F057 | 165 | Trampas conocidas (pruebas, es | - `.tabla-apilable` usa `td::before` para la etiqueta y apila bajo 640 px de contenedor, también en una ficha … | **Se mueve** a `docs/frontend/trampas.md`. |
| F058 | 168 | Trampas conocidas (pruebas, es | - Exportar funciones o constantes desde un `.tsx` de componentes dispara `react-refresh/only-export-components… | **Se mueve** a `docs/frontend/trampas.md`. |
| F059 | 170 | Trampas conocidas (pruebas, es | - `e2e/` no lo revisa `tsc`: sus datos simulados de la API se quedan atrás sin aviso (el comparador se cayó po… | Queda resumida entre las trampas que más se tropiezan; entera, en `docs/frontend/trampas.md`. |
| F060 | 172 | Trampas conocidas (pruebas, es | - Una página pública nueva va en `PAGINAS_PUBLICAS` (`src/api/client.ts`): si no, un 401 la manda a `/login`. … | Queda entre las trampas que más se tropiezan; también, entera, en `docs/frontend/trampas.md`. |
| F061 | 174 | Trampas conocidas (pruebas, es | - La guarda de tokens toma por color un nombre de variable con una palabra de color en inglés (`--linea-red` f… | **Se mueve** a `docs/frontend/trampas.md`. |
| F062 | 176 | Trampas conocidas (pruebas, es | - Dos Playwright a la vez se pisan: cada uno vacía `test-results/` al empezar y el otro falla con `ENOENT … .t… | Queda resumida entre las trampas que más se tropiezan; entera, en `docs/frontend/trampas.md`. |
| F063 | 178 | Trampas conocidas (pruebas, es | - Si el hook de diseño no devuelve nada (ni siquiera «No deterministic…»), pasa el detector a mano: `.claude/s… | Queda, en la viñeta del hook de Diseño; también en `docs/frontend/trampas.md`. |
