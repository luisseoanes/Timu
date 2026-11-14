---
version: 1
slug: "frontend-src-features-dashboard-dashboardpage-tsx"
primary_target: "frontend/src/features/dashboard/DashboardPage.tsx"
related_targets: ["frontend/src/features/dashboard/api.ts"]
---

# Panel del equipo · Inicio (R2-PAN-04)

## Alcance y modo

El Inicio del panel: el tablero de administración, comercial y operaciones, y la jornada del
médico. Superficie dentro de la línea visual de Familias (`DESIGN.md`); el sorteo fue de
composición, no de identidad. Modo: Operate. Construcción: en código. El boceto elegido es
`docs/rediseno/boceto-inicio-linea-de-hoy.html` (copia versionada del de la página de decisión).

## Público, tarea y restricciones

- Administración, comercial y operaciones, en la oficina: ver cómo va el período (afiliaciones,
  vigentes, recaudo, mora, rutas, satisfacción) y su evolución, y saber qué toca atender hoy.
  Mismos indicadores para los tres; cada perfil ve primero los de su área (decidido con el
  usuario el 2026-11-13).
- Médico, con el celular: su jornada (decidido con el usuario el 2026-11-13): su ruta de hoy, sus
  consultas sin firmar y sus tareas. El Inicio entra en su barra inferior.
- Indicadores con su evolución: el backend sirve la serie de 12 meses (`GET
  /dashboard/evolucion`, decidido con el usuario) con la misma fórmula y caché que `GET
  /dashboard/indicadores`.
- Restricciones: roles de color del manual (series `--serie-1` a `--serie-4`, nunca el rojo como
  serie), una sola acción verde por vista, controles de 44 px en táctil, WCAG 2.2 AA, cifras
  tabulares, definiciones de `docs/indicadores.md`.

## Direction contract

THESIS: El día del equipo es una línea de metro: lo vencido agrupado arriba, la marca de Hoy y
lo que viene, cada estación con su acción; las cifras del período van en una franja encima, cada
una con su serie. Rechaza el tablero de tarjetas de cifras sueltas con accesos rápidos y una
columna de alertas, donde nada dice qué hacer ni si va mejor o peor.

OWN-WORLD: El de `DESIGN.md`. Franja blanca de seis cifras separadas por hilos: etiqueta de 12 px,
cifra de 24 px tabular, variación contra el período comparable y su serie en línea fina de
`--serie-*`, con el último tramo en curso marcado. Línea vertical de 8 px marina con estaciones
de 24 px: vencida roja con alerta, Hoy como marca marina, la próxima con halo verde, lo que viene
en contorno.

STORY: Quien entra ve si el período va mejor o peor que el anterior, luego qué está vencido y
cuánto, y lo atiende desde su estación; después, qué servicios hay hoy y mañana. El médico ve lo
mismo contado a él: lo que tiene sin firmar o vencido, Hoy y las paradas de su ruta.

FIRST VIEWPORT: 1440×900. Barra marina con Inicio activo. Saludo en GeosansLight de 34 px con el
día, y a la derecha período, ciudad y descargar. Franja de seis cifras a todo el ancho. Debajo,
dos columnas: la línea «Hoy en la operación» (vencido agrupado con su acción, la primera en
verde; Hoy; los servicios de hoy y mañana) y, a 420 px, servicios completados por tipo y recaudo
contra facturado. A 390: saludo, cifras en dos columnas, la línea. Interacción propia, tomada
del «Cuadro» a petición del usuario: cada cifra de la franja es un botón que abre bajo la franja
su serie de 12 meses en grande (eje de meses y de valores, la variación y el mes en curso marcado
como parcial); la cifra abierta queda seleccionada en verde hondo y se cierra con otra pulsación
o con Escape. Cada estación vencida abre su módulo ya filtrado.

FORM: la línea de hoy, con el gesto del cuadro (la cifra abre su serie); candidato 7 de 7 de la lista ordenada (repartido por el sorteo junto al 2
y al 4; encabezaba la mano y lo eligió el usuario); seed:421eac1201a7e39d.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-13)

- **El médico tiene su Inicio de jornada**, no un salto a Rutas: lo eligió el usuario frente a la
  recomendación de entrar en Rutas (que ya resolvía su día).
- **Mismo tablero, orden por perfil.** Comercial ve primero vigentes, afiliaciones, recaudo y
  mora; operaciones, rutas y satisfacción; lo vencido también se ordena por perfil.
- **La evolución la sirve el backend**: siempre 12 meses, que terminan en el mes del período
  elegido (el último marcado como parcial si no ha terminado), más el período comparable: el
  mismo tramo del mes (o del año) anterior, o los mismos días justo antes.
- **Ajuste del usuario sobre la carta elegida**: la cifra de la franja abre su serie en grande,
  para que la evolución sea un gráfico de verdad y no solo líneas en miniatura. «Mora al cierre» pasa a ser histórica: lo pagado después del
  cierre cuenta como pendiente ese día (antes, una serie habría mostrado meses pasados sin mora).

- **Revisión final (2026-11-13)**: `ship` tras dos pasadas de arreglos. En la primera se añadieron
  recaudo contra facturado en la columna, el mes en curso en la miniatura, la acción y el médico
  en cada estación de servicio, lo de hoy ya pasado antes de Hoy («sin atender»), la variación y el
  año en el panel de la serie, la comparación en la línea del saludo y un solo control
  «Descargar». En la segunda, la acción del día agrupado, el gráfico de recaudo que no se repite
  con la serie abierta y la línea base de la variación.

## Pendiente

- Lo que quedó, en la hoja de ruta («Lo que quedó del Inicio tras cerrar `R2-PAN-04`»).
