# Convenciones del frontend

## Estructura por dominio

Cada dominio de la plataforma es una carpeta en `src/features/` con lo suyo dentro:

```
features/familias/
  api.ts                   Consultas y mutaciones con React Query
  FamiliasPage.tsx         Pantalla
  FamiliasPage.test.tsx    Sus pruebas, al lado de lo que prueban
  <Componente>.tsx         Piezas que sólo usa este dominio
```

Una pieza sube a `src/components/` únicamente cuando la usan dos dominios. Nada de una
carpeta `common/` que termine siendo un cajón de sastre.

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

## Permisos

`ProtectedRoute` acepta la lista de perfiles que pueden entrar. El frontend esconde lo que
el usuario no puede hacer, pero **eso no es seguridad**: la autorización real la impone el
backend en cada endpoint, con `require_roles` para el perfil y `restringir()` para las
filas. Un botón oculto sin permiso en el servidor es un defecto.

## Pruebas

Toda pantalla nueva llega con las suyas. No es una aspiración: el CI las exige en cada
push y hay umbral de cobertura del 60%.

- **Componentes**: Vitest + Testing Library. La API se simula con **MSW**
  (`src/test/handlers.ts`), a nivel de red y nunca haciendo mock de axios, para que se
  pruebe también cómo se arma la petición.
- **Recorridos**: Playwright en `e2e/`, sobre la aplicación compilada.
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

## Qué revisar antes de fusionar

1. ¿La pantalla usa sólo tokens? Buscar `#` en el diff: un color literal es un rechazo.
2. ¿Reutiliza los componentes existentes en vez de crear una variante casi igual?
3. ¿Lo interactivo se apoya en Radix en vez de reimplementarlo a mano?
4. ¿Tiene los estados de carga, error y vacío, **y pruebas de los tres**?
5. ¿Se ve bien a 1440, 1180 y 900 px de ancho?
6. ¿Los textos están en español, en voz activa y sin jerga?
7. ¿`npm run verificar` pasa? (lint + tipos + cobertura + build, lo mismo que el CI)

## Deuda conocida

- **Sin tema oscuro.** Decisión de producto; los tokens están listos para agregarlo.
- **Datos de ejemplo en el panel de inicio** hasta que existan los endpoints de `F4-DAS-02`.
