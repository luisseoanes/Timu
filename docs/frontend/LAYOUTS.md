# Plantillas de página

La estructura vive en [`vistas.css`](../../frontend/src/styles/vistas.css). Los componentes
no saben en qué página están: la grilla siempre la pone la plantilla.

## Ingreso — `.login`

Referencia: tarjeta partida en dos mitades iguales.

```
┌──────────────────────────┬──────────────────────────┐
│  Bienvenido              │        INGRESAR          │
│                          │                          │
│      [ ilustración ]     │  Correo        ______ 👤 │
│                          │  Contraseña    ______ 🔑 │
│                          │  [    Ingresar        ]  │
│  PLATAFORMA TIMU         │      Olvidé mi contraseña│
└──────────────────────────┴──────────────────────────┘
```

- El lienzo es un degradado radial de verdes claros; la tarjeta flota con `--sombra-3`.
- **Lado izquierdo**: degradado de `--verde-400` a `--verde-600`, saludo arriba,
  ilustración plana al centro y el nombre de la plataforma abajo en mayúsculas espaciadas.
  La ilustración es un SVG local: no se cargan imágenes externas.
- **Lado derecho**: título en mayúsculas espaciadas y `--verde-600`, campos subrayados con
  icono al final, botón principal de ancho completo y los enlaces de apoyo alineados a la
  derecha.
- Bajo 900 px las mitades se apilan y el lado de color se reduce a 220 px de alto.

## Shell del panel — `.shell`

```
┌────────────┬──────────────────────────────────────────────┐
│  TIMU      │  Título de la página     [buscador] 🔔 ❓    │
│  ▸ Panel   ├──────────────────────────────────────────────┤
│    Familias│                                              │
│    Cartera │                 contenido                    │
│    …       │                                              │
│  ─────────  │                                              │
│  Usuario   │                                              │
└────────────┴──────────────────────────────────────────────┘
```

- Dos columnas: barra lateral de 236 px y contenido. Todo con 16 px de aire alrededor,
  para que el lienzo verde se vea como marco.
- **Barra lateral**: tarjeta blanca fija con radio de panel. Marca arriba, navegación al
  centro y ficha del usuario abajo separada por una línea. El elemento activo lleva fondo
  `--verde-50`, texto `--verde-700` y una barra interna de 3 px en `--verde-500`.
- **Cabecera**: el título y el subtítulo salen del elemento de navegación activo, así que
  agregar un módulo es agregar una entrada al arreglo `NAV` de `AppLayout.tsx`. A la
  derecha, buscador en pastilla y botones circulares de notificaciones y ayuda.
- Bajo 900 px la barra lateral pasa a ocupar el ancho completo y su navegación se acomoda
  en dos columnas.

## Panel de inicio — `.con-rail`

Contenido principal más columna derecha de widgets de 300 px, tal como la referencia.

1. **Saludo** (`.bienvenida`) — degradado suave en diagonal, nombre del usuario, una línea
   de contexto y distintivos con las cifras del día.
2. **Accesos rápidos** (`.accesos`) — cuatro atajos a las acciones más frecuentes.
3. **Dos columnas** (`.dos-columnas`) — próximos servicios y estado de cartera, ambas con
   filas y enlace *Ver todos* en el encabezado.
4. **Columna derecha** (`.rail`) — cumplimiento del día con anillo y tres métricas, tarjeta
   de lo que requiere atención, y preventivos por vencer.

Bajo 1180 px la columna derecha baja y se reparte en dos columnas; bajo 900 px queda en una.

Los datos son de ejemplo y están marcados con un distintivo neutro hasta que existan los
endpoints del backlog (`F4-DAS-02`). Al conectarlos se retira ese distintivo.

## Listados — tarjeta única

Patrón de `FamiliasPage`: una tarjeta que contiene encabezado con conteo, fila de filtros
—buscador, selector de estado y acción principal empujada a la derecha— y la tabla dentro
de `.scroll-x`. Todo módulo de listado se construye así para que no aparezcan tres
gramáticas distintas de filtro en la aplicación.

## Reglas de adaptación

| Ancho | Qué cambia |
| --- | --- |
| ≥ 1180 px | Distribución completa con columna derecha |
| 900–1180 px | La columna derecha baja bajo el contenido, en dos columnas |
| < 900 px | Una sola columna; barra lateral arriba; ingreso apilado |

El cuerpo de la página nunca se desplaza en horizontal: lo que no cabe —tablas, gráficas—
se desplaza dentro de su propio contenedor.
