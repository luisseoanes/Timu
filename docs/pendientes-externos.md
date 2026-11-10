# Pendientes externos para cerrar requisitos

Lo que falta **fuera del código**, o detrás de un tercero o de una decisión de TIMU, para dar
por cerrada la revisión de un requisito. El código y sus pruebas ya están; esto es lo que no
se puede resolver desde el repositorio. Se tacha cuando se resuelve.

El estado de cada unidad de trabajo está en el [backlog](backlog.md); cómo funciona cada
integración, en [integraciones](integraciones.md).

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
- **Mientras tanto,** `IA_MODELO` vale por defecto `claude-opus-5-5`, el modelo más caro de
  la comparativa. Si la IA se enciende antes de migrar, conviene `claude-haiku-5-5`.

A este volumen (unas 300 consultas al bot y 14 borradores al mes) la diferencia entre los
modelos económicos es de centavos al mes ([costos](costos-infraestructura.md)): la decisión
pesa por calidad de los borradores, tratamiento de los datos y trabajo de integración.

## Recomendación de plan del bot comercial (`F1-PLA-04`, `F3-COM-03`)

El bot toma los precios del catálogo de planes, el mismo con el que cobra el registro: eso
está al día. Le falta el criterio. Las reglas `plan.recomendacion` que carga
`backend/app/modules/reglas/datos.py` recomiendan `familiar` e `individual`, planes que ya
no existen, así que siempre cae en «el plan de menor valor que cubre a todas las mascotas»
y propone un solo plan para todos los peludos. TIMU tiene que decir qué plan recomendar
según ciudad, especie y número de peludos. Con eso se ajustan las reglas en
Administración → Reglas y se reemplazan las de `datos.py`, que solo se cargan en una base
nueva.

## Marca e identidad ([manual de marca](manual-de-marca.md))

Para aplicar la marca a la plataforma, TIMU tiene que entregar dos cosas. Mientras tanto, el
panel funciona con lo provisional que se indica:

- **Logo en vector (SVG) y su versión para fondo oscuro.** El manual en PDF solo trae una
  imagen de 569×308 px. Además, el texto y las siluetas del logo van en marino y no se ven
  sobre fondo oscuro. Hasta que llegue, el panel muestra el nombre «TIMU» en texto.
- **Archivo de GeosansLight y su licencia de uso web.** El manual la exige, pero el archivo
  no se adjuntó y la fuente no está en Google Fonts. Hasta que llegue, todo va en Inter.
- **Recursos gráficos para la portada pública (index).** La portada se construye cuando
  lleguen; el resto de páginas públicas no la esperan ([hoja de ruta del
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
