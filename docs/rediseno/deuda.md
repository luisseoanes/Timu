# Rediseño del front: deuda decidida y techo del revisor

Anexo de la [hoja de ruta del rediseño](../hoja-de-ruta-rediseno.md), separado de ella el
2026-11-16 para que la hoja se lea rápido. Aquí está, entera, la deuda que el usuario decidió el
2026-11-15 (`DEU-1` a `DEU-70` y `DEU-E`), con su estado, y el «techo» del revisor final de cada
superficie. Lo que sigue pendiente está resumido en la hoja, en «Dónde se retoma». Cuando una
deuda cambia de estado, se actualiza aquí.

### Deuda decidida con el usuario (2026-11-15)

El usuario respondió de una vez la deuda acumulada hasta `R3-PUB-01`. Cada decisión lleva el
número de la lista que contestó (`DEU-<n>`) y dice dónde se hace: **ahora** es el lote de deuda que
sigue a `R3-PUB-01`, antes de `R3-PUB-02`; el resto, en la unidad que se nombra. Lo hecho se marca
**Hecho** con su fecha y lo que no se hace, **No**, con el motivo. Ninguna fila se borra: así se ve
qué quedó decidido. Los «Lo que quedó» de cada superficie (más abajo) son el detalle de origen.

| ID | Qué | Decisión | Dónde | Estado |
| --- | --- | --- | --- | --- |
| `DEU-1` | Las series 1 y 2 del manual no se distinguen sin ver el rojo y el verde | El manual pasa a verde, azul, naranja y marino | ahora | Hecho (2026-11-15): el manual, los tokens, `DESIGN.md` y el gráfico del Inicio, que usa la 1 y la 2 |
| `DEU-2` | El portal no ofrece la consulta en la clínica que el backend permite | El portal la ofrece y la API dice qué puede agendar, cambiar y cancelar la familia | ahora | Hecho (2026-11-16): `motivo_sin_agendar` y `tipos_agendables` en el plan, y `puede_cambiar`, `puede_cancelar` y `sin_cambios` en cada cita; el portal agenda también en la clínica |
| `DEU-3` | La visita preventiva del portal no se enlaza con ningún preventivo | El portal agenda preventivos concretos, como la bandeja | ahora | Hecho (2026-11-16): `GET /portal/preventivos` y `POST /portal/preventivos/{id}/visita`; agendarlo es la autorización de la familia (migración `0047`, RLS) |
| `DEU-4` | La desparasitación hecha en visita se aplica sin peso | Campo opcional en los pasos del catálogo; el peso en «Aplicación» | ahora | Hecho (2026-11-16): los pasos ganan `opcionales` con nombre y tipo; la desparasitación pide el peso, que va al carnet (migración `0046`) |
| `DEU-5` | «Por autorizar» con la llave solo en Preventivos | La llave en el mapeo común (`lib/estados.ts`): también en Servicios | ahora | Hecho (2026-11-15): la llave en `lib/estados.ts`, la fila y la ficha del servicio |
| `DEU-6` | La clínica aliada entra por «Equipo TIMU» | Renombrarla «Equipo y aliadas» (decidido con el usuario el 2026-11-16) | ahora | Hecho (2026-11-16) |
| `DEU-7` | La pantalla del enlace no dice cuánto dura | La API da la vigencia y la pantalla la dice | ahora | Hecho (2026-11-15): `expira_en` en `POST /auth/enlace` y «Este enlace sirve hasta…» |
| `DEU-8` | Las reglas se editan en JSON | Editor por campos | ahora | Pendiente |
| `DEU-9` | Pasar una cuenta a o desde clínica aliada | **No**: se crea otra cuenta, como ahora | — | No |
| `DEU-10` | Las plantillas de WhatsApp enseñan su código de Meta | Campo «nombre» en el catálogo de plantillas | ahora | Hecho (2026-11-16): `titulo` en las plantillas (migración `0044`); reglas, campañas y mensajes lo dicen, con el código debajo |
| `DEU-11` | Textos guardados sin tildes (catálogos y reglas sembradas) | Migración de datos que los corrige | ahora | Hecho (2026-11-16): `datos.py` con tildes y migración `0045` para lo sembrado que nadie editó. Las ciudades y los departamentos («Bogota», «Medellin»), que son la clave por la que se guardan, también: decidido con el usuario y hecho el 2026-11-16 (migración `0048`, que propaga el nombre por las llaves foráneas y corrige los JSON de segmentos, campañas y reglas; `ciudad_valida` acepta el nombre con o sin tildes) |
| `DEU-12` | Comercial no muestra correos ni llamadas | **No**: fuera de alcance | — | No |
| `DEU-13` | En el celular, la línea de Familias no se abre en «hoy» | Se arregla (es un defecto) | ahora | Hecho (2026-11-15): en vertical, tres o más vencidas van en un grupo rojo con «Ver cada una» |
| `DEU-14` | `datos_demo` sin una familia de portal al día | Siembra gruesa: uno o dos meses de operación que recorran todos los casos y todas las rutas | ahora | **Pendiente de terminar** (el usuario lo confirmó el 2026-11-16: hay que completar lo que falta, al final de esta celda). Hecho el 2026-11-16: el portal de Jorge Ramírez al día, las coberturas del plegable en los planes y el núcleo de la operación, `scripts/operacion_demo.py` (decidido con el usuario: se crea por la API y luego se corren las fechas al pasado, en un comando aparte que el CI corre tras la e2e del stack). Siembra ocho semanas: familias en cada estado de cartera (al día, en mora, congelada, anual, trimestral por renovar, nueva y dada de baja) con sus pagos fechados, 38 rutas pasadas en Bogotá y Medellín con 100 visitas, consultas firmadas, paradas omitidas y servicios cancelados, preventivos aplicados y vencidos y encuestas respondidas. También (2026-11-16): el embudo comercial en el tiempo (sin «afiliado»: lo pone la afiliación en línea al aprobarse el pago, y la pasarela de pruebas sigue pendiente), tareas cerradas y vencidas (también las que deja una calificación baja), remisiones atendidas, anulada, vencida y por usar, orientaciones virtuales cerradas y una campaña enviada. Solo se visita o se remite a quien ya estaba afiliado ese día. **Falta, y se termina antes del cierre (`R4`)**: visitas de otros tipos en la operación de `operacion_demo` (vacunas y desparasitaciones en ruta, con la aplicación del preventivo; controles y consultas en clínica, que necesitan franjas de esa modalidad), y `DEU-15` |
| `DEU-15` | Sin plantilla de consulta en `datos_demo` | **Opción 4, decidida por el usuario el 2026-11-16**: `datos_demo` crea por la API dos o tres plantillas de prueba («Control general», «Otitis externa», «Gastroenteritis leve»), un recorrido e2e abre una consulta, elige una y comprueba que rellena los campos, y `operacion_demo` usa esas plantillas en parte de sus consultas. **Además, las plantillas deben poder editarse**: hoy en Clínica → «Plantillas de consulta» solo se crean (médico y administración, `POST /clinica/plantillas`); falta editarlas y activarlas o desactivarlas (sin borrarlas: nada de negocio se borra). El sitio con más lógica es esa misma pestaña de Clínica, para los mismos perfiles, porque es contenido clínico y lo mantiene el equipo médico | otra sesión | **Pendiente (TODO)**: decidido, sin empezar; se hace en otra sesión, con la plantilla editable incluida |
| `DEU-16` | La prueba de la foto deja un PNG de 1×1 en la mascota de Ana | Que no ensucie los datos | ahora | Hecho (2026-11-16): la prueba quita la foto al terminar si la mascota no tenía una |
| `DEU-17` | El barrido responsive no mide 900 px | Se añade el ancho | ahora (adelanta parte de `R4-CIE-01`) | Hecho (2026-11-16): ninguna ruta falla a 900 px |
| `DEU-18` | El espaciado de la etiqueta en mayúsculas no tiene token | Un token y una sola medida | ahora | Hecho (2026-11-15): `--tracking-etiqueta`, y la guarda de tokens lo exige |
| `DEU-19` | Radios escritos a mano | Pasan a tokens | ahora | Hecho (2026-11-15): `--r-fino` y `--r-barra`, y la guarda de tokens rechaza un radio a mano |
| `DEU-20` | Cortes a 899 y a 900 px mezclados | Todo a 899 | ahora | Hecho (2026-11-15) |
| `DEU-21` | `--sombra-1` y `--sombra-2` valen `none` | Se retiran | ahora | Hecho (2026-11-15) |
| `DEU-22` | El portal copia cuatro reglas del backend | Lo cierra `DEU-2` | ahora | Hecho (2026-11-16): con `DEU-2` |
| `DEU-23` | El panel copia qué tipo de servicio agenda cada preventivo | La API lo dice en cada preventivo | ahora | Hecho (2026-11-15): `tipo_servicio_codigo` en cada preventivo |
| `DEU-24` | Contrato, fórmula y comprobante en PDF sin marca | Usan `marca_pdf` | ahora | Hecho (2026-11-15): piezas comunes en `marca_pdf`; además dicen cada cosa en palabras |
| `DEU-25` | Los campos con icono del acceso miden 48 px | 48 px es la norma del acceso | ahora (documentación) | Hecho (2026-11-15): `DESIGN.md` lo recoge en Inputs |
| `DEU-26` | Pasarela sin recuento ni vista en la URL, casos de la IA en JSON, `style` en Reportes | Se arreglan | ahora | Hecho (2026-11-15): recuentos y vista en la URL, casos en palabras (`esperado_texto`) y sin `style`; de paso, la API rechaza un caso que el evaluador no entiende |
| `DEU-27` | `.impeccable/design.json` va por detrás de `DESIGN.md` | Se completa en el cierre | `R4-CIE-03` | Pendiente |
| `DEU-28`–`DEU-70` | El «techo» del revisor en cada superficie | Como lo recomendó Claude: sí a todo salvo 28, 29, 30, 38, 39, 43, 44, 65, 68, 69 y 70 (detalle abajo) | ahora | Hecho (2026-11-16) |
| `DEU-E` | Lo que decide TIMU | Valor provisional en el código para cada uno, pero **todos siguen pendientes** hasta que TIMU confirme el valor oficial ([pendientes externos](../pendientes-externos.md#valores-provisionales)) | — | Pendiente de TIMU |

**Encontrado al cerrar este lote y resuelto el mismo día:** la prueba de Comercial «registra un
interesado sin enviar los campos vacíos y abre su ficha» fallaba de vez en cuando en
`npm run verificar`. La causa era real, no de la prueba: `useMutacion` de Comercial devolvía en su
`onSuccess` la promesa de recargar todo Comercial, y React Query la espera antes de llamar al
`onSuccess` de cada `mutate`; la ventana del interesado nuevo seguía «Guardando…» hasta que se
recargaba todo. Ya no se espera, y la prueba lo fija con una recarga que no responde. Portal,
Clínica, Tareas y Aliadas siguen esperando la recarga a propósito (evita un parpadeo y no retiene
ninguna ventana que abra otra cosa); si alguna llega a hacerlo, se cambia igual.

El «techo» aceptado, por superficie (los números son los de la lista). Hecho el 2026-11-16 salvo
lo que se marca como pendiente:

- **Rutas:** 31 etiquetar la hora de «Por rutear» («agendado a las …») · 32 centrar la columna
  del médico en escritorio · 33 capturar una ruta con una parada omitida (la siembra de `DEU-14`
  deja seis).
- **Clínica:** 34 área de texto de unos 75 caracteres en escritorio · 35 unificar la cabecera del
  borrador y la de la lectura (mismas piezas: título, distintivo del estado y modalidad; el tamaño
  del título sigue al contexto. Composición elegida sin preguntar: se cambia si el usuario prefiere
  otra) · 36 valores largos de la tabla apilable alineados a la izquierda en
  el celular.
- **Portal:** 37 la flecha de las listas como chevron de trazo · 40 el cuadrado del plan en Pagos ·
  41 icono propio para «Atendida».
- **Servicios:** 42 ficha fija al desplazar · 45 menos blanco en la ficha vacía · 46 foco en
  «Familia» al abrir «Agendar servicio».
- **Cartera y Preventivos:** 47 franjas de agendar en tres columnas iguales (solo en la ventana de
  preventivos: las de «Agendar servicio» dicen el rango y se partirían) · 48 «Escribir» en todos los
  grupos · 49 estrechar la columna del preventivo · 50 que el separador no parta el documento y la
  ciudad en el carnet a 390.
- **Comercial y Campañas:** 51 desvanecido o «mensajes anteriores» en la conversación recortada ·
  52 «Recibido» y «Enviado» con algo más que la palabra, cuerpos a dos líneas · 53 fichas de cifra
  de Encuestas más pequeñas · 54 «Destinatarios en CSV» alineado y oculto en un borrador · 55
  «Interesados» que no repita el recuento de «Abiertos» · 56 «A quién le llega» con más ancho a
  1440 · 57 un vacío de Segmentos que oriente.
- **Aliadas:** 58 etiquetas de la liquidación sin partir · 59 la ficha de la clínica lleva a sus
  remisiones atendidas y anuladas (la bandeja filtra por clínica) · 60 el total en un `th` · 61
  sin la columna de acciones vacía.
- **Administración:** 62 tarifas en 2×2, o en una línea si son iguales · 63 beneficios apilados en
  el celular · 64 la barra del presupuesto junto a «Gastado».
- **Común:** 66 la tira de pestañas a 390 indica que se desplaza.
- **Acceso:** 67 la línea se dibuja hasta «Hoy» al cargar (un tramo tras otro y la marca al
  final, `--duracion-dibujo`), respetando `prefers-reduced-motion`.
- **No:** 28 estaciones de 34 px, 29 etiquetas cuadradas y 30 paneles sin radio en Familias (el
  panel es denso y contradicen `DESIGN.md`); 38 estaciones en citas y pagos y 39 la marca de Hoy en
  la cita en camino (son otra composición); 43 la marca de «ahora» en Servicios y 44 las franjas
  como rejilla semanal (trabajo grande); 65 «Desactivar» en neutro (lo destructivo va en plano
  rojo); 68 «Afiliación» que se enciende al activar (retrasa la entrada), 69 el título alineado con
  la frase y 70 estaciones equidistantes a 900 (volvería a partir el rótulo).
