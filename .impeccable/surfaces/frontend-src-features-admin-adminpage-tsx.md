---
version: 1
slug: "frontend-src-features-admin-adminpage-tsx"
primary_target: "frontend/src/features/admin/AdminPage.tsx"
related_targets: ["frontend/src/features/admin/Usuarios.tsx","frontend/src/features/admin/Planes.tsx","frontend/src/features/admin/Reglas.tsx","frontend/src/features/admin/EditorRegla.tsx","frontend/src/features/admin/ProbarRegla.tsx","frontend/src/features/admin/Catalogos.tsx","frontend/src/features/admin/InteligenciaArtificial.tsx","frontend/src/features/admin/Supresion.tsx"]
---

# Panel del equipo · Administración (R2-PAN-10, segunda parte)

## Alcance y modo

Administración: usuarios, planes, reglas de negocio, catálogos, inteligencia artificial y
reportes con los eventos de la pasarela. Superficie dentro de la línea visual de Familias
(`DESIGN.md`), sin sorteo: hereda los patrones construidos (bandeja de Cartera, listado con ficha
de Comercial y Aliadas). Modo: Operate. Construcción: en código. Aliadas, la primera parte de
R2-PAN-10, tiene su propio contrato.

## Público, tarea y restricciones

- Solo administración, en la oficina y de vez en cuando: dar de alta y desactivar a alguien del
  equipo o de una clínica aliada, cambiar un perfil, revisar un plan y sus tarifas, entender y
  ajustar una regla, apagar una ciudad o un tipo de servicio, vigilar el gasto de la IA y
  reprocesar un pago que la pasarela no pudo registrar.
- Restricciones: roles de color del manual, una sola acción verde por vista, controles de 44 px en
  táctil, tablas apilables, WCAG 2.2 AA, Radix para lo interactivo. El panel no copia reglas del
  backend: la API agrupa a los usuarios y dice cada regla en palabras.

## Direction contract

THESIS: Administración es configuración que se toca poco: cada pestaña dice en palabras lo que hay
y qué cambia cada acción. Usuarios se lee como una bandeja (el equipo separado de las familias del
portal), y un plan o una regla se abren como un registro. Rechaza los códigos del backend a la
vista (`dias_mora gte 25`, `borrador`, `aliada`), las tarjetas con todas las tarifas abiertas a la
vez, las casillas sueltas que desactivan sin decir qué pasa y los verdes repetidos.

OWN-WORLD: El de `DESIGN.md`. Bandeja: selector segmentado con recuento, tabla apilable a todo el
ancho. Listado con ficha (`.con-ficha`): filas con hilo, ficha blanca con el nombre a 34 px,
pares etiqueta/valor, bloques con su h3, una sola acción verde y lo reversible en el menú de tres
puntos.

STORY: La gerencia abre Administración, ve en «Equipo» a las personas del panel, desactiva a quien
se fue (confirmando en rojo que sus sesiones se cierran), abre el Plan Familiar para revisar lo
que paga cada peludo y abre «Aviso de mora a los 25 días» para leer, sin descifrar JSON, que se
envía cuando la mora llega a 25 días.

FIRST VIEWPORT: 1440×900: pestañas Usuarios, Planes, Reglas, Catálogos, Inteligencia artificial y
Reportes y pasarela; en Usuarios, el título con «Nuevo usuario» en verde, la nota de las sesiones,
las vistas Equipo, Clínicas aliadas, Familias e Inactivos con su recuento, el buscador y la tabla.
390×844: las vistas en dos filas de dos y las filas apiladas.

FORM: bandeja heredada de Tareas, Cartera y Aliadas; listado con ficha heredado de Familias,
Comercial y Aliadas; seed: none (pinned) — el usuario eligió «Pestañas con los patrones» para
Administración («Se quedan las seis pestañas y cada una adopta un patrón ya construido. Usuarios:
bandeja con vistas por perfil y tabla apilable. Planes y Reglas: listado con ficha, con el plan
abierto (precio por número de peludos, coberturas, ciudades) o la regla abierta (su condición en
palabras y Probar). Catálogos, IA y Reportes: tablas apilables y una sola verde por vista»), el
2026-11-14.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-14)

