# Rediseño del front: notas de cierre de cada unidad

Anexo de la [hoja de ruta del rediseño](../hoja-de-ruta-rediseno.md), separado de ella el
2026-11-16. Al cerrar cada unidad se anotó «lo que quedó»: deuda, decisiones abiertas y
sugerencias del revisor. Es sobre todo historia: lo resuelto va tachado, con la deuda que lo
cerró ([deuda.md](deuda.md)). Una nota abierta nueva se añade aquí, en el apartado de su unidad.

### Lo que quedó de Familias tras su cierre

- ~~**En el celular, la línea no se abre en «hoy».**~~ Resuelto el 2026-11-15 (`DEU-13`): en
  vertical, lo vencido se agrupa.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo» de la dirección, no defectos): estaciones
  de 34 px con anillo de 6 px como en el boceto (hoy 24 y 4), etiquetas de estado cuadradas en
  lugar de píldoras, y el listado y el detalle como paneles planos a ras en lugar de tarjetas
  con radio de 12 px.

### Lo que quedó de Rutas tras su cierre

- **Mapa embebido** (requisito 6.7): decidido con el usuario dejarlo fuera; cada parada abre la
  navegación del celular. Para cerrarlo, TIMU elige proveedor y presupuesto
  ([pendientes externos](../pendientes-externos.md#mapa-de-las-rutas-requisito-67-r2-pan-06)).
- ~~**Registrar los pasos de la atención desde la propia parada**~~ Resuelto en `R2-PAN-05`: la consulta es el registro de la visita y «Registrar la atención» la abre. Antes: hoy «Registrar la atención»
  lleva a la ficha del servicio. Se decide al rediseñar ese detalle en `R2-PAN-05`.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes): etiquetar la hora de «Por rutear» («programado 4:19 a.
  m.»), centrar la columna del médico en escritorio y capturar una ruta con una parada omitida.

### Lo que quedó de Clínica tras su cierre

- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes): limitar el área de texto de la consulta a unos 75
  caracteres en escritorio, unificar la cabecera del borrador y la de la lectura, alinear a la
  izquierda los valores largos de la tabla apilable en el celular (es del componente común) y
  sembrar una plantilla de consulta en `datos_demo`.

### Lo que quedó del portal tras cerrar `R3-POR-01` y `R3-POR-02`

- ~~**Datos de demostración**~~ Resuelto el 2026-11-16 (`DEU-14`): Jorge Ramírez
  (`jorge@example.com`) entra al portal al día. Antes: la única familia con portal (Ana) tiene el plan congelado. Los
  estados «al día» se capturaron para el revisor interceptando la API. Una segunda familia con
  portal en `datos_demo` daría al barrido y a los recorridos el estado sano.
- ~~**La consulta en la clínica no se agenda desde el portal**~~ Resuelto el 2026-11-16 (`DEU-2`)., aunque el backend la permite
  (`MODALIDADES_AUTOGESTION`): la ventana de agendar solo ofrece las visitas en casa y las
  preventivas. Hay que decidir con el usuario si el portal la ofrece
  ([`portal-familias.md`](../portal-familias.md)).
- ~~**La prueba de la foto**~~ Resuelto el 2026-11-16 (`DEU-16`): la prueba quita la foto al terminar. Antes: (`e2e-stack/recorridos.spec.ts`) sube un PNG de 1×1 a la primera
  mascota de Ana, que el portal enseña después como su foto. No rompe nada, pero ensucia las
  capturas: hay que quitarla antes de capturar.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes): la flecha de las listas es un triángulo relleno,
  y el resto del sistema usa chevrones de trazo. En citas y pagos, el «techo» de la dirección:
  usar las estaciones de la línea (la vencida en las cuotas vencidas, la próxima con halo en la
  próxima cita), la marca de «Hoy» en la cita en camino y el color del plan en Pagos. Y
  «Confirmada» y «Atendida» comparten tono (en pestañas distintas).

### Lo que quedó del Inicio tras cerrar `R2-PAN-04`

