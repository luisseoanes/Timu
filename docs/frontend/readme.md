# Documentación del frontend — TIMU

> **En rediseño.** La interfaz se está rediseñando con la marca real de TIMU; el orden, el
> estado de cada unidad y el siguiente paso están en la
> [hoja de ruta](../hoja-de-ruta-rediseno.md). Ya usan la línea nueva la estructura del panel,
> Familias, Rutas, Clínica, el Inicio, las ventanas, la espera de sesión y el portal de familias entero; el
> resto de pantallas tiene la paleta, la tipografía y el logo nuevos con su composición
> anterior, hasta su unidad.

## Qué leer antes de escribir una pantalla

| Documento | Qué resuelve |
| --- | --- |
| [`DESIGN.md`](../../DESIGN.md) | **El sistema de diseño**, escrito por la skill desde lo construido: roles de color, tipografía, medidas, capas, componentes y sus reglas («do» y «don't»). Manda sobre lo demás en lo visual. |
| [Manual de marca](../manual-de-marca.md) | Color, tipografía, logo y voz de TIMU, y los roles y contrastes de la plataforma (Parte II). |
| [`PRODUCT.md`](../../PRODUCT.md) | Para quién es cada pantalla y desde qué dispositivo la usa. |
| [components.md](components.md) | Inventario de componentes y clases: cuándo va cada uno y qué regla no se rompe. |
| [layouts.md](layouts.md) | Plantillas de página: estructura del panel, listado con ficha, inicio, bandeja de tareas, ventanas, ingreso y portal, con los cortes de pantalla. |
| [conventions.md](conventions.md) | Estructura por dominio, nombres, datos, sesión, pruebas, accesibilidad, tokens y su guarda, qué revisar antes de empujar y la deuda conocida. |
| [capturas-revisor.md](capturas-revisor.md) | Cómo se capturan las pantallas para el revisor final de la skill: anchos, sesiones y cupos, estados simulados y el esqueleto del script. |

El diseño lo gobierna la skill del repositorio (`/impeccable`): una superficie con identidad
propia empieza con un sorteo de direcciones y se cierra con su revisor final hasta el `ship`
(ver la hoja de ruta, «Cómo se trabaja»). El contrato de cada superficie diseñada vive en
`.impeccable/surfaces/`.

## Dónde vive cada cosa

```
frontend/src/
  styles/
    tokens.css       Única fuente de color, tipografía, medidas, capas: paleta, roles y @pares
    base.css         Reinicio, @font-face de GeosansLight, tipografía base y utilidades
    componentes.css  Botones, campos, tarjetas, insignias, tablas (y la apilable), ventanas…
    vistas.css       Estructura de página: barra del panel, ingreso, portal, inicio, Familias,
                     Rutas y Clínica
    index.css        Índice que impone el orden de la cascada
  assets/            El logo en SVG y GeosansLight, con la receta para regenerarlos
  components/        Piezas compartidas sin lógica de dominio (Modal, Consulta, Pestanas,
                     Paginacion, Distintivo e Insignia, Icono, MarcaTimu, AnilloProgreso,
                     FotoEditable)
  features/<dominio>/  Pantallas y consultas por dominio (auth, familias, dashboard, …)
  layouts/           AppLayout: barra marina, barra inferior en el celular y cabecera
  lib/               errores, permisos, formato, estados y descargas
  routes/            ProtectedRoute: espera de sesión y guardas por perfil
  types/             api.ts, generado desde el OpenAPI del backend (no se edita a mano)
  test/              MSW (handlers, server), setup y guardas de la suite
```

## Las reglas que no se negocian

1. **Ningún componente escribe un color, un radio, una sombra o un `z-index` a mano.** Todo
   sale de un token de `tokens.css`; si falta un valor, se agrega al token. Lo vigila
   `src/test/tokens.test.ts` ([conventions.md](conventions.md#tokens-y-su-guarda)).
2. **El estado se comunica con icono y texto, no solo con color.** Toda condición (al día, en
   mora, vencido) usa una insignia.
3. **Una sola acción verde llena por vista.**
4. **El orden de importación de los estilos no cambia**: `tokens → base → componentes →
   vistas`; alterarlo rompe la cascada y hace que las vistas pierdan contra los componentes.

## Verificación local

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy /api → localhost:8000)
npm run verificar    # lint + tipos + pruebas con cobertura + build: lo mismo que el CI
npm run test:e2e     # recorridos con la API interceptada
E2E_BASE_URL=http://localhost:5173 npm run test:e2e:stack   # contra el stack real, con datos_demo
```
