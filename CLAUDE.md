# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repositorio

Scaffold de TIMU, plataforma de gestión veterinaria por afiliación. El contrato funcional
vive en `docs/Propuesta_TIMU_Puntos_15-19.docx` y el desglose ejecutable en
`docs/BACKLOG.md` (101 unidades con ID `fase-módulo-consecutivo`, p. ej. `F1-CAR-08`).

Los comentarios del código citan requisitos por número (`6.10`, `6.16`, `sección C`): son
referencias a ese documento. Al implementar un módulo pendiente, busca su ID en el backlog
y respeta el criterio de aceptación que ya está escrito allí.

## Comandos

```bash
# Todo el stack (api, worker, beat, db, redis, web)
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py     # admin@timu.co / cambiar123

# Backend sin Docker
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest                              # suite completa (SQLite en memoria)
pytest tests/test_familias.py::test_crear_y_listar_familia   # una sola prueba
ruff check . && ruff format .
mypy app

# Frontend
cd frontend && npm install
npm run dev                         # 5173, con proxy /api → localhost:8000
npm run typecheck                   # tsc --noEmit
npm run build
```

`npm run lint` está declarado en `package.json` pero **no hay configuración de ESLint** en
el repositorio; el comando falla. Usa `npm run typecheck` como puerta de calidad del
frontend hasta que se añada `eslint.config.js`.

## Arquitectura del backend

Un directorio por dominio en `app/modules/<dominio>/`, con hasta cuatro piezas:
`models.py` (SQLAlchemy) · `schemas.py` (Pydantic) · `service.py` (lógica y consultas) ·
`router.py` (HTTP). `app/modules/familias/` es la referencia completa del patrón; el resto
de dominios tiene modelos definidos y un router placeholder que devuelve
`Mensaje(detail="Modulo X: pendiente de implementar")`.

Reglas que atraviesan todo el backend:

- **`app/models.py` es el registro único de modelos.** Alembic (`autogenerate`) y los tests
  (`create_all`) sólo ven lo importado ahí. Un modelo nuevo que no se añada a ese fichero
  no existe para las migraciones ni para las pruebas.
- **`alembic/versions/` está vacío.** No hay migración inicial todavía (`F0-01`); un
  `alembic upgrade head` contra base limpia no crea nada. La primera migración hay que
  generarla con `alembic revision --autogenerate`.
- **La transacción la cierra `get_db`**, no los servicios. Las funciones de `service.py`
  hacen `flush()` para obtener IDs; el commit ocurre al terminar la petición, y el rollback
  ante cualquier excepción. No metas `commit()` en un servicio.
- **Autorización con `require_roles`** de `app/core/deps.py`:
  `dependencies=[Depends(require_roles(Rol.ADMIN))]`. Los alias `DbSession` y `CurrentUser`
  son los que se inyectan en los endpoints; un endpoint sin `CurrentUser` queda público.
- **Enums de dominio en `app/core/enums.py`**, no en cada módulo. Son `StrEnum` y viajan
  como cadenas en la API.
- **Los estados de servicio pasan por `app/modules/servicios/state_machine.py`.** Rutas,
  portal y comunicaciones deben llamar a `transicionar()`; ningún módulo reimplementa el
  grafo de transiciones ni asigna un estado a mano.
- **Los listados devuelven `Page[T]`** de `app/schemas/common.py` (`items`, `total`,
  `limit`, `offset`), con filtros combinables como en `familias.service.listar`.

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

- **`src/api/client.ts` es el único que habla con la API.** Inyecta el JWT desde
  `localStorage` y ante un 401 limpia el token y vuelve a `/login`. Ningún componente arma
  una URL ni usa `fetch`.
- **`src/types/` es el espejo tipado de los schemas de Pydantic.** Si cambias un schema del
  backend, actualiza el tipo en el mismo cambio.
- **Los estilos son CSS propio con cascada de orden fijo**: `tokens → base → componentes →
  vistas`, impuesto por `src/styles/index.css`. Alterar ese orden rompe las vistas.
- **Ningún color, radio o sombra literal en un componente**: todo sale de `tokens.css`. Un
  `#` en el diff de un componente es un rechazo en revisión.
- Toda lectura va por React Query con clave que incluya los filtros (`['familias', filtros]`)
  y toda pantalla cubre carga, error y vacío.

`docs/frontend/` (DESIGN-SYSTEM, COMPONENTS, LAYOUTS, CONVENTIONS) es normativo para
cualquier pantalla nueva: léelo antes de escribir UI. `CONVENTIONS.md` incluye la checklist
de revisión y la deuda conocida (sin tema oscuro, sin librería de componentes, datos de
ejemplo en el panel de inicio hasta `F4-DAS-02`).

## Convenciones de escritura

Todo el repositorio está en español: identificadores de dominio (`familias`, `mascotas`,
`cartera`), clases CSS en singular (`.tarjeta`, `.distintivo-alerta`), docstrings, mensajes
de error de la API y commits (`feat(backend): …`). El código del backend evita tildes en
docstrings y comentarios; el frontend y la documentación sí las usan. Sigue lo que ya haga
cada fichero.
