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
  `:focus-visible` con el color de foco (`--foco`, azul); no se elimina el contorno.
- Un botón que sólo tenga icono lleva `aria-label`; los iconos son `aria-hidden`.
- El estado nunca se comunica sólo con color: la insignia lleva icono y texto además del tono,
  y lo vencido de una fila se dice en texto («3 vencidas»), no solo con un punto rojo.
- Los campos siempre tienen etiqueta visible asociada.
- Con `prefers-reduced-motion` se desactivan transiciones y animaciones (ya está en
  `base.css`).

## Tokens y su guarda

[`tokens.css`](../../frontend/src/styles/tokens.css) es la única fuente de las medidas y los
colores, en tres capas: la **paleta** (solo se nombra dentro de ese fichero), los **roles**
(lo único que usan los componentes: `--texto`, `--accion-fondo`, `--estado-alerta-texto`…) y
el bloque **`@pares`**, con cada combinación de texto o control sobre su fondo y su contraste
mínimo. Lo que significa cada rol y cada medida está en [`DESIGN.md`](../../DESIGN.md) y en el
[manual de marca](../manual-de-marca.md) (secciones 9 y 10).

[`src/test/tokens.test.ts`](../../frontend/src/test/tokens.test.ts) hace fallar la suite si un
componente escribe un color a mano (también en `style={{}}` y en atributos SVG), usa un color
de la paleta en vez de un rol, usa una variable que no está definida, si un par no llega a su
mínimo, si un rol de texto o de control no tiene ningún par declarado, o si un `z-index` no
sale de la escala `--capa-*`. **Un rol nuevo llega con su par.** Los radios y las sombras no los
vigila la guarda: se revisan en el diff. Los `.svg` tampoco: sus colores son el activo de la
marca, no colores de la interfaz.

## Qué revisar antes de empujar

1. ¿La pantalla usa sólo tokens? Lo que no vigila la guarda (radios, sombras) se revisa en el
   diff.
2. ¿Reutiliza los componentes existentes ([components.md](components.md)) y la plantilla de
   su tipo ([layouts.md](layouts.md)) en vez de crear una variante casi igual?
3. ¿Lo interactivo se apoya en Radix en vez de reimplementarlo a mano?
4. ¿Tiene los estados de carga, error y vacío, **y pruebas de los tres**?
5. ¿Hay **una sola acción verde llena** por vista, y las confirmaciones destructivas van con
   `btn-peligro`?
6. ¿Las tablas son `tabla-apilable`, con `data-etiqueta` en cada celda?
7. ¿Se ve bien a 1440, 1180, 900 y **390** px? Las ventanas, por encima de todo; los títulos,
   sin pisarse; nada que desborde dentro de una pestaña (si la pantalla tiene pestañas, su
   ruta lleva `pestanas: true` en el barrido de `e2e-stack/responsive.spec.ts`).
8. ¿Los textos están en español, en voz activa y sin jerga?
9. ¿`npm run verificar` pasa? (lint + tipos + cobertura + build, lo mismo que el CI)

## Deuda conocida

- **Sin tema oscuro.** Decisión de producto; los tokens están listos para agregarlo.

Encontrado al escribir `DESIGN.md` (`R2-PAN-03`), fuera de lo que ya se rediseñó:

- **Espaciado de la etiqueta en mayúsculas sin token.** Es `.09em` en `.etiqueta`,
  `.tabla th`, `.ficha dt` y la tabla apilada, y `.08em` en `.resumen h3`, `.linea-hoy-texto`
  e `.indicador-titulo`. Hace falta un token y una sola medida.
- **Radios escritos a mano**: 3 px en `.marcador-plan`, 4 px en `.esqueleto-linea` y en
  `.barra-pista`/`.barra-valor`, 2 px en `.linea-hoy-marca` y 6 px en `:focus-visible` (el
  valor de `--r-campo`).
- **Cortes a 899 y a 900 px mezclados.** A 900 px justos, `.formulario` y `.dos-columnas` ya
  pasan a una columna mientras `.con-ficha` sigue a dos.
- **`--sombra-1` y `--sombra-2` valen `none`** y siguen referenciados. Es coherente con el
  diseño plano, pero son tokens muertos: o se retiran o se les da uso.
- **El ingreso, el portal y los módulos sin rediseñar** contradicen el sistema en puntos que
  sus unidades de la hoja de ruta corrigen: el antetítulo en pastilla y el vidrio de
  `.ingreso-vista`, la sombra de `.portal-nav` y la opacidad de `.cupo:disabled`.
- **El contrato, la fórmula médica y el comprobante de pago siguen en PDF sin marca**, con las
  fuentes base del PDF (latin-1), que estropean las tildes. El carnet ya usa
  `app/core/marca_pdf.py` (logo, paleta, GeosansLight e Inter); los demás lo adoptan en su
  unidad.
- **El panel copia qué pasos registra la consulta clínica.** `CAMPOS_DE_LA_CONSULTA`
  (`src/features/rutas/ruta.ts`) repite las claves de `_PASOS_DESDE_LA_CONSULTA`
  (`backend/app/modules/clinica/service.py`) para decidir si «Registrar la atención» abre la
  consulta o el servicio. Si el backend añade un campo y el panel no, el botón manda al sitio
  equivocado y ninguna prueba lo ve. Se cierra cuando la API diga en el catálogo de tipos de
  servicio qué pasos llena la consulta, mejor en `R2-PAN-08`. El flujo completo, en
  [`flujo-de-la-visita.md`](../flujo-de-la-visita.md).
- **Nombres de catálogo sin tildes** («Atencion en clinica aliada», «Vacunacion»): vienen de
  `backend/app/modules/catalogos/datos.py` y se ven en la línea y en los botones.
