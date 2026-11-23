<!--
Documento para la cliente (TIMU), lenguaje poco técnico. Es la versión en Markdown del Word y el PDF
«TIMU - Integraciones» que se entregaron para la reunión del 2026-11-17, con el mismo contenido.
Si TIMU decide algo, se actualiza aquí y se vuelve a generar el Word a partir de este texto. La
parte técnica (variables, código, estado de validación) está en docs/integraciones.md.
-->

# Integraciones de la plataforma TIMU

Qué falta para conectar la plataforma con WhatsApp, Wompi, Google y las demás herramientas: quién hace cada paso y qué queda por decidir.

*Preparado para la reunión del 17 de noviembre de 2026.*

## 1. Por qué empezar hoy

La plataforma ya tiene programadas estas conexiones, pero ninguna funciona de verdad hasta que TIMU abra sus cuentas en cada proveedor y nos dé acceso. Esos trámites dependen de Meta, de Wompi y de Google, no de nosotros, y algunos tardan semanas: sobre todo **la verificación de la empresa en Meta para WhatsApp** y **la habilitación del cobro automático en Wompi**. Por eso conviene arrancarlos ya, mientras seguimos con el resto del trabajo.

Todas las cuentas quedan a nombre de TIMU: si algún día cambia de proveedor de desarrollo, solo tiene que retirarnos el acceso.

### Resumen

| Integración | Para qué | Estado | Siguiente paso |
| --- | --- | --- | --- |
| WhatsApp | Avisos, recordatorios, encuestas, bot comercial y campañas | **Decidida** (el número, ver 3.1) | TIMU: verificación en Meta y elegir el número |
| Pagos con Wompi | Afiliación en línea, pagos del portal y cobro automático de cuotas | **Decidida** | TIMU: llaves de pruebas y pedir el cobro recurrente |
| Correo con Google Workspace | Enlaces de acceso y reportes por correo | **Decidida** | TIMU: cuenta de envío y registros del dominio |
| Google Maps (direcciones y rutas) | Ubicar direcciones y ordenar las rutas | **Decidida** | TIMU: cuenta de Google Cloud |
| Inteligencia artificial (Gemini) | Bot comercial y borradores de orientación virtual | **Decidida** | TIMU: misma cuenta de Google Cloud |
| Mapa visual de las rutas | Ver servicios y recorrido en un mapa | **Decidida** (Google Maps, sección 4.1) | TIMU: activar Maps JavaScript API en la misma cuenta de Google Cloud |
| Calendario | Agenda del equipo y confirmaciones | Por decidir | Elegir opción (sección 4.2) |
| Portada pública en timu.com.co | La web de TIMU, con los planes y la afiliación | Por decidir | Elegir opción (sección 4.3) |
| Hojas de cálculo | Exportar, importar y migrar datos | Por decidir | Elegir opción (sección 4.4) |
| Formularios | Que lo que llena la familia entre al perfil | Por decidir | Inventario y opción (sección 4.5) |
| Redes sociales | Captar interesados desde redes | Por decidir | Elegir opción (sección 4.6) |
| Otras herramientas y APIs | Conectar lo que TIMU ya usa | Por decidir | Inventario y opción (sección 4.7) |

## 2. Antes de empezar

**Una sola cuenta de Google Cloud**

Google Maps, el mapa visual de las rutas y Gemini cuelgan de una misma cuenta de Google Cloud de TIMU, con un medio de pago. Google solo cobra por encima de su capa gratuita mensual, y se pueden poner alertas de presupuesto para que avise antes de cualquier cobro.

**Cómo compartirnos los accesos**

- Lo mejor es **darnos un rol** (administrador o desarrollador) en cada plataforma: Meta, Wompi y Google. Así no hace falta enviar contraseñas, y TIMU puede retirar el acceso cuando quiera.
- Si hay que pasar una llave o una contraseña, por un canal seguro (un gestor de contraseñas o un enlace que caduca), **nunca por WhatsApp ni por correo** en texto plano.

**El dominio timu.com.co**

La plataforma se publicará en timu.com.co, reemplazando la web actual; WhatsApp y Wompi enviarán sus avisos a direcciones de ese dominio, que configuramos nosotros. De TIMU necesitamos que quien administra el dominio, el día del cambio, apunte timu.com.co y www.timu.com.co al servidor de la plataforma **sin modificar los registros del correo de Workspace**. Recomendamos hacer el cambio después de que Meta verifique la empresa y cuando la portada pública esté lista (sección 4.3), para que timu.com.co no se quede sin página de inicio ni se pierdan los enlaces que hoy circulan.

## 3. Integraciones decididas: paso a paso

