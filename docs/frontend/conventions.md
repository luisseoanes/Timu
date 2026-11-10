# Convenciones del frontend

## Estructura por dominio

Cada dominio de la plataforma es una carpeta en `src/features/` con lo suyo dentro:

```
features/familias/
  index.ts                 Superficie pública: lo único que otros dominios importan
  api.ts                   Consultas y mutaciones con React Query
  FamiliasPage.tsx         Pantalla
  FamiliasPage.test.tsx    Sus pruebas, al lado de lo que prueban
  <Componente>.tsx         Piezas del dominio
```

### Qué puede importar cada cosa

- **Dentro de un dominio**, con ruta relativa (`./api`).
- **De otro dominio**, solo lo que exporta su `index.ts`: `import { useFamilia } from
  '@/features/familias'`. Para usar algo que no está, se añade al `index.ts` de su dominio;
  nunca `@/features/familias/api` (ESLint lo rechaza) ni `../familias/api`.
- **Los datos de otro dominio se consumen con sus hooks**, no se copian: `useFamilia` desde
  clínica o servicios comparte la caché de React Query porque es la misma clave. Un widget de
  dominio que otros reutilizan (`SelectorFamilia`) también se queda en su dominio y se
  exporta.
- **A `src/components/` sube lo que es solo presentación** y no sabe de ningún dominio
  (`Modal`, `Icono`, `MarcaTimu`). Nada de una carpeta `common/` que termine siendo un cajón
  de sastre.
- Cada pieza vive en el dominio de lo que consulta: `useMascotas` (`/mascotas`) en
  `familias`, `useEquipo` (`/auth/equipo`) en `auth`.

Capas, de abajo arriba; cada una solo usa las anteriores:

| Capa | Qué | No puede importar |
| --- | --- | --- |
| Base | `src/api`, `src/components`, `src/lib`, `src/types`, `src/styles` | ningún dominio |
| Dominios base | `auth` (sesión, equipo) y `catalogos` | otro dominio |
| Dominios | el resto de `src/features/` | `admin`, `portal`, `publico`; ni cerrar un ciclo |
| Espacios de entrada | `admin`, `portal`, `publico` | — (solo los monta `App.tsx`) |
| Composición | `App.tsx`, `main.tsx`, `layouts/`, `routes/`, `test/` | — |

`src/test/arquitectura.test.ts` hace fallar la suite si algo de esto se incumple, también
por rutas relativas que ESLint no ve.

## Nombres

- Componentes y archivos de componente en `PascalCase`; el resto en `camelCase`.
- Clases CSS en español y en singular: `.tarjeta`, `.distintivo`, `.fila`. Los modificadores
  van con guion: `.distintivo-alerta`.
- Los tipos son el espejo de los schemas del backend y viven en `src/types/`. Si cambia un
  schema de Pydantic, se cambia aquí en el mismo cambio de código.

## Datos

- Toda lectura pasa por React Query con una clave que incluya los filtros:
  `['familias', filtros]`. Nada de `useEffect` con `fetch` a mano.
- Toda escritura invalida las claves que afecta en `onSuccess`.
- El cliente de axios de `src/api/client.ts` es el único que habla con la API: agrega el
  token y devuelve al ingreso cuando la sesión expira. Ningún componente arma una URL.
- Las tres pantallas obligatorias de cualquier consulta son cargando, error y vacío.

## Componentes interactivos

Todo lo que tenga comportamiento —diálogos, selects, tooltips, pestañas, avisos— se
construye sobre **primitivas de Radix**. Radix pone sólo el comportamiento: foco
atrapado, cierre con Escape, roles ARIA, navegación con teclado. El aspecto sigue
saliendo entero de `tokens.css`, así que el sistema visual no cambia. `Modal.tsx` es la
referencia. No se escribe a mano un componente que Radix ya resuelve: sale más caro y
sale peor en accesibilidad.

## Sesión

La sesión vive en una **cookie httpOnly con SameSite=lax** que pone el backend al
ingresar. El frontend no guarda ni lee tokens, y hay una regla de ESLint que rechaza
`localStorage`: es legible desde JavaScript y una XSS se llevaría la sesión, con
historia clínica de por medio. Para saber si hay sesión se pregunta a `/auth/me`.
Única excepción: el token de un solo uso del registro en línea vive en `sessionStorage`
(`features/publico/registro.ts`), solo en la pestaña que pagó. No abre sesión y deja de valer
al completar el registro; si falta (otra pestaña u otro equipo), la familia usa el enlace que
le llega por correo y WhatsApp.

