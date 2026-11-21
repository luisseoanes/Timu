# Pendientes externos para cerrar requisitos

Lo que falta **fuera del código**, o detrás de un tercero o de una decisión de TIMU, para dar
por cerrada la revisión de un requisito. El código y sus pruebas ya están; esto es lo que no
se puede resolver desde el repositorio. Se tacha cuando se resuelve.

Lo que falta **dentro** del código está al final, en [lo que falta en el
código](#lo-que-falta-en-el-código); cómo funciona cada integración, en
[integraciones](integraciones.md). Los requisitos se citan por su número en el [documento de
requerimientos](documento-requerimientos-funcionales.md), la única fuente de verdad.

Lo que TIMU tiene que hacer para cada integración (Meta, Wompi, Google, Workspace, el dominio) está
paso a paso en el documento para la cliente, [integraciones para TIMU](integraciones-timu.md); las
decisiones y lo que falta de nuestro lado, en [integraciones](integraciones.md#decisiones-del-2026-11-16).

## Valores provisionales

Decidido con el usuario el 2026-11-15: cada pendiente que depende de una decisión de TIMU tiene en
el código un **valor provisional** para que la plataforma funcione entera mientras tanto. **La
regla:** un valor provisional sigue **PENDIENTE** aunque funcione, y ninguno se tacha ni se marca
resuelto hasta que se informe explícitamente que TIMU dio el valor oficial. Al recibirlo se cambia
el código, se anota la fecha y quién lo confirmó, y solo entonces se tacha.

| Pendiente de TIMU | Valor provisional | Dónde vive | Estado |
| --- | --- | --- | --- |
| Precios de los planes | Colita Feliz $35.500, Mi Amigo Fiel $69.000 y Amigos por Siempre $98.000 al mes por un peludo (los del manual y de la página de cada plan), con su escala por número de peludos y los periodos largos | `backend/scripts/seed.py` (`PLANES_TIMU`); desplegado, el administrador los da de alta | PENDIENTE |
| Coberturas, topes y frecuencias de cada plan | Las del plegable 2026 donde lo dice: consultas a domicilio al mes, una en Mi Amigo Fiel y dos en Amigos por Siempre; la hospitalización, como atención en clínica aliada, al 40 % en Mi Amigo Fiel y al 80 % en Amigos por Siempre. Lo que no dice (Colita Feliz, vacunas, desparasitación, la consulta en la clínica, controles, orientación virtual y el cupo de la atención en clínica aliada), los cupos de prueba de la siembra (decidido con el usuario el 2026-11-16; la consulta en la clínica, cuatro al año, el 2026-11-18 con `DEU-14`) | `backend/scripts/datos_demo.py` (`BENEFICIOS` y `DEL_PLEGABLE`); desplegado, el administrador los da de alta | PENDIENTE |
| Términos y condiciones publicables | Ninguno: la plataforma no enlaza un documento de términos que no existe. El catálogo de planes tiene ya el campo para enlazarlo (`terminos_url`, solo https; R3-PUB-02), vacío | — | PENDIENTE |
| WhatsApp de contacto que ven la portada y quien se afilia (registro en línea, pago rechazado) | `+573000000000`, **ficticio**, solo en local: lo siembra `datos_demo`, que se niega a correr fuera de `ENVIRONMENT=local`; desplegado, el campo empieza vacío y, vacío, la portada y el registro no ofrecen WhatsApp. Desde `R3-PUB-04` ya no es la variable `WHATSAPP_CONTACTO_PUBLICO` (y su guarda de arranque), sino un dato de Administración: nadie debe escribir allí el ficticio | Administración → Datos de TIMU (`institucional`); `scripts/datos_portada.py` | PENDIENTE |
| Contrato de afiliación y sus condiciones generales | Las condiciones de `afiliaciones/documento.py` (`CONDICIONES`, versión `2026-11-provisional`): las firma el contrato y las muestra el modelo que la familia lee antes de pagar. **Pedirle a TIMU sus contratos reales** (decidido con el usuario el 2026-11-17) | `backend/app/modules/afiliaciones/documento.py` | PENDIENTE |
| Carencia y exclusiones de cada plan, que el registro en línea dice de frente | Las exclusiones, la nota legal del manual de marca de TIMU («Excluye preexistencias. Los beneficios no se acumulan y los topes aplican por episodio.»); la carencia, «Sin periodo de carencia.», la misma que rige al agregar un peludo. Iguales en los tres planes (decidido con el usuario el 2026-11-17: campos nuevos en el catálogo con texto provisional) | `backend/scripts/datos_demo.py` (`CONDICIONES`); desplegado, el administrador las escribe en Administración → Planes | PENDIENTE |
| Periodo de carencia del peludo que se agrega con contrato vigente | Sin carencia; no se permite con el contrato en mora ni congelado | `afiliaciones/altas.py` | PENDIENTE |
| Cobro del alta de un peludo desde el panel | No cobra el periodo en curso: el valor nuevo corre desde la siguiente cuota no emitida | `cartera/contratos.py` | PENDIENTE |
| Qué plan recomienda el bot comercial | Mi Amigo Fiel, el plan principal según el manual (sección 4), para cualquier ciudad, especie y número de peludos | Reglas `plan.recomendacion` (`reglas/datos.py` y su migración) | PENDIENTE |
| Proveedor de la IA | Mientras se migra a Gemini, `claude-haiku-5-5`, el económico de la comparativa | `IA_MODELO` (`core/config.py`, `.env.example`) | PENDIENTE |
| Tope de gasto mensual de la IA | US$ 50, el valor con que se arrancó; Administración lo cambia en la pestaña de IA (2026-11-20) | fila de `configuracion_ia` (migración 0058) | PENDIENTE |
| Si Gerencia recibe tareas (aprobaciones, escalamientos) | No: Gerencia mide y no opera, sin bandeja de tareas; una tarea solo se asigna a quien ve su área (Comercial; Atención al cliente para cartera y servicio al cliente; Operaciones; médico) (2026-11-20) | `AREAS_POR_ROL` (`tareas/service.py`) | PENDIENTE |
| Campañas por correo y segmentos fuera de las campañas (6.16, 6.18) | Las campañas salen solo por WhatsApp, el canal principal según el documento, aunque la plataforma ya envía correos para otras cosas; y los segmentos solo se usan en campañas, no en seguimiento, reportes ni acciones comerciales, que 6.16 también nombra (2026-11-20) | `campanas/service.py` (`_validar`), `campanas/segmentos.py` | PENDIENTE |
| En qué ciudades opera TIMU (dónde se puede afiliar una familia) | Bogotá y Medellín con su área metropolitana (Envigado, Itagüí, Sabaneta, Bello, La Estrella, Caldas, Copacabana, Girardota, Barbosa); las demás del catálogo, desactivadas (2026-11-20). El administrador activa otra en Catálogos | Migración 0060 y `activa` en `catalogos/datos.py` | PENDIENTE |
| Plantillas de WhatsApp aprobadas en Meta | Sin plantilla aprobada, ese mensaje no sale por WhatsApp (el enlace de activación y el de la afiliación salen también por correo). Cuáles faltan y qué deja de salir sin cada una lo dice el Inicio del administrador, desde lo que declara el código (`declarar_plantilla`, 2026-11-20). En la demostración local, `datos_demo` y `operacion_demo` dan por aprobadas las suyas (`recordatorio_renovacion` y `encuesta_satisfaccion`) para recorrer campañas y encuestas | `comunicaciones` | PENDIENTE |
| Nombre y registro de las plantillas de los avisos de mora (`cuota_vencida`, `aviso_mora`, `aviso_congelamiento`), que citan las reglas sembradas y aún no están en el catálogo de plantillas | Administración las nombra «Cuota vencida», «Aviso de mora» y «Aviso de congelamiento», con «aún sin registrar» en el editor de reglas (DEU-8, 2026-11-17); hasta que el equipo las registre con su texto aprobado en Meta, esos avisos no se envían por ningún canal: el proceso diario lo registra como error y lo reintenta (`cartera._notificar`) | `PLANTILLAS_DE_LAS_REGLAS` (`reglas/datos.py`) | PENDIENTE |
| Datos de TIMU que dice la portada (R3-PUB-04): presentación, visión, valores, clínica, horarios, teléfonos, correo, redes y NIT | Los de la web actual (https://timu.com.co, revisada el 2026-11-17), sembrados en local. **La misión no se siembra**: en la web está cortada a media frase («por esto, buscamos …»). El horario de los sábados de la clínica se contradice (5:00 p. m. en «Aliados», 4:00 p. m. en «Contáctanos»): se tomó el de «Aliados». El teléfono propio de la clínica (321 397 2365) no tiene campo: va entre los teléfonos si TIMU lo quiere a la vista. Desplegado, los escribe Administración → Datos de TIMU | `scripts/datos_portada.py` (`DATOS_TIMU`); `institucional` | PENDIENTE |
| Aliadas que muestra la portada | Las 17 de la página «Aliados» de la web, con su tipo, barrio, horario y orden en la red; sin logos (son marcas de terceros: los sube Administración). Confirmar con TIMU que siguen vigentes y que aceptan salir en la portada | `scripts/datos_portada.py` (`ALIADAS`); Administración → Aliadas | PENDIENTE |
| Beneficios adicionales y topes de cada plan | Los de la web: servicio fúnebre, desparasitante externo, especialistas, cirugía, exámenes, procedimientos, profilaxis, certificados, peluquería y precios preferenciales de terceros, con los topes de Mi Amigo Fiel (cirugía hasta $850.000, exámenes hasta $350.000). Donde la web se contradice con el plegable 2026 (la hospitalización de Mi Amigo Fiel, 80 % frente a 40 %), manda el plegable | `scripts/datos_portada.py` (`ADICIONALES`); Administración → Planes | PENDIENTE |
| Que las personas de las fotos del equipo aceptan salir en la web pública | TIMU confirmó el 2026-11-11 que las fotos son suyas, no que las personas que aparecen (la médica con el bulldog, la recepción, el saludo frente al logo) autorizan su uso en la web (Ley 1581: la imagen es un dato personal). La portada no se publica en el dominio sin esa confirmación. Aparte, las fotos que vienen de las piezas impresas (el parque, los gatitos, los recortes) parecen de banco de imágenes: TIMU confirma que su licencia permite usarlas en la web, o se cambian | `frontend/src/assets/portada/` (su `README.md`) | PENDIENTE |
| Política de tratamiento de datos (habeas data) que enlaza el formulario de contacto | La web actual la publica en `https://timu.com.co/wp-content/uploads/2025/05/Habeas-Data-TIMU.pdf`, sembrada en local. **Ese enlace muere cuando la web nueva sustituya a WordPress**: antes de cambiar el dominio, TIMU confirma que el documento sigue vigente y se aloja de nuevo (o TIMU da otro enlace), y Administración lo escribe. Sin enlace, el formulario solo dice para qué se usan los datos | `scripts/datos_portada.py` (`DATOS_TIMU`); Administración → Datos de TIMU | PENDIENTE |
| Mapa de las rutas | Sin mapa: cada parada abre la navegación del celular («Cómo llegar»). TIMU eligió Google Maps (informado por el usuario el 2026-11-21): sigue pendiente hasta que el mapa esté construido ([detalle](#mapa-de-las-rutas-requisito-67-r2-pan-06)) | `rutas` | PENDIENTE |
| Plazo para reportar lo atendido con una remisión ya vencida | 7 días tras la vigencia. Pasado ese plazo sin reporte, el proceso diario la pasa a «vencida» y cancela su servicio, lo que libera el cupo del beneficio (6.22, 2026-11-21) | `REMISION_GRACIA_REPORTE_DIAS` (`core/config.py`, `.env.example`) | PENDIENTE |
| Qué sigue disponible con el plan en pausa o en mora | El comportamiento de hoy, decidido con el usuario el 2026-11-21 (R4-CIE-02): no se agendan servicios ni se agregan peludos, y la orientación virtual sigue. El portal lo dice en el Inicio y en «Su plan» con el texto que da la API, y no marca los beneficios como disponibles | `_aviso_pausa` (`portal/service.py`); `motivo_sin_agendar`, `altas.motivo_sin_alta` | PENDIENTE |
| Número de urgencias que da el portal | El primer teléfono de Administración → Datos de TIMU (el que ya muestra la portada), y sin teléfono el WhatsApp de TIMU: la orientación virtual decía «llama a la línea de emergencias» sin número (R4-CIE-02, 2026-11-21). TIMU confirma si hay una línea de urgencias propia | `Urgencias` (`frontend/src/features/portal/Contacto.tsx`); Datos de TIMU | PENDIENTE |
| Ventana de la bandeja de preventivos | 30 días | `VENTANA_BANDEJA_DIAS` (`preventivos/service.py`) | PENDIENTE |
| Fotos originales para las páginas públicas | Las páginas públicas van sin fotos | — | PENDIENTE |
| Sandbox de Wompi de TIMU | No admite valor provisional: sin credenciales no hay prueba de punta a punta | — | PENDIENTE |
| Cómo recibe la familia el código de una remisión | Ninguno: la plataforma no lo envía ni lo muestra en el portal; se lo dice el equipo ([detalle](#remisiones-a-clínicas-aliadas-requisito-622)) | `aliadas/service.py` (`emitir`) | PENDIENTE |
| Si una remisión emitida sigue sirviendo cuando la familia cae en mora, se congela o se da de baja (**delicado**) | La baja o la cancelación del contrato cortan su vigencia ese día: lo atendido hasta entonces se sigue reportando y cobrando (decidido con el usuario el 2026-11-16, mientras lo precisa TIMU). La mora y la congelación la dejan servir hasta que vence, 30 días después de emitirse ([detalle](#remisiones-a-clínicas-aliadas-requisito-622)) | `REMISION_VIGENCIA_DIAS` (`core/config.py`); `aliadas/service.py` (`cortar_vigencia_al_cancelar`, `reportar_atencion`) | PENDIENTE |

## Requisito 6.1 (con el 6.12)

El código está completo, pero la revisión no se
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

## Inteligencia artificial: pasar a Gemini (Sección 14, 6.11 y 6.17)

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

**Un modelo por uso** (pregunta de TIMU, respondida el 2026-11-18): se puede tener uno económico
para el bot comercial y otro de más capacidad para los borradores clínicos. Hoy hay un único
`IA_MODELO` para los dos usos; separarlo es ligar el modelo a cada versión del prompt, para que
cambiarlo pase por los casos de evaluación como cualquier cambio del prompt. Lo decide esa
evaluación, con casos clínicos que escriba y revise un veterinario de TIMU: si el económico los
pasa, no hace falta el otro. El costo no lo impide (unos pocos dólares al mes con 14 borradores).

## Remisiones a clínicas aliadas (requisito 6.22)

Apuntado el 2026-11-16, al cerrar `R3-ALI-01` (el espacio de la clínica aliada). Las dos cosas son
decisiones de negocio de TIMU; el código está listo para cualquiera de las respuestas.

**1. La familia no recibe el código de su remisión.** El equipo emite la remisión en Aliadas y la
clínica la valida con su código (`6.22`): el código es la prueba de que la familia se
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
el plan vigente, la cartera al día y el beneficio disponible (`6.22`). Después no se vuelve a
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
qué pasa con la mora y la congelación; si la vigencia de 30 días es la que quiere; si una
atención hecha antes de la baja y reportada después se paga siempre; y cuántos días tiene la
clínica para reportarla (hoy 7, provisional).

**Resuelto el 2026-11-21: la remisión que vence sin usarse.** Su servicio quedaba agendado para
siempre y el cupo del beneficio ocupado, porque nada lo cerraba salvo anularla a mano (encontrado
el 2026-11-16). Ahora tiene un estado propio, `vencida` (decidido con el usuario, frente a
anularla, para distinguir la que caduca de la que alguien anula): pasado el plazo para reportar
(`REMISION_GRACIA_REPORTE_DIAS` tras la vigencia), la tarea diaria `aliadas.vencer_remisiones`
la pasa a `vencida` y cancela su servicio. El reporte fuera de plazo se rechaza aunque la tarea
aún no haya corrido, la clínica ve hasta qué día puede reportar (`reportar_hasta`) y la bandeja de
Aliadas tiene la vista «Vencidas».

## Recomendación de plan del bot comercial (6.11)

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
2026-11-12 para no meter una dependencia y un proveedor de teselas sin acordarlos.

**TIMU eligió Google Maps** (Maps JavaScript API, la opción A de la sección 4.1 de
[integraciones para TIMU](integraciones-timu.md); lo informó el usuario el 2026-11-21), en el
mismo proyecto de Google Cloud que factura la geocodificación y la matriz de distancias. Ya no
falta nada de TIMU salvo habilitar esa API (o darnos acceso al proyecto); lo que queda es
nuestro, y entra como unidad propia:

- **Una clave de navegador aparte** de `GOOGLE_MAPS_API_KEY`, que es del servidor: la del
  mapa se ve en el navegador, así que va restringida a timu.com.co y solo a Maps JavaScript API.
- **El costo** (tarifas globales consultadas el 2026-11-21): Dynamic Maps es un SKU Essentials
  con 10.000 cargas gratis al mes y US$ 7 por cada 1.000 de 10.001 a 100.000; su cupo es aparte
  del de Geocoding y del de la matriz. A TIMU se le dijo que el mapa **no pasará de lo
  gratuito**, así que lleva un límite diario de cargas en la consola de Google (Google Maps
  Platform → Cuotas) y se carga solo en la vista de rutas, no en cada pantalla. Google cobra por
  «carga correcta del mapa» y su página no aclara, para la API de JavaScript, si mover o acercar
  el mapa genera cargas nuevas: medirlo al construirlo.
- **Agotado el límite del día**, el mapa no se muestra y las rutas siguen funcionando como hoy
  («Cómo llegar»); el panel no puede quedarse en blanco ni romperse.

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

## Lo que falta en el código

El trabajo abierto que registraba el antiguo backlog por unidades, retirado el 2026-11-19 porque se
había alejado del documento de requerimientos. Cada punto cita el requisito que lo pide.

| Requisito | Qué falta | Estado |
| --- | --- | --- |
| 6.5 | Los días bloqueados de la agenda («Bloquear un día» en Servicios) no se ven ni se deshacen: no hay listado ni baja, y uno bloqueado por error deja la agenda sin cupos ese día. Encontrado en la revisión por perfiles del 2026-11-20. | Pendiente: decidir con el usuario |
| 6.6 | El pendiente de una atención es texto libre: no dice qué servicio es, así que no identifica la cobertura del plan ni el valor (puntos 2 y 3), no crea tarea para el equipo (punto 4) y al autorizarlo no inicia la programación (punto 7). Sí registra la autorización o el rechazo y no avanza sin ella. Revisión del 2026-11-20. | Parcial: decidir con el usuario |
| 6.7 | El mapa de las rutas con Google Maps («visualizar usuarios/servicios en un mapa»), que TIMU eligió (informado el 2026-11-21): clave de navegador, límite diario de cargas y caída a «Cómo llegar» ([detalle](#mapa-de-las-rutas-requisito-67-r2-pan-06)). | Pendiente |
| 6.7 | **Pasar la matriz de tiempos a la Routes API.** `integrations/mapas.py` llama a la Distance Matrix API (`…/maps/api/distancematrix/json`), que Google dejó como «legacy» y que un proyecto nuevo puede no habilitar. La clave que creó TIMU solo admite Geocoding API y Routes API, así que con ella la matriz fallaría y las rutas caerían siempre a la estimación en línea recta. Falta pasar a `computeRouteMatrix` de la Routes API: otra URL, cuerpo JSON, la clave en la cabecera `X-Goog-Api-Key`, la cabecera `X-Goog-FieldMask` obligatoria y una respuesta por elemento, no por filas. Se conservan la caché de `distancias_cache`, el reparto en bloques (revisar el máximo de elementos por petición, que no es el de 25 orígenes de la API vieja), el tope y la caída a línea recta. Su SKU (Compute Route Matrix Essentials) da 10.000 elementos gratis al mes y cobra US$ 5 por cada 1.000 después (tarifas del 2026-11-21). Prometido a TIMU el 2026-11-21 («estamos adaptando»). | Pendiente |
| 6.7 | **Que los frenos del gasto de Maps cuadren con lo prometido.** A TIMU se le dijo el 2026-11-21 que «el freno real lo ponemos nosotros», con un tope diario en la plataforma y cuotas diarias en Google. Hoy no es así: `MAPS_TOPE_DIARIO` vale 2.000 elementos al día (unos 60.000 al mes, hasta unos US$ 250), y el presupuesto que puso TIMU en Google Cloud es de COP 50.000 al mes. Además, la geocodificación (`integrations/geocodificacion.py`, que corre en cada cambio de dirección) no tiene ningún tope en la plataforma, y una migración (Sección 10) geocodifica a todas las familias de golpe. Falta: (1) acordar con TIMU el gasto máximo de Maps; hoy cabe en lo gratuito, pero a 12 meses la matriz se estima en unos US$ 52 al mes ([costos](costos-infraestructura.md)), por encima de ese presupuesto, y un tope fijado en lo gratuito empeora las rutas cuando se agota; (2) ajustar `MAPS_TOPE_DIARIO` a esa cifra y darle tope a la geocodificación, o dejar escrito por qué no lo necesita; (3) poner en la consola (Google Maps Platform → Cuotas) cuotas diarias a Geocoding API y a Routes API coherentes con lo anterior, como freno que no depende del código. La cuota del mapa visual va en su propia fila. | Pendiente: acordar el gasto con TIMU |
| 6.10 | Los estados del servicio son solicitado, agendado, en ruta, en atención, completado, pendiente de autorización, reprogramado y cancelado. Faltan, como estados o como equivalencia documentada, «contactado», «confirmado», «no autorizado» y «sin respuesta». Revisión del 2026-11-20. | Parcial: decidir con el usuario |
| 6.11 y 6.17 | **La IA sin saldo de Gemini.** Se suma a la adaptación del conector ([su sección](#inteligencia-artificial-pasar-a-gemini-sección-14-611-y-617)). Gemini va en prepago, y a TIMU se le recomendó comprar el mínimo con la recarga automática apagada. Cuando el saldo llega a cero, todas las claves del proyecto responden HTTP 402 hasta que alguien recarga. A TIMU se le dijo el 2026-11-21 que entonces «la IA se detiene pero la plataforma sigue funcionando sin ella». Falta: (1) que el conector nuevo convierta ese error en `ErrorIA`, como hace hoy `integrations/claude.py` con `APIStatusError`, para que `modules/ia` lo registre y el flujo siga sin IA; (2) distinguir «sin saldo» de un fallo pasajero y avisar a Administración: hoy una consulta en error solo se ve en la pestaña de IA, y nadie recibe un aviso. El tope mensual de la plataforma (`configuracion_ia`) es otro freno, aparte del saldo, y se mantiene. | Pendiente |
| 6.12 | El pago manual de un registro en línea (`POST /afiliaciones/{id}/pago-manual`) no tiene pantalla: sin la pasarela, Comercial no puede completar desde el panel la afiliación de quien se registró en la web. Revisión del 2026-11-20. | Pendiente: decidir con el usuario |
| 6.14 | El kardex (registro de la medicación administrada) no existe en la historia clínica. Revisión del 2026-11-20. | Pendiente: decidir con el usuario |
| 6.17 y 6.19 | **WhatsApp en coexistencia: lo que el equipo escribe desde la app.** A TIMU se le recomendó (y se le pidió confirmar el 2026-11-21) el número actual en coexistencia, la opción A de la sección 3.1 de [integraciones para TIMU](integraciones-timu.md). La condición de esa recomendación es que la plataforma registre también lo que el equipo escribe desde la app WhatsApp Business; sin eso, la conversación queda partida y se pierde la trazabilidad que piden el 6.17 y el 6.19. Meta envía esos mensajes al webhook como copias («echoes»; confirmar en la documentación de Meta el campo de suscripción al construirlo). Hoy `_registrar_entrante` (`comunicaciones/service.py`) no los recoge. Falta: (1) suscribirse a esas copias y registrarlas como mensajes salientes del equipo, en la conversación de la familia o del interesado; (2) que el bot comercial (`comercial/conversacion.py`) deje de contestar cuando una persona escribe desde la app, igual que al pasar a un asesor (`_asesor`), para que no respondan los dos a la vez. El criterio exacto se acuerda con TIMU. | Pendiente: TIMU confirma la opción A |
| 6.20 | Exportar las respuestas de las encuestas a Excel o CSV («la información deberá poder consultarse posteriormente y, de ser necesario, exportarse a Excel u otro formato»), con familia, mascota, servicio, fecha, profesional y puntaje. | Pendiente |
| Sección 9 | **El remitente del correo.** `SMTP_FROM` vale por defecto `TIMU <no-responder@timu.co>` (`core/config.py` y `backend/.env.example`), pero el dominio de TIMU es `timu.com.co`. Los registros SPF, DKIM y DMARC que publica TIMU cubren `timu.com.co`, así que con ese valor el correo saldría de un dominio que no es el suyo y caería en spam o lo rechazarían. Falta pasarlo a la cuenta de envío que cree TIMU (propuesta: `notificaciones@timu.com.co`, con el nombre de remitente que decida TIMU), que coincida con la cuenta con la que se autentica el SMTP de Workspace, y probar que llega a Gmail y a Outlook sin caer en spam. | Pendiente: falta la cuenta de TIMU |
| Sección 10 | La migración de la información actual de TIMU: mapeo campo a campo, dos corridas de prueba con conteos cuadrados y plan de reversa antes de la definitiva. | Pendiente: faltan los datos de TIMU |
| Sección 18 | Un recorrido automático del ciclo completo (captar, convertir, afiliar, gestionar, prevenir, atender, hacer seguimiento, medir y fidelizar). Hay ciclos parciales (afiliación, vacunación, atención virtual) y los recorridos de `e2e-stack/recorridos.spec.ts`; `operacion_demo` recorre buena parte por la API, pero no es una prueba. | Parcial |
| Sección E de la propuesta | El manual de usuario por perfil (lo promete la propuesta). Hay OpenAPI, README, guía del panel, guía de respaldos y [despliegue de staging](despliegue-staging.md); falta la guía de despliegue de producción. | Parcial |
| Sección D de la propuesta | La salida a producción: lista de verificación de seguridad, respaldos, monitoreo y plan de reversa ejecutados antes del corte. Incluye restringir la clave de Maps del servidor (`GOOGLE_MAPS_API_KEY`) por la IP de salida del servidor de producción, como se le dijo a TIMU el 2026-11-21: hasta entonces queda restringida solo a Geocoding API y Routes API. Eso exige que el proveedor que se elija dé una IP de salida fija; si no la da, la clave se queda restringida solo por API y hay que decírselo a TIMU. | Pendiente: falta decidir dónde va producción |
| — | El CI corre después de empujar a `main` y bloquea el release y el despliegue de staging, pero no impide que un cambio entre (no hay pull requests ni rama protegida). | Parcial, decidido así |