### 3.1 WhatsApp

> **Corrección del 22 de noviembre de 2026** (pendiente de pasar al Word cuando TIMU elija la ruta): la verificación de la empresa en Meta no es necesaria para empezar; sin ella, Meta deja escribir hasta a 250 personas distintas al día. Y la opción A no se conecta directamente desde la cuenta de TIMU: Meta exige un socio autorizado (*Solution Partner* o *Tech Provider*). A TIMU se le enviaron las rutas que quedan (la A con 360dialog, recomendada, la B y la C); el detalle técnico está en [integraciones](integraciones.md) y en [lo que falta en el código](pendiente-en-el-codigo.md).

**Para qué sirve.** WhatsApp es el canal principal de TIMU con las familias (requisito 6.19), y la plataforma lo usa en casi todos sus procesos: recordatorios, avisos de la ruta, encuestas, el bot comercial y las campañas (requisitos 6.11, 6.17, 6.18, 6.20 y 6.21). La conexión ya está programada; falta conectar la cuenta de TIMU y decidir con qué número.

#### Lo que la plataforma ya hace con WhatsApp

- **Avisos automáticos** con los mensajes aprobados por Meta (plantillas): acceso al portal, bienvenida, cartera, preventivos, ruta del día, encuestas, orientación virtual y campañas (lista completa al final de esta sección).
- **Respeta la regla de Meta de las 24 horas:** fuera de ellas solo salen plantillas aprobadas; dentro, el equipo puede escribir libremente. Si a un aviso le falta su plantilla aprobada, el enlace sale por correo.
- **Bot comercial** (6.11): atiende al interesado que escribe, le hace preguntas guiadas (ciudad, peludos…), lo registra como interesado en el embudo comercial y lo pasa a un asesor cuando lo pide o cuando la pregunta se sale del guion.
- **Bandeja de conversaciones:** el equipo ve las conversaciones que esperan a un asesor y contesta desde la plataforma. Cada conversación queda en la ficha del interesado o de la familia (6.19).
- **Encuestas por WhatsApp** (6.20): la familia responde en el chat y el puntaje queda asociado al servicio y al profesional; una calificación baja crea una tarea para el equipo.
- **Estados de cada mensaje:** enviado, entregado, leído o fallido, por destinatario, también en las campañas (6.18).
- **Bajas:** quien escribe «BAJA», «STOP», «NO MÁS» o «DETENER» deja de recibir mensajes automáticos.
- **Seguridad:** la plataforma comprueba la firma de Meta en cada mensaje que recibe, y los enlaces de un solo uso no quedan visibles en el historial.
- De lo que escribe la familia, la plataforma guarda el **texto**. Las fotos, los audios y los documentos quedan anotados (por ejemplo, «[imagen]»), pero hoy se ven en la aplicación, no en la plataforma.

#### Qué número usar: las opciones

Las dos primeras usan el número que TIMU tiene hoy; la tercera, uno nuevo. El requisito que más pesa en la elección es la **trazabilidad**: el documento de requerimientos nace de la pérdida de trazabilidad entre herramientas, y el 6.17 y el 6.19 piden que la conversación quede registrada y asociada a la mascota.

#### Opción A: El número actual, compartido entre la aplicación y la plataforma (coexistencia)

El número sigue funcionando en la aplicación WhatsApp Business del celular y, a la vez, la plataforma envía y recibe con él.

**A favor**

- Las familias siguen escribiendo al número que ya conocen: no hay que anunciar un cambio ni perder contactos.
- El equipo conserva la aplicación para lo que la plataforma aún no muestra: fotos, audios, documentos y llamadas.
- La transición es gradual: el equipo puede ir pasando la atención a la plataforma sin cortar nada.
- Los mensajes que el equipo escribe desde la aplicación siguen siendo gratis.

**En contra**

- Lo que el equipo escribe desde la aplicación **hoy no queda en la plataforma**. Meta envía una copia de esos mensajes y la plataforma tiene que recogerla: es un trabajo nuestro, y sin él la conversación queda partida entre la aplicación y la plataforma.
- El bot y una persona podrían contestar a la vez al mismo interesado: hay que acordar cuándo atiende cada uno.
- El celular tiene que seguir activo: si la aplicación queda inactiva unas dos semanas, Meta desconecta el número de la plataforma.
- No está disponible la insignia verde de cuenta oficial.
- Al conectar se desvinculan WhatsApp Web y los computadores enlazados, y el historial anterior pasa a la plataforma solo en parte.

#### Opción B: El número actual, solo en la plataforma

El número se pasa entero a la plataforma y deja de funcionar en la aplicación del celular.

**A favor**

