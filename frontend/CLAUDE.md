# CLAUDE.md — frontend

Reglas del panel (React 18, Vite, React Query). Lo transversal —comandos, stack con un
solo comando, invariante del CI, commits— está en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
Las rutas de este fichero son relativas a `frontend/`.

## Arquitectura

React 18 + Vite, alias `@/` → `src/`. Un directorio por dominio en `src/features/<dominio>/`
con su `api.ts` (React Query), sus pantallas y un `index.ts` con su superficie pública:
**entre dominios solo se importa `@/features/<dominio>`**, dentro de uno, con ruta relativa.
A `src/components/` sube lo que es solo presentación y no conoce ningún dominio. Las capas
(base, `auth` y `catalogos`, dominios, espacios de entrada) y la prohibición de ciclos están
en `docs/frontend/conventions.md` y las vigilan ESLint y `src/test/arquitectura.test.ts`.

Hay tres espacios con su propio layout: el panel del equipo (`AppLayout`, menú según el
perfil), el portal de familias (`/portal`) y el de la clínica aliada (`/aliada`);
`ProtectedRoute` lleva a cada perfil al suyo.

- **`src/api/client.ts` es el único que habla con la API.** Ningún componente arma una
  URL ni usa `fetch`; ESLint lo impide.
- **La sesión vive en una cookie httpOnly + SameSite=lax que pone el backend.** El
  frontend no guarda ni lee tokens: `localStorage` es legible por JavaScript y una XSS
  se llevaría la sesión, con historia clínica de por medio. Por eso el cliente va con
  `withCredentials: true` y `AuthContext` averigua si hay sesión preguntando a
  `/auth/me`. Hay una regla de ESLint que rechaza `localStorage`. Única excepción: el token
  de un solo uso del registro en línea vive en `sessionStorage` (`features/publico/registro.ts`),
  solo en la pestaña que pagó; no abre sesión y deja de valer al completar el registro.
- **Un fallo pasajero nunca cierra la sesión.** Pasajero es sin respuesta, 408, 429 o 5xx
  (`esErrorPasajero` en `src/lib/errores.ts`): no dice nada de la sesión. `AuthContext`
  reintenta `/auth/me` con espera creciente (respeta `Retry-After`) y, si sigue sin
  respuesta, `ProtectedRoute` avisa con «Reintentar» en vez de mandar al ingreso. En
  `src/api/client.ts`, una renovación con fallo pasajero devuelve ese error a la pantalla en
  lugar de redirigir: el límite de renovaciones es por IP y una oficina entera lo comparte.
  Solo una respuesta firme (401, u otro 4xx) termina la sesión.
- **Los componentes interactivos se construyen sobre primitivas de Radix** (diálogo,
  select, tooltip, tabs, toast…). Radix aporta sólo comportamiento —foco atrapado,
  Escape, roles ARIA—; el aspecto sale íntegro de `tokens.css`. `src/components/Modal.tsx`
  es la referencia. No se escribe a mano un componente que Radix ya resuelve.
- **`src/types/api.ts` se genera desde el OpenAPI** (`backend/scripts/generar_tipos_frontend.py`):
  si cambias un schema del backend, se regenera en el mismo cambio. Un `Literal` en el
  schema llega como unión de cadenas y deja que TypeScript rechace valores que la API no
  acepta.
- **Los estilos son CSS propio con cascada de orden fijo**: `tokens → base → componentes →
  vistas`, impuesto por `src/styles/index.css`. Alterar ese orden rompe las vistas.
- **Ningún color, radio o sombra literal en un componente**: todo sale de `tokens.css`.
  `src/test/tokens.test.ts` rechaza un color escrito a mano fuera de ese fichero (también en
  `style={{}}` y en atributos `fill`), un `var(--…)` sin definir y un `z-index` que no sale de
  la escala `--capa-*`. Los radios y las sombras
  los revisa quien empuja (`docs/frontend/conventions.md`, «Qué revisar antes de empujar»).
- Toda lectura va por React Query con clave que incluya los filtros (`['familias', filtros]`)
  y toda pantalla cubre carga, error y vacío.
- **El día de un instante (`2026-11-13T00:30:00Z`) sale de `diaISO` (`lib/formato.ts`)**, en la
  zona de Colombia; `.slice(0, 10)` da el día de UTC. Una fecha de calendario va directa a
  `fecha`/`fechaCorta`.
- **Toda pantalla nueva llega con sus pruebas.** Vitest + Testing Library para
  componentes, con la API simulada por MSW en `src/test/handlers.ts` — nunca con mock
  de axios, para que se pruebe también cómo se arma la petición. Playwright en `e2e/`
  para los recorridos con la API interceptada y en `e2e-stack/` contra el stack real (ver la
  raíz). Se consulta por rol y etiqueta accesible (`getByRole`,
  `getByLabelText`), no por clase CSS: si la prueba no encuentra el control, un lector
  de pantalla tampoco.

## Diseño

La interfaz está en rediseño con la marca real de TIMU: el orden y el estado de cada unidad
están en [`docs/hoja-de-ruta-rediseno.md`](../docs/hoja-de-ruta-rediseno.md).

