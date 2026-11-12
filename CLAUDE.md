# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repositorio

TIMU, plataforma de gestión veterinaria por afiliación. El contrato funcional
vive en `docs/propuesta-timu-puntos-15-19.md` y el desglose ejecutable en
`docs/backlog.md` (106 unidades con ID `fase-módulo-consecutivo`, p. ej. `F1-CAR-08`).
Lo que TIMU pidió está en
[`docs/documento-requerimientos-funcionales.md`](docs/documento-requerimientos-funcionales.md),
transcripción literal del documento de requerimientos al que responde la propuesta; no se
edita.

El código y el backlog citan los dos documentos así:

- Requisito por número (`6.10`, `6.16`) o sección por número (`Sección 8`, `Sección 14`): el
  documento de requerimientos. La propuesta repite los números `6.x` en su tabla B y
  reutiliza los números 15 a 19 porque responde a esos puntos, pero lo que se pide está en
  el documento de requerimientos.
- Sección por letra (`sección A`, `Sección C`): los apartados A a E de la sección 15 de la
  propuesta.

Al implementar un módulo pendiente, busca su ID en el backlog y respeta el criterio de
aceptación que ya está escrito allí. El frontend está en rediseño con la marca real de TIMU:
sus unidades (`R0-…` a `R4-…`) están en
[`docs/hoja-de-ruta-rediseno.md`](docs/hoja-de-ruta-rediseno.md), la identidad en
[`docs/manual-de-marca.md`](docs/manual-de-marca.md), el sistema de diseño en
[`DESIGN.md`](DESIGN.md) y el contexto de producto en [`PRODUCT.md`](PRODUCT.md). El diseño lo
gobierna la skill del repositorio (`/impeccable`,
en `.claude/skills/`, con su hook en `.claude/settings.json`). Lo que falta fuera del código
para cerrar un requisito (sandbox de Wompi, plantillas de Meta, decisiones de TIMU) está en
[`docs/pendientes-externos.md`](docs/pendientes-externos.md).

## Comandos

```bash
# Todo el stack (api, worker, beat, db, pgbouncer, redis, almacenamiento S3, web) en un solo comando.
# El servicio `inicializar` migra, carga catálogos, crea admin@timu.co / cambiar123 y el
# bucket antes de que arranquen api, worker y beat. No hace falta copiar ningún .env:
# backend/.env.example es la base y backend/.env (si existe) la sobrescribe.
# Puertos del host ocupados por otro proyecto → .env de la raíz (ver .env.example).
docker compose up --build
docker compose exec api python -m scripts.datos_demo   # familias, servicios, rutas… de prueba (solo local)
docker compose run --rm inicializar   # tras traer una migración nueva, sin reiniciar el stack
docker compose up -d --build -V       # tras traer dependencias nuevas: el código va montado, las librerías
                                      # van en la imagen, y -V renueva el node_modules anónimo de `web`

# Backend sin Docker
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload

docker compose up -d db-test        # PostgreSQL de pruebas (puerto 5433, perfil `test`: el up general no la levanta). Sin esto, pytest aborta.
pytest                              # suite completa, con cobertura y umbral del 91%
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
```

### Prueba de carga

Mide el volumen proyectado a 12 meses (F4-QAA-02) y mete datos sintéticos, así que se corre en
un proyecto aparte: procedimiento en [`docs/prueba-de-carga.md`](docs/prueba-de-carga.md). El CI
corre una versión reducida en el job del stack.

## Entorno de desarrollo: un solo comando

**Desde un clon limpio, `docker compose up --build` deja el stack completo funcionando,
sin pasos manuales ni ficheros que copiar.** Es una invariante del proyecto: ningún
cambio —de infraestructura, backend, frontend o dependencias— se da por terminado si la
rompe, y el compose se actualiza en el mismo cambio que lo hace necesario.

| Si el cambio… | …también tiene que |
| --- | --- |
| añade una variable de entorno | ir en `backend/.env.example` con un valor que funcione en local (o vacía si la función se apaga sin ella). Si depende del host (un puerto, una URL que abre el navegador), va en el `environment` del compose, derivada de `TIMU_*_PORT`, como `STORAGE_PUBLIC_ENDPOINT_URL`. |
| añade una dependencia | ir con versión fija en `requirements.txt` (API) o `requirements-worker.txt` (solo worker), o en `package.json` con su lockfile. Si una transitiva rompe el arranque, se fija también, con un comentario del porqué (ver `kombu`). |
| necesita un paso de preparación (datos base, un bucket, un recurso externo) | ir en `backend/scripts/inicializar.py`, idempotente. Nunca como «después ejecuta X» en la documentación. |
| añade una migración | nada más: `inicializar` aplica `upgrade head` en cada arranque. |
| añade un servicio | ir en el compose con `healthcheck` si otros dependen de él, `depends_on` con condición (`service_healthy`, `service_completed_successfully`), puerto del host configurable (`TIMU_<SERVICIO>_PORT`, documentado en el `.env.example` de la raíz) y `profiles` si no es del día a día (como `db-test` y `respaldos`). |
| toca un Dockerfile, el contexto de build o la estructura de directorios que montan los volúmenes | comprobarse con `--build`, no con la imagen que ya estaba. |

