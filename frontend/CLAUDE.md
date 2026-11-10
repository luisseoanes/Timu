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
- **Ningún color, radio o sombra literal en un componente**: todo sale de `tokens.css`. Un
  `#` en el diff de un componente no debe llegar a `main`: ningún lint lo detecta, así que lo
  comprueba quien empuja (`docs/frontend/conventions.md`, «Qué revisar antes de empujar»).
- Toda lectura va por React Query con clave que incluya los filtros (`['familias', filtros]`)
  y toda pantalla cubre carga, error y vacío.
- **Toda pantalla nueva llega con sus pruebas.** Vitest + Testing Library para
  componentes, con la API simulada por MSW en `src/test/handlers.ts` — nunca con mock
  de axios, para que se pruebe también cómo se arma la petición. Playwright en `e2e/`
  para los recorridos con la API interceptada y en `e2e-stack/` contra el stack real (ver la
  raíz). Se consulta por rol y etiqueta accesible (`getByRole`,
  `getByLabelText`), no por clase CSS: si la prueba no encuentra el control, un lector
  de pantalla tampoco.

[`docs/frontend/`](../docs/frontend/) (design-system, components, layouts, conventions) es normativo para
cualquier pantalla nueva: léelo antes de escribir UI. `conventions.md` incluye la checklist
de revisión y la deuda conocida (sin tema oscuro).

## Trampas conocidas de las pruebas

- **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana `base`. Los comunes van en un `beforeEach` y cada prueba los sustituye con su propio `server.use`.
- En jsdom el parser multipart de undici no acepta el `File` de jsdom, y el nombre llega como `blob`: una subida se comprueba leyendo `await request.text()`, no con `request.formData()`.
