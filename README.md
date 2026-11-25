# TIMU — Plataforma integral

Plataforma de gestión veterinaria por afiliación descrita en
`docs/propuesta-timu-puntos-15-19.md` (sección 15.C — Tecnología). Arquitectura modular por
dominios: familias, planes, afiliaciones, cartera, servicios, preventivos, clínica, rutas,
comunicaciones, comercial, campañas, encuestas, clínicas aliadas, IA, portal, dashboard e
institucional (los datos de TIMU que dice la portada).

Tres espacios con su propio acceso: el **panel del equipo** (`/panel`: administración,
comercial, operaciones y médicos), el **portal de familias** y el de la **clínica aliada**, y
páginas públicas sin sesión: la **portada** de `timu.com.co` (`/`) con una página por plan, el
registro en línea con pago (`/afiliacion`), las encuestas y la verificación de carnets.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 + FastAPI (async, OpenAPI autogenerado) |
| Frontend | React 18 + TypeScript + Vite + React Query |
| Interfaz | CSS propio sobre tokens ([DESIGN.md](DESIGN.md)), Radix para lo interactivo, Inter y GeosansLight servidas desde el proyecto |
| Base de datos | PostgreSQL 18 (RLS, triggers de integridad y auditoría) + PgBouncer + SQLAlchemy 2 + Alembic |
| Tareas programadas | Celery + Redis (`worker` ejecuta, `beat` programa) |
| Adjuntos | S3 compatible (SeaweedFS en desarrollo), siempre con URL firmada |
| Sesión | Cookies httpOnly: acceso corto y renovación que rota en cada uso |
| WhatsApp | Meta Cloud API oficial, con el número actual de TIMU |
| Pagos | Wompi (webhooks firmados para la conciliación) |
| Correo | Google Workspace de TIMU, por SMTP |
| Rutas | Google OR-Tools + Google Maps Platform |
| IA | Claude hoy (decidido pasar a Gemini), con prompts versionados que se evalúan antes de activarse |
| Infraestructura | Docker / Docker Compose |

## Puesta en marcha

```bash
docker compose up --build
```

Un solo comando: el servicio `inicializar` aplica las migraciones, carga los catálogos,
crea el usuario `admin@timu.co / cambiar123` y el bucket de adjuntos, y solo
entonces arrancan `api`, `worker` y `beat`. No hace falta copiar ningún `.env`:
`backend/.env.example` es la base y `backend/.env`, si existe, la sobrescribe. Las
integraciones externas (WhatsApp, Wompi, Maps, IA, SMTP) se apagan solas mientras sus
variables estén vacías ([integraciones](docs/integraciones.md)).

Si otro proyecto ocupa algún puerto del host, cópialo en la raíz y cámbialo ahí:

```bash
cp .env.example .env   # TIMU_API_PORT, TIMU_DB_PORT, TIMU_S3_PORT…
```

Servicios (puertos por defecto):

- Portada pública: http://localhost:5173 (el panel del equipo, en http://localhost:5173/panel)
- API + Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health (base, Redis y workers)
- Almacenamiento S3 (SeaweedFS): http://localhost:9000
- PgBouncer, el pool por el que la aplicación llega a la base: localhost:6432

Datos de demostración (solo local) y migraciones nuevas con el stack ya arriba:

```bash
docker compose exec api python -m scripts.datos_demo       # lo que piden las pruebas, ~1 min
docker compose exec api python -m scripts.operacion_demo   # ocho semanas de operación, ~5 min
docker compose run --rm inicializar
```