- Las familias siguen escribiendo al número que ya conocen.
- Toda la conversación pasa por la plataforma: trazabilidad completa (6.17 y 6.19).
- No depende de un celular encendido, y se puede pedir la insignia verde.

**En contra**

- El equipo atiende todo desde la plataforma, y hoy la plataforma no muestra fotos, audios ni documentos: hay que construirlo antes del cambio.
- El historial de chats de la aplicación no pasa a la plataforma.
- Es un cambio de golpe para el equipo: el día de la conexión deja de tener la aplicación.

#### Opción C: Un número nuevo dedicado a la plataforma

La plataforma usa un número nuevo, y el actual sigue en la aplicación como hoy.

**A favor**

- No toca la operación actual: el número de siempre sigue igual mientras se prueba la plataforma.
- Todo lo que pasa por el número nuevo queda en la plataforma.
- No depende de un celular encendido, y se puede pedir la insignia verde.

**En contra**

- Las familias tienen que guardar un número nuevo. Los avisos de un número desconocido se ignoran o se reportan como spam más a menudo, y eso baja la calidad del número ante Meta, que puede limitar sus envíos.
- Con dos números, las familias no saben a cuál escribir, y la conversación vuelve a quedar partida: la trazabilidad se pierde por otro lado.
- Hay que anunciar el número nuevo a todas las familias.
- Para atender desde la plataforma, sigue haciendo falta construir la vista de fotos, audios y documentos.

> **Nuestra recomendación:** **Opción A, el número actual en coexistencia, siempre que la plataforma registre también lo que el equipo escribe desde la aplicación.** Conserva el canal que las familias ya usan (el documento de requerimientos lo señala como el principal) y, con esa copia registrada, cumple la trazabilidad del 6.17 y el 6.19. Cuando la plataforma muestre fotos y audios, se puede pasar a la opción B. La opción C solo tiene sentido si TIMU quiere separar los avisos automáticos de la atención por personas.

#### Paso a paso

**Qué tiene que hacer TIMU (cualquier opción)**

1. Crear o confirmar el portafolio de empresa en Meta (business.facebook.com) a nombre de TIMU S.A.S., con un administrador de TIMU.
2. Iniciar la **verificación de la empresa** en Meta con los documentos de TIMU (por ejemplo, el certificado de existencia y representación legal y el RUT) y un correo o sitio web con el dominio timu.com.co. **Es el trámite que más tarda: empezarlo ya.**
3. Agregar un medio de pago en la cuenta de WhatsApp Business de Meta: los mensajes que envía la plataforma se cobran por mensaje.
4. Darnos acceso al portafolio con rol de administrador o desarrollador.
5. Revisar y aprobar los textos de los mensajes automáticos (plantillas, lista abajo). Nosotros los preparamos y los enviamos a Meta para su aprobación.

**Además, según la opción**

- **Opción A (coexistencia):** el número tiene que estar en la aplicación **WhatsApp Business** (no en WhatsApp personal), actualizada y activa hace más de una semana. El día de la conexión, alguien con ese celular a mano escanea un código desde la aplicación. Después, mantener la aplicación activa.
- **Opción B (solo plataforma):** respaldar los chats que quieran conservar, porque el historial no pasa. El día de la conexión, el número se da de baja en la aplicación (con la verificación en dos pasos desactivada) y se registra en la plataforma.
- **Opción C (número nuevo):** conseguir una línea que no esté registrada en ningún WhatsApp y que pueda recibir un SMS o una llamada con el código de verificación. Anunciar el número nuevo a las familias desde el número actual.

**Qué necesitamos que nos entreguen**

- Acceso al portafolio de Meta (con él obtenemos los identificadores del número y de la cuenta).
- Los textos de las plantillas aprobados por TIMU.
- La decisión sobre el número.

**Qué hacemos nosotros**

- Crear la aplicación de Meta y su usuario de sistema, con la llave permanente.
- Configurar la dirección que recibe los mensajes y los estados de entrega.
- Registrar en Meta cada plantilla con su nombre y sus variables exactos.
- **Con la opción A:** registrar en la plataforma lo que el equipo escribe desde la aplicación, y acordar con TIMU cuándo contesta el bot y cuándo una persona.
- **Con las opciones B o C:** mostrar en la plataforma las fotos, los audios y los documentos que envían las familias.
- Probar de punta a punta: enviar, recibir, estados de entrega, bot comercial y bajas.

**Costo.** Meta cobra cada mensaje que envía la plataforma: como referencia para Colombia, unos US$ 0,0008 por aviso o código y unos US$ 0,0125 por mensaje de campaña (Meta revisa sus tarifas cada trimestre). Con el volumen de hoy son unos US$ 8 al mes. En la opción A, lo que el equipo escribe desde la aplicación sigue siendo gratis.

