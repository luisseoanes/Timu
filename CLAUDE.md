# CLAUDE.md

Lo transversal del repositorio. Las reglas de cada lado viven junto a su código y se cargan al
trabajar allí: [`backend/CLAUDE.md`](backend/CLAUDE.md) (una línea por regla; el porqué, en
[`docs/backend/`](docs/backend/)) y [`frontend/CLAUDE.md`](frontend/CLAUDE.md). Un cambio que cruza los
dos lados (un schema nuevo, una regla de sesión) lee los dos.

## Qué es este repositorio

TIMU, plataforma de gestión veterinaria por afiliación. **La única fuente de verdad de lo que hay que
construir es el [documento de requerimientos](docs/documento-requerimientos-funcionales.md)**, copia
literal del PDF (`~/Descargas/documento-requerimientos-funcionales.pdf`) que no se edita; la
[propuesta](docs/propuesta-timu-puntos-15-19.md) le responde.

- **Cómo se citan.** Un requisito (`6.10`) o una sección por número (`Sección 8`): el documento de
  requerimientos (la propuesta repite los `6.x` en su tabla B y los números 15 a 19 porque responde a
  esos puntos, pero lo que se pide está en el documento). Una sección por letra (`sección A` a `E`): la
  sección 15 de la propuesta.
- **Al implementar, se parte del requisito del documento**, no de un resumen intermedio, y se cita su
  número en el código y en el commit.
- **Lo que falta.** Dentro del código, [`docs/pendiente-en-el-codigo.md`](docs/pendiente-en-el-codigo.md)
  (el antiguo backlog por unidades se retiró el 2026-11-19 porque se había alejado de los requisitos).
  Fuera (sandbox de Wompi, plantillas de Meta, decisiones de TIMU),
  [`docs/pendientes-externos.md`](docs/pendientes-externos.md): allí **un valor provisional sigue
  pendiente aunque funcione**, y no se marca resuelto hasta que se informe explícitamente que TIMU dio
  el valor oficial.
- **Lo que cumple y lo que no.** La [auditoría del documento](docs/auditoria-requisitos/README.md)
  (empezada el 2026-11-24) contrasta cada obligación con el código, con su evidencia: su README dice
  el método, el orden por bloques y por dónde va. Hasta cerrarla, se audita sin arreglar.
- **Diseño.** El frontend se rediseñó con la marca real de TIMU por unidades (`R0-…` a `R4-…`, en la
  [hoja de ruta](docs/hoja-de-ruta-rediseno.md)). La identidad está en el
  [manual de marca](docs/manual-de-marca.md), el sistema en [`DESIGN.md`](DESIGN.md) y el producto en
  [`PRODUCT.md`](PRODUCT.md). Lo gobierna la skill `/impeccable` (`.claude/skills/`, con su hook en
  `.claude/settings.json`).

## Comandos

```bash
# Todo el stack (api, worker, beat, db, pgbouncer, redis, almacenamiento S3, web). `inicializar` migra,
# carga catálogos, crea admin@timu.co / cambiar123 y el bucket antes de api, worker y beat. Sin copiar
# ningún .env: backend/.env.example es la base y backend/.env (si existe) la sobrescribe. Puertos del
# host ocupados por otro proyecto → .env de la raíz (ver .env.example).
docker compose up --build
docker compose exec api python -m scripts.datos_demo   # usuarios, familias, ruta… de prueba (solo local; solo crea lo que falta)
docker compose exec api python -m scripts.operacion_demo   # después: ocho semanas de operación (~5 min; si ya sembró, nada)
                                      # Qué deja cada uno, cómo se amplían y sus límites: docs/datos-de-demostracion.md
docker compose run --rm inicializar   # tras traer una migración nueva, sin reiniciar el stack
docker compose up -d api              # tras cambiar backend/.env.example: el entorno se lee al crear el contenedor;
                                      # --reload no lo recarga (worker y beat, si leen la variable)
docker compose up -d --build -V       # tras traer dependencias nuevas: el código va montado, las librerías
                                      # van en la imagen, y -V renueva el node_modules anónimo de `web`
# `exec api` trabaja en /app, que es backend/ montado: un script de prueba copiado ahí aparece en el
# repositorio. Va al /tmp del contenedor: `exec -T -w /app -e PYTHONPATH=/app api python /tmp/x.py`

# Backend sin Docker
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload

docker compose up -d db-test        # PostgreSQL de pruebas (puerto 5433, perfil `test`: el up general no la levanta). Sin esto, pytest aborta.
pytest                              # suite completa, con cobertura y umbral del 92%
pytest -m unit                      # sólo lo que no toca la base de datos
pytest tests/test_alcance.py::test_una_familia_solo_se_ve_a_si_misma   # una sola prueba
ruff format . && ruff check . && mypy app
python scripts/generar_tipos_frontend.py   # regenera frontend/src/types/api.ts desde el OpenAPI; no se edita a mano.
                                           # Solo exporta los schemas de su lista ESQUEMAS: uno nuevo se añade ahí

# Frontend
cd frontend && npm install
npm run dev                         # 5173, con proxy /api → localhost:8000
npm run verificar                   # lint + typecheck + cobertura + build (lo mismo que CI)
npm run test:watch                  # pruebas de componentes en vigilancia
npm run test:e2e                    # Playwright con la API interceptada (requiere: npx playwright install chromium)
npm run test:e2e:stack              # recorridos contra el stack real: docker compose up + datos_demo antes

# CI: log de un job (`gh run view --log-failed` a veces sale vacío)
gh api --allow-escape-sequences repos/{owner}/{repo}/actions/jobs/<id>/logs | sed 's/\x1b\[[0-9;]*m//g'
gh run watch <id> --exit-status --interval 60 && gh run view <id> --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
# `gh run watch` puede salir con 1 a mitad del run: confírmalo con `gh run view <id> --json status,conclusion`
```

