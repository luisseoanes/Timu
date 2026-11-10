# TIMU — Plataforma integral

Plataforma de gestión veterinaria por afiliación descrita en
`docs/propuesta-timu-puntos-15-19.md` (sección 15.C — Tecnología). Arquitectura modular por
dominios: familias, planes, afiliaciones, cartera, servicios, preventivos, clínica, rutas,
comunicaciones, comercial, campañas, encuestas, clínicas aliadas, IA, portal y dashboard.

Tres espacios con su propio acceso: el **panel del equipo** (administración, comercial,
operaciones y médicos), el **portal de familias** y el de la **clínica aliada**.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 + FastAPI (async, OpenAPI autogenerado) |
| Frontend | React 18 + TypeScript + Vite + React Query |
| Base de datos | PostgreSQL 18 (RLS, triggers de integridad y auditoría) + PgBouncer + SQLAlchemy 2 + Alembic |
| Tareas programadas | Celery + Redis (`worker` ejecuta, `beat` programa) |
| Adjuntos | S3 compatible (SeaweedFS en desarrollo), siempre con URL firmada |
| Sesión | Cookies httpOnly: acceso corto y renovación que rota en cada uso |
| WhatsApp | Meta Cloud API oficial |
| Pagos | Wompi (webhooks firmados para la conciliación) |
| Rutas | Google OR-Tools + Google Maps Platform |
| IA | Claude, con prompts versionados que se evalúan antes de activarse |
| Infraestructura | Docker / Docker Compose |

## Puesta en marcha

```bash
docker compose up --build
```

Un solo comando: el servicio `inicializar` aplica las migraciones, carga los catálogos,
crea el usuario `admin@timu.co / cambiar123` y el bucket de adjuntos, y solo
entonces arrancan `api`, `worker` y `beat`. No hace falta copiar ningún `.env`:
`backend/.env.example` es la base y `backend/.env`, si existe, la sobrescribe. Las
integraciones externas (WhatsApp, Wompi, Maps, SMTP) se apagan solas mientras sus
variables estén vacías.

Si otro proyecto ocupa algún puerto del host, cópialo en la raíz y cámbialo ahí:

```bash
cp .env.example .env   # TIMU_API_PORT, TIMU_DB_PORT, TIMU_S3_PORT…
```

Servicios (puertos por defecto):

- Panel: http://localhost:5173
- API + Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health (base, Redis y workers)
- Almacenamiento S3 (SeaweedFS): http://localhost:9000
- PgBouncer, el pool por el que la aplicación llega a la base: localhost:6432

Datos de demostración (solo local) y migraciones nuevas con el stack ya arriba:

```bash
docker compose exec api python -m scripts.datos_demo
docker compose run --rm inicializar
```

`datos_demo` crea familias, servicios, rutas y campañas, y estos usuarios con la clave
`demo12345`: `medico@timu.co`, `operaciones@timu.co`, `comercial@timu.co`,
`aliada@timu.co` (clínica aliada) y `ana@example.com` (portal de familias).

`db-test` (perfil `test`) y `respaldos` (perfil `respaldos`) no arrancan con el `up`
general.

## Desarrollo sin Docker

```bash
# Backend: base, Redis y almacenamiento del compose. `inicializar` aplica las migraciones y da
# login a `timu_app`, el rol con el que se conecta la API: sin ese paso no puede entrar.
docker compose up -d db redis almacenamiento
docker compose run --rm inicializar
cd backend
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend: el proxy de Vite manda /api a localhost:8000
cd frontend
npm install && npm run dev
```

Desde el host, `backend/.env` necesita `POSTGRES_HOST=localhost` (y `POSTGRES_PORT` si
cambiaste `TIMU_DB_PORT`) y `REDIS_URL=redis://localhost:6379/0`. Sin un worker de Celery,
`/health` responde «degradado» con `workers` en `falla`.

## Pruebas y calidad

