# Documentación del frontend — TIMU

> **En rediseño.** La interfaz se está rediseñando con la marca real de TIMU
> ([hoja de ruta](../hoja-de-ruta-rediseno.md)). Mientras dure:
>
> - el color, la tipografía, el logo y la voz los fija el [manual de marca](../manual-de-marca.md),
>   no este directorio;
> - el diseño lo gobierna la skill del repositorio (`/impeccable`), con el contexto de producto
>   de [`PRODUCT.md`](../../PRODUCT.md) y, cuando exista, el sistema de `DESIGN.md`;
> - `components.md` y `layouts.md` describen lo construido hasta ahora, que se reemplaza
>   pantalla por pantalla. Se reescriben al cerrar el rediseño (`R4-CIE-03`).

Hasta el rediseño, el panel seguía un sistema visual en tonos menta, ya descartado: tarjetas
blancas de esquinas amplias, barra lateral clara con el módulo activo resaltado y una columna
derecha de widgets en el panel de inicio.

Antes de escribir una pantalla nueva, lee estos cuatro documentos en orden:

| Documento | Qué resuelve |
| --- | --- |
| [design-system.md](design-system.md) | Espaciado, radios, sombras e iconografía. El color y la tipografía remiten al [manual de marca](../manual-de-marca.md). |
| [components.md](components.md) | Inventario de componentes con su anatomía, estados y cuándo corresponde cada uno. |
| [layouts.md](layouts.md) | Plantillas de página: ingreso, shell del panel, inicio con widgets y listados. |
| [conventions.md](conventions.md) | Estructura de carpetas, nombres, datos, sesión, pruebas, accesibilidad y qué revisar antes de empujar. |

## Dónde vive cada cosa

```
frontend/src/
  styles/
    tokens.css       Única fuente de verdad: color, tipografía, espaciado, radios, sombras
    base.css         Reinicio, tipografía base y utilidades de texto
    componentes.css  Botones, campos, tarjetas, distintivos, filas, tablas, anillo
    vistas.css       Estructura de página: shell, dashboard, login, adaptación responsiva
    index.css        Índice que impone el orden de la cascada
  components/        Piezas compartidas sin lógica de dominio (Modal, Consulta, Pestanas,
                     Paginacion, Distintivo, Icono, AnilloProgreso)
  features/<dominio>/  Pantallas y consultas por dominio (auth, familias, dashboard, …)
  layouts/           AppLayout: barra lateral, cabecera y contenido del panel
  lib/               errores (mensajeError, esErrorPasajero), permisos, formato, estados
  routes/            ProtectedRoute y guardas por perfil
  types/             api.ts, generado desde el OpenAPI del backend (no se edita a mano)
  test/              MSW (handlers, server), setup y guardas de la suite
```

## Las tres reglas que no se negocian

1. **Ningún componente escribe un color, un radio o una sombra a mano.** Todo sale de un
   token de `tokens.css`. Si falta un valor, se agrega al token, no al componente. Para los
   colores lo vigila `src/test/tokens.test.ts`.
2. **El estado se comunica con color y forma, no sólo con texto.** Toda condición
   (al día, en mora, vencido) usa un distintivo con su par de fondo y texto.
3. **El orden de importación de los estilos no cambia.** `tokens → base → componentes →
   vistas`; alterarlo rompe la cascada y hace que las vistas pierdan contra los componentes.

## Verificación local

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy /api → localhost:8000)
npm run verificar    # lint + tipos + pruebas con cobertura + build: lo mismo que el CI
npm run test:e2e     # recorridos con la API interceptada
```