- `npm run verificar 2>&1 | tail` o `pytest | tail` devuelven el código de `tail`, no el de la prueba:
  guarda el log, mira el `$?` del propio comando y lee el resultado en el log.
- `docker compose down -v` no baja `db-test` (va en el perfil `test`): sigue arriba con su base efímera.
- **Prueba de carga**: mide el volumen proyectado a 12 meses (Sección 14) y mete datos sintéticos, así
  que se corre en un proyecto aparte ([`docs/prueba-de-carga.md`](docs/prueba-de-carga.md)). El CI corre
  una versión reducida en el job del stack.

## Entorno de desarrollo: un solo comando

**Desde un clon limpio, `docker compose up --build` deja el stack completo funcionando, sin pasos
manuales ni ficheros que copiar.** Es una invariante: ningún cambio (de infraestructura, backend,
frontend o dependencias) se da por terminado si la rompe, y el compose se actualiza en el mismo cambio
que lo hace necesario.

| Si el cambio… | …también tiene que |
| --- | --- |
| añade una variable de entorno | ir en `backend/.env.example` con un valor que funcione en local (o vacía si la función se apaga sin ella). Si depende del host (un puerto, una URL que abre el navegador), va en el `environment` del compose, derivada de `TIMU_*_PORT`, como `STORAGE_PUBLIC_ENDPOINT_URL`. |
| añade una dependencia | ir con versión fija en `requirements.txt` (API) o `requirements-worker.txt` (solo worker), o en `package.json` con su lockfile. Si una transitiva rompe el arranque, se fija también, con un comentario del porqué (ver `kombu`). |
| necesita un paso de preparación (datos base, un bucket, un recurso externo) | ir en `backend/scripts/inicializar.py`, idempotente. Nunca como «después ejecuta X» en la documentación. |
| añade una migración | nada más: `inicializar` aplica `upgrade head` en cada arranque. |
| añade un servicio | ir en el compose con `healthcheck` si otros dependen de él, `depends_on` con condición (`service_healthy`, `service_completed_successfully`), puerto del host configurable (`TIMU_<SERVICIO>_PORT`, documentado en el `.env.example` de la raíz) y `profiles` si no es del día a día (como `db-test` y `respaldos`). |
| toca un Dockerfile, el contexto de build o la estructura de directorios que montan los volúmenes | comprobarse con `--build`, no con la imagen que ya estaba. |

Si el cambio toca alguna de esas filas, se verifica en un proyecto aparte (para no borrar los datos del
habitual, que se para antes porque comparten puertos):

```bash
docker compose stop
docker compose -p timu-verificacion up --build -d
docker compose -p timu-verificacion ps -a        # inicializar «Exited (0)», el resto en marcha
curl -fsS "$(docker compose -p timu-verificacion port api 8000)/health"   # db, redis y workers en «ok»
# recién levantado responde 503 unos segundos, hasta que los workers se registran: reintenta
docker compose -p timu-verificacion down -v --rmi local
docker compose up -d
```

Si no se hizo, se dice explícitamente al entregar el cambio. El job **Stack con un solo comando** de
`ci.yml` repite lo mismo en cada empuje a `main` y bloquea el release, pero para entonces el commit ya
está en `main`: la verificación local es la que evita romperlo.

