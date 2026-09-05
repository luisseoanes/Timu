# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repositorio

Scaffold de TIMU, plataforma de gestión veterinaria por afiliación. El contrato funcional
vive en `docs/propuesta-timu-puntos-15-19.md` y el desglose ejecutable en
`docs/backlog.md` (101 unidades con ID `fase-módulo-consecutivo`, p. ej. `F1-CAR-08`).

Los comentarios del código citan requisitos por número (`6.10`, `6.16`, `sección C`): son
referencias a ese documento. Al implementar un módulo pendiente, busca su ID en el backlog
y respeta el criterio de aceptación que ya está escrito allí.

## Comandos

```bash
# Todo el stack (api, worker, beat, db, redis, minio, web)
docker compose up --build
docker compose exec api alembic upgrade head       # aplica el esquema
docker compose exec api python scripts/seed.py     # admin@timu.co / cambiar123

# Backend sin Docker
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload

docker compose up -d db-test        # PostgreSQL de pruebas (puerto 5433). Sin esto, pytest aborta.
pytest                              # suite completa, con cobertura y umbral del 70%
pytest -m unit                      # sólo lo que no toca la base de datos
pytest tests/test_alcance.py::test_una_familia_solo_se_ve_a_si_misma   # una sola prueba
ruff format . && ruff check . && mypy app

# Frontend
cd frontend && npm install
npm run dev                         # 5173, con proxy /api → localhost:8000
npm run verificar                   # lint + typecheck + cobertura + build (lo mismo que CI)
npm run test:watch                  # pruebas de componentes en vigilancia
npm run test:e2e                    # Playwright (requiere: npx playwright install chromium)
```

En el backend `python3 -m venv` no funciona en la máquina de Pedro: usa
`uv venv --python 3.12` (ver la memoria del proyecto).

## Arquitectura del backend

Un directorio por dominio en `app/modules/<dominio>/`, con hasta cuatro piezas:
`models.py` (SQLAlchemy) · `schemas.py` (Pydantic) · `service.py` (lógica y consultas) ·
`router.py` (HTTP). `app/modules/familias/` es la referencia completa del patrón; el resto
de dominios tiene modelos definidos y un router placeholder que devuelve
`Mensaje(detail="Modulo X: pendiente de implementar")`.

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
- **La transacción la cierra `get_db`**, no los servicios. Las funciones de `service.py`
  hacen `flush()` para obtener IDs; el commit ocurre al terminar la petición, y el rollback
  ante cualquier excepción. No metas `commit()` en un servicio.
- **Autorización con `require_roles`** de `app/core/deps.py`:
  `dependencies=[Depends(require_roles(Rol.ADMIN))]`. Los alias `DbSession` y `CurrentUser`
  son los que se inyectan en los endpoints; un endpoint sin `CurrentUser` queda público.
- **Enums de dominio en `app/core/enums.py`**, no en cada módulo. Son `StrEnum` y viajan
  como cadenas en la API.
- **Los estados de servicio pasan por `app/modules/servicios/state_machine.py`.** Rutas,
  portal y comunicaciones llaman a `aplicar()`; ningún módulo reimplementa el grafo de
  transiciones ni asigna un estado a mano.
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
  despacha después. Los manejadores se registran con `@al_ocurrir("nombre.evento")`.
- **El estado de un servicio se cambia con `state_machine.aplicar()`**, no asignando
  `servicio.estado` ni llamando a `transicionar()` suelta: `aplicar` valida la
  transición *y* deja publicado el evento que dispara los efectos de 6.10.
- **Los campos JSON usan `JSONTipo`** de `app/core/database.py`, que es JSONB en
  PostgreSQL (indexable con GIN) y JSON en el resto. Nunca el `JSON` de SQLAlchemy.
- **Las tareas de Celery usan `sesion_worker()`**, la sesión síncrona de
  `app/core/database.py`. Celery no es async: `asyncio.run()` dentro de una tarea crea
  un event loop por ejecución y no reaprovecha conexiones. Los endpoints siguen async;
  los workers, no. Cada tarea abre su `with sesion_worker() as db:`.
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
  apunta a MinIO (`docker compose up minio`) y en producción al bucket del cliente:
  cambian las variables `STORAGE_*`, no el código. Nada se sirve público, todo con
  `url_firmada()`.

Integraciones (`app/integrations/`) y webhooks (`app/api/v1/webhooks.py`) están separados a
propósito: los webhooks son públicos y se validan por token de verificación (Meta) o firma
HMAC (pasarela), nunca por JWT. Su trabajo es responder rápido y encolar en Celery.

Celery (`app/workers/`) corre en dos contenedores distintos: `worker` ejecuta y `beat`
programa. El `beat_schedule` está en `celery_app.py` en zona `America/Bogota`; las tareas
llevan nombre explícito (`cartera.revisar_mora`) porque el schedule las referencia por
cadena.

Configuración: `Settings` de `pydantic-settings` con `.env`. `DATABASE_URL` es un campo
computado a partir de las variables `POSTGRES_*`; `DATABASE_URL_OVERRIDE` la sustituye.

Tests: `httpx.AsyncClient` sobre ASGI, SQLite en memoria y `dependency_overrides[get_db]`
(ver `tests/conftest.py`). `pytest.ini` fija `asyncio_mode = auto`, así que las pruebas
async no necesitan decorador. Ojo: con el override, la sesión de test no pasa por el commit
de `get_db`, así que la prueba hace `await db.commit()` cuando necesita datos previos.