**Tiempo del trámite.** La verificación de la empresa, de unos días a varias semanas. Cada plantilla suele aprobarse en horas; si Meta rechaza una, se ajusta el texto y se vuelve a enviar.

*Las condiciones de la coexistencia son las que publican hoy Meta y los proveedores de WhatsApp; las confirmamos en el momento de la conexión.*

**Mensajes automáticos (plantillas) que Meta tiene que aprobar**

| Momento | Plantillas |
| --- | --- |
| Acceso al portal | Activar la cuenta, recuperar la contraseña, código de ingreso |
| Afiliación | Bienvenida, completar la afiliación (y su recordatorio) |
| Cartera | Cuota vencida, aviso de mora, aviso de congelamiento, plan congelado, plan reactivado |
| Preventivos | Recordatorio de vacuna o desparasitación |
| Ruta del día | Franja de llegada, médico en camino |
| Después de la atención | Encuesta de satisfacción, seguimiento |
| Orientación virtual | Respuesta del equipo médico |
| Campañas | Las que defina el equipo, por ejemplo, el recordatorio de renovación |

### 3.2 Pagos con Wompi

**Para qué sirve.** La afiliación en línea con pago, el pago de cuotas y el alta de peludos desde el portal, el cobro automático de cuotas con la tarjeta guardada y la conciliación automática de cada pago (requisitos 6.2 y 6.12, y los pagos en línea de la sección 14).

**Qué tiene que hacer TIMU**

1. Abrir o confirmar la cuenta de comercio en Wompi a nombre de TIMU S.A.S., con la cuenta bancaria donde Wompi deposita el dinero.
2. Darnos un usuario en el panel de comercio de Wompi. Si no es posible, compartirnos por un canal seguro las llaves del **ambiente de pruebas**: llave pública, llave privada, secreto de integridad y secreto de eventos.
3. Pedir a su asesor comercial de Wompi la **habilitación del cobro recurrente** (guardar la tarjeta para cobrar las cuotas solas) y confirmar con qué medios funciona. **Pedirlo ya: es lo que más tarda.**
4. Definir qué medios de pago se ofrecen a las familias (tarjeta, PSE, Nequi, Bancolombia, Daviplata…).
5. Cuando terminemos las pruebas, activar la cuenta de producción y compartirnos sus llaves.
6. Recomendado: negociar la tarifa por volumen. Es el mayor costo de toda la operación digital.

**Qué necesitamos que nos entreguen**

- Acceso al panel o las llaves de pruebas.
- La confirmación de que el cobro recurrente quedó habilitado.
- Las llaves de producción, al final.

**Qué hacemos nosotros**

- Configurar las llaves y la dirección por la que Wompi avisa de cada pago.
- Probar en el ambiente de pruebas: pago aprobado, rechazado, reintento, enlace vencido y cobro recurrente.
- Pasar a producción y vigilar la conciliación de los primeros pagos.

**Costo.** La tarifa general publicada es de 2,65 % + $ 700 + IVA por pago aprobado: unos $ 2.725 en una cuota de $ 60.000. Wompi tiene tarifas menores para otros medios (por ejemplo, QR) y se puede negociar según el volumen.

**Tiempo del trámite.** La cuenta, unos días. El cobro recurrente depende de la aprobación de Wompi: mientras no esté, la plataforma cobra con enlace de pago, pero no cobra sola.

### 3.3 Correo con Google Workspace

**Para qué sirve.** Los enlaces para activar o recuperar la cuenta del portal, el enlace para completar la afiliación y los reportes programados con su Excel. WhatsApp sigue siendo el canal principal; el correo es el respaldo (sección 9).

**Qué tiene que hacer TIMU**

1. Crear una cuenta de envío, por ejemplo **notificaciones@timu.com.co** (puede requerir una licencia más de Workspace), o elegir una existente.
2. Activar la verificación en dos pasos de esa cuenta y crear una **contraseña de aplicación** para la plataforma. (Alternativa para el administrador de Workspace: activar el servicio de retransmisión de correo y autorizar la dirección del servidor de la plataforma, que le damos al publicarla.)
3. Publicar en el dominio timu.com.co los registros que certifican el correo: **SPF, DKIM y DMARC** (DKIM se genera en la consola de administración de Workspace). Sin ellos, los correos caen en la carpeta de spam.
4. Decidir el nombre que verá la familia como remitente (por ejemplo, «TIMU»).

**Qué necesitamos que nos entreguen**

