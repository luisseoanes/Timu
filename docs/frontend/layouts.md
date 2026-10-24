# Plantillas de página

La estructura vive en [`vistas.css`](../../frontend/src/styles/vistas.css). Los componentes
no saben en qué página están: la grilla siempre la pone la plantilla.

## Ingreso — `.ingreso` (`AccesoLayout`)

La misma plantilla sirve al ingreso, la recuperación y la activación de la cuenta.

```
┌───────────────────────────────┬────────────────────────────┐
│ [sello] TIMU                  │                            │
│                               │  Bienvenido de nuevo       │
│ (Plataforma clínica)          │  [ Equipo TIMU | Familias ]│
│ El cuidado de cada mascota…   │  Correo        [✉ ______ ] │
│  ▢ Historia clínica           │  Contraseña    [🔒 _____ 👁]│
│  ▢ Visitas a domicilio        │        ¿Olvidaste tu…?     │
│  ▢ Preventivos al día         │  [        Ingresar       ] │
│ ┌ vista previa de una visita ┐│  ─────────────────────────  │
│ └────────────────────────────┘│  🛡 Conexión cifrada        │
│ 🛡 Datos clínicos protegidos   │                            │
└───────────────────────────────┴────────────────────────────┘
```

- **Panel de marca**: degradado de `--verde-700` a `--marca-profunda` con dos halos
  radiales. Todo lo que va encima usa los tokens `--sobre-marca*`: texto, tarjetas de
  vidrio (`--sobre-marca-velo`) y bordes (`--sobre-marca-borde`). La vista previa de una
  visita es decorativa (`aria-hidden`).
- **Formulario**: selector segmentado (Radix Tabs) entre **Equipo** (correo y contraseña,
  con botón para ver la clave) y **Familias** (celular y código de un solo uso por
  WhatsApp). Los campos llevan icono a la izquierda (`.campo-adorno`).
- Los errores van en `.aviso-error` con `role="alert"`; las confirmaciones en `.aviso-ok`.
- Bajo 900 px el panel de marca desaparece y la marca sube encima del formulario.

Las páginas públicas sencillas (encuesta, verificación de carnet, afiliación, espacio de
la clínica aliada) usan `.publica` + `.publica-tarjeta`: marca arriba y una tarjeta
centrada.

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

Los indicadores salen de `GET /dashboard/indicadores` (período y ciudad) y la fórmula de
cada uno aparece al pasar el cursor. El perfil médico ve su jornada en lugar del panel
gerencial.

## Listados — tarjeta única

Patrón de `FamiliasPage`: una tarjeta que contiene encabezado con conteo, fila de filtros
—buscador, selector de estado y acción principal empujada a la derecha— y la tabla dentro
de `.scroll-x`. Todo módulo de listado se construye así para que no aparezcan tres
gramáticas distintas de filtro en la aplicación.

## Portal de familias — `.portal`

Primero para el celular: cabecera corta con la marca y navegación fija abajo (cinco
destinos). Desde 900 px la navegación sube a la cabecera como pastillas. El saludo usa el
degradado de marca (`.portal-hola`) con los accesos rápidos encima.

## Reglas de adaptación

| Ancho | Qué cambia |
| --- | --- |
| ≥ 1180 px | Distribución completa con columna derecha |
| 900–1180 px | La columna derecha baja bajo el contenido, en dos columnas |
| < 900 px | Una sola columna; barra lateral arriba; ingreso apilado |

El cuerpo de la página nunca se desplaza en horizontal: lo que no cabe —tablas, gráficas—
se desplaza dentro de su propio contenedor.
