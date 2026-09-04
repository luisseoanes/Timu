# Documentación del frontend — TIMU

El panel de TIMU sigue un sistema visual único: fondo verde menta, tarjetas blancas de
esquinas amplias, barra lateral clara con el módulo activo resaltado y una columna derecha
de widgets en el panel de inicio. El ingreso usa una tarjeta partida en dos: un lado
sólido con la marca y una ilustración, y el otro con el formulario.

Página viva del sistema, con la paleta y los componentes renderizados:
https://claude.ai/code/artifact/4a15c715-c825-40f7-b796-89f4bfd79e70

Antes de escribir una pantalla nueva, lee estos cuatro documentos en orden:

| Documento | Qué resuelve |
| --- | --- |
| [design-system.md](design-system.md) | Color, tipografía, espaciado, radios, sombras e iconografía. Los tokens y cómo se usan. |
| [components.md](components.md) | Inventario de componentes con su anatomía, estados y cuándo corresponde cada uno. |
| [layouts.md](layouts.md) | Plantillas de página: ingreso, shell del panel, inicio con widgets y listados. |
| [conventions.md](conventions.md) | Estructura de carpetas, nombres, datos, accesibilidad y qué revisar antes de fusionar. |

## Dónde vive cada cosa

```
frontend/src/
  styles/
    tokens.css       Única fuente de verdad: color, tipografía, espaciado, radios, sombras
    base.css         Reinicio, tipografía base y utilidades de texto
    componentes.css  Botones, campos, tarjetas, distintivos, filas, tablas, anillo
    vistas.css       Estructura de página: shell, dashboard, login, adaptación responsiva
    index.css        Índice que impone el orden de la cascada
  components/        Piezas compartidas sin lógica de dominio (Icono, AnilloProgreso)
  features/<dominio>/  Pantallas y consultas por dominio (auth, familias, dashboard, …)
  layouts/           AppLayout: barra lateral, cabecera y contenido
  routes/            ProtectedRoute y guardas por perfil
  types/             Espejo tipado de los schemas del backend
```

## Las tres reglas que no se negocian

1. **Ningún componente escribe un color, un radio o una sombra a mano.** Todo sale de un
   token de `tokens.css`. Si falta un valor, se agrega al token, no al componente.
2. **El estado se comunica con color y forma, no sólo con texto.** Toda condición
   (al día, en mora, vencido) usa un distintivo con su par de fondo y texto.
3. **El orden de importación de los estilos no cambia.** `tokens → base → componentes →
   vistas`; alterarlo rompe la cascada y hace que las vistas pierdan contra los componentes.

## Verificación local

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run typecheck  # tipos
npm run build      # compilación de producción
```