- La cuenta de envío y su contraseña de aplicación (o la retransmisión configurada).
- La confirmación de que los registros del dominio están publicados.

**Qué hacemos nosotros**

- Configurar la conexión de la plataforma.
- Probar que los correos llegan a Gmail y a Outlook sin caer en spam.

**Costo.** Incluido en Workspace, salvo la licencia si se crea un usuario dedicado.

**Tiempo del trámite.** Un día. Los registros del dominio pueden tardar hasta 48 horas en surtir efecto.

**Ten en cuenta**

- Una cuenta de Workspace envía hasta unos 2.000 correos al día; sobra para el volumen previsto.

### 3.4 Google Maps: direcciones y orden de las rutas

**Para qué sirve.** Ubicar en el mapa la dirección de cada familia y calcular los tiempos reales entre visitas para proponer el mejor orden de la ruta del día (requisito 6.7).

**Qué tiene que hacer TIMU**

1. Crear un proyecto de Google Cloud a nombre de TIMU (console.cloud.google.com), con su cuenta de facturación.
2. Darnos acceso al proyecto con rol de editor. Si lo prefieren hacer ellos: activar **Geocoding API** y **Routes API**.
3. Configurar una alerta de presupuesto (por ejemplo, US$ 50 al mes) para que Google avise antes de cualquier cobro.

**Qué necesitamos que nos entreguen**

- Acceso al proyecto, o una clave restringida a esas dos APIs y al servidor de la plataforma.

**Qué hacemos nosotros**

- Crear y restringir la clave.
- Ajustar el cálculo de tiempos a la Routes API: la que usa hoy la plataforma quedó como versión antigua y puede no estar disponible en un proyecto nuevo.
- Probar con direcciones reales de las familias.

**Costo.** Hoy cabe en la capa gratuita mensual de Google. Con 5.000 familias se estiman unos US$ 50 al mes, y la plataforma tiene un tope diario que impide pasar de unos US$ 250 al mes.

**Tiempo del trámite.** Un día.

### 3.5 Inteligencia artificial con Gemini

**Para qué sirve.** El bot comercial de WhatsApp responde dentro del guion aprobado y pasa a un asesor cuando la pregunta se sale de él; y en la orientación virtual, la IA redacta un borrador que siempre revisa y aprueba un profesional (requisitos 6.11 y 6.17, y la IA de apoyo de la sección 14).

**Qué tiene que hacer TIMU**

1. En el mismo proyecto de Google Cloud, activar la API de Gemini en la **capa de pago**. La capa gratuita usa los datos para mejorar los productos de Google, y con datos personales y clínicos eso choca con la Ley 1581.
2. Darnos acceso al proyecto (o la clave de la API).

**Qué necesitamos que nos entreguen**

- Acceso al proyecto con Gemini activado en la capa de pago.

**Qué hacemos nosotros**

- Adaptar la conexión de la plataforma a Gemini (hoy funciona con otro proveedor de IA).
- Probar los guiones y los borradores con sus casos de evaluación antes de activarlos.
- Fijar el presupuesto mensual: al agotarse, la plataforma sigue funcionando sin IA.

**Costo.** Centavos al mes con el volumen actual (unos US$ 0,33; unos US$ 3 al mes con 5.000 familias).

**Tiempo del trámite.** Un día para la cuenta.

## 4. Por decidir: opciones

En cada caso recomendamos la opción que mejor cumple el documento de requerimientos de TIMU, no la que sea más fácil de construir para nosotros. Al lado de cada título va el requisito que la pide.

### 4.1 Mapa visual de las rutas

> **Decidido: opción A, Google Maps dentro del panel** (informado el 21 de noviembre de 2026). TIMU activa **Maps JavaScript API** en el mismo proyecto de Google Cloud, o nos da acceso para hacerlo. Nosotros creamos una clave aparte para el mapa, restringida a timu.com.co, construimos el mapa y dejamos en Google un límite diario de cargas. Google da 10.000 cargas del mapa gratis al mes y cobra US$ 7 por cada 1.000 de más; con ese límite, el mapa no pasa de lo gratuito. Si un día se alcanzara, el mapa no se mostraría ese día, pero las rutas seguirían funcionando.

Requisito 6.7: «visualizar usuarios/servicios en un mapa y proponer una secuencia de atención que optimice desplazamientos». Hoy la plataforma ya propone la secuencia, y cada parada abre la navegación del celular, pero no dibuja el mapa dentro del panel.

#### Opción A: Google Maps dentro del panel

**A favor**

