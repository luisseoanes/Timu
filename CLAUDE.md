# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repositorio

TIMU, plataforma de gestión veterinaria por afiliación. El contrato funcional
vive en `docs/propuesta-timu-puntos-15-19.md` y el desglose ejecutable en
`docs/backlog.md` (101 unidades con ID `fase-módulo-consecutivo`, p. ej. `F1-CAR-08`).

Los comentarios del código citan requisitos por número (`6.10`, `6.16`, `sección C`): son
referencias a ese documento. Al implementar un módulo pendiente, busca su ID en el backlog
y respeta el criterio de aceptación que ya está escrito allí.

## Comandos

```bash
# Todo el stack (api, worker, beat, db, redis, almacenamiento S3, web) en un solo comando.
# El servicio `inicializar` migra, carga catálogos, crea admin@timu.co / cambiar123 y el
# bucket antes de que arranquen api, worker y beat. No hace falta copiar ningún .env:
# backend/.env.example es la base y backend/.env (si existe) la sobrescribe.
# Puertos del host ocupados por otro proyecto → .env de la raíz (ver .env.example).
docker compose up --build
docker compose exec api python -m scripts.datos_demo   # familias, servicios, rutas… de prueba (solo local)
docker compose run --rm inicializar   # tras traer una migración nueva, sin reiniciar el stack

# Backend sin Docker
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload

docker compose up -d db-test        # PostgreSQL de pruebas (puerto 5433, perfil `test`: el up general no la levanta). Sin esto, pytest aborta.
pytest                              # suite completa, con cobertura y umbral del 89%
pytest -m unit                      # sólo lo que no toca la base de datos
pytest tests/test_alcance.py::test_una_familia_solo_se_ve_a_si_misma   # una sola prueba
ruff format . && ruff check . && mypy app
python scripts/generar_tipos_frontend.py   # regenera frontend/src/types/api.ts desde el OpenAPI; no se edita a mano

# Frontend
cd frontend && npm install
npm run dev                         # 5173, con proxy /api → localhost:8000
npm run verificar                   # lint + typecheck + cobertura + build (lo mismo que CI)
npm run test:watch                  # pruebas de componentes en vigilancia
npm run test:e2e                    # Playwright con la API interceptada (requiere: npx playwright install chromium)
npm run test:e2e:stack              # recorridos contra el stack real: docker compose up + datos_demo antes
```

En el backend `python3 -m venv` no funciona en la máquina de Pedro: usa
`uv venv --python 3.12` (ver la memoria del proyecto).

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

## Invariante: el CI ejecuta todas las pruebas, y todas pasan

Ninguna prueba existe sin que el CI la ejecute en cada empuje a `main`, y ningún cambio
se da por terminado si la deja fuera, saltada o en rojo. Lo vigilan guardas que forman
parte de las propias suites; ninguno se desactiva:

| Guarda | Qué hace fallar |
| --- | --- |
| `backend/tests/conftest.py` (`pytest_sessionfinish`) | Cualquier prueba saltada o `xfail` en el backend. |
| `backend/tests/conftest.py` (`pytest_collection_modifyitems`) | Una prueba `unit` que usa la base, o una con las dos marcas. |
| `backend/tests/test_suite.py` | Una prueba del backend fuera de `tests/test_*.py`. |
| `frontend/src/test/suite.test.ts` | Una prueba del panel fuera de los patrones de Vitest (`src/**/*.{test,spec}.ts(x)`) o de Playwright (`e2e/`, `e2e-stack/`), o desactivada con `.only`, `.skip`, `.todo` o `.fixme`. |
| `frontend/src/test/setup.ts` | Una petición del panel que ninguna prueba simuló con MSW: la prueba falla en lugar de seguir en verde con un error de red que nadie miró. Los catálogos comunes van en `frontend/src/test/handlers.ts`. |
| `forbidOnly` en `frontend/playwright.config.ts` y `frontend/playwright.stack.config.ts` | Un `.only` en e2e cuando corre en CI. |
| Umbrales de cobertura | Que la cobertura baje del mínimo (abajo). |

Reglas que mantienen esto vivo:

- **Los pasos de pruebas del CI corren las suites enteras**: `pytest`,
  `npm run test:coverage`, `npm run test:e2e` y, en el job del stack, `npm run test:e2e:stack`,
  sin `-m`, `-k`, rutas ni filtros. Para ir rápido en local se filtra; el CI nunca.
- **Hay dos e2e y no se sustituyen**: `e2e/` intercepta la API y prueba el panel aislado,
  rápido y determinista; `e2e-stack/` recorre panel, portal y clínica aliada contra el stack
  real con los usuarios de `scripts.datos_demo`, en el job «Stack con un solo comando». Un
  recorrido nuevo que dependa de datos los crea `datos_demo`, no la prueba. Ingresan una vez
  por perfil (`e2e-stack/sesiones.setup.ts`): login y renovación comparten un límite de 10
  por minuto y por IP, y una suite que ingresa en cada prueba se bloquea a sí misma.
  El perfil de equipo es `comercial@timu.co`, no el admin: `datos_demo` gasta el cupo de
  120 por minuto del admin justo antes.
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

Umbrales de cobertura: backend **89%** combinando líneas y ramas (`--cov-fail-under` en
`pytest.ini`; la cobertura de ramas está activada en `pyproject.toml`), y panel **87%**
de líneas, **86%** de sentencias y funciones y **76%** de ramas (`vitest.config.ts`).
Están justo por debajo de lo medido para que no se degraden solos, no como objetivo.
Cuando la cobertura sube, se suben en el mismo commit; bajarlos requiere una razón
escrita en el cuerpo del commit. La cobertura del backend se mide con
`concurrency = greenlet` porque los servicios corren dentro de `db.run_sync`. Sin eso,
coverage deja de contar las líneas posteriores a la primera consulta y el informe miente.

`.github/workflows/ci.yml` ejecuta formato, análisis estático, tipos, todas las pruebas y el
job del stack; el release depende de todos ellos, así que no sale una versión sin la
batería completa.

## Commits y publicación de versiones

Todo está en [`CONTRIBUTING.md`](CONTRIBUTING.md): **léelo antes de cada commit**. Fija
qué va en cada commit, el formato `tipo(scope): descripción`, la lista de scopes, la
longitud, los pies permitidos (ningún `Co-Authored-By` ni enlace de sesión de Claude) y
cómo `semantic-release` decide la versión.

## Convenciones de escritura

Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`,
`cartera`), clases CSS en singular (`.tarjeta`, `.distintivo-alerta`), docstrings, mensajes
de error de la API y commits (`feat(backend): …`). Los ficheros de `docs/` se nombran en
**kebab-case** (`design-system.md`, `propuesta-timu-puntos-15-19.md`); el código sigue la
convención de su lenguaje: `snake_case` en Python, `PascalCase` para los componentes de
React. El código del backend evita tildes en
docstrings y comentarios; el frontend y la documentación sí las usan. Sigue lo que ya haga
cada fichero.
