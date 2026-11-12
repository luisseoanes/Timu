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
| Vacunación y desparasitación | Aplicación (obligatorio), Evidencia fotográfica | `producto`, `lote`; la evidencia no tiene campos | En el servicio (`/servicios/:id`, `PasosAtencion`). |

Un paso registrado no se modifica: ningún perfil del equipo tiene `UPDATE` sobre `servicio_pasos`
en la matriz de `backend/app/core/permisos_db.py`, solo leerlos e insertarlos.

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
consulta, así que en esos servicios «Registrar la atención» lleva al servicio. El panel lo
decide con `laConsultaLosRegistra` (`frontend/src/features/rutas/ruta.ts`), que copia la tabla
del backend. Esa copia es deuda: ver «Deuda conocida» en
[`frontend/conventions.md`](frontend/conventions.md).

## Lo que queda abierto

- **`R2-PAN-08`** (Cartera y preventivos) rediseña el registro de la aplicación de una vacuna
  y agenda un preventivo desde la línea de Familias. Es la unidad que debería cerrar la deuda
  anterior.
- **R3, el portal**, enseña a la familia sus visitas y su historia: los estados de la tabla de
  arriba son los que verá.