- Usa la misma cuenta y los mismos datos con que se ubican las direcciones y se calculan las rutas: lo que se ve en el mapa coincide con lo que se planificó.
- Puede dibujar el recorrido por las calles, en el orden propuesto.
- Cumple el 6.7 completo: el mapa y la secuencia, sobre el mismo dato.
- Tiene una capa gratuita mensual.

**En contra**

- Por encima de la capa gratuita, Google cobra por carga del mapa.
- Más dependencia de un solo proveedor.

#### Opción B: Mapa abierto (OpenStreetMap) con un proveedor de mapas

**A favor**

- No depende de Google para el mapa.
- Costo predecible con el proveedor que se contrate.

**En contra**

- Hay que contratar otro proveedor y, para dibujar el recorrido por las calles, otro servicio de rutas.
- Dos fuentes de datos (la de Google para las direcciones y la del mapa) que no siempre coinciden.
- Las condiciones de Google para mostrar sus datos sobre mapas de otros han cambiado con los años: habría que revisarlas.

#### Opción C: Seguir sin mapa

Cada parada abre la navegación del celular, como hoy.

**A favor**

- Sin costo adicional.

**En contra**

- No cumple la parte de «visualizar en un mapa» del 6.7.

> **Nuestra recomendación:** **Opción A.** Es la que cumple el 6.7 completo, con el mapa y la secuencia sobre los mismos datos con que se planifica la ruta.

### 4.2 Calendario

Sección 9: «Google Calendar u otros calendarios»; y el 6.5 pide «generar confirmaciones». La propuesta lo incluye en la implementación; falta decidir cómo.

#### Opción A: Calendario al que el equipo se suscribe

Cada médico y operaciones añaden un enlace a su Google Calendar, Outlook o el calendario del celular, y ven sus servicios y sus rutas, que se actualizan solos.

**A favor**

- Funciona con Google y con cualquier otro calendario: cumple el «u otros calendarios».
- No pide acceso a las cuentas personales del equipo.
- La agenda sigue mandando desde la plataforma: una sola fuente de verdad.

**En contra**

- Es de solo lectura: no se agenda desde el calendario.
- Los calendarios refrescan una suscripción cada cierto tiempo (Google puede tardar varias horas): un cambio de última hora se ve antes en la plataforma.

#### Opción B: Sincronización con Google Calendar

La plataforma crea y mueve los eventos en el calendario de cada persona.

**A favor**

- Los cambios aparecen casi al instante.
- Podría tener en cuenta lo que cada profesional tiene ocupado en su calendario.

**En contra**

- Solo sirve con Google.
- Cada persona tiene que autorizar su cuenta, y hay que decidir qué pasa si alguien edita el evento en su calendario (dos lugares donde se cambia lo mismo).
- Más desarrollo y más puntos de falla.

#### Opción C: Invitación de calendario en las confirmaciones

A la familia le llega su cita como evento de calendario, junto con la confirmación.

**A favor**

- Cumple el «generar confirmaciones» del 6.5 con cualquier calendario.

**En contra**

- Es un complemento: no resuelve la agenda del equipo.

> **Nuestra recomendación:** **Opciones A y C juntas**: cubren «Google Calendar u otros calendarios» y las confirmaciones, sin dar a la plataforma acceso a las cuentas personales. Pasaríamos a la opción B solo si el equipo trabaja su agenda en Google Calendar y necesita ver allí los cambios del día al instante.

### 4.3 La portada pública en timu.com.co

Sección 9: «página web»; el 6.12 pide conectar formulario, pago, afiliación y contrato; y el 6.11, que lo que se ofrece respete la ciudad y la disponibilidad de cada plan. Como la plataforma reemplazará la web actual en timu.com.co, la plataforma tiene que traer su propia portada pública: lo que ve quien entra a timu.com.co sin ser familia ni equipo.

La portada pública llevaría los **planes con sus precios y su disponibilidad por ciudad**, leídos del catálogo de la plataforma (el mismo con el que se cobra), el botón para afiliarse en línea con el plan elegido, **Nosotros**, la clínica, los aliados y el contacto, con el botón de WhatsApp. Lo que hay que decidir es cuánto de esto tiene que estar listo antes de cambiar el dominio.

#### Opción A: Portada completa antes del cambio de dominio

Se construye la portada con todo su contenido y se redirigen los enlaces de la web actual (/planes/, /nosotros/…) a su página nueva. El dominio cambia cuando la portada está lista y Meta ya verificó la empresa.

**A favor**

- timu.com.co nunca se queda sin página de inicio.
- Cumple el 6.11 y el 6.12 con una sola fuente de verdad: un cambio de precio en la plataforma cambia la web.
- No se pierden los enlaces que circulan en redes y en buscadores.

**En contra**

