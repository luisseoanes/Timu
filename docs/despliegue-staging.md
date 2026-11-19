# Despliegue de staging en Railway

Staging es el entorno de pruebas desplegado: el proyecto `timu` del workspace «Luis Seoanes's
Projects» de Railway, entorno `staging`. Lo usa el equipo para ver la plataforma fuera de local, con
los datos de demostración. El entorno `production` del mismo proyecto está vacío: dónde va producción
está por decidir ([costos de infraestructura](costos-infraestructura.md) recomienda Google Cloud).

| Qué | Dónde |
| --- | --- |
| Panel, portal y páginas públicas | <https://web-staging-8bfb.up.railway.app> |
| API (salud) | <https://api-staging-744d.up.railway.app/health> |

## Cómo llega un cambio: autodeploy desde `main`

> **Conectado el 2026-11-19**: Luis instaló la app de GitHub de Railway y conectó los tres
> servicios. Comprobado con `c8ae0ea`: los despliegues esperaron en `WAITING` hasta que el CI salió
> en verde y luego se construyeron solos; con `9a00165`, que solo tocaba `frontend/`, `api` y
> `worker` quedaron en `SKIPPED` por sus *watch patterns*.

Cada servicio con código está conectado al repositorio `luisseoanes/Timu`, rama `main`, con
**«Wait for CI»**: Railway ve el empuje, espera a que el CI de ese commit termine en verde y solo
entonces construye y despliega. Así a staging no llega nada que no haya pasado la batería completa,
igual que el release. Si el CI sale rojo, staging se queda como estaba.

Cada servicio solo se vuelve a desplegar si el empuje toca su carpeta (*watch patterns*): un cambio
del panel no reinicia la API.

| Servicio | Carpeta raíz | Imagen | Arranque | Se despliega si cambia |
| --- | --- | --- | --- | --- |
| `api` | `/backend` | `Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*`, con `python -m scripts.inicializar` antes (*pre-deploy*) y healthcheck en `/health/live` | `/backend/**` |
| `worker` | `/backend` | `Dockerfile` con `REQUIREMENTS=requirements-worker.txt` (OR-Tools) | `celery -A app.workers.celery_app.celery_app worker -B -l info --pool=solo` | `/backend/**` |
| `web` | `/frontend` | `Dockerfile.despliegue`: `npm run build` y Caddy sirve `dist/` | el de la imagen (Caddy, en `PORT`); healthcheck en `/` | `/frontend/**` |
| `Postgres` | — | `ghcr.io/railwayapp-templates/postgres-ssl:18`, con volumen | — | — |
| `Redis` | — | `redis:8.2`, con volumen | — | — |

- **El panel se sirve compilado** (`frontend/Dockerfile.despliegue` y `frontend/Caddyfile`), no con el
  servidor de Vite del compose. Caddy manda `/api/*` a la API por la red privada
  (`API_INTERNA=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:8000`), así que la cookie de sesión es del
  mismo dominio que el panel, como en local. El job «Stack con un solo comando» del CI construye esa
  imagen y comprueba que sirve una ruta del panel y una de la API: un fallo suyo se ve antes de
  desplegar.
- **`beat` no tiene despliegue**: el programador va dentro del `worker` (`-B`, con un solo proceso).
  En staging alcanza; con más de una réplica del worker habría que volver a separarlo.
- **Adjuntos** en el bucket de Railway del proyecto (`STORAGE_*`); `inicializar` comprueba que exista.

La configuración de cada servicio vive en Railway, no en el repositorio (decidido con el usuario el
2026-11-19: Railway retiró `railway.toml`, y la infraestructura como código se deja para cuando se
decida producción). Si se pierde o alguien la cambia en el panel, se rehace con
`railway environment edit` (CLI 5.75 o más reciente), servicio por servicio:

```bash
P=81bb4162-490d-4550-85a3-883a01332605   # proyecto timu
railway environment edit -p $P -e staging \
  -s api source.repo luisseoanes/Timu -s api source.branch main \
  -s api source.rootDirectory /backend -s api source.checkSuites true \
  -s api build.builder DOCKERFILE -s api build.dockerfilePath Dockerfile \
  -s api build.watchPatterns '["/backend/**"]' \
  -m "api desde GitHub con Wait for CI"
# worker: lo mismo con -s worker …; web: rootDirectory /frontend, dockerfilePath
# Dockerfile.despliegue, watchPatterns ["/frontend/**"] y la variable API_INTERNA.
```