- **Sorteos de la skill**: `serve-question --wait --key <k>` sale con 3 cada 60 s sin respuesta:
  repítelo en bucle en segundo plano hasta que salga 0. Las capturas para el revisor final siguen
  [`docs/frontend/capturas-revisor.md`](../docs/frontend/capturas-revisor.md).
  `concept-seed --help` no imprime ayuda: ejecuta una tirada. La forma del payload la da
  `serve-question --schema`.
  Una superficie sin sorteo (hereda patrones) escribe igual su contrato, con
  `seed: none (pinned)` y las palabras del usuario que fijan la composición.
- **Color, tipografía, logo y voz**: [`docs/manual-de-marca.md`](../docs/manual-de-marca.md).
  Los componentes usan los roles de su sección 10, nunca un color de la paleta.
- **Decisiones de diseño**: la skill del repositorio, `/impeccable`, con
  [`PRODUCT.md`](../PRODUCT.md) y el sistema de [`DESIGN.md`](../DESIGN.md), que manda en lo
  visual. Su hook revisa cada fichero de interfaz que se edita, y
  cada superficie se cierra con el agente `impeccable-finish-reviewer` hasta su `ship`.
- **Una sola acción verde llena (`btn-primario`) por vista**; las confirmaciones destructivas
  van con `btn-peligro`.
- **Las tablas nuevas usan `tabla-apilable`**, con `data-etiqueta` en cada celda y las acciones
  de fila en `td.tabla-acciones`.
- **GeosansLight (`--fuente-titulos`) solo en `h1` y `h2` de 20 px o más**; uno más pequeño
  vuelve a Inter. El logo es `MarcaTimu` (completo o `compacta`), con la receta de sus SVG en
  `src/assets/marca/README.md`.
- **Para mirar una pantalla**: un script de Playwright desde `frontend/` contra :5173, con el
  ingreso por `request.post('/api/v1/auth/login', { form: { username, password } })` (en JSON da
  422). La renovación rota el token: tras cada contexto, guarda otra vez su `storageState`, o el
  siguiente reusa uno rotado y el backend cierra la sesión. El script vive en el scratchpad y se
  copia a `frontend/` solo para ejecutarlo: `eslint .` lo recoge y `verificar` falla.
  Con una sesión guardada hace más de 30 min, `page.request` da 401: carga antes una pantalla y
  espera a `networkidle` para que se renueve. Un estado que depende de la hora se captura con
  `page.clock.setFixedTime`.
- [`docs/frontend/`](../docs/frontend/) (components, layouts, conventions) describe lo
  construido: qué pieza y qué plantilla reutilizar. `conventions.md` incluye la checklist de revisión y la deuda
  conocida (tema oscuro, PDF sin marca, medidas escritas a mano, tildes del catálogo).

## Trampas conocidas de las pruebas

- La ficha vacía y la abierta de un listado con ficha comparten `aria-label` («Ruta abierta»): espera a un elemento de la ficha (su título), no a la región, o la prueba lee el marcador.
- **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana `base`. Los comunes van en un `beforeEach` y cada prueba los sustituye con su propio `server.use`.
- En jsdom el parser multipart de undici no acepta el `File` de jsdom, y el nombre llega como `blob`: una subida se comprueba leyendo `await request.text()`, no con `request.formData()`.
- Al simular `window.location` con `vi.stubGlobal`, dale el `pathname` de una página pública: si no, el cliente manda a `/login` ante el 401 de `/auth/me` (`PAGINAS_PUBLICAS` en `src/api/client.ts`).
- El proyecto no usa Prettier: no corras `npx prettier`, que descarga uno y reformatea el fichero entero. El formato lo revisa ESLint.
- Vite incrusta como `data:` los recursos de menos de 4 KB: compara el `src` con el import del fichero, no con su nombre.
- Con una ventana de Radix abierta, el `body` lleva `pointer-events: none` y `elementFromPoint` se lo salta: quítalo mientras mides qué hay pintado encima.
- Una regla con `display:` le gana al atributo `hidden`, y jsdom no aplica el CSS: un pliegue que
  no pliega pasa en Vitest. Se prueba en Playwright (`e2e/`) con `toBeHidden()`.
- `moneda()` separa con espacio duro (`$ 225.000`): búscalo con `\s` en la expresión, no con un
  espacio. Si el nombre accesible de un título no casa, compara su `toHaveTextContent`.
- En `e2e/`, `page.route` da prioridad al último registrado: el comodín (`**/api/v1/**`) primero
  y las rutas de la prueba después.
- Un handler de MSW que ignora los parámetros contesta igual a dos consultas de la misma ruta: si
  la pantalla pide dos veces `/servicios` (agenda y `abiertos=true`), las filas salen duplicadas.
- Para congelar la hora sin romper MSW ni userEvent: `vi.useFakeTimers({ toFake: ['Date'] })` y
  `vi.useRealTimers()` en un `finally`.
- `useNombreTipoServicio` devuelve el código («consulta domiciliaria») hasta que llega el
  catálogo: un nombre que lo incluye se busca con `findBy`, no con `getBy`.
- Un bloque nuevo de `vistas.css` insertado antes de `.filtros` o `.listado .filtros > .input`
  pierde contra ellos: sube la especificidad (`.listado .filtros.mi-clase`) o ponlo detrás.
