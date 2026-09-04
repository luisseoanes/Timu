# TIMU — Plataforma integral

Scaffold del proyecto descrito en `docs/propuesta-timu-puntos-15-19.md`
(sección 15.C — Tecnología). Arquitectura modular por dominios: familias, cartera,
planes, servicios, preventivos, clínica, rutas, comunicaciones, campañas, encuestas,
clínicas aliadas, portal y dashboard.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 + FastAPI (async, OpenAPI autogenerado) |
| Frontend | React 18 + TypeScript + Vite |
| Base de datos | PostgreSQL 16 + SQLAlchemy 2 (async) + Alembic |
| Tareas programadas | Celery + Redis (beat para recordatorios y calendario preventivo) |
| WhatsApp | Meta Cloud API oficial |
| Pagos | Wompi / PayU (webhooks para conciliación) |
| Rutas | Google OR-Tools + Google Maps Platform |
| Infraestructura | Docker / Docker Compose |

## Puesta en marcha

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Servicios:

- API + Swagger: http://localhost:8000/docs
- Panel operativo: http://localhost:5173
- Health check: http://localhost:8000/health

Migraciones y datos iniciales:

```bash
docker compose exec api alembic revision --autogenerate -m "esquema inicial"
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py   # admin@timu.co / cambiar123
```

## Desarrollo sin Docker

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev
```

## Estructura

```
backend/
  app/
    core/          config, base de datos, seguridad, enums, dependencias
    modules/<dominio>/   models.py · schemas.py · service.py · router.py
    api/v1/        router agregador y webhooks (WhatsApp, pagos)
    integrations/  whatsapp.py · payments.py · routing.py (OR-Tools)
    workers/       celery_app.py + tasks/ (cartera, preventivos, comunicaciones, encuestas)
    models.py      registro único de modelos para Alembic
  alembic/         migraciones
  tests/           pytest + httpx (SQLite en memoria)
frontend/
  src/
    api/           cliente axios con JWT e interceptores
    styles/        tokens, base, componentes y vistas del sistema visual
    components/    piezas compartidas sin lógica de dominio
    features/      auth, familias, dashboard, … (un directorio por dominio)
    layouts/       AppLayout (barra lateral y cabecera)
    routes/        ProtectedRoute (guard por rol)
    types/         espejo tipado de los schemas del backend
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/backlog.md](docs/backlog.md) | Backlog completo del backend: 101 unidades con criterio de aceptación, por fase |
| [docs/frontend/](docs/frontend/) | Sistema visual del panel: tokens, componentes, plantillas y convenciones |

## Estado del scaffold

Implementado y funcional:

- Autenticación JWT con roles (admin, comercial, operaciones, médico, familia).
- Módulo de familias/mascotas completo: CRUD, filtros combinables (6.16), paginación.
- Modelos de datos de los 14 dominios, con las relaciones de la sección 6.
- Máquina de estados de servicios (6.10) con transiciones validadas y pruebas.
- Webhooks de WhatsApp (handshake de verificación) y de pagos (firma validada).
- Clientes de integración: Meta Cloud API, pasarela de pagos, optimización de rutas.
- Celery beat con los cuatro jobs recurrentes de la propuesta.

Pendiente por fase (routers con placeholder, modelos ya definidos): cartera, planes,
servicios, preventivos, clínica, rutas, comunicaciones, campañas, encuestas, aliadas,
portal de familias y dashboard.

## Pruebas y calidad

```bash
cd backend && pytest && ruff check .
cd frontend && npm run typecheck
```