`datos_demo` crea familias, servicios, rutas y campañas, un usuario por perfil del equipo, la
clínica aliada y dos familias con acceso al portal, todos con la clave `demo12345` (la tabla
de usuarios está en [datos de demostración](docs/datos-de-demostracion.md)). Solo crea lo que
falta: no actualiza lo ya sembrado. `operacion_demo`, después, siembra dos meses de historia: cartera en cada estado,
rutas pasadas con sus consultas, preventivos, encuestas, comercial, tareas, remisiones y una
campaña. Qué deja cada uno y cómo ampliarlos: [datos de demostración](docs/datos-de-demostracion.md).

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
porque mete datos sintéticos: ver [docs/prueba-de-carga.md](docs/prueba-de-carga.md).

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
                   auditoría, seguridad, alcance, outbox, límites, salud, marca de los PDF
    recursos/marca/  logo y fuentes de los PDF
    modules/<dominio>/   models.py · schemas.py · service.py · router.py
    api/v1/        router agregador y webhooks (WhatsApp, pagos)
    integrations/  WhatsApp, Wompi, correo, Maps, OR-Tools, S3, Claude
    workers/       celery_app.py (beat_schedule) + tasks/ por dominio
    models.py      registro único de modelos para Alembic
  alembic/         migraciones
  scripts/         inicializar, catálogos, seed, datos_demo, operacion_demo, datos_volumen,
                   generar_tipos_frontend
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
    assets/        logo en SVG y GeosansLight (con la receta para regenerarlos)
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
| [docs/documento-requerimientos-funcionales.md](docs/documento-requerimientos-funcionales.md) | Lo que TIMU pidió, copia literal del PDF y única fuente de verdad: los requisitos que cita el código (6.10, Sección 8…) |
| [docs/propuesta-timu-puntos-15-19.md](docs/propuesta-timu-puntos-15-19.md) | Contrato funcional: la propuesta que responde a ese documento (secciones A a E) |
| [docs/pendiente-en-el-codigo.md](docs/pendiente-en-el-codigo.md) | Lo que falta en el código, con el requisito que lo pide: la lista del trabajo abierto |
| [docs/auditoria-requisitos/](docs/auditoria-requisitos/README.md) | Auditoría de cumplimiento del documento de requerimientos (desde el 2026-11-24): cada obligación con su veredicto y su evidencia, por bloques, y las preguntas para TIMU |
| [docs/pendientes-externos.md](docs/pendientes-externos.md) | Lo que falta fuera del código para cerrar un requisito: sandbox de Wompi, plantillas de Meta, decisiones de TIMU y sus valores provisionales |
| [docs/estandares-calidad.md](docs/estandares-calidad.md) | Cada estándar de calidad pedido (Secciones 3 y 4) traducido a reglas, con la prueba que las hace cumplir y la deuda que queda |
| [docs/integraciones.md](docs/integraciones.md) | Cada servicio externo: qué hace, variables, dónde vive en el código, estado de validación y lo decidido con TIMU |
| [docs/integraciones-timu.md](docs/integraciones-timu.md) | Para la cliente: qué tiene que hacer TIMU en cada integración decidida y las opciones de las que faltan |
| [docs/costos-infraestructura.md](docs/costos-infraestructura.md) | Estimación de costos de tres nubes, integraciones e IA (10 de noviembre de 2026) |
| [docs/prueba-de-carga.md](docs/prueba-de-carga.md) | Cómo correr la prueba de carga con el volumen a 12 meses |
| [docs/despliegue-staging.md](docs/despliegue-staging.md) | Staging en Railway: autodeploy desde `main` con el CI en verde, configuración de cada servicio, migraciones y cómo volver a sembrar |
| [docs/perfiles-y-permisos.md](docs/perfiles-y-permisos.md) | Qué ve y qué hace cada perfil del equipo (Sección 12), en la API, en la base y en el panel |
| [docs/flujo-de-la-visita.md](docs/flujo-de-la-visita.md) | Cómo se atiende una visita en casa: estados de la parada y del servicio, pasos de cada tipo y la consulta como registro |
| [docs/portal-familias.md](docs/portal-familias.md) | Qué ve y qué hace la familia en el portal, de dónde sale cada dato y lo que dice la API para que el panel no copie reglas del backend |
| [docs/portada-publica.md](docs/portada-publica.md) | La portada y la página de cada plan: de dónde sale cada sección (lo que edita Administración), las reglas de la red de aliadas, del contacto a Comercial, las direcciones viejas y lo que falta de TIMU para publicarla |
| [docs/registro-en-linea.md](docs/registro-en-linea.md) | Cómo se afilia una familia sola, de la ciudad al portal: pantallas, rutas de la API, estados, token y plazos, y lo que sigue provisional |
| [docs/indicadores.md](docs/indicadores.md) | Definición de cada indicador del dashboard y de los exportables |
| [docs/datos-de-demostracion.md](docs/datos-de-demostracion.md) | Qué siembran `datos_demo` y `operacion_demo`, cómo se hizo la operación (por la API y corrida al pasado), sus límites y cómo ampliarlos |
| [docs/backend/](docs/backend/) | El detalle de las reglas del backend: [arquitectura](docs/backend/arquitectura.md), [persistencia](docs/backend/persistencia.md) y [pruebas](docs/backend/pruebas.md) |
| [docs/registros/](docs/registros/) | Registros de trabajos cerrados: el [plan de persistencia](docs/registros/plan-persistencia.md) (por qué la base garantiza integridad y permisos) y la [deuda de ciclos entre dominios](docs/registros/deuda-ciclos-dominios.md) |
| [DESIGN.md](DESIGN.md) | Sistema de diseño de la interfaz, escrito desde lo construido: roles de color, tipografía, medidas, componentes y sus reglas |
| [PRODUCT.md](PRODUCT.md) | Contexto de producto para diseñar: quién usa cada espacio, desde qué dispositivo y para qué |
| [docs/manual-de-marca.md](docs/manual-de-marca.md) | Identidad de TIMU (color, tipografía, logo y voz) y su ampliación para la plataforma: roles, contrastes, reglas de uso |
| [docs/hoja-de-ruta-rediseno.md](docs/hoja-de-ruta-rediseno.md) | Rediseño de la interfaz con la marca: unidades, estado, dónde se retoma, decisiones y siguiente paso |
| [docs/rediseno/](docs/rediseno/) | Anexos de la hoja: la [deuda decidida](docs/rediseno/deuda.md), las [notas de cierre](docs/rediseno/notas-de-cierre.md) de cada unidad, la [auditoría y crítica de R4-CIE-02](docs/rediseno/auditoria-r4-cie-02.md), el [inventario de los CLAUDE.md](docs/rediseno/inventario-claude-md.md) y los bocetos de cada superficie |
| [docs/frontend/](docs/frontend/) | Cómo se construye el panel: componentes, plantillas de página, convenciones, las trampas conocidas, la e2e contra el stack y cómo se capturan las pantallas para el revisor final |
| [infra/respaldos/README.md](infra/respaldos/README.md) | Respaldo y restauración de la base |
| `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md` | Reglas para Claude Code, una línea cada una; también sirven de guía técnica, con el detalle en `docs/` |
