# Contribuir a TIMU

Este documento fija **cómo se escriben los commits, cómo llegan a `main` y cómo salen las
versiones**. La
arquitectura y las convenciones de código están en [`CLAUDE.md`](CLAUDE.md) y, para el
panel, en [`docs/frontend/conventions.md`](docs/frontend/conventions.md).

Los commits no son solo historial: **alimentan el release**. `semantic-release` los lee en
cada empuje a `main` y decide con ellos el número de versión y las notas publicadas. Un
mensaje mal formado es trabajo que no aparece en ningún release; un commit que mezcla
cosas es uno que no se puede revertir sin llevarse otra por delante.

---

## 1. Antes de hacer commit

- [ ] El cambio es **uno solo** (ver [§2](#2-qué-va-en-un-commit)). Si al escribir el
      asunto necesitas un «y», probablemente son dos commits.
- [ ] Pasa la batería del lado que toca:
      backend `ruff format . && ruff check . && mypy app && pytest`;
      frontend `npm run verificar`.
- [ ] El stack sigue levantando con **un solo comando** (`docker compose up --build`) desde
      un clon limpio. Es una regla del proyecto, no una recomendación: ver
      *Entorno de desarrollo: un solo comando* en [`CLAUDE.md`](CLAUDE.md).
- [ ] Revisaste `git diff --staged` línea a línea: ni `.env`, ni credenciales, ni trazas
      de depuración, ni ficheros generados (`coverage.xml`, `dist/`, `*.tsbuildinfo`).
- [ ] El mensaje cumple [§3](#3-formato-del-mensaje), incluida la longitud.

No hay ramas ni pull requests: todo se empuja directamente a `main` (ver
[§4](#4-trabajo-directo-sobre-main)). Esta lista es el único control que hay antes de que
el commit llegue a `main`; el CI corre después.

## 2. Qué va en un commit

**Un commit es un cambio lógico, completo y reversible.** Tres consecuencias prácticas:

1. **Se puede revertir solo.** `git revert <sha>` deshace exactamente una cosa y nada más.
2. **Deja el repositorio en verde.** Compila y pasa las pruebas por sí mismo. Así
   `git bisect` sirve para encontrar el commit que introdujo un fallo; un commit roto en
   medio de la historia lo inutiliza.
3. **Se entiende de una vez.** Quien lo lee entiende el porqué sin reconstruirlo a partir
   de otros commits.

### Lo que va siempre junto, en el mismo commit

Separar estas piezas deja un commit intermedio roto o inconsistente:

| Si cambias… | …el mismo commit lleva |
| --- | --- |
| Un modelo de SQLAlchemy | su migración y su registro en `app/models.py` |
| Un schema de Pydantic | el tipo espejo en `frontend/src/types/` |
| Código con comportamiento | las pruebas que lo cubren |
| Una variable de entorno | su entrada en `.env.example` (y en `docker-compose.yml` si aplica) |
| Una dependencia nueva | el código que la usa y el lockfile |
| Un paso de preparación del entorno | su lugar en `backend/scripts/inicializar.py` |

### Lo que va siempre separado

| No mezcles… | Por qué |
| --- | --- |
| Refactor y cambio de comportamiento | El refactor debe poder revisarse sabiendo que no cambia nada observable. |
| Formato masivo o renombrado de ficheros y lógica | El ruido oculta el cambio real y rompe la detección de renombres de git. |
| Actualización de dependencias y funcionalidad | Si la actualización rompe algo, se revierte sin perder la funcionalidad. |
| Dos dominios con cambios independientes | `cartera` y `rutas` se liberan y se revierten por separado. |
| Infraestructura y aplicación que no dependen entre sí | Un cambio en el compose no debería viajar dentro de un `feat(clinica)`. |
| Un arreglo encontrado de paso | Va en su propio `fix`, con su propia explicación. |

### Backend y frontend de una misma funcionalidad

- Si el cambio de la API es **compatible** (añade, no quita), van en dos commits: primero
  el backend (`feat(cartera): …`) y después el panel que lo consume. Cada uno funciona
  por sí solo.
- Si el cambio de la API **rompe** al panel actual, van en un solo commit: separarlos
  dejaría un estado intermedio en el que el panel no funciona.

### Tamaño

No hay un límite de líneas, pero un diff de más de ~400 líneas (sin contar migraciones
autogeneradas ni lockfiles) casi siempre esconde más de un cambio. Pártelo.

Herramientas para conseguirlo sin dolor:

```bash
git add -p                         # elige qué fragmentos van en este commit
git commit --fixup <sha>                  # corrige un commit local aún sin empujar
git rebase -i --autosquash origin/main    # funde los fixup antes de empujar
```

## 3. Formato del mensaje

Seguimos [Conventional Commits 1.0.0](https://www.conventionalcommits.org/es/v1.0.0/):

```
tipo(scope)!: descripción            ← cabecera, obligatoria
                                     ← línea en blanco
Cuerpo: por qué se hace el cambio,   ← opcional (obligatorio en los casos de §3.2)
envuelto a 72 columnas.
                                     ← línea en blanco
Clave: valor                         ← pies, opcionales
```

### 3.1 Cabecera

#### Tipo

| Tipo | Úsalo cuando… | Efecto en la versión |
| --- | --- | --- |
| `feat` | aparece una capacidad nueva para quien usa el sistema | sube la *minor* |
| `fix` | se corrige un comportamiento incorrecto | sube la *patch* |
| `perf` | mejora el rendimiento sin cambiar el comportamiento | sube la *patch* |
| `revert` | se deshace un commit anterior (ver §3.4) | sube la *patch* |
| `refactor` | cambia la estructura del código sin cambiar el comportamiento | no publica |
| `test` | solo se añaden o corrigen pruebas | no publica |
| `docs` | solo documentación | no publica |
| `style` | formato sin efecto en el código (espacios, comas, orden de imports) | no publica |
| `build` | sistema de construcción o dependencias (`requirements*.txt`, `package.json`, Dockerfile) | no publica |
| `ci` | flujos de `.github/` | no publica |
| `chore` | mantenimiento que no encaja en lo anterior (`.gitignore`, datos de demo) | no publica |

Elige por **el efecto**, no por los ficheros tocados. Corregir un Dockerfile que impedía
arrancar el worker es un `fix`, no un `build`: quien lee el changelog necesita saberlo.

#### Scope

Un único scope, en minúscula, que diga **qué parte del sistema** cambia:

| Scope | Cuándo |
| --- | --- |
| Nombre del dominio: `afiliaciones`, `aliadas`, `archivos`, `auth`, `campanas`, `cartera`, `catalogos`, `clinica`, `comercial`, `comunicaciones`, `dashboard`, `encuestas`, `familias`, `ia`, `planes`, `portal`, `preventivos`, `reglas`, `rutas`, `servicios`, `tareas`, `admin`, `publico` | El cambio pertenece a ese dominio, en el backend (`app/modules/<dominio>`), en el panel (`src/features/<dominio>`) o en ambos. Es el caso normal. |
| `backend` / `frontend` | Afecta a toda una capa y no a un dominio: núcleo, middleware, sistema visual, cliente de la API. |
| `infra` | `docker-compose.yml`, Dockerfiles, `infra/`. |
| `deps` | Actualización de dependencias, normalmente con `build`. |
| `release` | Herramientas de publicación (`release.config.js`, `.github/scripts/`). |

- Usa el nombre del directorio tal cual: `clinica`, no `clínica` ni `historia-clinica`.
- Un dominio nuevo amplía esta lista en el mismo commit que lo crea.
- Si el cambio toca varios dominios sin que uno domine, **o se parte o va sin scope**.
  Nunca `feat(cartera,rutas)`: el analizador no lo agrupa.
- Con `docs`, el scope es el área documentada: `docs(frontend)`, `docs(backlog)`.

#### Descripción

- **Empieza en minúscula, con un verbo en presente** que diga qué cambia: «añade»,
  «corrige», «elimina», «permite», «evita». Se lee como una entrada del changelog:
  *Correcciones → **cartera:** corrige el cálculo de mora en meses de 28 días*.
- **Sin punto final.**
- **Dice qué cambia para quien lee el changelog, no cómo se implementó.** «corrige el
  cálculo de mora en meses de 28 días», no «cambia `timedelta` por `relativedelta`».
- Español con su ortografía completa: tildes y eñes incluidas (git y `semantic-release`
  manejan UTF-8 sin problema). Los identificadores de código, entre comillas invertidas.
- Prohibidas por vacías: «cambios», «arreglos», «ajustes varios», «wip», «actualización»,
  «fix», «más cosas».

#### Longitud

- **La cabecera completa (`tipo(scope): descripción`) no pasa de 72 caracteres.** Es el
  ancho que GitHub muestra antes de truncar y el que cabe en `git log --oneline` en una
  terminal estándar.
- Apunta a **50 caracteres o menos**. Si no cabe, suele ser porque el commit hace dos
  cosas, o porque la descripción cuenta el cómo, que va en el cuerpo.

#### Cambios rompientes

Un cambio que obliga a quien usa el sistema a hacer algo (un endpoint que cambia de forma,
una variable de entorno que se renombra, una migración destructiva) se marca **con las dos
cosas**:

1. `!` antes de los dos puntos: `feat(servicios)!: …`
2. Un pie `BREAKING CHANGE:` que explique qué hay que hacer para adaptarse.

### 3.2 Cuerpo

Separado de la cabecera por una línea en blanco y envuelto a **72 columnas**.

**Explica el porqué**: el problema, el contexto, la decisión y lo que se descartó. El
*qué* ya lo cuenta el diff; repetirlo no aporta nada.

Es **obligatorio** en estos casos:

- **`fix`**: el síntoma observable y la causa raíz.
- **Cambio rompiente**: el porqué del cambio. La migración para adaptarse va en el pie.
- **`revert`**: por qué se revierte.
- **Cualquier decisión no evidente**: una dependencia fijada, un caso límite, un atajo
  deliberado.

Para cambios triviales (una errata en la documentación) basta con la cabecera.

### 3.3 Pies

Formato de *trailer* de git: `Clave: valor`, uno por línea, tras una línea en blanco.

| Pie | Uso |
| --- | --- |
| `BREAKING CHANGE: <qué hacer para adaptarse>` | En mayúsculas y exactamente así; el analizador no reconoce variantes. |
| `Refs: #123` | Relaciona el commit con una incidencia sin cerrarla. |
| `Closes: #123` | Cierra la incidencia al llegar a `main`. |

**Ningún commit lleva `Co-Authored-By` de Claude ni de ningún otro asistente de IA, ni
enlace de sesión de Claude** (`Claude-Session: https://claude.ai/…`), ni líneas del tipo
«Generated with…». El historial es del proyecto: el autor es quien firma el commit y
responde por él, y un enlace de sesión no lo puede abrir el resto del equipo. Si una
herramienta los añade por defecto, se quitan antes de hacer el commit.

Cada commit se firma con la identidad real de quien lo hace (`user.name` y `user.email`
de git), nunca con una genérica.

### 3.4 Reversiones

Usa `git revert <sha>` y edita el mensaje que propone:

```
revert: feat(cartera): cobra la cuota con la tarjeta guardada

This reverts commit 3f2a9c1.

La pasarela rechaza los cobros recurrentes sin el token de la
suscripción y deja cuotas en estado intermedio. Se vuelve a
publicar cuando F1-CAR-11 guarde ese token.
```

Conserva la línea `This reverts commit <sha>.`: es la que reconoce el analizador para
enlazar la reversión con el commit original.

### 3.5 Ejemplos

Correctos:

```
feat(cartera): emite la cuota cinco días antes del vencimiento
fix(auth): evita que la cookie de renovación salga de /api/v1/auth
perf(dashboard): cachea los indicadores del día por cinco minutos
refactor(rutas): extrae el cálculo de franjas a su propio servicio
build(deps): actualiza fastapi a 0.115.6
docs(frontend): documenta el componente de tabla paginada
feat(servicios)!: renombra el estado «agendado» a «programado»
```

Con cuerpo y pie:

```
fix(deps): fija kombu para que worker y beat arranquen

celery 5.4 admite cualquier kombu<6 y pip instalaba la 5.7, cuyo
transporte de Redis importa `packaging` sin declararlo como
dependencia: worker y beat morían con ModuleNotFoundError al
arrancar. 5.4.2 es la versión publicada junto a celery 5.4.

Refs: #42
```

Incorrectos:

| Mensaje | Problema |
| --- | --- |
| `Arreglos varios` | Sin tipo; no aparece en ningún release y no dice nada. |
| `fix: cambios` | Descripción vacía. |
| `feat(Cartera): Añade cobro recurrente.` | Scope en mayúscula, descripción en mayúscula, punto final. |
| `feat(cartera,rutas): …` | Dos scopes: hay que partirlo o quitar el scope. |
| `fix(cartera): cambia timedelta por relativedelta en calcular_mora` | Cuenta el cómo, no el efecto. |
| `feat(comercial): embudo de interesados, conversaciones con asesor y campañas con segmentos y encuestas` | Más de 72 caracteres y, por el «y», varios commits en uno. |
| `chore: arregla el worker que no arrancaba` | Es un `fix`: el tipo esconde la corrección del changelog. |

## 4. Trabajo directo sobre `main`

No hay ramas de trabajo ni pull requests: **cada commit se empuja directamente a `main`**.
Eso tiene una consecuencia que conviene tener presente: **nada revisa un commit antes de
que llegue a `main`**. El CI corre después del empuje. Si falla, el commit roto ya está
en la historia y lo verá todo el que haga `pull`. Las reglas de esta sección existen para
compensar eso.

- **Verifica en local antes de empujar**, no después: la lista de [§1](#1-antes-de-hacer-commit)
  completa. No empujes «a ver qué dice el CI».
- **Empuja commits pequeños y a menudo.** Cuanto más tiempo vive un trabajo sin empujar,
  más se aleja de `main` y más difícil es integrarlo. Una funcionalidad grande se parte
  en commits que funcionan por sí solos (ver [§2](#2-qué-va-en-un-commit)), no se
  acumula en local durante días.
- **Trae lo nuevo con rebase, nunca con merge**: `git pull --rebase` (o
  `git config --global pull.rebase true` para que sea el comportamiento por defecto).
  Un `pull` con merge crea commits «Merge branch 'main' of …» que no siguen la
  convención, no los clasifica nadie y rompen la historia lineal.
- **Limpia antes de empujar, nunca después.** Los commits locales se pueden rehacer
  (`--amend`, `fixup` + `rebase --autosquash`) para que a `main` no lleguen «corrige lo
  anterior» ni «wip». Un commit ya empujado no se toca.
- **La historia de `main` no se reescribe**: nada de `push --force`, ni siquiera
  `--force-with-lease`. Otra persona puede haber construido encima.
- **Si un empuje rompe el CI, arreglarlo es lo primero**, antes de seguir con otra cosa.
  Si el arreglo no es inmediato, se revierte con `git revert` (ver
  [§3.4](#34-reversiones)) y se vuelve a empujar el cambio corregido.
- **Una funcionalidad a medio hacer no puede romper lo que ya funciona.** Si tiene que
  llegar a `main` antes de estar completa, va sin enlazar en el menú ni en el router, o
  detrás de una condición que la mantenga apagada.

## 5. Cómo se publican las versiones

### Flujo

1. Cada empuje a `main` ejecuta `.github/workflows/ci.yml` completo: formato, análisis
   estático, tipos, pruebas unitarias, de integración y de extremo a extremo, más el job
   **Stack con un solo comando**. Ese job levanta `docker compose up --build` sin ningún
   `.env`, como un clon recién hecho, y comprueba tres cosas: que `inicializar` termina
   sin errores, que `/health` responde con db, redis y workers en `ok`, y que el
   administrador puede entrar a través del panel.
2. Solo si todo pasa se ejecuta el job **Publicar**. Así no puede salir una versión que
   no haya superado la batería completa ni una con la que el stack no levante.
3. `semantic-release` lee los commits desde el último tag `vX.Y.Z` y aplica **el mayor
   efecto** que encuentre: con un `feat` y diez `fix`, sube la *minor*.
4. Si hay versión nueva, crea el tag `vX.Y.Z` y un *release* de GitHub con las notas
   agrupadas por secciones: Funcionalidades, Correcciones, Rendimiento, Reversiones y
   Refactorizaciones.

Backend y panel **comparten número de versión** y se publican juntos, igual que se
despliegan con docker compose. No se genera `CHANGELOG.md` ni se hace commit de versión:
las notas viven en los *releases* de GitHub.

### Qué mueve la versión

| Commits desde el último tag | Versión |
| --- | --- |
| Algún cambio rompiente (`!` o `BREAKING CHANGE`) | *major* (*minor* mientras estemos en 0.x, ver abajo) |
| Algún `feat` | *minor* |
| Algún `fix`, `perf` o `revert` | *patch* |
| Solo `refactor`, `test`, `docs`, `style`, `build`, `ci` o `chore` | ninguna |

Los `refactor` aparecen en las notas, pero no publican versión por sí solos: salen en el
siguiente release que sí la publique.

### Mientras la versión sea 0.x

`release.config.js` tiene la regla `{ breaking: true, release: 'minor' }` para que un
cambio rompiente no dispare el salto a 1.0.0 antes de tiempo. **Al publicar la 1.0.0 hay
que borrar esa línea**: si se queda, un cambio rompiente daría 1.1.0 en lugar de 2.0.0.

### Comprobar los mensajes antes de empujar

El CI revisa la convención **justo antes de publicar**, cuando el commit ya está en
`main`, y solo avisa: un commit mal formado no rompe el build, simplemente desaparece del
release, y para entonces ya no se puede corregir sin reescribir `main`. Por eso se revisan
en local, con los commits que aún no has empujado:

```bash
git fetch && node .github/scripts/commits-sin-convencion.mjs origin/main..HEAD
```

El script comprueba la forma de la cabecera y el tipo. El scope y la longitud no los
valida, y como no hay revisión de pull request, nadie más los va a mirar: dependen solo
de quien escribe el commit.
