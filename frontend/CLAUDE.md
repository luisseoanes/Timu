# CLAUDE.md — frontend

Reglas del panel (React 18, Vite, React Query), una línea cada una. Lo transversal (comandos, stack
con un solo comando, invariante del CI, commits) está en el [`CLAUDE.md` de la raíz](../CLAUDE.md); el
detalle, en [`docs/frontend/`](../docs/frontend/): [convenciones](../docs/frontend/conventions.md)
(capas, datos, sesión, permisos, pruebas, accesibilidad, tokens y la lista de revisión),
[componentes](../docs/frontend/components.md), [plantillas](../docs/frontend/layouts.md) y
[trampas](../docs/frontend/trampas.md). Las rutas son relativas a `frontend/`.

## Arquitectura

Alias `@/` → `src/`. Un directorio por dominio en `src/features/<dominio>/`, con su `api.ts` (React
Query), sus pantallas y un `index.ts` con su superficie pública. Tres espacios con sesión y su layout:
el panel del equipo en `/panel` (`AppLayout`, menú según el perfil), el portal de familias (`/portal`) y
la clínica aliada (`/aliada`); y la web pública sin sesión: la portada (`/`) y cada plan
(`/planes/<plan>`) con `MarcoPublico`, y el registro, la encuesta y el carnet con sus marcos.
`ProtectedRoute` lleva a cada perfil al suyo.

- **Entre dominios solo se importa `@/features/<dominio>`**; dentro de uno, con ruta relativa. A
  `src/components/` sube lo que es solo presentación y no conoce ningún dominio. Las capas (base,
  `auth` y `catalogos`, dominios, espacios de entrada) y la prohibición de ciclos las vigilan ESLint y
  `src/test/arquitectura.test.ts`.
- **`src/api/client.ts` es el único que habla con la API**: ningún componente arma una URL ni usa
  `fetch` (ESLint lo impide).
- **La sesión vive en una cookie httpOnly + SameSite=lax que pone el backend**: el frontend no guarda
  ni lee tokens (una XSS se llevaría la sesión, con historia clínica de por medio). El cliente va con
  `withCredentials: true`, `AuthContext` pregunta a `/auth/me` y ESLint rechaza `localStorage`. Única
  excepción: el token de un solo uso del registro en línea, en `sessionStorage`
  (`features/publico/registro.ts`), solo en la pestaña que pagó; no abre sesión y deja de valer al
  completar el registro.
- **Un fallo pasajero nunca cierra la sesión.** Sin respuesta, 408, 429 o 5xx (`esErrorPasajero`,
  `src/lib/errores.ts`) no dicen nada de la sesión: `AuthContext` reintenta `/auth/me` con espera
  creciente (respeta `Retry-After`) y, si sigue sin respuesta, `ProtectedRoute` avisa con «Reintentar»;
  una renovación con fallo pasajero devuelve el error a la pantalla en vez de redirigir (el límite de
  renovaciones es por IP y una oficina entera lo comparte). Solo un 401 u otro 4xx terminan la sesión.
- **Lo interactivo se construye sobre Radix** (diálogo, select, tooltip, tabs, toast…), que pone el
  comportamiento (foco atrapado, Escape, roles ARIA); el aspecto sale íntegro de `tokens.css`.
  `src/components/Modal.tsx` es la referencia. No se escribe a mano lo que Radix ya resuelve.
- **`src/types/api.ts` se genera desde el OpenAPI** (`backend/scripts/generar_tipos_frontend.py`) en
  el mismo cambio del schema; un `Literal` llega como unión de cadenas y TypeScript rechaza los
  valores que la API no acepta.
- **Una página nueva en `App.tsx` va con `perezosa(<módulo>, '<Página>')`**, nunca con un import
  estático: el paquete principal (públicas e ingreso) ronda los 500 kB y cada módulo es su trozo.
- **Cascada de orden fijo** `tokens → base → componentes → vistas`, impuesta por
  `src/styles/index.css`: alterarla rompe las vistas.
- **Ningún color, radio, sombra ni `z-index` literal**: todo sale de `tokens.css`, y
  `src/test/tokens.test.ts` lo vigila (las sombras, no: se revisan en el diff).
- **Toda lectura va por React Query** con una clave que incluye los filtros (`['familias', filtros]`),
  y toda pantalla cubre carga, error y vacío.
- **El día de un instante (`2026-11-13T00:30:00Z`) sale de `diaISO`** (`lib/formato.ts`), en la zona
  de Colombia; `.slice(0, 10)` da el de UTC. Una fecha de calendario va directa a `fecha`/`fechaCorta`.
- **Toda pantalla nueva llega con sus pruebas**: Vitest + Testing Library con la API simulada por MSW
  (`src/test/handlers.ts`), nunca con mock de axios, para probar también cómo se arma la petición; y
  Playwright en `e2e/` (API interceptada) y `e2e-stack/` (stack real). Se consulta por rol y etiqueta
  accesible (`getByRole`, `getByLabelText`), no por clase: si la prueba no encuentra el control, un
  lector de pantalla tampoco.