- ~~**Las series 1 y 2 del manual no se distinguen**~~ Resuelto el 2026-11-15 (`DEU-1`): el manual
  pasa a verde, azul, naranja y marino.
- **Rendimiento de la serie con volumen real**: son 13 cálculos por carga. Sobre los datos de
  demostración tarda 190–335 ms sin caché; contra el umbral de 2 s de F4-DAS-02 lo dirá la prueba
  de carga, que ya la incluye.
- ~~Las estaciones de servicio no nombran familia ni mascota~~: resuelto en `R2-PAN-05`, con el
  listado que las trae.
- **«Ver los servicios» y «Ver la agenda» llevan a la agenda de hoy**: Servicios ya lee sus
  filtros de la URL (`R2-PAN-05`) y muestra encima los atrasados, que es lo que esos enlaces
  buscan; no hace falta un filtro más.
- ~~**Los datos de demostración tienen poca historia**~~ Resuelto el 2026-11-16 (`DEU-14`, `operacion_demo`: ocho semanas de operación). Antes: las series son planas antes de agosto y
  Rutas tiene un solo mes con dato. El revisor juzgó con esa limitación.

### Lo que quedó de Servicios y Tareas tras cerrar `R2-PAN-05`

- ~~Fallo abierto: «Editar» un paso ya registrado devuelve 500~~: resuelto el 2026-11-14. Decidido
  con el usuario, los pasos se corrigen mientras el servicio está en atención y quedan fijos al
  completarlo: la matriz de RLS da `U` en `servicio_pasos` a quien los inserta (migración `0041`),
  con la prueba que reproducía el 500.
- ~~**El barrido responsive no mide 900 px**~~ Resuelto el 2026-11-16 (`DEU-17`).: el revisor lo propuso, pero medir un ancho más metería
  en `PENDIENTES` fallos de módulos sin rediseñar, y esa lista solo puede encoger. Esta superficie
  se comprobó a 900 en las capturas del revisor. Se puede añadir en `R4-CIE-01`, cuando
  `PENDIENTES` quede vacía.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo», no defectos): una ficha fija al desplazar
  (hoy se trae a la vista al abrirla y la fila pulsada queda fuera del listado visible), una marca
  de «ahora» dentro del grupo de Hoy y un tratamiento propio del servicio atrasado, las franjas
  como rejilla semanal por ciudad y modalidad en lugar de 24 filas, menos blanco en la ficha vacía
  y el foco en «Familia» al abrir «Agendar servicio».

### Lo que quedó de Cartera y preventivos tras cerrar `R2-PAN-08`

- ~~**El peso de la desparasitación no está en el paso «Aplicación»**~~ Resuelto el 2026-11-16 (`DEU-4`). del servicio: con «el servicio
  manda», una desparasitación hecha en visita se aplica sin peso (`F2-PRE-07` lo pide opcional). Para
  tenerlo hay que añadir un campo opcional a los pasos del catálogo (hoy todos los campos son
  obligatorios en `completar_paso`). Se decide con el usuario.
- ~~**Una visita preventiva agendada desde el portal no se enlaza con ningún preventivo**~~ Resuelto el 2026-11-16 (`DEU-3`).: el portal
  agenda un servicio de vacunación sin decir cuál, así que completarlo no aplica nada. Hay que decidir
  con el usuario si el portal agenda preventivos concretos (como la bandeja) o si la visita elige el
  preventivo al completarse.
- **La ventana de la bandeja de preventivos es de 30 días** (valor provisional de TIMU, en `pendientes-externos.md`) (`VENTANA_BANDEJA_DIAS`): lo que vence en
  el próximo mes. La puso esta unidad; si TIMU quiere otra, es una constante.
- ~~**Nombres de los esquemas sin tildes**~~ Resuelto el 2026-11-16 (`DEU-11`, migración `0045`). Antes: («Antirrabica canina», «Desparasitacion interna»): son del
  catálogo (`catalogos/datos.py`), deuda ya anotada en `docs/frontend/conventions.md`.