Conectar un servicio al repositorio necesita la app de GitHub de Railway instalada en la cuenta
de `luisseoanes` con acceso a `Timu`, y la cuenta de Railway de quien conecta vinculada a GitHub.

## Migraciones: llegan solas, nunca a mano

El *pre-deploy* de `api` corre `python -m scripts.inicializar` antes de arrancar la versión nueva:
`alembic upgrade head`, el rol de la aplicación, los catálogos, el administrador y el bucket. Una
migración que se empuja a `main` llega a staging en el despliegue de ese commit, sin ningún paso
más. Si falla, el despliegue falla y la API anterior sigue sirviendo.

Por eso, desde que existe staging:

- **Una migración se escribe como si hubiera datos reales** ([plan de
  persistencia](registros/plan-persistencia.md)): staging tiene datos que no se regeneran en cada
  arranque, y una migración que solo funciona sobre una base vacía rompe el despliegue.
- **Nunca se aplica una migración a mano en staging** ni se edita una ya empujada: lo que está en
  `main` es lo que hay en la base.
- **Una variable que `Settings` exige en staging** (`OBLIGATORIAS`, `_validar_ambiente`) se pone en
  Railway antes de empujar el cambio que la pide: si no, `inicializar` no arranca y el despliegue
  falla.

## Datos: vaciar y volver a sembrar

Staging lleva los mismos datos de demostración que local: `datos_demo` y `operacion_demo`, que
corren en `local` y en `staging` y se niegan en cualquier otro ambiente. En staging el administrador
entra con `ADMIN_PASSWORD_INICIAL` (variable de `api`), no con la clave de desarrollo; el resto del
equipo de prueba, con `demo12345`, como en local. **Las claves de demostración son públicas**: en
staging no se guarda nada real.

Para empezar de cero (borra todo lo de staging). Hace falta una clave SSH registrada en Railway
(`railway ssh keys add`):

```bash
P=81bb4162-490d-4550-85a3-883a01332605
ssh_api() { railway ssh -p $P -e staging -s api -- "$@"; }
API=https://api-staging-744d.up.railway.app/api/v1
ssh_api python -m scripts.vaciar_staging --confirmar staging   # esquema public y bucket
ssh_api python -m scripts.inicializar                          # migraciones desde la 0001, admin
ssh_api sh -c "DEMO_API=$API python -m scripts.datos_demo"     # ~1 min
ssh_api sh -c "DEMO_API=$API nohup python -m scripts.operacion_demo > /tmp/operacion.log 2>&1 &"
ssh_api tail -n 3 /tmp/operacion.log   # ~5 min, hasta «Listo: … rutas, … visitas…»
```

- **`DEMO_API` va con la URL pública de la API, en HTTPS**: staging tiene `COOKIE_SECURE=true`, y
  contra `http://localhost:8000` el script ingresa pero su cliente no vuelve a mandar la cookie (todo
  da 401).
- **Los planes los crea `datos_demo`**: desplegado, `seed` no los crea (los da de alta
  Administración), y si no hay ninguno el script crea los tres de TIMU por la API, con los valores
  provisionales de `seed.PLANES_TIMU`.
- `operacion_demo` va en segundo plano porque la sesión SSH se corta antes de que termine.
- Las fechas son relativas al día en que se siembra: la ruta de la médica de `datos_demo` cae en el
  primer día con cupo de esa semana, y con los días se queda en el pasado.

## Lo que queda abierto

- **La IP de quien llega**: la API confía en cualquier `X-Forwarded-For` (`--forwarded-allow-ips=*`),
  y su dominio público sigue abierto, así que los límites por IP de ingreso se pueden saltar
  falseando esa cabecera. En staging se acepta; antes de producción, la API deja de tener dominio
  público y solo confía en el proxy del panel.
- **Producción**: el entorno `production` de Railway está vacío y no se despliega desde aquí.