Cómo se verifica cuando el cambio toca cualquiera de esas filas. Se usa un proyecto
aparte para no borrar los datos del habitual, y hay que pararlo antes porque comparten
puertos:

```bash
docker compose stop
docker compose -p timu-verificacion up --build -d
docker compose -p timu-verificacion ps -a        # inicializar «Exited (0)», el resto en marcha
curl -fsS "$(docker compose -p timu-verificacion port api 8000)/health"   # db, redis y workers en «ok»
# recién levantado responde 503 unos segundos, hasta que los workers se registran: reintenta
docker compose -p timu-verificacion down -v --rmi local
docker compose up -d
```

Si no se ha hecho esta comprobación, se dice explícitamente al entregar el cambio. El
job **Stack con un solo comando** de `.github/workflows/ci.yml` repite lo mismo en cada
empuje a `main` y bloquea el release si falla, pero para entonces el commit ya está en
`main`: la verificación local es la que evita romperlo.

## Dónde está cada cosa

Este fichero es lo transversal. Las reglas de cada lado viven junto a su código y se
cargan al trabajar allí:

- [`backend/CLAUDE.md`](backend/CLAUDE.md): arquitectura del backend, migraciones y cómo
  se prueba contra PostgreSQL.
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md): arquitectura del panel, sesión en el
  navegador, estilos y pruebas con MSW.

Un cambio que cruza los dos lados (un schema nuevo, una regla de sesión) lee los dos.

## Estándares de calidad (Secciones 3 y 4)

El documento de requerimientos exige una solución modular que crezca sin reemplazar su
base, y escalabilidad, seguridad, integridad, trazabilidad, interoperabilidad, capacidad de
integración y sostenibilidad. [`docs/estandares-calidad.md`](docs/estandares-calidad.md)
traduce cada uno a reglas, dice qué guarda las hace cumplir y lista la deuda que queda.
**Un cambio que toque una de sus tablas cumple la regla o cierra la deuda; no relaja la
guarda.** Las tres que más se tropiezan:

- **Capas**: `core` y `schemas` no importan ningún dominio, `integrations` solo la base, y
  un dominio no importa `api` ni `workers` (salvo su `router.py`, que usa `app.api.deps`).
  Ninguna dependencia nueva entre dominios puede cerrar un ciclo: se invierte con un evento
  del outbox o inyectando la función, como `comunicaciones.conectar_entrantes`.
- **Eventos**: todo nombre que se publica o se escucha se declara con `declarar_evento` en el
  dominio que lo emite.
- **Dependencias**: ninguna vulnerabilidad publicada en lo que se despliega; si no hay versión
  corregida, `--ignore-vuln` en el job con motivo y fecha.

## Invariante: el CI ejecuta todas las pruebas, y todas pasan

Ninguna prueba existe sin que el CI la ejecute en cada empuje a `main`, y ningún cambio
se da por terminado si la deja fuera, saltada o en rojo. Lo vigilan guardas que forman
parte de las propias suites; ninguno se desactiva:

