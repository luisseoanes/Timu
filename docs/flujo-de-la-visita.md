# Flujo de una visita en casa

Cómo se atiende un servicio en casa de la familia, de la ruta a la firma de la consulta. Cruza
tres dominios (`servicios`, `rutas` y `clinica`) y los dos lados (API y panel), y ninguno de
ellos lo cuenta entero. Este documento enlaza al código; si el código cambia, manda el código
y este documento se corrige en el mismo commit.

## Qué entra en una ruta

Solo los servicios de modalidad `domiciliario` y `preventivo` (`MODALIDADES_EN_CASA` en
`backend/app/modules/rutas/service.py`), agendados y sin ruta. Con el catálogo actual
(`backend/app/modules/catalogos/datos.py`), eso es la consulta domiciliaria, la vacunación y la
desparasitación. Las dos últimas piden autorización: sin ella, el servicio no pasa a
`en_ruta` ni a `en_atencion` (`servicios.cambiar_estado`).

## Estados, de los dos lados

La parada y su servicio avanzan juntos. Los grafos los hace cumplir la base
(`backend/app/transiciones.py` y `servicios/state_machine.py`).

| Acción en Rutas | Parada | Servicio | Qué más pasa |
| --- | --- | --- | --- |
| «Voy en camino» (`en_camino`) | `pendiente` → `en_camino` | `agendado` → `en_ruta` | Aviso a la familia por WhatsApp. |
| «Llegué» (`llegada`) | → `en_sitio` | → `en_atencion` | Se puede llegar sin haber avisado. |
| «Terminar visita» (`salida`) | → `completada` | → `completado` | Nota y evidencia opcional. Con la última parada, la ruta termina. |

- **Una parada abierta a la vez** (`_sin_otra_en_curso`): no se sale hacia otra ni se llega a
  otra con una en `en_camino` o `en_sitio`.
- **El servicio no se completa sin sus pasos obligatorios** (`pasos_faltantes` en
  `servicios/service.py`). Por eso `salida` falla si faltan, y el panel no ofrece «Terminar
  visita» hasta que estén: ofrece «Registrar la atención» (`Terminar` en
  `frontend/src/features/rutas/AccionesParada.tsx`).

## Los pasos de cada tipo

| Tipos | Pasos | Campos | Dónde se registran |
| --- | --- | --- | --- |
| Consulta domiciliaria y clínica | Valoración clínica, Plan y recomendaciones (obligatorios) | `hallazgos`, `recomendaciones` | Al firmar la consulta clínica de la visita. También en el servicio. |
| Vacunación y desparasitación | Aplicación (obligatorio), Evidencia fotográfica | `producto`, `lote`; la evidencia no tiene campos | En la ficha del servicio (`/servicios/:id`, `FichaServicio`), pensada primero para el celular. |

Un paso registrado se corrige mientras el servicio está en atención: la ficha ofrece «Editar» y
`completar_paso` (`servicios/service.py`) lo actualiza, con `U` sobre `servicio_pasos` en la
matriz de `backend/app/core/permisos_db.py` para los perfiles que lo insertan (migración `0041`,
decidido con el usuario el 2026-11-14). Al completarse el servicio el paso queda fijo, porque
`completar_paso` solo admite registrar en atención, y la bitácora guarda cada versión. Si se
corrige a mano un paso que llenó la consulta firmada, la consulta no cambia: la corrección queda
en el paso y en la bitácora.

## La consulta es el registro de la visita

Decidido con el usuario en `R2-PAN-07` (`docs/hoja-de-ruta-rediseno.md`).

1. En una parada en sitio con mascota, «Registrar la atención» abre la consulta de esa mascota
   ligada al servicio: `/clinica/mascotas/:id?servicio=:servicio_id`. Clínica también la lista
   en el trabajo pendiente del médico.
2. Para firmar la consulta de una visita hace falta, además del motivo y el diagnóstico, el
   tratamiento (`faltanParaFirmar` en `frontend/src/features/clinica/consulta.ts`).
3. Al firmarla con el servicio `en_atencion`, `_registrar_pasos_del_servicio`
   (`backend/app/modules/clinica/service.py`) registra los pasos que la consulta llena, con la
   tabla `_PASOS_DESDE_LA_CONSULTA`:
   - `hallazgos`: el examen físico y el diagnóstico.
   - `recomendaciones`: el tratamiento.

   No toca los pasos ya registrados ni los que tienen un campo fuera de la tabla.
4. La consulta firmada ofrece «Volver a la ruta», y allí ya aparece «Terminar visita».

**Una vacuna no pasa por la consulta**: su aplicación (producto y lote) no la llena la
consulta, así que en esos servicios «Registrar la atención» lleva a la ficha del servicio con
`?origen=ruta` (decidido con el usuario en `R2-PAN-05`): la ficha abre en el primer paso que falta,
al guardarlo pasa al siguiente, bloquea «Completar» mientras falte alguno obligatorio y ofrece
«Volver a mi ruta». El panel decide adónde lleva el botón con `laConsultaLosRegistra` (`frontend/src/features/rutas/ruta.ts`),
que lee `lo_registra_la_consulta` de cada paso en el catálogo de tipos de servicio. Ese dato lo
calcula el catálogo con los campos que clínica le conecta al importarse
(`catalogos.conectar_campos_de_la_consulta`, desde `_PASOS_DESDE_LA_CONSULTA`): el panel ya no copia
la tabla (`R2-PAN-08`).

## La visita de un preventivo es su registro

Decidido con el usuario en `R2-PAN-08`: el servicio manda. La familia autoriza una vez y el
producto se escribe una vez, en la ficha del servicio.

- **Agendar** un preventivo (`preventivos.agendar`) crea su servicio y lo enlaza
  (`eventos_preventivos.servicio_id`). Si el preventivo ya está autorizado, o no lo necesita, el
  servicio nace autorizado.
- **Autorizar** el preventivo autoriza también su visita, si ya estaba agendada; autorizar la
  visita (`servicios.autorizar`) autoriza el preventivo.
- **Completar** la visita aplica el preventivo con el producto y el lote del paso «Aplicación»,
  la fecha de hoy y quien registró el paso, y programa la dosis siguiente. El carnet lo muestra
  sin que nadie lo vuelva a escribir.
- **Cancelar** la visita desenlaza el preventivo, que vuelve a estar por agendar.

Lo hace `_seguir_servicio` (`backend/app/modules/preventivos/service.py`), que servicios llama en
cada `cambiar_estado`: preventivos importa servicios, así que se lo conecta con
`servicios.conectar_al_cambiar_estado` al importarse, y sin conectar `cambiar_estado` falla en
lugar de dejar el preventivo sin aplicar. «Registrar aplicación» en Preventivos queda para lo que
se aplicó sin visita (en la clínica o fuera).

Dos huecos conocidos: el peso de la desparasitación (`F2-PRE-07`) no está en el paso «Aplicación»,
así que solo se anota al registrar la aplicación en Preventivos; y una visita preventiva agendada
desde el portal no se enlaza con ningún preventivo, así que completarla no lo aplica.

## Lo que queda abierto

- **El portal** enseña a la familia sus visitas y su historia: cada visita es una estación de
  la línea del inicio (`GET /portal/linea`) y una cita en «Tus citas», con el estado de esta
  tabla dicho con sus palabras («En camino», «En atención»; `estadoDeCita` en
  `frontend/src/features/portal/citas.ts`). El portal entero, en
  [`portal-familias.md`](portal-familias.md).
