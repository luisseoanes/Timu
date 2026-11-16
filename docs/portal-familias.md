# El portal de familias

Qué ve y qué puede hacer una familia en `/portal`, y de dónde sale cada cosa. Cruza la API
(`backend/app/modules/portal/`) y el panel (`frontend/src/features/portal/`), y ninguno de los
dos lo cuenta entero. Este documento enlaza al código; si el código cambia, manda el código y
este documento se corrige en el mismo commit. Cómo se ve está en
[`frontend/layouts.md`](frontend/layouts.md) y en `DESIGN.md`.

## Quién entra y qué ve

El perfil `familia` entra al portal y solo a él (`ProtectedRoute`). Todo lo que pide pasa por
`FamiliaActual` en el router: la familia de la sesión, sin parámetro que se pueda cambiar. RLS
la acota otra vez en la base.

| Pantalla | Lee | Notas |
| --- | --- | --- |
| Inicio | `GET /portal/linea`, `/plan`, `/estado-cuenta`, `/servicios`, `/mi-familia` | La línea es la misma que la del panel (`afiliaciones/linea.py`), con `mascota_id` en cada estación. |
| Peludos y ficha | `/mi-familia`, `/linea`, `/mascotas/{id}/carnet`, `/mascotas/{id}/historia` | La historia solo trae lo firmado y sin las notas internas del equipo. |
| Citas | `/servicios` y `/servicios?incluir_pasados=true` | Las pasadas las separa el panel (`pasadas` en `citas.ts`). |
| Pagos | `/estado-cuenta`, `/pagos` | Comprobante solo de un pago aprobado. |
| Datos | `/mi-familia`, `/documentos`, `/contrato` | Solo contacto y dirección se editan (`PATCH /mi-familia`). |

`/plan` y `/estado-cuenta` responden 404 sin contrato vigente. No es un error: el panel lo lee
como «sin plan» (`useMiPlan` y `useMiCuenta` devuelven `null`).

## Lo que dice el backend y el panel no copia

El portal no ofrece lo que el backend va a rechazar, y no lo deduce: se lo pregunta (`DEU-2`, el
2026-11-16; antes copiaba cuatro reglas, y una ya no coincidía).

| Qué | Lo dice | Lo usa el panel |
| --- | --- | --- |
| Si la familia puede agendar, y por qué no | `motivo_sin_agendar` de `GET /portal/plan`, con las causas del contrato de `servicios.elegibilidad` (plan vencido, en pausa, cuotas vencidas) | `motivoSinAgendar` en `plan.ts` |
| Qué puede agendar sola | `tipos_agendables` de `GET /portal/plan` (`MODALIDADES_AUTOGESTION`: en casa, preventivos y en la clínica) | `AgendarModal` en `Agenda.tsx` |
| Si una cita se cambia o se cancela, y por qué no | `puede_cambiar`, `puede_cancelar` y `sin_cambios` de cada cita (`portal.service.que_puede`: estado, ruta y `PORTAL_ANTELACION_HORAS`), lo mismo que comprueban `reprogramar` y `cancelar` | `puedeCambiar` y `puedeCancelar` en `citas.ts`, y la nota de la cita |

Lo que depende de cada cita al agendarla (el cupo de cada beneficio, la mascota, las reglas
configurables de `servicio.elegibilidad`) lo dice el 422 del backend, que llega a la familia tal
cual: es español para el usuario, por convención del backend.

## Pagar

- `POST /portal/pagos` con `cuota_id` paga esa cuota; sin él, todo lo abierto
  (`portal.service.iniciar_pago`). El verde de la pantalla paga todo; «Pagar esta» paga una.
- Devuelve el enlace de Wompi y la familia sale del portal. Vuelve a `/portal/pagos/:pagoId`, y
  esa pantalla pregunta por el pago cada pocos segundos mientras siga `pendiente`
  (`useMisPagos(esperando)`): el estado real llega por el webhook de la pasarela, que aplica el
  pago y pone al día a la familia (un plan en pausa se reactiva).
- El próximo cobro del estado de cuenta puede no tener cuota todavía (un plan en pausa no las
  genera). El inicio lo enseña como estación, sin botón de pago.

## Cómo se le dice a la familia

Las palabras para la familia no son las del equipo. Viven en el portal, no en `lib/estados.ts`
(que comparte el panel):

- **El plan**: `estadoDelPlan` y `frase` en `plan.ts`. «Congelada» es «En pausa», con tono de
  aviso y una frase que dice por qué y qué hacer.
- **Las citas**: `estadoDeCita` en `citas.ts` («Confirmada», «Por autorizar», «En camino»…).
  Una visita en camino o en atención es de ahora, aunque su hora ya haya pasado.
- **Las cuotas**: `nombreCuota` en `pagos.ts`, por su mes. La `descripcion` del backend es
  técnica («Cuota 2026-08»); solo manda en los ajustes, que los escribe el equipo.
- **Los cupos**: `cupo` en `plan.ts`, siempre con el número («le quedan 4 de 6 este año» o
  «sin tope de usos este mes»). Nunca «ilimitado» (manual de marca, voz).

## Datos de demostración

`datos_demo` crea una sola familia con portal, Ana Ruiz (`ana@example.com`, clave
`demo12345`), con el plan **congelado**: tres cuotas y siete preventivos vencidos, sin citas
ni pagos. Sirve para el estado más difícil, no para el sano. Las capturas de una familia al
día se hacen interceptando la API ([`frontend/capturas-revisor.md`](frontend/capturas-revisor.md)).

## Lo que queda abierto

- ~~**La consulta en la clínica no se agenda desde el portal**~~ y ~~**las cuatro reglas
  copiadas**~~: resueltas el 2026-11-16 (`DEU-2`, tabla de arriba).
- **Una segunda familia con portal en `datos_demo`**, al día, con citas y pagos, daría al
  barrido y a los recorridos el estado sano.