| Guarda | Qué hace fallar |
| --- | --- |
| `backend/tests/conftest.py` (`pytest_sessionfinish`) | Cualquier prueba saltada o `xfail` en el backend. |
| `backend/tests/conftest.py` (`pytest_collection_modifyitems`) | Una prueba `unit` que usa la base, o una con las dos marcas. |
| `backend/tests/conftest.py` (`esquema`) y `backend/tests/test_persistencia.py` | Que la suite se conecte con un rol que salta las protecciones de la base (superusuario o `BYPASSRLS`): las pruebas usan `timu_app`, como la aplicación. |
| `backend/tests/test_persistencia.py` y `backend/tests/test_migraciones.py` | Que el modelo y la base dejen de decir lo mismo: una clave primaria sin UUIDv7, un enum o un `CHECK` sin migración, un conjunto cerrado como texto libre, una referencia a catálogo sin clave foránea, un grafo de estados o un trigger de auditoría o inmutabilidad que falte, una tabla de negocio con `DELETE`, una tabla sin RLS o una política distinta de la matriz de `permisos_db.py`, un valor por defecto de servidor que el modelo no declara, una migración que no se revierte, una consulta de un listado o de una tarea del beat que recorre entera una tabla que crece, una llave de `publico` que ninguna política usa, o un `restaurar.sh` que cree el rol distinto de las migraciones. |
| `backend/tests/test_suite.py` | Una prueba del backend fuera de `tests/test_*.py`. |
| `backend/tests/test_base_tecnica.py` (`test_cada_ajuste_de_la_configuracion_esta_en_el_env_de_ejemplo`) | Un ajuste de `Settings` que no aparece en `backend/.env.example` (salvo los `*_OVERRIDE`). |
| `backend/tests/test_arquitectura.py` | Una capa que importa de otra superior, un dominio que usa el router de otro, una dependencia entre dominios que cierra un ciclo nuevo, una entrada de `CICLOS_CONOCIDOS` que ya no hace falta, o un import de `app` dentro de una función. |
| `backend/tests/test_permisos.py` (`test_la_guarda_recorre_todas_las_rutas_de_la_api`) | Que la guarda de permisos deje de ver rutas que publica el OpenAPI (pasó al subir a FastAPI 0.162: `app.routes` ya no las lista). |
| Job **Vulnerabilidades conocidas** de `ci.yml` | Una dependencia de la API, el worker o el panel con una vulnerabilidad publicada. |
| `frontend/src/test/tokens.test.ts` | Un color escrito a mano en `frontend/src` fuera de `styles/tokens.css` (`#hex`, `rgb()`, `oklch()`, un nombre de color, también en `style={{}}` y en atributos SVG), un `var(--…)` que no está definido, o un `z-index` que no sale de la escala `--capa-*`. |
| `frontend/e2e-stack/responsive.spec.ts` | Una ruta que, a 375, 768 o 1280 px, desborda en horizontal o tiene texto con contraste insuficiente según axe-core, sin estar en `PENDIENTES`; una entrada de `PENDIENTES` que ya no falla (la lista solo encoge); o una pantalla de `App.tsx` que el recorrido no abre. Con `pestanas: true` mide cada pestaña; ante un 429 espera a `Retry-After` y vuelve a cargar, y si persiste falla en vez de medir una pantalla de error. |
| `frontend/e2e-stack/recorridos.spec.ts` (ficha de familia) | Barras o línea pintadas sobre una ventana abierta, un control que se estira junto a un campo con ayuda, el pie de una ventana recortado, o más de una acción verde llena por pestaña. |
| `frontend/src/test/arquitectura.test.ts` y `no-restricted-imports` de ESLint | Un import a un fichero interno de otro dominio del panel (por alias o por ruta relativa), un `index.ts` que reexporta algo ajeno, la base o `auth`/`catalogos` dependiendo de un dominio, un espacio de entrada importado fuera de `App.tsx`, o un ciclo entre dominios. |
| `frontend/src/test/suite.test.ts` | Una prueba del panel fuera de los patrones de Vitest (`src/**/*.{test,spec}.ts(x)`) o de Playwright (`e2e/`, `e2e-stack/`), o desactivada con `.only`, `.skip`, `.todo` o `.fixme`. |
| `frontend/src/test/setup.ts` | Una petición del panel que ninguna prueba simuló con MSW: la prueba falla en lugar de seguir en verde con un error de red que nadie miró. Los catálogos comunes van en `frontend/src/test/handlers.ts`. |
| `forbidOnly` en `frontend/playwright.config.ts` y `frontend/playwright.stack.config.ts` | Un `.only` en e2e cuando corre en CI. |
| Umbrales de cobertura | Que la cobertura baje del mínimo (abajo). |
| Umbrales `count>0` de `infra/carga/recorrido.js` | Una prueba de carga que no llegó a hacer peticiones: sin muestras, k6 da por cumplido cualquier umbral de tiempos. |

Reglas que mantienen esto vivo:

- **Los pasos de pruebas del CI corren las suites enteras**: `pytest`,
  `npm run test:coverage`, `npm run test:e2e` y, en el job del stack, `npm run test:e2e:stack`,
  sin `-m`, `-k`, rutas ni filtros. Para ir rápido en local se filtra; el CI nunca. La única
  excepción, decidida a propósito, es la prueba de carga: el CI corre el mismo escenario con
  menos volumen, usuarios y duración, y la completa se corre en local.