- ~~**«Por autorizar» con el icono de la llave solo en la bandeja de preventivos**~~ Resuelto el 2026-11-15 (`DEU-5`). Antes: el revisor pidió
  que no compartiera el triángulo de lo vencido. Llevarlo al mapeo de `lib/estados.ts` cambiaría el
  distintivo en Servicios también: se decide con el usuario.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo»): las franjas de la ventana de agendar en una
  rejilla de tres columnas iguales, «Escribir» en todos los grupos de la bandeja (también sirve para
  avisar de la visita por agendar), estrechar la columna del preventivo para que «Toca» no quede en
  medio de un vacío a 1440, y en la tarjeta de familia del carnet a 390 el separador parte
  «1020304050 · Bogota».

### Lo que quedó de Comercial y campañas tras cerrar `R2-PAN-09`

- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo»): un desvanecido o «mensajes anteriores» en lo
  alto de la conversación recortada; distinguir «Recibido» y «Enviado» en Mensajes con algo más que
  la palabra, y recortar los cuerpos largos a dos líneas en peso normal; las fichas de cifra de
  Encuestas, grandes para dos cifras vacías; «Destinatarios en CSV» alineado con el contenido y
  oculto en un borrador que nunca salió; «Interesados 6» repite «Abiertos 6»; «A quién le llega» en
  una columna estrecha a 1440; y un vacío de Segmentos que oriente.
- ~~**La conversación de Comercial es la de WhatsApp**~~ Decidido con el usuario no hacerlo (`DEU-12`). Antes: el embudo no muestra correos ni llamadas,
  porque no se registran. Si TIMU los quiere en la ficha, hay que guardarlos primero.
- ~~**«Plantilla en Meta» enseña el código**~~ Resuelto el 2026-11-16 (`DEU-10`). con que se registra la plantilla (`recordatorio_renovacion`):
  el catálogo no tiene nombre legible. Darle uno es un campo nuevo en las plantillas.

### Lo que quedó de Aliadas y administración tras cerrar `R2-PAN-10`

- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo»). En Aliadas: las etiquetas de la liquidación
  apilada se parten en dos líneas; la ficha de una clínica no lleva a sus remisiones atendidas o
  anuladas (la bandeja no filtra por clínica); el total de la liquidación iría mejor en un `th`; y en
  Utilizadas y Anuladas queda la columna de acciones vacía. En Administración: las tarifas de un plan
  en 2×2, y en una línea cuando son iguales; los beneficios sin apilar en el celular; la barra de
  presupuesto de la IA junto a «Gastado»; y «Desactivar» en un plano neutro que solo se vuelva rojo
  al confirmar. Común a todo el panel: la tira de pestañas a 390 corta la última sin indicar que se
  desplaza.
- ~~**Lo que el documentador vio fuera del sistema**~~ Resuelto el 2026-11-15 (`DEU-26`). Antes: y no se canonizó: los eventos de la pasarela son una
  bandeja sin recuento en sus vistas (la API no los cuenta) y con la vista fuera de la URL; los casos de
  prueba de la IA enseñan lo esperado en JSON; y el formulario de reportes lleva un `style` en línea en su
  `fieldset`. Los dos últimos son anteriores a esta unidad.
- **Las reglas se editan en JSON** (decidido el editor por campos, pendiente: `DEU-8`): se leen y se prueban en palabras, pero cambiar una condición o una
  acción sigue siendo escribir el JSON del motor. Un editor por campos es trabajo nuevo.
- ~~**Pasar una cuenta a clínica aliada, o de clínica aliada al equipo, no se hace desde la fila**~~ Decidido con el usuario no hacerlo: se crea otra cuenta (`DEU-9`). Antes:
  necesita la clínica, que solo se elige al crear el usuario. Hoy hay que crear la cuenta nueva.
- ~~**Las plantillas de WhatsApp no tienen nombre legible**~~ Resuelto el 2026-11-16 (`DEU-10`).: las reglas y las campañas enseñan el código
  con que se registran en Meta (`aviso_mora`) como dato secundario.