```bash
# Backend: contra PostgreSQL de verdad, nunca SQLite
docker compose up -d db-test
cd backend && ruff format --check . && ruff check . && mypy app && pytest

# Frontend: lint + tipos + pruebas con cobertura + build, lo mismo que el CI
cd frontend && npm run verificar
npm run test:e2e         # Playwright con la API interceptada
npm run test:e2e:stack   # recorridos contra el stack real (docker compose up + datos_demo antes)
```

La prueba de carga (k6, con el volumen proyectado a 12 meses) se corre en un proyecto aparte
porque mete datos sintéticos: ver «Prueba de carga» en [`CLAUDE.md`](CLAUDE.md).

El CI (`.github/workflows/ci.yml`) corre todo en cada empuje a `main`, incluido un job que
levanta el stack con un solo comando, recorre panel, portal y clínica aliada contra él, corre
la prueba de carga reducida y respalda y restaura la base comparándola con la de origen.
El release depende de todos los jobs. Las suites fallan si una prueba se salta, queda fuera
de los patrones de los runners o hace una petición que nadie simuló, y si la cobertura baja
del umbral.

## Estructura

```
backend/
  app/
    core/          configuración, base de datos y permisos de la base (RLS), transiciones,
                   auditoría, seguridad, alcance, outbox, límites, salud
    modules/<dominio>/   models.py · schemas.py · service.py · router.py
    api/v1/        router agregador y webhooks (WhatsApp, pagos)
    integrations/  WhatsApp, Wompi, correo, Maps, OR-Tools, S3, Claude
    workers/       celery_app.py (beat_schedule) + tasks/ por dominio
    models.py      registro único de modelos para Alembic
  alembic/         migraciones
  scripts/         inicializar, catálogos, seed, datos_demo, datos_volumen, generar_tipos_frontend
  tests/           pytest contra PostgreSQL (db-test)
frontend/
  src/
    api/           client.ts: el único que habla con la API (cookies, renovación)
    features/      un directorio por dominio, con su api.ts y sus pantallas
    components/    piezas compartidas sin lógica de dominio
    layouts/       AppLayout del panel (portal y clínica aliada tienen el suyo en su feature)
    lib/           errores, permisos, formato, estados y descargas
    routes/        ProtectedRoute (guard por perfil)
    styles/        tokens, base, componentes y vistas del sistema visual
    types/         api.ts, generado desde el OpenAPI del backend
    test/          MSW, utilidades y guardas de la suite
  e2e/             Playwright con la API interceptada
  e2e-stack/       Playwright contra el stack real
infra/respaldos/   respaldo diario de PostgreSQL y restauración verificada
infra/carga/       escenario de k6 de la prueba de carga
```

## Documentación

| Documento | Contenido |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo se escriben los commits, cómo se trabaja sobre `main` y cómo salen las versiones |
| [docs/documento-requerimientos-funcionales.md](docs/documento-requerimientos-funcionales.md) | Lo que TIMU pidió, transcrito literal: los requisitos que citan el código y el backlog (6.10, Sección 8…) |
| [docs/propuesta-timu-puntos-15-19.md](docs/propuesta-timu-puntos-15-19.md) | Contrato funcional: la propuesta que responde a ese documento (secciones A a E) |
| [docs/backlog.md](docs/backlog.md) | Backlog del backend: 105 unidades con criterio de aceptación y estado, por fase |
| [docs/plan-persistencia.md](docs/plan-persistencia.md) | Por qué la base garantiza integridad y permisos: decisiones y registro de cada fase |
| [docs/indicadores.md](docs/indicadores.md) | Definición de cada indicador del dashboard y de los exportables |
| [docs/frontend/](docs/frontend/) | Sistema visual del panel: tokens, componentes, plantillas y convenciones |
| [infra/respaldos/README.md](infra/respaldos/README.md) | Respaldo y restauración de la base |
| `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md` | Reglas de arquitectura para Claude Code; también sirven de guía técnica |