- **Hay dos e2e y no se sustituyen**: `e2e/` intercepta la API y prueba el panel aislado,
  rápido y determinista; `e2e-stack/` recorre panel, portal y clínica aliada contra el stack
  real con los usuarios de `scripts.datos_demo`, en el job «Stack con un solo comando». Un
  recorrido nuevo que dependa de datos los crea `datos_demo`, no la prueba. Ingresan una vez
  por perfil (`e2e-stack/sesiones.setup.ts`, cinco perfiles): login y renovación comparten un
  límite de 10 por minuto y por IP, y una suite que ingresa en cada prueba se bloquea a sí
  misma. Solo el perfil de equipo ingresa por el formulario, que gasta dos (renovación y
  ingreso); el resto, por la API. Con el ingreso previo del job suman 7: un perfil nuevo por el
  formulario cuesta dos. En local, dos ejecuciones seguidas ya lo agotan: espera un minuto.
  El perfil de equipo es `comercial@timu.co`, no el admin: `datos_demo` gasta el cupo de
  120 por minuto del admin justo antes. Por eso Administración se recorre con
  `gerencia@timu.co`, un administrador que `datos_demo` crea solo para los recorridos.
  Además, la API limita a 120 peticiones por minuto por usuario: no lances scripts propios
  con `comercial@timu.co` justo antes del barrido, o sus pantallas cargarán un 429.
- **Una prueba que no puede pasar se arregla o se borra**, con la razón en el cuerpo del
  commit. No se salta, no se marca `xfail` y no se comenta.
- **Un tipo de prueba nuevo llega cableado al CI en el mismo cambio**: un runner, una
  carpeta fuera de los patrones, un proyecto de Playwright o un servicio que necesiten
  las pruebas. Ese cambio actualiza también `ci.yml`, el guarda correspondiente y esta
  tabla. Si no, esas pruebas no las corre nadie.
- **Todo cambio de comportamiento llega con sus pruebas**, y toda corrección con la
  prueba que habría detectado el fallo. Esa prueba debe fallar sin el arreglo.
- **Antes de empujar se corre en local lo que el cambio toca**. No hay pull requests,
  así que el CI llega cuando el commit ya está en `main`.

Umbrales de cobertura: backend **91%** combinando líneas y ramas (`--cov-fail-under` en
`pytest.ini`; la cobertura de ramas está activada en `pyproject.toml`), y panel **90%**
de líneas, sentencias y funciones y **80%** de ramas (`vitest.config.ts`).
Están justo por debajo de lo medido para que no se degraden solos, no como objetivo.
Cuando la cobertura sube, se suben en el mismo commit; bajarlos requiere una razón
escrita en el cuerpo del commit. La cobertura del backend se mide con
`concurrency = greenlet` porque los servicios corren dentro de `db.run_sync`. Sin eso,
coverage deja de contar las líneas posteriores a la primera consulta y el informe miente.

`.github/workflows/ci.yml` ejecuta formato, análisis estático (con las reglas de seguridad
`S` de Ruff), tipos, todas las pruebas, la auditoría de vulnerabilidades y el job del
stack; el release depende de todos ellos, así que no sale una versión sin la batería
completa.

## Commits y publicación de versiones

Todo está en [`CONTRIBUTING.md`](CONTRIBUTING.md): **léelo antes de cada commit**. Fija
qué va en cada commit, el formato `tipo(scope): descripción`, la lista de scopes, la
longitud, los pies permitidos (ningún `Co-Authored-By` ni enlace de sesión de Claude) y
cómo `semantic-release` decide la versión. `commits-sin-convencion.mjs` no mide los 72
caracteres: compruébalo con un comando que falle (exit ≠ 0) encadenado con `&&` antes de
`git push`.

En el worktree de commits, Vitest necesita `ln -s <repo>/frontend/node_modules`. Ese enlace
aparece como no rastreado: añade rutas explícitas (nunca `git add -A`) y bórralo antes de
`git worktree remove --force`.

## Convenciones de escritura

Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`,
`cartera`), clases CSS en singular (`.tarjeta`, `.distintivo-alerta`), docstrings, mensajes
de error de la API y commits (`feat(backend): …`). Los ficheros de `docs/` se nombran en
**kebab-case** (`manual-de-marca.md`, `propuesta-timu-puntos-15-19.md`); el código sigue la
convención de su lenguaje: `snake_case` en Python, `PascalCase` para los componentes de
React. El código del backend evita tildes en
docstrings y comentarios; el frontend y la documentación sí las usan. Sigue lo que ya haga
cada fichero.