## Diseño

Todas las pantallas están rediseñadas con la marca real de TIMU
([hoja de ruta](../docs/hoja-de-ruta-rediseno.md)). Lo visual lo gobierna la skill `/impeccable` con
[`PRODUCT.md`](../PRODUCT.md) y [`DESIGN.md`](../DESIGN.md), que manda en lo visual; color,
tipografía, logo y voz, en el [manual de marca](../docs/manual-de-marca.md), cuyos roles (sección 10)
son lo único que usan los componentes, nunca un color de la paleta.

- **El hook de la skill revisa cada fichero de interfaz editado con Edit/Write**, no uno copiado o
  generado con un script: ese se le pasa a mano (`echo '{"tool_name":"Write","tool_input":{"file_path":"<ruta>"}}' |
  .claude/skills/impeccable/scripts/impeccable hook`). Si no devuelve nada (ni siquiera «No
  deterministic…»), el detector a mano: `.claude/skills/impeccable/scripts/impeccable detect --json <fichero>`.
- **Una superficie se cierra con el agente `impeccable-finish-reviewer` hasta su `ship`**; las capturas
  que necesita, y cómo mirar cualquier pantalla con Playwright contra :5173 (sesiones, cupos, hora e
  idioma), en [`capturas-revisor.md`](../docs/frontend/capturas-revisor.md).
- **Sorteos de la skill**: `serve-question --wait --key <k>` sale con 3 cada 60 s sin respuesta:
  repítelo en bucle en segundo plano hasta que salga 0. `concept-seed --help` no imprime ayuda: ejecuta
  una tirada. La forma del payload la da `serve-question --schema`.
- **Toda superficie escribe su contrato**, también sin sorteo (hereda patrones: `seed: none (pinned)` y
  las palabras del usuario que fijan la composición), con `.claude/skills/impeccable/scripts/impeccable
  surface-brief write <Pantalla.tsx> <contrato.md> [ficheros…]`, que lo deja en `.impeccable/surfaces/`.
- **Una sola acción verde llena (`btn-primario`) por vista**; las confirmaciones destructivas, con
  `btn-peligro`.
- **Las tablas nuevas usan `tabla-apilable`**, con `data-etiqueta` en cada celda y las acciones de fila
  en `td.tabla-acciones`.
- **El título de una tarjeta de primer nivel es un `h2` en `.tarjeta-cabeza`** (Inter, no GeosansLight)
  y sus apartados, `h3`: el barrido falla si los encabezados saltan un nivel.
- **GeosansLight (`--fuente-titulos`) solo en `h1` y `h2` de 20 px o más**; uno más pequeño vuelve a
  Inter. El logo es `MarcaTimu` (completo o `compacta`), con la receta de sus SVG en
  `src/assets/marca/README.md`.

## Trampas que más se tropiezan

Todas, en [`docs/frontend/trampas.md`](../docs/frontend/trampas.md); una nueva se añade allí.

- **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana `base`. Los
  comunes van en un `beforeEach` y cada prueba los sustituye con su propio `server.use`.
- «Peticiones sin handler» que no son de la prueba eran de la anterior: `setup.ts` ya espera la red al
  cerrar (tope de 2 s); una consulta que se dispara más tarde se simula en la prueba que la provoca.
- Con una ventana de Radix abierta, el resto de la página queda oculto a los lectores de pantalla y
  `findByRole` no lo encuentra hasta que se cierra.
- `npx eslint`, `npx tsc` o `npx vitest` desde la raíz del repositorio descargan otra versión y fallan:
  se corren desde `frontend/`. Tampoco `npx prettier`: el proyecto no lo usa.
- Con la máquina cargada (`uptime` alto), `verificar` agota los tiempos de Vitest: confirma una falla
  con `npx vitest run --coverage --maxWorkers=2` antes de darla por buena.
- `npm run test:e2e` sirve `dist/` con `vite preview` y no recompila: tras cambiar el panel,
  `npx vite build` antes. Y dos Playwright a la vez se pisan (`test:e2e` y `test:e2e:stack`, uno detrás
  de otro).
- Una regla con `display:` le gana al atributo `hidden`, y jsdom no aplica el CSS: un pliegue que no
  pliega pasa en Vitest. Se prueba en `e2e/` con `toBeHidden()`.
- `e2e/` no lo revisa `tsc`: al cambiar un schema, sus datos simulados de la API se revisan a mano.
- Una página pública nueva va en `PAGINAS_PUBLICAS` (`src/api/client.ts`): si no, un 401 la manda a
  `/login`.
- `verificar` muestra un aviso previo de ESLint en `AuthContext.tsx`
  (`react-refresh/only-export-components`): no es de tu cambio.