- **Administración con pestañas y los patrones** (decidido con el usuario).
- **La API agrupa a los usuarios** (`grupo`: equipo, aliadas, familias, inactivos), los busca y
  da sus recuentos; un índice por perfil y estado sirve las vistas (migración 0042).
- **Cada regla en palabras**, generadas por el motor (`condicion_texto`, `accion_texto`); la
  edición sigue en JSON para quien la necesite.
- **Desactivar a alguien confirma en rojo**; activarlo de nuevo es directo. Desactivar un plan o
  una regla va en el menú: es reversible.
- **Los nombres de las modalidades suben a `catalogos`**, compartidos con Servicios.

## Editor de reglas por campos (DEU-8, 2026-11-17)

Decidido por el usuario, cada punto con la opción recomendada (Sección 7 «crear automatizaciones»,
6.3 «reglas modificables sin reconstruir», Sección 13 «personal no técnico»):

- **Ventana con la regla en palabras arriba** («Ventana, regla en palabras»): la ficha sigue de
  lectura con «Probar», y «Editar regla» abre la ventana, como Planes y Usuarios. Arriba, cuándo
  aplica y qué hace en palabras, que la API rehace con cada cambio (`POST /reglas/describir`).
- **Editar y crear**: «Nueva regla» en la cabecera del listado (verde solo sin una regla abierta);
  primero se elige cuándo se revisa (el evento). El código interno y la clave del aviso no se
  piden: los pone la API.
- **Un nivel: todas o alguna**: una lista de comparaciones (dato, comparación y valor). Una regla
  con grupos anidados, escrita por la API, se lee en palabras y se conserva al guardar.
- **La API declara y valida los campos de cada evento**: `GET /reglas/eventos` da sus campos con
  tipo, comparaciones y valores del catálogo, sus acciones con sus parámetros y los planes; una
  condición sobre un dato que el evento no da, o un valor que no está en el catálogo, se rechaza.

Desviaciones del boceto tomadas al construir (aceptadas por el revisor final):

- **Cada condición en dos filas**, en todos los anchos: el dato a lo ancho con su «quitar», y debajo
  la comparación y el valor (o las casillas de «es uno de», a todo el ancho). Con tres listas en una
  fila, la ventana de 560 px cortaba el nombre del dato («Ciudad de la famil»).
- **La frase fija arriba del cuerpo desde 600 px**, sobre una franja blanca que tapa lo que pasa por
  detrás; en el celular no se fija, para no ocupar la mitad de la hoja.
- **La acción como dato cuando el evento solo admite una** («Acción: Avisar por WhatsApp»), sin lista.
- **El control y la frase dicen lo mismo**: «al menos», «como mucho», «igual a», «más de», «menos
  de» y «distinto de» en la comparación y en la regla en palabras.
- **Las plantillas de mora que aún no están en el catálogo** se nombran con un nombre provisional
  («Aviso de mora · aún sin registrar»), nunca por su código.

## Perfiles por función (2026-11-19)

seed: none (pinned). El administrador configura y no opera (decidido con el usuario el 2026-11-19,
`docs/perfiles-y-permisos.md`). Administración pierde «Reportes y pasarela» (los reportes van al Inicio
de Gerencia y la pasarela a Cartera) y gana «Plantillas de WhatsApp», «Guion del asistente»,
«Encuestas» (su configuración) y «Supresión de datos».

- **Supresión de datos** (`Supresion.tsx`, Ley 1581), palabras del usuario: «la hace el
  Administrador sin ver la ficha». Busca por documento (campo y «Buscar» en una línea, el botón a la
  altura del campo), ve solo el nombre del titular, cuántas mascotas y el estado, y confirma en rojo.
  Con un contrato vigente no se ofrece anonimizar: lo dice («Atención al cliente lo cancela antes»)
  con una insignia de alerta, porque la base lo rechazaría.

## Pendiente

- Lo que quede, en las notas de cierre del rediseño (`docs/rediseno/notas-de-cierre.md`, «Lo que quedó de Aliadas y administración»).