## Arquitectura del frontend

React 18 + Vite, alias `@/` → `src/`. Un directorio por dominio en `src/features/<dominio>/`
con su `api.ts` (React Query) y sus pantallas; una pieza sube a `src/components/` sólo
cuando la usan dos dominios. Las rutas de módulos aún no implementados renderizan
`<Placeholder>` con su ticket del backlog.

- **`src/api/client.ts` es el único que habla con la API.** Ningún componente arma una
  URL ni usa `fetch`; ESLint lo impide.
- **La sesión vive en una cookie httpOnly + SameSite=lax que pone el backend.** El
  frontend no guarda ni lee tokens: `localStorage` es legible por JavaScript y una XSS
  se llevaría la sesión, con historia clínica de por medio. Por eso el cliente va con
  `withCredentials: true` y `AuthContext` averigua si hay sesión preguntando a
  `/auth/me`. Hay una regla de ESLint que rechaza `localStorage`.
- **Los componentes interactivos se construyen sobre primitivas de Radix** (diálogo,
  select, tooltip, tabs, toast…). Radix aporta sólo comportamiento —foco atrapado,
  Escape, roles ARIA—; el aspecto sale íntegro de `tokens.css`. `src/components/Modal.tsx`
  es la referencia. No se escribe a mano un componente que Radix ya resuelve.
- **`src/types/` es el espejo tipado de los schemas de Pydantic.** Si cambias un schema del
  backend, actualiza el tipo en el mismo cambio.
- **Los estilos son CSS propio con cascada de orden fijo**: `tokens → base → componentes →
  vistas`, impuesto por `src/styles/index.css`. Alterar ese orden rompe las vistas.
- **Ningún color, radio o sombra literal en un componente**: todo sale de `tokens.css`. Un
  `#` en el diff de un componente es un rechazo en revisión.
- Toda lectura va por React Query con clave que incluya los filtros (`['familias', filtros]`)
  y toda pantalla cubre carga, error y vacío.
- **Toda pantalla nueva llega con sus pruebas.** Vitest + Testing Library para
  componentes, con la API simulada por MSW en `src/test/handlers.ts` — nunca con mock
  de axios, para que se pruebe también cómo se arma la petición. Playwright en `e2e/`
  para los recorridos. Se consulta por rol y etiqueta accesible (`getByRole`,
  `getByLabelText`), no por clase CSS: si la prueba no encuentra el control, un lector
  de pantalla tampoco.

`docs/frontend/` (design-system, components, layouts, conventions) es normativo para
cualquier pantalla nueva: léelo antes de escribir UI. `conventions.md` incluye la checklist
de revisión y la deuda conocida (sin tema oscuro, datos de ejemplo en el panel de inicio
hasta `F4-DAS-02`).

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
| Desarrollo | tras `docker compose up`, y cada vez que se trae una migración nueva |
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
ven entre sí y no hay que limpiar tablas. Los marcadores `unit` e `integration` separan
lo que necesita base de datos de lo que no (`--strict-markers` rechaza los inventados).

Umbrales de cobertura: 70% en el backend, 60% en el panel. Están para que no se
degraden solos, no como objetivo; bajarlos requiere una razón escrita en el PR.

`.github/workflows/ci.yml` corre en **cada push y cada pull request**: formato, análisis
estático, tipos, pruebas unitarias, de integración y de extremo a extremo. El release es
un job más, condicionado a `main`, así que no existe forma de publicar una versión que
no haya pasado la batería completa.

## Commits y publicación de versiones

Los commits no son sólo historial: **alimentan el release**. `semantic-release` los lee
en cada empuje a `main` y decide la versión a partir de ellos, así que un mensaje mal
formado es trabajo que no aparece en ninguna parte.

- Formato Conventional Commits: `tipo(scope): asunto`, en español y en minúscula.
- `feat` sube la *minor*, `fix`/`perf`/`revert` la *patch*; `docs`, `test`, `chore`,
  `ci`, `build`, `style` y `refactor` no publican versión.
- El **scope es libre** y sirve para agrupar el changelog: `feat(clinica)`,
  `fix(cartera)` o `feat(backend)` entran todos en el mismo release. También vale sin
  scope.
- Un cambio rompiente se marca con `!` en la cabecera (`feat(servicios)!: …`), no sólo
  con `BREAKING CHANGE` en el pie.
- `.github/scripts/commits-sin-convencion.mjs` avisa en el CI de los mensajes que
  `semantic-release` no sabría clasificar.

**Mientras la versión sea 0.x**, `release.config.js` mantiene la regla
`{ breaking: true, release: 'minor' }` para que un cambio rompiente no dispare el salto
a 1.0.0. **Al publicar la 1.0.0 hay que borrar esa línea**: si se queda, un breaking
daría 1.1.0 en lugar de 2.0.0.

## Convenciones de escritura

Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`,
`cartera`), clases CSS en singular (`.tarjeta`, `.distintivo-alerta`), docstrings, mensajes
de error de la API y commits (`feat(backend): …`). Los ficheros de `docs/` se nombran en
**kebab-case** (`design-system.md`, `propuesta-timu-puntos-15-19.md`); el código sigue la
convención de su lenguaje: `snake_case` en Python, `PascalCase` para los componentes de
React. El código del backend evita tildes en
docstrings y comentarios; el frontend y la documentación sí las usan. Sigue lo que ya haga
cada fichero.