**Un fallo pasajero nunca cierra la sesión.** Sin respuesta, 408, 429 o 5xx
(`esErrorPasajero` en `src/lib/errores.ts`) no dicen nada de la sesión: `AuthContext`
reintenta con espera creciente y, si el servidor sigue sin contestar, `ProtectedRoute`
muestra un aviso con «Reintentar» en vez de mandar al ingreso. Una renovación con fallo
pasajero llega a la pantalla como un error más. Solo una respuesta firme (401 u otro 4xx)
termina la sesión. Una pantalla que trate cualquier error como «sin sesión» saca a la
gente de su trabajo por un pico de carga.

## Permisos

`ProtectedRoute` acepta la lista de perfiles que pueden entrar. El frontend esconde lo que
el usuario no puede hacer, pero **eso no es seguridad**: la autorización real la impone el
backend en cada endpoint, con `require_roles` para el perfil y `restringir()` para las
filas. Un botón oculto sin permiso en el servidor es un defecto.

## Pruebas

Toda pantalla nueva llega con las suyas. No es una aspiración: el CI las ejecuta todas en
cada push, falla si alguna está desactivada o fuera de los patrones (`src/test/suite.test.ts`)
y exige los umbrales de cobertura de `vitest.config.ts` (ver la invariante del CI en el
`CLAUDE.md` de la raíz).

- **Componentes**: Vitest + Testing Library. La API se simula con **MSW**
  (`src/test/handlers.ts`), a nivel de red y nunca haciendo mock de axios, para que se
  pruebe también cómo se arma la petición. **Una petición sin handler hace fallar la
  prueba** (`src/test/setup.ts`): lo que cargan todas las pantallas (catálogos, equipo,
  planes) va en `src/test/handlers.ts`.
- **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana
  `base`. Los handlers comunes de un fichero van en un `beforeEach` y cada prueba los
  sustituye con su propio `server.use`.
- **Recorridos**: Playwright en `e2e/` sobre la aplicación compilada y con la API
  interceptada, y en `e2e-stack/` contra el stack real con los usuarios de `datos_demo`.
  Un fallo de contrato entre panel y API (un valor que la API rechaza) solo lo detecta el
  segundo.
- Se consulta por **rol y etiqueta accesible** (`getByRole`, `getByLabelText`), jamás por
  clase CSS. Si la prueba no encuentra el control, un lector de pantalla tampoco: la
  prueba es también una comprobación de accesibilidad.
- Las tres pantallas obligatorias de una consulta —cargando, error y vacío— tienen que
  estar cubiertas por pruebas, no sólo escritas.

## Textos

Se escriben desde el lado de quien usa el sistema: *Familias*, no *Registros de titular*;
*Cerrar sesión*, no *Logout*. Voz activa, español de Colombia, sin jerga técnica en la
interfaz. Los mensajes de error dicen qué pasó y qué hacer. Los botones nombran su
resultado.

## Accesibilidad

- Todo control alcanzable con teclado y con foco visible: el sistema ya define
  `:focus-visible` en verde; no se elimina el contorno.
- Un botón que sólo tenga icono lleva `aria-label`; los iconos son `aria-hidden`.
- El estado nunca se comunica sólo con color: el distintivo lleva texto además del tono.
- Los campos siempre tienen etiqueta visible asociada.
- Con `prefers-reduced-motion` se desactivan transiciones y animaciones (ya está en
  `base.css`).

## Qué revisar antes de empujar

1. ¿La pantalla usa sólo tokens? Los colores escritos a mano y las variables sin definir los
   rechaza `src/test/tokens.test.ts`. Los radios y las sombras se revisan en el diff.
2. ¿Reutiliza los componentes existentes en vez de crear una variante casi igual?
3. ¿Lo interactivo se apoya en Radix en vez de reimplementarlo a mano?
4. ¿Tiene los estados de carga, error y vacío, **y pruebas de los tres**?
5. ¿Se ve bien a 1440, 1180 y 900 px de ancho?
6. ¿Los textos están en español, en voz activa y sin jerga?
7. ¿`npm run verificar` pasa? (lint + tipos + cobertura + build, lo mismo que el CI)

## Deuda conocida

- **Sin tema oscuro.** Decisión de producto; los tokens están listos para agregarlo.
