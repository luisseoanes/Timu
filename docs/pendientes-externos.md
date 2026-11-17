# Pendientes externos para cerrar requisitos

Lo que falta **fuera del código**, o detrás de un tercero o de una decisión de TIMU, para dar
por cerrada la revisión de un requisito. El código y sus pruebas ya están; esto es lo que no
se puede resolver desde el repositorio. Se tacha cuando se resuelve.

El estado de cada unidad de trabajo está en el [backlog](backlog.md); cómo funciona cada
integración, en [integraciones](integraciones.md).

## Valores provisionales

Decidido con el usuario el 2026-11-15: cada pendiente que depende de una decisión de TIMU tiene en
el código un **valor provisional** para que la plataforma funcione entera mientras tanto. **La
regla:** un valor provisional sigue **PENDIENTE** aunque funcione, y ninguno se tacha ni se marca
resuelto hasta que se informe explícitamente que TIMU dio el valor oficial. Al recibirlo se cambia
el código, se anota la fecha y quién lo confirmó, y solo entonces se tacha.

| Pendiente de TIMU | Valor provisional | Dónde vive | Estado |
| --- | --- | --- | --- |
| Precios de los planes | Colita Feliz $35.500, Mi Amigo Fiel $69.000 y Amigos por Siempre $98.000 al mes por un peludo (los del manual y de la página de cada plan), con su escala por número de peludos y los periodos largos | `backend/scripts/seed.py` (`PLANES_TIMU`); desplegado, el administrador los da de alta | PENDIENTE |
| Coberturas, topes y frecuencias de cada plan | Las del plegable 2026 donde lo dice: consultas a domicilio al mes, una en Mi Amigo Fiel y dos en Amigos por Siempre; la hospitalización, como atención en clínica aliada, al 40 % en Mi Amigo Fiel y al 80 % en Amigos por Siempre. Lo que no dice (Colita Feliz, vacunas, desparasitación, controles, orientación virtual y el cupo de la atención en clínica aliada), los cupos de prueba de la siembra (decidido con el usuario el 2026-11-16) | `backend/scripts/datos_demo.py` (`BENEFICIOS` y `DEL_PLEGABLE`); desplegado, el administrador los da de alta | PENDIENTE |
| Términos y condiciones publicables | Ninguno: la plataforma no enlaza un documento de términos que no existe | — | PENDIENTE |
| Periodo de carencia del peludo que se agrega con contrato vigente | Sin carencia; no se permite con el contrato en mora ni congelado | `afiliaciones/altas.py` | PENDIENTE |
| Cobro del alta de un peludo desde el panel | No cobra el periodo en curso: el valor nuevo corre desde la siguiente cuota no emitida | `cartera/contratos.py` | PENDIENTE |
| Qué plan recomienda el bot comercial | Mi Amigo Fiel, el plan principal según el manual (sección 4), para cualquier ciudad, especie y número de peludos | Reglas `plan.recomendacion` (`reglas/datos.py` y su migración) | PENDIENTE |
| Proveedor de la IA | Mientras se migra a Gemini, `claude-haiku-5-5`, el económico de la comparativa | `IA_MODELO` (`core/config.py`, `.env.example`) | PENDIENTE |
| Plantillas de WhatsApp aprobadas en Meta | Sin plantilla aprobada, el enlace de cada mensaje sale solo por correo. En la demostración local, `datos_demo` y `operacion_demo` dan por aprobadas las suyas (`recordatorio_renovacion` y `encuesta_satisfaccion`) para recorrer campañas y encuestas | `comunicaciones` | PENDIENTE |
| Mapa de las rutas | Sin mapa: cada parada abre la navegación del celular («Cómo llegar») | `rutas` | PENDIENTE |
| Ventana de la bandeja de preventivos | 30 días | `VENTANA_BANDEJA_DIAS` (`preventivos/service.py`) | PENDIENTE |
| Fotos originales para las páginas públicas | Las páginas públicas van sin fotos | — | PENDIENTE |
| Sandbox de Wompi de TIMU | No admite valor provisional: sin credenciales no hay prueba de punta a punta | — | PENDIENTE |
| Cómo recibe la familia el código de una remisión | Ninguno: la plataforma no lo envía ni lo muestra en el portal; se lo dice el equipo ([detalle](#remisiones-a-clínicas-aliadas-requisito-622)) | `aliadas/service.py` (`emitir`) | PENDIENTE |
| Si una remisión emitida sigue sirviendo cuando la familia cae en mora, se congela o se da de baja (**delicado**) | La baja o la cancelación del contrato cortan su vigencia ese día: lo atendido hasta entonces se sigue reportando y cobrando (decidido con el usuario el 2026-11-16, mientras lo precisa TIMU). La mora y la congelación la dejan servir hasta que vence, 30 días después de emitirse ([detalle](#remisiones-a-clínicas-aliadas-requisito-622)) | `REMISION_VIGENCIA_DIAS` (`core/config.py`); `aliadas/service.py` (`cortar_vigencia_al_cancelar`, `reportar_atencion`) | PENDIENTE |

## Requisito 6.1 (con el 6.12)

El código está completo (`F1-FAM-06` a `F1-FAM-09`, `F1-AFI-01`), pero la revisión no se
cierra hasta validar el registro en línea contra los terceros reales:

- **Prueba de punta a punta en el sandbox de Wompi de TIMU.** Registro en línea, pago en
  el checkout de pruebas, evento firmado que llega a la API por un túnel, formulario
  posterior y, al final, familia, contrato y acceso al portal. Comprueba lo que hoy solo se
  prueba contra dobles: la firma de integridad, la URL de vuelta y el pago rechazado.
  Bloqueada hasta tener las credenciales del sandbox de TIMU (llave pública, de integridad
  y de eventos) y el túnel para los eventos. En la misma sesión se comprueba lo que la
  documentación de Wompi no aclara sobre el cierre de lo que no se paga:
  - que el checkout acepta la firma de integridad **con** la fecha de `expiration-time`
    (`<referencia><monto><moneda><fecha><secreto>`). El ejemplo de la documentación
    conserva la firma sin fecha, así que no sirve de prueba.
  - qué pasa al vencer el enlace a las 24 h: si el checkout rechaza el pago y si Wompi
    emite algún evento. La documentación solo menciona un contador.
  - que, tras un rechazo, el pago con la referencia nueva de «Intentar de nuevo» se aprueba
    y completa el registro.
  - el reintento propio de Wompi (3 minutos, misma referencia): un aprobado con la
    referencia anterior debe pagar el registro y anular el intento nuevo. Si se pagan los
    dos, debe quedar la tarea «Pago doble de un registro en línea».
  - un evento aprobado que llega después del cierre de las 48 h debe dejar la tarea «Pago
    recibido de un registro en línea ya cerrado» y no afiliar.
  - qué datos del pagador trae de verdad la transacción de Wompi. El borrado de los seis
    meses quita `customer_email`, `customer_data`, `shipping_address` y `billing_data` del
    evento y vacía el `payload` del pago; si llegan con otros nombres, hay que añadirlos a
    `anonimizar_registros_abandonados()` (migración `0035`).
- **Plantilla `completar_afiliacion` aprobada en Meta** antes de producción. Sin ella, el
  enlace del formulario (al pagar y en el recordatorio de las 24 h) solo llega por correo.
  Se resuelve con la integración de la cuenta de WhatsApp Business de TIMU.
- **Agregar un peludo con contrato vigente desde el portal.** Implementado el 2026-11-10
  (migración `0037`, `afiliaciones/altas.py`, «Agregar un peludo» en el portal):
  - la familia elige ficha y plan y ve el valor nuevo del contrato;
  - paga por Wompi lo que queda del periodo en curso con la tarifa nueva, más la diferencia
    de las cuotas siguientes que ya se emitieron con el valor anterior (salen 5 días antes);
  - el peludo entra al contrato cuando se aprueba el pago;
  - lo que no se paga se cancela a las 48 h;
  - el registro público avisa que un afiliado agrega su peludo desde el portal.

  Pendiente de TIMU, con valores provisionales en el código: sin periodo de carencia para
  el peludo nuevo, y no se permite con el contrato en mora ni congelado. En el sandbox de
  la fase 4 se comprueba el pago del alta de punta a punta y el monto mínimo que acepta
  Wompi: un alta el penúltimo día del periodo cobra muy poco.
- **El alta de un peludo desde el panel no cobra lo del periodo en curso.** El equipo lo da
  de alta con su plan y el valor nuevo corre desde la siguiente cuota no emitida: ni se
  prorratea el periodo en curso ni se ajusta una cuota que ya se emitió. Es la regla
  anterior al alta desde el portal y está por decidir con TIMU si se iguala.
- ~~**Hueco de la Ley 1581 en `anonimizar_familia()`**~~ Resuelto el 2026-11-10 (migración
  `0036`, tras una auditoría columna por columna). Ahora también borra:
  - los datos del pagador que guardó la pasarela;
  - la IP y el navegador de las sesiones y de la evidencia de aceptación;
  - las coordenadas de la casa en las paradas de ruta y en la caché de distancias;
  - el PDF de las fórmulas;
  - los mensajes de la IA comercial;
  - los mensajes y las tareas del registro en línea, que ahora pasan a la familia al
    completarlo.

  En el texto libre clínico y operativo (historias, fórmulas, servicios, pendientes, tareas,
  notas de pago) reemplaza las menciones exactas a la familia (nombres, dirección,
  documento, correos, teléfonos) por `[anonimizado]`, y conserva el resto. Una mención
  indirecta, como un apodo o solo el nombre de pila, no se detecta. La lista de bajas de
  comunicaciones conserva el teléfono a propósito: impide volver a escribirle.
  `test_anonimizar_no_deja_datos_personales` recorre ahora todas las tablas. Pendiente: las
  familias anonimizadas antes de la `0036` no se reprocesan; si producción tiene alguna, hay
  que limpiarla a mano.

## Inteligencia artificial: pasar a Gemini (`F4-IAA-01` a `F4-IAA-04`)

Decidido el 2026-11-10, al preparar el documento de costos para TIMU: la IA se usará sobre
un modelo económico de Gemini (recomendado `gemini-3.1-flash-lite`, en la capa paga). Falta:

- **Adaptar el conector.** Hoy `backend/app/integrations/claude.py` habla con la API de
  Anthropic (`ANTHROPIC_API_KEY`, `IA_MODELO`), y el cálculo de costo de cada consulta
  (`claude.costo`) asume sus precios. Los prompts versionados, el presupuesto mensual y los
  casos de evaluación de `modules/ia` no dependen del proveedor.
- **Solo la capa paga.** La gratuita de Gemini usa los datos para mejorar productos de
  Google: con datos personales o clínicos choca con la Ley 1581.
- **Mientras tanto,** `IA_MODELO` vale por defecto `claude-haiku-5-5`, el económico de la
  comparativa: es el valor provisional (ver «Valores provisionales»). Antes del 2026-11-15 era
  `claude-opus-5-5`, el más caro.

A este volumen (unas 300 consultas al bot y 14 borradores al mes) la diferencia entre los
modelos económicos es de centavos al mes ([costos](costos-infraestructura.md)): la decisión
pesa por calidad de los borradores, tratamiento de los datos y trabajo de integración.

## Remisiones a clínicas aliadas (requisito 6.22)

Apuntado el 2026-11-16, al cerrar `R3-ALI-01` (el espacio de la clínica aliada). Las dos cosas son
decisiones de negocio de TIMU; el código está listo para cualquiera de las respuestas.

**1. La familia no recibe el código de su remisión.** El equipo emite la remisión en Aliadas y la
clínica la valida con su código (`F2-ALI-03`): el código es la prueba de que la familia se
presentó, y por eso la clínica no ve las remisiones por usar (decidido con el usuario). Pero
ningún canal se lo da a la familia: emitirla no envía ningún mensaje y el portal no la muestra.
Hoy se lo dice el equipo a mano, por fuera de la plataforma, y el requisito 6.22 pide que todo el
proceso quede registrado. TIMU tiene que decidir por dónde le llega:

- por WhatsApp al emitirla (necesita una plantilla aprobada en Meta, como las demás);
- en el portal, en la ficha del peludo o en sus citas;
- o las dos.

**2. Qué pasa con una remisión emitida si la cartera de la familia cambia. Es delicado** (lo
subrayó el usuario): toca a la vez lo que TIMU paga, la relación con las clínicas aliadas y la
atención de un peludo que puede estar hospitalizado. Sigue **PENDIENTE** de resolverse con TIMU
aunque ya haya un comportamiento provisional. Al emitirla se valida
el plan vigente, la cartera al día y el beneficio disponible (`F2-ALI-02`). Después no se vuelve a
mirar nada: la clínica la valida y reporta la atención hasta que vence, 30 días después. Esto
implica que:

- **Si la familia cae en mora o su plan se congela** después de la emisión, la clínica la atiende
  y TIMU le paga a la clínica su parte (hasta el tope del convenio: $ 200.000 en la radiografía de
  la demostración; en una hospitalización, el 40 % o el 80 % según el plan). El portal, en cambio,
  ya no le deja a esa familia agendar nada: la misma familia tiene cobertura en la aliada y no la
  tiene en TIMU.
- **Si la familia se da de baja** (o se cancela su contrato): hasta el 2026-11-16 la remisión
  seguía sirviendo el resto de su vigencia y TIMU la pagaba aunque la familia ya no fuera de TIMU.
  **Provisional desde ese día** (decidido con el usuario mientras lo precisa TIMU): la baja corta
  la vigencia ese mismo día. No la anula: una atención hecha hasta la baja y reportada después se
  sigue cobrando, y la clínica la reporta desde su pantalla con «Reportar una atención hecha hasta
  el …». Lo atendido después de la baja ya no.
- **Por el otro lado, la remisión es la autorización con la que la clínica atiende.** La atención
  se reporta después de hacerla, así que comprobar la cartera al reportar es el peor momento: la
  clínica ya atendió y TIMU le negaría el pago. Si se comprueba algo, tiene que ser al validar el
  código, antes de atender, y la clínica tiene que leer por qué no sirve.

Opciones para TIMU:

- **Compromiso firme**: una remisión emitida se honra hasta que vence, como una autorización. El
  riesgo se acota con la vigencia (hoy 30 días) y el tope de cada convenio.
- **Condicionada a seguir al día**: al validar, una familia en mora o congelada no tiene cobertura
  y la clínica lo ve antes de atender; la familia recibe el aviso de pagar.
- **Intermedia** (recomendación de Claude, y lo provisional de hoy): la baja o la cancelación del
  contrato cortan la vigencia de las remisiones por usar ese día, y la mora o la congelación las
  dejan servir hasta que vencen, porque la familia sigue siendo de TIMU y puede ponerse al día.

Lo que TIMU tiene que confirmar: si la baja corta la vigencia (lo provisional) o anula del todo;
qué pasa con la mora y la congelación; si la vigencia de 30 días es la que quiere; y si una
atención hecha antes de la baja y reportada después se paga siempre.

## Recomendación de plan del bot comercial (`F1-PLA-04`, `F3-COM-03`)

El bot toma los precios del catálogo de planes, el mismo con el que cobra el registro: eso
está al día. Le falta el criterio. Las reglas `plan.recomendacion` que carga
`backend/app/modules/reglas/datos.py` recomiendan `familiar` e `individual`, planes que ya
no existen, así que siempre cae en «el plan de menor valor que cubre a todas las mascotas»
y propone un solo plan para todos los peludos. TIMU tiene que decir qué plan recomendar
según ciudad, especie y número de peludos. Con eso se ajustan las reglas en
Administración → Reglas y se reemplazan las de `datos.py`, que solo se cargan en una base
nueva.

## Mapa de las rutas (requisito 6.7, `R2-PAN-06`)

El requisito pide «visualizar usuarios/servicios en un mapa». Las rutas se planean con
distancias reales y cada parada abre la navegación del celular («Cómo llegar», con las
coordenadas que usó el optimizador), pero el panel no dibuja un mapa: decidido con el usuario el
2026-11-12 para no meter una dependencia y un proveedor de teselas sin acordarlos. Para cerrarlo
hace falta que TIMU elija proveedor y presupuesto: Google Maps JavaScript (de pago por carga,
con la misma cuenta que ya factura la matriz de distancias de `F2-RUT-02`) o teselas de
OpenStreetMap con un proveedor que admita uso comercial. Con eso, el mapa entra como unidad
propia.

## Marca e identidad ([manual de marca](manual-de-marca.md))

El 2026-11-11 llegó el material gráfico de la marca: el manual original de la diseñadora
(2021, con su fuente de 40 páginas en Illustrator), el logo en vector, las tipografías,
los patrones y las piezas impresas (carnet de vacunación, plegable 2026, pendón y piezas de
mostrador). **Ese material no vive en el repositorio** (pesa casi 400 MB): está en la carpeta
de marca que compartió TIMU. En el repositorio solo está lo que ya se usa, con la receta para
regenerarlo (`frontend/src/assets/marca/README.md`, `backend/app/recursos/marca/README.md`).
Lo que queda en la carpeta y servirá más adelante:

- **Patrones** de siluetas de animales y cruces, en cada color de la marca: en vector en el
  manual fuente (`Manual de marca TIMU.ai`, las últimas láminas) y en PNG pequeños en
  `Aplicativos TIMU/`. Para las páginas públicas y de venta (`R3-PUB-02`, la portada).
- **Variantes del logo** con perro y gato y con animales grandes, y las versiones en blanco y
  en negro: en el manual fuente y en PNG en `Aplicativos TIMU/`.
- **Plegable 2026**: el contenido de los tres planes (beneficios y descuentos) y los datos de
  contacto y sedes, para el registro en línea y la portada.
- **Carnet de vacunación impreso**: la referencia del carnet en PDF (ya aplicada) y del
  carnet en pantalla (`R2-PAN-08`, `R3-POR-01`).
- **Fotos** de perros y gatos recortados (en los PDF de las piezas).

Lo que resuelve y lo que deja abierto:

- **Logo en vector: recibido e integrado.** `Marca TIMU.ai` trae el logo a color en sus tres
  versiones (con las siluetas bajo el lema, con perro y gato, y con animales grandes). La
  plataforma usa la primera, completa o compacta, a color o en blanco
  (`frontend/src/assets/marca/`).
- **GeosansLight: recibida y en uso.** Llegan la regular y la oblicua (Manfred Klein, 2004),
  con todos los caracteres del español. El archivo no declara licencia; TIMU confirmó el
  2026-11-11 que la tiene. La plataforma la sirve desde el proyecto en los títulos de 20 px o
  más (manual, sección 12).
- **Minimal, la tipografía del logotipo, no sirve para la interfaz:** su ficha dice
  «Copyright info pending», solo permite incrustarla para vista e impresión y le faltan ¿, ¡
  y €. No hace falta: el logo va en vector.
- **Colores: resuelto.** El texto del manual de 2021 da un azul petróleo y un naranja claro
  que no usa ni su propio logo ni ninguna pieza. TIMU confirmó el 2026-11-11 que valen los
  del logo, los de la plataforma. El naranja se ajustó al de las exportaciones del logo
  para pantalla (`#D48200`, antes `#D68A11`).
- **Servicios fúnebres: no se gestionan.** El plegable y el pendón venden «salud y servicios
  fúnebres», y el servicio fúnebre es beneficio de los tres planes, pero no está en el
  documento de requerimientos. Decidido con TIMU el 2026-11-11: de momento la plataforma se
  queda en los requerimientos.
- **Fotografías: son de TIMU.** TIMU confirmó el 2026-11-11 que las fotos de perros y gatos
  de las piezas son propias y que puede usarse cualquiera del banco de fotos que compartió.
  Para las páginas públicas faltan los originales en alta resolución; las de las piezas
  vienen recortadas e incrustadas en los PDF.
- **Recursos gráficos para la portada pública (index).** Los patrones, las fotos y el
  contenido del plegable son ese material; la portada se construye con ellos. El resto de páginas públicas no la esperan ([hoja de ruta del
  rediseño](hoja-de-ruta-rediseno.md#fuera-de-alcance)).

## Web pública (timu.com.co) frente al manual de marca

Revisada el 2026-11-10. Son contenidos de la web de TIMU, no de la plataforma, pero chocan
con el manual y con lo que la plataforma muestra. Los resuelve TIMU; mientras tanto, la
plataforma sigue el manual y toma planes, precios y coberturas del catálogo de la API:

- **Se presenta como seguro.** El inicio dice «Somos especialistas en salud veterinaria y
  especialistas en seguros», y el manual prohíbe hablar de «seguro para mascotas».
- **Usa «ilimitado»** en las coberturas de los tres planes (chat, procedimientos, cirugía,
  exámenes…), una palabra que el manual también prohíbe.
- **Precios que no coinciden.** `/planes/` publica Colita Feliz $29.200, Mi Amigo Fiel
  $57.200 y Amigos por Siempre $81.000. El inicio y la página de cada plan publican $35.500,
  $69.000 y $98.000. El catálogo de la plataforma tiene que coincidir con lo que TIMU confirme.
- **Coberturas contradictorias y sin términos publicados.** La hospitalización de Mi Amigo
  Fiel sale al 80 % en el inicio y al 40 % en su página. Las consultas aparecen como «1 vez»
  o «2 veces» en el inicio y «al mes» en las páginas de los planes. Todo dice «Aplica términos
  y condiciones», pero la web no publica ningún documento de términos.
- **El plegable 2026 resuelve parte de lo anterior:** la hospitalización de Mi Amigo Fiel es
  al 40 % (al 80 % en Amigos por Siempre) y las consultas son «al mes» (una en Mi Amigo Fiel,
  dos en Amigos por Siempre). No trae precios: los precios siguen sin confirmar, aplazado por
  TIMU el 2026-11-11.