- Depende de que TIMU entregue los contenidos, las fotos y los precios oficiales.
- El cambio de dominio espera a que todo esté listo.

#### Opción B: Portada mínima y cambio pronto

Se cambia el dominio con una portada corta (los planes del catálogo, afiliarse y contacto), y lo demás (Nosotros, clínica, aliados) se añade después. Los enlaces viejos llevan a la portada.

**A favor**

- El dominio cambia antes.
- Cumple desde el primer día lo que piden el 6.11 y el 6.12: planes del catálogo y afiliación en línea.

**En contra**

- Durante un tiempo desaparece información que hoy está en la web (Nosotros, clínica, aliados).
- Sigue dependiendo de los precios oficiales.

#### Opción C: Cambio sin portada

El dominio cambia ya, y quien entra a timu.com.co ve el ingreso a la plataforma.

**A favor**

- No hay nada que construir antes del cambio.

**En contra**

- TIMU se queda sin web pública: quien busca los planes no los encuentra.
- Se rompen los enlaces que circulan en redes y en buscadores.
- Si Meta aún no ha verificado la empresa, la verificación puede complicarse: Meta usa la web como prueba del negocio.

> **Nuestra recomendación:** **Opción A.** Es la que cumple la sección 9, el 6.11 y el 6.12 sin dejar a TIMU sin web en ningún momento. Si los contenidos tardan, la B es un paso intermedio aceptable, siempre después de la verificación de Meta.

### 4.4 Hojas de cálculo

Sección 9: «hojas de cálculo»; el 6.20 pide exportar las encuestas a Excel; la sección 10, migrar la información actual; y la 11, poder exportar los datos.

#### Opción A: Exportar e importar archivos (Excel o CSV)

Cada listado (familias, cartera, encuestas…) se descarga en Excel, y la información que TIMU tiene hoy en hojas se importa a la plataforma.

**A favor**

- Cubre el 6.20, la migración (10) y la exportación de datos (11).
- Los datos siguen viviendo en la plataforma, con sus permisos y su registro de quién hizo qué.
- Sin dependencia de un tercero.

**En contra**

- El archivo descargado es una foto de ese momento: no se actualiza solo.

#### Opción B: Sincronización en vivo con Google Sheets

**A favor**

- Una hoja siempre al día para quien trabaja en Sheets.

**En contra**

- Copia datos personales y de pago fuera de la plataforma: se pierden sus permisos y su trazabilidad, y complica el cumplimiento de la Ley 1581.
- Si alguien edita la hoja, hay dos lugares donde se cambia lo mismo.
- Más desarrollo.

> **Nuestra recomendación:** **Opción A.** Usaríamos la B solo para un reporte concreto que el equipo necesite en vivo y que no tenga datos personales.

### 4.5 Formularios

El 6.1 lo marca como requerimiento crítico: lo que la familia llena en un formulario tiene que entrar solo a su perfil. El 6.9 pide la autorización de preventivos por formulario, y el 6.12, la afiliación desde el formulario. La plataforma ya tiene sus propios formularios (registro en línea con pago, afiliación asistida, autorización de preventivos desde el portal, encuestas y alta de peludos), y todos llenan el perfil solos.

#### Opción A: Reemplazar los formularios externos por los de la plataforma

Los formularios que TIMU usa hoy en otras herramientas (por ejemplo, Google Forms) se retiran y se usan los de la plataforma.

**A favor**

- Cumple el 6.1 sin reprocesos: el dato entra validado y al perfil correcto.
- Una sola fuente de verdad.

**En contra**

- Hay que cambiar los enlaces que hoy circulan.

#### Opción B: Conectar los formularios externos

Las respuestas de los formularios actuales entran a la plataforma.

**A favor**

- No cambia lo que las familias ya conocen.

**En contra**

- El dato llega sin validar (documento, teléfono, ciudad) y hay que emparejarlo con la familia correcta.
- Si alguien cambia una pregunta del formulario externo, la conexión se rompe.
- Un desarrollo por cada formulario.

> **Nuestra recomendación:** **Opción A.** Para planearla necesitamos el inventario de los formularios que TIMU usa hoy.

### 4.6 Redes sociales

Sección 9: «redes sociales, cuando técnicamente sea posible»; el 6.11 habla de atender a quien llega «por WhatsApp u otros canales»; y el dashboard de la sección 8 pide la fuente de cada interesado.

#### Opción A: Registrar de qué red llega cada interesado

Enlaces marcados por red social, y el campo «origen» del interesado.

**A favor**

- Cumple la «fuente del lead» del dashboard (sección 8) con poco desarrollo.

**En contra**

- No trae las conversaciones de las redes a la plataforma.