## Staging en Railway: cada empuje verde se despliega solo

Railway (proyecto `timu`, entorno `staging`) despliega `api`, `worker` y `web` desde `main` en cuanto el
CI de ese commit sale en verde («Wait for CI»). Configuración de cada servicio y cómo volver a sembrar:
[`docs/despliegue-staging.md`](docs/despliegue-staging.md).

- **Las migraciones llegan solas** (el *pre-deploy* de la API corre `inicializar`): nunca a mano, y
  escritas como si hubiera datos reales; una que solo funciona sobre una base vacía rompe el despliegue.
- **Una variable que `Settings` exige desplegado se pone en Railway antes de empujar** el cambio que la
  pide; si no, `inicializar` no arranca.
- **El panel de staging es el compilado** (`frontend/Dockerfile.despliegue`, Caddy): un cambio que toca
  su build, el `Caddyfile` o cómo llega a `/api` se prueba con esa imagen, no con `npm run dev`.
- **Tras empujar se comprueba el despliegue** de los servicios que el cambio toca (`railway deployment
  list -p <proyecto> -s <servicio> -e staging --json`, con el id del proyecto de `despliegue-staging.md`:
  sin `-p` responde «No linked project found»; o el panel de Railway). Uno fallido deja staging en la
  versión anterior sin que el CI lo diga.

## Estándares de calidad (Secciones 3 y 4)

El documento pide una solución modular que crezca sin reemplazar su base, con escalabilidad, seguridad,
integridad, trazabilidad, interoperabilidad, capacidad de integración y sostenibilidad.
[`docs/estandares-calidad.md`](docs/estandares-calidad.md) traduce cada una a reglas, con su guarda y la
deuda que queda. **Un cambio que toque una de sus tablas cumple la regla o cierra la deuda; no relaja la
guarda.** Las tres que más se tropiezan:

- **Capas**: `core` y `schemas` no importan ningún dominio, `integrations` solo la base, y un dominio no
  importa `api` ni `workers` (salvo su `router.py`, que usa `app.api.deps`). Ninguna dependencia nueva
  entre dominios cierra un ciclo: se invierte con un evento del outbox o inyectando la función, como
  `comunicaciones.conectar_entrantes`.
- **Eventos**: todo nombre que se publica o se escucha se declara con `declarar_evento` en el dominio que
  lo emite.
- **Dependencias**: ninguna vulnerabilidad publicada en lo que se despliega; sin versión corregida,
  `--ignore-vuln` en el job con motivo y fecha (en las herramientas de npm, `EXCEPCIONES` de
  `.github/scripts/auditar-npm.mjs`).

## Invariante: el CI ejecuta todas las pruebas, y todas pasan

Ninguna prueba existe sin que el CI la ejecute en cada empuje a `main`, y ningún cambio se da por
terminado si la deja fuera, saltada o en rojo. Lo vigilan guardas que forman parte de las propias
suites, y ninguna se desactiva:

| Guarda | Qué hace fallar |
| --- | --- |
| `backend/tests/conftest.py` | Una prueba saltada o `xfail` (`pytest_sessionfinish`); una `unit` que usa la base o una con las dos marcas (`pytest_collection_modifyitems`); y, con `test_persistencia.py`, una suite conectada con un rol que salta las protecciones de la base (superusuario o `BYPASSRLS`): las pruebas usan `timu_app`, como la aplicación (`esquema`). |
| `backend/tests/test_persistencia.py` y `test_migraciones.py` | Que el modelo y la base dejen de decir lo mismo. Cada regla de «Persistencia» de `backend/CLAUDE.md` nombra su prueba (UUIDv7, enums y `CHECK`, conjuntos cerrados, claves foráneas a catálogos, grafos de estados, triggers de auditoría e inmutabilidad, `DELETE`, RLS y la matriz de `permisos_db.py`, caminos calientes de listados y del beat). Además: un valor por defecto de servidor que el modelo no declara, una migración que no se revierte, una llave de `publico` que ninguna política usa, un `restaurar.sh` que crea el rol distinto de las migraciones y un ciclo de llaves foráneas sin `use_alter` (`test_los_modelos_se_ordenan_sin_ciclos`). |
| `backend/tests/test_suite.py` | Una prueba del backend fuera de `tests/test_*.py`. |
| `backend/tests/test_base_tecnica.py` | Un ajuste de `Settings` que no está en `backend/.env.example`, salvo los `*_OVERRIDE` (`test_cada_ajuste_de_la_configuracion_esta_en_el_env_de_ejemplo`). |
| `backend/tests/test_arquitectura.py` | Una capa que importa de otra superior, un dominio que usa el router de otro, una dependencia entre dominios que cierra un ciclo nuevo, una entrada de `CICLOS_CONOCIDOS` que ya no hace falta o un import de `app` dentro de una función. |
| `backend/tests/test_permisos.py` | Que la guarda de permisos deje de ver rutas que publica el OpenAPI (`test_la_guarda_recorre_todas_las_rutas_de_la_api`: pasó al subir a FastAPI 0.162, cuando `app.routes` dejó de listarlas). |
| Job **Vulnerabilidades conocidas** de `ci.yml` | Una dependencia de la API, el worker o el panel con una vulnerabilidad publicada; en las herramientas de npm, una alta o crítica fuera de `EXCEPCIONES` de `.github/scripts/auditar-npm.mjs` (con motivo y fecha, solo sin versión corregida), o una excepción que ya no hace falta. |
| `frontend/src/test/tokens.test.ts` | Un color escrito a mano en `frontend/src` fuera de `styles/tokens.css` (`#hex`, `rgb()`, `oklch()` o un nombre, también en `style={{}}` y en atributos SVG), un `var(--…)` sin definir, un `z-index` fuera de la escala `--capa-*`, o un radio o el espaciado de una etiqueta escritos a mano en lugar de `--r-…` y `--tracking-etiqueta`. |
| `frontend/e2e-stack/responsive.spec.ts` | Una ruta que a 375, 768, 900 o 1280 px desborda en horizontal, tiene un fallo de WCAG 2.2 A o AA según axe-core (contraste, nombre con el texto visible, enlaces solo por color, tamaño de los objetivos, teclado…) o salta un nivel de encabezado; o una pantalla de `App.tsx` que el recorrido no abre. Mide cada pestaña (`pestanas: true`), cada sección de un índice por su dirección (`secciones`) y cada ficha que la pantalla abre desde la URL (`fichas`, con un registro de `datos_demo`); ante un 429 espera a `Retry-After` y vuelve a cargar, y si persiste falla en vez de medir una pantalla de error. Sin lista de excepciones: un fallo se arregla. |
| `frontend/e2e/publicas.spec.ts` | La encuesta, la verificación del carnet o el registro en línea que, con la API interceptada, desbordan o tienen un fallo de WCAG 2.2 A o AA a 375 o 1280 px. |
| `frontend/e2e-stack/recorridos.spec.ts` (ficha de familia) | Barras o línea pintadas sobre una ventana abierta, un control que se estira junto a un campo con ayuda, el pie de una ventana recortado o más de una acción verde llena por pestaña. |
| `frontend/src/test/arquitectura.test.ts` y `no-restricted-imports` de ESLint | Un import a un fichero interno de otro dominio del panel (por alias o por ruta relativa), un `index.ts` que reexporta algo ajeno, la base o `auth`/`catalogos` dependiendo de un dominio, un espacio de entrada importado fuera de `App.tsx` o un ciclo entre dominios. |
| `frontend/src/test/suite.test.ts` | Una prueba del panel fuera de los patrones de Vitest (`src/**/*.{test,spec}.ts(x)`) o de Playwright (`e2e/`, `e2e-stack/`), o desactivada con `.only`, `.skip`, `.todo` o `.fixme`. |
| `frontend/src/test/setup.ts` | Una petición que ninguna prueba simuló con MSW: la prueba falla en lugar de seguir en verde con un error de red que nadie miró (los catálogos comunes van en `src/test/handlers.ts`). Al terminar cada prueba deja salir y responder lo que estaba en vuelo antes de restaurar los handlers; si no, se lo cobraba a la siguiente. |
| `forbidOnly` de `frontend/playwright.config.ts` y `playwright.stack.config.ts` | Un `.only` en e2e cuando corre en CI. |
| Umbrales de cobertura | Que la cobertura baje del mínimo (abajo). |
| Umbrales `count>0` de `infra/carga/recorrido.js` | Una prueba de carga que no llegó a hacer peticiones: sin muestras, k6 da por cumplido cualquier umbral de tiempos. |
| `MINIMOS` de `backend/scripts/operacion_demo.py` | Una siembra de la operación por debajo de sus mínimos (rutas, visitas, encuestas respondidas, remisiones atendidas…): `Cliente.post` solo avisa de un error y sigue, y sin esto un cambio en la API podría vaciar la operación sin que nadie lo viera. |

Reglas que mantienen esto vivo:

- **El CI corre las suites enteras**: `pytest`, `npm run test:coverage`, `npm run test:e2e` y, en el job
  del stack, `npm run test:e2e:stack`, sin `-m`, `-k`, rutas ni filtros. En local se filtra para ir
  rápido; el CI nunca. La única excepción, a propósito, es la prueba de carga: el CI corre el mismo
  escenario con menos volumen, usuarios y duración, y la completa se corre en local.
- **Hay dos e2e y no se sustituyen**: `e2e/` intercepta la API y prueba el panel aislado, rápido y
  determinista; `e2e-stack/` recorre panel, portal y clínica aliada contra el stack real con los
  usuarios de `scripts.datos_demo`, en el job «Stack con un solo comando». Un recorrido nuevo que
  dependa de datos los crea `datos_demo`, no la prueba. Una sola sesión por perfil (ingreso y renovación
  comparten un límite de 10 por minuto y por IP; con los ocho perfiles van 9), y un recorrido busca lo que dejó `datos_demo` por su identidad, nunca el
  primero del listado (la ruta de la médica, con `rutaDemo`; si falla con «datos_demo no dejó ninguna
  ruta», se vuelve a sembrar hoy). El detalle: [`docs/frontend/e2e-stack.md`](docs/frontend/e2e-stack.md).
- **Una prueba que no puede pasar se arregla o se borra**, con la razón en el cuerpo del commit. No se
  salta, no se marca `xfail` y no se comenta.
- **Un tipo de prueba nuevo llega cableado al CI en el mismo cambio** (un runner, una carpeta fuera de
  los patrones, un proyecto de Playwright o un servicio que necesiten), con `ci.yml`, su guarda y esta
  tabla actualizados. Si no, esas pruebas no las corre nadie.
- **Todo cambio de comportamiento llega con sus pruebas**, y toda corrección con la prueba que habría
  detectado el fallo, que falla sin el arreglo.
- **Antes de empujar se corre en local lo que el cambio toca**: no hay pull requests, y el CI llega
  cuando el commit ya está en `main`.

**Umbrales de cobertura**: backend **92 %** combinando líneas y ramas (`--cov-fail-under` en
`pytest.ini`; las ramas, activadas en `pyproject.toml`), y panel **93 %** de líneas, **92 %** de
sentencias, **91 %** de funciones y **83 %** de ramas (`vitest.config.ts`). Están justo por debajo
de lo medido para que no se degraden solos, no como objetivo: cuando la cobertura sube, se suben en
el mismo commit, y bajarlos requiere una razón en el cuerpo del commit. La del backend varía unos 0,5
puntos entre ejecuciones del mismo código, así que una subida menor no obliga a subir el umbral (a
ras de lo medido, el CI fallaría por azar). Se mide con `concurrency = greenlet` porque los servicios corren dentro de `db.run_sync`: sin
eso, coverage deja de contar las líneas posteriores a la primera consulta y el informe miente.

`.github/workflows/ci.yml` ejecuta formato, análisis estático (con las reglas de seguridad `S` de Ruff),
tipos, todas las pruebas, la auditoría de vulnerabilidades y el job del stack; el release depende de
todos, así que no sale una versión sin la batería completa.

## Commits y publicación de versiones

Todo está en [`CONTRIBUTING.md`](CONTRIBUTING.md): **léelo antes de cada commit**. Fija qué va en cada
commit, el formato `tipo(scope): descripción`, los scopes, la longitud, los pies permitidos (ningún
`Co-Authored-By` ni enlace de sesión de Claude) y cómo `semantic-release` decide la versión.
`commits-sin-convencion.mjs` no mide los 72 caracteres: compruébalo con un comando que falle (exit ≠ 0)
encadenado con `&&` antes de `git push`. Con mucho trabajo sin commit, los commits se construyen en un
worktree aparte, con sus trampas ([`CONTRIBUTING.md` §2](CONTRIBUTING.md#tamaño)). Para fundir un
`--fixup` sin editor: `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash --autostash origin/main`.

## Convenciones de escritura

Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`, `cartera`),
clases CSS en singular (`.tarjeta`, `.distintivo-alerta`), docstrings, mensajes de error de la API y
commits (`feat(backend): …`). Los ficheros de `docs/` van en **kebab-case** (`manual-de-marca.md`); el
código sigue la convención de su lenguaje (`snake_case` en Python, `PascalCase` en los componentes de
React). El backend evita tildes en docstrings y comentarios; el frontend y la documentación sí las usan.
Sigue lo que ya haga cada fichero.