- ~~**Textos guardados sin tildes**~~ Resuelto el 2026-11-16 (`DEU-11`), también las ciudades (migración `0048`).: el motivo de algunas reglas sembradas («mas cupos») y los nombres de
  reglas y catálogos («Aviso de mora a los 25 dias», «Atencion en clinica aliada») vienen de los datos;
  la deuda ya está en `docs/frontend/conventions.md`.

### Lo que quedó del acceso tras cerrar `R3-PUB-01`

- ~~**La clínica aliada entra por «Equipo TIMU»**~~ Resuelto el 2026-11-16 (`DEU-6`): la pestaña se llama «Equipo y aliadas». Antes:, que no es su nombre. Se mantuvo el selector por
  público por decisión del usuario; si se renombra, es solo el texto de la pestaña.
- ~~**La vigencia de los enlaces no se dice en pantalla**~~ Resuelto el 2026-11-15 (`DEU-7`). Antes: (30 minutos la recuperación y 72 horas la
  activación, en `Settings`): el panel no copia esos valores. Si TIMU quiere decirla, la API la da
  con el estado del enlace.
- **La consulta del enlace no entra en la guarda de caminos calientes**, que solo recorre listados
  por GET: es una búsqueda por `token_hash`, que es único y tiene índice.
- **Lo que el documentador vio fuera del sistema** (los 48 px son la norma del acceso, `DEU-25`; las sombras a `none` se retiraron, `DEU-21`; la sombra de `.publica-tarjeta` se corrige en `R3-PUB-02`) y no se canonizó: los campos con icono del
  acceso miden 48 px (`.campo-adorno .input`, anterior a esta unidad) y no los 40/44 del resto;
  `.publica-tarjeta` lleva sombra estando quieta (es de las páginas públicas sin rediseñar, se
  corrige en su unidad); y el segmento activo del selector pide `--sombra-2`, que vale `none`.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes) (el «techo»): que el tramo de la línea se dibuje hasta
  «Hoy» al cargar (respetando `prefers-reduced-motion`), que en la activación la estación
  «Afiliación» se encienda al guardar la contraseña antes de llevar al portal, y anclar a 1440 el
  título del formulario a la altura de la frase del panel. A 900 px las estaciones de la línea no
  quedan a la misma distancia (sus columnas toman el ancho del rótulo).

### Lo que quedó de Mi clínica tras cerrar `R3-ALI-01`

- **La familia no recibe el código de la remisión por ningún canal**: la remisión no envía ningún
  mensaje y el portal no la muestra, así que hoy se lo dice el equipo. La clínica valida justo ese
  código. Decisión abierta con el usuario: enviarlo por WhatsApp al emitir, mostrarlo en el portal o
  las dos.
- **Al reportar no se vuelve a comprobar la cartera**: el plan, el pago y el cupo se validan al
  emitir la remisión (`F2-ALI-02`), no el día de la atención. Si la familia entra en mora entre una
  fecha y otra, la remisión sigue sirviendo hasta que vence. Decisión abierta con el usuario.
- **`datos_demo` escribe sin tildes** la clínica («Clinica Veterinaria del Norte»), su usuario
  («Recepcion Clinica del Norte») y la remisión («Radiografia de cadera por cojera»), que el
  recorrido de la aliada busca por ese texto. Corregirlo exige cambiar a la vez la prueba, y
  `datos_demo` solo crea lo que falta: en un stack ya sembrado quedarían los dos nombres.
- **El menú de la cuenta está repetido** en `AppLayout`, `PortalLayout` y `MiClinicaPage`: un
  componente común en `src/components/` lo dejaría en un sitio.
- **Encontrado de paso, en el arreglo del CI (`perf(dashboard)`, 2026-11-16)**: las políticas de RLS
  inflan el coste estimado de las consultas y PostgreSQL las compila con JIT, que en «Mora al
  cierre» costaba más que la consulta. Se arregló reescribiendo esa consulta; apagar el JIT para
  `timu_app` aliviaría cualquier otra, pero cambia todas. Decisión abierta con el usuario.
- **Sugerencias del revisor, opcionales** (el «techo»): la lista de lo atendido con el importe que
  cubrió TIMU en su propia columna, alineado a la derecha, en lugar de dentro de la línea de texto.
