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
  navegación del celular. TIMU eligió Google Maps (informado el 2026-11-21): queda construirlo
  ([pendientes externos](../pendientes-externos.md#mapa-de-las-rutas-requisito-67-r2-pan-06)).
- ~~**Registrar los pasos de la atención desde la propia parada**~~ Resuelto en `R2-PAN-05`: la consulta es el registro de la visita y «Registrar la atención» la abre. Antes: hoy «Registrar la atención»
  lleva a la ficha del servicio. Se decide al rediseñar ese detalle en `R2-PAN-05`.
- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes): etiquetar la hora de «Por rutear» («programado 4:19 a.
  m.»), centrar la columna del médico en escritorio y capturar una ruta con una parada omitida.

### Lo que quedó de Clínica tras su cierre

- **Sugerencias del revisor, opcionales** (decididas en `DEU-28`–`DEU-70`; ver el «techo» aceptado en [deuda.md](deuda.md), que dice cuáles se hicieron, cuáles no y cuáles siguen pendientes): limitar el área de texto de la consulta a unos 75
  caracteres en escritorio, unificar la cabecera del borrador y la de la lectura, alinear a la
  izquierda los valores largos de la tabla apilable en el celular (es del componente común) y
  ~~sembrar una plantilla de consulta en `datos_demo`~~ (resuelto el 2026-11-18, `DEU-15`).

### Lo que quedó de las plantillas de consulta tras cerrar `DEU-15` (2026-11-18)

- ~~**La ventana no deja elegir el tipo de atención de una plantilla**~~ Resuelto el 2026-11-18,
  decidido con el usuario: la ventana lo pide, y la consulta de una visita ofrece las plantillas de
  su tipo y las generales (6.14).
- **La consulta guarda de qué plantilla partió** (`historias_clinicas.plantilla_codigo`, con su
  llave foránea) y además copia sus textos al crearse: editar o desactivar una plantilla no cambia
  lo ya registrado. La ficha de la plantilla dice en cuántas consultas firmadas y vigentes se usó
  (`GET /clinica/plantillas/uso`), decidido con el usuario el 2026-11-18.
- **Sin el separador «Desactivadas» del boceto ASCII** que eligió el usuario: las inactivas van
  al final con su insignia, como en Planes, Reglas y Clínicas aliadas. El revisor lo dio por
  adaptación aceptable; si el usuario lo quiere, es un subtítulo en el listado.
- ~~**Administración tiene el hueco que se cerró en Clínica**~~ Resuelto el 2026-11-18: la página
  controla su pestaña, y `?plan=`, `?regla=` y `?eventos=` abren la suya al recargar.

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
  demostración tarda 190–335 ms sin caché; contra el umbral de 2 s de Sección 8 lo dirá la prueba
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
  manda», una desparasitación hecha en visita se aplica sin peso (`6.8` lo pide opcional). Para
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
- ~~**Las reglas se editan en JSON**~~ Resuelto el 2026-11-17 (`DEU-8`): editor por campos, con lo que quedó en «Lo que quedó del editor de reglas» más abajo. Antes: se leían y se probaban en palabras, pero cambiar una condición o una
  acción era escribir el JSON del motor.
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

- **La familia no recibe el código de la remisión por ningún canal** y **una remisión emitida
  sigue sirviendo con la familia en mora, congelada o dada de baja**: el usuario los pasó al equipo
  de TIMU el 2026-11-16. Están en [pendientes externos](../pendientes-externos.md#remisiones-a-clínicas-aliadas-requisito-622),
  con lo que implica cada opción. Mientras se precisa con TIMU (es delicado), el usuario decidió
  el 2026-11-16 que la baja corte la vigencia ese día sin anularla: lo atendido hasta la baja se
  sigue reportando, también desde la pantalla de la clínica con una remisión ya vencida.
- ~~**Una remisión que vence sin usarse deja su servicio agendado para siempre**~~ Resuelto el
  2026-11-21: estado propio `vencida` (decidido con el usuario), al que la pasa la tarea diaria
  pasado el plazo para reportar (7 días, provisional), cancelando su servicio; vista «Vencidas» en
  la bandeja ([pendientes externos](../pendientes-externos.md#remisiones-a-clínicas-aliadas-requisito-622)).
  Antes: con él quedaba ocupado el cupo del beneficio y ninguna tarea lo cerraba (anularla a mano sí
  lo cancelaba). Encontrado el 2026-11-16 al revisar la baja.
- ~~**`datos_demo` escribe sin tildes**~~ Resuelto el 2026-11-16: los nombres y textos que ve el
  equipo llevan sus tildes (la clínica, su usuario, la remisión, las familias, el equipo, la
  historia de Luna), con la e2e ajustada y la base local recreada.
- ~~**El menú de la cuenta está repetido**~~ Resuelto el 2026-11-16: `MenuCuenta`
  (`src/components/`), común al panel, el portal y la clínica aliada.
- ~~**El JIT de PostgreSQL para `timu_app`**~~ Medido el 2026-11-16 con la prueba de carga completa
  (5.000 familias, 20 usuarios, 5 minutos; PostgreSQL 18.6): ninguna de las 34.212 sentencias de la
  aplicación se compiló con JIT; el único caso era «Mora al cierre», ya reescrita. Se deja
  encendido: apagarlo no cambia nada medible. Si una consulta vuelve a pasar de su umbral,
  `pg_stat_statements` dice si fue el JIT (`jit_functions`, `jit_*_time`).
- **Sugerencias del revisor, opcionales** (el «techo»): la lista de lo atendido con el importe que
  cubrió TIMU en su propia columna, alineado a la derecha, en lugar de dentro de la línea de texto.

### Lo que quedó de la encuesta y el carnet tras cerrar `R3-PUB-03`

- **El barrido contra el stack mide la encuesta solo con un enlace inexistente**: su token vive en
  la base y la traza de mensajes lo tapa. El formulario (satisfacción y seguimiento) se mide sin
  desborde ni fallos de contraste en `e2e/publicas.spec.ts`, con la API interceptada.
- **Sugerencias del revisor, opcionales** (el «techo»): una rejilla compartida entre las tablas del
  carnet para que Producto, Lote, Próxima y Aplicó caigan en la misma columna en las tres secciones,
  como en el PDF (hoy cada tabla reparte su ancho y «Dosis 1, refuerzo» o «Dra. Sara Martínez»
  parten la fila); y la línea de marca del acceso, que en la encuesta resalta «Visita en casa» sea
  cual sea la atención (viene de `R3-PUB-01`).

### Lo que quedó del registro en línea tras cerrar `R3-PUB-02`

- **Sin pasarela de pruebas de Wompi** (pendiente de TIMU), el resultado del pago y el formulario de
  la familia se revisaron con la consulta del registro simulada; el recorrido contra el stack llega
  hasta «¿Cómo quieres pagar?» sin pagar.
- **Valores provisionales nuevos**, anotados en [pendientes externos](../pendientes-externos.md):
  la carencia y las exclusiones de cada plan, el WhatsApp de contacto (ficticio en local) y las
  condiciones generales del contrato (pedirle a TIMU sus contratos reales).
- **Sugerencias del revisor, opcionales** (el «techo»): el color del plan en el filete de la ficha
  entera, no solo en la cabecera de su cobertura (un borde lateral de color está vetado por el piso
  de oficio; tendría que ser otra forma); el segundo peludo plegado en una línea que se abre al
  tocarla (con dos fichas abiertas la página mide unos 2.900 px a 390); la tarifa por número de
  peludos dicha como ganancia al añadir uno («con 2 peludos, cada plan baja»); y separar el verde
  del plan Mi Amigo Fiel del verde de la acción, que conviven llenos en la misma vista.

### Lo que quedó del editor de reglas tras cerrar `DEU-8`

- **Las plantillas de los avisos de mora no están en el catálogo** (`cuota_vencida`, `aviso_mora`,
  `aviso_congelamiento`): las reglas sembradas las citan, Administración las nombra con un nombre
  provisional («Aviso de mora · aún sin registrar») y, hasta que el equipo las registre con su texto
  aprobado en Meta, esos avisos no se envían por ningún canal ([pendientes
  externos](../pendientes-externos.md#valores-provisionales)). Es anterior a esta unidad: el editor
  lo hizo visible.
- **Lo que pueden mirar las reglas lo fija el código**: cada evento declara sus datos
  (`reglas/contextos.py`) y el editor solo ofrece esos. Un dato nuevo (la edad de la mascota, el
  barrio) o un evento nuevo de la Sección 7 (respuestas, pagos, segmentación) siguen pidiendo un
  cambio de código, aunque ya no de pantalla.
- **Condiciones de un nivel**, decidido con el usuario: una regla con grupos anidados solo se
  escribe por la API; el editor la lee en palabras y la conserva al guardar.
- **Sugerencias del revisor, opcionales** (el «techo»): un conector «y» u «o» entre condiciones,
  sobre el hilo que las separa, según la unión elegida; un hilo bajo la franja fija de la regla en
  palabras cuando el cuerpo está desplazado; y la fecha nativa «dd/mm/yyyy», que es de todo el panel.

### Lo que quedó de la portada tras cerrar `R3-PUB-04`

- **No se publica en el dominio sin lo de TIMU** ([pendientes externos](../pendientes-externos.md)):
  confirmar los valores provisionales sacados de la web vieja (misión cortada, horario del sábado
  contradictorio, aliadas vigentes, adicionales y topes), el permiso de las personas de las fotos del
  equipo, la licencia de las fotos de las piezas impresas, el WhatsApp de contacto y volver a alojar
  la política de datos, cuyo enlace actual muere con WordPress.
- **Lo que el revisor no vio**: ningún estado en movimiento, y el envío real del contacto (sus dos
  capturas se simularon para no crear un interesado en la base local; lo cubren las pruebas).
- **Sin usar del material**: el logo con animales en color y los patrones de siluetas del `.ai` y
  los recortes de perro y gato no entraron en la portada; no están en el repositorio.
- **Detalles menores que el revisor dio por aceptables**: el «·» cierra el renglón cuando un horario
  largo de la red hace salto, y a 390 la pastilla «24 horas» deja el final del nombre de la aliada
  en un renglón propio. En el celular la portada es larga, sobre todo por el comparador apilado.