#### Opción B: Mensajes directos de Instagram y Facebook en la plataforma

Los mensajes de Instagram y Facebook llegan a la misma bandeja de conversaciones que WhatsApp, con la misma cuenta de Meta.

**A favor**

- Atiende el «u otros canales» del 6.11 en un solo lugar, con el historial en la ficha.

**En contra**

- Desarrollo adicional.
- Requiere permisos y una revisión de la aplicación por parte de Meta.

#### Opción C: Formularios de anuncios de Facebook e Instagram

Si TIMU pauta con formularios de anuncios, cada contacto entra solo al embudo comercial, con su origen.

**A favor**

- Cada interesado de la pauta llega a la plataforma sin digitarlo.

**En contra**

- Solo sirve si hay pauta, y requiere desarrollo y permisos de Meta.

> **Nuestra recomendación:** **Opción A siempre.** Además, la B si una parte importante de los interesados escribe hoy por Instagram o Facebook, o la C si TIMU pauta con formularios de anuncios. Para decidirlo necesitamos saber de dónde llegan hoy los interesados.

### 4.7 Otras herramientas y APIs externas

Sección 9: «APIs externas» y «otras herramientas actualmente utilizadas por TIMU»; el 6.2 menciona la plataforma externa que hoy genera las tareas de cobro; y la sección 10, la migración. El primer paso es un **inventario** de lo que TIMU usa hoy: esa plataforma de tareas de cobro, las hojas de cálculo, los formularios, la contabilidad, la facturación electrónica y cualquier otra.

#### Opción A: Una conexión estándar para cualquier herramienta

La plataforma da claves de acceso a otros sistemas y avisa automáticamente cuando pasa algo (un pago aprobado, una afiliación nueva…). Cualquier herramienta, o servicios como Zapier o Make, se conecta por ahí.

**A favor**

- Cumple las «APIs externas» para cualquier herramienta, también las futuras, sin rehacer la base (sección 3).
- TIMU controla quién accede y puede retirar cada clave.

**En contra**

- Desarrollo inicial.
- Cada herramienta concreta aún hay que configurarla.

#### Opción B: Un conector a la medida para cada herramienta

**A favor**

- Integración más profunda con una herramienta concreta.

**En contra**

- Un desarrollo por herramienta; si la herramienta cambia, se rehace.

#### Opción C: Reemplazar y migrar

Lo que la plataforma ya hace (por ejemplo, las tareas de cobro del 6.2) se deja de hacer en la herramienta externa y sus datos se migran.

**A favor**

- Elimina la doble digitación, que es el objetivo del documento de requerimientos.

**En contra**

- Hay que planear la migración y el cambio de hábito del equipo.

> **Nuestra recomendación:** **La C para lo que la plataforma ya cubre, la A como base para el resto**, y la B solo para algo crítico que lo necesite (por ejemplo, la facturación electrónica, si aplica). Lo definimos con el inventario.

## 5. Lista de pendientes para TIMU

**Empezar ya (son los trámites más lentos)**

- Iniciar la verificación de la empresa en Meta.
- Confirmar con qué número se conecta WhatsApp (3.1).
- Abrir o confirmar la cuenta de Wompi y pedir la habilitación del cobro recurrente.

**Esta semana**

- Darnos acceso al portafolio de Meta.
- Darnos un usuario en Wompi, o compartir las llaves de pruebas por un canal seguro.
- Crear el proyecto de Google Cloud con facturación y darnos acceso; activar Geocoding API, Routes API y Maps JavaScript API, y Gemini en la capa de pago.
- Crear la cuenta de envío en Workspace con su contraseña de aplicación, y publicar SPF, DKIM y DMARC en el dominio.
- Confirmar quién administra el dominio timu.com.co y la web actual. El día del cambio, esa persona apunta timu.com.co y www.timu.com.co a la plataforma sin tocar los registros del correo.

**Para decidir**

- Calendario (4.2), portada pública y cuándo se cambia el dominio (4.3), hojas de cálculo (4.4), formularios (4.5), redes sociales (4.6) y otras herramientas (4.7).

**Para entregarnos**

- El inventario de herramientas, formularios y hojas de cálculo que se usan hoy.
- De dónde llegan hoy los interesados (WhatsApp, Instagram, Facebook, web, referidos…).
- Los textos de las plantillas de WhatsApp, revisados.
- Los contenidos de la portada pública (Nosotros, clínica, aliados, contacto) y sus fotos.

*Las tarifas de terceros son aproximadas, consultadas en noviembre de 2026, sin IVA. Las fija cada proveedor (Meta, Wompi, Google) y pueden cambiar.*
