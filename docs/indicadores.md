# Indicadores del dashboard gerencial

Definición acordada de cada indicador (F4-DAS-01). Es la misma que devuelve
`GET /api/v1/dashboard/definiciones` y la que va en la hoja *Definiciones* de los
exportables. Si una fórmula cambia, se cambia a la vez en
`backend/app/modules/dashboard/service.py` y en este documento.

Todos se calculan para un período (`desde`, `hasta`, en hora de Colombia) y,
opcionalmente, una ciudad. Los resultados se cachean cinco minutos.

| Código | Indicador | Fórmula | Unidad |
| --- | --- | --- | --- |
| `afiliaciones` | Afiliaciones | Contratos con fecha de inicio dentro del período. | contratos |
| `retiros` | Retiros | Contratos cancelados con fecha de fin dentro del período. | contratos |
| `vigentes` | Afiliados vigentes al cierre | Contratos iniciados hasta el fin del período y sin fecha de fin anterior a él. | contratos |
| `recaudo` | Recaudo | Suma de pagos aprobados con fecha de pago dentro del período (cualquier medio). | COP |
| `facturado` | Facturado | Suma del valor de las cuotas (no anuladas) que vencen dentro del período. | COP |
| `recaudo_del_facturado` | Recaudo sobre lo facturado | Valor pagado de las cuotas que vencen en el período / valor de esas cuotas. | proporción |
| `mora` | Mora al cierre | Contratos vigentes con al menos una cuota vencida sin pagar al fin del período (lo pagado después del cierre cuenta como pendiente ese día); porcentaje sobre vigentes y saldo vencido total. | contratos / COP |
| `cumplimiento_rutas` | Cumplimiento de rutas | Paradas completadas / paradas planeadas en rutas no canceladas del período; puntualidad: completadas con llegada hasta 30 min después de la estimada. | proporción |
| `servicios_por_tipo` | Servicios completados por tipo | Servicios en estado completado, agendados dentro del período, por tipo. | servicios |
| `satisfaccion` | Satisfacción | Promedio de puntaje (1 a 5) de encuestas de satisfacción respondidas que se enviaron en el período; tasa de respuesta = respondidas / enviadas. | puntaje |

## Evolución

`GET /api/v1/dashboard/evolucion` (mismos filtros que los indicadores) devuelve:

- `meses`: los 12 meses que terminan en el mes de `hasta`, cada uno calculado con las mismas
  fórmulas y la misma caché. El último llega hasta `hasta`; si el mes aún no termina va con
  `parcial: true`, y el panel lo marca como en curso.
- `anterior`: el período con el que se compara el elegido. Si empieza el primer día de un mes
  (o de un año) y no sale de él, el mismo tramo del mes (o del año) anterior: del 1 al 13 de
  noviembre se compara con del 1 al 13 de octubre. Si no, los mismos días justo antes.

Por eso la mora es histórica: si contara el estado de hoy, un mes pasado cuya cuota se pagó
después saldría sin mora en la serie.

## Exportables y reportes

- `GET /api/v1/dashboard/indicadores?formato=csv|xlsx` descarga cualquier consulta.
- Los reportes programados (`/api/v1/dashboard/reportes`) llegan por correo con el
  período anterior en Excel: diarios (el día anterior), semanales (los lunes, la
  semana anterior) o mensuales (el día 1, el mes anterior).
