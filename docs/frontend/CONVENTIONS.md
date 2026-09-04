# Convenciones del frontend

## Estructura por dominio

Cada dominio de la plataforma es una carpeta en `src/features/` con lo suyo dentro:

```
features/familias/
  api.ts              Consultas y mutaciones con React Query
  FamiliasPage.tsx    Pantalla
  <Componente>.tsx    Piezas que sólo usa este dominio
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

## Permisos

`ProtectedRoute` acepta la lista de perfiles que pueden entrar. El frontend esconde lo que
el usuario no puede hacer, pero **eso no es seguridad**: la autorización real la impone el
backend en cada endpoint. Un botón oculto sin permiso en el servidor es un defecto.

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
3. ¿Tiene los estados de carga, error y vacío?
4. ¿Se ve bien a 1440, 1180 y 900 px de ancho?
5. ¿Los textos están en español, en voz activa y sin jerga?
6. ¿`npm run typecheck` y `npm run build` pasan?

## Deuda conocida

- **Sin tema oscuro.** Decisión de producto; los tokens están listos para agregarlo.
- **Sin librería de componentes.** Todo es CSS propio: la aplicación es pequeña y la
  referencia visual es específica. Si el catálogo crece más allá de lo documentado, la
  conversación es sobre extraer un paquete de componentes, no sobre adoptar un framework
  de UI que habría que repintar entero.
- **Datos de ejemplo en el panel de inicio** hasta que existan los endpoints de `F4-DAS-02`.
